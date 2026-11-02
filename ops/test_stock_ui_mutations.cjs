/*
 * Proves ops/test_stock_ui.cjs can FAIL on the Step 5 behaviour: breaks one thing at a time IN PLACE, runs the browser test, restores the file (finally block;
 * the original text is also held in memory, so an abort in the middle of a run leaves at most the one file being tested: check `git diff` if you kill it).
 *   node ops/test_stock_ui_mutations.cjs            (about 2 minutes per mutation, needs Chrome like test_stock_ui.cjs)
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.join(__dirname, '..');
const MUTATIONS = [
  ['boot ignores stock_tab_hidden (a hidden tab comes back on every page load)', 'dashboard.html', 'window.SNYPD.onStockMode(_sm, boot.data.stock_tab_hidden);', 'window.SNYPD.onStockMode(_sm);'],
  ['a History link no longer lands on Stock while Stock replaces History', 'dashboard.html', "window.SNYPD.stockReplacesHistory()) view = 'stock';", "window.SNYPD.stockReplacesHistory()) view = view;"],
  ['the History tab stays visible next to Stock', 'dashboard.html', "el.style.display = showStock ? 'none' : ''; });\n    var row", "el.style.display = ''; });\n    var row"],
  ['currency saved but the screen keeps the old one', 'assets/stock.js', 'S.cur = r[1].currency || S.cur; ', ''],
  ['a Today lane item cannot be opened when the Items list was never loaded', 'assets/stock.js', 'S.api.itemById(id).then(go)', 'Promise.resolve(null).then(go)'],
  ['Skip writes a persona', 'assets/stock.js', "case 'pq-skip': setSkipped();", "case 'pq-skip': answerPersona('resell'); setSkipped();"],
  ['old threshold below 7 accepted', 'assets/stock.js', '|| +oldv < 7 ||', '|| +oldv < 1 ||'],
  ['a partial sales count is shown as complete', 'assets/stock-core.js', 'partial: c.with_cost < c.sold,', 'partial: false,'],
  ['lane rule moved (reprice after 20 days instead of 30)', 'ops/stock_engine.js', "diffDays(t, x.i.listed_on) >= 30 && x.i.drops === 0", "diffDays(t, x.i.listed_on) >= 20 && x.i.drops === 0"]
];
const only = process.argv[2] ? +process.argv[2] : null;
let bad = 0;
MUTATIONS.forEach(([name, file, from, to], k) => {
  if (only != null && only !== k) return;
  const target = path.join(root, file), buf = fs.readFileSync(target), src = buf.toString('utf8'), crlf = src.includes('\r\n');
  const norm = crlf ? src.replace(/\r\n/g, '\n') : src;
  if (norm.split(from).length !== 2) { console.log(`BROKEN MUTATION  ${name}: text found ${norm.split(from).length - 1} times in ${file}`); bad++; return; }
  let out = norm.replace(from, () => to); if (crlf) out = out.replace(/\n/g, '\r\n');
  try {
    fs.writeFileSync(target, out);
    const r = spawnSync(process.execPath, [path.join(__dirname, 'test_stock_ui.cjs')], { encoding: 'utf8', timeout: 280000 });
    if (r.status === 0) { console.log(`MISSED  ${name}: the browser test still passes`); bad++; }
    else console.log(`caught  ${name}  ->  ${((r.stdout + r.stderr).match(/FAIL[^\n]*?: ([^\n]*)/) || [0, 'failed'])[1].slice(0, 110)}`);
  } finally { fs.writeFileSync(target, buf); }
});
if (bad) { console.log(`\n${bad} problem(s)`); process.exit(1); }
console.log(`\nPASS: all ${only != null ? 1 : MUTATIONS.length} UI mutations are caught`);
