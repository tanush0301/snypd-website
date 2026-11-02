/*
 * Step 4: the import engine (assets/stock-import.js): CSV, the own .xlsx reader (on files written by openpyxl, ops/stock/import/), header aliases,
 * dates (DD/MM vs MM/DD), money, conditions, categories, quantity, status inference, review numbers, and a run through the QA engine.
 *   node ops/test_stock_import.cjs
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const I = require('../assets/stock-import.js');
const core = require('../assets/stock-core.js');
const Engine = require('./stock_engine.js');

let passed = 0; const failures = []; const queue = [];
const test = (name, fn) => queue.push({ name, fn });
const fx = f => fs.readFileSync(path.join(__dirname, 'stock', 'import', f));
const buf = b => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
const csvPlan = (text, opts) => { const c = I.parseCsv(text); return I.buildPlan({ rows: c.rows, delimiter: c.delimiter }, Object.assign({ lang: 'en', currency: 'EUR', today: '2026-11-02' }, opts)); };
const pay = (plan, i) => plan.rows[i || 0].payload;

// ------------------------------------------------------------------ CSV
test('CSV: delimiter detection, quotes, escaped quotes, embedded newline, BOM, CRLF, blank lines', () => {
  const t = String.fromCharCode(0xfeff) + 'Item,Notes\r\n"Jacket, blue","he said ""hi"""\r\n"Two\nlines",x\r\n\r\n';
  const c = I.parseCsv(t);
  assert.equal(c.delimiter, ','); assert.deepEqual(c.rows, [['Item', 'Notes'], ['Jacket, blue', 'he said "hi"'], ['Two\nlines', 'x']]);
  assert.equal(I.parseCsv('a;b;c\n1;2;3').delimiter, ';'); assert.equal(I.parseCsv('a\tb\n1\t2').delimiter, '\t');
  assert.equal(I.parseCsv('"a;b",c\n1,2').delimiter, ',', 'a delimiter inside quotes does not count');
  assert.deepEqual(I.parseCsv('x,y').rows, [['x', 'y']]);
});
test('header aliases: the 17 template columns (EN), the French names, "A / B" headers, unknown columns ignored', () => {
  const en = ['Item', 'Brand', 'Size', 'Condition', 'Category', 'Quantity', 'Bought', 'Buy price', 'Extra costs', 'Source', 'Platform', 'List price', 'Sold price', 'Sold date', 'Fees', 'Shipping paid', 'Notes'];
  assert.deepEqual(I.mapHeaders(en).map(m => m.field), ['title', 'brand', 'size', 'condition', 'category', 'quantity', 'bought', 'buy', 'extra', 'source', 'platform', 'list', 'sold', 'soldon', 'fee', 'ship', 'notes'], '17 of 17');
  const fr = ['Article', 'Marque', 'Taille', String.fromCharCode(0xc9) + 'tat', 'Cat' + String.fromCharCode(0xe9) + 'gorie', 'Quantit' + String.fromCharCode(0xe9), "Date d'achat", "Prix d" + String.fromCharCode(0x2019) + "achat", 'Frais en plus', 'Source', 'Plateforme', 'Prix affich' + String.fromCharCode(0xe9), 'Prix de vente', 'Date de vente', 'Frais', 'Envoi pay' + String.fromCharCode(0xe9), 'Notes'];
  assert.deepEqual(I.mapHeaders(fr).map(m => m.field), ['title', 'brand', 'size', 'condition', 'category', 'quantity', 'bought', 'buy', 'extra', 'source', 'platform', 'list', 'sold', 'soldon', 'fee', 'ship', 'notes'], 'French names');
  assert.deepEqual(I.mapHeaders(['Extra costs / Frais en plus', 'Fees / Frais', 'List price / Prix affich' + String.fromCharCode(0xe9), 'Shipping paid / Envoi pay' + String.fromCharCode(0xe9), "Date d" + String.fromCharCode(0x2019) + "achat", 'Mystery']).map(m => m.field), ['extra', 'fee', 'list', 'ship', 'bought', null]);
  assert.deepEqual(I.mapHeaders(['Item', 'Item']).map(m => m.field), ['title', null], 'a field is taken once');
  assert.deepEqual(I.buildPlan({ rows: [['Brand'], ['x']] }, {}).errors, ['no_title_column']);
  assert.deepEqual(I.buildPlan({ rows: [] }, {}).errors, ['empty']);
});
test('status inference, quantity, money, notes and row numbers', () => {
  const plan = csvPlan('Item,Buy price,List price,Sold price,Sold date,Bought,Quantity,Platform\nA,10,,,,2026-10-01,,\nB,10,30,,,2026-10-01,3,Vinted\n\nC,10,30,25,2026-10-10,2026-10-01,1,eBay\nD,,,,,2026-10-01,0,\nE,5,,,2026-10-12,2026-10-01,2,\nF,,,,,,51,\n');
  assert.deepEqual(plan.rows.map(r => r.n), [2, 3, 5, 6, 7, 8], 'row numbers are the file\'s own, blank lines kept in the count');
  assert.deepEqual(plan.rows.map(r => r.payload.status), ['stock', 'listed', 'sold', 'stock', 'sold', 'stock']);
  assert.deepEqual(plan.rows.map(r => r.payload.quantity), [1, 3, 1, null, 2, null]);
  assert.deepEqual(plan.rows.filter(r => r.bad).map(r => r.n), [6, 8], 'quantity 0 and 51 are refused');
  assert.equal(I.toRpcRows(plan).length, 4);
  assert.deepEqual(pay(plan, 2), { title: 'C', buy_cents: 1000, extra_cents: 0, list_cents: 3000, sold_cents: 2500, quantity: 1, bought_on: '2026-10-01', platform: 'ebay', status: 'sold', sold_on: '2026-10-10', brand: null, size: null, notes: null, link: null, src: null, condition: null, category: null, fee_cents: null, ship_paid_cents: null });
  assert.equal(plan.stats.noBuy, 2); assert.equal(plan.stats.qtyRows, 2); assert.equal(plan.stats.soldNoDate, 0);
  const rpc = I.toRpcRows(plan); assert(!('brand' in rpc[0].row) && rpc[0].n === 2, 'null fields are not sent, file row number kept');
  assert.equal(I.batches(Array.from({ length: 1201 }, (_, i) => i)).map(b => b.length).join(), '500,500,201');
});
test('a sold price without a sold date uses the buy date and says so; a date without a price is still a sale', () => {
  const p = csvPlan('Item,Buy price,Sold price,Bought,Sold date\nA,10,25,2026-10-01,\nB,10,,2026-10-01,2026-10-09\n');
  assert.deepEqual(p.rows.map(r => [r.payload.status, r.payload.sold_on, r.flags.join()]), [['sold', '2026-10-01', 'sold_no_date'], ['sold', '2026-10-09', '']]); assert.equal(p.stats.soldNoDate, 1);
});

// ------------------------------------------------------------------ dates
test('dates: ISO, day-first, month-first, text months in EN and FR, impossible and future dates', () => {
  const d = (v, o) => I.toIso(I.dateParts(v), o || 'dmy', '2026-11-02');
  assert.equal(d('2026-10-27'), '2026-10-27'); assert.equal(d('27/10/2026'), '2026-10-27'); assert.equal(d('27.10.2026'), '2026-10-27'); assert.equal(d('27-10-26'), '2026-10-27');
  assert.equal(d('10/27/2026', 'mdy'), '2026-10-27'); assert.equal(d('03/04/2026', 'dmy'), '2026-04-03'); assert.equal(d('03/04/2026', 'mdy'), '2026-03-04');
  assert.equal(d('27 Oct 2026'), '2026-10-27'); assert.equal(d('Oct 27, 2026'), '2026-10-27'); assert.equal(d('27 oct. 2026'), '2026-10-27'); assert.equal(d('3 janv. 2026'), '2026-01-03'); assert.equal(d('14 ao' + String.fromCharCode(0xfb) + 't 2026'), '2026-08-14');
  assert.equal(d(46322), '2026-10-27', 'an Excel serial number'); assert.equal(d('31/02/2026'), null); assert.equal(d('27/10/2027'), null, 'future'); assert.equal(d('27/10/1999'), null); assert.equal(d('hello'), null); assert.equal(d(''), null);
});
test('date order: day>12 first decides DMY, day>12 second decides MDY, mixed and unknown are reported', () => {
  const o = (cells) => I.buildPlan({ rows: [['Item', 'Bought'], ...cells.map(c => ['x', c])] }, { today: '2026-11-02' }).review.dateOrder;
  assert.deepEqual([o(['27/10/2026', '03/04/2026']).order, o(['27/10/2026']).certain], ['dmy', true]);
  assert.deepEqual([o(['10/27/2026', '03/04/2026']).order, o(['10/27/2026']).certain], ['mdy', true]);
  const amb = o(['03/04/2026', '05/06/2026']); assert.deepEqual([amb.order, amb.certain, amb.hasNumericDates], ['dmy', false, true]);
  assert.equal(o(['27/10/2026', '10/27/2026']).mixed, true); assert.equal(o(['2026-10-27']).hasNumericDates, false, 'ISO dates are never ambiguous');
  const mdy = I.buildPlan({ rows: [['Item', 'Bought'], ['x', '03/04/2026']] }, { today: '2026-11-02', dateOrder: 'mdy' }); assert.equal(mdy.rows[0].payload.bought_on, '2026-03-04', 'the user\'s choice wins');
});

// ------------------------------------------------------------------ money
test('money: numbers, decimal comma in ; files, thousands, currency words, other-currency symbols are counted, negatives refused', () => {
  const p = csvPlan('Item;Prix d\'achat;Frais en plus;Prix affiche\nA;12,50;1,5;"1.234,56"\nB;EUR 20;;' + String.fromCharCode(0xa3) + '30\nC;-5;;$ 10\nD;abc;;\n');
  assert.deepEqual([pay(p, 0).buy_cents, pay(p, 0).extra_cents, pay(p, 0).list_cents], [1250, 150, 123456]);
  assert.equal(pay(p, 1).buy_cents, 2000); assert.equal(pay(p, 1).list_cents, 3000, 'the symbol is read as the account currency: nothing is converted');
  assert.equal(pay(p, 2).buy_cents, null); assert(p.rows[2].flags.includes('bad_buy')); assert.equal(pay(p, 2).list_cents, 1000); assert(p.rows[3].flags.includes('bad_buy'));
  assert.deepEqual(p.review.mixedCurrencies, { GBP: 1, USD: 1 }); assert.equal(p.stats.mixedCells, 2);
  const usd = csvPlan('Item,Buy price\nA,$12\nB,' + String.fromCharCode(0x20ac) + '5', { currency: 'USD' }); assert.deepEqual(usd.review.mixedCurrencies, { EUR: 1 });
  const num = I.buildPlan({ rows: [['Item', 'Buy price'], ['A', 12.5], ['B', 0], ['C', -1]] }, {}); assert.deepEqual(num.rows.map(r => r.payload.buy_cents), [1250, 0, null]);
});

// ------------------------------------------------------------------ conditions, categories, duplicates, caps
test('conditions: EN and FR grades and spellings map; unknown values are listed with their row numbers; the user\'s choice applies', () => {
  const p = csvPlan('Item,Condition\nA,Very good\nB,Tr' + String.fromCharCode(0xe8) + 's bon ' + String.fromCharCode(0xe9) + 'tat\nC,NWT\nD,Neuf\nE,Comme neuf\nF,Comme neuf\nG,used\nH,\nI,Bon\n');
  assert.deepEqual(p.rows.map(r => r.payload.condition), ['very_good', 'very_good', 'new_with_tag', 'new_no_tag', null, null, null, null, 'good']);
  assert.deepEqual(p.review.unrecognisedConditions, { 'Comme neuf': [6, 7], 'used': [8] });
  assert.deepEqual([p.stats.condSet, p.stats.condEmpty], [5, 4]);
  const q = csvPlan('Item,Condition\nE,Comme neuf\nG,used\n', { conditionMap: { 'comme neuf': 'very_good', used: '' } });
  assert.deepEqual(q.rows.map(r => r.payload.condition), ['very_good', null]); assert.deepEqual(q.review.unrecognisedConditions, {});
});
test('categories: default and renamed categories match in EN/FR, new ones get a key and a name, skipping leaves them empty', () => {
  const p = csvPlan('Item,Category\nA,Outerwear\nB,Vestes et manteaux\nC,Shoes\nD,Vintage\nE,vintage\nF,Sportswear\nG,\nH,Mes pulls\n', { categories: [{ key: 'tops', name: 'Mes pulls' }, { key: 'shoes', name: 'Shoes' }] });
  assert.deepEqual(p.rows.map(r => r.payload.category), ['outerwear', 'outerwear', 'shoes', 'c-vintage', 'c-vintage', 'c-sportswear', null, 'tops']);
  assert.deepEqual(p.review.newCategories, { Vintage: [5], vintage: [6], Sportswear: [7] });
  assert.deepEqual(p.review.newCategoryKeys, [{ key: 'c-vintage', name: 'Vintage' }, { key: 'c-sportswear', name: 'Sportswear' }]);
  const s = csvPlan('Item,Category\nD,Vintage\n', { categoryMap: { vintage: 'skip' } }); assert.equal(pay(s).category, null); assert.deepEqual(s.review.newCategoryKeys, []);
});
test('duplicates are counted and kept by default; skipping removes the repeats; platform names map, unknown becomes Other', () => {
  const csv = 'Item,Buy price,Bought,Platform\nTee,5,2026-10-01,Facebook Marketplace\nTee,5,2026-10-01,Vestiaire Collective\ntee ,5,2026-10-01,Mystery\n';
  const p = csvPlan(csv); assert.equal(p.stats.duplicates, 2); assert.equal(p.rows.length, 3); assert.deepEqual(p.rows.map(r => r.payload.platform), ['facebook', 'vestiaire', 'other']);
  const q = csvPlan(csv, { skipDuplicates: true }); assert.equal(q.rows.length, 1);
});
test('Free cap preview: held items that fit, sold rows never count, the rest is reported', () => {
  const p = csvPlan('Item,Sold price,Sold date,Quantity\nA,,,10\nB,5,2026-10-01,5\nC,,,10\nD,,,10\n', { freeLeft: 22 });
  assert.deepEqual(p.review.freeCap, { left: 22, fits: 20, over: 10 }); assert.equal(csvPlan('Item\nA\n').review.freeCap, null);
});
test('more than 5,000 rows: the first 5,000 are read and the rest is reported', () => {
  const rows = [['Item']]; for (let i = 0; i < 5003; i++) rows.push(['x' + i]);
  const p = I.buildPlan({ rows }, {}); assert.deepEqual([p.rows.length, p.truncated], [5000, 3]);
});

// ------------------------------------------------------------------ XLSX
test('xlsx: the English template written by openpyxl: sheets, real date cells as ISO, numbers stay numbers, the blank row keeps its number', async () => {
  const x = await I.readXlsx(buf(fx('template-en.xlsx')));
  assert.deepEqual(x.sheets.map(s => s.name), ['Items', 'Lists']);
  const rows = x.sheets[0].rows; assert.equal(rows[0].length, 17); assert.equal(rows[0][7], 'Buy price');
  assert.equal(rows[1][6], '2026-09-01', 'date cell -> ISO'); assert.equal(rows[2][7], 12.5); assert.equal(rows[2][8], 1.2); assert.deepEqual(rows[3], [], 'row 4 is blank and stays');
  assert.equal(rows[4][0], 'Nike ACG fleece'); assert.equal(rows[1][16], 'small mark');
  const plan = I.buildPlan({ rows: rows }, { lang: 'en', currency: 'EUR', today: '2026-11-02' });
  assert.deepEqual(plan.rows.map(r => r.n), [2, 3, 5, 6]);
  assert.deepEqual(plan.rows.map(r => r.payload.status), ['sold', 'listed', 'stock', 'listed']);
  assert.deepEqual(plan.rows.map(r => r.payload.quantity), [1, 2, 1, 1]);
  const a = pay(plan, 0); assert.deepEqual([a.buy_cents, a.sold_cents, a.sold_on, a.fee_cents, a.ship_paid_cents, a.bought_on, a.condition, a.category, a.platform, a.src], [3000, 8000, '2026-09-20', 400, 350, '2026-09-01', 'very_good', 'outerwear', 'vinted', 'Charity shop']);
  assert.equal(pay(plan, 2).condition, 'new_with_tag'.replace('new_with_tag', 'new_with_tag')); assert.equal(plan.review.dateOrder.hasNumericDates, false);
  const lists = x.sheets[1].rows; assert.equal(lists[0][2], 'Very good');
});
test('xlsx: the French file with dates and amounts as text, an unknown condition, a new category, quantity 3', async () => {
  const x = await I.readXlsx(buf(fx('template-fr.xlsx'))); assert.equal(x.sheets[0].name, 'Stock');
  const plan = I.buildPlan({ rows: x.sheets[0].rows }, { lang: 'fr', currency: 'EUR', today: '2026-11-02' });
  assert.equal(plan.errors.length, 0); assert.equal(plan.rows.length, 3);
  assert.deepEqual(plan.review.dateOrder, { order: 'dmy', detected: 'dmy', certain: true, mixed: false, sample: '27/10/2026', hasNumericDates: true });
  assert.deepEqual(plan.rows.map(r => r.payload.bought_on), ['2026-10-27', '2026-10-03', '2026-09-15']);
  assert.deepEqual(plan.rows.map(r => r.payload.buy_cents), [3650, 1200, 1000]); assert.equal(pay(plan, 1).extra_cents, 150);
  assert.deepEqual(plan.review.unrecognisedConditions, { 'Comme neuf': [3] }); assert.deepEqual(plan.review.newCategories, { Vintage: [3] });
  assert.deepEqual(plan.rows.map(r => r.payload.quantity), [1, 3, 1]); assert.equal(plan.stats.items, 5);
  const sold = pay(plan, 2); assert.deepEqual([sold.status, sold.sold_cents, sold.sold_on, sold.fee_cents, sold.ship_paid_cents], ['sold', 2800, '2026-09-30', 140, 350]);
  assert.deepEqual(plan.rows.map(r => r.payload.category), ['outerwear', 'c-vintage', 'bottoms']); assert.equal(pay(plan, 1).src, 'Vide-grenier');
});
test('xlsx: entities, rich text, formulas without a cached value, booleans, big numbers, sheet names with spaces', async () => {
  const x = await I.readXlsx(buf(fx('mixed-types.xlsx'))); assert.equal(x.sheets[0].name, 'My items & more'); const r = x.sheets[0].rows;
  assert.equal(r[1][0], 'Jacket <special> & "quoted"'); assert.equal(r[1][2], 'caf' + String.fromCharCode(0xe9) + ' ' + String.fromCharCode(0x2013) + ' notes');
  assert.equal(r[2][0], 'Rich bold text item'); assert.equal(r[2][1], 1234567.89); assert.equal(r[3][1], '', 'a formula with no cached value is empty, never a guess'); assert.equal(r[4][2], 'TRUE');
  const plan = I.buildPlan({ rows: r }, { today: '2026-11-02' }); assert.deepEqual(plan.rows.map(p => p.payload.buy_cents), [2500, 123456789, null, 900]);
});
test('xlsx written by SheetJS with a SHARED-STRINGS table (the layout Excel, Google Sheets and LibreOffice write): strings, entities, accents, date styles, numbers', async () => {
  const x = await I.readXlsx(buf(fx('shared-strings.xlsx'))); assert.equal(x.sheets[0].name, 'Stock list'); const r = x.sheets[0].rows;
  assert.deepEqual(r[0], ['Item', 'Brand', 'Cat' + String.fromCharCode(0xe9) + 'gorie', 'Buy price', 'Bought', 'Notes', 'Quantity']);
  assert.deepEqual(r[1], ['Barbour jacket & co', 'Barbour', 'Outerwear', 12.5, '2026-10-27', 'repeat', 2]); assert.equal(r[3][0], 'Third <item>'); assert.equal(r[3][5], 'caf' + String.fromCharCode(0xe9));
  const plan = I.buildPlan({ rows: r }, { lang: 'fr', today: '2026-11-02' }); assert.deepEqual(plan.rows.map(p => [p.payload.title, p.payload.buy_cents, p.payload.bought_on, p.payload.category, p.payload.quantity]),
    [['Barbour jacket & co', 1250, '2026-10-27', 'outerwear', 2], ['Second item', 800, '2026-10-03', 'outerwear', 1], ['Third <item>', 500, '2026-09-15', 'tops', 1]]);
});
test('xlsx: refusals are clear: not a zip, old .xls, truncated file, too big', async () => {
  const code = async b => { try { await I.readXlsx(b); } catch (e) { return e.code; } return 'none'; };
  assert.equal(await code(buf(Buffer.from('just some text, not a spreadsheet'))), 'not_a_spreadsheet');
  assert.equal(await code(buf(Buffer.from([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1, 0, 0, 0, 0]))), 'xls_unsupported');
  assert.equal(await code(buf(fx('template-en.xlsx').subarray(0, 900))), 'not_a_spreadsheet');
  assert.equal(await code(new ArrayBuffer(I.LIMITS.fileBytes + 1)), 'too_big');
  const file = async (name, bytes) => { try { return (await I.readFile({ name, size: bytes.length, arrayBuffer: async () => buf(bytes) })).kind; } catch (e) { return e.code; } };
  assert.equal(await file('stock.xls', Buffer.from('x')), 'xls_unsupported'); assert.equal(await file('stock.xlsx', fx('template-en.xlsx')), 'xlsx'); assert.equal(await file('renamed.csv', fx('template-en.xlsx')), 'xlsx', 'a zip is recognised by its content');
  assert.equal(await file('s.csv', Buffer.from('Item,Buy price\nTee,5\n')), 'csv');
  const ansi = await I.readFile({ name: 'fr.csv', size: 20, arrayBuffer: async () => buf(Buffer.from([0x41, 0x72, 0x74, 0x69, 0x63, 0x6c, 0x65, 0x3b, 0xc9, 0x74, 0x61, 0x74, 0x0a, 0x78, 0x3b, 0x42, 0x6f, 0x6e, 0x0a])) });
  assert.equal(ansi.sheets[0].table.rows[0][1], String.fromCharCode(0xc9) + 'tat', 'a Windows-1252 CSV is read as such');
});

// ------------------------------------------------------------------ through the QA engine
test('end to end: the French file through the engine (importRows, skipped report, undo this import)', async () => {
  const x = await I.readXlsx(buf(fx('template-fr.xlsx')));
  const plan = I.buildPlan({ rows: x.sheets[0].rows }, { lang: 'fr', currency: 'EUR', today: '2026-11-02', conditionMap: { 'comme neuf': 'very_good' } });
  const eng = Engine.createEngine({ uid: 'u', today: () => '2026-11-02', paid: true }); const api = core.createApi({ rpc: eng.rpc }, { today: () => '2026-11-02' });
  const rows = I.toRpcRows(plan).map(r => r.row), imp = '99999999-9999-4999-8999-999999999999';
  const res = await api.importRows(imp, rows);
  assert.deepEqual([res.rows_inserted, res.items_created, res.skipped.length], [3, 5, 0]);
  const items = eng.state.items.filter(i => i.import_id === imp); assert.equal(items.length, 5);
  assert.deepEqual(items.map(i => i.status).sort(), ['listed', 'sold', 'stock', 'stock', 'stock']);
  assert.equal(items.filter(i => i.condition === 'very_good').length, 4, 'the user\'s mapping of "Comme neuf" was applied');
  assert.deepEqual((await api.undoImport(imp)).removed, 5); assert.equal(eng.state.items.length, 0);
  const free = Engine.createEngine({ uid: 'f', today: () => '2026-11-02', paid: false }); const fapi = core.createApi({ rpc: free.rpc });
  const big = I.buildPlan({ rows: [['Item', 'Quantity']].concat(Array.from({ length: 30 }, (_, i) => ['it' + i, 1])) }, { today: '2026-11-02', freeLeft: 25 });
  const r2 = await fapi.importRows('88888888-8888-4888-8888-888888888888', I.toRpcRows(big).map(r => r.row));
  assert.deepEqual([r2.rows_inserted, r2.skipped.length, r2.free_limit_hit], [25, 5, true]); assert.deepEqual(big.review.freeCap, { left: 25, fits: 25, over: 5 }, 'the preview said the same before sending');
});
test('stock-import.js is pure ASCII and loads without stock-core in a sandbox', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'stock-import.js'), 'utf8');
  assert.equal((src.match(/[^\x20-\x7e\r\n]/g) || []).length, 0);
  const vm = require('node:vm'); const w = {}; vm.runInNewContext(src, { self: w, Blob, DecompressionStream, TextDecoder, TextEncoder, Intl, window: w }); assert(w.SnypdStockImport && w.SnypdStockImport.buildPlan);
});

(async () => {
  for (const t of queue) { try { await t.fn(); passed++; } catch (e) { failures.push({ name: t.name, error: e }); } }
  if (failures.length) { for (const f of failures) console.log('FAIL  ' + f.name + '\n      ' + String(f.error && f.error.stack || f.error).split('\n').slice(0, 7).join('\n      ')); console.log(`\n${failures.length} of ${passed + failures.length} FAILED`); process.exit(1); }
  console.log(`PASS: ${passed} of ${passed + failures.length} import checks (CSV, own xlsx reader on real files, aliases, dates, money, review numbers, engine round trip)`);
})();
