/* SNYPD cookie consent.
 *
 * Nothing optional runs until the visitor says yes. Pages keep their inline
 * gtag()/dataLayer stubs - those only queue calls in memory - but the loaders
 * that actually send data live here and run after consent:
 *
 *   analytics  -> Google Analytics 4 (gtag.js) and, where a page had it,
 *                 Google Tag Manager (whose only tags are the same GA4 property)
 *   marketing  -> the Whop pixel, the Meta Pixel (dataset 1104479635308667,
 *                 Facebook/Instagram ads) and the stored referral code (snypd_ref)
 *
 * Each page declares what it loaded before this existed, so behaviour after
 * consent is unchanged page by page:
 *   <script src="/assets/consent.js" data-ga="G-..." data-gtm="GTM-..." data-whop="biz_..."></script>
 *
 * The choice is kept in localStorage ("snypd_consent") with a timestamp and a
 * version. Bump VERSION when the categories change, so everyone is asked again.
 * Accept all and Reject all are the same size and style on purpose: refusing
 * must be as easy as agreeing.
 *
 * Public API: window.SNYPDConsent.get() / .open() / .whenGranted(cat, fn)
 * This file must stay pure ASCII (account.html is a byte-sensitive page).
 */
(function () {
  if (window.SNYPDConsent) return;

  var VERSION = 2; /* 2: Meta Pixel added to marketing (Oct 2026) */
  var KEY = 'snypd_consent';
  var me = document.currentScript;
  var cfg = {
    ga: me && me.getAttribute('data-ga'),
    gtm: me && me.getAttribute('data-gtm'),
    whop: me && me.getAttribute('data-whop'),
    meta: (me && me.getAttribute('data-meta')) || '1104479635308667'
  };

  /* Google Consent Mode v2 (Google requires it for ads measured in the EEA).
     Every page starts with all four Google signals denied; apply() grants
     them per category: analytics -> analytics_storage, marketing -> the three
     ad signals. Google's scripts still only load after consent (runAnalytics).
     This runs before the pages' inline gtag('config') because consent.js is
     included above it on every page. */
  window.dataLayer = window.dataLayer || [];
  function gConsent() { window.dataLayer.push(arguments); }
  gConsent('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', wait_for_update: 500
  });

  var loaded = { analytics: false, marketing: false };
  var waiting = { analytics: [], marketing: [] };

  function read() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (c && c.v === VERSION && typeof c.analytics === 'boolean' && typeof c.marketing === 'boolean') return c;
    } catch (e) {}
    return null;
  }

  function write(analytics, marketing) {
    var c = { v: VERSION, analytics: !!analytics, marketing: !!marketing, at: new Date().toISOString() };
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
    return c;
  }

  function addScript(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    (document.head || document.documentElement).appendChild(s);
  }

  function runAnalytics() {
    if (loaded.analytics) return;
    loaded.analytics = true;
    window.dataLayer = window.dataLayer || [];
    if (cfg.ga) addScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(cfg.ga));
    if (cfg.gtm) {
      window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
      addScript('https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(cfg.gtm));
    }
  }

  function runMarketing() {
    if (loaded.marketing) return;
    loaded.marketing = true;
    if (cfg.meta) {
      /* Meta's own base code, unchanged. It is only ever added after consent, so
         nothing reaches Meta before the visitor says yes. */
      !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
      /* No automatic events: Meta would otherwise also report button clicks (even
         the Reject click) and page metadata. Only PageView + CompleteRegistration. */
      window.fbq('set', 'autoConfig', false, cfg.meta);
      window.fbq('init', cfg.meta);
      window.fbq('track', 'PageView');
    }
    if (!cfg.whop) return;
    /* The Whop pixel's own loader, unchanged, followed by the same two calls
       every page made before. */
    !function(w,d,s,u,n,a,b){if(w[n])return;a=w[n]={q:[],t:+new Date,s:[],o:u,track:function(){a.q.push([+new Date].concat([].slice.call(arguments)))},setScope:function(){a.s=[].slice.call(arguments).filter(function(x){return typeof x==="string"});a.q.push([+new Date,"setScope"].concat(a.s))},scope:function(){var c=[].slice.call(arguments);return{track:function(){a.q.push([+new Date].concat([].slice.call(arguments)).concat([{__scope:c}]))}}}};b=d.createElement(s);b.async=1;b.src=u+"/s.js";d.getElementsByTagName(s)[0].parentNode.insertBefore(b,d.getElementsByTagName(s)[0])}(window,document,"script","https://t.whop.tw","whop");
    window.whop.setScope(cfg.whop);
    window.whop.track('page');
  }

  function flush(cat) {
    var list = waiting[cat];
    waiting[cat] = [];
    for (var i = 0; i < list.length; i++) { try { list[i](); } catch (e) {} }
  }

  function apply(c) {
    gConsent('consent', 'update', {
      analytics_storage: c.analytics ? 'granted' : 'denied',
      ad_storage: c.marketing ? 'granted' : 'denied',
      ad_user_data: c.marketing ? 'granted' : 'denied',
      ad_personalization: c.marketing ? 'granted' : 'denied'
    });
    if (c.analytics) { runAnalytics(); flush('analytics'); }
    if (c.marketing) { runMarketing(); flush('marketing'); }
  }

  /* Withdrawing consent must actually remove what was stored. */
  function clearCookie(name) {
    var host = location.hostname;
    var parts = host.split('.');
    var domains = ['', host, '.' + host];
    if (parts.length > 2) domains.push('.' + parts.slice(-2).join('.'));
    for (var i = 0; i < domains.length; i++) {
      document.cookie = name + '=; Max-Age=0; path=/' + (domains[i] ? '; domain=' + domains[i] : '');
    }
  }
  function cookieNames() {
    return document.cookie.split(';').map(function (x) { return x.split('=')[0].replace(/^\s+|\s+$/g, ''); }).filter(Boolean);
  }
  function wipe(analytics, marketing) {
    var names = cookieNames();
    for (var i = 0; i < names.length; i++) {
      var n = names[i];
      if (analytics && (n === '_ga' || n.indexOf('_ga_') === 0 || n === '_gid')) clearCookie(n);
      if (marketing && (n.indexOf('_wuid') === 0 || n === '_fbp' || n === '_fbc')) clearCookie(n);
    }
    if (marketing) {
      ['_wuid', '_wuid_link_domain', '_wsc', '_wsc_probed_at', '_wfp', 'snypd_ref'].forEach(function (k) {
        try { localStorage.removeItem(k); } catch (e) {}
      });
      try { sessionStorage.removeItem('_wsc_probed'); } catch (e) {}
    }
  }

  function save(analytics, marketing) {
    var before = read();
    var c = write(analytics, marketing);
    /* Lets a page that shows the current choice (cookies.html) update itself. */
    try { document.dispatchEvent(new CustomEvent('snypd:consent', { detail: c })); } catch (e) {}
    closeBanner();
    closeSettings();
    var revokedA = before && before.analytics && !c.analytics;
    var revokedM = before && before.marketing && !c.marketing;
    if (revokedA || revokedM) {
      wipe(revokedA, revokedM);
      /* Scripts already running cannot be unloaded; a reload is the only way
         to make sure they stop. */
      if ((revokedA && loaded.analytics) || (revokedM && loaded.marketing)) { location.reload(); return; }
    }
    apply(c);
  }

  /* ---------- UI (homepage v5 look: flat, square, DM Mono) ---------- */
  var CSS =
    '.snc-bar{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;background:#0C0C0D;border-top:1px solid #26262A;' +
      'font-family:"DM Mono",ui-monospace,monospace;color:#E8EAEB;padding:16px 20px calc(16px + env(safe-area-inset-bottom));box-shadow:0 -10px 40px rgba(0,0,0,.6);}' +
    '.snc-in{max-width:1320px;margin:0 auto;display:flex;flex-wrap:wrap;align-items:center;gap:14px 24px;}' +
    '.snc-txt{flex:1 1 420px;margin:0;font-size:12.5px;line-height:1.6;color:#8B9094;}' +
    '.snc-txt b{font-weight:400;color:#FFFFFF;}' +
    '.snc-txt a,.snc-panel a{color:#00E5A0;text-decoration:none;}' +
    '.snc-txt a:hover,.snc-panel a:hover{color:#57FFC8;}' +
    '.snc-btns{display:flex;flex-wrap:wrap;gap:10px;}' +
    '.snc-btn{font-family:inherit;font-size:12px;letter-spacing:.09em;color:#FFFFFF;background:#141416;border:1px solid #3A3A40;padding:13px 18px;min-height:46px;cursor:pointer;border-radius:0;}' +
    '.snc-btn:hover{background:#1C1C1F;border-color:#55555C;}' +
    '.snc-link{font-family:inherit;font-size:12px;letter-spacing:.09em;color:#00E5A0;background:none;border:0;padding:13px 4px;min-height:46px;cursor:pointer;}' +
    '.snc-link:hover{color:#57FFC8;}' +
    '.snc-btn:focus-visible,.snc-link:focus-visible,.snc-sw input:focus-visible+span{outline:2px solid #00E5A0;outline-offset:2px;}' +
    '.snc-ov{position:fixed;inset:0;z-index:2147483001;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:16px;}' +
    '.snc-panel{width:100%;max-width:560px;max-height:calc(100vh - 32px);overflow:auto;background:#0A0A0B;border:1px solid #26262A;' +
      'font-family:"DM Mono",ui-monospace,monospace;color:#E8EAEB;box-shadow:0 20px 70px rgba(0,0,0,.7);}' +
    '.snc-hd{padding:20px 22px 16px;border-bottom:1px solid #1D1D20;}' +
    '.snc-hd h2{margin:0 0 8px;font-family:"Cabinet Grotesk","DM Mono",sans-serif;font-weight:900;font-size:26px;letter-spacing:-.03em;line-height:1;color:#FFFFFF;}' +
    '.snc-hd p{margin:0;font-size:12px;line-height:1.6;color:#8B9094;}' +
    '.snc-row{display:flex;gap:16px;align-items:flex-start;justify-content:space-between;padding:16px 22px;border-bottom:1px solid #1D1D20;}' +
    '.snc-row h3{margin:0 0 5px;font-size:12.5px;font-weight:400;letter-spacing:.06em;color:#FFFFFF;}' +
    '.snc-row p{margin:0;font-size:12px;line-height:1.6;color:#8B9094;}' +
    '.snc-sw{position:relative;flex:0 0 auto;display:inline-block;width:46px;height:26px;margin-top:2px;}' +
    '.snc-sw input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer;}' +
    '.snc-sw span{position:absolute;inset:0;background:#141416;border:1px solid #3A3A40;pointer-events:none;}' +
    '.snc-sw span:after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;background:#8B9094;}' +
    '.snc-sw input:checked+span{background:rgba(0,229,160,.14);border-color:#00E5A0;}' +
    '.snc-sw input:checked+span:after{left:23px;background:#00E5A0;}' +
    '.snc-sw input:disabled{cursor:not-allowed;}' +
    '.snc-sw input:disabled+span{opacity:.6;}' +
    '.snc-ft{display:flex;flex-wrap:wrap;gap:10px;padding:16px 22px 20px;}' +
    '@media (max-width:699.98px){.snc-btns{width:100%;}.snc-btns .snc-btn{flex:1 1 0;white-space:nowrap;}.snc-btns .snc-link{flex:1 1 100%;text-align:left;min-height:40px;padding:8px 0;}}' +
    '@media (prefers-reduced-motion:reduce){.snc-bar,.snc-ov{transition:none;}}';

  var bar = null, ov = null, lastFocus = null;

  function injectCss() {
    if (document.getElementById('snc-css')) return;
    var st = document.createElement('style');
    st.id = 'snc-css';
    st.appendChild(document.createTextNode(CSS));
    document.head.appendChild(st);
  }

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function showBanner() {
    if (bar) return;
    injectCss();
    bar = el('div', 'snc-bar');
    bar.setAttribute('role', 'region');
    bar.setAttribute('aria-label', 'Cookie choices');
    bar.innerHTML =
      '<div class="snc-in">' +
        '<p class="snc-txt"><b>Cookies.</b> SNYPD only stores what it needs to keep you signed in. ' +
        'With your OK we also use Google Analytics to see how the site is used, and the Whop pixel and Meta Pixel to measure sign-ups from ads and partner links. ' +
        '<a href="/cookies">Cookie policy</a></p>' +
        '<div class="snc-btns">' +
          '<button type="button" class="snc-btn" data-snc="reject">REJECT ALL</button>' +
          '<button type="button" class="snc-btn" data-snc="accept">ACCEPT ALL</button>' +
          '<button type="button" class="snc-link" data-snc="settings">SETTINGS</button>' +
        '</div>' +
      '</div>';
    bar.addEventListener('click', function (e) {
      var t = e.target.closest && e.target.closest('[data-snc]');
      if (!t) return;
      var a = t.getAttribute('data-snc');
      if (a === 'reject') save(false, false);
      else if (a === 'accept') save(true, true);
      else if (a === 'settings') openSettings();
    });
    document.body.appendChild(bar);
    // Room under the page so the bar never hides the last buttons (it covered
    // CREATE ACCOUNT on /signup at 390px, 2026-10-07).
    document.body.style.paddingBottom = bar.offsetHeight + 'px';
    /* The bar is fixed to the bottom, so without room for it the end of the
       page - including the footer's Privacy/Cookies links - sits under it. */
    prevPad = document.body.style.paddingBottom;
    padForBar();
    window.addEventListener('resize', padForBar);
  }

  var prevPad = '';
  function padForBar() {
    if (bar) document.body.style.paddingBottom = bar.offsetHeight + 'px';
  }

  function closeBanner() {
    if (!bar) return;
    if (bar.parentNode) bar.parentNode.removeChild(bar);
    bar = null;
    document.body.style.paddingBottom = '';
    window.removeEventListener('resize', padForBar);
    document.body.style.paddingBottom = prevPad;
  }

  function row(id, title, text, checked, locked) {
    return '<div class="snc-row"><div><h3 id="' + id + '-t">' + title + '</h3><p>' + text + '</p></div>' +
      '<label class="snc-sw"><input type="checkbox" id="' + id + '" aria-labelledby="' + id + '-t"' +
      (checked ? ' checked' : '') + (locked ? ' disabled' : '') + '><span></span></label></div>';
  }

  function onKey(e) {
    if (e.key === 'Escape') { e.preventDefault(); closeSettings(); }
  }

  function openSettings() {
    injectCss();
    closeSettings();
    lastFocus = document.activeElement;
    var c = read() || { analytics: false, marketing: false };
    ov = el('div', 'snc-ov');
    ov.innerHTML =
      '<div class="snc-panel" role="dialog" aria-modal="true" aria-labelledby="snc-title">' +
        '<div class="snc-hd"><h2 id="snc-title">Cookie settings</h2>' +
          '<p>Choose what SNYPD may store on this device. You can change it any time on the cookie policy page or with the "Cookie settings" link in the homepage footer. ' +
          '<a href="/cookies">Full list of cookies</a></p></div>' +
        row('snc-nec', 'NECESSARY', 'Keeps you signed in, remembers the plan you picked before checkout and your dashboard settings. The site cannot work without these, so they are always on.', true, true) +
        row('snc-an', 'ANALYTICS', 'Google Analytics 4: which pages are visited and how people find SNYPD. Google receives your IP address and browser details.', c.analytics, false) +
        row('snc-mk', 'MARKETING', 'Whop pixel and Meta Pixel: measure sign-ups that came from ads (including Facebook and Instagram ads) and partner links. Meta receives your IP address, browser details and the SNYPD pages you visit. Also remembers the partner code in a partner link you arrived through.', c.marketing, false) +
        '<div class="snc-ft">' +
          '<button type="button" class="snc-btn" data-snc="save">SAVE CHOICES</button>' +
          '<button type="button" class="snc-btn" data-snc="reject">REJECT ALL</button>' +
          '<button type="button" class="snc-btn" data-snc="accept">ACCEPT ALL</button>' +
        '</div>' +
      '</div>';
    ov.addEventListener('click', function (e) {
      if (e.target === ov) { closeSettings(); return; }
      var t = e.target.closest && e.target.closest('[data-snc]');
      if (!t) return;
      var a = t.getAttribute('data-snc');
      if (a === 'save') save(document.getElementById('snc-an').checked, document.getElementById('snc-mk').checked);
      else if (a === 'reject') save(false, false);
      else if (a === 'accept') save(true, true);
    });
    document.addEventListener('keydown', onKey);
    document.body.appendChild(ov);
    var first = document.getElementById('snc-an');
    if (first) first.focus();
  }

  function closeSettings() {
    if (!ov) return;
    document.removeEventListener('keydown', onKey);
    if (ov.parentNode) ov.parentNode.removeChild(ov);
    ov = null;
    /* Still undecided: the banner stays so the choice can be made later. */
    if (!read()) showBanner();
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (e) {} }
  }

  window.SNYPDConsent = {
    get: read,
    open: function () {
      if (document.body) openSettings();
      else document.addEventListener('DOMContentLoaded', openSettings);
    },
    whenGranted: function (cat, fn) {
      var c = read();
      if (c && c[cat]) { try { fn(); } catch (e) {} return; }
      if (waiting[cat]) waiting[cat].push(fn);
    }
  };

  /* Any element with data-cookie-settings opens the settings panel. */
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-cookie-settings]');
    if (!t) return;
    e.preventDefault();
    openSettings();
  });

  /* French pages: the banner text comes from /assets/i18n.js (the app's translation
     layer), loaded here first so the banner never flashes up in English. */
  function whenLangReady(fn) {
    var lang = (document.documentElement.getAttribute('lang') || 'en').slice(0, 2);
    if (lang !== 'fr' || window.SNYPD_I18N) { fn(); return; }
    var done = false, go = function () { if (!done) { done = true; fn(); } };
    var s = document.createElement('script');
    s.src = '/assets/i18n.js';
    s.onload = go; s.onerror = go;
    setTimeout(go, 2000);
    document.head.appendChild(s);
  }

  var existing = read();
  if (existing) apply(existing);
  else whenLangReady(function () {
    if (document.body) showBanner();
    else document.addEventListener('DOMContentLoaded', showBanner);
  });
})();

/* Not about consent: a visitor reading a French page who goes on to sign up or log
   in gets the app in French (?lang=fr; /assets/i18n.js keeps that choice). */
(function () {
  var h = document.documentElement;
  if (!/^fr/.test(h.getAttribute('lang') || '') || h.hasAttribute('data-i18n-app')) return;
  function decorate() {
    [].forEach.call(document.querySelectorAll('a[href]'), function (a) {
      var u;
      try { u = new URL(a.getAttribute('href'), location.href); } catch (e) { return; }
      if (u.origin !== location.origin || !/^\/(signup|login|dashboard)$/.test(u.pathname) || u.searchParams.has('lang')) return;
      u.searchParams.set('lang', 'fr');
      a.setAttribute('href', u.pathname + u.search + u.hash);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate);
  else decorate();
})();

/* Not about consent: keeps campaign tags (utm_*, e.g. from a Meta ad) and a Whop
   partner code (a=<Whop username>, from a partner's link) on links to other SNYPD
   pages, so the sign-up page can save them with the new account (assets/auth.js)
   and /plans can pass the partner code to Whop's checkout. The only thing stored
   on the device is the partner code, and only once marketing is allowed
   (snypd_aff, read for 30 days: the same window as Whop's own partner links). */
(function () {
  var q = new URLSearchParams(location.search), tags = [];
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'a'].forEach(function (k) {
    var v = q.get(k);
    if (v && /^[A-Za-z0-9_.-]{1,60}$/.test(v)) tags.push([k, v]);
  });
  /* Entry page: the SNYPD page a visitor started on ("fr.bot-vinted", "home"), carried
     only on links to /signup, /login and /plans so sign-ups can be counted per page
     (auth.js saves it as entry_page). From the address only, never stored. */
  var from = q.get('from'), FROM_OK = /^[a-z0-9.-]{1,80}$/;
  if (!(from && FROM_OK.test(from))) {
    from = location.pathname.replace(/^\/+|\/+$/g, '').replace(/\.html$/, '').replace(/\//g, '.') || 'home';
    if (!FROM_OK.test(from) || /^(signup|login|reset-password|dashboard|account|admin|plans)$/.test(from)) from = null;
  }
  if (!tags.length && !from) return;
  var aff = q.get('a');
  if (aff && /^[A-Za-z0-9_.-]{1,60}$/.test(aff) && window.SNYPDConsent) {
    SNYPDConsent.whenGranted('marketing', function () {
      try { localStorage.setItem('snypd_aff', JSON.stringify({ a: aff, t: Date.now() })); } catch (e) {}
    });
  }
  function decorate() {
    [].forEach.call(document.querySelectorAll('a[href]'), function (a) {
      var u;
      try { u = new URL(a.getAttribute('href'), location.href); } catch (e) { return; }
      if (u.origin !== location.origin || u.pathname === location.pathname) return;
      tags.forEach(function (t) { if (!u.searchParams.has(t[0])) u.searchParams.set(t[0], t[1]); });
      if (from && /^\/(signup|login|plans)$/.test(u.pathname) && !u.searchParams.has('from')) u.searchParams.set('from', from);
      a.setAttribute('href', u.pathname + u.search + u.hash);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate);
  else decorate();
})();

/* Not about consent: Vercel Web Analytics counts page views without cookies and
   without storing anything on the device (a visitor is a hash of the request that
   Vercel discards after 24 h; vercel.com/docs/analytics/privacy-policy), so it runs
   for every visitor. Addresses are cut to the path plus campaign tags before they
   are sent, so sign-in codes and reset tokens never leave the page; account pages
   are not counted at all. */
(function () {
  if (/^\/(account|reset-password|dashboard|admin)(\/|$)/.test(location.pathname)) return;
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  window.va('beforeSend', function (ev) {
    try {
      var u = new URL(ev.url), keep = new URLSearchParams();
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'a'].forEach(function (k) {
        if (u.searchParams.has(k)) keep.set(k, u.searchParams.get(k));
      });
      var q = keep.toString();
      ev.url = u.origin + u.pathname + (q ? '?' + q : '');
      return ev;
    } catch (e) { return null; }
  });
  var s = document.createElement('script');
  s.defer = true;
  s.src = '/_vercel/insights/script.js';
  (document.head || document.documentElement).appendChild(s);
})();
