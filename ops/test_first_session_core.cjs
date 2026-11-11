/* First-session measurement, pure logic (assets/first-session.js). Run: node ops/test_first_session_core.cjs
 * No browser, no network. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const FS = require(path.join(__dirname, '..', 'assets', 'first-session.js'));
let passed = 0;
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const ok = (c, m) => { assert(c, m); passed++; };

// ---- device ------------------------------------------------------------------------------------------------
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const IPHONE_CHROME = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/141.0.0.0 Mobile/15E148 Safari/604.1';
const IPHONE_IG = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 350.0.0.0';
const IPAD_DESKTOP_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15';
const ANDROID = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36';
const ANDROID_FB = ANDROID + ' [FBAN/FB4A;FBAV/480.0.0.0;]';
const WIN = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36';
eq(FS.device(IPHONE, 'iPhone', 5, false), 'ios-safari', 'iPhone Safari tab');
eq(FS.device(IPHONE, 'iPhone', 5, true), 'ios-app', 'iPhone Home Screen app');
eq(FS.device(IPHONE_CHROME, 'iPhone', 5, false), 'ios-other', 'Chrome on iPhone');
eq(FS.device(IPHONE_IG, 'iPhone', 5, false), 'ios-inapp', 'Instagram in-app browser on iPhone');
eq(FS.device(IPAD_DESKTOP_UA, 'MacIntel', 5, false), 'ios-safari', 'iPad that reports a Mac user agent');
eq(FS.device(IPAD_DESKTOP_UA, 'MacIntel', 0, false), 'desktop', 'a real Mac');
eq(FS.device(ANDROID, 'Linux armv81', 5, false), 'android', 'Android Chrome');
eq(FS.device(ANDROID, 'Linux armv81', 5, true), 'android-app', 'Android installed');
eq(FS.device(ANDROID_FB, 'Linux armv81', 5, false), 'android-inapp', 'Facebook in-app browser on Android');
eq(FS.device(WIN, 'Win32', 0, false), 'desktop', 'Windows');
eq(FS.device(WIN, 'Win32', 0, true), 'desktop-app', 'Windows installed');
eq(FS.device(undefined, undefined, undefined, undefined), 'desktop', 'nothing known');

// ---- price bounds: never the words, only whether a limit exists ----------------------------------------------
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=nike+dunk&price_from=30&price_to=60'), { max: 1, min: 'def' });
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=nike+dunk&price_from=30.0&currency=EUR'), { max: 0, min: 'def' });
eq(FS.priceBounds('https://www.vinted.co.uk/catalog?search_text=x&price_from=25&price_to=40'), { max: 1, min: 'def' }, 'GBP default floor');
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=x&price_from=5&price_to=20'), { max: 1, min: 'own' });
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=x&price_to=17'), { max: 1, min: 'none' });
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=x'), { max: 0, min: 'none' });
eq(FS.priceBounds('https://www.vinted.fr/catalog?search_text=x&price_from=0&price_to=0'), { max: 0, min: 'none' }, 'zeros are no limit');
eq(FS.priceBounds(null), { max: 0, min: 'none' });

// ---- who is measured: 7 days from the first record (or from sign-up when there is no record) ------------------
const NOW = Date.parse('2026-11-10T12:00:00Z'), D = 86400000;
ok(FS.shouldTrack(new Date(NOW - 3600000).toISOString(), null, NOW), 'an hour-old account');
ok(FS.shouldTrack(new Date(NOW - 6.9 * D).toISOString(), null, NOW), 'day 6.9');
ok(!FS.shouldTrack(new Date(NOW - 7.1 * D).toISOString(), null, NOW), 'day 7.1: no');
ok(!FS.shouldTrack(new Date(NOW - 400 * D).toISOString(), null, NOW), 'an old account is never measured');
ok(!FS.shouldTrack(null, null, NOW), 'no sign-up date: no');
ok(!FS.shouldTrack('garbage', null, NOW), 'bad sign-up date: no');
ok(!FS.shouldTrack(new Date(NOW + D).toISOString(), null, NOW), 'a sign-up date in the future: no');
ok(FS.shouldTrack(new Date(NOW - 30 * D).toISOString(), { t0: new Date(NOW - 2 * D).toISOString() }, NOW), 'a record started 2 days ago wins over the sign-up date');
ok(!FS.shouldTrack(new Date(NOW - D).toISOString(), { t0: new Date(NOW - 8 * D).toISOString() }, NOW), 'a record started 8 days ago: closed');

// ---- merge ---------------------------------------------------------------------------------------------------
const T1 = '2026-11-10T12:00:00.000Z', T2 = '2026-11-10T12:05:00.000Z', T3 = '2026-11-10T12:20:00.000Z';
let r = FS.merge(null, {}, T1, 'ios-safari');
eq(r, { v: 1, t0: T1, dev: 'ios-safari', devs: ['ios-safari'] }, 'first record');
const frozen = JSON.stringify(r);
let r2 = FS.merge(r, { wz: 1 }, T2, 'ios-safari');
eq(JSON.stringify(r), frozen, 'merge never changes its input');
eq(r2.wz, 1);
eq(FS.merge(r2, { wz: 3 }, T2, 'ios-safari').wz, 3);
eq(FS.merge(FS.merge(r2, { wz: 3 }, T2, 'ios-safari'), { wz: 1 }, T2, 'ios-safari').wz, 3, 'the wizard step never goes down');
eq(FS.merge(r2, { wz: 9 }, T2, 'ios-safari').wz, 1, 'an unknown step is ignored');
// first hunt only, and no words stored
let h = FS.merge(r2, { hunt: 'https://www.vinted.fr/catalog?search_text=secret+words&price_from=30', src: 'quick' }, T2, 'ios-safari');
eq([h.max, h.min, h.src], [0, 'def', 'quick']);
ok(!JSON.stringify(h).includes('secret'), 'the search words are never stored');
ok(!JSON.stringify(h).includes('vinted'), 'the link is never stored');
let h2 = FS.merge(h, { hunt: 'https://www.vinted.fr/catalog?search_text=x&price_to=10', src: 'sheet' }, T3, 'ios-safari');
eq([h2.max, h2.min, h2.src], [0, 'def', 'quick'], 'a second hunt does not overwrite the first');
eq(FS.merge(r2, { hunt: 'https://www.vinted.fr/catalog?search_text=x', src: 'bogus' }, T2, 'ios-safari').src, undefined, 'unknown source ignored');
// alerts
let a = FS.merge(h, { al_try: 1 }, T2, 'ios-safari');
a = FS.merge(a, { al: 'ios' }, T2, 'ios-safari');
eq([a.al, a.al1, a.al_try, a.al_on], ['ios', 'ios', 1, undefined]);
a = FS.merge(a, { later: 1 }, T2, 'ios-safari');
eq(a.later, 1);
let b = FS.merge(a, {}, T3, 'ios-app');
eq([b.dev, b.devs, b.app], ['ios-safari', ['ios-safari', 'ios-app'], T3], 'the installed app is a second device and stamps "app" once');
eq(FS.merge(b, {}, '2026-11-11T08:00:00.000Z', 'ios-app').app, T3, '"app" keeps its first time');
b = FS.merge(b, { al_try: 1 }, T3, 'ios-app');
b = FS.merge(b, { al: 'on' }, T3, 'ios-app');
eq([b.al, b.al1, b.al_try, b.al_on, b.al_dev], ['on', 'ios', 2, T3, 'ios-app'], 'alerts came on in the app; the first result is kept');
eq(FS.merge(b, { al: 'denied' }, T3, 'ios-safari').al, 'on', 'once on, a later state on another device does not undo it');
eq(FS.merge(b, { al: 'on' }, '2026-11-12T08:00:00.000Z', 'desktop').al_on, T3, 'al_on keeps its first time');
eq(FS.merge(r, { al: 'nonsense' }, T2, 'ios-safari').al, undefined, 'unknown alert state ignored');
eq(FS.merge(r, { al_try: 500 }, T2, 'ios-safari').al_try, undefined, 'absurd counts ignored');
// cards
eq(FS.merge(r, { card: 'shown' }, T2, 'x').card, 'shown');
eq(FS.merge(FS.merge(r, { card: 'resume' }, T2, 'x'), { card: 'shown' }, T2, 'x').card, 'resume', '"shown" never replaces an action');
eq(FS.merge(FS.merge(r, { card: 'snooze' }, T2, 'x'), { card: 'resume' }, T2, 'x').card, 'resume');
let v = FS.merge(r, { vol: 'shown', vol_k: 'broad' }, T2, 'x');
eq([v.vol, v.vol_k], ['shown', 'broad']);
v = FS.merge(v, { vol: 'calm' }, T2, 'x');
eq(FS.merge(v, { vol: 'shown', vol_k: 'coach' }, T2, 'x'), v, 'a second showing changes nothing');
eq(FS.merge(v, { vol: 'keep' }, T2, 'x').vol, 'keep', 'the last button wins');
// counters
let c = FS.merge(r, { werr: 1 }, T2, 'x'); c = FS.merge(c, { werr: 1 }, T2, 'x'); c = FS.merge(c, { hw: 1 }, T2, 'x');
eq([c.werr, c.hw], [2, 1], 'form refusals and words warnings are counted');
eq(FS.merge(r, { werr: 5, hw: 'x' }, T2, 'x'), FS.merge(r, {}, T2, 'x'), 'only single steps count');
let big = r; for (let i = 0; i < 40; i++) big = FS.merge(big, { werr: 1 }, T2, 'x');
eq(big.werr, 20, 'counters stop at 20');
// five devices: the list stops at four
let many = r;
['a', 'b', 'c', 'd', 'e'].forEach(x => { many = FS.merge(many, {}, T2, x); });
eq(many.devs.length, 4);
ok(JSON.stringify(FS.merge(b, { vol: 'apply', vol_k: 'coach', card: 'resume' }, T3, 'ios-app')).length < 400, 'the whole record stays small');

// ---- tracker: debounce, re-read before writing, cap, never throws ----------------------------------------------
function harness(opts) {
  let clock = Date.parse(T1), timers = [], remote = opts.remote === undefined ? null : opts.remote;
  const saves = [], loads = [];
  const t = FS.create(Object.assign({
    prev: opts.prev || null, device: opts.device || 'ios-safari',
    now: () => new Date(clock).toISOString(),
    setTimeout: (fn, ms) => { const id = timers.length + 1; timers.push({ id, fn, at: clock + ms }); return id; },
    clearTimeout: (id) => { timers = timers.filter(x => x.id !== id); },
    load: async () => { loads.push(clock); return remote; },
    save: async (fs) => { if (opts.fail && opts.fail()) return { error: { message: 'offline' } }; saves.push(JSON.parse(JSON.stringify(fs))); remote = fs; return { error: null }; },
  }, opts.over || {}));
  const tick = async (ms) => {
    clock += ms;
    const due = timers.filter(x => x.at <= clock); timers = timers.filter(x => x.at > clock);
    due.forEach(x => x.fn());
    for (let i = 0; i < 12; i++) await Promise.resolve();
  };
  return { t, saves, loads, tick, setRemote: (x) => { remote = x; }, getRemote: () => remote };
}
(async () => {
  let H = harness({});
  H.t.track({}); H.t.track({ wz: 1 }); H.t.track({ wz: 1 });
  await H.tick(1000);
  eq(H.saves.length, 0, 'nothing is written before the quiet period ends');
  H.t.track({ wz: 2 });
  await H.tick(2999);
  eq(H.saves.length, 0, 'a new step restarts the wait');
  await H.tick(2);
  eq(H.saves.length, 1, 'one write for the whole burst');
  eq([H.saves[0].dev, H.saves[0].wz], ['ios-safari', 2]);
  H.t.track({ wz: 1 }); H.t.track({});
  await H.tick(5000);
  eq(H.saves.length, 1, 'steps that change nothing cause no write');

  // another device wrote in between: its fields survive
  H = harness({});
  H.t.track({ wz: 3 }); H.t.track({ al_try: 1 }); H.t.track({ al: 'ios' });
  await H.tick(3001);
  const appRecord = FS.merge(FS.merge(H.getRemote(), { al_try: 1 }, T3, 'ios-app'), { al: 'on' }, T3, 'ios-app');
  H.setRemote(appRecord);                       // the installed app stored "alerts on"
  H.t.track({ card: 'snooze' });                // the old Safari tab is still open and records something
  await H.tick(3001);
  const last = H.saves[H.saves.length - 1];
  eq([last.al, last.al_on, last.app, last.card, last.al_try], ['on', T3, T3, 'snooze', 2], 'a stale tab does not erase what the app stored');

  // a failed write is retried with the next step, nothing is lost
  let failing = true;
  H = harness({ fail: () => failing });
  H.t.track({ wz: 1 });
  await H.tick(3001);
  eq(H.saves.length, 0);
  failing = false;
  H.t.track({ wz: 2 });
  await H.tick(3001);
  eq([H.saves.length, H.saves[0].wz, H.saves[0].dev], [1, 2, 'ios-safari'], 'the failed step is included in the next write');

  // cap
  H = harness({ over: { cap: 3 } });
  for (let i = 0; i < 6; i++) { H.t.track({ al_try: 1 }); await H.tick(3001); }
  eq(H.saves.length, 3, 'never more than the cap of writes per page load');

  // a throwing save or load never escapes
  H = harness({ over: { save: () => { throw new Error('boom'); } } });
  H.t.track({ wz: 1 });
  await H.tick(3001);
  ok(true, 'a throwing save is swallowed');
  H = harness({ over: { load: async () => { throw new Error('boom'); } } });
  H.t.track({ wz: 1 });
  await H.tick(3001);
  eq(H.saves.length, 1, 'a failing re-read falls back to what this page knows');
  const T = FS.create({ device: 'desktop', save: async () => ({ error: null }) });
  T.track(null); T.track(undefined); T.track('x'); T.track({ wz: 'x', al: 7, card: {}, vol: [] });
  ok(T.state().v === 1 && T.state().wz === undefined, 'garbage patches are ignored');
  T.flush();

  console.log(`PASS: ${passed} first-session core checks.`);
})().catch(e => { console.error(e); process.exitCode = 1; });
