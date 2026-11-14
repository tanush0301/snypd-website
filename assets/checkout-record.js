/* SNYPD checkout record (14 Nov 2026; website repo outreach/62, growth plan move 1).
 *
 * Records, on the signed-in account's own Supabase Auth metadata (user_metadata.co), what happened in the plans
 * page's checkout: which plan's checkout was opened and where the visit came from, the kind of device, whether
 * Apple Pay could pay on it, whether Whop's payment form loaded or the hosted fallback was shown, and whether the
 * checkout was closed, failed, was canceled or was paid. No payment details (Whop handles them), no email, no
 * listing. It changes nothing a user sees and never blocks or throws into the page.
 *
 *   SnypdCheckoutRecord.device(ua, platform, touchPoints, standalone) -> 'ios-safari' | 'ios-other' | 'ios-inapp' |
 *       'ios-app' | 'android' | 'android-inapp' | 'android-app' | 'desktop' | 'desktop-app'  (same as first-session.js)
 *   SnypdCheckoutRecord.source(search, referrer, origin) -> 'email' | 'signup' | 'site:<page>' | 'dash' | 'account' |
 *       'auth' | 'site' | 'other' | 'direct'
 *   SnypdCheckoutRecord.merge(prev, ev, nowIso) -> next      (pure; never mutates prev)
 *   SnypdCheckoutRecord.create({ prev, save, load, now, setTimeout, clearTimeout, wait, cap }) -> { track, flush, state }
 *       load() returns the record as stored right now (another device may have written since this page loaded)
 *
 * Events (ev.k): 'open' {plan, src, d, ap} | 'load' | 'fallback' | 'close' {secs} | 'paid' | 'failed' | 'canceled'
 * Fields of co (all optional except v, t0):
 *   v 1 | t0 first record | t last open | o opens | p last plan opened | pl plans opened (max 6, first-open order)
 *   src where the last open came from | src1 where the first open came from | d device at the last open
 *   ap 1/0 Apple Pay could pay on this device at the last open (set only when the page could tell)
 *   ld payment form finished loading | fb hosted fallback shown | c closed without a result
 *   cs seconds the last closed checkout was open (max 3600) | r last result: paid | failed | canceled | rt when
 *   Counters stop at 99.
 * Pure ASCII.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdCheckoutRecord = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var PLANS = { pass: 1, solo: 1, kickstart: 1, pro: 1, elite: 1 };
  var DEVICES = { 'ios-safari': 1, 'ios-other': 1, 'ios-inapp': 1, 'ios-app': 1, 'android': 1, 'android-inapp': 1,
    'android-app': 1, 'desktop': 1, 'desktop-app': 1 };
  var RESULTS = { paid: 1, failed: 1, canceled: 1 };
  var COUNTERS = { load: 'ld', fallback: 'fb' };
  var SRC_RE = /^(email|signup|dash|account|auth|site|other|direct|site:[a-z0-9.-]{1,40})$/;
  var MAX = 99;

  function device(ua, platform, touchPoints, standalone) {
    ua = String(ua || '');
    var inApp = /Instagram|FBAN|FBAV|FB_IAB/.test(ua);
    var ios = /iPad|iPhone|iPod/.test(ua) || (platform === 'MacIntel' && Number(touchPoints) > 1);
    if (ios) {
      if (standalone) return 'ios-app';
      if (inApp) return 'ios-inapp';
      return (/Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/.test(ua)) ? 'ios-safari' : 'ios-other';
    }
    if (/Android/.test(ua)) return standalone ? 'android-app' : (inApp ? 'android-inapp' : 'android');
    return standalone ? 'desktop-app' : 'desktop';
  }

  // Where this visit to the plans page came from. Only names of our own pages are kept, never a full address.
  function source(search, referrer, origin) {
    var q = null;
    try { q = new URLSearchParams(String(search || '')); } catch (e) { q = null; }
    if (q) {
      if (q.get('promo')) return 'email';                    // trial-ended email links carry ?promo=
      if (q.get('checkout') && !q.has('status')) return 'signup';  // homepage plan button -> sign-up -> here
      var from = String(q.get('from') || '').toLowerCase();
      if (/^[a-z0-9.-]{1,40}$/.test(from)) return 'site:' + from;  // consent.js tags our own links with from=<page>
    }
    var ref = String(referrer || ''), org = String(origin || '');
    if (!ref) return 'direct';
    if (!org || ref.indexOf(org) !== 0 || !/^($|[\/?#])/.test(ref.slice(org.length))) return 'other';
    var path = ref.slice(org.length).split(/[?#]/)[0] || '/';
    if (/^\/dashboard(\.html)?\/?$/.test(path)) return 'dash';
    if (/^\/account(\.html)?\/?$/.test(path)) return 'account';
    if (/^\/(signup|login|reset-password)(\.html)?\/?$/.test(path)) return 'auth';
    if (path === '/' || path === '/index.html') return 'site:home';
    return 'site';
  }

  function inc(n, key) { n[key] = Math.min(MAX, (Number(n[key]) || 0) + 1); }

  function valid(ev) {
    if (!ev || typeof ev !== 'object') return false;
    if (ev.k === 'open') return !!PLANS[ev.plan];
    return !!(COUNTERS[ev.k] || ev.k === 'close' || RESULTS[ev.k]);
  }

  // An unknown event leaves the record exactly as it was (no empty record, no write).
  function merge(prev, ev, nowIso) {
    var base = prev && typeof prev === 'object' ? prev : null;
    if (!valid(ev)) return base;
    var n = {}, k;
    if (base) for (k in base) if (Object.prototype.hasOwnProperty.call(base, k)) n[k] = base[k];
    n.v = 1;
    if (!n.t0) n.t0 = nowIso;
    var kind = ev.k;
    if (kind === 'open') {
      inc(n, 'o');
      n.t = nowIso;
      n.p = ev.plan;
      var pl = Array.isArray(n.pl) ? n.pl.slice(0) : [];
      if (pl.indexOf(ev.plan) < 0 && pl.length < 6) pl.push(ev.plan);
      n.pl = pl;
      if (typeof ev.src === 'string' && SRC_RE.test(ev.src)) {
        n.src = ev.src;
        if (!n.src1) n.src1 = ev.src;
      }
      if (DEVICES[ev.d]) n.d = ev.d;
      if (ev.ap === 0 || ev.ap === 1) n.ap = ev.ap;
    } else if (COUNTERS[kind]) {
      inc(n, COUNTERS[kind]);
    } else if (kind === 'close') {
      inc(n, 'c');
      var s = ev.secs == null || ev.secs === '' ? NaN : Number(ev.secs);
      if (isFinite(s) && s >= 0) n.cs = Math.min(3600, Math.round(s));
    } else if (RESULTS[kind]) {
      n.r = kind;
      n.rt = nowIso;
    }
    return n;
  }

  function create(o) {
    o = o || {};
    var now = o.now || function () { return new Date().toISOString(); };
    var st = o.setTimeout || setTimeout, ct = o.clearTimeout || clearTimeout;
    var wait = o.wait == null ? 1500 : o.wait, cap = o.cap == null ? 12 : o.cap;
    var saved = o.prev && typeof o.prev === 'object' ? o.prev : null;
    // cur = what this page believes the record is; pending = the events not yet stored, each with its own time,
    // so they can be re-applied on top of whatever another device stored in the meantime.
    var cur = saved, pending = [], timer = null, writes = 0, busy = false, again = false;
    var same = function (a, b) { return JSON.stringify(a) === JSON.stringify(b); };
    var replay = function (base, list) {
      var n = base;
      for (var i = 0; i < list.length; i++) n = merge(n, list[i].e, list[i].at);
      return n;
    };

    function flush() {
      if (timer) { ct(timer); timer = null; }
      if (busy) { again = true; return; }
      if (!pending.length || writes >= cap) return;
      var batch = pending.slice(0);
      busy = true;
      var finish = function (ok, stored) {
        busy = false;
        if (ok) {
          saved = stored;
          pending = pending.slice(batch.length);
          cur = replay(saved, pending);
        }
        if (again) { again = false; flush(); }
      };
      var load = o.load ? Promise.resolve().then(o.load).then(function (r) { return r && typeof r === 'object' ? r : saved; }, function () { return saved; })
        : Promise.resolve(saved);
      load.then(function (base) {
        var next = replay(base, batch);
        if (same(next, base)) { finish(true, base); return; }
        writes++;
        return Promise.resolve(o.save(next)).then(function (r) { finish(!(r && r.error), next); });
      }).then(null, function () { finish(false); });
    }
    function track(ev) {
      try {
        var at = now();
        var next = merge(cur, ev, at);
        if (same(next, cur)) return;
        cur = next;
        pending.push({ e: ev || {}, at: at });
        if (timer) ct(timer);
        timer = st(flush, wait);
      } catch (e) { /* measurement must never break the page */ }
    }
    return { track: track, flush: flush, state: function () { return cur; }, writes: function () { return writes; } };
  }

  return { device: device, source: source, merge: merge, create: create };
}));
