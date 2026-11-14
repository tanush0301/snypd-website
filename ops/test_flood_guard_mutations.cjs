/*
 * Mutation check for the flood guard (website outreach/62 move 3).
 *   node ops/test_flood_guard_mutations.cjs   (needs Chrome; about 10 minutes)
 * Breaks one thing at a time in dashboard.html, runs the test that should notice, and restores the file byte for byte
 * afterwards (also on failure). Every break must make its test fail.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.join(__dirname, '..');
const FILE = path.join(root, 'dashboard.html');
const BROWSER = 'ops/test_flood_guard.cjs', CARD = 'ops/test_broad_hunt.cjs';

const MUTATIONS = [
  ['          if (mx && max === null && wqNoMax !== words) {', '          if (false) {', BROWSER, 'wizard nudge never shown'],
  ['          if (min !== null && max !== null && min >= max && !minEdited && wqMin && min === vq.floorFor(wqSite.value)) {', '          if (false) {', BROWSER, 'untouched default minimum still refuses'],
  ['min >= max && !minEdited && wqMin && min === vq.floorFor', 'min >= max && wqMin && min === vq.floorFor', BROWSER, 'a typed minimum is cleared too'],
  ['        if (mx && !/[?&]price_to=[0-9]/.test(url) && mxKeptUrl !== url) {', '        if (false) {', BROWSER, 'sheet nudge never shown'],
  ['          }, () => { mxKeptUrl = url; addHunt(); });', '          }, () => { addHunt(); });', BROWSER, 'sheet "Start without a max" loops'],
  ['      return isFinite(v) && v > 0 ? Math.round(v * 100) / 100 : null;', '      return isFinite(v) ? Math.round(v * 100) / 100 : null;', BROWSER, 'a max of 0 accepted'],
  ["    card.dataset.kind = 'broad';", "    card.dataset.kind = '';", BROWSER, 'busy card does not stamp its kind'],
  ['      const p25 = Math.floor(amounts[Math.floor((amounts.length - 1) * 0.25)]);', '      const p25 = Math.floor(amounts[Math.floor((amounts.length - 1) * 0.5)]);', CARD, 'suggestion is the median, not the cheapest quarter'],
  ['      if (p25 >= 1 && !(isFinite(curMax) && p25 >= curMax) && !(floor !== null && p25 <= floor)) suggest = p25;', '      if (p25 >= 1 && !(floor !== null && p25 <= floor)) suggest = p25;', CARD, 'suggestion ignores a lower existing max'],
  ['      if (p25 >= 1 && !(isFinite(curMax) && p25 >= curMax) && !(floor !== null && p25 <= floor)) suggest = p25;', '      if (p25 >= 1 && !(isFinite(curMax) && p25 >= curMax)) suggest = p25;', CARD, 'suggestion ignores the minimum'],
  ['    if (broadHunt && amounts.length >= 8) {', '    if (broadHunt && amounts.length >= 1) {', CARD, 'suggestion from too few prices'],
  ["calmAllBtn.style.display = broadBusy.length >= 2 ? '' : 'none';", "calmAllBtn.style.display = broadBusy.length >= 3 ? '' : 'none';", CARD, 'Calm all hidden for two busy hunts'],
  ["    broadBusy = allRows.filter(h => h.is_active === true && (h.push_mode || 'every') === 'every' && busySigs", '    broadBusy = allRows.filter(h => h.is_active === true && busySigs', CARD, 'hunts already on Calm counted as busy'],
  ['if (coachShown.feed) broadRemember(coachShown.sig); ', '', CARD, 'Keep it on a suggestion forgets the busy hunt'],
  ["        h.push_mode = 'calm'; h.push_calm_minutes = 15; done++;", "        h.push_mode = 'calm'; h.push_calm_minutes = 15;", CARD, 'Calm all miscounts what it switched'],
];

let caught = 0;
for (const [from, to, test, what] of MUTATIONS) {
  const orig = fs.readFileSync(FILE);
  const text = orig.toString('utf8');
  const n = text.split(from).length - 1;
  if (n !== 1) { console.error('MUTATION SETUP: expected 1 match, found ' + n + ': ' + from.slice(0, 80)); process.exit(2); }
  try {
    fs.writeFileSync(FILE, text.replace(from, () => to));
    const r = spawnSync(process.execPath, [path.join(root, test)], { cwd: root, encoding: 'utf8', timeout: 240000 });
    const failed = r.status !== 0;
    console.log((failed ? 'caught  ' : 'MISSED  ') + what + '  (' + path.basename(test) + ')');
    if (failed) caught++;
  } finally {
    fs.writeFileSync(FILE, orig);
  }
}
console.log((caught === MUTATIONS.length ? 'PASS' : 'FAIL') + ': ' + caught + ' of ' + MUTATIONS.length + ' deliberate breaks caught.');
process.exit(caught === MUTATIONS.length ? 0 : 1);
