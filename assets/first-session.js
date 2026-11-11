/* SNYPD first-session measurement (10 Nov 2026; website repo outreach/53, release R1).
 *
 * Records, on the account's own Supabase Auth metadata (user_metadata.fs), which set-up steps a new account
 * reached: device type, wizard step, whether the first hunt has a price limit, what happened at the alerts step,
 * the first open as an installed Home Screen app, and what was tapped on the "too broad" card. No listing, no
 * search words, no address. It changes nothing a user sees and never blocks or throws into the page.
 *
 *   SnypdFirstSession.device(ua, platform, touchPoints, standalone) -> 'ios-safari' | 'ios-other' | 'ios-inapp' |
 *       'ios-app' | 'android' | 'android-inapp' | 'android-app' | 'desktop' | 'desktop-app'
 *   SnypdFirstSession.priceBounds(vintedUrl) -> { max: 0|1, min: 'none'|'def'|'own' }
 *   SnypdFirstSession.shouldTrack(joinedAtIso, prev, nowMs) -> boolean     (first 7 days only)
 *   SnypdFirstSession.merge(prev, patch, nowIso, device) -> next           (pure; never mutates prev)
 *   SnypdFirstSession.create({ prev, device, save, load, now, setTimeout, clearTimeout, wait, cap }) -> { track, flush, state }
 *       load() returns the record as stored right now (another device may have written since this page loaded)
 *
 * Fields of fs (all optional except v, t0, dev):
 *   v 1 | t0 first record | dev first device | devs every device seen (max 4) | app first open as an installed app
 *   wz highest wizard step seen: 1 words, 2 alert style, 3 alerts
 *   src where the first hunt was saved: 'quick' (wizard form) or 'sheet' (Filters) | max 1/0 | min none/def/own
 *   werr times step 1 refused the form (for example minimum above maximum) | hw times the words warning showed
 *   al latest alerts result: on | denied | ios (shown the Home Screen text) | unsup | err ; stays 'on' once on
 *   al1 first result | al_try taps on "Turn on alerts" | later 1 = tapped "Set this up later"
 *   al_on when alerts first came on | al_dev on which device
 *   card set-up card: shown < snooze < resume | vol broad/coach card: shown, or the last button (calm, apply, edit,
 *   keep, undo) | vol_k 'broad' or 'coach'
 * Pure ASCII (dashboard.html carries a BOM and loads this file).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdFirstSession = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var WINDOW_MS = 7 * 86400000;
  // The wizard's pre-filled minimum in each site's currency (dashboard.html FLOOR_BY_CURRENCY).
  var DEFAULT_FLOORS = [30, 25, 35, 130, 750, 350, 220, 12000, 150];
  var AL = { on: 1, denied: 1, ios: 1, unsup: 1, err: 1 };
  var CARD_RANK = { shown: 1, snooze: 2, resume: 3 };
  var VOL = { shown: 1, calm: 1, apply: 1, edit: 1, keep: 1, undo: 1 };
  var SRC = { quick: 1, sheet: 1 };

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

  function priceBounds(url) {
    var s = String(url || '');
    var to = /[?&]price_to=([0-9.]+)/.exec(s), from = /[?&]price_from=([0-9.]+)/.exec(s);
    var max = to && Number(to[1]) > 0 ? 1 : 0;
    var min = 'none';
    if (from && Number(from[1]) > 0) min = DEFAULT_FLOORS.indexOf(Number(from[1])) >= 0 ? 'def' : 'own';
    return { max: max, min: min };
  }

  function shouldTrack(joinedAtIso, prev, nowMs) {
    var t0 = prev && prev.t0 ? Date.parse(prev.t0) : NaN;
    if (isFinite(t0)) return nowMs - t0 < WINDOW_MS;
    var joined = Date.parse(joinedAtIso || '');
    return isFinite(joined) && nowMs - joined >= 0 && nowMs - joined < WINDOW_MS;
  }

  function merge(prev, patch, nowIso, dev) {
    var n = {}, k;
    if (prev && typeof prev === 'object') for (k in prev) if (Object.prototype.hasOwnProperty.call(prev, k)) n[k] = prev[k];
    patch = patch || {};
    n.v = 1;
    if (!n.t0) n.t0 = nowIso;
    if (dev) {
      if (!n.dev) n.dev = dev;
      var devs = Array.isArray(n.devs) ? n.devs.slice(0) : [];
      if (devs.indexOf(dev) < 0 && devs.length < 4) devs.push(dev);
      n.devs = devs;
      if (/-app$/.test(dev) && !n.app) n.app = nowIso;
    }
    var wz = Number(patch.wz);
    if (wz === 1 || wz === 2 || wz === 3) n.wz = Math.max(Number(n.wz) || 0, wz);
    if (patch.hunt != null && n.max === undefined) {
      var b = priceBounds(patch.hunt);
      n.max = b.max; n.min = b.min;
      if (SRC[patch.src]) n.src = patch.src;
    }
    var tries = Number(patch.al_try);
    if (tries > 0 && tries < 50) n.al_try = Math.min(99, (Number(n.al_try) || 0) + Math.floor(tries));
    if (patch.al && AL[patch.al]) {
      if (!n.al1) n.al1 = patch.al;
      if (n.al !== 'on') n.al = patch.al;
      if (patch.al === 'on' && !n.al_on) { n.al_on = nowIso; if (dev) n.al_dev = dev; }
    }
    if (patch.later) n.later = 1;
    if (patch.werr === 1) n.werr = Math.min(20, (Number(n.werr) || 0) + 1);
    if (patch.hw === 1) n.hw = Math.min(20, (Number(n.hw) || 0) + 1);
    if (patch.card && CARD_RANK[patch.card] && CARD_RANK[patch.card] > (CARD_RANK[n.card] || 0)) n.card = patch.card;
    if (patch.vol && VOL[patch.vol] && !(patch.vol === 'shown' && n.vol)) n.vol = patch.vol;
    if ((patch.vol_k === 'broad' || patch.vol_k === 'coach') && !n.vol_k) n.vol_k = patch.vol_k;
    return n;
  }

  function create(o) {
    o = o || {};
    var now = o.now || function () { return new Date().toISOString(); };
    var st = o.setTimeout || setTimeout, ct = o.clearTimeout || clearTimeout;
    var wait = o.wait == null ? 3000 : o.wait, cap = o.cap == null ? 8 : o.cap;
    var saved = o.prev && typeof o.prev === 'object' ? o.prev : null;
    // cur = what this page believes the record is; pending = the steps not yet stored, each with its own time,
    // so they can be re-applied on top of whatever another device stored in the meantime.
    var cur = saved, pending = [], timer = null, writes = 0, busy = false, again = false;
    var same = function (a, b) { return JSON.stringify(a) === JSON.stringify(b); };
    var replay = function (base, list) {
      var n = base;
      for (var i = 0; i < list.length; i++) n = merge(n, list[i].p, list[i].at, o.device);
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
    function track(patch) {
      try {
        var at = now();
        var next = merge(cur, patch, at, o.device);
        if (same(next, cur)) return;
        cur = next;
        pending.push({ p: patch || {}, at: at });
        if (timer) ct(timer);
        timer = st(flush, wait);
      } catch (e) { /* measurement must never break the page */ }
    }
    return { track: track, flush: flush, state: function () { return cur; }, writes: function () { return writes; } };
  }

  return { device: device, priceBounds: priceBounds, shouldTrack: shouldTrack, merge: merge, create: create, WINDOW_MS: WINDOW_MS };
}));
