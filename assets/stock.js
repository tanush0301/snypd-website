/*
 * SNYPD Stock UI, Step 3: the Items screen (list, filters, quick add, mark sold / returned / written off, item detail with history,
 * delete + restore, 8 s undo). Loaded lazily by dashboard.html after assets/stock-core.js and assets/stock-i18n.js, only when
 * dashboard_boot() says stock_mode is admin or all. Vanilla JS, no framework. Pure ASCII.
 * Every number comes from the RPCs (assets/stock-core.js); nothing here computes totals. Item titles, brands, notes are user content:
 * always escaped, never translated (the panel carries data-i18n-skip so the runtime translator leaves it alone).
 */
(function () {
  'use strict';
  var C = window.SnypdStock;
  if (!C) { console.error('SNYPD Stock: stock-core.js missing'); return; }
  var STR = window.SNYPD_STOCK_STR || { en: {}, fr: {} };
  var lang = (window.SNYPD_I18N && window.SNYPD_I18N.lang === 'fr') ? 'fr' : 'en';
  var S = null;   // state of the open panel

  // ------------------------------------------------------------------ helpers
  function T(key, vars) {
    var s = (STR[lang] && STR[lang][key]) || (STR.en && STR.en[key]) || key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.split('{' + k + '}').join(vars[k]); });
    return s;
  }
  function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function M(cents) { return C.formatMoney(cents, S.cur, lang); }
  function MS(cents) { return C.formatMoney(cents, S.cur, lang, { signed: true }); }
  function today() { return (S && S.todayFn) ? S.todayFn() : C.localToday(); }
  function fmtDate(iso) { if (!iso) return '--'; try { return new Date(iso + 'T12:00:00').toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); } catch (e) { return iso; } }
  function $(sel, root) { return (root || S.panel).querySelector(sel); }
  function catName(key) {
    if (!key) return T('cat.none');
    var c = (S.cats || []).filter(function (x) { return x.key === key; })[0];
    var defaults = C.DEFAULT_CATEGORY_KEYS.indexOf(key) >= 0;
    if (c && !(defaults && c.name === STR.en['cat.' + key])) return c.name;   // a renamed category keeps the user's own name
    return defaults ? T('cat.' + key) : (c ? c.name : key);
  }
  var statusLabel = function (s) { return T('status.' + s); };
  function option(val, label, sel) { return '<option value="' + esc(val) + '"' + (sel ? ' selected' : '') + '>' + esc(label) + '</option>'; }
  function condOptions(sel) { return option('', T('cond.none'), !sel) + C.CONDITIONS.map(function (c) { return option(c, T('cond.' + c), sel === c); }).join(''); }
  function platOptions(sel) { return option('', T('plat.none'), !sel) + C.PLATFORMS.map(function (p) { return option(p, T('plat.' + p), sel === p); }).join(''); }
  function catOptions(sel, withAny) {
    var cs = (S.cats || []).filter(function (c) { return !c.hidden || c.key === sel; });
    return option('', withAny ? T('filter.any') : T('cat.none'), !sel) + cs.map(function (c) { return option(c.key, catName(c.key), sel === c.key); }).join('');
  }
  function moneyExample() { return lang === 'fr' ? '12,50' : '12.50'; }
  function moneyText(cents) { return cents == null ? '' : (lang === 'fr' ? (cents / 100).toFixed(2).replace('.', ',') : (cents / 100).toFixed(2)); }

  // ------------------------------------------------------------------ errors -> plain text
  function errMsg(e) {
    var code = e && e.code, cap = (S && S.boot && S.boot.plan && S.boot.plan.free_cap) || C.CAPS.freeHeld;
    switch (code) {
      case 'stock_free_limit': return T('err.free_limit', { cap: cap });
      case 'stock_item_cap': return T('err.item_cap', { cap: C.CAPS.itemsPerAccount });
      case 'stock_item_not_found': return T('err.not_found');
      case 'stock_transition_not_allowed': return T('err.conflict');
      case 'stock_written_off': return T('err.written_off');
      case 'stock_reprice_must_lower': return T('err.reprice');
      case 'stock_date_in_future': return T('err.date_future');
      case 'stock_sold_before_bought': return T('err.sold_before');
      case 'stock_return_before_sale': return T('err.return_before');
      case 'stock_undo_expired': return T('err.undo_gone');
      case 'stock_nothing_to_undo': return T('err.nothing_undo');
      case 'stock_disabled': return T('err.disabled');
      case 'stock_expense_cap': return T('err.exp_cap');
      case 'stock_network': return T('err.network');
      default: return (e && e.kind === 'validation') ? T('err.validation') : T('err.unknown');
    }
  }

  // ------------------------------------------------------------------ open / shell
  function open(opts) {
    if (S && S.panel === opts.panel) { refresh(); return; }
    S = { client: opts.client, panel: opts.panel, todayFn: opts.today || null, api: C.createApi(opts.client, { today: opts.today }), boot: null, cur: 'EUR', cats: [], rows: [], next: null, total: 0,
      f: { status: HELD.slice(), q: '', condition: '', category: '', deleted: false, sort: 'oldest' }, sortOk: true, loading: true, err: null, req: 0, view: 'overview', ov: { days: 30, data: null, lanes: null, loading: false, err: null, req: 0, stale: false }, pinned: {}, itemsLoaded: false, undo: null, undoTimer: null, sheet: null, opener: null, searchTimer: null };
    S.panel.setAttribute('data-i18n-skip', '');
    S.panel.innerHTML = '<div class="st-wrap"><div class="st-skel"></div><div class="st-skel"></div><div class="st-skel"></div></div>';
    S.api.boot().then(function (b) {
      S.boot = b;
      if (b.mode === 'off') { S.panel.innerHTML = '<div class="st-wrap"><div class="st-err">' + esc(T('err.disabled')) + '</div></div>'; return; }
      S.cur = b.currency || 'EUR'; S.cats = b.categories || [];
      shell(); showView('overview');
      if (window.SNYPD && window.SNYPD.pendingStockSettings) { window.SNYPD.pendingStockSettings = false; openSettings(null); }
    }).catch(function (e) { S.panel.innerHTML = '<div class="st-wrap"><div class="st-err">' + esc(T('err.load')) + ' <button class="st-btn st-ghost" data-act="reopen">' + esc(T('err.retry')) + '</button></div></div>'; S.panel.onclick = function (ev) { if (ev.target.closest('[data-act="reopen"]')) { var p = S.panel, c = S.client; S = null; open({ client: c, panel: p }); } }; console.error('SNYPD Stock boot failed', e); });
  }
  function shell() {
    var statuses = [['held', T('chip.held')], ['', T('all')], ['stock', T('status.stock')], ['listed', T('status.listed')], ['reserved', T('status.reserved')], ['sold', T('status.sold')], ['returned', T('status.returned')], ['written_off', T('status.written_off')], ['old', T('tag.stale')]];
    S.panel.innerHTML =
      '<div class="st-wrap">' +
      '<h1 class="st-sr">' + esc(T('title')) + '</h1>' +
      '<div class="st-navrow"><div class="st-nav" role="group" aria-label="' + esc(T('title')) + '"><button type="button" class="st-navb" data-act="view" data-view="overview" aria-pressed="true">' + esc(T('nav.overview')) + '</button><button type="button" class="st-navb" data-act="view" data-view="items" aria-pressed="false">' + esc(T('nav.items')) + ' <span id="st-navn"></span></button><button type="button" class="st-navb" data-act="view" data-view="money" aria-pressed="false" id="st-nav-money" style="display:none">' + esc(T('nav.money')) + '</button></div>' +
      '<div class="st-navr"><div id="st-meter"></div><button type="button" class="st-btn st-tert" data-act="settings">' + esc(T('set.btn')) + '</button><button type="button" class="st-btn st-prim" data-act="add">' + esc(T('add')) + '</button></div></div>' +
      '<div id="st-capmsg"></div>' +
      '<div id="st-over"></div><div id="st-money" style="display:none"></div><div id="st-items" style="display:none">' +
      '<div class="st-itemshd"><h2 class="st-h2">' + esc(T('nav.items')) + '</h2><span class="st-secsub" id="st-itemssub"></span></div>' +
      '<div class="st-tools" id="st-tools">' +
      '<input class="st-in st-search" type="search" id="st-q" placeholder="' + esc(T('search')) + '" aria-label="' + esc(T('search.aria')) + '" autocomplete="off">' +
      '<button type="button" class="st-btn st-ghost st-toolsbtn" data-act="tools" aria-expanded="false" aria-controls="st-tools">' + esc(T('tools.btn')) + '</button>' +
      '<select class="st-in" id="st-cond" aria-label="' + esc(T('filter.condition')) + '">' + option('', T('filter.condition') + colon() + T('filter.any'), true) + C.CONDITIONS.map(function (c) { return option(c, T('cond.' + c)); }).join('') + '</select>' +
      '<select class="st-in" id="st-cat" aria-label="' + esc(T('filter.category')) + '">' + option('', T('filter.category') + colon() + T('filter.any'), true) + (S.cats || []).filter(function (c) { return !c.hidden; }).map(function (c) { return option(c.key, catName(c.key)); }).join('') + '</select>' +
      '<select class="st-in" id="st-sort" aria-label="' + esc(T('sort.label')) + '">' + option('oldest', T('sort.oldest'), true) + option('newest', T('sort.newest')) + '</select>' +
      '<select class="st-in" id="st-plat" aria-label="' + esc(T('f.platform')) + '">' + option('', T('plat.all'), true) + C.PLATFORMS.map(function (p) { return option(p, T('plat.' + p)); }).join('') + '</select>' +
      '<button type="button" class="st-btn st-tert" data-act="deleted" id="st-del" aria-pressed="false">' + esc(T('deleted.show')) + '</button>' +
      '<button type="button" class="st-btn st-ghost" data-act="import">' + esc(T('imp.btn')) + '</button><button type="button" class="st-btn st-ghost" data-act="export" id="st-export">' + esc(T('exp.btn')) + '</button>' +
      '<span class="st-count" id="st-count" aria-live="polite"></span></div>' +
      '<div class="st-chips" id="st-chips" role="group" aria-label="' + esc(T('filter.status')) + '">' + statuses.map(function (s) { return '<button type="button" class="st-chip" data-act="chip" data-status="' + s[0] + '" aria-pressed="' + (s[0] === 'held' ? 'true' : 'false') + '">' + esc(s[1]) + ' <span class="st-cn"></span></button>'; }).join('') + '</div>' +
      '<div id="st-body"></div></div></div><div id="st-ov"></div><div id="st-undo-root"></div>';
    S.panel.onclick = onClick; S.panel.onkeydown = onKey; S.panel.onchange = onChange;
    $('#st-q').oninput = function () { clearTimeout(S.searchTimer); var v = this.value; S.searchTimer = setTimeout(function () { S.f.q = v.trim(); load(true); }, 250); };
    $('#st-cond').onchange = function () { S.f.condition = this.value; load(true); };
    $('#st-cat').onchange = function () { S.f.category = this.value; load(true); };
    $('#st-plat').onchange = function () { S.f.platform = this.value; load(true); };
    $('#st-sort').onchange = function () { S.f.sort = this.value; load(true); };
    // a claim photo that fails to load (deleted on Vinted, offline) turns back into the initials tile
    S.panel.addEventListener('error', function (ev) { var im = ev.target; if (im && im.tagName === 'IMG' && im.classList.contains('st-ph')) { var t = im.parentNode; if (t) { t.classList.remove('has-ph'); t.textContent = t.getAttribute('data-ini') || '--'; } } }, true);
    renderMeter();
  }
  var CHIP_KEY = { held: 'held', '': 'all', stock: 'in_stock', listed: 'listed', reserved: 'reserved', sold: 'sold', returned: 'returned', written_off: 'written_off', old: 'old' };
  function renderChipCounts() {
    Array.prototype.forEach.call(S.panel.querySelectorAll('#st-chips .st-chip'), function (b) { var n = b.querySelector('.st-cn'); if (n) n.textContent = S.counts ? String(S.counts[CHIP_KEY[b.getAttribute('data-status')]]) : ''; });
  }
  function loadCounts() {   // migration 070; any failure only leaves the numbers off
    return S.api.counts(today()).then(function (c) { S.counts = c; renderChipCounts(); renderMeter(); }).catch(function () { S.counts = null; });
  }
  function renderMeter() {
    var el = $('#st-meter'); if (!el) return;
    var m = C.freeCapState(S.boot), n = $('#st-navn'), cm = $('#st-capmsg'), sub = $('#st-itemssub');
    if (n) n.textContent = String(m.held);
    if (sub && S.boot.counts) sub.textContent = S.counts ? T('it.sub3', { held: S.boot.counts.held, sold: S.counts.sold, rows: S.boot.counts.items }) : T('it.sub', { held: S.boot.counts.held, rows: S.boot.counts.items });
    if (!m.limited) { el.innerHTML = ''; if (cm) cm.innerHTML = ''; return; }
    el.innerHTML = '<div class="st-meter' + (m.warn ? ' warn' : '') + '"><span class="st-meter-txt">' + esc(T('meter.label')) + ' <b>' + m.held + ' / ' + m.cap + '</b></span><span class="st-meter-bar"><span class="st-meter-fill" style="width:' + Math.min(100, Math.round(m.held / m.cap * 100)) + '%"></span></span></div>';
    if (cm) cm.innerHTML = m.atCap ? '<p class="st-note">' + esc(T('meter.limit', { cap: m.cap })) + ' <a class="st-link" href="plans.html">' + esc(T('meter.upgrade')) + '</a></p>' : '';
  }

  // ------------------------------------------------------------------ overview + Today lanes + first run + settings (step 5)
  var PERIODS = [7, 30, 90, 365, null];
  var LANE_ROWS = 3;   // rows per Today lane (the RPC returns up to 5)
  var HELD = ['stock', 'listed', 'reserved', 'returned'];
  function colon() { return lang === 'fr' ? String.fromCharCode(0xa0) + ': ' : ': '; }
  function perKey(d) { return d == null ? 'all' : String(d); }
  function skipped() { try { return localStorage.getItem('snypd_stock_pq_skipped') === '1'; } catch (e) { return false; } }
  function setSkipped() { try { localStorage.setItem('snypd_stock_pq_skipped', '1'); } catch (e) { /* a convenience only */ } }
  function showView(v) {
    S.view = v;
    var over = $('#st-over'), items = $('#st-items'), money = $('#st-money'); if (!over || !items) return;
    over.style.display = v === 'overview' ? '' : 'none'; items.style.display = v === 'items' ? '' : 'none'; if (money) money.style.display = v === 'money' ? '' : 'none';
    Array.prototype.forEach.call(S.panel.querySelectorAll('.st-navb'), function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-view') === v ? 'true' : 'false'); });
    if (v === 'overview') { if (!S.ov.data || S.ov.stale) loadOverview(); else renderOverview(); }
    else if (v === 'money') loadMoney();
    else if (!S.itemsLoaded) { S.itemsLoaded = true; load(true); loadCounts(); } else if (S.ov.stale) refresh();
  }
  function loadOverview() {
    var o = S.ov, req = ++o.req; o.loading = true; o.err = null; renderOverview();
    return Promise.all([S.api.overview(o.days), S.api.lanes(), S.api.overviewSeries(o.days).catch(function () { return null; })]).then(function (r) {
      if (req !== o.req) return; o.data = r[0]; o.lanes = r[1]; o.series = r[2]; markMoney(r[2]); o.loading = false; o.stale = false; renderOverview();
    }).catch(function (e) { if (req !== o.req) return; o.loading = false; o.err = e; renderOverview(); });
  }
  function renderOverview() {
    var el = $('#st-over'); if (!el) return;
    var o = S.ov;
    if (o.err && !o.data) { el.innerHTML = '<div class="st-err">' + esc(errMsg(o.err)) + ' <button type="button" class="st-btn st-ghost" data-act="ov-retry">' + esc(T('err.retry')) + '</button></div>'; return; }
    if (!o.data) { el.innerHTML = '<div class="st-skel"></div><div class="st-skel"></div><div class="st-skel"></div>'; return; }
    var v = C.viewOverview(o.data);
    if (v.empty) { el.innerHTML = firstRunHtml(); return; }
    var h = '';
    if (o.err) h += '<div class="st-err">' + esc(errMsg(o.err)) + ' <button type="button" class="st-btn st-ghost" data-act="ov-retry">' + esc(T('err.retry')) + '</button></div>';
    if (S.boot.currency_source === 'default') h += '<p class="st-note">' + esc(T('ov.cur', { cur: S.cur })) + ' <button type="button" class="st-linkb" data-act="settings">' + esc(T('ov.cur.change')) + '</button></p>';
    var oldDays = o.data.old_after_days || S.boot.old_after_days || C.CAPS.oldAfterDefault, pk = perKey(o.days), L = o.lanes || {};
    // Order (review 3 Nov 2026): The numbers first, because profit is what people open Stock for, then Today, Stock now, and the charts last.
    // Holding was dropped the same day: its rule is a subset of List, and the claims mirror never sets src_type, so it repeated List or stayed empty.
    h += numbersHtml(o, v, pk);
    var LANES = [['reprice', [['reprice', 'lane.btn.reprice']], 'listed'], ['list', [['list', 'act.list']], 'stock'], ['follow', [['sold', 'act.sold'], ['active', 'act.active']], 'reserved']];
    var worth = LANES.reduce(function (n, ld) { return n + ((L[ld[0]] && L[ld[0]].count) || 0); }, 0);
    h += '<section class="st-sec" aria-labelledby="st-h-lanes"><div class="st-sechd"><h2 class="st-h2" id="st-h-lanes">' + esc(T('ov.lanes')) + '</h2>' +
      (o.lanes ? '<span class="st-secsub" id="st-lanes-sub">' + esc(T('ov.lanes.sub', { n: worth, date: todayLabel() })) + '</span>' : '') + '</div><div class="st-lanes">' +
      LANES.map(function (ld) {
        var k = ld[0], ln = L[k] || { count: 0, items: [] }, shown = ln.items.slice(0, LANE_ROWS);
        return '<div class="st-lane" id="st-lane-' + k + '"><div class="st-lane-hd"><span>' + esc(T('lane.' + k)) + '</span><b>' + esc(String(ln.count)) + '</b></div><p class="st-d">' + esc(T('lane.' + k + '.d')) + '</p>' +
          (ln.count ? shown.map(function (it) {
            return '<div class="st-lane-row"><button type="button" class="st-lane-it" data-act="lane-open" data-id="' + esc(it.id) + '">' + tileHtml(it.title, it.image_url) + '<span class="st-lane-tx"><span class="t">' + esc(it.title) + '</span><span class="a">' + esc(laneMeta(k, it)) + '</span></span></button>' +
              '<div class="st-lane-acts">' + ld[1].map(function (a, i) { return '<button type="button" class="st-btn ' + (i ? 'st-tert' : 'st-ghost') + '" data-act="lane-act" data-do="' + a[0] + '" data-id="' + esc(it.id) + '">' + esc(T(a[1])) + '</button>'; }).join('') + '</div></div>';
          }).join('') + (ln.count > shown.length ? '<button type="button" class="st-linkb st-lane-more" data-act="lane-more" data-status="' + ld[2] + '">' + esc(T('lane.more', { n: ln.count - shown.length })) + '</button>' : '') : '<p class="st-d st-dim">' + esc(T('lane.' + k + '.none')) + '</p>') + '</div>';
      }).join('') + '</div></section>';
    // Stock now: today's snapshot, not affected by the period
    h += '<section class="st-sec" aria-labelledby="st-h-now"><div class="st-sechd"><h2 class="st-h2" id="st-h-now">' + esc(T('ov.now')) + '</h2><span class="st-secsub">' + esc(T('ov.snapshot')) + '</span></div><div class="st-strip">' +
      '<div class="st-t3"><span class="st-lbl">' + esc(T('ov.t.stock')) + '</span><b class="st-big" id="st-hero-held">' + esc(String(v.held.count)) + '</b><small>' + esc(T('ov.held')) + '</small><small>' + esc(T('ov.split', { a: v.held.inStock, b: v.held.listed, c: v.held.reserved })) + '</small></div>' +
      '<div class="st-t3"><span class="st-lbl">' + esc(T('ov.cash')) + '</span><b class="st-big" id="st-cash">' + esc(M(v.held.cashCents)) + '</b><small>' + esc(T('ov.cash.cap')) + '</small>' + (v.held.noCost ? '<small>' + esc(T('ov.cash.nocost', { n: v.held.noCost })) + '</small>' : '') + '</div>' +
      '<div class="st-t3"><span class="st-lbl">' + esc(T('ov.stale', { d: oldDays })) + '</span><b class="st-big' + (v.held.old ? ' st-warnv' : ' st-dim') + '" id="st-old">' + esc(String(v.held.old)) + '</b>' +
      (v.held.old ? '<small id="st-old-sub">' + esc(T('ov.old.cost', { cost: M(v.held.oldCostCents) })) + '</small><button type="button" class="st-btn st-ghost" data-act="see-old">' + esc(T('ov.old.see')) + '</button>' : '<small id="st-old-sub">' + esc(T('ov.old.none')) + '</small>') + '</div></div></section>';
    var charts = chartsHtml(o);
    if (charts) h += '<section class="st-sec st-chsec" aria-label="' + esc(T('ch.day.title')) + '">' + charts + '</section>';
    el.innerHTML = h;
  }
  // The numbers: hero net profit + delta, revenue / sales / average / days to sell, returns and write-offs; "Fix them" when sales are left out
  function numbersHtml(o, v, pk) {
    var ARROW_UP = String.fromCharCode(0x25b2), ARROW_DN = String.fromCharCode(0x25bc);
    var pct = (v.deltaNetCents != null && v.prevNetCents) ? v.deltaNetCents / Math.abs(v.prevNetCents) : null, dir = v.deltaNetCents == null ? 0 : (v.deltaNetCents > 0 ? 1 : (v.deltaNetCents < 0 ? -1 : 0));
    var pctTxt = pct == null ? null : (pct < 0 ? C.MINUS : '+') + (Math.abs(pct) * 100).toFixed(1).replace('.', lang === 'fr' ? ',' : '.') + (lang === 'fr' ? String.fromCharCode(0xa0) + '%' : '%');
    var deltaP = { amount: v.deltaNetCents == null ? '' : MS(v.deltaNetCents), pct: pctTxt, prev: v.prevNetCents == null ? '' : M(v.prevNetCents), n: o.days };
    return '<section class="st-sec" aria-labelledby="st-h-num"><div class="st-sechd"><h2 class="st-h2" id="st-h-num">' + esc(T('ov.numbers')) + '</h2><span class="st-secsub" id="st-num-sub">' + esc(T('per.' + pk) + (o.days != null ? ' \u00b7 ' + T('ov.vs', { n: o.days }) : '')) + '</span>' +
      '<div class="st-chips" role="group" aria-label="' + esc(T('per.label')) + '">' + PERIODS.map(function (d) { return '<button type="button" class="st-chip" data-act="period" data-days="' + perKey(d) + '" aria-pressed="' + (d === o.days ? 'true' : 'false') + '">' + esc(T('per.btn.' + perKey(d))) + '</button>'; }).join('') + '</div></div>' +
      '<div class="st-numgrid"><div class="st-herocard"><span class="st-lbl">' + esc(T('ov.net') + ' \u00b7 ' + T('per.' + pk)) + '</span>' +
      '<div class="st-heroline"><span class="st-hero' + (v.netCents != null && v.netCents < 0 ? ' st-neg' : '') + '" id="st-hero-net">' + (v.netCents == null ? '<span class="st-miss">--</span>' : esc(M(v.netCents))) + '</span></div>' +
      (o.series && o.series.expenses > 0 && v.netCents != null ? '<p class="st-delta" id="st-after">' + esc(T('ov.after', { exp: M(o.series.expenses), after: MS(v.netCents - o.series.expenses) })) + ' <button type="button" class="st-linkb" data-act="view" data-view="money">' + esc(T('ov.after.link')) + '</button></p>' : '') +
      (v.deltaNetCents != null && o.days != null ? '<p class="st-delta" id="st-delta">' + (dir ? '<span class="' + (dir > 0 ? 'st-pos' : 'st-neg') + '">' + (dir > 0 ? ARROW_UP : ARROW_DN) + '</span> ' : '') + esc(T(pctTxt == null ? 'ov.delta.nopct' : 'ov.delta', deltaP)) + '</p>' : '') +
      (v.hasEvents ? '' : '<p class="st-split">' + esc(T('ov.net.empty')) + '</p>') +
      (v.partial ? '<p class="st-hint" id="st-partial">' + esc(T('ov.partial.note', { a: v.withCost, b: v.sold, c: v.sold - v.withCost })) + ' <button type="button" class="st-linkb" data-act="fix">' + esc(T('fix.btn')) + '</button></p>' : '') + '</div>' +
      cell(T('ov.rev'), v.revenueCents == null ? '--' : M(v.revenueCents), v.sold === 1 ? T('ov.sales.n1') : T('ov.sales.n', { n: v.sold }), 'st-c-rev') +
      cell(T('ov.sold'), String(v.sold), T('per.' + pk), 'st-c-sales') +
      cell(T('ov.avg'), v.avgProfitCents == null ? '--' : M(v.avgProfitCents), v.sold ? T('ov.avg.cap', { a: v.withCost, b: v.sold }) : null, 'st-c-avg') +
      cell(T('ov.days'), v.daysToSell == null ? '--' : T('ov.days.v', { n: Math.round(v.daysToSell) }), T('ov.days.cap'), 'st-c-days') + '</div>' +
      '<div class="st-numsub">' + cell(T('ov.returns'), String(v.returns), null, 'st-c-ret') + cell(T('ov.wo'), String(v.writeOffs), v.writeOffs ? T('ov.wo.cost', { amount: M(v.writeOffCostCents) }) : null, 'st-c-wo') + '</div></section>';
  }
  // the meta line of a lane row (design Bc): Reprice "Depop . 85.00 . listed 90d . 0 price drops", List "in stock 91d . cost 53.40", Follow up "Vinted . 56.00 . reserved 5d".
  // lane_days / platform / price / cost come from migration 069; before it only the age is known and only that is shown.
  function laneMeta(k, it) {
    var d = it.lane_days != null ? it.lane_days : it.days, parts = [];
    var plat = it.platform ? T('plat.' + it.platform) : null, price = it.list_cents != null ? M(it.list_cents) : null;
    if (k === 'reprice') { if (plat) parts.push(plat); if (price) parts.push(price); parts.push(T('lane.meta.listed', { d: d })); if (it.drops != null) parts.push(T('lane.meta.drops', { n: it.drops })); }
    else if (k === 'follow') { if (plat) parts.push(plat); if (price) parts.push(price); parts.push(T('lane.meta.reserved', { d: d })); }
    else { parts.push(T('lane.meta.stock', { d: d })); if (it.cost_cents != null) parts.push(T('lane.meta.cost', { c: M(it.cost_cents) })); }
    return parts.join(' \u00b7 ');
  }
  // ------------------------------------------------------------------ Overview charts (migration 069): net profit per day + by platform, plain SVG / CSS, a Table toggle for each
  function niceMax(v) { if (v <= 0) return 1; var u = Math.pow(10, Math.floor(Math.log(v) / Math.LN10)), c = [1, 2, 2.5, 5, 10], i; for (i = 0; i < c.length; i++) if (c[i] * u >= v) return c[i] * u; return 10 * u; }
  function shortDay(iso) { var p = iso.split('-'); try { return new Intl.DateTimeFormat(lang === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'short' }).format(new Date(+p[0], +p[1] - 1, +p[2])); } catch (e) { return iso; } }
  function chartsHtml(o) {
    var s = o.series; if (!s) return '';
    var pk = perKey(o.days), h = '<div class="st-charts">';
    var pts = [], i, j, bucket = (s.daily.length > 90) ? 7 : 1;
    for (i = 0; i < s.daily.length; i += bucket) { var seg = s.daily.slice(i, i + bucket), n = 0, so = 0; for (j = 0; j < seg.length; j++) { n += seg[j].net; so += seg[j].sold; } pts.push({ d: seg[0].d, net: n, sold: so }); }
    var anySales = s.by_platform.length > 0;
    if (pts.length) {
      var total = pts.reduce(function (a, p) { return a + p.net; }, 0), asTable = !!S.ov.dayTable;
      h += '<section class="st-chart" id="st-ch-day" aria-labelledby="st-h-chd"><div class="st-chart-hd"><h3 class="st-h3" id="st-h-chd">' + esc(T('ch.day.title')) + '</h3><span class="st-secsub">' + esc(T(bucket > 1 ? 'ch.sub.weekly' : 'ch.sub.daily', { period: T('per.btn.' + pk) })) + '</span>' +
        '<button type="button" class="st-btn st-ghost st-tbl" data-act="chart-table" data-which="day" aria-pressed="' + (asTable ? 'true' : 'false') + '">' + esc(T(asTable ? 'ch.chart' : 'ch.table')) + '</button></div>';
      if (!anySales) h += '<p class="st-d st-dim">' + esc(T('ch.none')) + '</p>';
      else if (asTable) h += '<div class="st-tblwrap"><table class="st-ctable"><thead><tr><th>' + esc(T('ch.col.day')) + '</th><th>' + esc(T('ch.col.net')) + '</th><th>' + esc(T('ch.col.sold')) + '</th></tr></thead><tbody>' + pts.filter(function (p) { return p.net !== 0 || p.sold !== 0; }).map(function (p) { return '<tr><td>' + esc(shortDay(p.d)) + '</td><td>' + esc(MS(p.net)) + '</td><td>' + esc(String(p.sold)) + '</td></tr>'; }).join('') + '</tbody></table></div>';
      else h += dayChartSvg(pts, total);
      h += '</section>';
    }
    var by = s.by_platform, asT2 = !!S.ov.platTable, maxAbs = by.reduce(function (m, x) { return Math.max(m, Math.abs(x.net)); }, 1);
    h += '<section class="st-chart" id="st-ch-plat" aria-labelledby="st-h-chp"><div class="st-chart-hd"><h3 class="st-h3" id="st-h-chp">' + esc(T('ch.plat.title')) + '</h3>' +
      '<button type="button" class="st-btn st-ghost st-tbl" data-act="chart-table" data-which="plat" aria-pressed="' + (asT2 ? 'true' : 'false') + '">' + esc(T(asT2 ? 'ch.chart' : 'ch.table')) + '</button></div>';
    if (!by.length) h += '<p class="st-d st-dim">' + esc(T('ch.none')) + '</p>';
    else if (asT2) h += '<div class="st-tblwrap"><table class="st-ctable"><thead><tr><th>' + esc(T('f.platform')) + '</th><th>' + esc(T('ch.col.net')) + '</th><th>' + esc(T('ch.col.sold')) + '</th></tr></thead><tbody>' + by.map(function (x) { return '<tr><td>' + esc(x.platform ? T('plat.' + x.platform) : T('plat.none')) + '</td><td>' + esc(MS(x.net)) + '</td><td>' + esc(String(x.sold)) + '</td></tr>'; }).join('') + '</tbody></table></div>';
    else h += '<ul class="st-pbars">' + by.map(function (x) { var w = Math.max(2, Math.round(Math.abs(x.net) / maxAbs * 100)); return '<li><span class="st-pn">' + esc(x.platform ? T('plat.' + x.platform) : T('plat.none')) + '</span><span class="st-pbar"><i class="' + (x.net < 0 ? 'neg' : 'pos') + '" style="width:' + w + '%"></i></span><span class="st-pv">' + esc(T(x.sold === 1 ? 'ch.plat.row1' : 'ch.plat.row', { amount: M(x.net), n: x.sold })) + '</span></li>'; }).join('') + '</ul>';
    h += '<p class="st-hint">' + esc(T('ch.note')) + '</p></section></div>';
    return h;
  }
  function dayChartSvg(pts, total) {
    var W = 640, H = 200, L = 52, Rr = 8, Tp = 14, B = 24, n = pts.length, pw = W - L - Rr, ph = H - Tp - B;
    var mx = niceMax(Math.max.apply(null, pts.map(function (p) { return p.net; }).concat([0])) / 100) * 100, mnRaw = Math.min.apply(null, pts.map(function (p) { return p.net; }).concat([0])), mn = mnRaw < 0 ? -niceMax(-mnRaw / 100) * 100 : 0;
    var y = function (v) { return Tp + (mx - v) / (mx - mn) * ph; }, bw = Math.max(1, pw / n * 0.7), step = pw / n, svg = '', cum = 0, cumPts = [], cmax = 1, k;
    pts.forEach(function (p) { cum += p.net; cumPts.push(cum); if (cum > cmax) cmax = cum; });
    var ticks = [mn, 0, mx / 2, mx].filter(function (v, i, a) { return a.indexOf(v) === i; });
    ticks.forEach(function (v) { svg += '<line x1="' + L + '" x2="' + (W - Rr) + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '" class="st-gl' + (v === 0 ? ' z' : '') + '"/><text x="' + (L - 6) + '" y="' + (y(v) + 3).toFixed(1) + '" text-anchor="end" class="st-ax">' + esc(C.formatMoney(v, S.cur, lang, { dp: 0 })) + '</text>'; });
    pts.forEach(function (p, i) { var x = L + i * step + (step - bw) / 2, y0 = y(0), y1 = y(p.net), top = Math.min(y0, y1), hh = Math.max(Math.abs(y1 - y0), p.net === 0 ? 0 : 1); if (hh > 0) svg += '<rect x="' + x.toFixed(1) + '" y="' + top.toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + hh.toFixed(1) + '" class="' + (p.net < 0 ? 'st-bn' : 'st-bp') + '"><title>' + esc(shortDay(p.d) + ': ' + MS(p.net)) + '</title></rect>'; });
    if (cmax > 0 && n > 1) { var line = cumPts.map(function (v, i) { return (L + i * step + step / 2).toFixed(1) + ',' + (Tp + (1 - Math.max(v, 0) / cmax) * ph * 0.45).toFixed(1); }).join(' '); svg += '<polyline points="' + line + '" class="st-cumline"/><text x="' + (L + 6) + '" y="' + (Tp + 10) + '" class="st-ax st-cumt">' + esc(T('ch.cum', { amount: M(total) })) + '</text>'; }
    var idx = n <= 1 ? [0] : [0, Math.round((n - 1) / 3), Math.round((n - 1) * 2 / 3), n - 1];
    idx.filter(function (v, i, a) { return a.indexOf(v) === i; }).forEach(function (i) { svg += '<text x="' + (L + i * step + step / 2).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="' + (i === 0 ? 'start' : (i === n - 1 ? 'end' : 'middle')) + '" class="st-ax">' + esc(shortDay(pts[i].d)) + '</text>'; });
    return '<svg class="st-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(T('ch.aria.day', { from: shortDay(pts[0].d), to: shortDay(pts[n - 1].d), amount: M(total) })) + '" preserveAspectRatio="none">' + svg + '</svg>';
  }
  function tileHtml(title, img) {
    var ini = initials(title);
    if (!img || !/^https:\/\/images[0-9]*\.vinted\.net\//.test(img)) return '<span class="st-tile2" aria-hidden="true">' + esc(ini) + '</span>';
    return '<span class="st-tile2 has-ph" aria-hidden="true" data-ini="' + esc(ini) + '"><img class="st-ph" src="' + esc(img) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer"></span>';
  }
  function initials(title) { return String(title || '').replace(/[^A-Za-z0-9]/g, '').slice(0, 2).toUpperCase() || '--'; }
  function todayLabel() {
    var p = today().split('-'), d = new Date(+p[0], +p[1] - 1, +p[2]);
    try { return new Intl.DateTimeFormat(lang === 'fr' ? 'fr-FR' : 'en-GB', { weekday: 'short', day: 'numeric', month: 'short' }).format(d); } catch (e) { return today(); }
  }
  function cell(label, value, sub, id) { return '<div class="st-cell" id="' + id + '"><span class="st-lbl">' + esc(label) + '</span><b>' + esc(value) + '</b>' + (sub ? '<small>' + esc(sub) + '</small>' : '') + '</div>'; }
  var WALL = 'CH RL NI AR LE SI PA ST CA AD SA TN AC BA MO PR DR YE LO HU WO GU RA KA OF SU JO NB CP AS VA DI BU MA TO FI HE KO LA ME NO OB PE QU RI SE TI UM VE WA XO YO ZA AB BE CO DE EL FO GA'.split(' ');
  function firstRunHtml() {
    var persona = S.boot.persona, m = C.freeCapState(S.boot), h;
    if (persona === 'buy') {   // buyers get the light card: one action, and a way to hide the tab
      return '<div class="st-first" id="st-first-light"><h2>' + esc(T('fr.buy.title')) + '</h2><p>' + esc(T('fr.buy.body')) + '</p><div class="st-firstb"><button type="button" class="st-btn st-prim" data-act="add">' + esc(T('fr.add')) + '</button> <button type="button" class="st-btn st-ghost" data-act="hide-tab">' + esc(T('fr.buy.hide')) + '</button></div></div>';
    }
    var tiles = WALL.map(function (s) { return '<span class="st-tile">' + s + '</span>'; }).join('');
    h = '<div class="st-firstwrap"><div class="st-wall" aria-hidden="true">' + tiles + '</div><div class="st-first" id="st-first"><div class="st-kicker">' + esc(T('fr.kicker')) + '</div><h2>' + esc(T('fr.title')) + '</h2><p>' + esc(T('fr.body')) + '</p>' +
      '<div class="st-firstb"><button type="button" class="st-btn st-prim" data-act="import">' + esc(T('fr.import')) + '</button></div>' +
      '<p class="st-hint st-formats">' + esc(T('fr.formats')) + '</p><p class="st-hint"><button type="button" class="st-link" data-act="template">' + esc(T('fr.template')) + '</button></p>' +
      '<div class="st-firstadd"><button type="button" class="st-btn st-ghost" data-act="add">' + esc(T('fr.add')) + '</button><span>' + esc(T('fr.addhint')) + '</span></div>' +
      '<p class="st-hint st-foot">' + esc(m.limited ? T('fr.free', { cap: m.cap }) : T('fr.paid')) + '</p></div></div>';
    if (!persona && !skipped()) {
      h += '<div class="st-pq" id="st-pq" role="group" aria-label="' + esc(T('pq.title')) + '"><span class="st-lbl">' + esc(T('pq.title')) + '</span><div class="st-seg">' +
        C.PERSONAS.map(function (p) { return '<button type="button" class="st-segb" data-act="persona" data-p="' + p + '" aria-pressed="false"><b>' + esc(T('pq.' + p)) + '</b><span>' + esc(T('pq.' + p + '.d')) + '</span></button>'; }).join('') +
        '</div><button type="button" class="st-btn st-tert" data-act="pq-skip">' + esc(T('pq.skip')) + '</button><p class="st-hint">' + esc(T('pq.note')) + '</p></div>';
    }
    return h;
  }
  // ------------------------------------------------------------------ export + template download (step 2)
  function downloadFile(text, name) {
    var url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })), a = document.createElement('a');
    a.href = url; a.download = name; a.rel = 'noopener'; document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }
  function exportItems(btn) {
    if (S.exporting) return; S.exporting = true; if (btn) btn.disabled = true;
    var rows = [], cursor = null, pages = 0;
    function next() {
      return S.api.itemsPage({}, 200, cursor).then(function (p) {
        rows = rows.concat(p.rows || []); pages++;
        if (!p.next_cursor || pages >= 40) return rows; cursor = p.next_cursor; return next();
      });
    }
    showBar(T('exp.busy'), false);
    next().then(function () {
      if (!rows.length) { showBar(T('exp.none'), false); return; }
      var name = 'snypd-stock-' + C.localToday() + '.csv';
      downloadFile(C.exportCsv(rows, { lang: lang, labels: { status: function (k) { return T('status.' + k); }, cond: function (k) { return T('cond.' + k); }, cat: catName, plat: function (k) { return T('plat.' + k); } } }), name);
      showBar(T('exp.done', { n: rows.length, file: name }), false);
    }).catch(function () { showBar(T('exp.err'), false); }).then(function () { S.exporting = false; if (btn) btn.disabled = false; });
  }

  function answerPersona(p) {
    S.api.saveSettings({ persona: p }).then(function () { S.boot.persona = p; renderOverview(); showBar(T('pq.saved', { a: T('pq.' + p) }), false); }).catch(function (e) { showBar(errMsg(e), false); });
  }
  function hideTab() {
    S.api.saveSettings({ tab_hidden: true }).then(function () { S.boot.tab_hidden = true; applyTab(true); }).catch(function (e) { showBar(errMsg(e), false); });
  }
  function applyTab(hidden) { if (window.SNYPD && window.SNYPD.applyStockTab) window.SNYPD.applyStockTab(hidden); }
  function openLane(id) {
    var known = findRow(id);
    var go = function (row) { if (!row) return; if (row.image_url === undefined) row.image_url = laneImage(id); S.pinned[id] = row; S.opener = $('[data-id="' + id + '"]'); openDetail(id); };
    if (known) { go(known); return; }
    S.api.itemById(id).then(go).catch(function (e) { showBar(errMsg(e), false); });
  }
  function laneImage(id) { var L = (S.ov && S.ov.lanes) || {}, hit = null; ['reprice', 'list', 'follow', 'hold'].forEach(function (k) { ((L[k] && L[k].items) || []).forEach(function (it) { if (it.id === id && it.image_url) hit = it.image_url; }); }); return hit; }
  function laneAct(a, id, opener) {
    var go = function (row) { if (!row) return; S.pinned[id] = row; S.opener = opener || null; runDetailAction(a, id); };
    var known = findRow(id);
    if (known) go(known); else S.api.itemById(id).then(function (row) { go(row); }).catch(function (e) { showBar(errMsg(e), false); });
  }
  function currencyName(code) {
    try { return code + ' - ' + new Intl.DisplayNames([lang === 'fr' ? 'fr' : 'en'], { type: 'currency' }).of(code); } catch (e) { return code; }
  }
  function openSettings(opener) {
    S.opener = opener || null; S.sheet = { kind: 'settings', persona: S.boot.persona || null };
    var b = S.boot;
    var body = '<div id="st-sheet-err"></div><div class="st-form">' +
      fld('cur', T('set.currency'), '<select class="st-in" id="sf-cur">' + C.CURRENCIES.map(function (c) { return option(c, currencyName(c), c === S.cur); }).join('') + '</select>', 'full') +
      '<p class="st-hint full">' + esc(T('set.currency.note')) + (b.currency_source === 'default' ? ' ' + esc(T('set.currency.src')) : '') + '</p>' +
      '<div class="st-f full"><span class="st-lbl">' + esc(T('set.persona')) + '</span><div class="st-seg" id="sf-persona">' +
      C.PERSONAS.map(function (p) { return '<button type="button" class="st-segb" data-act="seg" data-p="' + p + '" aria-pressed="' + (S.sheet.persona === p ? 'true' : 'false') + '">' + esc(T('pq.' + p)) + '</button>'; }).join('') + '</div></div>' +
      fld('old', T('set.old'), txt('old', b.old_after_days || C.CAPS.oldAfterDefault, '', ' inputmode="numeric" maxlength="3"')) +
      '<p class="st-hint full">' + esc(T('set.old.hint')) + '</p>' +
      '<div class="st-f full"><label class="st-check"><input type="checkbox" id="sf-tab"' + (b.tab_hidden ? '' : ' checked') + '> ' + esc(T('set.tab')) + '</label><p class="st-hint">' + esc(T('set.tab.hint')) + '</p></div>' +
      '<div class="st-f full" id="sf-weekly-wrap" style="display:none"><label class="st-check"><input type="checkbox" id="sf-weekly" checked> ' + esc(T('set.weekly')) + '</label><p class="st-hint">' + esc(T('set.weekly.hint')) + '</p></div></div>';
    mountSheet(T('set.title'), body, '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('cancel')) + '</button><button type="button" class="st-btn st-prim" data-act="submit" id="st-go">' + esc(T('set.save')) + '</button>');
    var f = $('#sf-cur'); if (f) f.focus();
    S.api.settingsRow().then(function (r) {   // 073; before it the column does not exist and the switch simply stays hidden
      if (!S.sheet || S.sheet.kind !== 'settings') return;
      var on = !r || r.weekly_email !== false, cb = $('#sf-weekly'), w = $('#sf-weekly-wrap'); if (!cb || !w) return;
      cb.checked = on; S.sheet.weekly0 = on; w.style.display = '';
    }).catch(function () { /* no switch */ });
  }
  function saveSettingsSheet() {
    var b = S.boot, patch = {}, cur = $('#sf-cur').value, oldv = ($('#sf-old').value || '').trim();
    if (!/^[0-9]{1,3}$/.test(oldv) || +oldv < 7 || +oldv > 365) { fieldErr('old', T('set.err.old')); return; } fieldErr('old', '');
    if (cur !== S.cur) patch.currency = cur;
    var pers = S.sheet.persona; if (pers && pers !== b.persona) patch.persona = pers;
    if (+oldv !== (b.old_after_days || C.CAPS.oldAfterDefault)) patch.old_after_days = +oldv;
    var hidden = !$('#sf-tab').checked; if (hidden !== !!b.tab_hidden) patch.tab_hidden = hidden;
    var wk = $('#sf-weekly'); if (wk && S.sheet.weekly0 !== undefined && wk.checked !== S.sheet.weekly0) patch.weekly_email = wk.checked;
    if (!Object.keys(patch).length) { closeSheet(); return; }
    var go = $('#st-go'); if (go) go.disabled = true;
    S.api.saveSettings(patch).then(function () {
      closeSheet(); S.ov.stale = true;
      if (patch.tab_hidden !== undefined) applyTab(patch.tab_hidden);
      return reloadKeep().then(function () { showBar(patch.currency ? T('set.cur.saved', { cur: patch.currency }) : (Object.keys(patch).length === 1 && patch.weekly_email !== undefined ? T(patch.weekly_email ? 'set.weekly.on' : 'set.weekly.off') : T('set.saved')), false); });
    }).catch(function (e) { sheetError(e); });
  }

  // ------------------------------------------------------------------ data
  function apiFilters() {
    var f = S.f, o = {};
    if (f.fix) o.status = ['sold']; else if (f.status) o.status = f.status;
    if (f.sort && S.sortOk) o.sort = f.sort;
    if (f.q) o.q = f.q;
    if (f.condition) o.condition = [f.condition];
    if (f.category) o.category = f.category;
    if (f.platform) o.platform = f.platform;
    if (f.deleted) o.deleted = 'only';
    if (f.old) o.old = true;
    o.today = today();
    return o;
  }
  function load(reset) {
    var req = ++S.req; S.loading = true; S.err = null;
    if (reset) { S.rows = []; S.next = null; }
    renderBody();
    return S.api.itemsPage(apiFilters(), S.f.fix ? 200 : 50, reset ? null : S.next).then(function (p) {
      if (req !== S.req) return;
      if (p.rows.length && !('image_url' in p.rows[0]) && S.sortOk) { S.sortOk = false; var so = $('#st-sort'); if (so) so.style.display = 'none'; if (S.f.sort === 'oldest') { S.f.sort = 'newest'; return load(true); } }   // before 071: newest order only
      S.rows = reset ? p.rows : S.rows.concat(p.rows); S.next = p.next_cursor; S.total = p.total; S.loading = false; renderBody();
    }).catch(function (e) { if (req !== S.req) return; S.loading = false; S.err = e; renderBody(); });
  }
  function reloadKeep() {   // after a change: same filters, at least as many rows as were shown
    var req = ++S.req, n = Math.min(200, Math.max(50, S.rows.length));
    return Promise.all([S.api.itemsPage(apiFilters(), n, null), S.api.boot().catch(function () { return null; })]).then(function (r) {
      if (req !== S.req) return;
      S.rows = r[0].rows; S.next = r[0].next_cursor; S.total = r[0].total; if (r[1] && r[1].mode !== 'off') { S.boot = r[1]; S.cur = r[1].currency || S.cur; S.cats = r[1].categories || S.cats; }
      renderMeter(); renderBody(); if (S.itemsLoaded) loadCounts();
      if (S.view === 'overview') loadOverview(); else S.ov.stale = true;
      if (S.view === 'money') loadMoney();
    });
  }
  function refresh() { if (S && S.boot && S.boot.mode !== 'off') reloadKeep().catch(function (e) { console.error('SNYPD Stock refresh failed', e); }); }

  // ------------------------------------------------------------------ list
  function renderBody() {
    var el = $('#st-body'); if (!el) return;
    var cnt = $('#st-count'), del = $('#st-del');
    if (del) { del.setAttribute('aria-pressed', S.f.deleted ? 'true' : 'false'); del.textContent = S.f.deleted ? T('deleted.back') : T('deleted.show'); }
    $('#st-chips').style.display = S.f.deleted ? 'none' : '';
    Array.prototype.forEach.call(S.panel.querySelectorAll('.st-chip'), function (b) { var st = b.getAttribute('data-status'); b.setAttribute('aria-pressed', (!S.f.fix && (st === 'old' ? !!S.f.old : (!S.f.old && ((S.f.status || []).join(',') === (st === 'stock' ? 'stock,returned' : (st === 'held' ? HELD.join(',') : st)) || (!S.f.status && st === ''))))) ? 'true' : 'false'); });
    renderChipCounts();
    if (cnt) cnt.textContent = '';
    var h = '';
    if (S.err) h += '<div class="st-err">' + esc(errMsg(S.err)) + ' <button type="button" class="st-btn st-ghost" data-act="retry">' + esc(T('err.retry')) + '</button></div>';
    if (S.f.deleted) h += '<p class="st-note">' + esc(T('deleted.note', { days: C.CAPS.deletedDays })) + '</p>';
    if (S.f.old) h += '<p class="st-note">' + esc(T('filter.old', { d: (S.boot && S.boot.old_after_days) || C.CAPS.oldAfterDefault })) + ' <button type="button" class="st-linkb" data-act="clear">' + esc(T('clear')) + '</button></p>';
    var rows = S.f.fix ? S.rows.filter(needsFix) : S.rows;
    if (S.f.fix && !S.loading) h += '<p class="st-note" id="st-fixnote">' + esc(rows.length ? T('fix.note', { n: rows.length }) : T('fix.none')) + ' <button type="button" class="st-linkb" data-act="clear">' + esc(T('clear')) + '</button></p>';
    if (S.loading && !S.rows.length) { el.innerHTML = h + '<div class="st-table" role="status" aria-label="' + esc(T('loading')) + '"><div class="st-skel"></div><div class="st-skel"></div><div class="st-skel"></div></div>'; return; }
    if (!rows.length && !S.err) {
      var noItems = !!(S.boot && S.boot.counts && S.boot.counts.items === 0), filtered = !noItems || S.f.q || S.f.condition || S.f.category || S.f.platform || S.f.old;
      if (S.f.fix) { el.innerHTML = h; return; }
      if (S.f.deleted) h += '<div class="st-empty"><p>' + esc(T('empty.deleted', { days: C.CAPS.deletedDays })) + '</p></div>';
      else if (filtered) h += '<div class="st-empty"><p>' + esc(T('empty.filtered')) + '</p><button type="button" class="st-btn st-ghost" data-act="clear">' + esc(T('clear')) + '</button></div>';
      else h += '<div class="st-empty"><h3>' + esc(T('empty.title')) + '</h3><p>' + esc(T('empty.body')) + '</p><button type="button" class="st-btn st-prim" data-act="add">' + esc(T('empty.add')) + '</button> <button type="button" class="st-btn st-ghost" data-act="import">' + esc(T('imp.btn')) + '</button></div>';
      el.innerHTML = h; return;
    }
    h += '<div class="st-table" role="table"><div class="st-th" role="row"><span>' + esc(T('col.item')) + '</span><span>' + esc(T('col.status')) + '</span><span>' + esc(T('col.platform')) + '</span><span class="st-num">' + esc(T('col.bought')) + '</span><span class="st-num">' + esc(T('col.days')) + '</span><span class="st-num">' + esc(T('col.pop')) + '</span></div>';
    var t0 = today();
    rows.forEach(function (r) { h += rowHtml(r, t0); });
    h += '</div>';
    h += '<p class="st-foot2" id="st-showing" aria-live="polite">' + esc(S.f.fix ? (S.next ? T('fix.checked', { n: S.rows.length, total: S.total }) : '') : T('it.showing', { n: S.rows.length, total: S.total })) + '</p>';
    if (S.next) h += '<div class="st-more"><button type="button" class="st-btn st-ghost" data-act="more"' + (S.loading ? ' disabled' : '') + '>' + esc(T('more')) + '</button></div>';
    el.innerHTML = h;
  }
  function needsFix(r) { return r.status === 'sold' && (r.sold_cents == null || r.buy_cents == null); }
  function rowHtml(r, t0) {
    var cost = C.costCents(r), profit = C.saleProfitCents(r), held = C.isHeld({ status: r.status, deleted_at: null });
    var price = r.status === 'sold' ? r.sold_cents : r.list_cents, age = held ? C.ageDays(r, t0) : null;
    var oldAfter = (S.boot && S.boot.old_after_days) || C.CAPS.oldAfterDefault, stale = held && age != null && age >= oldAfter;
    var sub = [r.brand, r.size].filter(Boolean).map(esc).join(' &middot; ');
    var pTxt = profit == null ? '<span class="st-miss">--</span>' : '<span class="' + (profit < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(profit)) + '</span>';
    var pop = r.status === 'sold' ? pTxt : (r.list_cents != null ? esc(M(r.list_cents)) : '<span class="st-miss">--</span>');
    var last = S.f.deleted ? '<button type="button" class="st-btn st-ghost" data-act="restore" data-id="' + esc(r.id) + '">' + esc(T('act.restore')) + '</button>' : esc(r.platform ? T('plat.' + r.platform) : '--');
    return '<div class="st-row" role="row" tabindex="0" data-act="open" data-id="' + esc(r.id) + '">' +
      '<div class="c-item st-itemc">' + tileHtml(r.title, r.image_url) + '<span class="st-item"><b>' + esc(r.title) + '</b>' + (sub ? '<span class="st-sub">' + sub + '</span>' : '') + '</span></div>' +
      '<div class="c-status"><span class="st-tag ' + esc(r.status) + '">' + esc(statusLabel(r.status)) + '</span>' + (stale ? ' <span class="st-tag stale">' + esc(T('tag.stale')) + '</span>' : '') + '</div>' +
      '<div class="c-plat">' + last + '</div><div class="c-cost st-num">' + esc(M(cost)) + '</div>' +
      '<div class="c-age st-num' + (stale ? ' st-warnv' : '') + '">' + (age == null ? '<span class="st-miss">--</span>' : esc(T('age.days', { n: age }))) + '</div><div class="c-pop st-num">' + pop + '</div>' +
      '<div class="c-acts">' + (held ? '<button type="button" class="st-btn st-ghost" data-act="lane-act" data-do="sold" data-id="' + esc(r.id) + '">' + esc(T('act.sold')) + '</button>' : '') + '<button type="button" class="st-btn st-tert" data-act="open" data-id="' + esc(r.id) + '">' + esc(T('act.edit')) + '</button></div>' +
      '<div class="c-meta"><span>' + esc(T('lane.meta.cost', { c: M(cost) })) + '</span><span>' + esc(T(r.status === 'sold' ? 'meta.profit' : 'meta.price', { v: pop.replace(/<[^>]*>/g, '') })) + '</span>' + (age != null ? '<span>' + esc(T('age.days', { n: age })) + '</span>' : '') + '</div></div>';
  }

  // ------------------------------------------------------------------ events
  function onClick(ev) {
    var el = ev.target.closest('[data-act]'); if (!el || !S) return;
    var act = el.getAttribute('data-act'), id = el.getAttribute('data-id');
    if (act === 'restore') { ev.stopPropagation(); doRestore(id); return; }
    if (el.classList.contains('st-btn') || el.classList.contains('st-chip') || el.classList.contains('st-x') || el.tagName === 'BUTTON' || act === 'open' || act === 'scrim') ev.preventDefault();
    switch (act) {
      case 'add': S.opener = el; openSheet('add'); break;
      case 'bundle': openBundle(); break;
      case 'exp-add': S.opener = el; openExpense(); break;
      case 'exp-del': deleteExpense(id); break;
      case 'mo-prev': S.mo.month = monthShift(S.mo.month, -1); loadMoney(); break;
      case 'mo-next': if (S.mo.month < monthStart(today())) { S.mo.month = monthShift(S.mo.month, 1); loadMoney(); } break;
      case 'mo-repeat': repeatLastMonth(el); break;
      case 'mo-csv': exportPnl(); break;
      case 'rp': { var rit = S.sheet && S.sheet.item, rp = parseInt(el.getAttribute('data-pct'), 10), rv = rit ? C.suggestLower(rit.list_cents, rp) : null;
        if (rv != null) { var rf = $('#sf-newprice'); if (rf) rf.value = moneyText(rv); Array.prototype.forEach.call(S.panel.querySelectorAll('[data-act="rp"]'), function (b) { b.setAttribute('aria-pressed', b === el ? 'true' : 'false'); });
          var rh = $('#st-rp-hint'); if (rh) rh.textContent = T('rp.hint', { p: rp }); var re = S.panel.querySelector('.st-fe[data-for="newprice"]'); if (re) re.textContent = ''; }
        break; }
      case 'b-add': bundleAddRow(null, true); break;
      case 'b-del': bundleDelRow(+el.getAttribute('data-i')); break;
      case 'import': S.opener = el; openImport(); break;
      case 'template': downloadFile(C.templateCsv(lang), lang === 'fr' ? 'snypd-modele-revendeur.csv' : 'snypd-reseller-template.csv'); break;
      case 'export': exportItems(el); break;
      case 'im-pick': { var fi = $('#im-file'); if (fi) fi.click(); break; }
      case 'im-go': imRun(false); break;
      case 'im-resume': imRun(true); break;
      case 'im-undo': imUndo(); break;
      case 'im-again': openImport(); break;
      case 'chip': { var st = el.getAttribute('data-status'); S.f.fix = false; S.f.old = st === 'old'; S.f.status = (st === '' || st === 'old') ? null : (st === 'stock' ? ['stock', 'returned'] : (st === 'held' ? HELD.slice() : [st])); load(true); break; }
      case 'deleted': S.f.deleted = !S.f.deleted; S.f.status = null; load(true); break;
      case 'clear': S.f = { status: null, q: '', condition: '', category: '', platform: '', deleted: false, old: false, fix: false }; $('#st-q').value = ''; $('#st-cond').value = ''; $('#st-cat').value = ''; $('#st-plat').value = ''; load(true); break;
      case 'more': load(false); break;
      case 'retry': load(true); break;
      case 'open': S.opener = el; openDetail(id); break;
      case 'close': case 'scrim': closeSheet(); break;
      case 'undo': doUndo(); break;
      case 'qty-': case 'qty+': { var q = $('#sf-quantity'); if (q) { q.value = Math.max(1, Math.min(C.CAPS.quantityPerAdd, (parseInt(q.value, 10) || 1) + (act === 'qty+' ? 1 : -1))); } break; }
      case 'submit': submitSheet(false); break;
      case 'submit-next': submitSheet(true); break;
      case 'submit-noprice': submitSheet(false, true); break;
      case 'do': runDetailAction(el.getAttribute('data-do'), id); break;
      case 'save-detail': saveDetail(id); break;
      case 'view': showView(el.getAttribute('data-view')); break;
      case 'settings': openSettings(el); break;
      case 'seg': { var sg = el.getAttribute('data-p'); S.sheet.persona = sg; Array.prototype.forEach.call(S.panel.querySelectorAll('#sf-persona .st-segb'), function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-p') === sg ? 'true' : 'false'); }); break; }
      case 'period': { var dv = el.getAttribute('data-days'); S.ov.days = dv === 'all' ? null : +dv; loadOverview(); break; }
      case 'ov-retry': loadOverview(); break;
      case 'chart-table': { var wh = el.getAttribute('data-which'); if (wh === 'day') S.ov.dayTable = !S.ov.dayTable; else S.ov.platTable = !S.ov.platTable; renderOverview(); break; }
      case 'see-old': S.f = { status: null, q: '', condition: '', category: '', deleted: false, old: true }; if ($('#st-q')) $('#st-q').value = ''; if ($('#st-cond')) $('#st-cond').value = ''; if ($('#st-cat')) $('#st-cat').value = ''; S.itemsLoaded = true; showView('items'); load(true); break;
      case 'lane-open': openLane(id); break;
      case 'lane-more': { var ls = el.getAttribute('data-status'); goItems({ status: ls === 'stock' ? ['stock', 'returned'] : [ls] }); break; }
      case 'fix': goItems({ status: null, fix: true }); break;
      case 'tools': { var tl = $('#st-tools'), open1 = !tl.classList.contains('open'); tl.classList.toggle('open', open1); el.setAttribute('aria-expanded', open1 ? 'true' : 'false'); break; }
      case 'lane-act': laneAct(el.getAttribute('data-do'), id, el); break;
      case 'persona': answerPersona(el.getAttribute('data-p')); break;
      case 'pq-skip': setSkipped(); renderOverview(); showBar(T('pq.skipped'), false); break;
      case 'hide-tab': hideTab(); break;
      default: break;
    }
  }
  // jump from the Overview to Items with a fresh filter (search and selects cleared)
  function goItems(f) {
    S.f = { status: f.status, q: '', condition: '', category: '', platform: '', deleted: false, old: false, fix: !!f.fix };
    ['#st-q', '#st-cond', '#st-cat', '#st-plat'].forEach(function (s) { var e = $(s); if (e) e.value = ''; });
    S.itemsLoaded = true; showView('items'); load(true); loadCounts();
    var top = $('#st-items'); if (top && top.scrollIntoView) top.scrollIntoView({ block: 'start' });
  }
  function onKey(ev) {
    if (ev.key === 'Enter' && S.sheet && S.sheet.kind === 'bundle' && ev.target.tagName === 'INPUT') { ev.preventDefault(); bundleEnter(ev.target); return; }
    if (ev.key === 'Escape' && S.sheet) { ev.stopPropagation(); if (S.sheet.kind === 'add' && clearAdd()) return; closeSheet(); return; }
    if (ev.key === 'Enter' && ev.target.closest('.st-row') && ev.target.classList.contains('st-row')) { S.opener = ev.target; openDetail(ev.target.getAttribute('data-id')); return; }
    if (ev.key === 'Enter' && S.sheet && S.sheet.kind !== 'detail' && ev.target.tagName === 'INPUT') { ev.preventDefault(); submitSheet(!ev.shiftKey && S.sheet.kind === 'add'); }
    if (ev.key === 'Tab' && S.sheet) trapFocus(ev);
  }
  document.addEventListener('keydown', function (ev) {
    if (!S || !S.undo || !S.panel || S.panel.style.display === 'none') return;
    if ((ev.ctrlKey || ev.metaKey) && (ev.key === 'z' || ev.key === 'Z') && !/INPUT|TEXTAREA|SELECT/.test((ev.target && ev.target.tagName) || '')) { ev.preventDefault(); doUndo(); }
  });
  function trapFocus(ev) {
    var box = $('.st-sheet'); if (!box) return;
    var f = box.querySelectorAll('button:not(:disabled), input:not(:disabled), select, textarea, a[href]'); if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); } else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
  }

  // ------------------------------------------------------------------ undo bar / toast
  function showBar(text, canUndo, undoFn) {
    clearTimeout(S.undoTimer);
    var prev = S.undo && S.undo.canUndo ? S.undo.text : null;
    S.undo = { text: text, canUndo: canUndo, fn: undoFn || null };
    var root = $('#st-undo-root'); if (!root) return;
    root.innerHTML = '<div class="st-undo" role="status"><div class="st-undo-row"><span>' + esc(text) + (prev ? '<small>' + esc(T('undo.prev', { what: prev })) + '</small>' : '') + '</span>' + (canUndo ? '<button type="button" class="st-btn st-tert" data-act="undo">' + esc(T('undo')) + '</button>' : '') + '</div><div class="st-undo-bar"></div></div>';
    S.undoTimer = setTimeout(hideBar, canUndo ? 8000 : 4000);
  }
  function hideBar() { clearTimeout(S.undoTimer); S.undo = null; var root = $('#st-undo-root'); if (root) root.innerHTML = ''; }
  function doUndo() {
    if (!S.undo || !S.undo.canUndo) return;
    if (S.undo.fn) { var fn = S.undo.fn; hideBar(); fn().catch(function (e) { showBar(errMsg(e), false); }); return; }
    S.api.undo().then(function () { hideBar(); return reloadKeep(); }).then(function () { showBar(T('toast.undone'), false); }).catch(function (e) { showBar(errMsg(e), false); reloadKeep().catch(function () {}); });
  }

  // ------------------------------------------------------------------ mutations
  function mutate(fn, label) {
    return fn().then(function (r) { return reloadKeep().then(function () { showBar(label, true); return { ok: true, r: r }; }); }).catch(function (e) { return { ok: false, e: e }; });
  }
  function doRestore(id) {
    mutate(function () { return S.api.restoreItem(id); }, T('toast.restored')).then(function (res) { if (!res.ok) showBar(errMsg(res.e), false); });
  }

  // ------------------------------------------------------------------ sheets
  function openSheet(kind, item) {
    S.sheet = { kind: kind, item: item || null };
    var title = { add: 'sheet.add', list: 'sheet.list', reprice: 'sheet.reprice', sold: 'sheet.sold', returned: 'sheet.returned', wo: 'sheet.wo' }[kind];
    var go = { add: 'sheet.add.go', list: 'sheet.list.go', reprice: 'sheet.reprice.go', sold: 'sheet.sold.go', returned: 'sheet.returned.go', wo: 'sheet.wo.go' }[kind];
    var body = formFor(kind, item);
    var foot = '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('cancel')) + '</button>' +
      (kind === 'add' ? '<button type="button" class="st-btn st-ghost" data-act="submit-next">' + esc(T('sheet.add.next')) + '</button>' : '') + (kind === 'sold' ? '<button type="button" class="st-btn st-ghost" data-act="submit-noprice">' + esc(T('sheet.sold.none')) + '</button>' : '') +
      '<button type="button" class="st-btn ' + (kind === 'wo' ? 'st-danger' : 'st-prim') + '" data-act="submit" id="st-go">' + esc(T(go)) + '</button>';
    mountSheet(T(title) + (item ? (lang === 'fr' ? String.fromCharCode(160) : '') + ': ' + item.title : ''), '<div id="st-sheet-err"></div>' + body, foot);
    var first = $('.st-sheet input:not([type=hidden]), .st-sheet select'); if (first) first.focus();
    if (kind === 'sold') { var upd = function () { previewSold(); }; Array.prototype.forEach.call(S.panel.querySelectorAll('#sf-sold, #sf-ship, #sf-fee'), function (i) { i.addEventListener('input', upd); }); $('#sf-platform').addEventListener('change', upd); upd(); }
    if (kind === 'returned') { var dest = function () { var wo = S.panel.querySelector('input[name=dest]:checked').value === 'wo'; $('#sf-reason-wrap').style.display = wo ? '' : 'none'; }; Array.prototype.forEach.call(S.panel.querySelectorAll('input[name=dest]'), function (i) { i.addEventListener('change', dest); }); dest(); }
  }
  function mountSheet(title, bodyHtml, footHtml) {
    $('#st-ov').innerHTML = '<div class="st-scrim" data-act="scrim"></div><div class="st-sheet" role="dialog" aria-modal="true" aria-label="' + esc(title) + '"><div class="st-sheet-hd"><h2>' + esc(title) + '</h2><button type="button" class="st-x" data-act="close" aria-label="' + esc(T('close')) + '">&times;</button></div><div class="st-sheet-bd">' + bodyHtml + '</div>' + (footHtml ? '<div class="st-sheet-ft">' + footHtml + '</div>' : '') + '</div>';
  }
  // Esc on Quick add clears what was typed first (design Cc: "Esc clears"); it closes only when the form is already empty
  function clearAdd() {
    var ids = ['title', 'brand', 'size', 'buy', 'extra', 'source'], dirty = false;
    ids.forEach(function (n) { var e = $('#sf-' + n); if (e && e.value) { dirty = true; e.value = ''; } });
    if (dirty) { var t = $('#sf-title'); if (t) t.focus(); }
    return dirty;
  }
  function needPanel() {
    var chips = []; for (var i = 0; i < 13; i++) chips.push('<span class="st-mapc">' + esc(T('imp.need.c' + i)) + '</span>');
    return '<div class="st-need"><span class="st-lbl">' + esc(T('imp.need.title')) + '</span><p>' + esc(T('imp.need.body')) + '</p><div class="st-map">' + chips.join('') + '</div><p class="st-hint">' + esc(T('imp.need.priv')) + '</p></div>';
  }
  function closeSheet() {
    S.sheet = null; var ov = $('#st-ov'); if (ov) ov.innerHTML = '';
    if (S.opener && document.body.contains(S.opener)) S.opener.focus();
  }
  function fld(name, label, control, cls) { return '<div class="st-f' + (cls ? ' ' + cls : '') + '"><label for="sf-' + name + '">' + esc(label) + '</label>' + control + '<div class="st-fe" data-for="' + name + '"></div></div>'; }
  function txt(name, val, ph, extra) { return '<input class="st-in" id="sf-' + name + '" name="' + name + '" value="' + esc(val == null ? '' : val) + '"' + (ph ? ' placeholder="' + esc(ph) + '"' : '') + (extra || '') + ' autocomplete="off">'; }
  function mny(name, cents) { return txt(name, moneyText(cents), T('ph.money', { v: moneyExample() }), ' inputmode="decimal"'); }
  function dat(name, val, max) { return '<input class="st-in" type="date" id="sf-' + name + '" name="' + name + '" value="' + esc(val || '') + '"' + (max ? ' max="' + esc(max) + '"' : '') + '>'; }
  function formFor(kind, it) {
    var t0 = today();
    if (kind === 'add') {
      return '<p class="st-hint st-bopen"><button type="button" class="st-linkb" data-act="bundle">' + esc(T('bundle.open')) + '</button></p><div class="st-form">' + fld('title', T('f.title'), txt('title', '', '', ' maxlength="140"'), 'full') + fld('brand', T('f.brand'), txt('brand', '', '', ' maxlength="60"')) + fld('size', T('f.size'), txt('size', '', '', ' maxlength="20"')) +
        fld('condition', T('f.condition'), '<select class="st-in" id="sf-condition">' + condOptions('') + '</select>') + fld('category', T('f.category'), '<select class="st-in" id="sf-category">' + catOptions('') + '</select>') +
        fld('quantity', T('f.quantity'), '<div class="st-qty"><button type="button" data-act="qty-" aria-label="' + esc(T('qty.dec')) + '">-</button><input class="st-in" id="sf-quantity" value="1" inputmode="numeric" maxlength="2"><button type="button" data-act="qty+" aria-label="' + esc(T('qty.inc')) + '">+</button></div>') +
        fld('bought', T('f.bought'), dat('bought', t0, t0)) + fld('buy', T('f.buy'), mny('buy')) + fld('extra', T('f.extra'), mny('extra')) + fld('source', T('f.source'), txt('source', '', T('f.source.ph'), ' maxlength="80"'), 'full') + '</div><p class="st-hint" id="st-addlog" aria-live="polite">' + esc(T('sheet.add.log0')) + '</p><p class="st-hint">' + esc(T('sheet.add.keys')) + '</p><p class="st-hint">' + esc(T('sheet.add.hint')) + '</p>';
    }
    if (kind === 'list') return '<div class="st-form">' + fld('platform', T('f.platform'), '<select class="st-in" id="sf-platform">' + platOptions(it.platform) + '</select>') + fld('list', T('f.list'), mny('list', it.list_cents)) + fld('listed', T('f.listed'), dat('listed', t0, t0)) + '</div>';
    if (kind === 'reprice') {
      var rpc = [5, 10, 20].filter(function (p) { return C.suggestLower(it.list_cents, p) != null; });
      return '<div class="st-form"><div class="st-f full"><span class="st-lbl">' + esc(T('f.list')) + '</span><b>' + esc(M(it.list_cents)) + '</b></div>' + fld('newprice', T('f.newprice'), mny('newprice', C.suggestLower(it.list_cents, 10)), 'full') +
        (rpc.length ? '<div class="st-f full st-rp"><span class="st-lbl">' + esc(T('rp.chips')) + '</span><div class="st-chips st-rpc">' + rpc.map(function (p) { return '<button type="button" class="st-chip" data-act="rp" data-pct="' + p + '" aria-pressed="' + (p === 10) + '">' + esc(T('rp.chip', { p: p })) + '</button>'; }).join('') + '</div>' +
          (rpc.indexOf(10) >= 0 ? '<p class="st-hint" id="st-rp-hint">' + esc(T('rp.hint', { p: 10 })) + '</p>' : '') + '</div>' : '') + '</div>';
    }
    if (kind === 'sold') {
      var plat0 = it.platform || S.lastPlat || 'vinted';
      return '<p class="st-d" id="st-soldctx">' + esc(soldCtx(it)) + '</p><div class="st-form">' + fld('sold', T('f.sold'), mny('sold', it.list_cents), 'full') + fld('soldon', T('f.soldon'), dat('soldon', t0, t0)) + fld('platform', T('f.platform'), '<select class="st-in" id="sf-platform">' + platOptions(plat0) + '</select>') + fld('fee', T('f.fee.sale'), mny('fee'), 'full') + fld('ship', T('f.ship'), mny('ship'), 'full') + '</div><div class="st-prev" id="st-prev" style="margin-top:14px"></div><p class="st-hint" id="st-feenote"></p><p class="st-hint">' + esc(T('sold.formula')) + '</p>';
    }
    if (kind === 'returned') {
      return '<div class="st-form">' + fld('returnedon', T('f.returnedon'), dat('returnedon', t0, t0)) + fld('refund', T('f.refund'), mny('refund', it.sold_cents)) + fld('retship', T('f.retship'), mny('retship'), 'full') +
        '<div class="st-f full"><span class="st-lbl">' + esc(T('f.dest')) + '</span><div class="st-radios"><label><input type="radio" name="dest" value="stock" checked> ' + esc(T('f.dest.stock')) + '</label><label><input type="radio" name="dest" value="wo"> ' + esc(T('f.dest.wo')) + '</label></div></div>' +
        '<div class="st-f full" id="sf-reason-wrap" style="display:none"><label for="sf-reason">' + esc(T('f.reason')) + '</label><select class="st-in" id="sf-reason">' + C.WRITE_OFF_REASONS.map(function (r) { return option(r, T('reason.' + r)); }).join('') + '</select></div></div>';
    }
    if (kind === 'wo') return '<div class="st-form">' + fld('reason', T('f.reason'), '<select class="st-in" id="sf-reason">' + C.WRITE_OFF_REASONS.map(function (r) { return option(r, T('reason.' + r)); }).join('') + '</select>') + fld('date', T('f.date'), dat('date', t0, t0)) + '</div><p class="st-hint">' + esc(T('sheet.wo.note')) + '</p>';
    return '';
  }
  function soldCtx(it) {
    var parts = [], cost = C.costCents(it), MN = String.fromCharCode(0xb7);
    if (it.buy_cents != null) parts.push(T('sold.ctx.bought', { v: M(it.buy_cents) }));
    if (it.extra_cents) parts.push(T('sold.ctx.extra', { v: M(it.extra_cents) }));
    if (it.list_cents != null) parts.push(it.status !== 'listed' && it.status !== 'reserved' ? T('sold.ctx.price', { v: M(it.list_cents) }) : (it.platform ? T('sold.ctx.listed', { v: M(it.list_cents), plat: T('plat.' + it.platform) }) : T('sold.ctx.listed0', { v: M(it.list_cents) })));
    return parts.join(' ' + MN + ' ');
  }
  function previewSold() {
    var it = S.sheet.item, box = $('#st-prev'); if (!box) return;
    var isV = soldOnVinted(), feeIn = $('#sf-fee'), feeWrap = feeIn && feeIn.closest('.st-f'), fee = isV ? { ok: true, cents: null } : C.parseMoneyInput(feeIn ? feeIn.value : '', lang), fc = fee.ok && fee.cents ? fee.cents : 0;
    if (feeWrap) feeWrap.style.display = isV ? 'none' : '';
    var note = $('#st-feenote'); if (note) note.textContent = T(isV ? 'sold.fee.vinted' : (fc ? 'sold.fee.set' : 'sold.nofees'));
    var sold = C.parseMoneyInput(($('#sf-sold') || {}).value, lang), ship = C.parseMoneyInput(($('#sf-ship') || {}).value, lang), cost = C.costCents(it), MI = String.fromCharCode(0x2212);
    if (cost == null) { box.innerHTML = esc(T('preview.nocost')); return; }
    if (!sold.ok || sold.cents == null) { box.innerHTML = esc(T('preview.cost', { cost: M(cost) })); return; }
    var sh = ship.ok && ship.cents ? ship.cents : 0, p = sold.cents - cost - sh - fc, f = [T('prev.f.sold', { v: M(sold.cents) }), T('prev.f.buy', { v: M(it.buy_cents) })];
    if (it.extra_cents) f.push(T('prev.f.extra', { v: M(it.extra_cents) })); if (fc) f.push(T('prev.f.fee', { v: M(fc) })); if (sh) f.push(T('prev.f.ship', { v: M(sh) }));
    box.innerHTML = '<span class="st-lbl">' + esc(T(isV || fc ? 'prev.title2' : 'prev.title')) + '</span><strong class="' + (p < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(p)) + '</strong><small>' + esc(f.join(' ' + MI + ' ')) + '</small>';
  }
  function soldOnVinted() { var p = $('#sf-platform'); return !!p && p.value === 'vinted'; }
  // read helpers: set the inline error and return undefined on failure
  function fieldErr(name, msg) { var e = S.panel.querySelector('.st-fe[data-for="' + name + '"]'), i = S.panel.querySelector('#sf-' + name); if (e) e.textContent = msg || ''; if (i) i.classList.toggle('bad', !!msg); }
  function readMoney(name, required) {
    var el = $('#sf-' + name); var r = C.parseMoneyInput(el ? el.value : '', lang);
    if (!r.ok) { fieldErr(name, r.reason === 'too_many_decimals' ? T('err.too_many_decimals') : T('err.amount', { example: moneyExample() })); return { bad: true }; }
    if (r.empty && required) { fieldErr(name, T('err.required')); return { bad: true }; }
    fieldErr(name, ''); return { cents: r.cents };
  }
  function readDate(name) { var el = $('#sf-' + name), v = el ? el.value : ''; if (!v) { fieldErr(name, T('err.required')); return { bad: true }; } fieldErr(name, ''); return { v: v }; }
  function sheetError(e) { var box = $('#st-sheet-err'); if (box) box.innerHTML = '<div class="st-err">' + esc(errMsg(e)) + (e && e.code === 'stock_free_limit' ? ' <a class="st-link" href="plans.html">' + esc(T('meter.upgrade')) + '</a>' : '') + '</div>'; var go = $('#st-go'); if (go) go.disabled = false; }

  function submitSheet(andNext, noPrice) {
    var sh = S.sheet; if (!sh) return;
    if (sh.kind === 'settings') { saveSettingsSheet(); return; }
    if (sh.kind === 'bundle') { submitBundle(); return; }
    if (sh.kind === 'expense') { submitExpense(); return; }
    var go = $('#st-go'), item = sh.item, run, label, bad = false;
    var box = $('#st-sheet-err'); if (box) box.innerHTML = '';
    if (sh.kind === 'add') {
      var title = ($('#sf-title').value || '').trim();
      if (!title) { fieldErr('title', T('err.required')); $('#sf-title').focus(); return; } fieldErr('title', '');
      var buy = readMoney('buy'), extra = readMoney('extra'), bought = readDate('bought'); if (buy.bad || extra.bad || bought.bad) return;
      var qty = parseInt($('#sf-quantity').value, 10); if (!(qty >= 1 && qty <= C.CAPS.quantityPerAdd)) { qty = 1; $('#sf-quantity').value = '1'; }
      var src = ($('#sf-source').value || '').trim();
      var rec = { title: title, brand: $('#sf-brand').value, size: $('#sf-size').value, condition: $('#sf-condition').value || null, category: $('#sf-category').value || null, buy_cents: buy.cents == null ? null : buy.cents, extra_cents: extra.cents || 0, bought_on: bought.v, src: src || null, src_type: src ? 'place' : null };
      run = function () { return S.api.addItems(rec, qty); }; label = T('toast.added', { n: qty });
    } else if (sh.kind === 'list') {
      var lp = readMoney('list'), ld = readDate('listed'); if (lp.bad || ld.bad) return;
      run = function () { return S.api.setStatus(item.id, 'listed', { platform: $('#sf-platform').value || null, listCents: lp.cents == null ? undefined : lp.cents, on: ld.v }); }; label = T('toast.listed');
    } else if (sh.kind === 'reprice') {
      var np = readMoney('newprice', true); if (np.bad) return;
      if (item.list_cents != null && np.cents >= item.list_cents) { fieldErr('newprice', T('err.reprice')); return; }
      run = function () { return S.api.setStatus(item.id, 'listed', { listCents: np.cents }); }; label = T('toast.repriced');
    } else if (sh.kind === 'sold') {
      var sp = noPrice ? { cents: null } : readMoney('sold', true), sd = readDate('soldon'), sh2 = readMoney('ship'), fe = soldOnVinted() ? { cents: null } : readMoney('fee'); if (sp.bad || sd.bad || sh2.bad || fe.bad) return;
      var splat = $('#sf-platform').value || undefined; if (splat) S.lastPlat = splat;
      run = function () { return S.api.markSold(item.id, { soldCents: sp.cents == null ? null : sp.cents, on: sd.v, platform: splat, feeCents: fe.cents == null ? undefined : fe.cents, shipPaidCents: sh2.cents == null ? undefined : sh2.cents }); }; label = T('toast.sold');
    } else if (sh.kind === 'returned') {
      var rd = readDate('returnedon'), rf = readMoney('refund'), rs = readMoney('retship'); if (rd.bad || rf.bad || rs.bad) return;
      var wo = S.panel.querySelector('input[name=dest]:checked').value === 'wo';
      run = function () { return S.api.markReturned(item.id, { on: rd.v, refundCents: rf.cents == null ? undefined : rf.cents, returnShipCents: rs.cents == null ? undefined : rs.cents, to: wo ? 'written_off' : 'stock', reason: wo ? $('#sf-reason').value : undefined }); }; label = wo ? T('toast.written_off') : T('toast.returned');
    } else if (sh.kind === 'wo') {
      var wd = readDate('date'); if (wd.bad) return;
      run = function () { return S.api.writeOff(item.id, $('#sf-reason').value, wd.v); }; label = T('toast.written_off');
    } else return;
    if (go) go.disabled = true;
    mutate(run, label).then(function (res) {
      if (!res.ok) { sheetError(res.e); return; }
      if (sh.kind === 'add' && andNext) {   // keep brand, category, date and source for the next one
        var lg = $('#st-addlog'); if (lg) lg.textContent = T('sheet.add.log', { t: title }); $('#sf-title').value = ''; $('#sf-buy').value = ''; $('#sf-extra').value = ''; $('#sf-size').value = ''; $('#sf-quantity').value = '1'; if (go) go.disabled = false; $('#sf-title').focus();
      } else closeSheet();
    });
  }

  // ------------------------------------------------------------------ Money (migration 072): one month's expenses + month-by-month P&L
  function monthStart(d) { return d.slice(0, 8) + '01'; }
  function monthShift(d, k) { var y = +d.slice(0, 4), m = +d.slice(5, 7) + k; while (m > 12) { m -= 12; y++; } while (m < 1) { m += 12; y--; } return y + '-' + (m < 10 ? '0' : '') + m + '-01'; }
  function monthEnd(d) { var n = monthShift(d, 1), t = Date.UTC(+n.slice(0, 4), +n.slice(5, 7) - 1, 1) - 86400000, x = new Date(t); return x.getUTCFullYear() + '-' + ('0' + (x.getUTCMonth() + 1)).slice(-2) + '-' + ('0' + x.getUTCDate()).slice(-2); }
  function monthLabel(d, short) { try { return new Intl.DateTimeFormat(lang === 'fr' ? 'fr-FR' : 'en-GB', { month: short ? 'short' : 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, 1))); } catch (e) { return d.slice(0, 7); } }
  function markMoney(series) { if (!series || !('expenses' in series)) return; S.hasMoney = true; var b = $('#st-nav-money'); if (b) b.style.display = ''; }
  function loadMoney() {
    if (!S.mo) S.mo = { month: monthStart(today()), data: null, pnl: null, req: 0 };
    var mo = S.mo, req = ++mo.req; mo.loading = true; mo.err = null; renderMoney();
    return Promise.all([S.api.expensesMonth(mo.month), S.api.pnl(12)]).then(function (r) {
      if (req !== mo.req) return; mo.data = r[0]; mo.pnl = r[1]; mo.loading = false; renderMoney();
    }).catch(function (e) { if (req !== mo.req) return; mo.loading = false; mo.err = e; renderMoney(); });
  }
  function catLabel(k) { return T('xcat.' + k); }
  // the P&L months, newest first, without the empty months before the account's first activity (the current month always stays)
  function pnlRows() {
    var rows = (S.mo && S.mo.pnl && S.mo.pnl.months) || [], last = 0;
    rows.forEach(function (m, i) { if (m.sold || m.revenue || m.item_profit || m.expenses) last = i; });
    return rows.slice(0, last + 1);
  }
  function renderMoney() {
    var el = $('#st-money'); if (!el || !S.mo) return;
    var mo = S.mo, cur = monthStart(today()), ml = monthLabel(mo.month), h = '';
    h += '<section class="st-sec" aria-labelledby="st-h-money"><div class="st-sechd"><h2 class="st-h2" id="st-h-money">' + esc(T('mo.title')) + '</h2><span class="st-secsub">' + esc(T('mo.sub')) + '</span></div>';
    h += '<div class="st-motools"><div class="st-monav"><button type="button" class="st-btn st-ghost" data-act="mo-prev" aria-label="' + esc(T('mo.prev')) + '">&lsaquo;</button><b id="st-mo-month">' + esc(ml) + '</b>' +
      '<button type="button" class="st-btn st-ghost" data-act="mo-next" aria-label="' + esc(T('mo.next')) + '"' + (mo.month >= cur ? ' disabled' : '') + '>&rsaquo;</button></div>' +
      '<div class="st-moacts"><button type="button" class="st-btn st-ghost" data-act="mo-repeat">' + esc(T('mo.repeat')) + '</button><button type="button" class="st-btn st-prim" data-act="exp-add">' + esc(T('mo.add')) + '</button></div></div>';
    if (mo.err) h += '<div class="st-err">' + esc(errMsg(mo.err)) + ' <button type="button" class="st-btn st-ghost" data-act="view" data-view="money">' + esc(T('err.retry')) + '</button></div>';
    if (!mo.data) { el.innerHTML = h + '<div class="st-skel"></div><div class="st-skel"></div></section>'; return; }
    var d = mo.data;
    h += '<div class="st-mosum"><div class="st-cell"><span class="st-lbl">' + esc(T('mo.total', { month: ml })) + '</span><b id="st-mo-total">' + esc(M(d.total)) + '</b>' +
      (d.by_category.length ? '<small>' + esc(d.by_category.map(function (c) { return catLabel(c.category) + ' ' + M(c.total); }).join(' \u00b7 ')) + '</small>' : '') + '</div></div>';
    if (!d.rows.length) h += '<p class="st-d st-dim" id="st-mo-empty">' + esc(T('mo.none', { month: ml })) + '</p>';
    else h += '<div class="st-mlist" role="table" aria-label="' + esc(T('mo.total', { month: ml })) + '">' + d.rows.map(function (r) {
      return '<div class="st-mrow" role="row"><span class="d">' + esc(fmtDate(r.spent_on)) + '</span><span class="c">' + esc(catLabel(r.category)) + '</span><span class="n">' + esc(r.note || '') + '</span><b class="a">' + esc(M(r.amount_cents)) + '</b>' +
        '<button type="button" class="st-x" data-act="exp-del" data-id="' + esc(r.id) + '" aria-label="' + esc(T('mo.del')) + '">&times;</button></div>';
    }).join('') + '</div>';
    h += '</section>';
    // month by month
    var rows = pnlRows();
    h += '<section class="st-sec" aria-labelledby="st-h-pnl"><div class="st-sechd"><h2 class="st-h2" id="st-h-pnl">' + esc(T('mo.pnl')) + '</h2><span class="st-secsub">' + esc(T(rows.length === 1 ? 'mo.pnl.sub1' : 'mo.pnl.sub', { n: rows.length })) + '</span>' +
      '<button type="button" class="st-btn st-ghost" data-act="mo-csv">' + esc(T('mo.export')) + '</button></div>' +
      '<div class="st-tblwrap st-pnlwrap"><table class="st-ctable st-pnl" id="st-pnl"><thead><tr><th>' + esc(T('mo.c.month')) + '</th><th class="st-num">' + esc(T('mo.c.sold')) + '</th><th class="st-num">' + esc(T('mo.c.rev')) + '</th><th class="st-num">' + esc(T('mo.c.item')) + '</th><th class="st-num">' + esc(T('mo.c.exp')) + '</th><th class="st-num">' + esc(T('mo.c.after')) + '</th></tr></thead><tbody>' +
      rows.map(function (m) {
        var quiet = !m.sold && !m.revenue && !m.item_profit && !m.expenses;
        return '<tr' + (quiet ? ' class="st-dim"' : '') + ' data-month="' + esc(m.month) + '"><td>' + esc(monthLabel(m.month + '-01', true)) + '</td><td class="st-num">' + esc(String(m.sold)) + '</td><td class="st-num">' + esc(M(m.revenue)) + '</td><td class="st-num">' + esc(MS(m.item_profit)) + '</td><td class="st-num">' + esc(M(m.expenses)) + '</td><td class="st-num"><b class="' + (m.after < 0 ? 'st-neg' : '') + '">' + esc(MS(m.after)) + '</b></td></tr>';
      }).join('') + '</tbody></table></div>' +
      // phones: one card per month, profit after expenses first (the six-column table does not fit 390 px)
      '<ul class="st-pnlcards" id="st-pnlcards">' + rows.map(function (m) {
        return '<li data-month="' + esc(m.month) + '"><div class="t"><b>' + esc(monthLabel(m.month + '-01')) + '</b><span><small>' + esc(T('mo.c.after')) + '</small> <b class="' + (m.after < 0 ? 'st-neg' : '') + '">' + esc(MS(m.after)) + '</b></span></div>' +
          '<small>' + esc(T('mo.card', { item: MS(m.item_profit), exp: M(m.expenses), sold: m.sold })) + '</small></li>';
      }).join('') + '</ul><p class="st-hint">' + esc(T('mo.pnl.note')) + '</p></section>';
    el.innerHTML = h;
  }
  function openExpense() {
    if (!S.mo) S.mo = { month: monthStart(today()), data: null, pnl: null, req: 0 };
    var t0 = today(), def = S.mo.month === monthStart(t0) ? t0 : monthEnd(S.mo.month);
    S.sheet = { kind: 'expense' };
    var body = '<div id="st-sheet-err"></div><div class="st-form">' + fld('xamount', T('f.exp.amount'), mny('xamount'), 'full') + fld('xdate', T('f.exp.date'), dat('xdate', def, t0)) +
      fld('xcat', T('f.exp.cat'), '<select class="st-in" id="sf-xcat">' + C.EXPENSE_CATEGORIES.map(function (c) { return option(c, catLabel(c), c === 'packaging'); }).join('') + '</select>') +
      fld('xnote', T('f.exp.note'), txt('xnote', '', '', ' maxlength="200"'), 'full') + '</div>';
    mountSheet(T('sheet.exp'), body, '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('cancel')) + '</button><button type="button" class="st-btn st-prim" data-act="submit" id="st-go">' + esc(T('exp.go')) + '</button>');
    var f = $('#sf-xamount'); if (f) f.focus();
  }
  function submitExpense() {
    var am = readMoney('xamount', true), dd = readDate('xdate'); if (am.bad || dd.bad) return;
    if (!(am.cents > 0)) { fieldErr('xamount', T('err.amount', { example: moneyExample() })); return; }
    var row = { spent_on: dd.v, amount_cents: am.cents, category: $('#sf-xcat').value, note: ($('#sf-xnote').value || '').trim() || null }, go = $('#st-go'); if (go) go.disabled = true;
    S.api.addExpenses([row]).then(function () {
      closeSheet(); S.ov.stale = true; S.mo.month = monthStart(row.spent_on);
      return loadMoney().then(function () { showBar(T('toast.exp.added', { amount: M(row.amount_cents) }), false); });
    }).catch(function (e) { sheetError(e); });
  }
  function deleteExpense(id) {
    S.api.deleteExpenses([id]).then(function (r) {
      var back = (r.deleted || []).map(function (x) { return { spent_on: x.spent_on, amount_cents: x.amount_cents, category: x.category, note: x.note }; });
      S.ov.stale = true;
      return loadMoney().then(function () {
        showBar(T('toast.exp.deleted'), true, function () { return S.api.addExpenses(back).then(function () { return loadMoney(); }).then(function () { showBar(T('toast.exp.restored'), false); }); });
      });
    }).catch(function (e) { showBar(errMsg(e), false); });
  }
  function repeatLastMonth(btn) {   // copies the previous month's expenses into the month shown, same day of the month (never after today)
    var to = S.mo.month, from = monthShift(to, -1), t0 = today(), last = monthEnd(to) < t0 ? monthEnd(to) : t0;
    if (btn) btn.disabled = true;
    S.api.expensesMonth(from).then(function (m) {
      if (!m.rows.length) { showBar(T('mo.repeat.none', { month: monthLabel(from) }), false); return; }
      var rows = m.rows.slice(0, 100).map(function (r) { var day = to.slice(0, 8) + r.spent_on.slice(8, 10); if (day > monthEnd(to)) day = monthEnd(to); if (day > last) day = last; return { spent_on: day, amount_cents: r.amount_cents, category: r.category, note: r.note }; });
      return S.api.addExpenses(rows).then(function (res) {
        var ids = res.ids || []; S.ov.stale = true;
        return loadMoney().then(function () {
          showBar(T(ids.length === 1 ? 'mo.repeat.done1' : 'mo.repeat.done', { n: ids.length, month: monthLabel(from) }), true, function () { return S.api.deleteExpenses(ids).then(function () { return loadMoney(); }).then(function () { showBar(T('mo.repeat.undone'), false); }); });
        });
      });
    }).catch(function (e) { showBar(errMsg(e), false); }).then(function () { if (btn) btn.disabled = false; });
  }
  function exportPnl() {   // the table as CSV: FR = semicolon + decimal comma, like the items export
    var rows = pnlRows(), sep = lang === 'fr' ? ';' : ',', q = function (v) { v = String(v); return /[";,\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var lines = [[T('mo.c.month'), T('mo.c.sold'), T('mo.c.rev'), T('mo.c.item'), T('mo.c.exp'), T('mo.c.after')].map(q).join(sep)];
    rows.slice().reverse().forEach(function (m) { lines.push([m.month, m.sold, moneyText(m.revenue), moneyText(m.item_profit), moneyText(m.expenses), moneyText(m.after)].map(q).join(sep)); });
    downloadFile(String.fromCharCode(0xfeff) + lines.join('\r\n') + '\r\n', (lang === 'fr' ? 'snypd-mois-par-mois-' : 'snypd-month-by-month-') + C.localToday() + '.csv');
  }

  // ------------------------------------------------------------------ bundle: several items bought for one price (rows go in as one import, undone as one)
  var BUNDLE_MAX = 50;
  function openBundle() {
    var keep = S.sheet && S.sheet.kind === 'add' ? { src: ($('#sf-source') || {}).value || '', bought: ($('#sf-bought') || {}).value || '' } : { src: '', bought: '' };
    S.sheet = { kind: 'bundle', rows: [0, 1, 2].map(function () { return { title: '', size: '', cost: '' }; }) };
    var t0 = today();
    var body = '<div id="st-sheet-err"></div><div class="st-form">' + fld('btotal', T('bundle.total'), mny('btotal'), 'full') + fld('bought', T('f.bought'), dat('bought', keep.bought || t0, t0)) +
      fld('source', T('f.source'), txt('source', keep.src, T('f.source.ph'), ' maxlength="80"')) +
      fld('condition', T('f.condition'), '<select class="st-in" id="sf-condition">' + condOptions('') + '</select>') + fld('category', T('f.category'), '<select class="st-in" id="sf-category">' + catOptions('') + '</select>') + '</div>' +
      '<div class="st-h3">' + esc(T('bundle.items')) + '</div><div id="b-rows"></div>' +
      '<p><button type="button" class="st-btn st-ghost" data-act="b-add">' + esc(T('bundle.addrow')) + '</button></p>' +
      '<p class="st-note" id="b-sum" aria-live="polite"></p><p class="st-hint">' + esc(T('bundle.hint')) + '</p>';
    mountSheet(T('sheet.bundle'), body, '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('cancel')) + '</button><button type="button" class="st-btn st-prim" data-act="submit" id="st-go">' + esc(T('bundle.go', { n: 3 })) + '</button>');
    renderBundleRows(); $('#sf-btotal').addEventListener('input', bundleUpdate); $('#sf-btotal').focus();
  }
  function bundleRowHtml(r, i) {
    var n = i + 1;
    return '<div class="st-brow" data-i="' + i + '"><input class="st-in b-title" data-i="' + i + '" value="' + esc(r.title) + '" placeholder="' + esc(T('bundle.item.ph', { n: n })) + '" aria-label="' + esc(T('bundle.item.aria', { n: n })) + '" maxlength="140" autocomplete="off">' +
      '<input class="st-in b-size" data-i="' + i + '" value="' + esc(r.size) + '" placeholder="' + esc(T('f.size')) + '" aria-label="' + esc(T('bundle.size.aria', { n: n })) + '" maxlength="20" autocomplete="off">' +
      '<input class="st-in b-cost" data-i="' + i + '" value="' + esc(r.cost) + '" inputmode="decimal" aria-label="' + esc(T('bundle.cost.aria', { n: n })) + '" autocomplete="off">' +
      '<button type="button" class="st-x b-del" data-act="b-del" data-i="' + i + '" aria-label="' + esc(T('bundle.del', { n: n })) + '">&times;</button></div>';
  }
  function renderBundleRows(focusIx) {
    var box = $('#b-rows'); if (!box) return;
    box.innerHTML = S.sheet.rows.map(bundleRowHtml).join('');
    Array.prototype.forEach.call(box.querySelectorAll('input'), function (inp) {
      inp.addEventListener('input', function () { var r = S.sheet.rows[+inp.getAttribute('data-i')]; if (!r) return; r[inp.classList.contains('b-title') ? 'title' : (inp.classList.contains('b-size') ? 'size' : 'cost')] = inp.value; bundleUpdate(); });
      if (inp.classList.contains('b-title')) inp.addEventListener('paste', bundlePaste);
    });
    bundleUpdate();
    if (focusIx != null) { var f = box.querySelector('.b-title[data-i="' + focusIx + '"]'); if (f) f.focus(); }
  }
  function bundleAddRow(after, focus) {
    var rows = S.sheet.rows; if (rows.length >= BUNDLE_MAX) { bundleUpdate(); return; }
    var at = after == null ? rows.length : after + 1; rows.splice(at, 0, { title: '', size: '', cost: '' }); renderBundleRows(focus ? at : null);
  }
  function bundleDelRow(i) { if (S.sheet.rows.length <= 1) return; S.sheet.rows.splice(i, 1); renderBundleRows(Math.min(i, S.sheet.rows.length - 1)); }
  function bundleEnter(t) {   // Enter on a name: next row (a new one after the last); elsewhere: on to the first name
    if (t.classList.contains('b-title')) { var i = +t.getAttribute('data-i'); if (i === S.sheet.rows.length - 1) bundleAddRow(i, true); else { var nx = $('.b-title[data-i="' + (i + 1) + '"]'); if (nx) nx.focus(); } return; }
    var first = $('.b-title[data-i="0"]'); if (first) first.focus();
  }
  function bundlePaste(ev) {   // a pasted list (one item per line) becomes rows, starting at this one
    var txt0 = (ev.clipboardData || window.clipboardData) ? (ev.clipboardData || window.clipboardData).getData('text') : '';
    var lines = String(txt0 || '').split(/\r?\n/).map(function (l) { return l.trim(); }).filter(Boolean);
    if (lines.length < 2) return;
    ev.preventDefault();
    var i = +ev.target.getAttribute('data-i'), rows = S.sheet.rows;
    lines.forEach(function (l, k) { var at = i + k; if (at >= BUNDLE_MAX) return; if (!rows[at]) rows[at] = { title: '', size: '', cost: '' }; rows[at].title = l.slice(0, 140); });
    renderBundleRows(Math.min(i + lines.length, rows.length) - 1);
  }
  // reads the sheet: total, typed costs, the split; writes the cost placeholders and the summary line
  function bundleState() {
    var tot = C.parseMoneyInput(($('#sf-btotal') || {}).value, lang), rows = S.sheet.rows, locked = {}, badCost = [];
    rows.forEach(function (r, i) { if (String(r.cost || '').trim() === '') return; var p = C.parseMoneyInput(r.cost, lang); if (!p.ok || p.cents == null) badCost.push(i); else locked[i] = p.cents; });
    var total = tot.ok && !tot.empty ? tot.cents : null;
    var sp = total == null ? null : C.splitCents(total, rows.length, locked), m = C.freeCapState(S.boot), room = m.limited ? Math.max(m.cap - m.held, 0) : null;
    return { total: total, totalBad: !tot.ok, rows: rows, locked: locked, badCost: badCost, split: sp, room: room, cap: m.cap };
  }
  function bundleUpdate() {
    var st = bundleState(), sum = $('#b-sum'), go = $('#st-go'), n = st.rows.length, msg, bad = true;
    Array.prototype.forEach.call(S.panel.querySelectorAll('#b-rows .b-cost'), function (inp) { var i = +inp.getAttribute('data-i'); inp.placeholder = st.split && st.split.cents[i] != null && st.locked[i] == null ? moneyText(st.split.cents[i]) : moneyExample(); inp.classList.toggle('bad', st.badCost.indexOf(i) >= 0); });
    if (n < 2) msg = T('bundle.min');
    else if (n > BUNDLE_MAX) msg = T('bundle.max', { n: BUNDLE_MAX });
    else if (st.room != null && n > st.room) msg = T('bundle.cap', { cap: st.cap, room: st.room });
    else if (st.totalBad) msg = T('err.amount', { example: moneyExample() });
    else if (st.total == null) msg = T('bundle.need_total');
    else if (st.badCost.length) msg = T('err.amount', { example: moneyExample() });
    else if (!st.split.ok) msg = st.split.reason === 'over' ? T('bundle.over', { total: M(st.total) }) : T('bundle.mismatch', { sum: M(st.total - st.split.rest), total: M(st.total) });
    else { bad = false; msg = Object.keys(st.locked).length ? T('bundle.sum2', { n: n, total: M(st.total) }) : T(st.total % n ? 'bundle.sum.about' : 'bundle.sum', { n: n, each: M(Math.floor(st.total / n)), total: M(st.total) }); }
    if (sum) { sum.textContent = msg; sum.classList.toggle('st-warn', bad); }
    if (go) go.textContent = T('bundle.go', { n: n });
    return !bad;
  }
  function submitBundle() {
    var box = $('#st-sheet-err'); if (box) box.innerHTML = '';
    if (!bundleUpdate()) { var s0 = $('#b-sum'); if (s0) s0.focus && s0.scrollIntoView && s0.scrollIntoView({ block: 'nearest' }); return; }
    var bd = readDate('bought'); if (bd.bad) return;
    var st = bundleState(), src = ($('#sf-source').value || '').trim(), cond = $('#sf-condition').value || null, cat = $('#sf-category').value || null, n = st.rows.length;
    var note = T('bundle.note', { n: n, total: M(st.total), date: fmtDate(bd.v) });
    var rows = st.rows.map(function (r, i) {
      return { title: (r.title || '').trim() || T('bundle.autoname', { src: src || T('bundle.word'), k: i + 1 }), size: (r.size || '').trim() || null, buy_cents: st.split.cents[i], extra_cents: 0,
        bought_on: bd.v, src: src || null, src_type: src ? 'place' : null, condition: cond, category: cat, notes: note };
    });
    var importId = uuid(), go = $('#st-go'); if (go) go.disabled = true;
    S.api.importRows(importId, rows).then(function (r) {
      if (!r || r.rows_inserted !== n || (r.skipped && r.skipped.length)) {   // all or nothing: take back whatever went in
        return S.api.undoImport(importId).catch(function () {}).then(function () { sheetError({ code: r && r.free_limit_hit ? 'stock_free_limit' : 'bundle_partial' }); var b2 = $('#st-sheet-err'); if (b2 && !(r && r.free_limit_hit)) b2.innerHTML = '<div class="st-err">' + esc(T('bundle.partial')) + '</div>'; });
      }
      closeSheet();
      return reloadKeep().then(function () {
        showBar(T('bundle.added', { n: n, total: M(st.total) }), true, function () { return S.api.undoImport(importId).then(function () { return reloadKeep(); }).then(function () { showBar(T('bundle.undone'), false); }); });
      });
    }).catch(function (e) { sheetError(e); });
  }

  // ------------------------------------------------------------------ item detail
  function findRow(id) { return S.rows.filter(function (r) { return r.id === id; })[0] || S.pinned[id]; }
  function actionsFor(it) {
    var a = [];
    if (it.status === 'stock' || it.status === 'returned') a.push('list', 'sold', 'wo');
    else if (it.status === 'listed') a.push('reprice', 'reserve', 'unlist', 'sold', 'wo');
    else if (it.status === 'reserved') a.push('active', 'sold', 'wo');
    else if (it.status === 'sold') a.push('returned');
    a.push('delete'); return a;
  }
  function openDetail(id) {
    var it = findRow(id); if (!it) return;
    S.sheet = { kind: 'detail', item: it };
    var cost = C.costCents(it), profit = C.saleProfitCents(it), held = C.isHeld(it), t0 = today();
    var facts = '<div class="st-facts"><div class="st-fact"><span>' + esc(T('detail.cost')) + '</span><b>' + esc(M(cost)) + '</b></div><div class="st-fact"><span>' + esc(T(it.status === 'sold' ? 'f.sold' : 'f.list')) + '</span><b>' + esc(M(it.status === 'sold' ? it.sold_cents : it.list_cents)) + '</b></div><div class="st-fact"><span>' + esc(T(profit != null ? 'detail.profit' : 'detail.age')) + '</span><b>' + (profit != null ? '<span class="' + (profit < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(profit)) + '</span>' : (held ? esc(T('age.days', { n: C.ageDays(it, t0) })) : '--')) + '</b></div></div>';
    var acts = '<div class="st-acts">' + actionsFor(it).map(function (a) {
      var cls = a === 'delete' ? 'st-btn st-ghost st-danger' : (a === 'sold' ? 'st-btn st-prim' : 'st-btn st-ghost');
      return '<button type="button" class="' + cls + '" data-act="do" data-do="' + a + '" data-id="' + esc(it.id) + '">' + esc(T('act.' + (a === 'wo' ? 'wo' : a))) + '</button>';
    }).join('') + '</div>';
    var form = '<div class="st-h3">' + esc(T('detail.edit')) + '</div><div class="st-form">' +
      fld('title', T('f.title'), txt('title', it.title, '', ' maxlength="140"'), 'full') + fld('brand', T('f.brand'), txt('brand', it.brand, '', ' maxlength="60"')) + fld('size', T('f.size'), txt('size', it.size, '', ' maxlength="20"')) +
      fld('condition', T('f.condition'), '<select class="st-in" id="sf-condition">' + condOptions(it.condition) + '</select>') + fld('category', T('f.category'), '<select class="st-in" id="sf-category">' + catOptions(it.category) + '</select>') +
      fld('buy', T('f.buy'), mny('buy', it.buy_cents)) + fld('extra', T('f.extra'), mny('extra', it.extra_cents)) + fld('bought', T('f.bought'), dat('bought', it.bought_on, t0)) +
      (it.status === 'sold' ? fld('sold', T('f.sold'), mny('sold', it.sold_cents)) + fld('soldon', T('f.soldon'), dat('soldon', it.sold_on, t0)) : fld('list', T('f.list'), mny('list', it.list_cents))) +
      fld('source', T('f.source'), txt('source', it.src === 'SNYPD alert' ? T('src.alert') : it.src, '', ' maxlength="80"' + (it.src === 'SNYPD alert' ? ' disabled' : '')), 'full') +
      fld('link', T('f.link'), txt('link', it.link, '', ' maxlength="500"'), 'full') + fld('notes', T('f.notes'), '<textarea class="st-in" id="sf-notes" rows="3" maxlength="2000" style="height:auto;padding:8px 12px">' + esc(it.notes || '') + '</textarea>', 'full') + '</div>';
    var extra = (it.returned_on ? '<p class="st-note" style="margin-top:12px">' + esc(T('detail.returned', { date: fmtDate(it.returned_on) })) + '</p>' : '') + (it.claim_id ? '<p class="st-note" style="margin-top:12px">' + esc(T('detail.claim')) + '</p>' : '');
    var foot = '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('close')) + '</button><button type="button" class="st-btn st-prim" data-act="save-detail" data-id="' + esc(it.id) + '" id="st-go">' + esc(T('save')) + '</button>';
    var photo = it.image_url && /^https:\/\/images[0-9]*\.vinted\.net\//.test(it.image_url) ? '<div class="st-dphoto" data-ini=""><img class="st-ph" src="' + esc(it.image_url) + '" alt="' + esc(T('detail.photo')) + '" decoding="async" referrerpolicy="no-referrer"></div>' : '';
    mountSheet(it.title, '<div id="st-sheet-err"></div>' + photo + '<span class="st-tag ' + esc(it.status) + '" style="margin-bottom:12px">' + esc(statusLabel(it.status)) + '</span>' + facts + acts + form + extra + '<div class="st-h3">' + esc(T('detail.history')) + '</div><ul class="st-tl" id="st-tl"><li>...</li></ul>', foot);
    S.api.itemHistory(it.id).then(function (h) { if (!S.sheet || S.sheet.item.id !== it.id) return; var ul = $('#st-tl'); if (ul) ul.innerHTML = h.length ? h.map(histHtml).join('') : '<li>' + esc(T('detail.history.none')) + '</li>'; }).catch(function () { var ul = $('#st-tl'); if (ul) ul.innerHTML = '<li>' + esc(T('err.load')) + '</li>'; });
    var f = $('.st-sheet .st-btn'); if (f) f.focus();
  }
  function histHtml(h) {
    var d = h.data || {}, bits = [], plat = d.platform ? T('plat.' + d.platform) : null;
    if (h.kind === 'bought') { if (d.cost_cents != null) bits.push(T('h.cost', { amount: M(d.cost_cents) })); if (d.src) bits.push(d.src === 'SNYPD alert' ? T('src.alert') : d.src); }
    else if (h.kind === 'listed' || h.kind === 'relisted') { if (d.price_cents != null) bits.push(T('h.price', { amount: M(d.price_cents) })); if (plat) bits.push(T('h.via', { platform: plat })); }
    else if (h.kind === 'sale') { if (d.sold_cents != null) bits.push(T('h.sold', { amount: M(d.sold_cents) })); if (plat) bits.push(T('h.via', { platform: plat })); if (d.days != null) bits.push(T('h.days', { n: d.days })); if (d.profit_cents != null) bits.push(T('h.profit', { amount: MS(d.profit_cents) })); }
    else if (h.kind === 'return') { if (d.refund_cents != null) bits.push(T('h.refund', { amount: M(d.refund_cents) })); bits.push(T(d.to === 'written_off' ? 'h.to_wo' : 'h.to_stock')); if (d.profit_cents != null) bits.push('<span class="rev">' + esc(T('h.reversal', { amount: MS(d.profit_cents) })) + '</span>'); }
    else if (h.kind === 'write_off') { if (d.reason) bits.push(T('h.reason', { reason: T('reason.' + d.reason) })); if (d.cost_cents != null) bits.push(T('h.cost', { amount: M(d.cost_cents) })); }
    return '<li class="' + esc(h.kind) + '"><b>' + esc(T('h.' + h.kind)) + '</b><span class="d">' + esc(fmtDate(h.at)) + '</span>' + (bits.length ? bits.map(function (b) { return b.indexOf('<span') === 0 ? b : esc(b); }).join(' &middot; ') : '') + '</li>';
  }
  function runDetailAction(a, id) {
    var it = findRow(id); if (!it) return;
    if (a === 'list' || a === 'reprice' || a === 'sold' || a === 'returned' || a === 'wo') { openSheet(a, it); return; }
    var run, label;
    if (a === 'reserve') { run = function () { return S.api.setStatus(id, 'reserved', { on: today() }); }; label = T('toast.reserved'); }
    else if (a === 'active') { run = function () { return S.api.setStatus(id, 'listed'); }; label = T('toast.active'); }
    else if (a === 'unlist') { run = function () { return S.api.setStatus(id, 'stock'); }; label = T('toast.unlisted'); }
    else if (a === 'delete') { run = function () { return S.api.deleteItem(id); }; label = T('toast.deleted'); }
    else return;
    mutate(run, label).then(function (res) { if (res.ok) closeSheet(); else sheetError(res.e); });
  }
  function saveDetail(id) {
    var it = findRow(id); if (!it) return;
    var patch = {}, bad = false;
    var title = ($('#sf-title').value || '').trim(); if (!title) { fieldErr('title', T('err.required')); return; } fieldErr('title', '');
    if (title !== it.title) patch.title = title;
    [['brand', 'brand'], ['size', 'size'], ['link', 'link']].forEach(function (p) { var v = ($('#sf-' + p[0]).value || '').trim(); if (v !== (it[p[1]] || '')) patch[p[1]] = v; });
    var notes = ($('#sf-notes').value || '').trim(); if (notes !== (it.notes || '')) patch.notes = notes;
    var cond = $('#sf-condition').value || null; if (cond !== (it.condition || null)) patch.condition = cond || '';
    var cat = $('#sf-category').value || null; if (cat !== (it.category || null)) patch.category = cat || '';
    var m = function (name, key, required) { var r = readMoney(name, required); if (r.bad) { bad = true; return; } if ((r.cents == null ? null : r.cents) !== (it[key] == null ? null : it[key])) patch[key] = r.cents == null ? null : r.cents; };
    m('buy', 'buy_cents'); m('extra', 'extra_cents');
    if (it.status === 'sold') m('sold', 'sold_cents'); else m('list', 'list_cents');
    var bd = readDate('bought'); if (bd.bad) bad = true; else if (bd.v !== it.bought_on) patch.bought_on = bd.v;
    if (it.status === 'sold') { var sd = readDate('soldon'); if (sd.bad) bad = true; else if (sd.v !== it.sold_on) patch.sold_on = sd.v; }
    if (it.src !== 'SNYPD alert') { var src = ($('#sf-source').value || '').trim(); if (src !== (it.src || '')) { patch.src = src; patch.src_type = src ? (it.src_type || 'place') : ''; } }
    if (bad) return;
    if (!Object.keys(patch).length) { closeSheet(); return; }
    var go = $('#st-go'); if (go) go.disabled = true;
    S.api.editItem(id, patch).then(function () { return reloadKeep(); }).then(function () { closeSheet(); showBar(T('toast.saved'), false); }).catch(function (e) { sheetError(e); });
  }

  // ------------------------------------------------------------------ import (step 4): file -> review -> batches of 500 -> done / undo this import
  var IM = null;
  function loadImportLib() {
    if (window.SnypdStockImport) return Promise.resolve(window.SnypdStockImport);
    if (!S.importLib) S.importLib = new Promise(function (ok, bad) { var s = document.createElement('script'); s.src = '/assets/stock-import.js'; s.onload = function () { ok(window.SnypdStockImport); }; s.onerror = function () { S.importLib = null; bad(new Error('stock-import.js')); }; document.head.appendChild(s); });
    return S.importLib;
  }
  function freeLeft() { var m = C.freeCapState(S.boot); return m.limited ? Math.max(m.cap - m.held, 0) : null; }
  function uuid() { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); var h = '0123456789abcdef', o = ''; for (var i = 0; i < 36; i++) o += (i === 8 || i === 13 || i === 18 || i === 23) ? '-' : (i === 14 ? '4' : h[Math.floor(Math.random() * 16)]); return o; }
  function openImport() {
    S.sheet = { kind: 'import' };
    IM = { step: 'pick', file: null, sheets: [], sheetIx: 0, dateOrder: null, skipDups: false, condMap: {}, catMap: {}, plan: null, importId: null, done: null, err: null, rpc: [], batches: [], catsFailed: 0 };
    renderImport();
  }
  function imShell(body, foot) {
    var bd = $('.st-sheet-bd'), top = bd ? bd.scrollTop : 0;
    mountSheet(T('imp.title'), '<div id="st-sheet-err"></div>' + body, foot);
    var nb = $('.st-sheet-bd'); if (nb) nb.scrollTop = top;
  }
  function imErrText(e) {
    var c = e && e.code;
    return T(c === 'xls_unsupported' ? 'imp.err.xls' : c === 'not_a_spreadsheet' ? 'imp.err.not' : c === 'encrypted' ? 'imp.err.encrypted' : c === 'too_big' ? 'imp.err.big' : 'imp.err.read');
  }
  function renderImport() {
    if (!S.sheet || S.sheet.kind !== 'import' || !IM) return;
    var close = '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('imp.close')) + '</button>';
    if (IM.step === 'pick' || IM.step === 'reading') {
      imShell((IM.err ? '<div class="st-err">' + esc(IM.err) + '</div>' : '') + '<div class="st-drop" id="im-drop">' + (IM.step === 'reading' ? '<p>' + esc(T('imp.reading')) + '</p>' :
        '<button type="button" class="st-btn st-prim" data-act="im-pick">' + esc(T('imp.pick')) + '</button><p>' + esc(T('imp.drop')) + '</p><p class="st-hint">' + esc(T('imp.formats')) + ' ' + esc(T('imp.limits')) + '</p><p class="st-hint"><button type="button" class="st-link" data-act="template">' + esc(T('fr.template')) + '</button></p>') + needPanel() +
        '<input type="file" id="im-file" accept=".csv,.tsv,.txt,.xlsx" hidden></div>', close);
      var fi = $('#im-file'), dz = $('#im-drop');
      if (fi) fi.onchange = function () { if (fi.files && fi.files[0]) imRead(fi.files[0]); };
      if (dz) { dz.ondragover = function (e) { e.preventDefault(); dz.classList.add('over'); }; dz.ondragleave = function () { dz.classList.remove('over'); }; dz.ondrop = function (e) { e.preventDefault(); dz.classList.remove('over'); if (e.dataTransfer.files && e.dataTransfer.files[0]) imRead(e.dataTransfer.files[0]); }; }
      return;
    }
    if (IM.step === 'review') { imReview(close); return; }
    if (IM.step === 'running') { imShell('<div class="st-prev" id="im-prog" role="status"></div>', ''); imProgress(); return; }
    if (IM.step === 'failed') { imShell('<div class="st-err">' + esc(T('imp.failed', { done: IM.done.items })) + '</div>', close + '<button type="button" class="st-btn st-ghost st-danger" data-act="im-undo">' + esc(T('imp.undo')) + '</button><button type="button" class="st-btn st-prim" data-act="im-resume">' + esc(T('imp.resume')) + '</button>'); return; }
    if (IM.step === 'done') imDone(close);
  }
  function imRead(file) {
    IM.step = 'reading'; IM.err = null; renderImport();
    loadImportLib().then(function (L) { return L.readFile(file).then(function (r) { return [L, r]; }); }).then(function (x) {
      var L = x[0], r = x[1]; IM.file = file; IM.sheets = r.sheets; IM.sheetIx = 0;
      for (var i = 0; i < r.sheets.length; i++) { var rows = r.sheets[i].table.rows.filter(function (row) { return row.some(function (c) { return String(c == null ? '' : c).trim() !== ''; }); }); if (rows.length && L.mapHeaders(rows[0]).some(function (m) { return m.field === 'title'; })) { IM.sheetIx = i; break; } }
      IM.dateOrder = null; IM.skipDups = false; IM.condMap = {}; IM.catMap = {}; imAnalyse(true);
    }).catch(function (e) { IM.step = 'pick'; IM.err = imErrText(e); renderImport(); });
  }
  function imPlan() {
    var L = window.SnypdStockImport, sh = IM.sheets[IM.sheetIx];
    return L.buildPlan(sh.table, { lang: lang, currency: S.cur, categories: S.cats, freeLeft: freeLeft(), today: today(), dateOrder: IM.dateOrder || undefined, skipDuplicates: IM.skipDups, conditionMap: IM.condMap, categoryMap: IM.catMap });
  }
  function imAnalyse(first) {
    IM.plan = imPlan();
    if (IM.plan.errors.length) { IM.step = 'pick'; IM.err = T(IM.plan.errors[0] === 'empty' ? 'imp.err.empty' : 'imp.err.notitle'); renderImport(); return; }
    IM.step = 'review'; renderImport();
  }
  function imReview(close) {
    var L = window.SnypdStockImport, p = IM.plan, st = p.stats, rv = p.review, rpc = L.toRpcRows(p), items = rpc.reduce(function (a, r) { return a + (r.row.quantity || 1); }, 0), h = '';
    var skippedTitle = st.skippedNoTitle, badQty = p.rows.filter(function (r) { return r.bad; }).length;
    h += '<p class="st-note"><b>' + esc(IM.file.name) + '</b>';
    if (IM.sheets.length > 1) h += ' &middot; ' + esc(T('imp.sheet')) + ' <select class="st-in" data-im="sheet" aria-label="' + esc(T('imp.sheet')) + '">' + IM.sheets.map(function (s, i) { return option(String(i), s.name, i === IM.sheetIx); }).join('') + '</select>';
    h += '</p>';
    h += '<div class="st-h3">' + esc(T('imp.cols')) + '</div><div class="st-map">' + p.mapping.map(function (m) { return '<span class="st-mapc ' + (m.field ? 'ok' : 'no') + '">' + esc(m.header || '-') + ' &rarr; ' + esc(m.field ? T('f.' + ({ title: 'title', brand: 'brand', size: 'size', condition: 'condition', category: 'category', quantity: 'quantity', bought: 'bought', buy: 'buy', extra: 'extra', source: 'source', platform: 'platform', list: 'list', sold: 'sold', soldon: 'soldon', fee: 'fee', ship: 'ship', notes: 'notes', link: 'link' }[m.field])) : T('imp.cols.none')) + '</span>'; }).join('') + '</div>';
    h += '<p class="st-note" style="margin-top:12px">' + esc(T('imp.read_as', { cur: S.cur })) + '</p>';
    var notes = [T('imp.sum', { rows: st.rows - skippedTitle - badQty, items: items, held: st.held, sold: st.sold })];
    if (st.qtyRows) notes.push(T('imp.qty', { n: st.qtyRows })); if (st.noBuy) notes.push(T('imp.nobuy', { n: st.noBuy })); if (st.badMoney) notes.push(T('imp.badmoney', { n: st.badMoney }));
    if (st.badDates) notes.push(T('imp.baddates', { n: st.badDates })); if (st.soldNoDate) notes.push(T('imp.sold_nodate', { n: st.soldNoDate }));
    if (skippedTitle) notes.push(T('imp.notitle', { n: skippedTitle })); if (badQty) notes.push(T('imp.badqty', { n: badQty })); if (p.truncated) notes.push(T('imp.trunc', { n: p.truncated }));
    h += '<ul class="st-list">' + notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>';
    if (rv.mixedCurrencies && Object.keys(rv.mixedCurrencies).length) h += '<div class="st-err" style="border-color:rgba(255,176,32,.4);background:rgba(255,176,32,.06)">' + esc(T('imp.mixed', { n: st.mixedCells, cur: S.cur })) + '</div>';
    var d = rv.dateOrder;
    if (d.hasNumericDates && (!d.certain || d.mixed)) h += '<div class="st-h3">' + esc(T('imp.dateorder')) + '</div><div class="st-radios"><label><input type="radio" name="im-order" value="dmy"' + (d.order === 'dmy' ? ' checked' : '') + ' data-im="order"> ' + esc(T('imp.dateorder.dmy')) + '</label><label><input type="radio" name="im-order" value="mdy"' + (d.order === 'mdy' ? ' checked' : '') + ' data-im="order"> ' + esc(T('imp.dateorder.mdy')) + '</label></div>' + (d.mixed ? '<p class="st-hint">' + esc(T('imp.dateorder.mixed')) + '</p>' : '') + (d.sample ? '<p class="st-hint">' + esc(T('imp.dateorder.sample', { s: d.sample })) + '</p>' : '');
    var cu = Object.keys(rv.unrecognisedConditions);
    if (cu.length) h += '<div class="st-h3">' + esc(T('imp.cond')) + '</div>' + cu.map(function (raw) { var key = L.norm(raw); return '<div class="st-f" style="margin-bottom:10px"><label>' + esc(T('imp.cond.row', { raw: raw, n: rv.unrecognisedConditions[raw].length })) + '</label><select class="st-in" data-im="cond" data-key="' + esc(key) + '">' + option('', T('imp.cond.none'), !IM.condMap[key]) + C.CONDITIONS.map(function (c) { return option(c, T('cond.' + c), IM.condMap[key] === c); }).join('') + '</select></div>'; }).join('');
    var cn = Object.keys(rv.newCategories);
    if (cn.length) h += '<div class="st-h3">' + esc(T('imp.cat')) + '</div>' + cn.map(function (name) { var key = L.norm(name); return '<div class="st-f" style="margin-bottom:10px"><label>' + esc(T('imp.cat.row', { name: name, n: rv.newCategories[name].length })) + '</label><select class="st-in" data-im="cat" data-key="' + esc(key) + '">' + option('create', T('imp.cat.create'), IM.catMap[key] !== 'skip') + option('skip', T('imp.cat.skip'), IM.catMap[key] === 'skip') + '</select></div>'; }).join('');
    if (st.duplicates || IM.skipDups) h += '<p class="st-note" style="margin-top:12px">' + esc(T('imp.dups', { n: st.duplicates })) + '</p><label class="st-radios"><span><input type="checkbox" data-im="dups"' + (IM.skipDups ? ' checked' : '') + '> ' + esc(T('imp.dups.skip')) + '</span></label>';
    if (rv.freeCap && rv.freeCap.over > 0) h += '<div class="st-err">' + esc(T('imp.cap', { cap: (S.boot.plan && S.boot.plan.free_cap) || C.CAPS.freeHeld, fits: rv.freeCap.fits, over: rv.freeCap.over })) + ' <a class="st-link" href="plans.html">' + esc(T('imp.cap.link')) + '</a></div>';
    var foot = close + '<button type="button" class="st-btn st-ghost" data-act="im-again">' + esc(T('imp.back')) + '</button><button type="button" class="st-btn st-prim" data-act="im-go" id="st-go"' + (items ? '' : ' disabled') + '>' + esc(items ? T('imp.go', { items: items }) : T('imp.go.none')) + '</button>';
    imShell(h, foot);
  }
  function onChange(ev) {
    var t = ev.target, k = t && t.getAttribute && t.getAttribute('data-im'); if (!k || !IM || IM.step !== 'review') return;
    if (k === 'sheet') { IM.sheetIx = parseInt(t.value, 10) || 0; IM.condMap = {}; IM.catMap = {}; IM.dateOrder = null; }
    else if (k === 'order') IM.dateOrder = t.value;
    else if (k === 'dups') IM.skipDups = !!t.checked;
    else if (k === 'cond') IM.condMap[t.getAttribute('data-key')] = t.value;
    else if (k === 'cat') { var key = t.getAttribute('data-key'); if (t.value === 'skip') IM.catMap[key] = 'skip'; else delete IM.catMap[key]; }
    imAnalyse(false);
  }
  function imProgress() {
    var el = $('#im-prog'); if (!el) return;
    var total = IM.rpc.reduce(function (a, r) { return a + (r.row.quantity || 1); }, 0);
    el.innerHTML = esc(T('imp.running', { done: IM.done.items, total: total })) + '<div class="st-meter-bar" style="margin-top:12px"><div class="st-meter-fill" style="width:' + (total ? Math.round(IM.done.items / total * 100) : 0) + '%"></div></div>';
  }
  function imRun(resume) {
    var L = window.SnypdStockImport;
    var go = $('#st-go'); if (go) go.disabled = true;
    var start;
    if (resume) start = Promise.resolve();
    else {
      IM.importId = uuid(); IM.done = { rows: 0, items: 0, skipped: [], limit: false, cap: false, batchIx: 0 }; IM.catsFailed = 0;
      var cats = IM.plan.review.newCategoryKeys;
      start = (cats.length ? S.api.addCategories(cats) : Promise.resolve()).catch(function (e) {
        IM.catsFailed = cats.length; Object.keys(IM.plan.review.newCategories).forEach(function (n) { IM.catMap[L.norm(n)] = 'skip'; }); IM.plan = imPlan();   // the rows keep going, without those categories
      }).then(function () { IM.rpc = L.toRpcRows(IM.plan); IM.batches = L.batches(IM.rpc); });
    }
    IM.step = 'running'; renderImport();
    start.then(function next() {
      if (IM.done.batchIx >= IM.batches.length) return;
      var b = IM.batches[IM.done.batchIx];
      return S.api.importRows(IM.importId, b.map(function (x) { return x.row; })).then(function (r) {
        IM.done.rows += r.rows_inserted; IM.done.items += r.items_created; IM.done.limit = IM.done.limit || r.free_limit_hit; IM.done.cap = IM.done.cap || r.item_cap_hit;
        (r.skipped || []).forEach(function (s) { IM.done.skipped.push({ n: b[s.index] ? b[s.index].n : '?', reason: s.reason }); });
        IM.done.batchIx++; imProgress(); return next();
      });
    }).then(function () { return reloadKeep(); }).then(function () { IM.step = 'done'; renderImport(); }).catch(function (e) { IM.step = 'failed'; renderImport(); console.error('SNYPD Stock import stopped', e); });
  }
  function skipReason(reason) { var m = /stock_[a-z_]+/.exec(reason || ''); var c = m && m[0]; return T(c === 'stock_title_required' ? 'imp.skip.title_required' : c === 'stock_free_limit' ? 'imp.skip.free_limit' : c === 'stock_item_cap' ? 'imp.skip.item_cap' : 'imp.skip.other'); }
  function imDone(close) {
    var d = IM.done, h = '<div class="st-prev"><strong class="st-pos">' + esc(T('imp.done', { items: d.items })) + '</strong>' + esc(T('imp.done.rows', { rows: d.rows })) + '</div>';
    if (IM.catsFailed) h += '<p class="st-note" style="margin-top:12px">' + esc(T('imp.cat.notcreated', { n: IM.catsFailed })) + '</p>';
    if (d.skipped.length) h += '<div class="st-h3">' + esc(T('imp.done.skipped', { n: d.skipped.length })) + '</div><ul class="st-list">' + d.skipped.slice(0, 20).map(function (s) { return '<li>' + esc(T('imp.skipped.row', { n: s.n, reason: skipReason(s.reason) })) + '</li>'; }).join('') + '</ul>' + (d.skipped.length > 20 ? '<p class="st-hint">...</p>' : '');
    if (d.limit) h += '<div class="st-err">' + esc(T('err.free_limit', { cap: (S.boot.plan && S.boot.plan.free_cap) || C.CAPS.freeHeld })) + ' <a class="st-link" href="plans.html">' + esc(T('meter.upgrade')) + '</a></div>';
    imShell(h, close + '<button type="button" class="st-btn st-ghost" data-act="im-again">' + esc(T('imp.again')) + '</button>' + (d.items ? '<button type="button" class="st-btn st-ghost st-danger" data-act="im-undo">' + esc(T('imp.undo')) + '</button>' : ''));
  }
  function imUndo() {
    if (!IM || !IM.importId) return;
    if (!window.confirm(T('imp.undo.confirm', { n: IM.done ? IM.done.items : 0 }))) return;
    S.api.undoImport(IM.importId).then(function () { return reloadKeep(); }).then(function () { closeSheet(); showBar(T('imp.undone'), false); }).catch(function (e) { sheetError(e); });
  }

  window.SNYPD = window.SNYPD || {};
  window.SNYPD.stock = { open: open, refresh: refresh };
})();
