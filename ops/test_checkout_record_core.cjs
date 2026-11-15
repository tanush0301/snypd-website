/*
 * Checkout record core (assets/checkout-record.js; website repo outreach/62, move 1).
 *   node ops/test_checkout_record_core.cjs
 * Pure checks: no browser, no network, no account.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const R = require('../assets/checkout-record.js');

let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };

(async () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'checkout-record.js'), 'utf8');
  ok(!/[^\x00-\x7F]/.test(src), 'checkout-record.js is pure ASCII');

  // ----- device(): same classes as first-session.js
  const FS = require('../assets/first-session.js');
  const UAS = [
    ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1', 'iPhone', 5, false],
    ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148', 'iPhone', 5, true],
    ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 300.0', 'iPhone', 5, false],
    ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0 Mobile/15E148 Safari/604.1', 'iPhone', 5, false],
    ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15', 'MacIntel', 5, false],
    ['Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36', 'Linux armv8l', 5, false],
    ['Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36 Instagram 300.0', 'Linux armv8l', 5, false],
    ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36', 'Win32', 0, false],
    ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36', 'Win32', 0, true],
  ];
  const expectDev = ['ios-safari', 'ios-app', 'ios-inapp', 'ios-other', 'ios-safari', 'android', 'android-inapp', 'desktop', 'desktop-app'];
  UAS.forEach((u, i) => {
    eq(R.device(...u), expectDev[i], 'device class ' + expectDev[i]);
    eq(R.device(...u), FS.device(...u), 'same class as first-session.js for ' + expectDev[i]);
  });

  // ----- source(): only names of our own pages, never a full address
  const O = 'https://www.snypd.store';
  eq(R.source('?promo=STAY50', '', O), 'email', 'trial-ended email link');
  eq(R.source('?checkout=pro', O + '/dashboard', O), 'signup', 'sign-up plan flow');
  eq(R.source('?checkout=pro&status=failed', O + '/plans', O), 'site', 'a return is not the sign-up flow');
  eq(R.source('?from=fr.bot-vinted', '', O), 'site:fr.bot-vinted', 'from= tag kept');
  eq(R.source('?from=Home', '', O), 'site:home', 'from= lower-cased');
  eq(R.source('?from=%3Cscript%3E', '', O), 'direct', 'odd from= ignored');
  eq(R.source('?from=' + 'a'.repeat(41), '', O), 'direct', 'over-long from= ignored');
  eq(R.source('', O + '/dashboard', O), 'dash', 'from the dashboard');
  eq(R.source('', O + '/dashboard?activated=pro#x', O), 'dash', 'dashboard with query');
  eq(R.source('', O + '/account', O), 'account', 'from the account page');
  eq(R.source('', O + '/login?next=/plans', O), 'auth', 'from sign-in');
  eq(R.source('', O + '/', O), 'site:home', 'from the homepage');
  eq(R.source('', O + '/vinted-bot', O), 'site', 'from another page of ours');
  eq(R.source('', 'https://chatgpt.com/', O), 'other', 'another site');
  eq(R.source('', 'https://www.snypd.store.evil.example/', O), 'other', 'a look-alike host that starts with our address is another site');
  eq(R.source('', O, O), 'site:home', 'our bare origin is the homepage');
  eq(R.source('', '', O), 'direct', 'no referrer');
  eq(R.source(null, null, null), 'direct', 'nothing at all');

  // ----- merge(): one event at a time
  const T1 = '2026-11-14T10:00:00.000Z', T2 = '2026-11-14T10:05:00.000Z';
  let m = R.merge(null, { k: 'open', plan: 'pro', src: 'site:home', d: 'ios-safari', ap: 1 }, T1);
  eq(m, { v: 1, t0: T1, o: 1, t: T1, p: 'pro', pl: ['pro'], src: 'site:home', src1: 'site:home', d: 'ios-safari', ap: 1 }, 'first open');
  const frozen = JSON.stringify(m);
  let m2 = R.merge(m, { k: 'open', plan: 'pass', src: 'dash', d: 'desktop', ap: 0 }, T2);
  eq(JSON.stringify(m), frozen, 'merge never mutates the previous record');
  eq([m2.o, m2.p, m2.pl, m2.src, m2.src1, m2.d, m2.ap, m2.t, m2.t0], [2, 'pass', ['pro', 'pass'], 'dash', 'site:home', 'desktop', 0, T2, T1], 'second open keeps the first source and first time');
  m2 = R.merge(m2, { k: 'open', plan: 'pro' }, T2);
  eq([m2.o, m2.pl, m2.src, m2.d, m2.ap], [3, ['pro', 'pass'], 'dash', 'desktop', 0], 'open without extras keeps the last known values; plan list has no repeats');
  eq(R.merge(m2, { k: 'load' }, T2).ld, 1, 'form loaded counted');
  eq(R.merge(m2, { k: 'fallback' }, T2).fb, 1, 'fallback counted');
  let c = R.merge(m2, { k: 'close', secs: 41.6 }, T2);
  eq([c.c, c.cs], [1, 42], 'close counted with rounded seconds');
  eq(R.merge(c, { k: 'close', secs: 99999 }, T2).cs, 3600, 'close seconds capped at an hour');
  eq(R.merge(c, { k: 'close', secs: null }, T2).cs, 42, 'close without a time keeps the last time');
  eq(R.merge(c, { k: 'close', secs: -5 }, T2).cs, 42, 'negative time ignored');
  for (const r of ['paid', 'failed', 'canceled']) {
    const x = R.merge(m2, { k: r }, T2);
    eq([x.r, x.rt], [r, T2], 'result ' + r);
  }
  let big = { v: 1, t0: T1, o: 99, ld: 99, fb: 99, c: 99, pl: ['pass', 'solo', 'kickstart', 'pro', 'elite'] };
  big = R.merge(big, { k: 'open', plan: 'elite' }, T2);
  big = R.merge(big, { k: 'load' }, T2);
  big = R.merge(big, { k: 'fallback' }, T2);
  big = R.merge(big, { k: 'close' }, T2);
  eq([big.o, big.ld, big.fb, big.c, big.pl.length], [99, 99, 99, 99, 5], 'counters stop at 99');

  // invalid events change nothing (no empty record, no write)
  eq(R.merge(null, { k: 'open', plan: 'platinum' }, T1), null, 'unknown plan: no record');
  eq(R.merge(null, { k: 'open', plan: 'free' }, T1), null, 'free is not a checkout');
  eq(R.merge(null, { k: 'whatever' }, T1), null, 'unknown event: no record');
  eq(R.merge(null, null, T1), null, 'no event: no record');
  ok(R.merge(m, { k: 'nope' }, T2) === m, 'unknown event returns the same record');
  const bad = R.merge(null, { k: 'open', plan: 'solo', src: 'https://x.example/?email=a@b.c', d: 'toaster', ap: 'yes' }, T1);
  eq([bad.src, bad.src1, bad.d, bad.ap], [undefined, undefined, undefined, undefined], 'unknown source, device and Apple Pay values are not stored');
  ok(!JSON.stringify(bad).includes('@'), 'no address or email can enter the record');

  // ----- create(): debounce, write cap, re-read before writing
  const fakeTimers = () => {
    let id = 0; const q = new Map();
    return {
      setTimeout: (fn, ms) => { q.set(++id, fn); return id; },
      clearTimeout: (i) => q.delete(i),
      run: () => { const fns = [...q.values()]; q.clear(); fns.forEach(f => f()); },
      size: () => q.size,
    };
  };
  const tick = () => new Promise(r => setImmediate(r));
  let clock = 0;
  const now = () => new Date(Date.UTC(2026, 10, 14, 10, 0, clock++)).toISOString();

  // debounce: several events, one write
  let timers = fakeTimers(), saves = [];
  let rec = R.create({ prev: null, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    save: (co) => { saves.push(co); return Promise.resolve({}); } });
  rec.track({ k: 'open', plan: 'pro', src: 'dash' });
  rec.track({ k: 'load' });
  rec.track({ k: 'close', secs: 12 });
  eq(saves.length, 0, 'nothing written before the pause');
  timers.run(); await tick(); await tick();
  eq(saves.length, 1, 'one write for three events');
  eq([saves[0].o, saves[0].ld, saves[0].c, saves[0].cs], [1, 1, 1, 12], 'the write holds all three');
  rec.track({ k: 'nope' });
  eq(timers.size(), 0, 'an unknown event schedules nothing');

  // re-read before writing: another device stored opens in the meantime
  timers = fakeTimers(); saves = [];
  let server = { v: 1, t0: T1, o: 5, p: 'solo', pl: ['solo'], r: 'failed', rt: T1 };
  rec = R.create({ prev: { v: 1, t0: T1, o: 1, p: 'solo', pl: ['solo'] }, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    load: () => Promise.resolve(server), save: (co) => { saves.push(co); server = co; return Promise.resolve({}); } });
  rec.track({ k: 'open', plan: 'pro' });
  timers.run(); await tick(); await tick();
  eq([saves[0].o, saves[0].pl, saves[0].r], [6, ['solo', 'pro'], 'failed'], 'counts continue from what another device stored');

  // a failed save keeps the events for the next try
  timers = fakeTimers(); saves = [];
  let fail = true;
  rec = R.create({ prev: null, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    save: (co) => { saves.push(co); return Promise.resolve(fail ? { error: new Error('offline') } : {}); } });
  rec.track({ k: 'open', plan: 'pass' });
  timers.run(); await tick(); await tick();
  fail = false;
  rec.track({ k: 'paid' });
  timers.run(); await tick(); await tick();
  eq(saves.length, 2, 'retried after a failed save');
  eq([saves[1].o, saves[1].p, saves[1].r], [1, 'pass', 'paid'], 'the retry still holds the open');

  // save that throws never escapes
  timers = fakeTimers();
  rec = R.create({ prev: null, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    save: () => { throw new Error('boom'); } });
  rec.track({ k: 'open', plan: 'solo' });
  let threw = false;
  try { timers.run(); await tick(); await tick(); } catch (e) { threw = true; }
  ok(!threw, 'a throwing save never reaches the page');

  // load that fails falls back to what this page knows
  timers = fakeTimers(); saves = [];
  rec = R.create({ prev: { v: 1, t0: T1, o: 2, p: 'solo', pl: ['solo'] }, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    load: () => Promise.reject(new Error('network')), save: (co) => { saves.push(co); return Promise.resolve({}); } });
  rec.track({ k: 'open', plan: 'solo' });
  timers.run(); await tick(); await tick();
  eq(saves[0].o, 3, 'a failed re-read uses the record this page loaded');

  // write cap per page load
  timers = fakeTimers(); saves = [];
  rec = R.create({ prev: null, now, cap: 3, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    save: (co) => { saves.push(co); return Promise.resolve({}); } });
  for (let i = 0; i < 6; i++) { rec.track({ k: 'open', plan: 'pro' }); timers.run(); await tick(); await tick(); }
  eq(saves.length, 3, 'at most `cap` writes per page load');
  eq(rec.state().o, 6, 'the page still counts what it could not store');

  // flush() writes at once (used right after a payment, before the page may leave)
  timers = fakeTimers(); saves = [];
  rec = R.create({ prev: null, now, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    save: (co) => { saves.push(co); return Promise.resolve({}); } });
  rec.track({ k: 'open', plan: 'elite' });
  rec.track({ k: 'paid' });
  rec.flush(); await tick(); await tick();
  eq([saves.length, saves[0].r], [1, 'paid'], 'flush writes without waiting');
  timers.run(); await tick();
  eq(saves.length, 1, 'no second write after a flush with nothing new');

  // an identical record is not written again
  timers = fakeTimers(); saves = [];
  const same = { v: 1, t0: T1, o: 1, t: T1, p: 'pro', pl: ['pro'] };
  rec = R.create({ prev: same, now: () => T1, setTimeout: timers.setTimeout, clearTimeout: timers.clearTimeout,
    load: () => Promise.resolve({ v: 1, t0: T1, o: 1, t: T1, p: 'pro', pl: ['pro'], r: 'paid', rt: T1 }),
    save: (co) => { saves.push(co); return Promise.resolve({}); } });
  rec.track({ k: 'paid' });
  timers.run(); await tick(); await tick();
  eq(saves.length, 0, 'nothing written when the stored record already says the same');

  console.log('PASS: ' + passed + ' checkout-record core checks.');
})().catch((e) => { console.error(e); process.exit(1); });
