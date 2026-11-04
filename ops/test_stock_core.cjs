/*
 * Step 2 of the Stock build: tests for the data layer (assets/stock-core.js) and the QA port of the RPCs (ops/stock_engine.js).
 *   node ops/test_stock_core.cjs
 * Sections
 *   C  contract with the SQL: enums, caps, error codes, argument names are diffed against backend-repo migrations 065/066/067
 *      (SNYPD_BACKEND env var, default C:/Users/Tanus/snypd_codebase). If the backend repo is not there the section is reported as SKIPPED, loudly.
 *   M  money helpers: formatting for 8 currencies x en/fr, the design's hero test strings, parsing, round trips
 *   E  error mapping
 *   H  item / overview helpers ("29 of 31", free-cap meter)
 *   A  ACCEPTANCE: the frozen design dataset through createApi() -> engine, against acceptance-oracle.json (the same oracle the SQL tests use)
 *   L  hand-worked lifecycle (the exact numbers of backend ops/stock_tests/tests_b.sql B7/B7b)
 *   F  free cap 25 held, 5,000 cap, Hunt Pass, claims mirror, import batches, kill switch, PostgREST argument contract, items page
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const core = require('../assets/stock-core.js');
const Engine = require('./stock_engine.js');

const fx = JSON.parse(fs.readFileSync(path.join(__dirname, 'stock', 'acceptance-fixture.json'), 'utf8'));
const oracle = JSON.parse(fs.readFileSync(path.join(__dirname, 'stock', 'acceptance-oracle.json'), 'utf8'));
const BACKEND = process.env.SNYPD_BACKEND || 'C:/Users/Tanus/snypd_codebase';

let passed = 0; const failures = []; const queue = [];
function test(name, fn) { queue.push({ name, fn }); }
async function run() {
  for (const t of queue) {
    try { await t.fn(); passed++; } catch (e) { failures.push({ name: t.name, error: e }); }
  }
}
async function rejects(promise, code, why) {
  try { await promise; } catch (e) { assert.equal(e.code, code, `${why || ''} expected ${code}, got ${e.code} (${e.message})`); return e; }
  throw new Error(`${why || ''} expected rejection ${code}, but it resolved`);
}
const clock = { t: Date.UTC(2026, 9, 27, 12, 0, 0) };
function account(o) {
  o = o || {};
  const eng = Engine.createEngine({ uid: o.uid || 'user-1', today: () => o.today || '2026-10-27', now: () => clock.t, paid: o.paid !== false, mode: o.mode || 'all', admin: !!o.admin, searches: o.searches || [] });
  const api = core.createApi({ rpc: eng.rpc }, { today: () => o.today || '2026-10-27' });
  return { eng, api };
}
const money = (c, lang) => core.formatMoney(c, 'EUR', lang || 'en');

// =========================================================================================== C: contract with the SQL
let sql = null;
try {
  const dir = path.join(BACKEND, 'ops', 'migrations');
  sql = { t065: fs.readFileSync(path.join(dir, '065_stock_tables.sql'), 'utf8'), t066: fs.readFileSync(path.join(dir, '066_stock_rpcs.sql'), 'utf8'), t067: fs.readFileSync(path.join(dir, '067_stock_claims_mirror.sql'), 'utf8'), t069: fs.readFileSync(path.join(dir, '069_stock_overview_series_and_lane_rows.sql'), 'utf8'), t070: fs.readFileSync(path.join(dir, '070_stock_counts.sql'), 'utf8'), t071: fs.readFileSync(path.join(dir, '071_stock_items_sort_and_photos.sql'), 'utf8'), t072: fs.readFileSync(path.join(dir, '072_stock_expenses.sql'), 'utf8') };
} catch (e) { sql = null; }
const listIn = (text, col) => { const m = new RegExp('\\b' + col + '\\s+text[^,]*?check\\s*\\(\\s*' + col + '\\s+in\\s*\\(([^)]*)\\)\\s*\\)').exec(text); assert(m, 'no CHECK list for column ' + col); return [...m[1].matchAll(/'([^']+)'/g)].map(x => x[1]); };
if (sql) {
  test('C enums in stock-core == engine == migration 065 (status, platform, condition, write-off reason, src type, currency, persona, history kind)', () => {
    const pairs = [['status', 'STATUSES', 'status'], ['platform', 'PLATFORMS', 'platform'], ['condition', 'CONDITIONS', 'condition'], ['write_off_reason', 'WRITE_OFF_REASONS', 'writeOffReason'],
      ['src_type', 'SRC_TYPES', 'srcType'], ['currency', 'CURRENCIES', 'currency'], ['persona', 'PERSONAS', 'persona'], ['kind', 'HISTORY', 'historyKind']];
    for (const [col, coreKey, engKey] of pairs) {
      const fromSql = listIn(sql.t065, col);
      assert.deepEqual(Engine.ENUMS[engKey], fromSql, `engine ${engKey} != SQL ${col}`);
      if (coreKey !== 'HISTORY') assert.deepEqual(core[coreKey], fromSql, `core ${coreKey} != SQL ${col}`);
    }
    assert.deepEqual(core.HELD, Engine.ENUMS.held);
  });
  test('C caps in stock-core == engine == SQL (25 held, 5,000 items, 50 per add, 500 per import call, 30 categories, 30 days deleted, money max)', () => {
    const num = (re, text) => { const m = re.exec(text); assert(m, 'cap not found: ' + re); return +m[1]; };
    assert.equal(num(/stock_free_cap\(\) returns integer language sql immutable as \$\$ select (\d+)/, sql.t065), core.CAPS.freeHeld);
    assert.equal(core.CAPS.freeHeld, Engine.CAPS.freeHeld);
    assert.equal(num(/v_room := (\d+) - v_total/, sql.t066), core.CAPS.itemsPerAccount);
    assert.equal(core.CAPS.itemsPerAccount, Engine.CAPS.items);
    assert.equal(num(/v_qty > (\d+) then raise exception 'stock_quantity_range'/, sql.t066), core.CAPS.quantityPerAdd);
    assert.equal(core.CAPS.quantityPerAdd, Engine.CAPS.quantity);
    assert.equal(num(/jsonb_array_length\(p_rows\) > (\d+)/, sql.t066), core.CAPS.importBatch);
    assert.equal(core.CAPS.importBatch, Engine.CAPS.importBatch);
    assert.equal(num(/count\(\*\) from public\.stock_categories c where c\.user_id = new\.user_id\) >= (\d+)/, sql.t065), core.CAPS.categories);
    assert.equal(core.CAPS.categories, Engine.CAPS.categories);
    assert.equal(num(/deleted_at < now\(\) - interval '(\d+) days'/, sql.t066), core.CAPS.deletedDays);
    assert.equal(num(/created_at < now\(\) - interval '(\d+) seconds'/, sql.t066), Engine.CAPS.undoSeconds);
    assert.equal(num(/buy_cents\s+bigint check \(buy_cents between 0 and (\d+)\)/, sql.t065), core.CAPS.moneyMaxCents);
    assert.equal(core.CAPS.moneyMaxCents, Engine.CAPS.money);
    assert.deepEqual([...sql.t066.matchAll(/\('([a-z]+)', '[^']+', \d+\)/g)].map(m => m[1]), core.DEFAULT_CATEGORY_KEYS);
    assert.deepEqual(Engine.DEFAULT_CATEGORIES.map(c => c[0]), core.DEFAULT_CATEGORY_KEYS);
  });
  test('C expense categories in stock-core == the CHECK in migration 072', () => {
    const m = /category\s+text not null check \(category in \(([^)]*)\)\)/.exec(sql.t072); assert(m, 'no category CHECK in 072');
    assert.deepEqual([...m[1].matchAll(/'([^']+)'/g)].map(x => x[1]), core.EXPENSE_CATEGORIES);
  });
  test('C every error the SQL raises has a code + kind in stock-core, and the engine raises only codes the SQL raises', () => {
    const sqlCodes = new Set([...(sql.t065 + sql.t066 + sql.t071 + sql.t072).matchAll(/raise exception '(stock_[a-z_]+)'/g)].map(m => m[1]));
    assert(sqlCodes.size >= 20, 'found only ' + sqlCodes.size + ' codes in the SQL');
    assert.deepEqual([...sqlCodes].sort(), Object.keys(core.CODE_KIND).sort(), 'CODE_KIND must list exactly the codes the SQL raises');
    const engSrc = fs.readFileSync(path.join(__dirname, 'stock_engine.js'), 'utf8');
    const engCodes = new Set([...engSrc.matchAll(/raise\('(stock_[a-z_]+)'/g)].map(m => m[1]));
    for (const c of engCodes) assert(sqlCodes.has(c), 'engine raises ' + c + ' which the SQL does not');
    const notInEngine = [...sqlCodes].filter(c => !engCodes.has(c));
    assert.deepEqual(notInEngine, [], 'every error the SQL raises is implemented by the engine (the category cap now too, step 4)');
  });
  test('C RPC argument names and required arguments in the engine == the SQL function signatures; stock-core calls only those', () => {
    const sigs = {};
    for (const m of (sql.t066 + sql.t069 + sql.t070 + sql.t072).matchAll(/create or replace function public\.(stock_[a-z_]+)\(([^)]*)\)\s*returns/g)) {
      sigs[m[1]] = m[2].split(',').map(s => s.trim()).filter(Boolean).map(s => ({ name: s.split(/\s+/)[0], required: !/\bdefault\b/i.test(s) }));
    }
    const publicNames = Object.keys(Engine.SIGNATURES);
    assert.equal(publicNames.length, 21);
    for (const n of publicNames) {
      assert(sigs[n], 'SQL has no function ' + n);
      assert.deepEqual(Engine.SIGNATURES[n], sigs[n].map(a => a.name), 'argument names of ' + n);
      assert.deepEqual((Engine.REQUIRED[n] || []).slice().sort(), sigs[n].filter(a => a.required).map(a => a.name).sort(), 'required arguments of ' + n);
    }
    // stock-core's api sends only declared names (the engine rejects anything else with PGRST202; here every method is exercised against it)
    const seen = [];
    const spy = { rpc: async (name, args) => { seen.push([name, Object.keys(args)]); return { data: null, error: { message: 'spy' } }; } };
    const api = core.createApi(spy, { today: () => '2026-10-27' });
    return Promise.all([api.boot(), api.overview(30), api.lanes(), api.itemsPage({}, 10, null), api.addItems({ title: 'x' }, 1), api.importRows('i', []), api.undoImport('i'), api.setStatus('1', 'listed', { platform: 'vinted', listCents: 1, on: '2026-01-01' }),
      api.markSold('1', { soldCents: 1, on: '2026-01-01', platform: 'vinted', feeCents: 1, shipPaidCents: 1 }), api.markReturned('1', { on: '2026-01-01', refundCents: 1, refundFee: true, returnShipCents: 1, to: 'stock', reason: null }),
      api.writeOff('1', 'lost', '2026-01-01'), api.editItem('1', {}), api.deleteItem('1'), api.restoreItem('1'), api.undo(), api.overviewSeries(30), api.counts(), api.addExpenses([]), api.deleteExpenses(['1']), api.expensesMonth('2026-10-01'), api.pnl(12)].map(p => p.catch(() => null))).then(() => {
      assert.equal(seen.length, 21);
      for (const [name, keys] of seen) {
        assert(sigs[name], 'api calls unknown function ' + name);
        for (const k of keys) assert(sigs[name].some(a => a.name === k), `${name} sent undeclared argument ${k}`);
        for (const a of sigs[name].filter(x => x.required)) assert(keys.includes(a.name), `${name} did not send required argument ${a.name}`);
      }
    });
  });
  test('C the claims mirror (067) truncation lengths match the engine port: title 140, brand 60, size 20 (no brand/size > those in the table CHECKs)', () => {
    assert(/left\(coalesce\(nullif\(btrim\(new\.title\), ''\), 'Claimed listing'\), 140\)/.test(sql.t067));
    assert(/left\(nullif\(btrim\(new\.brand_title\), ''\), 60\)/.test(sql.t067));
    assert(/left\(nullif\(btrim\(new\.size_title\), ''\), 20\)/.test(sql.t067));
  });
} else {
  console.log(`SKIPPED section C: backend repo not found at ${BACKEND} (set SNYPD_BACKEND). The enums, caps, error codes and argument names were NOT diffed against the migrations.`);
}

// =========================================================================================== M: money
test('M the design\'s 8 hero test strings (plan section 6), with spaces normalised', () => {
  const norm = s => s.replace(/\s/g, ' ');
  const E = String.fromCharCode(0x20ac), M = core.MINUS;
  assert.equal(norm(core.formatMoney(61240, 'EUR', 'en')), E + '612.40');
  assert.equal(norm(core.formatMoney(-1800, 'EUR', 'en')), M + E + '18.00');
  assert.equal(norm(core.formatMoney(112450, 'EUR', 'en')), E + '1,124.50');
  assert.equal(norm(core.formatMoney(112450, 'EUR', 'fr')), '1 124,50 ' + E);
  assert.equal(norm(core.formatMoney(290770, 'EUR', 'fr')), '2 907,70 ' + E);
  assert.equal(norm(core.formatMoney(1234560, 'EUR', 'fr')), '12 345,60 ' + E);
  assert.equal(norm(core.formatMoney(8740, 'EUR', 'en', { signed: true })), '+' + E + '87.40');
  assert.equal(norm(core.formatMoney(-107140, 'EUR', 'fr')), M + '1 071,40 ' + E);
});
test('M every launch currency formats like Intl narrowSymbol in en-GB / fr-FR, minus is U+2212, missing is "--"', () => {
  for (const cur of core.CURRENCIES) for (const [lang, loc] of [['en', 'en-GB'], ['fr', 'fr-FR']]) {
    const ref = new Intl.NumberFormat(loc, { style: 'currency', currency: cur, currencyDisplay: 'narrowSymbol' });
    assert.equal(core.formatMoney(112450, cur, lang), ref.format(1124.5), `${cur} ${lang}`);
    assert.equal(core.formatMoney(-112450, cur, lang), core.MINUS + ref.format(1124.5), `${cur} ${lang} negative`);
    assert(!/-/.test(core.formatMoney(-5, cur, lang)), 'ASCII hyphen in a negative amount');
  }
  assert.equal(core.formatMoney(null, 'EUR', 'en'), '--');
  assert.equal(core.formatMoney(undefined, 'EUR', 'fr'), '--');
  assert.equal(core.formatMoney(NaN, 'EUR', 'en'), '--');
  assert.equal(core.formatMoney(0, 'EUR', 'en'), String.fromCharCode(0x20ac) + '0.00');
  assert.equal(core.moneyLabel(112450, 'EUR', 'fr'), '1 124,50 ' + String.fromCharCode(0x20ac), 'label uses plain spaces only');
});
test('M parseMoneyInput: separators, grouping, currency words, refusals', () => {
  const p = (t, l) => core.parseMoneyInput(t, l);
  const ok = (t, l, c) => { const r = p(t, l); assert(r.ok, `"${t}" ${l} should parse, got ${JSON.stringify(r)}`); assert.equal(r.cents, c, `"${t}" ${l}`); };
  const bad = (t, l, why) => { const r = p(t, l); assert(!r.ok, `"${t}" ${l} should be refused`); assert.equal(r.reason, why, `"${t}" ${l}`); };
  ok('12.50', 'en', 1250); ok('12,50', 'fr', 1250); ok('12,5', 'fr', 1250); ok('12', 'en', 1200); ok('0', 'en', 0); ok('0,05', 'fr', 5); ok('.5', 'en', 50); ok('12.', 'en', 1200);
  ok('1,234.56', 'en', 123456); ok('1.234,56', 'fr', 123456); ok('1,234,567.89', 'en', 123456789); ok('1 124,50', 'fr', 112450);
  ok('1,234', 'en', 123400); ok('1.234', 'fr', 123400); ok('1.234.567', 'en', 123456700); ok('1.234.567', 'fr', 123456700); ok('EUR 12', 'en', 1200); ok('12 EUR', 'en', 1200); ok('1 124,50 ' + String.fromCharCode(0x20ac), 'fr', 112450);
  bad('1.234', 'en', 'too_many_decimals'); bad('1,234', 'fr', 'too_many_decimals'); bad('12abc34', 'en', 'not_a_number'); bad('abc', 'en', 'not_a_number'); bad('-5', 'en', 'negative');
  bad(core.MINUS + '5', 'en', 'negative'); bad('1.2.3', 'en', 'bad_grouping'); bad('12,34.56', 'en', 'bad_grouping'); bad('99999999999', 'en', 'too_large'); bad('..', 'en', 'bad_grouping');
  assert.deepEqual(p('', 'en'), { ok: true, cents: null, empty: true });
  assert.deepEqual(p('   ', 'fr'), { ok: true, cents: null, empty: true });
});
test('M parse(format(x)) == x for 4,000 amounts, EUR and GBP and SEK, en and fr (what the user sees can be typed back)', () => {
  let s = 12345;
  const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 4000; i++) {
    const cents = Math.floor(rnd() * Math.pow(10, 1 + Math.floor(rnd() * 7)));
    for (const cur of ['EUR', 'GBP', 'SEK']) for (const lang of ['en', 'fr']) {
      const r = core.parseMoneyInput(core.formatMoney(cents, cur, lang), lang);
      assert(r.ok && r.cents === cents, `${cur} ${lang} ${cents} -> "${core.formatMoney(cents, cur, lang)}" -> ${JSON.stringify(r)}`);
    }
  }
});

// =========================================================================================== E: errors
test('E parseError maps every SQL code to its kind, and the other failure shapes', () => {
  for (const [code, kind] of Object.entries(core.CODE_KIND)) {
    const e = core.parseError({ message: code, code: 'P0001', details: 'x' });
    assert.equal(e.code, code); assert.equal(e.kind, kind); assert(e instanceof core.StockError); assert(!e.retryable);
  }
  assert.equal(core.parseError({ message: 'stock_free_limit', details: 'The Free plan holds 25 items.' }).detail, 'The Free plan holds 25 items.');
  const c = core.parseError({ message: 'new row for relation "stock_items" violates check constraint "stock_items_sold_needs_date"', code: '23514' });
  assert.equal(c.code, 'stock_check_violation'); assert.equal(c.constraint, 'stock_items_sold_needs_date'); assert.equal(c.kind, 'validation');
  assert.equal(core.parseError({ message: 'Could not find the function public.stock_x in the schema cache', code: 'PGRST202' }).code, 'stock_not_deployed');
  assert.equal(core.parseError({ message: 'permission denied for table stock_items', code: '42501' }).kind, 'forbidden');
  assert.equal(core.parseError({ message: 'JWT expired' }).kind, 'auth');
  const n = core.parseError(new TypeError('Failed to fetch')); assert.equal(n.kind, 'network'); assert(n.retryable);
  assert.equal(core.parseError('something odd').code, 'stock_unknown');
  const again = core.parseError(c); assert.equal(again, c, 'a StockError passes through unchanged');
});

// =========================================================================================== H: helpers
test('H item helpers: age restarts at a return, old = 45+ days, cost null without a buy price, profit only for sold rows', () => {
  const base = { status: 'stock', bought_on: '2026-09-01', returned_on: null, buy_cents: 1000, extra_cents: 250, deleted_at: null };
  assert.equal(core.ageDays(base, '2026-10-27'), 56); assert(core.isOld(base, '2026-10-27')); assert(!core.isOld(base, '2026-10-14'), '43 days is not old'); assert(!core.isOld(base, '2026-10-15'), '44 days is not old yet'); // 2026-09-01 + 45 days = 2026-10-16
  assert(core.isOld(base, '2026-10-16'));
  const ret = Object.assign({}, base, { status: 'returned', returned_on: '2026-10-20' });
  assert.equal(core.ageDays(ret, '2026-10-27'), 7); assert(!core.isOld(ret, '2026-10-27'));
  assert.equal(core.costCents(base), 1250); assert.equal(core.costCents({ buy_cents: null, extra_cents: 100 }), null);
  const sold = { status: 'sold', buy_cents: 3000, extra_cents: 0, sold_cents: 5000, fee_cents: null, ship_paid_cents: 120 };
  assert.equal(core.saleProfitCents(sold), 1880); assert.equal(core.saleProfitCents(Object.assign({}, sold, { buy_cents: null })), null); assert.equal(core.saleProfitCents(base), null);
  assert(!core.isHeld(Object.assign({}, base, { deleted_at: '2026-10-01T00:00:00Z' })));
  assert.equal(core.daysBetween('2026-03-01', '2026-02-01'), 28); assert.equal(core.daysBetween('2026-10-27', '2026-10-24'), 3);
  assert.equal(core.localToday(new Date(2026, 9, 5, 23, 59).getTime()), '2026-10-05');
});
test('H freeCapState: meter amber from 20, at cap from 25, unlimited when paid', () => {
  const b = (held, cap) => ({ plan: { paid: cap == null, free_cap: cap }, counts: { held } });
  assert.deepEqual(core.freeCapState(b(19, 25)), { limited: true, held: 19, cap: 25, left: 6, atCap: false, warn: false });
  assert.equal(core.freeCapState(b(20, 25)).warn, true); assert.equal(core.freeCapState(b(25, 25)).atCap, true); assert.equal(core.freeCapState(b(30, 25)).left, 0);
  assert.deepEqual(core.freeCapState(b(300, null)), { limited: false, held: 300, cap: null, left: null, atCap: false, warn: false });
});

// =========================================================================================== A: acceptance
test('A the design dataset through createApi -> engine reproduces the oracle: 5 periods (current + previous), held, lanes, months', async () => {
  const { eng, api } = account({ uid: 'A', today: '2026-10-27' });
  assert.deepEqual(eng.loadFixture(fx), { items: 218, history: 580 });
  for (const k of ['7', '30', '90', '365', 'all']) {
    const ov = await api.overview(k === 'all' ? null : +k, '2026-10-27');
    assert.deepEqual(ov.current, oracle.periods[k].cur, `${k} current`);
    if (k !== 'all') assert.deepEqual(ov.previous, oracle.periods[k].prev, `${k} previous`);
    else assert.equal(ov.previous, null);
    const h = oracle.held;
    assert.deepEqual({ count: ov.held.count, in_stock: ov.held.in_stock, listed: ov.held.listed, reserved: ov.held.reserved, returned: ov.held.returned, cash: ov.held.cash_cents, old: ov.held.old, old_cost: ov.held.old_cost_cents },
      { count: h.count, in_stock: h.in_stock, listed: h.listed, reserved: h.reserved, returned: h.returned, cash: h.cash, old: h.old, old_cost: h.old_cost });
  }
  assert.deepEqual(eng.agg('2026-08-01', '2026-09-01'), oracle.months['2026-08']);
  assert.deepEqual(eng.agg('2026-09-01', '2026-10-01'), oracle.months['2026-09']);
  const lanes = await api.lanes('2026-10-27');
  assert.deepEqual({ reprice: lanes.reprice.count, list: lanes.list.count, follow: lanes.follow.count, hold: lanes.hold.count }, oracle.lanes);
  assert(lanes.list.items.length === 5 && lanes.list.items[0].days >= lanes.list.items[4].days, 'top 5, oldest first');
});
test('A the plan\'s literal acceptance numbers, formatted like the screen will show them', async () => {
  // load through a fresh engine so this test stands alone
  const a = account({ uid: 'A' }); a.eng.loadFixture(fx);
  const v30 = core.viewOverview(await a.api.overview(30, '2026-10-27'));
  const E = String.fromCharCode(0x20ac);
  assert.equal(v30.held.count, 58); assert.deepEqual([v30.held.inStock, v30.held.listed, v30.held.reserved], [18, 36, 4]);
  assert.equal(money(v30.held.cashCents), E + '1,124.50'); assert.equal(v30.held.old, 12); assert.equal(money(v30.held.oldCostCents), E + '318.00');
  assert.equal(v30.sold, 31); assert.equal(money(v30.revenueCents), E + '1,846.00'); assert.equal(money(v30.netCents), E + '612.40');
  assert.equal(v30.partialLabel, '29 of 31'); assert(v30.partial); assert.equal(money(v30.avgProfitCents), E + '21.12'); assert.equal(v30.daysToSell, 18);
  assert.equal(money(v30.prevNetCents), E + '549.60'); assert.equal(money(v30.deltaNetCents), E + '62.80');
  const v7 = core.viewOverview(await a.api.overview(7, '2026-10-27')); assert.equal(money(v7.netCents), E + '152.00'); assert.equal(money(v7.prevNetCents), E + '164.20');
  const v90 = core.viewOverview(await a.api.overview(90, '2026-10-27')); assert.equal(money(v90.netCents), E + '1,545.60'); assert.equal(v90.sold, 83); assert.equal(v90.withCost, 81);
  const all = core.viewOverview(await a.api.overview(null, '2026-10-27')); assert.equal(money(all.netCents, 'fr').replace(/\s/g, ' '), '2 907,70 ' + E); assert.equal(all.sold, 153); assert.equal(all.withCost, 151); assert.equal(all.prevNetCents, null);
  const aug = a.eng.agg('2026-08-01', '2026-09-01'), sep = a.eng.agg('2026-09-01', '2026-10-01');
  assert.equal(money(aug.net), E + '471.20'); assert.equal(money(sep.net), E + '504.10');
  const items = a.eng.state.items;
  assert.equal(items.filter(i => i.returned_on && i.deleted_at == null).length, 3);
  const wo = items.filter(i => i.status === 'written_off'); assert.equal(wo.length, 4); assert.equal(money(wo.reduce((x, i) => x + i.buy_cents + i.extra_cents, 0)), E + '74.50');
  assert.equal(v30.held.count + 0, 58); assert.equal(items.filter(i => i.deleted_at != null).length, 3, 'deleted copies are in the table but in no total');
});
test('A migration 069 in the engine: lane rows carry platform, list price, cost, drops, brand; the charts add up to the Overview number for every period, and the design chart numbers match', async () => {
  const a = account({ uid: 'A' }); a.eng.loadFixture(fx);
  const lanes = await a.api.lanes('2026-10-27');
  assert.deepEqual(Object.keys(lanes.reprice.items[0]).sort(), ['brand', 'cost_cents', 'days', 'drops', 'id', 'image_url', 'lane_days', 'list_cents', 'platform', 'title']);   // image_url: migration 071
  const top = lanes.reprice.items[0]; assert.deepEqual([top.title, top.platform, top.list_cents, top.cost_cents, top.drops, top.lane_days, top.days], ['Carhartt WIP Detroit jacket, black, XL', 'depop', 8500, 4000, 0, 90, 94]);
  assert.deepEqual([lanes.reprice.count, lanes.list.count, lanes.follow.count, lanes.hold.count], [9, 17, 3, 9]);
  for (const k of ['reprice', 'list', 'follow', 'hold']) for (const x of lanes[k].items) { const it = a.eng.state.items.find(i => i.id === x.id); assert.deepEqual([x.platform, x.list_cents, x.drops, x.brand, x.cost_cents], [it.platform == null ? null : it.platform, it.list_cents == null ? null : it.list_cents, it.drops, it.brand == null ? null : it.brand, it.buy_cents == null ? null : it.buy_cents + it.extra_cents]); }
  for (const d of [7, 30, 90, 365, null]) {
    const ov = await a.api.overview(d, '2026-10-27'), s = await a.api.overviewSeries(d, '2026-10-27'), sm = (arr, k) => arr.reduce((n, x) => n + x[k], 0);
    assert.equal(sm(s.by_platform, 'net'), ov.current.net, 'platform bars add up to the net, period ' + d); assert.equal(sm(s.by_platform, 'sold'), ov.current.sold);
    if (d != null) { assert.equal(s.daily.length, d); assert.equal(sm(s.daily, 'net'), ov.current.net, 'daily bars add up to the net, period ' + d); assert.equal(sm(s.daily, 'sold'), ov.current.sold); } else assert.equal(s.daily.length, 0);
  }
  const s30 = await a.api.overviewSeries(30, '2026-10-27');
  assert.deepEqual(s30.by_platform, [{ platform: 'vinted', net: 29290, sold: 16 }, { platform: 'facebook', net: 11670, sold: 6 }, { platform: 'marktplaats', net: 10380, sold: 3 }, { platform: 'vestiaire', net: 4600, sold: 2 }, { platform: 'ebay', net: 3450, sold: 3 }, { platform: 'depop', net: 1850, sold: 1 }]);
  assert.deepEqual([s30.daily[0].d, s30.daily[29].d, Math.min(...s30.daily.map(x => x.net))], ['2026-09-28', '2026-10-27', -1800]);
  await rejects(a.api.overviewSeries(45), 'stock_bad_period', 'bad period');
});
test('L hand-worked charts (== SQL test C4): a sale that is returned, a sale, a write-off, a sale with fee + shipping, then undo', async () => {
  const { api } = account({ uid: 'Q' });
  const add = async (title, buy, extra) => (await api.addItems({ title, buy_cents: buy, extra_cents: extra || 0, bought_on: '2026-10-01' }, 1)).ids[0];
  const g1 = await add('G1', 1000), g2 = await add('G2', 500), g3 = await add('G3', 500), g4 = await add('G4', 2000, 100);
  await api.markSold(g1, { soldCents: 2500, on: '2026-10-20', platform: 'ebay' }); await api.markReturned(g1, { on: '2026-10-22', returnShipCents: 0, to: 'stock' });
  await api.markSold(g2, { soldCents: 1200, on: '2026-10-20', platform: 'vinted' }); await api.writeOff(g3, 'lost', '2026-10-22');
  await api.markSold(g4, { soldCents: 3000, on: '2026-10-25', platform: 'depop', feeCents: 200, shipPaidCents: 100 });
  const ov = await api.overview(30, '2026-10-27'), s = await api.overviewSeries(30, '2026-10-27');
  assert.deepEqual([ov.current.net, ov.current.sold], [800, 2]);
  assert.deepEqual(s.by_platform, [{ platform: 'vinted', net: 700, sold: 1 }, { platform: 'depop', net: 600, sold: 1 }, { platform: 'ebay', net: 0, sold: 0 }, { platform: '', net: -500, sold: 0 }]);
  assert.deepEqual(s.daily.filter(x => x.net !== 0 || x.sold !== 0), [{ d: '2026-10-20', net: 2200, sold: 2 }, { d: '2026-10-22', net: -2000, sold: -1 }, { d: '2026-10-25', net: 600, sold: 1 }]);
  const s7 = await api.overviewSeries(7, '2026-10-27');
  assert.deepEqual(s7.by_platform, [{ platform: 'depop', net: 600, sold: 1 }, { platform: '', net: -500, sold: 0 }, { platform: 'ebay', net: -1500, sold: -1 }]);
  await api.undo();
  const su = await api.overviewSeries(30, '2026-10-27'); assert.equal(su.by_platform.reduce((n, x) => n + x.net, 0), 200); assert(!su.by_platform.some(x => x.platform === 'depop'));
});
test('A migration 070 in the engine: the chip counts equal the list totals and the design numbers (== SQL test D2)', async () => {
  const a = account({ uid: 'A' }); a.eng.loadFixture(fx);
  const c = await a.api.counts('2026-10-27'), tot = async f => (await a.api.itemsPage(Object.assign({ today: '2026-10-27' }, f), 1, null)).total;
  assert.deepEqual([c.in_stock, c.listed, c.reserved, c.sold, c.old, c.held], [18, 36, 4, 153, 12, 58]);
  assert.deepEqual([c.all, c.in_stock, c.listed, c.reserved, c.sold, c.returned, c.written_off, c.old],
    [await tot({}), await tot({ status: ['stock', 'returned'] }), await tot({ status: ['listed'] }), await tot({ status: ['reserved'] }), await tot({ status: ['sold'] }), await tot({ status: ['returned'] }), await tot({ status: ['written_off'] }), await tot({ old: true })]);
  assert.equal(c.in_stock + c.listed + c.reserved + c.sold + c.written_off, c.all, 'the statuses partition the items');
});
test('A empty account: boot, overview and view are quiet (no events, "--" numbers)', async () => {
  const { api } = account({ uid: 'N' });
  const boot = await api.boot(); assert.equal(boot.mode, 'all'); assert.equal(boot.counts.items, 0); assert.equal(boot.categories.length, 9);
  const v = core.viewOverview(await api.overview(30)); assert(v.empty); assert(!v.hasEvents); assert.equal(v.netCents, null); assert.equal(v.avgProfitCents, null); assert.equal(core.formatMoney(v.netCents, 'EUR', 'en'), '--');
});

// =========================================================================================== L: lifecycle (== SQL tests B7 / B7b)
test('L hand-worked lifecycle: add, undo, list, reprice, sell, undo, return, relist, re-sell, edit, write-off, return-to-write-off, delete/restore/purge', async () => {
  const { eng, api } = account({ uid: 'L', paid: true });
  const hist = id => eng.state.history.filter(h => h.item_id === id);
  const i1 = (await api.addItems({ title: 'Barbour Bedale', brand: 'Barbour', buy_cents: 3000, extra_cents: 0, category: 'outerwear', condition: 'very_good', src: 'hunt x', src_type: 'hunt', bought_on: '2026-10-01' }, 1)).ids[0];
  const add3 = await api.addItems({ title: 'Pack of 3', buy_cents: 500, bought_on: '2026-10-02' }, 3);
  assert.equal(add3.items_created, 3);
  const undo3 = await api.undo(); assert.equal(undo3.items, 3);
  assert.equal(eng.state.items.filter(i => i.title === 'Pack of 3').length, 0); assert.equal(add3.ids.map(id => hist(id).length).reduce((a, b) => a + b, 0), 0);
  await rejects(api.undo(), 'stock_nothing_to_undo', 'second undo');
  const listed = await api.setStatus(i1, 'listed', { platform: 'vinted', listCents: 5000, on: '2026-10-05' });
  const repr = await api.setStatus(i1, 'listed', { listCents: 4500 });
  await rejects(api.setStatus(i1, 'listed', { listCents: 4600 }), 'stock_reprice_must_lower', 'higher reprice');
  assert.deepEqual([listed.status, repr.list_cents, repr.drops, hist(i1).filter(h => h.kind === 'listed').length, hist(i1).length], ['listed', 4500, 1, 1, 2]);
  const sold1 = await api.markSold(i1, { soldCents: 5000, on: '2026-10-12', platform: 'vinted' });
  assert.deepEqual([sold1.profit_cents, sold1.days], [2000, 11]);
  let ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.sold, ov.current.rev, ov.current.net], [1, 5000, 2000]);
  await api.undo(); ov = await api.overview(30, '2026-10-27');
  const row = eng.state.items.find(i => i.id === i1);
  assert.deepEqual([row.status, row.list_cents, row.sold_cents, hist(i1).filter(h => h.kind === 'sale').length, ov.current.any], ['listed', 4500, null, 0, false]);
  await api.markSold(i1, { soldCents: 5000, on: '2026-10-12', platform: 'vinted' });
  const ret1 = await api.markReturned(i1, { on: '2026-10-14', returnShipCents: 450 });
  assert.deepEqual([ret1.status, ret1.refund_cents, ret1.reversal_cents, ret1.sold_cents, ret1.returned_on], ['returned', 5000, -2450, null, '2026-10-14']);
  ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.sales, ov.current.returns, ov.current.sold, ov.current.rev, ov.current.with_cost, ov.current.net], [1, 1, 0, 0, 0, -450]);
  await api.setStatus(i1, 'listed', { platform: 'vinted', listCents: 4800, on: '2026-10-16' });
  assert.equal(hist(i1).map(h => h.kind).join(','), 'bought,listed,sale,return,relisted');
  const sold2 = await api.markSold(i1, { soldCents: 4000, on: '2026-10-20', platform: 'vinted' });
  assert.deepEqual([sold2.days, sold2.profit_cents], [6, 1000]);
  assert.equal(hist(i1).map(h => h.kind).join(','), 'bought,listed,sale,return,relisted,sale');
  ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.sales, ov.current.returns, ov.current.sold, ov.current.rev, ov.current.net, ov.current.days], [2, 1, 1, 4000, 550, 9], '2 sales (snapshot + row), not 3');
  // B7b
  const ed1 = await api.editItem(i1, { buy_cents: 2500, brand: '' });
  ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.net, ed1.brand, hist(i1).length], [1050, null, 6]);
  await rejects(api.editItem(i1, { status: 'stock' }), 'stock_field_not_editable', 'status');
  await rejects(api.editItem(i1, { user_id: 'x' }), 'stock_field_not_editable', 'user_id');
  const eCond = await rejects(api.editItem(i1, { condition: 'mint' }), 'stock_check_violation', 'condition'); assert.equal(eCond.constraint, 'stock_items_condition_check');
  await rejects(api.setStatus(i1, 'listed', { listCents: 100 }), 'stock_transition_not_allowed', 'sold -> listed');
  const i4 = (await api.addItems({ title: 'Plain item', buy_cents: 1000, bought_on: '2026-10-03' }, 1)).ids[0];
  await rejects(api.editItem(i4, { sold_cents: 900 }), 'stock_field_not_editable', 'sale field on unsold');
  await rejects(api.markReturned(i4), 'stock_transition_not_allowed', 'return of unsold');
  const i2 = (await api.addItems({ title: 'Bag', buy_cents: 2500, bought_on: '2026-10-02' }, 1)).ids[0];
  await api.setStatus(i2, 'listed', { platform: 'vinted', listCents: 4000, on: '2026-10-05' });
  await api.setStatus(i2, 'reserved', { on: '2026-10-06' });
  await api.setStatus(i2, 'listed'); await api.undo();
  assert.equal(eng.state.items.find(i => i.id === i2).status, 'reserved', 'undo takes back only the last action');
  await api.writeOff(i2, 'damaged', '2026-10-10');
  await rejects(api.markReturned(i2), 'stock_written_off', 'return of a written-off item');
  await api.undo();
  assert.deepEqual([eng.state.items.find(i => i.id === i2).status, hist(i2).filter(h => h.kind === 'write_off').length], ['reserved', 0]);
  await api.writeOff(i2, 'damaged', '2026-10-10');
  const i3 = (await api.addItems({ title: 'Coat', buy_cents: 3000, bought_on: '2026-10-01' }, 1)).ids[0];
  await api.markSold(i3, { soldCents: 5000, on: '2026-10-12', platform: 'vinted' });
  const r3 = await api.markReturned(i3, { on: '2026-10-15', to: 'written_off', reason: 'lost' });
  assert.deepEqual([r3.status, r3.written_off_on, hist(i3).map(h => h.kind).join(',')], ['written_off', '2026-10-15', 'bought,sale,return,write_off']);
  ov = await api.overview(30, '2026-10-27');
  const c = ov.current;
  assert.equal([c.sales, c.returns, c.wos, c.sold, c.with_cost, c.sales_rev, c.refunds, c.rev, c.sales_profit, c.ret_profit, c.wo_cost, c.net, c.day_sum, c.days].join('/'), '3/2/2/1/1/14000/10000/4000/5500/-4450/5500/-4450/28/9');
  await api.deleteItem(i2); ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.wos, ov.current.wo_cost, ov.current.net], [1, 3000, -1950]);
  await api.restoreItem(i2); ov = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov.current.wos, ov.current.net], [2, -4450]);
  eng.state.items.find(i => i.id === i4).deleted_at = new Date(clock.t - 31 * 86400000).toISOString();
  await api.addItems({ title: 'purges the old deleted one' }, 1);
  assert.deepEqual([eng.state.items.filter(i => i.id === i4).length, hist(i4).length], [0, 0], 'deleted 31 days ago: purged with its history');
  clock.t += 20000;
  await rejects(api.undo(), 'stock_undo_expired', 'undo after 20 s');
  clock.t -= 20000;
  // B7c: aging restarts at a return. Bought 2026-08-01 (87 days before the 27th), sold, returned 2026-10-20: age 7, NOT old, but in the 'list' lane (7 days)
  const i5 = (await api.addItems({ title: 'Old coat', buy_cents: 2000, bought_on: '2026-08-01' }, 1)).ids[0];
  await api.markSold(i5, { soldCents: 3000, on: '2026-08-10', platform: 'vinted' }); await api.markReturned(i5, { on: '2026-10-20' });
  let ov5 = await api.overview(30, '2026-10-27'); let ln5 = await api.lanes('2026-10-27');
  assert.deepEqual([ov5.held.old, ln5.list.items.some(x => x.id === i5), core.ageDays(eng.state.items.find(i => i.id === i5), '2026-10-27')], [0, true, 7], 'age counts from the return, not the purchase');
  eng.setSettings({ old_after_days: 7 }); ov5 = await api.overview(30, '2026-10-27');
  assert.deepEqual([ov5.old_after_days, ov5.held.old], [7, 1], 'the Old-after setting is the threshold: 7 days >= 7');
});

// =========================================================================================== F: caps, claims, import, switch, contract, page
test('F Free = 25 HELD items: 26th refused, import reports the rest, selling frees a slot, restore at the cap refused, claim mirror bypasses, Hunt Pass unlimited', async () => {
  const { eng, api } = account({ uid: 'F', paid: false });
  assert.equal((await api.addItems({ title: 'cap item', buy_cents: 1000 }, 25)).items_created, 25);
  const e26 = await rejects(api.addItems({ title: '26th' }, 1), 'stock_free_limit', '26th'); assert.equal(e26.kind, 'limit');
  const boot = await api.boot(); assert.deepEqual([boot.plan.paid, boot.plan.free_cap, boot.counts.held], [false, 25, 25]);
  assert.deepEqual(core.freeCapState(boot), { limited: true, held: 25, cap: 25, left: 0, atCap: true, warn: true });
  const imp = await api.importRows('11111111-1111-4111-8111-111111111111', [{ title: 'held a' }, { title: 'sold ok', status: 'sold', sold_on: '2026-10-20', sold_cents: 2500, bought_on: '2026-10-01' }, { title: 'held b' }]);
  assert.deepEqual([imp.rows_inserted, imp.skipped.length, imp.free_limit_hit, imp.skipped[0].reason], [1, 2, true, 'stock_free_limit']);
  const first = eng.state.items.find(i => i.status === 'stock');
  await api.markSold(first.id, { soldCents: 2000, on: '2026-10-27', platform: 'vinted' });
  assert.equal((await api.addItems({ title: 'after a sale' }, 1)).items_created, 1);
  await rejects(api.addItems({ title: 'again' }, 1), 'stock_free_limit', 'back at 25');
  const second = eng.state.items.find(i => i.status === 'stock');
  await api.deleteItem(second.id); await api.addItems({ title: 'refill to the cap' }, 1);
  await rejects(api.restoreItem(second.id), 'stock_free_limit', 'restore at the cap');
  eng.mirrorClaim({ id: 'claim-1', title: 'Claim at cap', brand_title: 'Nike', size_title: 'M', bought_price_cents: 900, status: 'holding', claimed_at: '2026-10-26T10:00:00Z' });
  assert.equal((await api.boot()).counts.held, 26, 'a Feed claim at the cap is still mirrored');
  const paid = account({ uid: 'H', paid: true }); assert.equal((await paid.api.addItems({ title: 'pass item' }, 26)).items_created, 26);
  assert.equal(eng.state.items.find(i => i.id === first.id).status, 'sold', 'selling at the cap worked');
});
test('F 5,000-item cap: a 20-row import into 4,990 rows lets 10 in and reports 10; the next quick add is refused', async () => {
  const { eng, api } = account({ uid: 'P', paid: true });
  for (let i = 0; i < 4990; i++) eng.state.items.push({ id: 'bulk-' + i, user_id: 'P', title: 'bulk ' + i, status: 'stock', bought_on: '2026-10-01', extra_cents: 0, deleted_at: null, drops: 0 });
  const rows = Array.from({ length: 20 }, (_, i) => ({ title: 'imp ' + i }));
  const r = await api.importRows('22222222-2222-4222-8222-222222222222', rows);
  assert.deepEqual([r.rows_inserted, r.skipped.length, r.item_cap_hit], [10, 10, true]);
  await rejects(api.addItems({ title: 'over' }, 1), 'stock_item_cap', 'at 5,000');
  assert.equal(eng.state.items.length, 5000);
  await rejects(api.importRows('33333333-3333-4333-8333-333333333333', Array.from({ length: 501 }, (_, i) => ({ title: 'x' + i }))), 'stock_batch_too_large', '501 rows');
});
test('F import: 3 rows = 5 items (quantity 3), 2 rows reported by index with the reason, history counts, undo this import removes only its own items', async () => {
  const { eng, api } = account({ uid: 'I', paid: true });
  const imp1 = 'aaaaaaaa-0000-4000-8000-000000000001', imp2 = 'aaaaaaaa-0000-4000-8000-000000000002';
  await api.importRows(imp2, [{ title: 'other import', buy_cents: 100 }]);
  const res = await api.importRows(imp1, [
    { title: 'Jacket', quantity: 3, buy_cents: 1000, bought_on: '2026-10-01', src: 'Car boot', category: 'outerwear' }, { title: '', buy_cents: 5 },
    { title: 'Sold tee', status: 'sold', sold_cents: 2500, sold_on: '2026-10-10', buy_cents: 1000, bought_on: '2026-10-02', platform: 'vinted' },
    { title: 'Listed shoes', status: 'listed', list_cents: 4000, platform: 'ebay', bought_on: '2026-10-03' }, { title: 'Bad condition', condition: 'mint' }]);
  assert.deepEqual([res.rows_inserted, res.items_created, res.skipped[0].index, res.skipped[0].reason, res.skipped[1].index], [3, 5, 1, 'stock_title_required', 4]);
  assert(/violates check constraint/.test(res.skipped[1].reason));
  const mine = new Set(eng.state.items.filter(i => i.import_id === imp1).map(i => i.id));
  const kinds = {}; eng.state.history.filter(h => mine.has(h.item_id)).forEach(h => { kinds[h.kind] = (kinds[h.kind] || 0) + 1; });
  assert.deepEqual(kinds, { bought: 5, listed: 1, sale: 1 });
  const sale = eng.state.history.find(h => mine.has(h.item_id) && h.kind === 'sale'); assert.deepEqual([sale.data.profit_cents, sale.data.days], [1500, 8]);
  assert.equal((await api.undoImport(imp1)).removed, 5);
  assert.deepEqual([eng.state.items.filter(i => i.import_id === imp1).length, eng.state.items.filter(i => i.import_id === imp2).length, eng.state.history.length], [0, 1, 1]);
});
test('F claims mirror (067): title/brand/size cut, null title, sold claim without price, update only while plain "stock", delete soft-deletes', async () => {
  const { eng, api } = account({ uid: 'X', paid: false });
  const long = 'T'.repeat(150), brand = 'B'.repeat(69);
  eng.mirrorClaim({ id: 'c1', title: long, brand_title: brand, size_title: 'S'.repeat(18), bought_price_cents: 1000, status: 'holding', claimed_at: '2026-10-11T10:00:00Z', vinted_url: 'https://www.vinted.fr/items/2' });
  eng.mirrorClaim({ id: 'c2', title: null, brand_title: 'Adidas', size_title: '42', bought_price_cents: 3000, status: 'holding', claimed_at: '2026-10-13T10:00:00Z' });
  eng.mirrorClaim({ id: 'c3', title: 'Barbour', status: 'sold', bought_price_cents: 4000, claimed_at: '2026-10-14T10:00:00Z', sold_at: '2026-10-18T09:00:00Z', sold_price_cents: null });
  eng.mirrorClaim({ id: 'c4', title: 'Levis', status: 'sold', bought_price_cents: 2000, claimed_at: '2026-10-12T10:00:00Z', sold_at: '2026-10-20T12:00:00Z', sold_price_cents: 3500 });
  const by = id => eng.state.items.find(i => i.claim_id === id);
  assert.deepEqual([by('c1').title.length, by('c1').brand.length, by('c1').size.length, by('c1').src], [140, 60, 18, 'SNYPD alert']);
  assert.deepEqual([by('c2').title, by('c3').status, by('c3').sold_cents, by('c4').sold_cents, by('c4').sold_on], ['Claimed listing', 'sold', null, 3500, '2026-10-20']);
  assert.equal(eng.mirrorClaim({ id: 'c1' }), null, 'never twice');
  assert.equal(eng.state.history.filter(h => h.kind === 'bought').length, 4); assert.equal(eng.state.history.filter(h => h.kind === 'sale').length, 2);
  // update: holding -> sold while still stock; a listed item is never overwritten
  eng.mirrorClaim({ id: 'c5', title: 'New claim', brand_title: 'Zara', bought_price_cents: 1200, status: 'holding', claimed_at: '2026-10-20T10:00:00Z' });
  eng.mirrorClaimUpdate({ id: 'c5', title: 'New claim', bought_price_cents: 1200, status: 'sold', sold_price_cents: 2000, sold_at: '2026-10-25T10:00:00Z' }, 1200);
  const c5 = by('c5'); assert.deepEqual([c5.status, c5.sold_cents], ['sold', 2000]);
  assert.equal(eng.state.history.find(h => h.item_id === c5.id && h.kind === 'sale').data.profit_cents, 800);
  eng.mirrorClaim({ id: 'c6', title: 'Nike hoodie', bought_price_cents: 1500, status: 'holding', claimed_at: '2026-10-10T10:00:00Z' });
  await api.setStatus(by('c6').id, 'listed', { platform: 'vinted', listCents: 2500, on: '2026-10-11' });
  eng.mirrorClaimUpdate({ id: 'c6', status: 'sold', sold_price_cents: 1800, sold_at: '2026-10-26T10:00:00Z', bought_price_cents: 1500 }, 1500);
  assert.deepEqual([by('c6').status, by('c6').sold_cents], ['listed', null], 'what the user did in Stock is not overwritten');
  eng.mirrorClaimDelete('c1'); assert(by('c1').deleted_at != null);
  eng.mirrorClaimDelete('c6'); assert.equal(by('c6').deleted_at, null, 'only a plain stock item is soft-deleted');
});
test('F kill switch: off refuses every RPC but answers boot; admin = admin accounts only; all = everyone; the mirror keeps working while off', async () => {
  const off = account({ uid: 'A', mode: 'off' });
  assert.deepEqual(await off.api.boot(), { mode: 'off' });
  for (const call of [() => off.api.overview(30), () => off.api.lanes(), () => off.api.itemsPage({}), () => off.api.addItems({ title: 'x' }), () => off.api.undo()]) { const e = await rejects(call(), 'stock_disabled', 'off'); assert.equal(e.kind, 'disabled'); }
  off.eng.mirrorClaim({ id: 'c1', title: 'quiet', status: 'holding', claimed_at: '2026-10-11T10:00:00Z' });
  assert.equal(off.eng.state.items.length, 1, 'captured quietly while off');
  off.eng.setMode('all'); assert.equal((await off.api.boot()).counts.items, 1, 'visible after the switch');
  const adm = account({ uid: 'ADM', mode: 'admin', admin: true }), norm = account({ uid: 'B', mode: 'admin', admin: false });
  assert.equal((await adm.api.boot()).mode, 'admin'); await adm.api.overview(30);
  assert.deepEqual(await norm.api.boot(), { mode: 'off' }); await rejects(norm.api.overview(30), 'stock_disabled', 'normal account in admin mode');
});
test('F PostgREST contract: an unknown or missing argument fails like the real API (PGRST202 -> stock_not_deployed), not silently', async () => {
  const { eng } = account({ uid: 'A' });
  const r1 = await eng.rpc('stock_overview', { p_days: 30, p_typo: 1 }); assert.equal(r1.error.code, 'PGRST202');
  const r2 = await eng.rpc('stock_mark_sold', { p_id: 'x' }); assert.equal(r2.error.code, 'PGRST202', 'p_sold_cents is required');
  const r3 = await eng.rpc('stock_nope', {}); assert.equal(r3.error.code, 'PGRST202');
  const r4 = await eng.rpc('stock_mark_sold', {}); const e = core.parseError(r4.error); assert.equal(e.code, 'stock_not_deployed'); assert.equal(e.kind, 'unknown');
  const bad = account({ uid: 'A' }); await rejects(bad.api.overview(30, '2099-01-01'), 'stock_date_in_future', 'future today');
  await rejects(bad.api.overview(45), 'stock_bad_period', 'period 45');
});
test('F boot: default currency from the FIRST hunt (not the later one), settings win, persona-only keeps the default', async () => {
  const { eng, api } = account({ uid: 'N', searches: [{ vinted_url: 'https://www.vinted.fr/catalog?search_text=b', created_at: '2026-10-05' }, { vinted_url: 'https://www.vinted.co.uk/catalog?search_text=a', created_at: '2026-10-01' }] });
  const b1 = await api.boot(); assert.deepEqual([b1.currency, b1.currency_source, b1.first_hunt_site, b1.categories.length], ['GBP', 'default', 'vinted.co.uk', 9]);
  assert.equal((await api.boot()).categories.length, 9);
  eng.setSettings({ persona: 'resell' }); const b2 = await api.boot(); assert.deepEqual([b2.currency, b2.currency_source, b2.persona], ['GBP', 'default', 'resell']);
  eng.setSettings({ currency: 'SEK' }); const b3 = await api.boot(); assert.deepEqual([b3.currency, b3.currency_source, b3.default_currency], ['SEK', 'settings', 'GBP']);
  for (const [url, cur] of [['vinted.fr', 'EUR'], ['vinted.se', 'SEK'], ['vinted.pl', 'PLN'], ['vinted.com', 'USD'], ['vinted.cz', 'CZK'], ['vinted.ro', 'RON'], ['vinted.hu', 'HUF'], ['vinted.xx', 'EUR']]) {
    const a = account({ uid: 'u', searches: [{ vinted_url: 'https://www.' + url + '/catalog', created_at: '2026-10-01' }] }); assert.equal((await a.api.boot()).currency, cur, url);
  }
  assert.equal((await account({ uid: 'z' }).api.boot()).currency, 'EUR', 'no hunt yet -> EUR');
});
test('F items page: walkItems yields all 215 live items once, strictly ordered; filters and escaping behave like the SQL', async () => {
  const { eng, api } = account({ uid: 'A' }); eng.loadFixture(fx);
  const ids = [], rows = []; for await (const r of api.walkItems({}, 50)) { ids.push(r.id); rows.push(r); }
  assert.equal(ids.length, 215); assert.equal(new Set(ids).size, 215); assert(rows.every(r => !('user_id' in r)));
  for (let i = 1; i < rows.length; i++) assert(rows[i - 1].bought_on > rows[i].bought_on || (rows[i - 1].bought_on === rows[i].bought_on && rows[i - 1].id > rows[i].id), 'order at ' + i);
  const total = async f => (await api.itemsPage(f, 50)).total;
  assert.equal(await total({ status: ['sold'] }), 153); assert.equal(await total({ status: ['returned'] }), 2); assert.equal(await total({ status: ['written_off'] }), 4); assert.equal(await total({ status: ['stock'] }), 16);
  assert.equal(await total({ deleted: 'only' }), 3); assert.equal(await total({ old: true, today: '2026-10-27' }), 12); assert((await total({ q: 'CARHARTT' })) > 0); assert.equal(await total({ q: '%' }), 0);
  assert.equal((await api.itemsPage({}, 5000)).rows.length, 200, 'limit clamped to 200'); assert.equal((await api.itemsPage({}, 0)).rows.length, 1, 'limit clamped to 1');
});
test('F qa_mock.js itself, run in a sandbox: Stock RPCs reach the engine, ?stock_seed / ?stock / ?plan work, claim insert/update/delete mirror, other RPCs unchanged', async () => {
  const vm = require('node:vm');
  const src = fs.readFileSync(path.join(__dirname, 'qa_mock.js'), 'utf8');
  function load(search, withEngine) {
    const win = { addEventListener() {}, fetch: async () => ({}) };
    if (withEngine !== false) win.SnypdStockEngine = Engine;
    const ctx = vm.createContext({ window: win, location: { search }, URLSearchParams, Promise, Date, Math, JSON, console: { log() {}, warn: console.warn, error: console.error }, Response, setTimeout, setInterval, clearInterval, Object, Array, String, Number, RegExp,
      fetch: async url => { assert.equal(url, 'acceptance-fixture.json'); return { json: async () => fx }; } });
    vm.runInContext(src, ctx);
    return win;
  }
  const win = load('?plan=elite&stock_seed=acceptance&stock_today=2026-10-27');
  const sb = win.supabase.createClient(), api = core.createApi(sb, { today: () => '2026-10-27' });
  const boot = await api.boot();
  assert.deepEqual([boot.mode, boot.plan.paid, boot.counts.items], ['all', true, 218], '215 dataset items + the 3 claims the mock seeds, mirrored');
  const ov = await api.overview(30, '2026-10-27');
  assert.equal(ov.held.count, 58 + 2, 'the 2 seeded holding claims are held items');
  // claim hooks: insert -> item; update to sold -> item sold; delete -> soft-deleted
  const uid = 'qa-user-0000-0000-0000-000000000001';
  await sb.from('user_claims').insert({ id: 'hook-1', user_id: uid, title: 'Hook claim', brand_title: 'Zara', bought_price_cents: 700, status: 'holding', claimed_at: '2026-10-26T10:00:00.000Z' });
  let page = await api.itemsPage({ q: 'Hook claim' }, 10); assert.equal(page.total, 1); assert.deepEqual([page.rows[0].status, page.rows[0].buy_cents, page.rows[0].src], ['stock', 700, 'SNYPD alert']);
  await sb.from('user_claims').update({ status: 'sold', sold_price_cents: 1500, sold_at: '2026-10-27T09:00:00.000Z' }).eq('id', 'hook-1');
  page = await api.itemsPage({ q: 'Hook claim' }, 10); assert.deepEqual([page.rows[0].status, page.rows[0].sold_cents], ['sold', 1500]);
  await sb.from('user_claims').insert({ id: 'hook-2', user_id: uid, title: 'Delete me', status: 'holding', claimed_at: '2026-10-26T10:00:00.000Z' });
  await sb.from('user_claims').delete().eq('id', 'hook-2');
  assert.equal((await api.itemsPage({ q: 'Delete me' }, 10)).total, 0, 'a deleted claim leaves Stock (soft-deleted)');
  assert.equal((await api.itemsPage({ q: 'Delete me', deleted: 'only' }, 10)).total, 1);
  const hist = await api.itemHistory(page.rows[0].id);
  assert.deepEqual(hist.map(h => h.kind), ['bought', 'sale'], 'itemHistory reads stock_history through the mock builder, oldest first');
  // other RPCs keep the old "not implemented" answer; a bad Stock call fails like the SQL does
  assert.match((await sb.rpc('dashboard_boot')).error.message, /not implemented/);
  await rejects(api.markSold('missing-id', { soldCents: 1 }), 'stock_item_not_found', 'unknown item');
  // step 5: settings are one own-row upsert (065 policies), an item can be read by id, and a currency change never converts a stored amount
  const cashBefore = (await api.overview(30, '2026-10-27')).held.cash_cents;
  assert.deepEqual(await api.saveSettings({ currency: 'GBP', persona: 'resell', old_after_days: 60, tab_hidden: true, junk: 1 }), { currency: 'GBP', persona: 'resell', old_after_days: 60, tab_hidden: true, user_id: uid }, 'only the four settings are written');
  const bset = await api.boot(); assert.deepEqual([bset.currency, bset.currency_source, bset.persona, bset.old_after_days, bset.tab_hidden], ['GBP', 'settings', 'resell', 60, true]);
  assert.equal((await api.overview(30, '2026-10-27')).held.cash_cents, cashBefore, 'relabelling to GBP leaves every stored amount as it was');
  await rejects(api.saveSettings({ old_after_days: 3 }), 'stock_check_violation', 'old threshold outside 7 to 365');
  await rejects(api.saveSettings({ currency: 'JPY' }), 'stock_check_violation', 'a currency outside the 8 launch currencies');
  const oneRow = await api.itemById(page.rows[0].id); assert.equal(oneRow.id, page.rows[0].id, 'itemById returns the row'); assert.equal(await api.itemById('no-such-id'), null, 'itemById: unknown id is null, not an error');
  const bootKeyHidden = (await api.boot()).tab_hidden; assert.equal(bootKeyHidden, true, 'boot carries tab_hidden');
  // switches
  assert.deepEqual(await core.createApi(load('?plan=elite&stock=off').supabase.createClient()).boot(), { mode: 'off' });
  assert.equal((await core.createApi(load('?plan=free').supabase.createClient()).boot()).plan.free_cap, 25, '?plan=free is a Free account');
  assert.equal((await core.createApi(load('?plan=elite&stock_paid=0').supabase.createClient()).boot()).plan.paid, false);
  assert.deepEqual(await core.createApi(load('?plan=free&stock=admin').supabase.createClient()).boot(), { mode: 'off' }, 'admin mode: a free QA user is not admin');
  // no engine script loaded: the old behaviour, nothing breaks
  const bare = load('?plan=elite', false).supabase.createClient(); assert.match((await bare.rpc('stock_boot')).error.message, /not implemented/);
  assert.equal(win.__qaErrors.length, 0, 'no window errors recorded: ' + win.__qaErrors.join(' | '));
});
test('F qa_mock.js wiring: the Stock RPCs and the claims hooks are present, and ops/ stays out of deploys', () => {
  const mock = fs.readFileSync(path.join(__dirname, 'qa_mock.js'), 'utf8');
  for (const needle of ['SnypdStockEngine', "/^stock_/.test(name)", 'stock_seed', 'mirrorClaimUpdate', 'mirrorClaimDelete', 'stock_today', 'stock_claims', 'stock_hidden', 'stock_tab_hidden', "table === 'stock_settings'"]) assert(mock.includes(needle), 'qa_mock.js is missing ' + needle);
  assert(/^ops\/\s*$/m.test(fs.readFileSync(path.join(__dirname, '..', '.vercelignore'), 'utf8')), 'ops/ must stay in .vercelignore');
  assert.equal((fs.readFileSync(path.join(__dirname, '..', 'assets', 'stock-core.js'), 'utf8').match(/[^\x20-\x7e\r\n]/g) || []).length, 0, 'stock-core.js must stay pure ASCII');
});

test('X CSV export + template: formula guard on text cells only, missing stays empty, FR = semicolon + decimal comma, the importer reads the headers back', () => {
  const Imp = require('../assets/stock-import.js'), BOM = String.fromCharCode(0xfeff);
  const rows = [
    { title: '=SUM(A1)', brand: '+1', size: '-2', status: 'sold', condition: 'good', category: 'tops', buy_cents: 1000, extra_cents: 150, bought_on: '2026-10-01', src: '@hunt', platform: 'vinted', list_cents: 3000, sold_cents: 2500, sold_on: '2026-10-09', ship_paid_cents: 0, fee_cents: 0, notes: 'say "hi"\nsecond line; ok' },
    { title: 'Loss, jacket', status: 'sold', buy_cents: 5000, sold_cents: 4500, bought_on: '2026-10-02', sold_on: '2026-10-03' },
    { title: 'No cost', status: 'stock', buy_cents: null, extra_cents: null, bought_on: '2026-10-04' }
  ];
  const en = core.exportCsv(rows, { lang: 'en', labels: { status: k => k.toUpperCase() } }), fr = core.exportCsv(rows, { lang: 'fr' });
  assert.equal(en.charAt(0), BOM, 'BOM');
  const lines = en.slice(1).split('\r\n');
  assert.equal(lines[0], core.EXPORT_HEAD.en.join(','), 'header row');
  assert(lines[1].startsWith("'=SUM(A1),'+1,'-2,SOLD,"), 'text cells starting with = + - are guarded: ' + lines[1]);
  assert(lines[1].includes(",'@hunt,"), 'a leading @ is guarded too');
  assert(en.includes('"say ""hi""\nsecond line; ok"'), 'quotes doubled, newline kept inside quotes');
  assert(lines[1].includes(',10.00,1.50,2026-10-01,') && lines[1].includes(',25.00,2026-10-09,13.50,'), 'amounts are plain numbers with a point; profit = sold - cost incl. extra: ' + lines[1]);
  assert(lines[2].startsWith('"Loss, jacket",,,SOLD,'), 'a comma inside a value is quoted: ' + lines[2]);
  assert(lines[2].includes(',-5.00,'), 'a negative profit is a number, never guarded: ' + lines[2]);
  assert(lines[3].startsWith('No cost,,,STOCK,,,,,2026-10-04,'), 'missing amounts stay empty, never 0: ' + lines[3]);
  assert(!/NaN|undefined|null/.test(en), 'no NaN/undefined/null in the file');
  const frl = fr.slice(1).split('\r\n');
  assert(frl[0].includes(';') && !frl[0].includes(',') && frl[0].startsWith('Article;Marque;Taille;Statut;'), 'French header uses semicolons');
  assert(frl[1].includes(';10,00;1,50;2026-10-01;'), 'French amounts use a decimal comma: ' + frl[1]);
  assert(frl[2].startsWith('Loss, jacket;'), 'a comma needs no quotes when the separator is a semicolon: ' + frl[2]);
  assert.equal(core.exportCsv([], { lang: 'en' }), BOM + core.EXPORT_HEAD.en.join(',') + '\r\n', 'no rows: header only');
  // what the file says in its header must be readable by our own importer
  const want = { 'Item': 'title', 'Brand': 'brand', 'Size': 'size', 'Condition': 'condition', 'Category': 'category', 'Buy price': 'buy', 'Extra costs': 'extra', 'Date bought': 'bought', 'Source': 'source', 'Platform': 'platform', 'List price': 'list', 'Sold price': 'sold', 'Date sold': 'soldon', 'Notes': 'notes', 'Status': null, 'Profit': null };
  for (const m of Imp.mapHeaders(core.EXPORT_HEAD.en)) assert.equal(m.field, want[m.header], 'import reads the export header ' + m.header);
  // the template: 17 columns, every one recognised by the importer, in both languages
  for (const lang of ['en', 'fr']) {
    const tpl = core.templateCsv(lang); assert.equal(tpl.charAt(0), BOM);
    const head = Imp.parseCsv(tpl)[0] || Imp.parseCsv(tpl).rows[0];
    const m = Imp.mapHeaders(head), fields = m.map(x => x.field);
    assert.equal(head.length, 17, lang + ' template has 17 columns');
    assert(fields.every(Boolean) && new Set(fields).size === 17, lang + ' template: all 17 columns recognised by the importer, none twice: ' + fields.join(','));
  }
});
test('A migration 072 in the engine: P&L months = the design numbers and the Overview engine; expenses come off; series carries the period total; validation, isolation, undo', async () => {
  const a = account({ uid: 'A' }); a.eng.loadFixture(fx);
  const ox = require('./stock/acceptance-oracle.json');
  await a.api.addExpenses([{ spent_on: '2026-10-05', amount_cents: 1250, category: 'packaging' }, { spent_on: '2026-10-20', amount_cents: 999, category: 'tools', note: '  Listing tool  ' }, { spent_on: '2026-09-15', amount_cents: 500, category: 'postage' }]);
  const p = await a.api.pnl(3, '2026-10-27');
  assert.deepEqual(p.months.map(m => m.month), ['2026-10', '2026-09', '2026-08']);
  assert.deepEqual(p.months.map(m => m.item_profit).reverse(), ['2026-08', '2026-09', '2026-10'].map(k => ox.months[k].net));
  assert.deepEqual(p.months.map(m => m.revenue).reverse(), ['2026-08', '2026-09', '2026-10'].map(k => ox.months[k].rev));
  assert.deepEqual(p.months.map(m => m.sold).reverse(), ['2026-08', '2026-09', '2026-10'].map(k => ox.months[k].sold));
  assert.deepEqual(p.months.map(m => [m.expenses, m.item_profit - m.after]), [[2249, 2249], [500, 500], [0, 0]]);
  const mo = await a.api.expensesMonth('2026-10-17');
  assert.deepEqual([mo.month, mo.total, mo.count, mo.rows.map(r => r.amount_cents), mo.by_category.map(c => c.category + ':' + c.total), mo.rows.find(r => r.category === 'tools').note], ['2026-10', 2249, 2, [999, 1250], ['packaging:1250', 'tools:999'], 'Listing tool']);
  assert.deepEqual([(await a.api.overviewSeries(30, '2026-10-27')).expenses, (await a.api.overviewSeries(90, '2026-10-27')).expenses], [2249, 2749]);
  for (const [rows, code] of [[[{ spent_on: '2026-10-01', amount_cents: 100, category: 'food' }], 'stock_bad_category'], [[{ spent_on: '2026-10-01', amount_cents: 0, category: 'other' }], 'stock_amount_range'], [[{ amount_cents: 1, category: 'other' }], 'stock_expense_date_required'], [[{ spent_on: '2026-10-01', amount_cents: 1, category: 'other', note: 'x'.repeat(201) }], 'stock_note_too_long'], [[], 'stock_batch_too_large'], [[{ spent_on: '2026-10-01', amount_cents: 1, category: 'other' }, { spent_on: '2026-10-01', amount_cents: 1, category: 'nope' }], 'stock_bad_category']])
    await rejects(a.api.addExpenses(rows), code, code);
  assert.equal((await a.api.expensesMonth('2026-10-01')).count, 2, 'all or nothing');
  const sep = (await a.api.expensesMonth('2026-09-01')).rows[0], del = await a.api.deleteExpenses([sep.id]);
  assert.deepEqual(del.deleted.map(r => [r.spent_on, r.amount_cents, r.category]), [['2026-09-15', 500, 'postage']]);
  await rejects(a.api.deleteExpenses([sep.id]), 'stock_expense_not_found', 'gone');
  await a.api.addExpenses(del.deleted.map(r => ({ spent_on: r.spent_on, amount_cents: r.amount_cents, category: r.category, note: r.note })));
  assert.equal((await a.api.expensesMonth('2026-09-01')).total, 500, 'undo puts it back');
});

// bundle entry: one price for several items
test('A bundle split: rows always add up to the total exactly, leftover cents go to the first rows, typed costs are kept, over / mismatch refused', () => {
  const sp = core.splitCents;
  assert.deepEqual(sp(4000, 12, {}).cents, [334, 334, 334, 334, 333, 333, 333, 333, 333, 333, 333, 333]);
  assert.deepEqual(sp(1000, 3, { 0: 500 }).cents, [500, 250, 250]);
  assert.deepEqual(sp(1001, 3, { 1: 1 }).cents, [500, 1, 500]);
  assert.deepEqual([sp(1000, 2, { 0: 600, 1: 500 }).ok, sp(1000, 2, { 0: 600, 1: 500 }).reason], [false, 'over']);
  assert.deepEqual([sp(1000, 2, { 0: 300, 1: 500 }).ok, sp(1000, 2, { 0: 300, 1: 500 }).reason, sp(1000, 2, { 0: 300, 1: 500 }).rest], [false, 'mismatch', 200]);
  assert.deepEqual(sp(1000, 2, { 0: 400, 1: 600 }), { ok: true, cents: [400, 600], rest: 0 });
  assert.deepEqual(sp(0, 3, {}).cents, [0, 0, 0]);
  let seed = 7; const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
  for (let k = 0; k < 2000; k++) {
    const n = 1 + rnd(50), total = rnd(500000), locked = {};
    for (let i = 0; i < n; i++) if (rnd(4) === 0) locked[i] = rnd(Math.max(1, Math.floor(total / n) * 2));
    const r = sp(total, n, locked), used = Object.values(locked).reduce((a, b) => a + b, 0);
    if (r.ok) {
      assert.equal(r.cents.reduce((a, b) => a + b, 0), total, 'sum == total');
      for (const i of Object.keys(locked)) assert.equal(r.cents[i], locked[i], 'typed cost kept');
      const free = r.cents.filter((c, i) => locked[i] == null); if (free.length) assert(Math.max(...free) - Math.min(...free) <= 1, 'even within 1 cent');
      assert(r.cents.every(c => Number.isInteger(c) && c >= 0), 'whole, non-negative cents');
    } else assert(used > total ? r.reason === 'over' : (r.reason === 'mismatch' && Object.keys(locked).length === n), 'refusal reason: ' + r.reason);
  }
});

run().then(() => {
  const total = passed + failures.length;
  if (failures.length) {
    for (const f of failures) console.log(`FAIL  ${f.name}\n      ${String(f.error && f.error.stack || f.error).split('\n').slice(0, 6).join('\n      ')}`);
    console.log(`\n${failures.length} of ${total} FAILED, ${passed} passed${sql ? '' : ' (section C SKIPPED)'}`);
    process.exit(1);
  }
  console.log(`PASS: ${passed} of ${total} checks${sql ? ' (including the contract with migrations 065-067)' : ' -- section C (contract with the SQL) SKIPPED'}`);
});
