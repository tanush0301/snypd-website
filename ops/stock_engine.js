/*
 * Stock RPC engine: an in-memory JavaScript port of migrations 065-068 (backend repo ops/migrations/) for QA and tests.
 * Never shipped (ops/ is in .vercelignore, never referenced by a page).
 *
 * WHY: ops/qa_mock.js says it plainly - a mock that does not enforce the real constraints has hidden real bugs before. So this engine
 *   (1) uses the SAME function names and argument names as the SQL (an unknown argument name fails like PostgREST does, PGRST202);
 *   (2) enforces the same CHECK constraints, with the same constraint names in the error text;
 *   (3) raises the same error codes ('stock_free_limit', 'stock_transition_not_allowed', ...) as the SQL RPCs;
 *   (4) implements the same maths: events summed by their own date, a sale history row only counts when a later 'return' row reversed it,
 *       held = stock + listed + reserved + returned, age = today - coalesce(returned_on, bought_on).
 * ops/test_stock_core.cjs checks it against the frozen design numbers (the same oracle the SQL test suite is checked against) and against the
 * hand-worked lifecycle numbers of ops/stock_tests/tests_b.sql B7. If you change a SQL function, change this port and those tests together.
 *
 * Works as a CommonJS module (node tests) and as a plain <script> (window.SnypdStockEngine) for qa_mock.js.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdStockEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const ENUMS = {
    status: ['stock', 'listed', 'reserved', 'sold', 'returned', 'written_off'],
    held: ['stock', 'listed', 'reserved', 'returned'],
    platform: ['vinted', 'ebay', 'depop', 'vestiaire', 'marktplaats', 'facebook', 'other'],
    condition: ['new_with_tag', 'new_no_tag', 'very_good', 'good', 'satisfactory'],
    writeOffReason: ['lost', 'damaged', 'unsellable', 'given_away'],
    srcType: ['hunt', 'place'],
    currency: ['EUR', 'GBP', 'SEK', 'PLN', 'USD', 'CZK', 'RON', 'HUF'],
    persona: ['buy', 'resell', 'both'],
    historyKind: ['bought', 'listed', 'relisted', 'sale', 'return', 'write_off']
  };
  const CAPS = { freeHeld: 25, items: 5000, quantity: 50, importBatch: 500, categories: 30, undoSeconds: 15, deletedDays: 30, oldAfterDefault: 45, money: 1000000000 };
  const DEFAULT_CATEGORIES = [['tops', 'Tops', 10], ['bottoms', 'Bottoms', 20], ['outerwear', 'Outerwear', 30], ['shoes', 'Shoes', 40], ['bags', 'Bags and accessories', 50],
    ['electronics', 'Electronics', 60], ['home', 'Home', 70], ['collect', 'Collectibles and games', 80], ['other', 'Other', 90]];
  // Allowed argument names per function (PostgREST refuses a call whose argument set it cannot match).
  const SIGNATURES = {
    stock_boot: [], stock_overview: ['p_days', 'p_today'], stock_lanes: ['p_today'], stock_items_page: ['p_filters', 'p_limit', 'p_cursor'],
    stock_add_items: ['p_item', 'p_quantity'], stock_import_rows: ['p_import_id', 'p_rows'], stock_undo_import: ['p_import_id'],
    stock_set_status: ['p_id', 'p_to', 'p_platform', 'p_list_cents', 'p_on'], stock_mark_sold: ['p_id', 'p_sold_cents', 'p_sold_on', 'p_platform', 'p_fee_cents', 'p_ship_paid_cents'],
    stock_mark_returned: ['p_id', 'p_returned_on', 'p_refund_cents', 'p_refund_fee', 'p_return_ship_cents', 'p_to', 'p_reason'],
    stock_write_off: ['p_id', 'p_reason', 'p_on'], stock_edit_item: ['p_id', 'p_patch'], stock_delete_item: ['p_id'], stock_restore_item: ['p_id'], stock_undo: []
  };
  const REQUIRED = { stock_add_items: ['p_item'], stock_import_rows: ['p_import_id', 'p_rows'], stock_undo_import: ['p_import_id'], stock_set_status: ['p_id', 'p_to'], stock_mark_sold: ['p_id', 'p_sold_cents'],
    stock_mark_returned: ['p_id'], stock_write_off: ['p_id', 'p_reason'], stock_edit_item: ['p_id', 'p_patch'], stock_delete_item: ['p_id'], stock_restore_item: ['p_id'] };
  const EDITABLE = ['title', 'brand', 'size', 'condition', 'category', 'buy_cents', 'extra_cents', 'list_cents', 'bought_on', 'src', 'src_type', 'notes', 'link', 'platform', 'sold_cents', 'sold_on', 'fee_cents', 'ship_paid_cents'];

  // ---------- errors (shape of a PostgREST error body: message, code, details, hint) ----------
  function pgError(message, code, details, hint) { const e = new Error(message); e.pg = { message, code: code || 'P0001', details: details || null, hint: hint || null }; return e; }
  const raise = (message, detail, code) => { throw pgError(message, code || 'P0001', detail || null); };

  // ---------- small helpers ----------
  const pad = n => String(n).padStart(2, '0');
  function isoDate(ms) { const d = new Date(ms); return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`; }
  function parseDate(v) {   // strict YYYY-MM-DD, like ::date on a clean ISO string
    if (v == null || v === '') return null;
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(v));
    if (!m) raise(`invalid input syntax for type date: "${v}"`, null, '22007');
    const t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
    if (isoDate(t) !== String(v)) raise(`date/time field value out of range: "${v}"`, null, '22008');
    return String(v);
  }
  const dayNum = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / 86400000;
  const diffDays = (a, b) => Math.round(dayNum(a) - dayNum(b));          // a - b in days
  const addDays = (s, n) => isoDate((dayNum(s) + n) * 86400000);
  function toBigint(v) {
    if (v == null || v === '') return null;
    if (typeof v === 'number') { if (!Number.isInteger(v)) raise(`invalid input syntax for type bigint: "${v}"`, null, '22P02'); return v; }
    if (typeof v === 'string' && /^-?\d+$/.test(v.trim())) return Number(v.trim());
    return raise(`invalid input syntax for type bigint: "${v}"`, null, '22P02');
  }
  const txt = v => (v == null ? null : String(v));
  const btrim = v => (v == null ? '' : String(v).trim());
  const nullif = (v, x) => (v === x ? null : v);
  const clone = o => JSON.parse(JSON.stringify(o));
  const sum = (arr, f) => arr.reduce((a, x) => a + (f(x) || 0), 0);

  function check(name, ok) { if (!ok) raise(`new row for relation "stock_items" violates check constraint "${name}"`, null, '23514'); }
  function checkRow(r) {   // the CHECKs of 065, same names
    const len = (v, a, b) => v != null && v.length >= a && v.length <= b;
    check('stock_items_title_check', len(btrim(r.title), 1, 140));
    check('stock_items_brand_check', r.brand == null || r.brand.length <= 60);
    check('stock_items_size_check', r.size == null || r.size.length <= 20);
    check('stock_items_condition_check', r.condition == null || ENUMS.condition.includes(r.condition));
    check('stock_items_category_check', r.category == null || len(r.category, 1, 40));
    for (const f of ['buy_cents', 'extra_cents', 'list_cents', 'sold_cents', 'fee_cents', 'ship_paid_cents', 'refund_cents', 'return_ship_cents']) {
      check(`stock_items_${f}_check`, r[f] == null || (r[f] >= 0 && r[f] <= CAPS.money));
    }
    check('stock_items_status_check', ENUMS.status.includes(r.status));
    check('stock_items_platform_check', r.platform == null || ENUMS.platform.includes(r.platform));
    check('stock_items_src_check', r.src == null || r.src.length <= 80);
    check('stock_items_src_type_check', r.src_type == null || ENUMS.srcType.includes(r.src_type));
    check('stock_items_write_off_reason_check', r.write_off_reason == null || ENUMS.writeOffReason.includes(r.write_off_reason));
    check('stock_items_drops_check', r.drops >= 0);
    check('stock_items_notes_check', r.notes == null || r.notes.length <= 2000);
    check('stock_items_link_check', r.link == null || r.link.length <= 500);
    check('stock_items_sold_needs_date', r.status !== 'sold' || r.sold_on != null);
    check('stock_items_wo_needs_fields', r.status !== 'written_off' || (r.written_off_on != null && r.write_off_reason != null));
    check('stock_items_returned_needs_on', r.status !== 'returned' || r.returned_on != null);
    check('stock_items_sold_after_bought', r.sold_on == null || r.sold_on >= r.bought_on);
    check('stock_items_wo_after_bought', r.written_off_on == null || r.written_off_on >= r.bought_on);
  }

  function createEngine(opts) {
    opts = opts || {};
    const S = {
      uid: opts.uid || 'qa-user-0000-0000-0000-000000000001', items: [], history: [], hid: 0, settings: null, categories: [], undo: null, searches: opts.searches || [],
      paid: opts.paid !== false, admin: !!opts.admin, mode: opts.mode || 'all', seq: 0
    };
    const nowMs = () => (opts.now ? opts.now() : Date.now());
    const today = () => (opts.today ? opts.today() : isoDate(nowMs()));
    const newId = () => (opts.newId ? opts.newId() : (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'item-' + (++S.seq) + '-' + Math.random().toString(16).slice(2, 10)));
    const stockMode = () => (S.mode === 'all' ? 'all' : (S.mode === 'admin' && S.admin ? 'admin' : 'off'));
    function gate() { if (!S.uid) raise('stock_auth_required', null, '28000'); if (stockMode() === 'off') raise('stock_disabled'); }
    const live = () => S.items.filter(i => i.deleted_at == null);
    const isHeld = i => ENUMS.held.includes(i.status);
    const heldItems = () => live().filter(isHeld);
    const costOf = (buy, extra) => (buy == null ? null : buy + (extra || 0));
    const checkDate = d => { if (d != null && diffDays(d, today()) > 1) raise('stock_date_in_future', null, '22007'); return d; };

    function blank(f) {
      return Object.assign({ id: newId(), user_id: S.uid, title: null, brand: null, size: null, condition: null, category: null, buy_cents: null, extra_cents: 0, list_cents: null, sold_cents: null,
        fee_cents: null, ship_paid_cents: null, refund_cents: null, return_ship_cents: null, refund_fee: false, bought_on: today(), listed_on: null, reserved_on: null, sold_on: null,
        returned_on: null, written_off_on: null, status: 'stock', platform: null, src: null, src_type: null, write_off_reason: null, drops: 0, notes: null, link: null,
        deleted_at: null, import_id: null, claim_id: null, created_at: new Date(nowMs()).toISOString(), updated_at: new Date(nowMs()).toISOString() }, f || {});
    }
    function touch(r) { r.updated_at = new Date(nowMs()).toISOString(); }
    function addHistory(item_id, kind, at, data) { const h = { id: ++S.hid, item_id, user_id: S.uid, kind, at, data: data || {}, created_at: new Date(nowMs()).toISOString() }; S.history.push(h); return h.id; }
    function remember(kind, label, ids, prev, hist) { S.undo = { kind, label, item_ids: ids, prev: prev ? clone(prev) : null, history_ids: hist || [], created_at: nowMs() }; }
    function getItem(id) { const r = S.items.find(i => i.id === id && i.user_id === S.uid && i.deleted_at == null); if (!r) raise('stock_item_not_found', null, 'P0002'); return r; }
    function purgeDeleted() { const cut = nowMs() - CAPS.deletedDays * 86400000; const gone = S.items.filter(i => i.deleted_at != null && Date.parse(i.deleted_at) < cut).map(i => i.id); removeItems(gone); return gone.length; }
    function removeItems(ids) { const set = new Set(ids); S.items = S.items.filter(i => !set.has(i.id)); S.history = S.history.filter(h => !set.has(h.item_id)); }
    const freeCapLeft = () => (S.paid ? null : Math.max(CAPS.freeHeld - heldItems().length, 0));

    // ---------- insert (quick add, import) ----------
    function insertRows(rows, importId, strict) {
      if (!Array.isArray(rows)) raise('stock_rows_must_be_array', null, '22023');
      const today0 = today();
      let room = CAPS.items - S.items.length;
      let slots = freeCapLeft();
      const ids = [], hist = [], skipped = []; let ok = 0, limit = false, cap = false;
      rows.forEach((j, idx) => {
        const snap = { items: S.items.length, history: S.history.length, hid: S.hid };
        const added = [];
        try {
          j = j || {};
          const title = btrim(j.title);
          if (title === '') raise('stock_title_required');
          const status = (j.status == null || j.status === '') ? 'stock' : String(j.status);
          if (!['stock', 'listed', 'sold'].includes(status)) raise('stock_bad_status');
          const qty = j.quantity == null || j.quantity === '' ? 1 : toBigint(j.quantity);
          if (qty < 1 || qty > CAPS.quantity) raise('stock_quantity_range');
          const bought = parseDate(j.bought_on) || today0;
          if (diffDays(bought, today0) > 1) raise('stock_date_in_future');
          const buy = toBigint(j.buy_cents), extra = j.extra_cents == null ? 0 : toBigint(j.extra_cents), list = toBigint(j.list_cents);
          const sold = toBigint(j.sold_cents), fee = toBigint(j.fee_cents), ship = toBigint(j.ship_paid_cents);
          const plat = nullif(txt(j.platform), ''), src = nullif(btrim(j.src), '');
          const cost = costOf(buy, extra);
          let soldOn = null, listed = null;
          if (status === 'sold') {
            soldOn = parseDate(j.sold_on);
            if (soldOn == null) raise('stock_sold_needs_date');
            if (diffDays(soldOn, today0) > 1) raise('stock_date_in_future');
          } else if (status === 'listed') listed = parseDate(j.listed_on) || bought;
          if (qty > room) { cap = true; raise('stock_item_cap'); }
          if (status !== 'sold' && slots != null && qty > slots) { limit = true; raise('stock_free_limit'); }
          const batch = [];
          for (let q = 0; q < qty; q++) {
            const r = blank({ title, brand: nullif(btrim(j.brand), ''), size: nullif(btrim(j.size), ''), condition: nullif(txt(j.condition), ''), category: nullif(btrim(j.category), ''),
              buy_cents: buy, extra_cents: extra, list_cents: list, sold_cents: status === 'sold' ? sold : null, fee_cents: status === 'sold' ? fee : null, ship_paid_cents: status === 'sold' ? ship : null,
              bought_on: bought, listed_on: listed, sold_on: soldOn, status, platform: status === 'stock' ? null : plat, src, src_type: nullif(txt(j.src_type), ''),
              notes: nullif(btrim(j.notes), ''), link: nullif(btrim(j.link), ''), import_id: importId || null });
            checkRow(r); batch.push(r);
          }
          S.items.push(...batch); added.push(...batch);
          const newHist = [];
          batch.forEach(r => newHist.push(addHistory(r.id, 'bought', bought, { cost_cents: cost, src })));
          if (status === 'listed') batch.forEach(r => newHist.push(addHistory(r.id, 'listed', listed, { platform: plat, price_cents: list })));
          else if (status === 'sold') {
            const days = diffDays(soldOn, bought), profit = (cost == null || sold == null) ? null : sold - cost - (fee || 0) - (ship || 0);
            batch.forEach(r => newHist.push(addHistory(r.id, 'sale', soldOn, { sold_cents: sold, platform: plat, days, profit_cents: profit, fee_cents: fee, ship_paid_cents: ship })));
          }
          ids.push(...batch.map(r => r.id)); hist.push(...newHist); ok++; room -= qty;
          if (status !== 'sold' && slots != null) slots -= qty;
        } catch (e) {
          // the statement-level rollback of the failed row (a plpgsql sub-block): undo whatever this row added
          if (added.length) removeItems(added.map(r => r.id));
          S.hid = Math.max(S.hid, snap.hid);
          if (strict || !e.pg) throw e;
          skipped.push({ index: idx, reason: e.pg.message });
        }
      });
      return { ids, rows_inserted: ok, items_created: ids.length, skipped, free_limit_hit: limit, item_cap_hit: cap, history_ids: hist };
    }

    // ---------- event maths (== _stock_agg) ----------
    function events() {
      const lv = new Map(live().map(i => [i.id, i])), ev = [];
      live().forEach(i => {
        if (i.status === 'sold') ev.push({ t: 'sale', d: i.sold_on, amt: i.sold_cents, prof: (i.buy_cents == null || i.sold_cents == null) ? null : i.sold_cents - (i.buy_cents + i.extra_cents) - (i.fee_cents || 0) - (i.ship_paid_cents || 0), days: diffDays(i.sold_on, i.returned_on || i.bought_on) });
        if (i.status === 'written_off') ev.push({ t: 'wo', d: i.written_off_on, cost: costOf(i.buy_cents, i.extra_cents) });
      });
      S.history.forEach(h => {
        if (!lv.has(h.item_id)) return;
        if (h.kind === 'sale' && S.history.some(r => r.item_id === h.item_id && r.kind === 'return' && r.id > h.id)) ev.push({ t: 'sale', d: h.at, amt: h.data.sold_cents == null ? null : h.data.sold_cents, prof: h.data.profit_cents == null ? null : h.data.profit_cents, days: h.data.days == null ? null : h.data.days });
        if (h.kind === 'return') ev.push({ t: 'return', d: h.at, prof: h.data.profit_cents == null ? null : h.data.profit_cents, refund: h.data.refund_cents == null ? null : h.data.refund_cents });
      });
      return ev;
    }
    function agg(from, to) {   // [from, to) by event date, like _stock_agg
      const w = events().filter(e => e.d >= from && e.d < to);
      const sa = w.filter(e => e.t === 'sale'), re = w.filter(e => e.t === 'return'), wo = w.filter(e => e.t === 'wo');
      const salesProfit = sum(sa, e => e.prof), retProfit = sum(re, e => e.prof), woCost = sum(wo, e => e.cost);
      const salesRev = sum(sa, e => e.amt), refunds = sum(re, e => e.refund), daySum = sum(sa, e => e.days);
      return { any: w.length > 0, sales: sa.length, returns: re.length, wos: wo.length, sold: sa.length - re.length, with_cost: sa.filter(e => e.prof != null).length - re.filter(e => e.prof != null).length,
        sales_rev: salesRev, refunds, rev: salesRev - refunds, sales_profit: salesProfit, ret_profit: retProfit, wo_cost: woCost, net: salesProfit + retProfit - woCost, day_sum: daySum,
        days: sa.length > 0 ? Math.round(daySum / sa.length) : null };
    }
    const oldAfter = () => (S.settings && S.settings.old_after_days) || CAPS.oldAfterDefault;
    const ageOf = (i, t) => diffDays(t, i.returned_on || i.bought_on);

    // ---------- the RPCs ----------
    const R = {};
    R.stock_boot = function () {
      if (!S.uid) raise('stock_auth_required', null, '28000');
      const mode = stockMode();
      if (mode === 'off') return { mode: 'off' };
      if (!S.categories.length) S.categories = DEFAULT_CATEGORIES.map(c => ({ key: c[0], name: c[1], sort: c[2], hidden: false }));
      const first = S.searches.filter(s => s.vinted_url).sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)))[0];
      const m = first && /^https?:\/\/(?:www\.)?(vinted\.[a-z.]+)/.exec(first.vinted_url);
      const site = m ? m[1] : null;
      const def = { 'vinted.co.uk': 'GBP', 'vinted.se': 'SEK', 'vinted.pl': 'PLN', 'vinted.com': 'USD', 'vinted.cz': 'CZK', 'vinted.ro': 'RON', 'vinted.hu': 'HUF' }[site] || 'EUR';
      const set = S.settings || {};
      return { mode, currency: set.currency || def, currency_source: set.currency ? 'settings' : 'default', default_currency: def, first_hunt_site: site,
        persona: set.persona || null, tab_hidden: !!set.tab_hidden, old_after_days: set.old_after_days || CAPS.oldAfterDefault,
        categories: S.categories.slice().sort((a, b) => a.sort - b.sort || (a.key < b.key ? -1 : 1)).map(c => ({ key: c.key, name: c.name, hidden: c.hidden, sort: c.sort })),
        plan: { paid: S.paid, free_cap: S.paid ? null : CAPS.freeHeld },
        counts: { held: heldItems().length, items: live().length, deleted: S.items.length - live().length } };
    };
    R.stock_overview = function (a) {
      gate();
      const days = a.p_days == null ? null : a.p_days;
      const t = checkDate(parseDate(a.p_today)) || today();
      if (days != null && ![7, 30, 90, 365].includes(days)) raise('stock_bad_period', null, '22023');
      const old = oldAfter(), h = heldItems();
      const cost = i => (i.buy_cents || 0) + i.extra_cents, isOld = i => ageOf(i, t) >= old;
      const held = { count: h.length, in_stock: h.filter(i => i.status === 'stock' || i.status === 'returned').length, listed: h.filter(i => i.status === 'listed').length,
        reserved: h.filter(i => i.status === 'reserved').length, returned: h.filter(i => i.status === 'returned').length, cash_cents: sum(h, cost), no_cost: h.filter(i => i.buy_cents == null).length,
        old: h.filter(isOld).length, old_cost_cents: sum(h.filter(isOld), cost) };
      let cur, prev = null;
      if (days == null) cur = agg('0001-01-01', addDays(t, 1));
      else { cur = agg(addDays(t, -days + 1), addDays(t, 1)); prev = agg(addDays(t, -2 * days + 1), addDays(t, -days + 1)); }
      return { today: t, days, old_after_days: old, items: live().length, held, current: cur, previous: prev };
    };
    R.stock_lanes = function (a) {
      gate();
      const t = checkDate(parseDate(a.p_today)) || today(), h = heldItems().map(i => ({ i, age: ageOf(i, t) }));
      const rules = {
        reprice: x => x.i.status === 'listed' && x.i.listed_on != null && diffDays(t, x.i.listed_on) >= 30 && x.i.drops === 0,
        list: x => (x.i.status === 'stock' || x.i.status === 'returned') && x.age >= 7,
        follow: x => x.i.status === 'reserved' && x.i.reserved_on != null && diffDays(t, x.i.reserved_on) >= 3,
        hold: x => (x.i.status === 'stock' || x.i.status === 'returned') && x.i.src_type === 'hunt' && x.age >= 14 };
      const out = { today: t };
      Object.keys(rules).forEach(k => { const m = h.filter(rules[k]).sort((p, q) => q.age - p.age || (p.i.id < q.i.id ? -1 : 1)); out[k] = { count: m.length, items: m.slice(0, 5).map(x => ({ id: x.i.id, title: x.i.title, days: x.age })) }; });
      return out;
    };
    R.stock_items_page = function (a) {
      gate();
      const f = a.p_filters || {}, limit = Math.min(Math.max(a.p_limit == null ? 50 : a.p_limit, 1), 200), t = parseDate(f.today) || today();
      const q = f.q ? String(f.q).trim().slice(0, 100).toLowerCase() : null, old = oldAfter(), deleted = f.deleted || 'none';
      const base = S.items.filter(i => i.user_id === S.uid
        && ((deleted === 'only' && i.deleted_at != null) || (deleted !== 'only' && i.deleted_at == null))
        && (!f.status || f.status.includes(i.status)) && (!f.condition || f.condition.includes(i.condition))
        && (!q || (i.title || '').toLowerCase().includes(q) || (i.brand || '').toLowerCase().includes(q))
        && (!f.category || i.category === f.category) && (!f.platform || i.platform === f.platform) && (!f.src || i.src === f.src)
        && (!f.old || (isHeld(i) && ageOf(i, t) >= old)));
      base.sort((x, y) => (x.bought_on < y.bought_on ? 1 : x.bought_on > y.bought_on ? -1 : (x.id < y.id ? 1 : x.id > y.id ? -1 : 0)));
      const c = a.p_cursor && a.p_cursor.bought_on ? a.p_cursor : null;
      const after = c ? base.filter(i => i.bought_on < c.bought_on || (i.bought_on === c.bought_on && i.id < c.id)) : base;
      const shown = after.slice(0, limit), more = after.length > limit;
      const strip = i => { const o = clone(i); delete o.user_id; return o; };
      const last = shown[shown.length - 1];
      return { rows: shown.map(strip), next_cursor: more && last ? { bought_on: last.bought_on, id: last.id } : null, total: base.length };
    };
    R.stock_add_items = function (a) {
      gate(); purgeDeleted();
      const res = insertRows([Object.assign({}, a.p_item || {}, { quantity: a.p_quantity == null ? 1 : a.p_quantity, status: 'stock' })], null, true);
      remember('add', 'add', res.ids, null, res.history_ids);
      const out = Object.assign({}, res); delete out.history_ids; return out;
    };
    R.stock_import_rows = function (a) {
      gate();
      if (a.p_import_id == null) raise('stock_import_id_required', null, '22023');
      if (!Array.isArray(a.p_rows) || a.p_rows.length > CAPS.importBatch) raise('stock_batch_too_large', null, '22023');
      purgeDeleted();
      const res = insertRows(a.p_rows, a.p_import_id, false);
      const out = Object.assign({}, res); delete out.ids; delete out.history_ids; return out;
    };
    R.stock_undo_import = function (a) { gate(); const ids = S.items.filter(i => i.import_id === a.p_import_id && i.user_id === S.uid).map(i => i.id); removeItems(ids); return { removed: ids.length }; };
    R.stock_set_status = function (a) {
      gate();
      const it = getItem(a.p_id), prev = clone(it), on = checkDate(parseDate(a.p_on)) || today(), to = a.p_to; let hist = [];
      if (to === 'listed' && (it.status === 'stock' || it.status === 'returned')) {
        const had = it.returned_on != null;
        Object.assign(it, { status: 'listed', platform: nullif(txt(a.p_platform), ''), list_cents: a.p_list_cents != null ? toBigint(a.p_list_cents) : it.list_cents, listed_on: on, drops: 0 });
        checkRow(it);
        hist = [addHistory(it.id, had ? 'relisted' : 'listed', on, { platform: nullif(txt(a.p_platform), ''), price_cents: a.p_list_cents != null ? toBigint(a.p_list_cents) : it.list_cents })];
      } else if (to === 'listed' && it.status === 'listed') {
        const p = toBigint(a.p_list_cents);
        if (p == null || it.list_cents == null || p >= it.list_cents) raise('stock_reprice_must_lower', null, '22023');
        Object.assign(it, { list_cents: p, drops: it.drops + 1 }); checkRow(it);
      } else if (to === 'listed' && it.status === 'reserved') { Object.assign(it, { status: 'listed', reserved_on: null }); }
      else if (to === 'reserved' && it.status === 'listed') { Object.assign(it, { status: 'reserved', reserved_on: on }); }
      else if (to === 'stock' && it.status === 'listed') { Object.assign(it, { status: it.returned_on != null ? 'returned' : 'stock', platform: null, listed_on: null }); }
      else raise('stock_transition_not_allowed', `${it.status} -> ${to == null ? 'null' : to}`);
      touch(it); remember('update', 'status', [it.id], [prev], hist);
      return strip(it);
    };
    function strip(i) { const o = clone(i); delete o.user_id; return o; }
    R.stock_mark_sold = function (a) {
      gate();
      const it = getItem(a.p_id), prev = clone(it), on = checkDate(parseDate(a.p_sold_on)) || today();
      if (!ENUMS.held.includes(it.status)) raise('stock_transition_not_allowed', `${it.status} -> sold`);
      if (on < (it.returned_on || it.bought_on)) raise('stock_sold_before_bought', null, '22007');
      const soldC = toBigint(a.p_sold_cents), fee = toBigint(a.p_fee_cents), ship = toBigint(a.p_ship_paid_cents), plat = nullif(txt(a.p_platform), '') || it.platform;
      const cost = costOf(it.buy_cents, it.extra_cents), profit = (cost == null || soldC == null) ? null : soldC - cost - (fee || 0) - (ship || 0), days = diffDays(on, it.returned_on || it.bought_on);
      Object.assign(it, { status: 'sold', sold_cents: soldC, sold_on: on, platform: plat, fee_cents: fee, ship_paid_cents: ship, reserved_on: null }); checkRow(it); touch(it);
      const h = addHistory(it.id, 'sale', on, { sold_cents: soldC, platform: plat, days, profit_cents: profit, fee_cents: fee, ship_paid_cents: ship });
      remember('update', 'sold', [it.id], [prev], [h]);
      return Object.assign(strip(it), { profit_cents: profit, days });
    };
    R.stock_mark_returned = function (a) {
      gate();
      const it = getItem(a.p_id), prev = clone(it), on = checkDate(parseDate(a.p_returned_on)) || today(), to = a.p_to == null ? 'stock' : a.p_to;
      if (it.status === 'written_off') raise('stock_written_off', 'This item is written off. Undo the write-off first.');
      if (it.status !== 'sold') raise('stock_transition_not_allowed', `${it.status} -> returned`);
      if (!['stock', 'written_off'].includes(to)) raise('stock_bad_destination', null, '22023');
      if (to === 'written_off' && a.p_reason == null) raise('stock_write_off_reason_required', null, '22023');
      if (on < it.sold_on) raise('stock_return_before_sale', null, '22007');
      const cost = costOf(it.buy_cents, it.extra_cents), refund = a.p_refund_cents != null ? toBigint(a.p_refund_cents) : (it.sold_cents != null ? it.sold_cents : 0);
      const ship = a.p_return_ship_cents == null ? 0 : toBigint(a.p_return_ship_cents), feeBack = !!a.p_refund_fee;
      const rev = cost == null ? null : cost - refund + (feeBack ? (it.fee_cents || 0) : 0) - ship;
      Object.assign(it, { status: to === 'written_off' ? 'written_off' : 'returned', returned_on: on, refund_cents: refund, return_ship_cents: ship, refund_fee: feeBack, sold_cents: null, sold_on: null,
        fee_cents: null, ship_paid_cents: null, platform: null, listed_on: null, reserved_on: null, drops: 0, written_off_on: to === 'written_off' ? on : null, write_off_reason: to === 'written_off' ? a.p_reason : null });
      checkRow(it); touch(it);
      const hist = [addHistory(it.id, 'return', on, { refund_cents: refund, return_ship_cents: ship, fee_back: feeBack, to, profit_cents: rev })];
      if (to === 'written_off') hist.push(addHistory(it.id, 'write_off', on, { reason: a.p_reason, cost_cents: cost, from_status: 'returned' }));
      remember('update', 'returned', [it.id], [prev], hist);
      return Object.assign(strip(it), { reversal_cents: rev });
    };
    R.stock_write_off = function (a) {
      gate();
      const it = getItem(a.p_id), prev = clone(it), on = checkDate(parseDate(a.p_on)) || today();
      if (!ENUMS.held.includes(it.status)) raise('stock_transition_not_allowed', `${it.status} -> written_off`);
      if (a.p_reason == null || !ENUMS.writeOffReason.includes(a.p_reason)) raise('stock_write_off_reason_required', null, '22023');
      Object.assign(it, { status: 'written_off', written_off_on: on, write_off_reason: a.p_reason }); checkRow(it); touch(it);
      const h = addHistory(it.id, 'write_off', on, { reason: a.p_reason, cost_cents: costOf(it.buy_cents, it.extra_cents), from_status: prev.status });
      remember('update', 'write_off', [it.id], [prev], [h]);
      return strip(it);
    };
    R.stock_edit_item = function (a) {
      gate();
      const p = a.p_patch;
      if (p == null || typeof p !== 'object' || Array.isArray(p)) raise('stock_patch_must_be_object', null, '22023');
      const it = getItem(a.p_id);
      Object.keys(p).forEach(k => { if (!EDITABLE.includes(k)) raise('stock_field_not_editable', k, '42501'); });
      if (it.status !== 'sold' && ['sold_cents', 'sold_on', 'fee_cents', 'ship_paid_cents'].some(k => k in p)) raise('stock_field_not_editable', 'sale fields of an item that is not sold', '42501');
      const next = clone(it), has = k => Object.prototype.hasOwnProperty.call(p, k);
      if (has('title')) next.title = btrim(p.title);
      ['brand', 'size', 'category', 'src', 'notes', 'link'].forEach(k => { if (has(k)) next[k] = nullif(btrim(p[k]), ''); });
      ['condition', 'src_type', 'platform'].forEach(k => { if (has(k)) next[k] = nullif(txt(p[k]), ''); });
      ['buy_cents', 'list_cents', 'sold_cents', 'fee_cents', 'ship_paid_cents'].forEach(k => { if (has(k)) next[k] = toBigint(p[k]); });
      if (has('extra_cents')) next.extra_cents = toBigint(p.extra_cents) == null ? 0 : toBigint(p.extra_cents);
      if (has('bought_on')) next.bought_on = checkDate(parseDate(p.bought_on)) || it.bought_on;
      if (has('sold_on')) next.sold_on = checkDate(parseDate(p.sold_on)) || it.sold_on;
      checkRow(next); Object.assign(it, next); touch(it);
      return strip(it);
    };
    R.stock_delete_item = function (a) {
      gate(); purgeDeleted();
      const it = getItem(a.p_id), prev = clone(it);
      it.deleted_at = new Date(nowMs()).toISOString(); touch(it); remember('update', 'delete', [it.id], [prev], []);
      return { id: it.id, deleted: true };
    };
    R.stock_restore_item = function (a) {
      gate();
      const cut = nowMs() - CAPS.deletedDays * 86400000;
      const it = S.items.find(i => i.id === a.p_id && i.user_id === S.uid && i.deleted_at != null && Date.parse(i.deleted_at) >= cut);
      if (!it) raise('stock_item_not_found', null, 'P0002');
      const prev = clone(it);
      if (ENUMS.held.includes(it.status) && !S.paid && heldItems().length >= CAPS.freeHeld) raise('stock_free_limit', `The Free plan holds ${CAPS.freeHeld} items.`);
      it.deleted_at = null; touch(it); remember('update', 'restore', [it.id], [prev], []);
      return strip(it);
    };
    R.stock_undo = function () {
      gate();
      const u = S.undo;
      if (!u) raise('stock_nothing_to_undo');
      if (u.created_at < nowMs() - CAPS.undoSeconds * 1000) { S.undo = null; raise('stock_undo_expired'); }
      let n = 0;
      if (u.kind === 'add') { const ids = u.item_ids.filter(id => S.items.some(i => i.id === id)); removeItems(ids); n = ids.length; }
      else {
        u.prev.forEach(p => { const t = S.items.find(i => i.id === p.id && i.user_id === S.uid); if (t) { const keep = { id: t.id, user_id: t.user_id, created_at: t.created_at }; Object.assign(t, p, keep); touch(t); n++; } });
        const hs = new Set(u.history_ids); S.history = S.history.filter(h => !hs.has(h.id));
      }
      S.undo = null;
      return { undone: u.label, items: n, ids: u.item_ids };
    };

    async function rpc(name, args) {
      args = args || {};
      const fn = R[name];
      if (!fn || !SIGNATURES[name]) return { data: null, error: { message: `Could not find the function public.${name} in the schema cache`, code: 'PGRST202', details: null, hint: null } };
      const unknown = Object.keys(args).filter(k => !SIGNATURES[name].includes(k));
      const missing = (REQUIRED[name] || []).filter(k => !(k in args));
      if (unknown.length || missing.length) return { data: null, error: { message: `Could not find the function public.${name}(${Object.keys(args).sort().join(', ')}) in the schema cache`, code: 'PGRST202', details: null, hint: null } };
      try { return { data: clone(fn(args)), error: null }; }
      catch (e) { if (e.pg) return { data: null, error: e.pg }; throw e; }
    }

    // ---------- server-side paths the browser never has ----------
    function loadFixture(fx) {   // bypasses caps like a superuser backfill; history in logical write order
      fx.items.forEach(f => { const r = blank(Object.assign({}, f, { user_id: S.uid })); delete r.design_id; delete r.has_market; delete r.deleted_on; if (f.deleted_on) r.deleted_at = new Date(f.deleted_on + 'T12:00:00Z').toISOString(); S.items.push(r); });
      fx.history.forEach(h => addHistory(h.item, h.kind, h.at, h.data));
      return { items: S.items.length, history: S.history.length };
    }
    function mirrorClaim(c) {   // 067: a Feed claim becomes a Stock item (bypasses the Free cap on purpose)
      if (S.items.some(i => i.claim_id === c.id)) return null;
      const bought = isoDate(Date.parse(c.claimed_at || new Date(nowMs()).toISOString())), sold = c.status === 'sold';
      const soldOn = sold ? (c.sold_at ? isoDate(Date.parse(c.sold_at)) : bought) : null;
      const r = blank({ title: (btrim(c.title) || 'Claimed listing').slice(0, 140), brand: nullif(btrim(c.brand_title).slice(0, 60), ''), size: nullif(btrim(c.size_title).slice(0, 20), ''),
        buy_cents: c.bought_price_cents == null ? null : c.bought_price_cents, bought_on: bought, status: sold ? 'sold' : 'stock', sold_cents: sold ? (c.sold_price_cents == null ? null : c.sold_price_cents) : null,
        sold_on: soldOn && soldOn < bought ? bought : soldOn, src: 'SNYPD alert', link: nullif(btrim(c.vinted_url).slice(0, 500), ''), claim_id: c.id });
      checkRow(r); S.items.push(r); addHistory(r.id, 'bought', bought, { cost_cents: r.buy_cents, src: 'SNYPD alert' });
      if (sold) addHistory(r.id, 'sale', r.sold_on, { sold_cents: r.sold_cents, platform: null, days: diffDays(r.sold_on, bought), profit_cents: (r.buy_cents == null || r.sold_cents == null) ? null : r.sold_cents - r.buy_cents });
      return r.id;
    }
    function mirrorClaimUpdate(c, oldBoughtPrice) {   // 067 UPDATE branch: never overwrites what the user did to the item in Stock
      const it = S.items.find(i => i.claim_id === c.id && i.deleted_at == null);
      if (!it) return mirrorClaim(c);
      if (c.status === 'sold' && it.status === 'stock') {
        const bought = it.bought_on, soldOn = (c.sold_at ? isoDate(Date.parse(c.sold_at)) : bought), on = soldOn < bought ? bought : soldOn;
        const cost = costOf(c.bought_price_cents != null ? c.bought_price_cents : it.buy_cents, it.extra_cents);
        const profit = (cost == null || c.sold_price_cents == null) ? null : c.sold_price_cents - cost;
        Object.assign(it, { status: 'sold', sold_cents: c.sold_price_cents == null ? null : c.sold_price_cents, sold_on: on, buy_cents: c.bought_price_cents != null ? c.bought_price_cents : it.buy_cents });
        checkRow(it); touch(it);
        addHistory(it.id, 'sale', on, { sold_cents: it.sold_cents, platform: null, days: diffDays(on, bought), profit_cents: profit });
      } else if (c.bought_price_cents !== oldBoughtPrice && (it.status === 'stock' || it.status === 'sold')) { it.buy_cents = c.bought_price_cents == null ? null : c.bought_price_cents; touch(it); }
      return it.id;
    }
    function mirrorClaimDelete(claimId) {   // 067 DELETE branch: soft-delete only while the item is still plain 'stock'
      const it = S.items.find(i => i.claim_id === claimId && i.deleted_at == null && i.status === 'stock');
      if (it) { it.deleted_at = new Date(nowMs()).toISOString(); touch(it); }
    }
    return { rpc, state: S, agg, loadFixture, mirrorClaim, mirrorClaimUpdate, mirrorClaimDelete, setMode: m => { S.mode = m; }, setPaid: p => { S.paid = !!p; }, setSettings: s => { const n = Object.assign({}, S.settings, s); const bad = nm => raise(`new row for relation "stock_settings" violates check constraint "stock_settings_${nm}_check"`, null, '23514'); if (n.currency != null && !ENUMS.currency.includes(n.currency)) bad('currency'); if (n.persona != null && !ENUMS.persona.includes(n.persona)) bad('persona'); if (n.old_after_days != null && !(n.old_after_days >= 7 && n.old_after_days <= 365)) bad('old_after_days'); S.settings = n; },
      setSearches: s => { S.searches = s; }, today, helpers: { diffDays, addDays, isoDate } };
  }

  return { createEngine, ENUMS, CAPS, SIGNATURES, REQUIRED, EDITABLE, DEFAULT_CATEGORIES };
});
