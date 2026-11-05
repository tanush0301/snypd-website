/*
 * Mutation check for ops/test_stock_design.cjs: each break below is applied in place, the test must go red, the file is restored.
 *   node ops/test_stock_design_mutations.cjs
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.join(__dirname, '..');
const M = [
  ['assets/stock.js', 'var rev = cst == null ? null : cst - rc - sc;', 'var rev = cst == null ? null : rc - cst - sc;', 'return reversal sign'],
  ['assets/stock.js', "((r.status === 'listed' || r.status === 'reserved') && r.list_cents != null ?", "(r.list_cents != null ?", 'old list price shown on a not-listed row'],
  ['assets/stock.js', "(r.buy_cents == null ? '<span class=\"st-miss\">--</span>' : esc(M(r.buy_cents)))", 'esc(M(cost))', 'Bought column back to cost incl. extras'],
  ['assets/stock.js', 'S.api.updateCategory(key, patch).catch(', 'Promise.resolve().catch(', 'category rename/hide never saved'],
  ['assets/stock.js', "var cv = act === 'cond-pick' ? el.getAttribute('data-c') : '';", "var cv = el.getAttribute('data-c') || 'good';", 'Clear does not clear the condition'],
  ['assets/stock.js', "(v.netCents > 0 ? ' st-pos' : '')", "''", 'hero profit not green'],
  ['assets/stock.js', 'if (s[1]) prev = s[1];', '', 'timeline gaps measured from nothing'],
  ['assets/stock.js', "if (ev.key === 'Enter' && ev.target.id === 'st-catnew') { ev.preventDefault(); catAdd(); return; }", '', 'Enter in "new category" submits the sheet'],
  ['assets/stock.js', 'C.daysBetween(t0, d) >= 0 && C.daysBetween(t0, d) < 30) L.push(T(\'wo.e4\', { a: M(v.netCents), b: M(v.netCents - cst) }));', ') L.push(T(\'wo.e4\', { a: M(v.netCents), b: M(v.netCents - cst) }));', 'write-off net line ignores the date'],
  ['assets/stock.css', '#stock-panel.panel { margin-left: -20px; margin-right: -20px; border-left: 0; border-right: 0; }', '', 'phone frame back'],
  ['assets/stock.css', "@font-face { font-family: 'Cabinet Grotesk';", "@font-face { font-family: 'Cabinet Grotesk X';", 'display font not loaded'],
  ['assets/stock.js', "'<div class=\"st-f full\">' + condButtons(it.condition) + '</div>'", "'<div class=\"st-f full\">' + condButtons('') + '</div>'", 'edit form forgets the condition']
];
let caught = 0;
for (const [file, from, to, name] of M) {
  const f = path.join(root, file), orig = fs.readFileSync(f, 'utf8');
  if (!orig.includes(from)) { console.error('MUTATION TARGET NOT FOUND: ' + name); process.exit(1); }
  fs.writeFileSync(f, orig.replace(from, to));
  let r; try { r = spawnSync(process.execPath, [path.join(__dirname, 'test_stock_design.cjs')], { encoding: 'utf8', timeout: 240000 }); } finally { fs.writeFileSync(f, orig); }
  const red = r.status !== 0; if (red) caught++;
  console.log((red ? 'caught ' : 'MISSED ') + name);
}
console.log(caught + ' of ' + M.length + ' mutations caught');
process.exit(caught === M.length ? 0 : 1);
