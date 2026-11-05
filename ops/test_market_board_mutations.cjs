/*
 * Market board (Session 67): break dashboard.html one way at a time (in place, always restored) and confirm
 * ops/test_market_board.cjs goes red.   node ops/test_market_board_mutations.cjs
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const FILE = path.join(__dirname, '..', 'dashboard.html');
const TEST = path.join(__dirname, 'test_market_board.cjs');
const M = [
  ['teaser shows 3 per column', 'slice(0, full ? 3 : 1)', 'slice(0, 3)'],
  ['item names not escaped', "'<span data-i18n-skip>' + escapeHtml(mbName(i)) + '</span>'", "'<span data-i18n-skip>' + mbName(i) + '</span>'"],
  ['EUR maximum kept on a non-euro account', "if (cur !== 'EUR' && btn &&", 'if (false && btn &&'],
  ['Pay at most ignores the margin', "<b data-mr-max>' + eur(Math.round(t * (100 - m) / 100))", "<b data-mr-max>' + eur(Math.round(t * 50 / 100))"],
  ['weekly report back under the header', '<div id="hr-box" class="hr hr--top" style="display:none"></div>\r\n<div class="hd">', '<div class="hd">\r\n<div id="hr-box" class="hr hr--top" style="display:none"></div>'],
  ['board asked again on every visit', 'Date.now() - mbAt < 1800000', 'Date.now() - mbAt < 0'],
  ['mix line dropped', 'if (c.mix) {', 'if (false) {'],
  ['hunt sheet ignores the first hunt site', 'if (site) qSite.value = site;', ''],
  ['teaser row opens the chart', "if (!mbData || mbData.tier !== 'full' || !i.series) {", 'if (!i.series) { i.series = { typical: [], low: [], high: [], listings: [] }; } if (false) {'],
  ['Filters button shown on Market', "(view === 'stock' || view === 'market') ? 'hidden'", "view === 'stock' ? 'hidden'"],
  ['falling sign lost', "(p > 0 ? '+' : (p < 0 ? '&minus;' : ''))", "(p > 0 ? '+' : '')"],
];
const orig = fs.readFileSync(FILE);
const text = orig.toString('utf8');
let missed = 0, setup = 0;
try {
  for (const [name, a, b] of M) {
    if (a === b) continue;
    if (text.split(a).length !== 2) { console.log('SETUP ERROR (not exactly once): ' + name); setup++; continue; }
    fs.writeFileSync(FILE, text.replace(a, b));
    const r = spawnSync(process.execPath, [TEST], { encoding: 'utf8', timeout: 300000 });
    const caught = r.status !== 0;
    console.log((caught ? 'caught  ' : 'MISSED  ') + name + (caught ? '  (' + ((r.stdout + r.stderr).match(/FAIL: [^\n]*/) || [''])[0].slice(0, 90) + ')' : ''));
    if (!caught) missed++;
  }
} finally {
  fs.writeFileSync(FILE, orig);
}
const n = M.filter(m => m[1] !== m[2]).length;
console.log((n - missed - setup) + ' of ' + n + ' UI mutations caught' + (setup ? ', ' + setup + ' setup errors' : ''));
process.exit(missed || setup ? 1 : 0);
