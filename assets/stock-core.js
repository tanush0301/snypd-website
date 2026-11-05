/*
 * SNYPD Stock - data layer (no DOM). Loaded lazily by the Stock tab (assets/stock.js, a later step); also required by the node tests.
 * Pure ASCII on purpose (like i18n.js / sw.js / consent.js): the one non-ASCII character this needs (the minus sign, U+2212) is built
 * with String.fromCharCode, because the editing tools turn backslash-u escapes into real characters.
 *
 * What is here
 *  - constants that MUST equal the database CHECKs / caps in backend-repo migrations 065-066 (ops/test_stock_core.cjs diffs them against the .sql)
 *  - money: cents <-> text, per-currency formatting (design stock-currency.js: Intl narrowSymbol, en -> en-GB, fr -> fr-FR, U+2212 minus)
 *  - small pure helpers on item rows (age, held, old, cost, profit) and on the overview JSON (display numbers, "29 of 31")
 *  - errors: every RAISE of the SQL RPCs mapped to a stable code + kind, so the UI never parses prose
 *  - createApi(supabaseClient): one method per RPC, argument names exactly as the SQL declares them; unwraps {data, error}, throws StockError
 * Money is integer cents in the ACCOUNT currency and is never converted. "--" is how a missing number is written.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdStock = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ------------------------------------------------------------------ constants (== SQL)
  const STATUSES = ['stock', 'listed', 'reserved', 'sold', 'returned', 'written_off'];
  const HELD = ['stock', 'listed', 'reserved', 'returned'];
  const PLATFORMS = ['vinted', 'ebay', 'depop', 'vestiaire', 'marktplaats', 'facebook', 'other'];
  const CONDITIONS = ['new_with_tag', 'new_no_tag', 'very_good', 'good', 'satisfactory'];
  const WRITE_OFF_REASONS = ['lost', 'damaged', 'unsellable', 'given_away'];
  const SRC_TYPES = ['hunt', 'place'];
  const CURRENCIES = ['EUR', 'GBP', 'SEK', 'PLN', 'USD', 'CZK', 'RON', 'HUF'];
  const PERSONAS = ['buy', 'resell', 'both'];
  const PERIODS = [7, 30, 90, 365];
  const DEFAULT_CATEGORY_KEYS = ['tops', 'bottoms', 'outerwear', 'shoes', 'bags', 'electronics', 'home', 'collect', 'other'];
  const CAPS = { freeHeld: 25, itemsPerAccount: 5000, quantityPerAdd: 50, importBatch: 500, categories: 30, undoWindowSeconds: 8, deletedDays: 30, oldAfterDefault: 45, moneyMaxCents: 1000000000 };
  const LOCALES = { en: 'en-GB', fr: 'fr-FR' };
  const MINUS = String.fromCharCode(0x2212);

  // ------------------------------------------------------------------ money
  const nfCache = {};
  function numberFormat(currency, lang, dp) {
    const key = currency + '|' + lang + '|' + (dp == null ? 'd' : dp);
    if (!nfCache[key]) {
      const o = { style: 'currency', currency: currency, currencyDisplay: 'narrowSymbol' };
      if (dp != null) { o.minimumFractionDigits = dp; o.maximumFractionDigits = dp; }
      nfCache[key] = new Intl.NumberFormat(LOCALES[lang] || LOCALES.en, o);
    }
    return nfCache[key];
  }
  // formatMoney(112450, 'EUR', 'en') -> EUR sign + "1,124.50"; negative -> U+2212 first; null/NaN -> "--"; opts.signed adds "+" to positive amounts
  function formatMoney(cents, currency, lang, opts) {
    if (cents == null || typeof cents !== 'number' || isNaN(cents)) return '--';
    const o = opts || {}, nf = numberFormat(currency || 'EUR', lang || 'en', o.dp);
    const s = nf.format(Math.abs(cents) / 100);
    if (cents < 0) return MINUS + s;
    return (o.signed && cents > 0 ? '+' : '') + s;
  }
  // the same amount as plain text for aria-label / copy: every Unicode space (no-break, narrow no-break, thin) becomes a normal space
  function moneyLabel(cents, currency, lang, opts) { return formatMoney(cents, currency, lang, opts).replace(/\s/g, ' '); }
  // "12.50", "12,50", "1,234.56", "1.234,56", "EUR 12", "12 EUR", "1 124,50 EUR" -> cents. Currency symbols/letters are accepted only BEFORE or AFTER the
  // number ("12abc34" is refused). Never guesses a third decimal: 3 digits after the language's own decimal sign is refused; after the OTHER sign it is a
  // thousands group. Negative -> refused. Empty -> {ok:true, cents:null, empty:true} (the field is simply not filled in).
  function parseMoneyInput(text, lang) {
    const raw = String(text == null ? '' : text).trim();
    if (raw === '') return { ok: true, cents: null, empty: true };
    if (raw.charAt(0) === '-' || raw.charAt(0) === MINUS) return { ok: false, cents: null, reason: 'negative' };
    const m = /^([^\d.,]*)([\d.,\s]*[\d.,])([^\d.,]*)$/.exec(raw);
    if (!m) return { ok: false, cents: null, reason: 'not_a_number' };
    const s = m[2].replace(/\s/g, '');
    const decSign = lang === 'fr' ? ',' : '.';
    const lastDot = s.lastIndexOf('.'), lastComma = s.lastIndexOf(',');
    let dec = null;
    if (lastDot >= 0 && lastComma >= 0) dec = lastDot > lastComma ? '.' : ',';
    else if (lastDot >= 0 || lastComma >= 0) {
      const sep = lastDot >= 0 ? '.' : ',', count = s.split(sep).length - 1, tail = s.length - s.lastIndexOf(sep) - 1;
      if (count > 1) dec = null;
      else if (tail === 3) dec = sep === decSign ? sep : null;
      else dec = sep;
    }
    let intPart = s, decPart = '';
    if (dec) { const i = s.lastIndexOf(dec); intPart = s.slice(0, i); decPart = s.slice(i + 1); }
    if (decPart.length > 2) return { ok: false, cents: null, reason: 'too_many_decimals' };
    if (/[.,]/.test(intPart) && !/^\d{1,3}([.,]\d{3})+$/.test(intPart)) return { ok: false, cents: null, reason: 'bad_grouping' };
    const digits = intPart.replace(/[.,]/g, '');
    if (digits === '' && decPart === '') return { ok: false, cents: null, reason: 'not_a_number' };
    const cents = (parseInt(digits || '0', 10) * 100) + parseInt((decPart + '00').slice(0, 2), 10);
    if (!(cents >= 0 && cents <= CAPS.moneyMaxCents)) return { ok: false, cents: null, reason: 'too_large' };
    return { ok: true, cents: cents };
  }

  // ------------------------------------------------------------------ dates
  const pad = n => String(n).padStart(2, '0');
  function localToday(now) { const d = now ? new Date(now) : new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }   // the DEVICE date: what the user calls "today"
  const dayNum = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / 86400000;
  function daysBetween(later, earlier) { return Math.round(dayNum(later) - dayNum(earlier)); }

  // ------------------------------------------------------------------ item helpers (rows as the RPCs return them)
  const isHeld = item => HELD.indexOf(item.status) >= 0 && item.deleted_at == null;
  const costCents = item => (item.buy_cents == null ? null : item.buy_cents + (item.extra_cents || 0));      // null = no buy price ("--")
  const ageDays = (item, today) => daysBetween(today, item.returned_on || item.bought_on);                      // fixed rule: restarts at a return
  const isOld = (item, today, oldAfter) => isHeld(item) && ageDays(item, today) >= (oldAfter == null ? CAPS.oldAfterDefault : oldAfter);
  function saleProfitCents(item) {   // only for a currently sold item with a buy price and a sale price; fee/shipping null = 0
    if (item.status !== 'sold' || item.buy_cents == null || item.sold_cents == null) return null;
    return item.sold_cents - costCents(item) - (item.fee_cents || 0) - (item.ship_paid_cents || 0);
  }

  // ------------------------------------------------------------------ overview JSON -> display numbers
  // Partial totals are shown as "29 of 31" (never a silent partial). avgProfit = net / sales with a cost, rounded to the cent.
  function viewOverview(ov) {
    const c = ov.current, p = ov.previous, h = ov.held;
    const view = {
      today: ov.today, days: ov.days, hasEvents: !!c.any, empty: ov.items === 0,
      held: { count: h.count, inStock: h.in_stock, listed: h.listed, reserved: h.reserved, returned: h.returned, cashCents: h.cash_cents, noCost: h.no_cost, old: h.old, oldCostCents: h.old_cost_cents },
      sold: c.sold, withCost: c.with_cost, partial: c.with_cost < c.sold, partialLabel: c.with_cost < c.sold ? c.with_cost + ' of ' + c.sold : null,
      revenueCents: c.any ? c.rev : null, netCents: c.any ? c.net : null, avgProfitCents: c.with_cost > 0 ? Math.round(c.net / c.with_cost) : null,
      daysToSell: c.days, returns: c.returns, writeOffs: c.wos, writeOffCostCents: c.wo_cost, refundsCents: c.refunds,
      prevNetCents: p && p.any ? p.net : null
    };
    view.deltaNetCents = (view.netCents != null && view.prevNetCents != null) ? view.netCents - view.prevNetCents : null;
    return view;
  }
  // Free-plan state from stock_boot().plan + counts: drives the 25-item meter (amber from 20) and the limit line.
  function freeCapState(boot) {
    const cap = boot.plan && boot.plan.free_cap, held = boot.counts ? boot.counts.held : 0;
    if (cap == null) return { limited: false, held: held, cap: null, left: null, atCap: false, warn: false };
    return { limited: true, held: held, cap: cap, left: Math.max(cap - held, 0), atCap: held >= cap, warn: held >= 20 };
  }

  // ------------------------------------------------------------------ errors
  // kind: disabled | auth | limit | validation | conflict | not_found | forbidden | network | unknown
  const CODE_KIND = {
    stock_disabled: 'disabled', stock_auth_required: 'auth',
    stock_free_limit: 'limit', stock_item_cap: 'limit', stock_category_limit: 'limit',
    stock_item_not_found: 'not_found',
    stock_transition_not_allowed: 'conflict', stock_written_off: 'conflict', stock_nothing_to_undo: 'conflict', stock_undo_expired: 'conflict',
    stock_field_not_editable: 'forbidden',
    stock_date_in_future: 'validation', stock_rows_must_be_array: 'validation', stock_title_required: 'validation', stock_bad_status: 'validation', stock_quantity_range: 'validation',
    stock_sold_needs_date: 'validation', stock_batch_too_large: 'validation', stock_import_id_required: 'validation', stock_reprice_must_lower: 'validation',
    stock_sold_before_bought: 'validation', stock_bad_destination: 'validation', stock_write_off_reason_required: 'validation', stock_return_before_sale: 'validation',
    stock_patch_must_be_object: 'validation', stock_bad_period: 'validation', stock_bad_sort: 'validation',
    stock_expense_cap: 'limit', stock_expense_not_found: 'not_found', stock_expense_date_required: 'validation', stock_amount_range: 'validation', stock_bad_category: 'validation', stock_note_too_long: 'validation'   // 072
  };
  class StockError extends Error {
    constructor(info) { super(info.message || info.code); this.name = 'StockError'; this.code = info.code; this.kind = info.kind; this.detail = info.detail || null; this.constraint = info.constraint || null; this.retryable = !!info.retryable; this.raw = info.raw || null; }
  }
  function parseError(err) {
    if (err instanceof StockError) return err;
    const msg = String((err && (err.message || err.error_description || err.msg)) || err || '');
    const detail = (err && (err.details || err.detail)) || null;
    const m = /\bstock_[a-z_]+\b/.exec(msg);
    if (m && CODE_KIND[m[0]]) return new StockError({ code: m[0], kind: CODE_KIND[m[0]], message: m[0], detail: detail, raw: err });
    const chk = /violates check constraint "([^"]+)"/.exec(msg);
    if (chk) return new StockError({ code: 'stock_check_violation', kind: 'validation', message: msg, constraint: chk[1], raw: err });
    if (/PGRST202|Could not find the function/i.test(msg) || (err && err.code === 'PGRST202')) return new StockError({ code: 'stock_not_deployed', kind: 'unknown', message: msg, raw: err });
    if (/permission denied|row-level security/i.test(msg) || (err && err.code === '42501')) return new StockError({ code: 'stock_forbidden', kind: 'forbidden', message: msg, raw: err });
    if (/JWT|not authenticated|401/i.test(msg)) return new StockError({ code: 'stock_auth_required', kind: 'auth', message: msg, raw: err });
    if (/Failed to fetch|NetworkError|network|timeout|ECONN|fetch failed|Load failed/i.test(msg)) return new StockError({ code: 'stock_network', kind: 'network', message: msg, retryable: true, raw: err });
    return new StockError({ code: 'stock_unknown', kind: 'unknown', message: msg, raw: err });
  }

  // ------------------------------------------------------------------ API: one method per RPC (names/arguments == the SQL)
  function compact(o) { const out = {}; Object.keys(o).forEach(k => { if (o[k] !== undefined) out[k] = o[k]; }); return out; }
  function createApi(client, opts) {
    const o = opts || {};
    const today = () => (o.today ? o.today() : localToday());
    async function call(name, args) {
      let r;
      try { r = await client.rpc(name, compact(args || {})); } catch (e) { throw parseError(e); }
      if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
      return r.data;
    }
    const api = {
      boot: () => call('stock_boot'),
      overview: (days, on) => call('stock_overview', { p_days: days == null ? null : days, p_today: on || today() }),
      lanes: on => call('stock_lanes', { p_today: on || today() }),
      counts: on => call('stock_counts', { p_today: on || today() }),
      overviewSeries: (days, on) => call('stock_overview_series', { p_days: days == null ? null : days, p_today: on || today() }),
      // 072: expenses + month-by-month P&L
      addExpenses: rows => call('stock_add_expenses', { p_rows: rows }),
      deleteExpenses: ids => call('stock_delete_expenses', { p_ids: ids }),
      expensesMonth: month => call('stock_expenses_month', { p_month: month || today() }),
      pnl: (months, on) => call('stock_pnl', { p_months: months == null ? 12 : months, p_today: on || today() }),
      itemsPage: (filters, limit, cursor) => call('stock_items_page', { p_filters: filters || {}, p_limit: limit == null ? 50 : limit, p_cursor: cursor || null }),
      addItems: (item, quantity) => call('stock_add_items', { p_item: item, p_quantity: quantity == null ? 1 : quantity }),
      importRows: (importId, rows) => call('stock_import_rows', { p_import_id: importId, p_rows: rows }),
      undoImport: importId => call('stock_undo_import', { p_import_id: importId }),
      setStatus: (id, to, x) => { x = x || {}; return call('stock_set_status', { p_id: id, p_to: to, p_platform: x.platform, p_list_cents: x.listCents, p_on: x.on }); },
      markSold: (id, x) => { x = x || {}; return call('stock_mark_sold', { p_id: id, p_sold_cents: x.soldCents == null ? null : x.soldCents, p_sold_on: x.on, p_platform: x.platform, p_fee_cents: x.feeCents, p_ship_paid_cents: x.shipPaidCents }); },
      markReturned: (id, x) => { x = x || {}; return call('stock_mark_returned', { p_id: id, p_returned_on: x.on, p_refund_cents: x.refundCents, p_refund_fee: x.refundFee, p_return_ship_cents: x.returnShipCents, p_to: x.to, p_reason: x.reason }); },
      writeOff: (id, reason, on) => call('stock_write_off', { p_id: id, p_reason: reason, p_on: on }),
      editItem: (id, patch) => call('stock_edit_item', { p_id: id, p_patch: patch }),
      deleteItem: id => call('stock_delete_item', { p_id: id }),
      restoreItem: id => call('stock_restore_item', { p_id: id }),
      undo: () => call('stock_undo'),
      // new categories (import review, later Settings): a direct insert, allowed by the own-row policy; the 30-per-account trigger answers stock_category_limit
      addCategories: async list => {
        let u; try { u = await client.auth.getUser(); } catch (e) { throw parseError(e); }
        const uid = u && u.data && u.data.user && u.data.user.id; if (!uid) throw parseError('not authenticated 401');
        let r; try { r = await client.from('stock_categories').insert(list.map(c => ({ user_id: uid, key: c.key, name: c.name, sort: 100 }))); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return list.length;
      },
      // Manage categories (design Ia): rename / hide one of your own categories; a direct UPDATE allowed by the own-row policy of 065, the name CHECK answers stock_check_violation.
      // Items keep their category key, so a rename relabels them and a hidden category keeps its items.
      updateCategory: async (key, patch) => {
        const row = {}; if (patch.name !== undefined) row.name = String(patch.name).trim(); if (patch.hidden !== undefined) row.hidden = !!patch.hidden;
        let r; try { r = await client.from('stock_categories').update(row).eq('key', key); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return row;
      },
      // account settings (currency, persona, tab_hidden, old_after_days): own-row insert/update policies on stock_settings (065), so one upsert; the CHECKs answer stock_check_violation.
      // Changing the currency relabels the numbers and never converts them.
      saveSettings: async patch => {
        const row = {}; ['currency', 'persona', 'tab_hidden', 'old_after_days', 'weekly_email'].forEach(k => { if (patch[k] !== undefined) row[k] = patch[k]; });   // weekly_email: 073
        let u; try { u = await client.auth.getUser(); } catch (e) { throw parseError(e); }
        const uid = u && u.data && u.data.user && u.data.user.id; if (!uid) throw parseError('not authenticated 401');
        row.user_id = uid;
        let r; try { r = await client.from('stock_settings').upsert(row, { onConflict: 'user_id' }); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return row;
      },
      // the weekly-email switch (073) lives only in the settings row: select-own through RLS; null = no row yet (= on). Before 073 the column is missing and this throws.
      settingsRow: async () => {
        let r; try { r = await client.from('stock_settings').select('weekly_email').maybeSingle(); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return r.data || null;
      },
      // one item by id (a Today lane opens its item without paging through the list); select-own through RLS
      itemById: async id => {
        let r; try { r = await client.from('stock_items').select('*').eq('id', id).maybeSingle(); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return r.data || null;
      },
      // the item's timeline (stock_history is select-own through RLS; only the RPCs can write it)
      itemHistory: async id => {
        let r;
        try { r = await client.from('stock_history').select('id,kind,at,data').eq('item_id', id).order('id', { ascending: true }); } catch (e) { throw parseError(e); }
        if (!r || r.error) throw parseError(r && r.error ? r.error : 'empty response');
        return r.data || [];
      },
      // every item of a filter, page by page (never more than 200 per request); stops at the first error
      walkItems: async function* (filters, pageSize) {
        let cursor = null;
        for (;;) {
          const page = await api.itemsPage(filters, pageSize || 200, cursor);
          for (const row of page.rows) yield row;
          if (!page.next_cursor) return;
          cursor = page.next_cursor;
        }
      }
    };
    return api;
  }

  // ------------------------------------------------------------------ export (CSV) + template (step 2)
  // UTF-8 with a BOM so Excel keeps the accents; French = semicolon + decimal comma (Excel in FR/BE), English = comma + decimal point. Dates are ISO
  // (YYYY-MM-DD), which the importer reads back. Amounts are plain numbers in the account currency (no symbol), a missing value stays empty (never 0).
  // Text cells that begin with = + - @ (or a tab / CR) get a leading apostrophe so a spreadsheet never runs them as a formula.
  const U = String.fromCharCode;
  const fx = s => s.replace(/~e/g, U(0xe9)).replace(/~E/g, U(0xc9)).replace(/~'/g, U(0x2019));
  const EXPORT_HEAD = {
    en: ['Item', 'Brand', 'Size', 'Status', 'Condition', 'Category', 'Buy price', 'Extra costs', 'Date bought', 'Source', 'Platform', 'List price', 'Sold price', 'Date sold', 'Profit', 'Notes'],
    fr: ['Article', 'Marque', 'Taille', 'Statut', '~Etat', 'Cat~egorie', "Prix d~'achat", 'Frais en plus', "Date d~'achat", 'Source', 'Plateforme', 'Prix affich~e', 'Prix de vente', 'Date de vente', 'B~en~efice', 'Notes'].map(fx)
  };
  const TEMPLATE_HEAD = {
    en: ['Item', 'Brand', 'Size', 'Condition', 'Category', 'Quantity', 'Bought', 'Buy price', 'Extra costs', 'Source', 'Platform', 'List price', 'Sold price', 'Sold date', 'Fees', 'Shipping paid', 'Notes'],
    fr: ['Article', 'Marque', 'Taille', '~Etat', 'Cat~egorie', 'Quantit~e', "Date d~'achat", "Prix d~'achat", 'Frais en plus', 'Source', 'Plateforme', 'Prix affich~e', 'Prix de vente', 'Date de vente', 'Frais', 'Envoi pay~e', 'Notes'].map(fx)
  };
  function csvCell(v, isText, sep) {
    let s = v == null ? '' : String(v);
    if (isText && /^[=+\-@\t\r]/.test(s)) s = "'" + s;
    if (s.indexOf(sep) >= 0 || /["\r\n]/.test(s)) s = '"' + s.replace(/"/g, '""') + '"';
    return s;
  }
  // o.labels = { status(key), cond(key), cat(key), plat(key) } -> display text; falls back to the stored key
  function exportCsv(rows, o) {
    const lang = o && o.lang === 'fr' ? 'fr' : 'en', L = (o && o.labels) || {}, sep = lang === 'fr' ? ';' : ',', dec = lang === 'fr' ? ',' : '.';
    const lab = (fn, k) => (k == null || k === '' ? '' : (fn ? fn(k) : k));
    const amt = c => (c == null ? '' : (c / 100).toFixed(2).replace('.', dec));
    const lines = [EXPORT_HEAD[lang].join(sep)];
    for (const it of rows) {
      const cells = [[it.title, 1], [it.brand, 1], [it.size, 1], [lab(L.status, it.status), 1], [lab(L.cond, it.condition), 1], [lab(L.cat, it.category), 1],
        [amt(it.buy_cents)], [amt(it.extra_cents)], [it.bought_on || ''], [it.src, 1], [lab(L.plat, it.platform), 1], [amt(it.list_cents)], [amt(it.sold_cents)], [it.sold_on || ''],
        [amt(saleProfitCents(it))], [it.notes, 1]];
      lines.push(cells.map(c => csvCell(c[0], c[1], sep)).join(sep));
    }
    return U(0xfeff) + lines.join('\r\n') + '\r\n';
  }
  // == migration 072: the six expense categories (CHECK on stock_expenses.category)
  const EXPENSE_CATEGORIES = ['packaging', 'postage', 'promotion', 'tools', 'travel', 'other'];

  // ------------------------------------------------------------------ bundle: one price paid for several items
  // splitCents(total, n, locked): locked = { rowIndex: cents } the user typed; the other rows share what is left evenly, the leftover cents going to the
  // first of them (so the rows always add up to the total exactly). reason: 'over' = typed costs exceed the total, 'mismatch' = every row typed, sum != total.
  function splitCents(total, n, locked) {
    locked = locked || {};
    const out = new Array(n).fill(null), free = []; let used = 0;
    for (let i = 0; i < n; i++) { if (locked[i] != null) { out[i] = locked[i]; used += locked[i]; } else free.push(i); }
    const rest = total - used;
    if (rest < 0) return { ok: false, reason: 'over', cents: out, rest };
    if (!free.length) return rest === 0 ? { ok: true, cents: out, rest } : { ok: false, reason: 'mismatch', cents: out, rest };
    const base = Math.floor(rest / free.length); let extra = rest - base * free.length;
    free.forEach(i => { out[i] = base + (extra > 0 ? 1 : 0); if (extra > 0) extra--; });
    return { ok: true, cents: out, rest };
  }
  // reprice suggestion: pct lower than the current price, rounded DOWN to a whole unit from 10.00 up (to 0.10 below 10.00);
  // always above 0 and below the current price, else null (no lower price to suggest)
  function suggestLower(cents, pct) {
    if (!(cents > 0) || !(pct > 0 && pct < 100)) return null;
    const raw = Math.floor(cents * (100 - pct) / 100), step = raw >= 1000 ? 100 : 10, v = Math.floor(raw / step) * step;
    return v > 0 && v < cents ? v : null;
  }
  function templateCsv(lang) { const l = lang === 'fr' ? 'fr' : 'en'; return U(0xfeff) + TEMPLATE_HEAD[l].join(l === 'fr' ? ';' : ',') + '\r\n'; }

  return { STATUSES, HELD, PLATFORMS, CONDITIONS, WRITE_OFF_REASONS, SRC_TYPES, CURRENCIES, PERSONAS, PERIODS, DEFAULT_CATEGORY_KEYS, CAPS, LOCALES, MINUS, CODE_KIND,
    formatMoney, moneyLabel, parseMoneyInput, localToday, daysBetween, isHeld, costCents, ageDays, isOld, saleProfitCents, viewOverview, freeCapState,
    StockError, parseError, createApi, exportCsv, templateCsv, EXPORT_HEAD, TEMPLATE_HEAD, splitCents, suggestLower, EXPENSE_CATEGORIES };
});
