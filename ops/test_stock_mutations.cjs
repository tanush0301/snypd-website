/*
 * Proves ops/test_stock_core.cjs can FAIL: copies the Stock files to a temp folder, breaks one thing at a time, and expects the test run to go red.
 *   node ops/test_stock_mutations.cjs
 */
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.join(__dirname, '..');
const files = ['ops/test_stock_core.cjs', 'ops/test_stock_import.cjs', 'ops/stock_engine.js', 'ops/qa_mock.js', 'ops/stock/acceptance-fixture.json', 'ops/stock/acceptance-oracle.json', 'ops/stock/import/template-en.xlsx', 'ops/stock/import/template-fr.xlsx', 'ops/stock/import/mixed-types.xlsx', 'ops/stock/import/shared-strings.xlsx', 'assets/stock-core.js', 'assets/stock-import.js', '.vercelignore'];
const MUTATIONS = [
  ['double-count a reversed sale (history sale rows always count)', 'ops/stock_engine.js', "S.history.some(r => r.item_id === h.item_id && r.kind === 'return' && r.id > h.id)", 'true'],
  ['aging ignores the return date', 'ops/stock_engine.js', 'diffDays(t, i.returned_on || i.bought_on)', 'diffDays(t, i.bought_on)'],
  ['engine Free cap 26 instead of 25', 'ops/stock_engine.js', 'freeHeld: 25', 'freeHeld: 26'],
  ['reversal profit off by one cent', 'ops/stock_engine.js', 'const rev = cost == null ? null : cost - refund +', 'const rev = cost == null ? null : cost - refund - 1 +'],
  ['argument renamed in the engine signature (p_today)', 'ops/stock_engine.js', "stock_overview: ['p_days', 'p_today']", "stock_overview: ['p_days', 'p_on']"],
  ['a SQL error code missing from the client map', 'assets/stock-core.js', "stock_undo_expired: 'conflict',", ''],
  ['negative amounts print an ASCII hyphen', 'assets/stock-core.js', 'if (cents < 0) return MINUS + s;', "if (cents < 0) return '-' + s;"],
  ['money parser guesses repeated separators are decimals', 'assets/stock-core.js', 'if (count > 1) dec = null;', 'if (count > 1) dec = sep;'],
  ['import: day-first dates read month-first', 'assets/stock-import.js', "d = p.a; mo = p.b; }", "d = p.b; mo = p.a; }", 'ops/test_stock_import.cjs'],
  ['import: xlsx date styles ignored (serials stay numbers)', 'assets/stock-import.js', 'val = xfs[+a.s || 0] && isFinite(num) ?', 'val = false && isFinite(num) ?', 'ops/test_stock_import.cjs'],
  ['import: shared strings looked up off by one', 'assets/stock-import.js', "val = v ? (sst[+v[1]] || '') : '';", "val = v ? (sst[+v[1] + 1] || '') : '';", 'ops/test_stock_import.cjs'],
  ['import: sold rows without a price and a date counted as stock', 'assets/stock-import.js', 'if (p.sold_cents != null || soldOn)', 'if (p.sold_cents != null)', 'ops/test_stock_import.cjs'],
  ['import: Free-cap preview lets sold rows consume slots', 'assets/stock-import.js', "r.payload.status !== 'sold' && r.payload.quantity", 'r.payload.quantity', 'ops/test_stock_import.cjs'],
  ['series: write-offs are left out of the daily and platform net', 'ops/stock_engine.js', "- sum(ev.filter(e => e.t === 'wo'), e => e.cost);", ';'],
  ['series: a return is booked under no platform', 'ops/stock_engine.js', 'platform: lastSalePlatform(h), d: h.at,', "platform: '', d: h.at,"],
  ['lanes: the row loses its cost', 'ops/stock_engine.js', 'cost_cents: x.i.buy_cents == null ? null : x.i.buy_cents + x.i.extra_cents, drops', 'cost_cents: null, drops'],
  ['export: the formula guard is removed from text cells', 'assets/stock-core.js', "if (isText && /^[=+\\-@\\t\\r]/.test(s)) s = \"'\" + s;", ''],
  ['export: a missing amount is written as 0.00', 'assets/stock-core.js', "(c == null ? '' : (c / 100)", "(c == null ? '0.00' : (c / 100)"],
  ['export: French file uses a decimal point', 'assets/stock-core.js', "dec = lang === 'fr' ? ',' : '.';", "dec = '.';"],
  ['import: an unrecognised condition is silently accepted as empty without listing it', 'assets/stock-import.js', '(unrec[craw] = unrec[craw] || []).push(n);', '', 'ops/test_stock_import.cjs']
];

let bad = 0;
for (const [name, file, from, to, testFile] of MUTATIONS) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'stockmut-'));
  try {
    for (const f of files) { fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true }); fs.copyFileSync(path.join(root, f), path.join(dir, f)); }
    const target = path.join(dir, file), src = fs.readFileSync(target, 'utf8');
    if (!src.includes(from)) { console.log(`BROKEN MUTATION  ${name}: text not found in ${file}`); bad++; continue; }
    fs.writeFileSync(target, src.replace(from, to));
    const r = spawnSync(process.execPath, [path.join(dir, testFile || 'ops/test_stock_core.cjs')], { encoding: 'utf8', env: Object.assign({}, process.env) });
    if (r.status === 0) { console.log(`MISSED  ${name}: the tests still pass`); bad++; }
    else console.log(`caught  ${name}  ->  ${(r.stdout.match(/^FAIL  (.*)$/m) || [0, r.stderr.split('\n')[0]])[1].slice(0, 100)}  [${(r.stdout.match(/(\d+) of (\d+) FAILED/) || [0, '?', '?']).slice(1, 3).join(' of ')} failed]`);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
}
if (bad) { console.log(`\n${bad} mutation(s) not caught`); process.exit(1); }
console.log(`\nPASS: all ${MUTATIONS.length} mutations are caught`);
