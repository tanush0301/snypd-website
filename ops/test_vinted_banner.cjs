/* "Can't reach Vinted" is judged on the last successful check, not on the last find (19 Nov 2026).
 * Runs the real dashboard code for the heartbeat answer and the banner rule. No network, no browser.
 * Run: node ops/test_vinted_banner.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');
function section(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert(a >= 0 && b > a, 'section not found: ' + start);
  return html.slice(a, b);
}
const state = section('  let hbKnowsChecks = false;', '  async function sendHeartbeat() {');
const rule = section('      let vintedStale = false;', "      setSyncState(vintedStale ? 'vinted_unreachable' : 'ok');");
const MIN = 60000;

function page(startMs) {
  const g = { clock: startMs, console };
  g.Date = { now: () => g.clock, parse: Date.parse };
  g.Number = Number; g.Math = Math;
  const ctx = vm.createContext(g);
  vm.runInContext('const VINTED_STALE_MIN = 15;\n' + state +
    '\nfunction stale(running, feed) {\n' + rule + '\n return vintedStale; }\n' +
    'globalThis.note = noteHeartbeatAnswer; globalThis.stale = stale;', ctx);
  return g;
}
const T0 = 1795000000000;
const iso = ms => new Date(ms).toISOString();
let passed = 0;
const ok = (name, cond) => { assert(cond, name); passed++; };

// 1. A precise search: last find 3 hours ago, checked 20 s ago -> no banner (the bug the founder saw).
let p = page(T0);
p.note({ status: 'ok', searches: 1, last_ok: 1000, now: 1020 });
ok('quiet search, just checked: no banner', p.stale(true, { newestFetchedAt: iso(T0 - 180 * MIN) }) === false);
ok('quiet search, no rows at all: no banner', p.stale(true, { newestFetchedAt: null }) === false);

// 2. Checks stopped getting answers: last answer 16 min ago -> banner, even with a fresh row.
p = page(T0);
p.note({ status: 'ok', searches: 2, last_ok: 1000, now: 1000 + 16 * 60 });
ok('no answer for 16 min: banner', p.stale(true, { newestFetchedAt: iso(T0 - 1 * MIN) }) === true);
p.note({ status: 'ok', searches: 2, last_ok: 1000, now: 1000 + 14 * 60 });
ok('answer 14 min ago: no banner', p.stale(true, { newestFetchedAt: null }) === false);

// 3. The server's clock differs from the device's: only the difference now - last_ok counts.
p = page(T0);
p.note({ status: 'ok', searches: 1, last_ok: 5000000, now: 5000030 });
ok('clock skew ignored', p.stale(true, {}) === false);
p.clock += 16 * MIN;   // no further heartbeat answer
ok('age keeps growing on the device clock', p.stale(true, {}) === true);

// 4. Searches are checked but none has an answer yet: banner only after 15 min of that.
p = page(T0);
p.note({ status: 'ok', searches: 1 });
ok('no answer yet, just started: no banner', p.stale(true, {}) === false);
p.clock += 10 * MIN; p.note({ status: 'ok', searches: 1 });
ok('no answer yet after 10 min: no banner', p.stale(true, {}) === false);
p.clock += 6 * MIN; p.note({ status: 'ok', searches: 1 });
ok('no answer yet after 16 min: banner', p.stale(true, {}) === true);
p.note({ status: 'ok', searches: 1, last_ok: 10, now: 12 });
ok('first answer clears it', p.stale(true, {}) === false);

// 4b. An answer resets the no-answer clock: when answers vanish again later (stamp expired),
// the 15 minutes start afresh instead of counting from the first silence.
p = page(T0);
p.note({ status: 'ok', searches: 1 });
p.clock += 5 * MIN; p.note({ status: 'ok', searches: 1, last_ok: 10, now: 12 });
p.clock += 30 * MIN; p.note({ status: 'ok', searches: 1 });
ok('no-answer clock restarts after an answer', p.stale(true, {}) === false);
p.clock += 16 * MIN; p.note({ status: 'ok', searches: 1 });
ok('and fires 16 min after the new silence', p.stale(true, {}) === true);

// 5. No search being checked (free account, nothing polled): never a banner from this rule.
p = page(T0);
p.note({ status: 'ok', searches: 0 });
p.clock += 60 * MIN; p.note({ status: 'ok', searches: 0 });
ok('no searches checked: no banner', p.stale(true, { newestFetchedAt: iso(T0 - 300 * MIN) }) === false);

// 6. Older backend ({status: ok} only) or an unreadable answer: the old rule, unchanged.
for (const ans of [{ status: 'ok' }, { ok: true }, null, 'x', { searches: '2' }]) {
  p = page(T0);
  p.note(ans);
  ok('old rule: old row -> banner', p.stale(true, { newestFetchedAt: iso(T0 - 16 * MIN) }) === true);
  ok('old rule: fresh row -> none', p.stale(true, { newestFetchedAt: iso(T0 - 2 * MIN) }) === false);
  ok('old rule: no row -> none', p.stale(true, { newestFetchedAt: null }) === false);
}
// a good answer followed by an old-style one falls back too
p = page(T0);
p.note({ status: 'ok', searches: 1, last_ok: 1, now: 2 });
p.note({ status: 'ok' });
ok('falls back when the field disappears', p.stale(true, { newestFetchedAt: iso(T0 - 16 * MIN) }) === true);

// 7. Not running: never a banner.
p = page(T0);
p.note({ status: 'ok', searches: 1, last_ok: 1, now: 5000 });
ok('stopped: no banner', p.stale(false, { newestFetchedAt: iso(T0 - 300 * MIN) }) === false);

// 8. Garbage values never throw.
p = page(T0);
p.note({ status: 'ok', searches: 1, last_ok: 'a', now: {} });
ok('garbage stamps: treated as no answer yet', p.stale(true, {}) === false);
p.note({ status: 'ok', searches: 1, last_ok: 2000, now: 1000 });
ok('last_ok after now: age 0', p.stale(true, {}) === false);

console.log('vinted banner: ' + passed + ' checks passed');
