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
  ['assets/stock.js', "'<div class=\"st-f full\">' + condButtons(it.condition) + '</div>'", "'<div class=\"st-f full\">' + condButtons('') + '</div>'", 'edit form forgets the condition'],
  // live-check fixes 1-10 (5 Nov 2026)
  ['assets/stock.js', "T(wag === 1 ? 'dt.day1' : 'dt.days', { n: wag })", "T('dt.days', { n: wag })", 'fix 1: "1 days" is back'],
  ['assets/stock.js', "T(wo ? 'wo.e4' : 'ret.e4',", "T('wo.e4',", 'fix 2: the return talks about write-offs'],
  ['assets/stock.js', "if (n > 1) svg += '<text x=", "if (n > 1) svg += '<polyline class=\"st-cumline\" points=\"0,0\"/><text x=", 'fix 3: a running-total line is drawn'],
  ['assets/stock.js', "return s[1] || i === next; });", "return true; });", 'fix 4: every timeline step, dates or not'],
  ['assets/stock.js', "(sold ? mrow('dt.net',", "(true ? mrow('dt.net',", 'fix 4: net profit row on unsold items'],
  ['assets/stock.js', '<details class="st-dsec st-histbox" id="st-histbox">', '<details class="st-dsec st-histbox" id="st-histbox" open>', 'fix 5: history always open'],
  ['assets/stock.js', "if (box && h.some(function (x) { return x.kind === 'return' || x.kind === 'write_off'; })) box.open = true;", '', 'fix 5: a return does not open the history'],
  ['assets/stock.js', "(o.lanes && !worth ?", "(false ?", 'fix 6: three empty lane cards are back'],
  ['assets/stock.js', "return v === today(); } catch (e) { return true; } }", "return true; } catch (e) { return true; } }", 'fix 7: the currency note on every visit'],
  ['assets/stock.js', "'</div><p class=\"st-hint\" id=\"st-addlog\" aria-live=\"polite\">' + esc(T('sheet.add.keys')) + '</p>';", "'</div><p class=\"st-hint\" id=\"st-addlog\" aria-live=\"polite\">' + esc(T('sheet.add.keys')) + '</p><p class=\"st-hint\">' + esc(T('sheet.add.hint')) + '</p>';", 'fix 8: the extra hint lines are back'],
  ['assets/stock.js', "fld('buy', T('f.buy'), mny('buy')) + fld('bought', T('f.bought'), dat('bought', t0, t0)) +" + String.fromCharCode(10) + "        '<div class=\"st-f full\">' + condButtons('') + '</div>'", "'<div class=\"st-f full\">' + condButtons('') + '</div>' + fld('buy', T('f.buy'), mny('buy')) + fld('bought', T('f.bought'), dat('bought', t0, t0))", 'fix 9: buy price after the condition again'],
  ['assets/stock.js', "if (!open && b) b.focus();", "if (open) { var f = $('#st-catman .st-in'); if (f) f.focus(); } else if (b) b.focus();", 'fix 10: the cursor jumps into the first rename field'],
  ['assets/stock.js', 'st-catset" data-act="cat-manage"', 'st-catset" data-act="cat-manage-x"', 'fix 10: Settings cannot manage categories'],
  // polish 11-14 (5 Nov 2026)
  ['assets/stock.js', "var nextAct = (r.status === 'stock' || r.status === 'returned') ? 'list' :", "var nextAct = (r.status === 'stock' || r.status === 'returned') ? 'sold' :", 'polish 11: not-listed cards offer Mark sold again'],
  ['assets/stock.js', "esc(T('act.details'))", "esc(T('act.edit'))", 'polish 11: the card button says Edit again'],
  ['assets/stock.css', '@media (max-width: 720px) { .st-row > .c-pop.st-nopop { display: none; } }', '', 'polish 11: lone "--" on phone cards'],
  ['assets/stock.js', "if (back && k !== 'detail' && findRow(back)) openDetail(back);", '', 'polish 12: Cancel drops to the list'],
  ['assets/stock.js', "S.sheet = null; S.returnTo = null;", "S.sheet = null;", 'polish 12: a stale way back survives a saved action'],
  ['assets/stock.js', "(soldIn != null ? esc(T('age.soldin', { n: soldIn })) : '<span class=\"st-miss\">--</span>')", "'<span class=\"st-miss\">--</span>'", 'polish 13: sold rows show "--" again'],
  ['assets/stock.js', "ab.className = 'st-btn ' + (v === 'money' ? 'st-ghost' : 'st-prim');", "ab.className = 'st-btn st-prim';", 'polish 14: two purple buttons on Money'],
  ['assets/stock.js', "canRepeat = !!mo.pnl && (pm ? pm.expenses > 0 : true);", "canRepeat = true;", 'polish 14: Repeat last month with nothing to repeat']
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
