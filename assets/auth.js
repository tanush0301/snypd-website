/* SNYPD auth screen: /login, /signup, /reset-password.
   Implements the Claude Design component "SNYPDAuthScreen" (project
   a9271573-..., boards in "SNYPD Auth 1a States.dc.html"). Markup and inline
   styles are the design's own; the design's demo timers are replaced by the
   real Supabase calls. One view + status state machine drives everything:

     views:  login, signup, forgot, forgot-sent, verify, reset, reset-done,
             reset-expired
     status: idle, field-errors, wrong-password, not-confirmed, exists,
             exists-notice, loading, slow, network, expired, signed-in, resent
             (+ rate-limit, error: real Supabase outcomes the boards don't
             draw, shown in the same banner style)

   Google sign-in returns to /login, never straight to /dashboard: an OAuth
   error comes back in the URL, and the dashboard (no session -> /login) used
   to drop it silently. Here it is shown, and a real session is forwarded. */
(function () {
  'use strict';

  var script = document.currentScript;
  var PAGE = (script && script.getAttribute('data-page')) || 'login';
  var sb = window.SNYPD && window.SNYPD.supabase;
  var form = document.getElementById('au-form');
  if (!form) return;

  var PROD = /(^|\.)snypd\.store$/i.test(location.hostname);
  var SITE = PROD ? 'https://www.snypd.store' : location.origin;
  var FOUNDING_URL = 'https://api.snypd.store/api/v1/founding-members';
  var RE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var PLAN_NAMES = { solo: 'Solo', pro: 'Pro', kickstart: 'Kickstart', elite: 'Elite' };
  var LAST_EMAIL_KEY = 'snypd_last_email';
  var VERIFY_EMAIL_KEY = 'snypd_verify_email';
  function pendingEmail(value) {
    try {
      if (value !== undefined) sessionStorage.setItem(VERIFY_EMAIL_KEY, value);
      return sessionStorage.getItem(VERIFY_EMAIL_KEY) || '';
    } catch (e) { return ''; }
  }
  var SLOW_MS = 8000, TIMEOUT_MS = 30000, COOLDOWN = 60;
  /* The sign-up line links /terms and /privacy. Those pages are drafted but
     not published yet (see CLAUDE.md, Session 27), so the line stays hidden
     until they are live. Flip to true in the same commit that publishes them. */
  var LEGAL_LIVE = true;

  var TITLES = {
    login: 'Log in to SNYPD', signup: 'Sign up free - SNYPD Vinted Monitor',
    forgot: 'Reset your password - SNYPD', 'forgot-sent': 'Check your inbox - SNYPD',
    verify: 'Check your email - SNYPD', reset: 'Set a new password - SNYPD',
    'reset-done': 'Password updated - SNYPD', 'reset-expired': 'Reset link expired - SNYPD'
  };

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function track(name, params) {
    try { if (window.gtag) window.gtag('event', name, params || {}); } catch (e) {}
    /* window.fbq only exists after marketing consent (assets/consent.js). */
    try { if (name === 'sign_up' && window.fbq) window.fbq('track', 'CompleteRegistration'); } catch (e) {}
  }

  var qs = new URLSearchParams((window.SNYPD_AUTH_URL && window.SNYPD_AUTH_URL.search) || location.search);
  var hs = new URLSearchParams(((window.SNYPD_AUTH_URL && window.SNYPD_AUTH_URL.hash) || location.hash).replace(/^#/, ''));
  var plan = (qs.get('plan') || '').toLowerCase();

  /* A price-guide page's "alert me" button (/signup?hunt=<words>&max=<EUR>): kept for a
     day so the dashboard's first-hunt wizard opens with this search filled in
     (dashboard.html). Stored only because the visitor asked for exactly this search. */
  (function () {
    var h = (qs.get('hunt') || '').trim().replace(/\s+/g, ' '), m = Number(qs.get('max'));
    if (h && h.length <= 80) lsSet('snypd_hunt_intent', JSON.stringify({ q: h, max: m > 0 ? Math.round(m) : 0, t: Date.now() }));
  })();

  var S = {
    view: PAGE === 'signup' ? 'signup' : PAGE === 'reset' ? 'reset' : 'login',
    status: 'idle', email: '', code: '', pw: '', pw2: '', show: false, errors: {},
    cooldown: 0, founding: null, marketing: false, errText: '', oauth: false, ready: PAGE !== 'reset'
  };

  /* ---------- validation (the design's own rules) ---------- */
  function validate(view, email, pw, pw2, code) {
    var e = {};
    if (view === 'login' || view === 'signup' || view === 'forgot' || view === 'verify') {
      var m = (email || '').trim();
      if (!m) e.email = 'Enter your email.';
      else if (!RE_EMAIL.test(m)) e.email = 'Enter a full email, like name@example.com.';
    }
    if (view === 'verify' && !/^\d{6,10}$/.test((code || '').replace(/\s/g, ''))) e.code = 'Enter the code from your latest confirmation email.';
    if (view === 'login' && !pw) e.pw = 'Enter your password.';
    if (view === 'signup' || view === 'reset') {
      if (!pw) e.pw = 'Choose a password (at least 6 characters).';
      else if (pw.length < 6) e.pw = 'At least 6 characters.';
    }
    if (view === 'reset' && !e.pw && pw2 !== pw) e.pw2 = "Passwords don't match.";
    return e;
  }

  /* ---------- Supabase error -> screen state ---------- */
  function classify(err) {
    if (!err) return null;
    var m = String(err.message || '').toLowerCase(), s = err.status, code = String(err.code || '');
    if (err.name === 'AuthRetryableFetchError' || /failed to fetch|load failed|networkerror|network request failed/.test(m)) return 'network';
    if (s === 429 || /rate_limit/.test(code) || /rate limit|too many/.test(m)) return 'rate-limit';
    if (code === 'invalid_credentials' || /invalid login credentials/.test(m)) return 'wrong-password';
    if (code === 'email_not_confirmed' || /email not confirmed/.test(m)) return 'not-confirmed';
    if (code === 'user_already_exists' || code === 'email_exists' || /already registered|already been registered|already exists/.test(m)) return 'exists';
    if (code === 'same_password' || /different from the old/.test(m)) return 'same-password';
    if (code === 'weak_password' || /password should|password is too/.test(m)) return 'weak-password';
    if (code === 'email_address_invalid' || /email address .*invalid|invalid email/.test(m)) return 'bad-email';
    if (err.name === 'AuthSessionMissingError' || /session missing|session_not_found/.test(m + code)) return 'no-session';
    return 'other';
  }

  /* Runs one auth request: loading -> slow after 8s -> network after 30s. */
  var slowT = null, reqId = 0;
  function run(promiseFn, onDone) {
    var id = ++reqId;
    S.errors = {}; S.status = 'loading'; render();
    clearTimeout(slowT);
    slowT = setTimeout(function () { if (id === reqId && S.status === 'loading') { S.status = 'slow'; render(); } }, SLOW_MS);
    var timer;
    var timeout = new Promise(function (res) { timer = setTimeout(function () { res({ error: { name: 'AuthRetryableFetchError', message: 'timeout' } }); }, TIMEOUT_MS); });
    var call;
    try { call = Promise.resolve(promiseFn()); } catch (e) { call = Promise.resolve({ error: e }); }
    Promise.race([call.catch(function (e) { return { error: e }; }), timeout]).then(function (r) {
      clearTimeout(timer); clearTimeout(slowT);
      if (id !== reqId) return;
      onDone(r || {});
    });
  }

  /* ---------- actions ---------- */
  function go(view, extra) {
    reqId++; clearTimeout(slowT); clearTimeout(redirectT);
    S.view = view; S.status = 'idle'; S.errors = {}; S.errText = '';
    if (extra) for (var k in extra) S[k] = extra[k];
    if (view === 'login' || view === 'signup') {
      var path = '/' + view;
      if (location.pathname !== path || location.search || location.hash) { try { history.replaceState(null, '', path); } catch (e) {} }
    }
    if (view === 'verify') {
      pendingEmail(S.email);
      try { history.replaceState(null, '', '/login?verify=1'); } catch (e) {}
    }
    render();
  }

  var tick = null;
  function startCooldown() {
    S.cooldown = COOLDOWN;
    clearInterval(tick);
    tick = setInterval(function () {
      S.cooldown = Math.max(0, S.cooldown - 1);
      if (!S.cooldown) clearInterval(tick);
      render();
    }, 1000);
  }

  var redirectT = null;
  function toLoginExists() { go('login', { status: 'exists-notice', pw: '' }); focusField('pw'); }
  function openDashboard(email) {
    if (email) lsSet(LAST_EMAIL_KEY, email);
    S.view = 'login'; S.status = 'signed-in'; render();
    setTimeout(function () { location.replace('/dashboard'); }, 600);
  }

  /* Campaign tags (utm_*) from the address, e.g. from a Meta ad. Read from the URL
     only, never stored on the device; saved with the new account so sign-ups can be
     counted per ad (assets/consent.js keeps them on links between pages). */
  function campaignTags(src) {
    var out = {}, q = src || new URLSearchParams(location.search);
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'].forEach(function (k) {
      var v = q.get(k);
      if (v && /^[A-Za-z0-9_.-]{1,60}$/.test(v)) out[k] = v;
    });
    return out;
  }

  /* Entry page (from=fr.bot-vinted, set by assets/consent.js on links to /signup,
     /login and /plans): the SNYPD page this visitor started on. Address only. */
  function entryPage(src) {
    var v = null;
    try { v = (src || new URLSearchParams(location.search)).get('from'); } catch (e) {}
    return v && /^[a-z0-9.-]{1,80}$/.test(v) ? v : null;
  }

  /* Whop partner code (a=<Whop username>) from a partner's link: from the address
     (assets/consent.js keeps it on links), else from this browser (snypd_aff, only
     stored with marketing consent, 30 days). Saved with the account so /plans can
     pass it to Whop's checkout after the email is confirmed, maybe in another tab. */
  function partnerCode() {
    var v = null;
    try { v = new URLSearchParams(location.search).get('a'); } catch (e) {}
    if (!v) {
      try { var s = JSON.parse(lsGet('snypd_aff') || 'null'); if (s && s.a && Date.now() - s.t < 30 * 864e5) v = s.a; } catch (e) {}
    }
    return v && /^[A-Za-z0-9_.-]{1,60}$/.test(v) ? v : null;
  }

  /* The item a price-guide page sent this visitor for (snypd_hunt_intent, set above),
     saved with the new account so sign-ups can be counted per price page. */
  function huntIntent() {
    try {
      var h = JSON.parse(lsGet('snypd_hunt_intent') || 'null');
      return h && typeof h.q === 'string' && Date.now() - Number(h.t) < 864e5 ? h.q.slice(0, 80) : null;
    } catch (e) { return null; }
  }

  function signupData() {
    var data = { marketing_opt_in: !!S.marketing };
    var tags = campaignTags();
    for (var k in tags) data[k] = tags[k];
    var aff = partnerCode();
    if (aff) data.whop_aff = aff;
    if (S.marketing) {
      data.marketing_opt_in_at = new Date().toISOString();
      data.marketing_opt_in_source = 'signup';
      // Same wording/version as the dashboard card and /account (19 Oct 2026).
      data.marketing_opt_in_text = 'v2 2026-10-19: Product updates, Vinted tips and occasional offers';
    }
    var hi = huntIntent();
    if (hi) data.entry_hunt = hi;
    var ep = entryPage();
    if (ep) data.entry_page = ep;
    var ref = lsGet('snypd_ref');
    if (ref && /^[a-z2-9]{4,8}$/.test(ref)) data.ref_code = ref;
    try {
      var pi = JSON.parse(lsGet('snypd_plan_intent') || 'null');
      if (pi && pi.plan) data.plan_intent = pi.plan;
    } catch (e) {}
    return data;
  }

  function fail(kind, err) {
    if (kind === 'network' || kind === 'rate-limit') { S.status = kind; return; }
    S.status = 'error';
    S.errText = 'Something went wrong' + (err && err.message ? ': ' + err.message : '') + '. Try again.';
  }

  function submit() {
    if (S.status === 'loading' || S.status === 'slow' || S.oauth) return;
    var v = S.view, email = (S.email || '').trim();
    var errors = validate(v, S.email, S.pw, S.pw2, S.code);
    if (Object.keys(errors).length) {
      S.errors = errors; S.status = 'field-errors'; render();
      focusField(errors.email ? 'email' : errors.pw ? 'pw' : errors.code ? 'code' : 'pw2');
      return;
    }
    S.email = email;

    if (v === 'login') {
      run(function () { return sb.auth.signInWithPassword({ email: email, password: S.pw }); }, function (r) {
        if (!r.error && r.data && r.data.session) { track('login', { method: 'email' }); openDashboard(email); return; }
        var k = classify(r.error);
        if (k === 'wrong-password') { S.status = 'wrong-password'; S.pw = ''; render(); focusField('pw'); return; }
        if (k === 'not-confirmed') { go('verify', { pw: '', code: '', status: 'not-confirmed' }); return; }
        else if (k === 'bad-email') { S.status = 'field-errors'; S.errors = { email: 'Enter a full email, like name@example.com.' }; }
        else fail(k, r.error);
        render();
      });
    } else if (v === 'signup') {
      run(function () {
        return sb.auth.signUp({ email: email, password: S.pw, options: { emailRedirectTo: SITE + '/login', data: signupData() } });
      }, function (r) {
        if (!r.error) {
          var u = r.data && r.data.user;
          if (u && Array.isArray(u.identities) && u.identities.length === 0) { existsNow(); return; }
          if (r.data && r.data.session) { track('sign_up', { method: 'email' }); openDashboard(email); return; }
          track('sign_up', { method: 'email' });
          go('verify', { pw: '' }); startCooldown(); render();
          return;
        }
        var k = classify(r.error);
        if (k === 'exists') { existsNow(); return; }
        if (k === 'weak-password') { S.status = 'field-errors'; S.errors = { pw: r.error.message || 'Choose a stronger password.' }; render(); focusField('pw'); return; }
        if (k === 'bad-email') { S.status = 'field-errors'; S.errors = { email: 'Enter a full email, like name@example.com.' }; render(); focusField('email'); return; }
        fail(k, r.error); render();
      });
    } else if (v === 'verify') {
      var token = S.code.replace(/\s/g, '');
      pendingEmail(email);
      run(function () { return sb.auth.verifyOtp({ email: email, token: token, type: 'email' }); }, function (r) {
        var session = r.data && r.data.session, user = session && session.user;
        if (!r.error && user && user.email_confirmed_at && String(user.email || '').toLowerCase() === email.toLowerCase()) {
          S.code = ''; pendingEmail('');
          track('email_verified', { method: 'code' });
          openDashboard(user.email); return;
        }
        verificationFailed(r.error);
      });
    } else if (v === 'forgot') {
      run(function () { return sb.auth.resetPasswordForEmail(email, { redirectTo: SITE + '/reset-password' }); }, function (r) {
        var k = classify(r.error);
        /* Same screen whether or not the account exists; only a failure to
           send at all keeps the visitor here. */
        if (k === 'network' || k === 'rate-limit') { S.status = k; render(); return; }
        go('forgot-sent'); startCooldown(); render();
      });
    } else if (v === 'reset') {
      run(function () { return sb.auth.updateUser({ password: S.pw }); }, function (r) {
        if (!r.error) { go('reset-done', { pw: '', pw2: '' }); return; }
        var k = classify(r.error);
        if (k === 'same-password') { S.status = 'field-errors'; S.errors = { pw: 'Use a different password from your current one.' }; render(); focusField('pw'); return; }
        if (k === 'weak-password') { S.status = 'field-errors'; S.errors = { pw: r.error.message || 'Choose a stronger password.' }; render(); focusField('pw'); return; }
        if (k === 'no-session') { go('reset-expired'); return; }
        fail(k, r.error); render();
      });
    }
  }

  function existsNow() {
    S.status = 'exists'; render();
    clearTimeout(redirectT);
    redirectT = setTimeout(toLoginExists, 2500);
  }

  function verificationFailed(err) {
    var k = classify(err);
    S.status = k === 'network' || k === 'rate-limit' ? k : 'verification-error';
    S.code = ''; render();
  }

  function resendSignup() {
    if (S.cooldown > 0 || S.status === 'loading' || S.status === 'slow') return;
    var email = (S.email || '').trim();
    var errors = validate('forgot', email);
    if (Object.keys(errors).length) { S.errors = errors; S.status = 'field-errors'; render(); focusField('email'); return; }
    pendingEmail(email);
    run(function () { return sb.auth.resend({ type: 'signup', email: email, options: { emailRedirectTo: SITE + '/login' } }); }, function (r) {
      var k = classify(r.error);
      if (k === 'network' || k === 'rate-limit') S.status = k;
      else if (r.error) fail(k, r.error);
      else { S.status = 'resent'; S.code = ''; startCooldown(); }
      render();
    });
  }

  function resend() {
    if (S.cooldown > 0 || S.status === 'loading' || S.status === 'slow') return;
    if (S.view === 'verify') { resendSignup(); return; }
    var email = (S.email || '').trim();
    run(function () { return sb.auth.resetPasswordForEmail(email, { redirectTo: SITE + '/reset-password' }); }, function (r) {
      var k = classify(r.error);
      if (k === 'network' || k === 'rate-limit') S.status = k;
      else { S.status = 'resent'; startCooldown(); }
      render();
    });
  }

  function google() {
    if (S.status === 'loading' || S.status === 'slow' || S.oauth) return;
    S.oauth = true; S.errText = ''; if (S.status !== 'field-errors') S.status = 'idle'; render();
    track('login_start', { method: 'google' });
    /* Google can't carry account data, so campaign tags and the partner code ride
       on the return address and are saved on the new account back on /login. */
    var back = new URLSearchParams(campaignTags());
    var aff = partnerCode();
    if (aff) back.set('a', aff);
    var ep = entryPage();
    if (ep) back.set('from', ep);
    var backQs = back.toString();
    Promise.resolve().then(function () {
      return sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: SITE + '/login' + (backQs ? '?' + backQs : ''), queryParams: { prompt: 'select_account' } }
      });
    }).then(function (r) {
      if (r && r.error) throw r.error;
      /* The browser is now leaving for Google. If it doesn't (blocked
         navigation), give the button back after a while. */
      setTimeout(function () { S.oauth = false; render(); }, 8000);
    }).catch(function (err) {
      S.oauth = false;
      var k = classify(err);
      if (k === 'network') S.status = 'network';
      else { S.status = 'error'; S.errText = "Couldn't start Google sign-in. Try again, or use your email."; }
      render();
    });
  }

  /* ---------- banner (design copy, plus the two real outcomes it lacks) ---------- */
  function banner() {
    var st = S.status, v = S.view;
    if (st === 'network') return { tone: 'danger', text: "Couldn't reach SNYPD. Check your connection and try again." };
    if (st === 'rate-limit') return { tone: 'danger', text: 'Too many attempts in a short time. Wait a minute, then try again.' };
    if (st === 'error') return { tone: 'danger', text: S.errText };
    if (v === 'verify') {
      if (st === 'verification-error' || st === 'link-expired') return { tone: 'warn', text: 'That confirmation could not be completed. Use the code from your latest email, or request a new email below. Already confirmed? Go back to log in.' };
      if (st === 'not-confirmed') return { tone: 'info', text: 'Confirm your email to finish signing up. Enter your latest code below, or request a new email.' };
      if (st === 'resent') return { tone: 'ok', text: 'Confirmation email requested. Use only the latest email; earlier codes may no longer work.' };
    }
    if (v === 'login') {
      if (st === 'wrong-password') return { tone: 'danger', text: "That email and password don't match. Check both, or reset your password.", label: 'Reset password', act: 'forgot' };
      if (st === 'not-confirmed') return { tone: 'warn', text: 'Confirm your email first. We sent a link to ' + S.email + '.', label: 'Resend confirmation email', act: 'resend-confirm' };
      if (st === 'exists-notice') return { tone: 'info', text: 'You already have an account with ' + S.email + '. Log in below.', label: 'Forgot password?', act: 'forgot' };
      if (st === 'expired') return { tone: 'info', text: 'Your session expired. Log in to get back to your hunts.' };
      if (st === 'link-expired') return { tone: 'warn', text: 'That email link has expired or was already used. Log in below, and if your email still needs confirming we will offer a new link.' };
      if (st === 'signed-in') return { tone: 'ok', text: 'Signed in. Opening your dashboard…' };
    }
    if (v === 'signup' && st === 'exists') return { tone: 'info', text: 'This email already has an account. Taking you to log in…', label: 'Go now', act: 'exists-now' };
    if (st === 'resent') return { tone: 'ok', text: 'Sent again. It can take a minute to arrive.' };
    return null;
  }

  /* ---------- rendering: the design's markup, verbatim styles ---------- */
  var ID = 'au';
  var H1 = "font-family:'Cabinet Grotesk',var(--font);font-weight:900;line-height:1;letter-spacing:-.04em;";
  var STACK = 'display:flex;flex-direction:column;gap:12px;';
  var SUB = 'font-size:13px;line-height:1.6;color:var(--text-secondary);';
  var LINKBTN = 'background:none;border:none;padding:0;font-size:13px;color:var(--success);cursor:pointer;';
  var BANNER = 'padding:12px 14px;display:flex;flex-direction:column;gap:6px;font-size:13px;line-height:1.6;color:var(--text-primary);overflow-wrap:anywhere;';
  var BIGBTN = 'height:52px;display:flex;align-items:center;justify-content:center;background:var(--brand);color:var(--brand-fg);font-size:13px;letter-spacing:.1em;text-decoration:none;';
  var INPUT = 'width:100%;box-sizing:border-box;height:52px;background:var(--panel);border:1px solid ';
  var GOOGLE_SVG = '<svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.150 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path></svg>';

  function attr(name, on) { return on ? ' ' + name : ''; }

  function bannerHTML(b) {
    if (!b) return '';
    var action = b.act ? '<button type="button" data-act="' + b.act + '" style="align-self:flex-start;background:none;border:none;padding:0;min-height:32px;font-size:13px;color:var(--success);cursor:pointer;text-decoration:underline;">' + esc(b.label) + '</button>' : '';
    if (b.tone === 'danger') return '<div role="alert" style="border:1px solid rgba(255,92,92,.45);background:rgba(255,92,92,.06);' + BANNER + '"><span><span style="color:var(--danger);">✕</span> ' + esc(b.text) + '</span>' + action + '</div>';
    if (b.tone === 'warn') return '<div role="alert" style="border:1px solid rgba(255,176,32,.45);background:rgba(255,176,32,.06);' + BANNER + '"><span><span style="color:var(--warning);">!</span> ' + esc(b.text) + '</span>' + action + '</div>';
    if (b.tone === 'info') return '<div role="status" style="border:1px solid var(--border3);background:var(--panel);' + BANNER + '"><span>' + esc(b.text) + '</span>' + action + '</div>';
    return '<div role="status" style="border:1px solid rgba(0,229,160,.42);background:rgba(0,229,160,.06);padding:12px 14px;font-size:13px;line-height:1.6;color:var(--text-primary);"><span style="color:var(--success);">✓</span> ' + esc(b.text) + '</div>';
  }

  function errSpan(id, text) {
    return '<span id="' + id + '" class="au-err" style="font-size:12px;line-height:1.5;color:var(--danger);">' + esc(text) + '</span>';
  }

  function tpl() {
    var v = S.view, st = S.status, er = S.errors || {};
    var busy = st === 'loading' || st === 'slow';
    var lock = busy || S.oauth;
    var out = [];
    var isLogin = v === 'login', isSignup = v === 'signup';

    if (isLogin) out.push('<h1 style="margin:0 0 4px;' + H1 + 'font-size:clamp(40px,5vw,48px);">Log in</h1>');
    if (isSignup) {
      var f = S.founding, founding = '';
      if (typeof f === 'number') {
        var pulse = f > 0 ? '<span aria-hidden="true" style="width:7px;height:7px;flex:0 0 auto;background:#00E5A0;animation:pulseDot 2.2s ease infinite;"></span>' : '';
        founding = '<div style="display:flex;align-items:center;gap:8px;">' + pulse + '<span style="font-size:12px;letter-spacing:.06em;color:var(--text-secondary);">FOUNDING · ' + (f > 0 ? f + ' of the first 100 spots left' : 'all 100 founding spots claimed') + '</span></div>';
      }
      out.push('<div style="' + STACK + '"><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);text-wrap:balance;">Create your free account</h1><span style="font-size:13px;color:var(--text-secondary);">Free plan, no card.</span>' + founding + '</div>');
      if (PLAN_NAMES[plan]) out.push('<div style="border:1px solid var(--border-hover);background:var(--panel);padding:12px 14px;font-size:13px;line-height:1.6;color:var(--text-secondary);">You picked <span style="color:var(--text-primary);">' + PLAN_NAMES[plan] + '</span>. You start on Free; upgrade in one click from the dashboard.</div>');
    }
    if (v === 'forgot') out.push('<div style="' + STACK + '"><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);">Reset your password</h1><span style="' + SUB + '">Enter your account email. We\'ll send a link to set a new password.</span></div>');
    if (v === 'forgot-sent') out.push('<div style="' + STACK + '"><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);">Check your inbox</h1><span style="' + SUB + 'overflow-wrap:anywhere;">If an account exists for <span style="color:var(--text-primary);">' + esc(S.email) + '</span>, we\'ve sent a password reset link.</span></div>');
    if (v === 'verify') out.push('<div style="' + STACK + '"><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);">Confirm your email</h1><span style="' + SUB + '">Enter your account email and the code from your latest SNYPD confirmation email. If an older email only has a link, request a new email below.</span></div>');
    if (v === 'reset') out.push('<h1 style="margin:0 0 4px;' + H1 + 'font-size:clamp(36px,4.5vw,44px);">Set a new password</h1>');
    if (v === 'reset-done') {
      out.push('<div style="' + STACK + '"><span style="font-size:12px;letter-spacing:.14em;color:var(--success);">✓ SAVED</span><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);">Password updated</h1><span style="' + SUB + '">You\'re signed in with your new password.</span></div>');
      out.push('<a href="/dashboard" class="h-brandlink" style="' + BIGBTN + '">OPEN DASHBOARD</a>');
    }
    if (v === 'reset-expired') {
      out.push('<div style="' + STACK + '"><h1 style="margin:0;' + H1 + 'font-size:clamp(36px,4.5vw,44px);text-wrap:balance;">This reset link has expired</h1><span style="' + SUB + '">Reset links work once and expire after a while. Send yourself a new one.</span></div>');
      out.push('<button type="button" data-act="forgot" class="h-brand" style="height:52px;width:100%;background:var(--brand);color:var(--brand-fg);border:none;font-size:13px;letter-spacing:.1em;cursor:pointer;">SEND A NEW LINK</button>');
    }

    out.push(bannerHTML(banner()));

    /* Instagram/Facebook/TikTok open links in their own in-app browser, and Google
       refuses sign-in there (disallowed_useragent). Most SNYPD visitors arrive from
       Instagram, so there the email form comes first and Google is not offered. */
    if ((isLogin || isSignup) && IN_APP) {
      out.push('<div role="note" style="border:1px solid var(--border-hover);background:var(--panel);padding:14px 16px;font-size:13px;line-height:1.55;color:var(--text-secondary);">You opened this inside Instagram or another app. Google sign-in does not work here, so use your email below. Prefer Google? Tap the <b style="color:var(--text-primary);font-weight:500;">...</b> menu at the top and open this page in your browser.</div>');
    } else if (isLogin || isSignup) {
      out.push('<button type="button" data-act="google"' + attr('disabled', lock) + ' class="h-ghost" style="display:flex;align-items:center;justify-content:center;gap:12px;height:52px;width:100%;background:var(--panel);border:1px solid var(--border-hover);color:var(--text-primary);font-size:13px;letter-spacing:.08em;cursor:pointer;">' + GOOGLE_SVG + '<span>CONTINUE WITH GOOGLE</span></button>');
      out.push('<div style="display:flex;align-items:center;gap:12px;"><span style="flex:1;height:1px;background:var(--border);"></span><span style="font-size:12px;letter-spacing:.12em;color:var(--text-muted);">OR</span><span style="flex:1;height:1px;background:var(--border);"></span></div>');
    }

    if (isLogin || isSignup || v === 'forgot' || v === 'verify') {
      out.push('<div class="au-fbox" style="display:flex;flex-direction:column;gap:8px;"><label for="' + ID + '-em" style="font-size:12px;letter-spacing:.1em;color:var(--text-secondary);">EMAIL</label>' +
        '<input id="' + ID + '-em" name="email" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" inputmode="email" data-f="email"' + attr('readonly', busy) + ' aria-invalid="' + (er.email ? 'true' : 'false') + '" aria-describedby="' + ID + '-eme" class="f-in" style="' + INPUT + (er.email ? 'var(--danger)' : 'var(--border)') + ';color:var(--text-primary);font-size:16px;padding:0 14px;outline:none;border-radius:0;">' +
        (er.email ? errSpan(ID + '-eme', er.email) : '') + '</div>');
    }

    if (v === 'verify') {
      out.push('<div class="au-fbox" style="display:flex;flex-direction:column;gap:8px;"><label for="' + ID + '-code" style="font-size:12px;letter-spacing:.1em;color:var(--text-secondary);">CONFIRMATION CODE</label>' +
        '<input id="' + ID + '-code" name="code" type="text" inputmode="numeric" autocomplete="one-time-code" autocapitalize="none" spellcheck="false" maxlength="20" data-f="code"' + attr('readonly', busy) + ' aria-invalid="' + (er.code ? 'true' : 'false') + '" aria-describedby="' + ID + '-codee" class="f-in" style="' + INPUT + (er.code ? 'var(--danger)' : 'var(--border)') + ';color:var(--text-primary);font-size:20px;letter-spacing:.15em;padding:0 14px;outline:none;border-radius:0;">' +
        (er.code ? errSpan(ID + '-codee', er.code) : '') + '</div>');
    }

    if (isLogin || isSignup || v === 'reset') {
      var hint = isSignup || v === 'reset';
      var described = [er.pw ? ID + '-pwe' : '', hint ? ID + '-pwh' : ''].filter(Boolean).join(' ');
      out.push('<div class="au-fbox" style="display:flex;flex-direction:column;gap:8px;"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;min-height:32px;">' +
        '<label for="' + ID + '-pw" style="font-size:12px;letter-spacing:.1em;color:var(--text-secondary);">' + (v === 'reset' ? 'NEW PASSWORD' : 'PASSWORD') + '</label>' +
        (isLogin ? '<button type="button" data-act="forgot" style="background:none;border:none;padding:0 0 0 12px;min-height:32px;font-size:12px;color:var(--success);cursor:pointer;">Forgot password?</button>' : '') +
        (hint ? '<span id="' + ID + '-pwh" style="font-size:12px;color:var(--text-muted);">At least 6 characters</span>' : '') +
        '</div><div style="position:relative;">' +
        '<input id="' + ID + '-pw" name="password" type="' + (S.show ? 'text' : 'password') + '" autocomplete="' + (isLogin ? 'current-password' : 'new-password') + '"' + (isLogin ? '' : ' minlength="6"') + ' data-f="pw"' + attr('readonly', busy) + ' aria-invalid="' + (er.pw ? 'true' : 'false') + '"' + (described ? ' aria-describedby="' + described + '"' : '') + ' class="f-in" style="' + INPUT + (er.pw ? 'var(--danger)' : 'var(--border)') + ';color:var(--text-primary);font-size:16px;padding:0 84px 0 14px;outline:none;border-radius:0;">' +
        '<button type="button" data-act="toggle-pw" aria-label="' + (S.show ? 'Hide password' : 'Show password') + '" aria-pressed="' + (S.show ? 'true' : 'false') + '" aria-controls="' + ID + '-pw" class="h-toggle" style="position:absolute;top:4px;right:4px;height:44px;min-width:68px;background:none;border:none;color:var(--text-secondary);font-size:12px;letter-spacing:.1em;cursor:pointer;">' + (S.show ? 'HIDE' : 'SHOW') + '</button>' +
        '</div>' + (er.pw ? errSpan(ID + '-pwe', er.pw) : '') + '</div>');
    }

    if (v === 'reset') {
      out.push('<div class="au-fbox" style="display:flex;flex-direction:column;gap:8px;"><label for="' + ID + '-pw2" style="font-size:12px;letter-spacing:.1em;color:var(--text-secondary);">CONFIRM PASSWORD</label>' +
        '<input id="' + ID + '-pw2" name="password2" type="' + (S.show ? 'text' : 'password') + '" autocomplete="new-password" minlength="6" data-f="pw2"' + attr('readonly', busy) + ' aria-invalid="' + (er.pw2 ? 'true' : 'false') + '" aria-describedby="' + ID + '-pw2e" class="f-in" style="' + INPUT + (er.pw2 ? 'var(--danger)' : 'var(--border)') + ';color:var(--text-primary);font-size:16px;padding:0 14px;outline:none;border-radius:0;">' +
        (er.pw2 ? errSpan(ID + '-pw2e', er.pw2) : '') + '</div>');
    }

    if (isSignup) out.push('<label style="display:flex;align-items:center;gap:12px;min-height:44px;cursor:pointer;"><input type="checkbox" name="marketing" data-f="marketing"' + attr('checked', S.marketing) + attr('disabled', busy) + ' style="width:18px;height:18px;margin:0;flex:0 0 auto;accent-color:#00E5A0;cursor:pointer;"><span style="font-size:13px;color:var(--text-secondary);">Email me product updates, Vinted tips and occasional offers.</span></label>');

    if (isLogin || isSignup || v === 'forgot' || v === 'reset' || v === 'verify') {
      var labels = { verify: ['CONFIRM EMAIL', 'CONFIRMING…'], login: ['LOG IN', 'LOGGING IN…'], signup: ['CREATE ACCOUNT', 'CREATING ACCOUNT…'], forgot: ['SEND RESET LINK', 'SENDING…'], reset: ['SAVE PASSWORD', 'SAVING…'] }[v];
      out.push('<div style="display:flex;flex-direction:column;gap:10px;"><button type="submit"' + attr('disabled', lock) + ' class="h-brand" style="height:52px;width:100%;background:var(--brand);color:var(--brand-fg);border:none;font-size:13px;letter-spacing:.1em;cursor:' + (busy ? 'progress' : 'pointer') + ';opacity:' + (busy ? 0.7 : 1) + ';">' + (busy ? labels[1] : labels[0]) + '</button>' +
        (st === 'slow' ? '<span role="status" style="font-size:12px;line-height:1.6;color:var(--warning);">Still working. Your connection looks slow; keep this tab open.</span>' : '') +
        (isSignup && LEGAL_LIVE ? '<span style="font-size:12px;line-height:1.6;color:var(--text-muted);">By creating an account you agree to the <a href="/terms">Terms</a> and <a href="/privacy">Privacy Policy</a>.</span>' : '') +
        '</div>');
    }

    if (v === 'forgot-sent' || v === 'verify') {
      var cd = S.cooldown, gmail = /@(gmail|googlemail)\.com$/i.test((S.email || '').trim());
      out.push('<div style="display:flex;flex-direction:column;gap:10px;">' +
        (gmail ? '<a href="https://mail.google.com/" target="_blank" rel="noopener" class="h-brandlink" style="' + BIGBTN + '">OPEN GMAIL</a>' : '') +
        '<button type="button" data-act="resend"' + attr('disabled', cd > 0 || busy) + ' class="h-ghost" style="height:52px;width:100%;background:var(--panel);border:1px solid var(--border-hover);color:' + (cd > 0 ? 'var(--text-muted)' : 'var(--text-primary)') + ';font-size:13px;letter-spacing:.08em;cursor:pointer;">' +
        (cd > 0 ? 'RESEND IN 0:' + String(cd).padStart(2, '0') : busy ? 'SENDING…' : (v === 'verify' ? 'RESEND EMAIL' : 'RESEND LINK')) + '</button>' +
        '<span style="font-size:12px;line-height:1.6;color:var(--text-muted);">Nothing yet? Check spam or Promotions. It can take a minute.</span></div>');
    }

    if (isLogin) out.push('<span style="font-size:13px;color:var(--text-secondary);">No account? <a href="/signup">Create one free</a></span>');
    if (isSignup) out.push('<span style="font-size:13px;color:var(--text-secondary);">Already have an account? <a href="/login">Log in</a></span>');
    if (v === 'forgot' || v === 'forgot-sent') out.push('<button type="button" data-act="login" style="align-self:flex-start;' + LINKBTN + 'min-height:44px;">← Back to log in</button>');
    if (v === 'verify') out.push('<button type="button" data-act="login" style="align-self:flex-start;' + LINKBTN + 'min-height:44px;">← Back to log in</button>');

    out.push('<span style="font-size:12px;line-height:1.6;color:var(--text-muted);padding-top:16px;border-top:1px solid var(--border);"><span style="color:var(--success);">✓</span> Never asks for your Vinted password - never logs into your account - only reads public listings.</span>');
    return out.join('');
  }

  function fieldEl(f) { return document.getElementById(ID + (f === 'email' ? '-em' : f === 'pw' ? '-pw' : f === 'code' ? '-code' : '-pw2')); }
  function focusField(f) { setTimeout(function () { var el = fieldEl(f); if (el) { try { el.focus(); } catch (e) {} } }, 0); }

  var IN_APP = /Instagram|FBAN|FBAV|FB_IAB|TikTok|musical_ly|Snapchat/i.test(navigator.userAgent || '');

  function render() {
    if (!S.ready) { form.innerHTML = ''; return; }
    var a = document.activeElement, inForm = a && form.contains(a), ss = null, se = null;
    var fid = inForm && a.id ? a.id : null, fact = inForm && !fid ? a.getAttribute('data-act') : null;
    if (fid) { try { ss = a.selectionStart; se = a.selectionEnd; } catch (e) {} }
    var busy = S.status === 'loading' || S.status === 'slow';
    form.setAttribute('aria-busy', busy ? 'true' : 'false');
    form.innerHTML = tpl();
    ['email', 'pw', 'pw2', 'code'].forEach(function (f) { var el = fieldEl(f); if (el) el.value = S[f] || ''; });
    if (fid) {
      var el = document.getElementById(fid);
      if (el) { try { el.focus({ preventScroll: true }); if (ss != null) el.setSelectionRange(ss, se); } catch (e) {} }
    } else if (fact) {
      var btn = form.querySelector('[data-act="' + fact + '"]');
      if (btn && !btn.disabled) { try { btn.focus({ preventScroll: true }); } catch (e) {} }
    }
    document.title = TITLES[S.view] || document.title;
  }

  /* As-you-type re-check after a failed submit, without rebuilding the
     inputs (a rebuild while typing can drop the phone keyboard). */
  function recheck() {
    var errors = validate(S.view, S.email, S.pw, S.pw2, S.code);
    S.errors = errors;
    [['email', '-eme'], ['pw', '-pwe'], ['pw2', '-pw2e'], ['code', '-codee']].forEach(function (p) {
      var el = fieldEl(p[0]); if (!el) return;
      var msg = errors[p[0]], box = el.closest('.au-fbox'), span = box && box.querySelector('.au-err');
      el.setAttribute('aria-invalid', msg ? 'true' : 'false');
      el.style.borderColor = msg ? 'var(--danger)' : 'var(--border)';
      if (msg && !span && box) box.insertAdjacentHTML('beforeend', errSpan(ID + p[1], msg));
      else if (msg && span) span.textContent = msg;
      else if (!msg && span) span.parentNode.removeChild(span);
      if (p[0] === 'pw') {
        var d = [msg ? ID + '-pwe' : '', (S.view === 'signup' || S.view === 'reset') ? ID + '-pwh' : ''].filter(Boolean).join(' ');
        if (d) el.setAttribute('aria-describedby', d); else el.removeAttribute('aria-describedby');
      }
    });
    if (!Object.keys(errors).length) S.status = 'idle';
  }

  /* ---------- events ---------- */
  form.addEventListener('submit', function (e) { e.preventDefault(); submit(); });
  form.addEventListener('input', function (e) {
    var f = e.target.getAttribute('data-f');
    if (!f || f === 'marketing') return;
    S[f] = e.target.value;
    if (S.view === 'verify' && f === 'email') {
      S.code = ''; var codeField = fieldEl('code'); if (codeField) codeField.value = '';
      pendingEmail(S.email.trim());
    }
    if (S.status === 'field-errors') recheck();
  });
  form.addEventListener('change', function (e) {
    if (e.target.getAttribute('data-f') === 'marketing') S.marketing = e.target.checked;
  });
  form.addEventListener('click', function (e) {
    var b = e.target.closest('[data-act]');
    if (!b || b.disabled) return;
    var act = b.getAttribute('data-act');
    if (act === 'google') google();
    else if (act === 'toggle-pw') { S.show = !S.show; render(); }
    else if (act === 'forgot') go('forgot', { pw: '', pw2: '' });
    else if (act === 'login') go('login', { code: '', pw: '' });
    else if (act === 'signup') go('signup', { pw: '' });
    else if (act === 'resend') resend();
    else if (act === 'resend-confirm') go('verify', { pw: '', code: '' });
    else if (act === 'exists-now') { clearTimeout(redirectT); toLoginExists(); }
  });

  /* ---------- right panel: live listings figure, same source as the homepage ---------- */
  (function () {
    var num = document.getElementById('au-listings'), asof = document.getElementById('au-asof');
    if (!num || !asof || !sb) return;
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'];
    try {
      sb.from('public_stats').select('value, as_of').eq('key', 'listings_matched').maybeSingle().then(function (res) {
        var row = res && res.data, when = row && new Date(row.as_of);
        if (!row || typeof row.value !== 'number' || row.value <= 0 || !when || isNaN(when.getTime())) return;
        num.textContent = String(row.value).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        asof.textContent = 'As of ' + when.getUTCDate() + ' ' + MONTHS[when.getUTCMonth()] + ' ' + when.getUTCFullYear();
      }, function () {});
    } catch (e) {}
  })();

  /* ---------- founding line (sign-up only; hidden if the endpoint doesn't answer) ---------- */
  if (PAGE === 'signup') {
    var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var ft = setTimeout(function () { if (ctl) ctl.abort(); }, 5000);
    fetch(FOUNDING_URL, ctl ? { signal: ctl.signal } : undefined)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && typeof d.remaining === 'number') { S.founding = Math.max(0, d.remaining); if (S.view === 'signup') render(); } })
      .catch(function () {})
      .then(function () { clearTimeout(ft); });
  }

  /* ---------- boot ---------- */
  function urlError() {
    var err = hs.get('error') || qs.get('error');
    if (!err) return null;
    return { code: hs.get('error_code') || qs.get('error_code') || err, text: hs.get('error_description') || qs.get('error_description') || err };
  }
  function cleanUrl(keep) {
    try { history.replaceState(null, '', location.pathname + (keep || '')); } catch (e) {}
  }

  if (!sb) {
    S.ready = true; S.status = 'network'; render();
    return;
  }

  var uErr = urlError();

  if (PAGE === 'reset') {
    (async function () {
      var ok = false;
      if (!uErr) {
        try {
          var code = qs.get('code'), th = qs.get('token_hash');
          if (code) { var x = await sb.auth.exchangeCodeForSession(code); ok = !x.error; }
          else if (th) { var y = await sb.auth.verifyOtp({ token_hash: th, type: 'recovery' }); ok = !y.error; }
          if (!ok) { var s = await sb.auth.getSession(); ok = !!(s.data && s.data.session); }
        } catch (e) { ok = false; }
      }
      cleanUrl();
      S.ready = true; S.view = ok ? 'reset' : 'reset-expired';
      render();
    })();
    return;
  }

  // A verification intent must never fall back to an unrelated cached session.
  if (qs.get('verify') === '1' && !uErr && !qs.get('token_hash')) {
    go('verify', { email: pendingEmail(), ready: true });
    return;
  }
  S.ready = false; render();

  (async function () {
    if (uErr) {
      cleanUrl(plan && PLAN_NAMES[plan] ? '?plan=' + plan : '');
      S.ready = true;
      if (/otp_expired|expired|token.*not.*found|invalid.*link/i.test(uErr.code + ' ' + uErr.text)) {
        go('verify', { email: pendingEmail(), code: '', status: 'link-expired' }); return;
      }
      if (S.view !== 'login') go('login');
      if (uErr.code === 'access_denied' && !/expired/i.test(uErr.text)) {
        S.status = 'error'; S.errText = 'Google sign-in was cancelled. Try again, or use your email.';
      } else {
        S.status = 'error'; S.errText = "Sign-in didn't complete (" + uErr.text.replace(/\+/g, ' ') + '). Try again, or use your email.';
      }
      render();
      return;
    }
    var th = qs.get('token_hash'), type = qs.get('type');
    var sess = null;
    if (th) {
      var result;
      try {
        if (!/^(email|signup|magiclink)$/.test(type || '')) throw new Error('Unsupported confirmation type');
        result = await sb.auth.verifyOtp({ token_hash: th, type: type });
      } catch (e) { result = { error: e }; }
      cleanUrl();
      sess = result.data && result.data.session;
      if (result.error || !sess || !sess.user || !sess.user.email_confirmed_at) {
        go('verify', { email: pendingEmail(), ready: true }); verificationFailed(result.error); return;
      }
      pendingEmail('');
    }
    var oauthReturn = /access_token/.test(hs.toString());
    if (!th) {
      try {
        var r = await sb.auth.getSession();
        if (r.error) throw r.error;
        sess = r.data && r.data.session;
      } catch (e) { S.ready = true; fail(classify(e), e); render(); cleanUrl(); return; }
    }
    S.ready = true; render();
    if (location.hash && /access_token|refresh_token/.test(location.hash)) cleanUrl();
    if (sess && sess.user) {
      /* Google sign-ups come back here from Google; count a brand-new account as a sign-up
         (email sign-ups are counted in signup()). */
      var created = Date.parse(sess.user.created_at || '');
      if (oauthReturn && created && Date.now() - created < 15 * 60 * 1000) {
        track('sign_up', { method: 'google' });
        /* Tags from the return address set in google(): same fields as an email sign-up. */
        var md = sess.user.user_metadata || {}, add = md.utm_source ? {} : campaignTags(qs), retAff = qs.get('a');
        var hi = huntIntent();
        if (hi && !md.entry_hunt) add.entry_hunt = hi;
        var retEp = entryPage(qs);
        if (retEp && !md.entry_page) add.entry_page = retEp;
        if (retAff && /^[A-Za-z0-9_.-]{1,60}$/.test(retAff) && !md.whop_aff) add.whop_aff = retAff;
        if (Object.keys(add).length) { try { await sb.auth.updateUser({ data: add }); } catch (e) {} }
      }
      if (PAGE === 'signup') { if (sess.user.email) lsSet(LAST_EMAIL_KEY, sess.user.email); location.replace('/dashboard'); return; }
      openDashboard(sess.user.email || '');
      return;
    }
    if (PAGE === 'login' && qs.get('reason') === 'expired') {
      S.email = lsGet(LAST_EMAIL_KEY) || '';
      S.status = 'expired'; render();
      if (S.email) focusField('pw');
    }
  })();

  /* A request that timed out on our side can still land; follow it. */
  try {
    sb.auth.onAuthStateChange(function (event, session) {
      if (event === 'SIGNED_IN' && session && PAGE !== 'reset' && S.view === 'login' && S.status !== 'signed-in' && (S.status === 'network' || S.status === 'loading' || S.status === 'slow')) {
        openDashboard(session.user && session.user.email);
      }
    });
  } catch (e) {}
})();
