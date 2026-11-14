/*
 * Mutation check for the paying customer's first-days check (website outreach/62 move 2).
 *   node ops/test_paid_check_mutations.cjs   (needs Chrome; about 8 minutes)
 * Breaks one thing at a time in dashboard.html, runs ops/test_paid_check.cjs, and restores the file byte for byte
 * afterwards (also on failure). Every break must make the test fail.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.join(__dirname, '..');
const FILE = path.join(root, 'dashboard.html');
const TEST = path.join(root, 'ops/test_paid_check.cjs');

const MUTATIONS = [
  ["        try { localStorage.setItem('snypd_paid_check', JSON.stringify({ p: plan, t: Date.now() })); } catch (e) {}", '', 'activation does not start the check'],
  ['    return !!(s && !s.done && age >= 0 && age < PAID_CHECK_MS);', '    return !!(s && !s.done && age >= 0);', 'the check never expires'],
  ['    return !!(s && !s.done && age >= 0 && age < PAID_CHECK_MS);', '    return !!(s && age >= 0 && age < PAID_CHECK_MS);', 'Done is ignored'],
  ["    try { localStorage.setItem(PAID_CHECK_KEY, JSON.stringify(s)); } catch (e) {}", '', 'Done is not stored'],
  ['    if (!paidCheckActive() || !PAID_LIMITS[plan]) { card.style.display = \'none\'; return; }', '    if (!paidCheckActive()) { card.style.display = \'none\'; return; }', 'shown on Free'],
  ['    const phone = /^(ios|android)/.test(dev);', '    const phone = false;', 'a phone is not recognised'],
  ["    const open = active.filter(h => (h.push_mode || 'every') === 'every' && !/[?&]price_to=[0-9]/.test(String(h.vinted_url || '')));", "    const open = active.filter(h => (h.push_mode || 'every') === 'every');", 'a max price does not count'],
  ["    const open = active.filter(h => (h.push_mode || 'every') === 'every' && !/[?&]price_to=[0-9]/.test(String(h.vinted_url || '')));", "    const open = active.filter(h => !/[?&]price_to=[0-9]/.test(String(h.vinted_url || '')));", 'Calm searches counted as a flood risk'],
  ["    if (plan && paidCheckActive()) { try { localStorage.setItem('snypd_ref_live_later', plan); } catch (e) {} return; }", '', 'referral card does not wait'],
  ['      referralPlanLiveCard();\n    }\n  }\n  async function paintPaidCheck() {', '    }\n  }\n  async function paintPaidCheck() {', 'referral card never comes back after Done'],
  ["          try { if (window.SNYPD && typeof window.SNYPD.enableAlerts === 'function') await window.SNYPD.enableAlerts(); } catch (er) {}", '', 'Turn on alerts does nothing'],
  ["          if (pill) pill.click(); else { const add = document.getElementById('empty-add-hunt'); if (add) add.click(); }", '', 'Review them does nothing'],
  ["      if (active.length < limit) s.push('Your plan allows ' + limit + '.');", '', 'plan limit not said'],
];

let caught = 0;
for (const [from, to, what] of MUTATIONS) {
  const orig = fs.readFileSync(FILE);
  const text = orig.toString('utf8');
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  const f = from.split('\n').join(eol), t = to.split('\n').join(eol);
  const n = text.split(f).length - 1;
  if (n !== 1) { console.error('MUTATION SETUP: expected 1 match, found ' + n + ': ' + from.slice(0, 80)); process.exit(2); }
  try {
    fs.writeFileSync(FILE, text.replace(f, () => t));
    const r = spawnSync(process.execPath, [TEST], { cwd: root, encoding: 'utf8', timeout: 240000 });
    const failed = r.status !== 0;
    console.log((failed ? 'caught  ' : 'MISSED  ') + what);
    if (failed) caught++;
  } finally {
    fs.writeFileSync(FILE, orig);
  }
}
console.log((caught === MUTATIONS.length ? 'PASS' : 'FAIL') + ': ' + caught + ' of ' + MUTATIONS.length + ' deliberate breaks caught.');
process.exit(caught === MUTATIONS.length ? 0 : 1);
