/* SNYPD in-app feedback questions (9 Nov 2026; website repo outreach/47, migration 081).
 *
 *   SnypdFeedback.pick(state) -> { id, qs: [question ids] } | null      pure, no DOM (tests call it in node)
 *     state: { done: [ids] | undefined, plan, profile, now, firstFindAt, activeDays14, lastRoundAt, force }
 *   SnypdFeedback.mount({ sb, boot, plan, profile }) -> shows at most one popup per visit
 *
 * Shows nothing when dashboard_boot() has no feedback_done key (migration 081 not applied) or the RPC fails.
 * Never on page load: after ~20 s or the first interaction, never while the first-hunt wizard or any sheet is open.
 * Closing = skipped (recorded, does not delay the next question). Pure ASCII (dashboard.html carries a BOM).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdFeedback = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var H = 36e5, D = 864e5;
  var LEAD = ['A', 'B1', 'C', 'D', 'E1', 'G', 'H'];

  var Q = {
    A: { t: 'What do you want SNYPD to do for you?', a: [['one_item', 'Find one specific item'], ['deals', 'Good deals for myself'], ['reselling', 'Reselling'], ['looking', 'Just looking']] },
    B1: { t: "If SNYPD didn't exist, how would you find these items?", a: [['saved_searches', 'Vinted saved searches'], ['refresh', 'Refresh Vinted myself'], ['other_app', 'Another app or bot'], ['wouldnt', "Wouldn't bother"]], text: { on: 'other_app', ph: 'Which one?' } },
    C: { t: "What's the main reason you haven't upgraded?", a: [['too_expensive', 'Too expensive'], ['one_item', 'Only needed one item'], ['no_alerts', "Didn't get alerts"], ['nothing_found', "Didn't find anything"], ['found_it', 'Already found it'], ['other_app', 'Using another app'], ['other', 'Other']], text: { ph: 'What would make it worth paying for? (optional)' } },
    B2: { t: 'What would SNYPD be worth to you per month?', a: [['0', '\u20ac0'], ['0_3', 'Up to \u20ac3'], ['3_6', '\u20ac3-6'], ['6_15', '\u20ac6-15'], ['15_plus', '\u20ac15+']] },
    D: { t: 'How would you feel if you could no longer use SNYPD?', a: [['very', 'Very disappointed'], ['somewhat', 'Somewhat disappointed'], ['not', 'Not disappointed']] },
    D_text: { t: "What's the main benefit you get from SNYPD?", free: true },
    E1: { t: 'Which matters most to you?', a: [['speed', 'Alert speed'], ['price_check', 'Price check on each find'], ['board', 'Market board'], ['report', 'Weekly hunt report'], ['calm', 'Calm or cheap-only alerts']] },
    E2: { t: 'What should we build next?', a: [['app', 'Phone app'], ['tracker', 'Stock & profit tracker'], ['telegram', 'Telegram alerts'], ['price_drop', 'Price-drop alerts'], ['other', 'Other']] },
    G: { t: 'What almost stopped you from buying?', a: [['price', 'Price'], ['unsure', 'Unsure it works'], ['checkout', 'Checkout'], ['trial_short', 'Trial too short'], ['nothing', 'Nothing']] },
    F: { t: 'What type of people would benefit most from SNYPD?', free: true },
    H: { t: 'Would you pay more for a price check on any Vinted item, without a hunt?', a: [['yes', 'Yes'], ['maybe', 'Maybe'], ['no', 'No']] },
    I: { t: 'How do you track what you buy and sell?', a: [['spreadsheet', 'Spreadsheet'], ['notes', 'Notes'], ['app', 'An app'], ['none', 'Not at all']] }
  };

  function trialEnd(p) {
    var e = Date.parse((p && p.trial_ends_at) || '');
    if (isFinite(e)) return e;
    var s = Date.parse((p && p.free_trial_started_at) || '');
    return isFinite(s) ? s + 7 * D : NaN;
  }
  function has(done, id) { return done.indexOf(id) >= 0; }

  // Rounds for paid accounts and running trials: fixed order, 2 questions each, >= 7 days apart.
  function nextRound(done, s, paying) {
    var rounds = [];
    if ((Number(s.activeDays14) || 0) >= 2) rounds.push(['D', 'D_text']);
    rounds.push(['E1', 'E2']);
    rounds.push(paying ? ['G', 'F'] : ['F']);
    rounds.push(['H', 'I']);
    for (var i = 0; i < rounds.length; i++) {
      var left = rounds[i].filter(function (q) { return !has(done, q); });
      if (left.length) return left;
    }
    return null;
  }

  function pick(s) {
    if (!s || !Array.isArray(s.done)) return null;               // migration 081 not live: show nothing
    var done = s.done, now = s.now || Date.now(), p = s.profile || {};
    if (s.force && Q[s.force]) return { id: s.force, qs: s.force === 'D' ? ['D', 'D_text'] : [s.force] };
    var plan = String(s.plan || 'free').toLowerCase();
    var paying = plan !== 'free';
    var start = Date.parse(p.free_trial_started_at || '');
    var end = trialEnd(p);
    if (!paying && isFinite(start) && isFinite(end)) {
      if (now >= end) {
        return (now < end + 3 * D && !has(done, 'C')) ? { id: 'C', qs: ['C'] } : null;
      }
      var ff = Date.parse(s.firstFindAt || '');
      if (!has(done, 'A') && isFinite(ff) && now - ff >= 2 * H) return { id: 'A', qs: ['A'] };
      if (!has(done, 'B1') && now - start >= 24 * H && now - start < 48 * H) return { id: 'B1', qs: ['B1'] };
      // Day 1-2 belong to A and B1: no paid-style round while they are still pending.
      if (now - start < 48 * H && (!has(done, 'A') || !has(done, 'B1'))) return null;
    } else if (!paying) {
      return null;                                                // free account, no trial: nothing to ask
    }
    var last = Number(s.lastRoundAt) || 0;
    if (last && now - last < 7 * D) return null;
    var r = nextRound(done, s, paying);
    return r ? { id: r[0], qs: r } : null;
  }

  // ---- DOM -----------------------------------------------------------------------------------------------
  var CSS = '.fb-ov{position:fixed;inset:0;z-index:600;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:24px}' +
    '.fb-box{width:100%;max-width:520px;background:var(--panel);border:1px solid var(--border);padding:28px;box-sizing:border-box;max-height:90vh;overflow-y:auto}' +
    '.fb-hd{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}' +
    '.fb-ey{font-size:11px;letter-spacing:.1em;color:var(--text-muted);text-transform:uppercase;margin-bottom:10px}' +
    '.fb-t{font-size:18px;font-weight:500;margin:0 0 16px;color:var(--text-primary)}' +
    '.fb-x{flex:none;width:40px;height:40px;font:inherit;font-size:18px;color:var(--text-secondary);background:transparent;border:1px solid var(--border3,#3A4147);cursor:pointer}' +
    '.fb-opts{display:flex;flex-direction:column;gap:8px}' +
    '.fb-o{text-align:left;font:inherit;font-size:14px;color:var(--text-primary);background:transparent;border:1px solid var(--border);padding:12px 14px;cursor:pointer;min-height:44px}' +
    '.fb-o[aria-pressed="true"]{border-color:var(--success);color:var(--success)}' +
    '.fb-ta{width:100%;box-sizing:border-box;min-height:72px;margin-top:12px;font:inherit;font-size:14px;color:var(--text-primary);background:transparent;border:1px solid var(--border);padding:10px}' +
    '.fb-ft{display:flex;justify-content:space-between;gap:10px;margin-top:18px;flex-wrap:wrap}' +
    '.fb-ft .btn{min-height:44px}.fb-msg{font-size:13px;color:var(--text-muted);margin:8px 0 0;line-height:1.5}' +
    '@media (max-width:600px){.fb-ov{align-items:flex-end;padding:0;background:rgba(8,9,10,.62)}' +
    '.fb-box{max-width:none;border-left:0;border-right:0;border-bottom:0;padding:20px 16px;padding-bottom:max(24px,env(safe-area-inset-bottom));box-shadow:0 -18px 50px rgba(0,0,0,.65);max-height:85dvh}}';

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function busy() {
    var nodes = document.querySelectorAll('.wiz-overlay,.mr-sheet');
    for (var i = 0; i < nodes.length; i++) {
      try { if (getComputedStyle(nodes[i]).display !== 'none') return true; } catch (e) {}
    }
    return false;
  }
  function store(k, v) {
    try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {}
    return null;
  }
  function seen(v) {
    try { if (v) sessionStorage.setItem('snypd_fb_seen', '1'); return !!sessionStorage.getItem('snypd_fb_seen'); } catch (e) { return !!v; }
  }

  // Next step after C (plan 47): every answer leads somewhere.
  function nextStep(answer) {
    var S = window.SNYPD || {};
    if (answer === 'too_expensive') return { msg: 'Solo keeps one search running 24/7. With code STAY50 your first month is half price.', label: 'See Solo with STAY50', href: '/plans?promo=STAY50' };
    if (answer === 'one_item') return { msg: 'For one item, a 30-day Hunt Pass is \u20ac3.99 once, no subscription.', label: 'See the Hunt Pass', href: '/plans' };
    if (answer === 'no_alerts') return { msg: 'Alerts need permission on this device. Turn them on here, it takes a few seconds.', label: 'Turn on alerts', run: function () { if (typeof S.enableAlerts === 'function') S.enableAlerts(); } };
    if (answer === 'nothing_found') return { msg: 'Vinted only shows listings that contain every word you typed. A quick check of your hunt words often fixes this.', label: 'Check my hunt words', run: function () { if (typeof S.switchView === 'function') S.switchView('filters'); } };
    return { msg: 'Thank you, this helps us a lot.' };
  }

  function mount(o) {
    if (!o || !o.sb || !o.boot || typeof document === 'undefined') return;
    var params;
    try { params = new URLSearchParams(location.search); } catch (e) { params = null; }
    var force = params && params.get('fb');
    if (seen() && !force) return;
    var st = {
      done: o.boot.feedback_done, plan: o.plan, profile: o.profile || o.boot.profile || {},
      firstFindAt: (o.boot.feedback_signals || {}).first_find_at, activeDays14: (o.boot.feedback_signals || {}).active_days_14,
      lastRoundAt: Number(store('snypd_fb_round_at')) || 0, force: force, now: Date.now()
    };
    var choice = pick(st);
    if (!choice) return;

    var fired = false;
    function go() {
      if (fired) return;
      if (busy() || document.hidden) { setTimeout(go, 5000); return; }
      fired = true;
      ['click', 'keydown', 'scroll'].forEach(function (ev) { window.removeEventListener(ev, early, true); });
      show(o.sb, choice, force && params.get('a'), force && params.get('src') === 'email');
    }
    function early() { setTimeout(go, 1500); }
    ['click', 'keydown', 'scroll'].forEach(function (ev) { window.addEventListener(ev, early, { capture: true, once: true, passive: true }); });
    setTimeout(go, force ? 300 : 20000);
  }

  function show(sb, choice, preset, fromEmail) {
    seen(true);
    if (!document.getElementById('fb-css')) { var s = el('style'); s.id = 'fb-css'; s.textContent = CSS; document.head.appendChild(s); }
    var ov = el('div', 'fb-ov'); ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
    var box = el('div', 'fb-box'); ov.appendChild(box);
    var queue = choice.qs.slice(), lead = choice.id, answeredAny = false;

    function send(q, answer, detail, skipped) {
      return sb.rpc('feedback_submit', { p_question: q, p_answer: answer || null, p_detail: detail || null, p_skipped: !!skipped, p_source: fromEmail ? 'email' : 'dashboard' })
        .then(function (r) { if (r && r.error) throw r.error; return r && r.data; })
        .catch(function (e) { console.error('SNYPD feedback: save failed', e); return null; });
    }
    function close(skip) {
      if (skip && !answeredAny) send(queue[0] || lead, null, null, true);
      if (LEAD.indexOf(lead) >= 0 && ['D', 'E1', 'G', 'H', 'F'].indexOf(lead) >= 0) store('snypd_fb_round_at', String(Date.now()));
      if (ov.parentNode) ov.parentNode.removeChild(ov);
      document.removeEventListener('keydown', esc);
    }
    function esc(e) { if (e.key === 'Escape') close(true); }
    document.addEventListener('keydown', esc);

    function header(title, eyebrow) {
      box.innerHTML = '';
      var hd = el('div', 'fb-hd'), l = el('div');
      l.appendChild(el('div', 'fb-ey', eyebrow || 'Quick question'));
      l.appendChild(el('h2', 'fb-t', title));
      var x = el('button', 'fb-x', '\u00d7'); x.type = 'button'; x.setAttribute('aria-label', 'Close');
      x.addEventListener('click', function () { close(true); });
      hd.appendChild(l); hd.appendChild(x); box.appendChild(hd);
    }

    function render() {
      var q = queue[0];
      if (!q) return done(null, 0);
      var def = Q[q];
      header(def.t);
      var sel = null, ta = null;
      if (def.a) {
        var opts = el('div', 'fb-opts');
        def.a.forEach(function (a) {
          var b = el('button', 'fb-o', a[1]); b.type = 'button'; b.setAttribute('aria-pressed', 'false'); b.setAttribute('data-a', a[0]);
          b.addEventListener('click', function () {
            sel = a[0];
            Array.prototype.forEach.call(opts.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
            if (def.text) ta.style.display = (!def.text.on || def.text.on === sel) ? '' : 'none';
            ok.disabled = false;
          });
          opts.appendChild(b);
        });
        box.appendChild(opts);
      }
      if (def.text || def.free) {
        ta = el('textarea', 'fb-ta'); ta.maxLength = 1000;
        ta.placeholder = def.free ? 'Your answer' : def.text.ph;
        if (def.text && def.text.on) ta.style.display = 'none';
        if (def.free) ta.addEventListener('input', function () { ok.disabled = !ta.value.trim(); });
        box.appendChild(ta);
      }
      var ft = el('div', 'fb-ft');
      var later = el('button', 'btn btn-ghost', 'Not now'); later.type = 'button';
      later.addEventListener('click', function () { close(true); });
      var ok = el('button', 'btn', 'Send'); ok.type = 'button'; ok.disabled = true;
      ok.addEventListener('click', function () {
        ok.disabled = true;
        var detail = ta && ta.style.display !== 'none' ? ta.value.trim() : '';
        var first = !answeredAny; answeredAny = true;
        send(q, def.free ? null : sel, detail, false).then(function (r) {
          queue.shift();
          var xp = first && r && r.xp ? r.xp : 0;
          if (q === 'C') {
            if (sel === 'too_expensive') queue.unshift('B2');
            if (queue.length) { cAnswer = sel; cXp = xp; return render(); }
            return done(sel, xp);
          }
          if (q === 'B2') return done(cAnswer, cXp);
          if (queue.length) { lastXp = lastXp || xp; return render(); }
          done(null, lastXp || xp);
        });
      });
      ft.appendChild(later); ft.appendChild(ok); box.appendChild(ft);
      if (preset && def.a && q === lead) {
        var pb = box.querySelector('[data-a="' + String(preset).replace(/[^a-z0-9_]/g, '') + '"]');
        if (pb) pb.click();
        preset = null;
      }
    }
    var cAnswer = null, cXp = 0, lastXp = 0;

    function done(cAns, xp) {
      header('Thank you', 'Saved');
      var step = lead === 'C' ? nextStep(cAns) : { msg: 'Thank you, this helps us a lot.' };
      box.appendChild(el('p', 'fb-msg', step.msg));
      if (xp) box.appendChild(el('p', 'fb-msg', '+' + xp + ' XP'));
      if (xp && window.SNYPD && typeof window.SNYPD.loadStreakAndXP === 'function') { try { window.SNYPD.loadStreakAndXP(); } catch (e) {} }
      var ft = el('div', 'fb-ft');
      var c = el('button', 'btn btn-ghost', 'Close'); c.type = 'button';
      c.addEventListener('click', function () { close(false); });
      ft.appendChild(c);
      if (step.label) {
        var a = el(step.href ? 'a' : 'button', 'btn', step.label);
        if (step.href) a.href = step.href; else { a.type = 'button'; a.addEventListener('click', function () { close(false); step.run(); }); }
        ft.appendChild(a);
      }
      box.appendChild(ft);
    }

    // Email link (outreach/47): the answer arrives preselected and is saved only when the person taps Send here.
    // Mail scanners open links but never tap, so they cannot answer for anyone.
    render();
    document.body.appendChild(ov);
  }

  return { pick: pick, mount: mount, questions: Q, _nextStep: nextStep };
}));
