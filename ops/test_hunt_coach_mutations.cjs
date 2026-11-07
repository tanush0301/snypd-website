/*
 * Hunt coach + hunter statistics (7 Nov 2026): break dashboard.html one way at a time (in place, always restored) and
 * confirm ops/test_hunt_coach.cjs goes red.   node ops/test_hunt_coach_mutations.cjs
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const FILE = path.join(__dirname, '..', 'dashboard.html');
const TEST = path.join(__dirname, 'test_hunt_coach.cjs');
const M = [
  ['max price added twice', 'if (/[?&]price_to=[^&]*/.test(base)) return', 'if (false) return'],
  ['range can invert', 'if (min !== null && min >= a.suggest.max) return;', ''],
  ['advice for a changed link shown', 'return row && row.is_active === true && row.vinted_url === x.url && !coachDismissed(x);', 'return row && row.is_active === true && !coachDismissed(x);'],
  ['applied advice comes back', "      coachRemember(a);\r\n      coachPaint(['Done:", "      coachPaint(['Done:"],
  ['hunt name not escaped', 'sp.textContent = t;', 'sp.innerHTML = t;'],
  ['undo writes the new link again', 'try { await coachWrite(a.id, before); }', 'try { await coachWrite(a.id, after); }'],
  ['notice for new accounts too', 'if (seen || !(joined < STATS_POLICY_AT)) return;', 'if (seen) return;'],
  ['switch writes the opposite', "sb.rpc('set_hunter_stats_opt_out', { p_out: !counted })", "sb.rpc('set_hunter_stats_opt_out', { p_out: counted })"],
  ['failed save leaves the switch flipped', "          paint(!counted);\r\n", ''],
  ['opted-out account shown as counted', 'paint(!(data && data.hunter_stats_opt_out === true));', 'paint(true);'],
];
const orig = fs.readFileSync(FILE);
const text = orig.toString('utf8');
let missed = 0, setup = 0;
try {
  for (const [name, a, b] of M) {
    if (text.split(a).length !== 2) { console.log('SETUP ERROR (not exactly once): ' + name); setup++; continue; }
    fs.writeFileSync(FILE, text.replace(a, b));
    const r = spawnSync(process.execPath, [TEST], { encoding: 'utf8', timeout: 400000 });
    const caught = r.status !== 0;
    const why = ((r.stdout + r.stderr).match(/AssertionError[^\n]*/) || [''])[0].slice(0, 100);
    console.log((caught ? 'caught  ' : 'MISSED  ') + name + (caught ? '  (' + why + ')' : ''));
    if (!caught) missed++;
  }
} finally {
  fs.writeFileSync(FILE, orig);
}
console.log('mutations: ' + M.length + ', missed: ' + missed + ', setup errors: ' + setup);
process.exit(missed || setup ? 1 : 0);
