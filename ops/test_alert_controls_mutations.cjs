/*
 * Live-review fixes (Session 67): break dashboard.html one way at a time (in place, always restored) and confirm the
 * test that owns that behaviour goes red.   node ops/test_alert_controls_mutations.cjs
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const FILE = path.join(__dirname, '..', 'dashboard.html');
const T = n => path.join(__dirname, n);
const M = [
  ['hidden attribute loses to .btn again', '[hidden] { display: none !important; }', '', 'test_alert_controls.cjs'],
  ['"Not now" ignored on reload', '(actionable && !cardSnoozed())', 'actionable', 'test_alert_controls.cjs'],
  ['Test button back after a successful test', "testBtn.hidden = st !== 'on' || testedHere();", "testBtn.hidden = st !== 'on';", 'test_alert_controls.cjs'],
  ['blocked chip without the guide link', "alertsChip.setAttribute('href', href);", '', 'test_alert_controls.cjs'],
  ['phone shows the stats again', ', #dashboard-panel:not(.status-open) #feed-stats { display: none; }', ' { display: none; }', 'test_alert_controls.cjs'],
  ['greyed "Running..." button back', '#btn-start:disabled { display: none; }', '', 'test_alert_controls.cjs'],
  ['quiet hours saved without the time zone', '{ p_on: next, p_tz: tz }', "{ p_on: next, p_tz: 'UTC' }", 'test_alert_controls.cjs'],
  ['unclaim ignores earlier reversals', ", 'unclaim_reversal', 'reconcile']).eq('item_id', itemId);", "]).eq('item_id', itemId);", 'test_alert_controls.cjs'],
  ['repeat unclaim not blocked', '      if (reversingItems.has(itemId)) return;\r\n', '', 'test_alert_controls.cjs'],
  ['Hunt this below keeps the EUR30 minimum', "if (minPriceInput && qMax && qMax.value) { minPriceInput.value = '';", "if (false) { minPriceInput.value = '';", 'test_market_board.cjs'],
  ['chart sheet under the top bar', '.mr-sheet { position: fixed; inset: 0; z-index: 500;', '.mr-sheet { position: fixed; inset: 0; z-index: 90;', 'test_market_board.cjs'],
  ['all brands at once', '(mbHuntAll ? hs : hs.slice(0, 8))', 'hs', 'test_market_board.cjs'],
  ['thin conditions listed one by one', "if (c.status !== 'ok' && c.status !== 'mixed') { thinN += c.finds || 0; return; }", 'if (false) {}', 'test_hunt_report.cjs'],
];
const orig = fs.readFileSync(FILE);
const text = orig.toString('utf8');
let missed = 0, setup = 0;
try {
  for (const [name, a, b, test] of M) {
    if (text.split(a).length !== 2) { console.log('SETUP ERROR (not exactly once): ' + name); setup++; continue; }
    fs.writeFileSync(FILE, text.replace(a, b));
    const r = spawnSync(process.execPath, [T(test)], { encoding: 'utf8', timeout: 400000 });
    const caught = r.status !== 0;
    console.log((caught ? 'caught  ' : 'MISSED  ') + name + (caught ? '  (' + ((r.stdout + r.stderr).match(/FAIL: [^\n]*/) || [''])[0].slice(0, 90) + ')' : ''));
    if (!caught) missed++;
  }
} finally {
  fs.writeFileSync(FILE, orig);
}
console.log((M.length - missed - setup) + ' of ' + M.length + ' UI mutations caught' + (setup ? ', ' + setup + ' setup errors' : ''));
process.exit(missed || setup ? 1 : 0);
