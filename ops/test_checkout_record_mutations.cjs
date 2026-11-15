/*
 * Mutation check for the checkout record (website repo outreach/62, move 1).
 *   node ops/test_checkout_record_mutations.cjs   (needs Chrome, like test_checkout_record_page.cjs; ~4 minutes)
 * Breaks one thing at a time in plans.html or assets/checkout-record.js, runs the test that should notice, and
 * restores the file byte for byte afterwards (also on failure). Every break must make its test fail.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.join(__dirname, '..');

const PAGE = 'ops/test_checkout_record_page.cjs', CORE = 'ops/test_checkout_record_core.cjs';
const MUTATIONS = [
  ['plans.html', "    if (typeof coFromTrack === 'function') coFromTrack(name, params || {});", '', PAGE, 'track() no longer feeds the record'],
  ['plans.html', "      if (!o.hidden && !coDone[k]) track('plans_checkout_close'", "      if (false) track('plans_checkout_close'", PAGE, 'closes not recorded'],
  ['plans.html', "          if (!busy && !loaded) { loaded = true; track('plans_checkout_loaded', { plan: k }); }", '', PAGE, 'form loaded not recorded'],
  ['plans.html', "      if (!o.hidden && !coDone[k]) track(", "      if (!o.hidden) track(", PAGE, 'close after a payment counted as a close'],
  ['plans.html', "coTrack({ k: 'paid' }); if (coRec) coRec.flush(); }", "coTrack({ k: 'paid' }); }", PAGE, 'payment waits for the debounce'],
  ['plans.html', "      coQueue.splice(0).forEach(function (ev) { coRec.track(ev); });", '', PAGE, 'events from before the start are lost'],
  ['plans.html', "        load: function () { return sb.auth.getUser().then(function (r) { return stored(r && r.data && r.data.user); }); },", '', PAGE, 'no re-read before writing'],
  ['plans.html', "          if (window.ApplePaySession && ApplePaySession.canMakePayments) ev.ap = ApplePaySession.canMakePayments() ? 1 : 0;", '', PAGE, 'Apple Pay not recorded'],
  ['plans.html', "        save: function (co) { return sb.auth.updateUser({ data: { co: co } }); }", "        save: function (co) { return sb.auth.updateUser({ data: { co: co, email_hint: 'x' } }); }", PAGE, 'a second account field is written'],
  ['assets/checkout-record.js', "      if (q.get('promo')) return 'email';", '', CORE, 'trial-ended email source lost'],
  ['assets/checkout-record.js', '    if (!valid(ev)) return base;', '', CORE, 'invalid events create records'],
  ['assets/checkout-record.js', "    if (!org || ref.indexOf(org) !== 0 || !/^($|[\\/?#])/.test(ref.slice(org.length))) return 'other';",
    "    if (!org || ref.indexOf(org) !== 0) return 'other';", CORE, 'look-alike host counted as ours'],
  ['assets/checkout-record.js', '  function inc(n, key) { n[key] = Math.min(MAX, (Number(n[key]) || 0) + 1); }',
    '  function inc(n, key) { n[key] = (Number(n[key]) || 0) + 1; }', CORE, 'counters unbounded'],
  ['assets/checkout-record.js', '        if (same(next, base)) { finish(true, base); return; }', '', CORE, 'identical record written again'],
];

let caught = 0;
for (const [rel, from, to, test, what] of MUTATIONS) {
  const file = path.join(root, rel);
  const orig = fs.readFileSync(file);
  const text = orig.toString('utf8');
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  const f = from.split('\n').join(eol);
  const n = text.split(f).length - 1;
  if (n !== 1) { console.error('MUTATION SETUP: expected 1 match in ' + rel + ', found ' + n + ': ' + from.slice(0, 70)); process.exit(2); }
  try {
    fs.writeFileSync(file, text.replace(f, () => to));
    const r = spawnSync(process.execPath, [path.join(root, test)], { cwd: root, encoding: 'utf8', timeout: 180000 });
    const failed = r.status !== 0;
    console.log((failed ? 'caught  ' : 'MISSED  ') + what + '  (' + path.basename(test) + ')');
    if (failed) caught++;
  } finally {
    fs.writeFileSync(file, orig);
  }
}
console.log((caught === MUTATIONS.length ? 'PASS' : 'FAIL') + ': ' + caught + ' of ' + MUTATIONS.length + ' deliberate breaks caught.');
process.exit(caught === MUTATIONS.length ? 0 : 1);
