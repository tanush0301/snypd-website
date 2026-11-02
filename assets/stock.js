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
  function today() { return C.localToday(); }
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
      case 'stock_network': return T('err.network');
      default: return (e && e.kind === 'validation') ? T('err.validation') : T('err.unknown');
    }
  }

  // ------------------------------------------------------------------ open / shell
  function open(opts) {
    if (S && S.panel === opts.panel) { refresh(); return; }
    S = { client: opts.client, panel: opts.panel, api: C.createApi(opts.client, { today: opts.today }), boot: null, cur: 'EUR', cats: [], rows: [], next: null, total: 0,
      f: { status: null, q: '', condition: '', category: '', deleted: false }, loading: true, err: null, req: 0, undo: null, undoTimer: null, sheet: null, opener: null, searchTimer: null };
    S.panel.setAttribute('data-i18n-skip', '');
    S.panel.innerHTML = '<div class="st-wrap"><div class="st-skel"></div><div class="st-skel"></div><div class="st-skel"></div></div>';
    S.api.boot().then(function (b) {
      S.boot = b;
      if (b.mode === 'off') { S.panel.innerHTML = '<div class="st-wrap"><div class="st-err">' + esc(T('err.disabled')) + '</div></div>'; return; }
      S.cur = b.currency || 'EUR'; S.cats = b.categories || [];
      shell(); load(true);
    }).catch(function (e) { S.panel.innerHTML = '<div class="st-wrap"><div class="st-err">' + esc(T('err.load')) + ' <button class="st-btn st-ghost" data-act="reopen">' + esc(T('err.retry')) + '</button></div></div>'; S.panel.onclick = function (ev) { if (ev.target.closest('[data-act="reopen"]')) { var p = S.panel, c = S.client; S = null; open({ client: c, panel: p }); } }; console.error('SNYPD Stock boot failed', e); });
  }
  function shell() {
    var statuses = [['', T('all')], ['stock', T('status.stock')], ['listed', T('status.listed')], ['reserved', T('status.reserved')], ['sold', T('status.sold')], ['returned', T('status.returned')], ['written_off', T('status.written_off')]];
    S.panel.innerHTML =
      '<div class="st-wrap">' +
      '<div class="st-head"><h1 class="st-title">' + esc(T('title')) + '</h1><button type="button" class="st-btn st-prim" data-act="add">' + esc(T('add')) + '</button></div>' +
      '<div id="st-meter"></div>' +
      '<div class="st-tools">' +
      '<input class="st-in st-search" type="search" id="st-q" placeholder="' + esc(T('search')) + '" aria-label="' + esc(T('search.aria')) + '" autocomplete="off">' +
      '<select class="st-in" id="st-cond" aria-label="' + esc(T('filter.condition')) + '">' + option('', T('filter.condition') + ': ' + T('filter.any'), true) + C.CONDITIONS.map(function (c) { return option(c, T('cond.' + c)); }).join('') + '</select>' +
      '<select class="st-in" id="st-cat" aria-label="' + esc(T('filter.category')) + '">' + option('', T('filter.category') + ': ' + T('filter.any'), true) + (S.cats || []).filter(function (c) { return !c.hidden; }).map(function (c) { return option(c.key, catName(c.key)); }).join('') + '</select>' +
      '<button type="button" class="st-btn st-tert" data-act="deleted" id="st-del" aria-pressed="false">' + esc(T('deleted.show')) + '</button>' +
      '<span class="st-count" id="st-count" aria-live="polite"></span></div>' +
      '<div class="st-chips" id="st-chips" role="group" aria-label="' + esc(T('filter.status')) + '">' + statuses.map(function (s) { return '<button type="button" class="st-chip" data-act="chip" data-status="' + s[0] + '" aria-pressed="' + (s[0] === '' ? 'true' : 'false') + '">' + esc(s[1]) + '</button>'; }).join('') + '</div>' +
      '<div id="st-body"></div></div><div id="st-ov"></div><div id="st-undo-root"></div>';
    S.panel.onclick = onClick; S.panel.onkeydown = onKey;
    $('#st-q').oninput = function () { clearTimeout(S.searchTimer); var v = this.value; S.searchTimer = setTimeout(function () { S.f.q = v.trim(); load(true); }, 250); };
    $('#st-cond').onchange = function () { S.f.condition = this.value; load(true); };
    $('#st-cat').onchange = function () { S.f.category = this.value; load(true); };
    renderMeter();
  }
  function renderMeter() {
    var el = $('#st-meter'); if (!el) return;
    var m = C.freeCapState(S.boot);
    if (!m.limited) { el.innerHTML = ''; return; }
    el.innerHTML = '<div class="st-meter' + (m.warn ? ' warn' : '') + '"><div class="st-meter-txt">' + esc(T('meter', { held: m.held, cap: m.cap })) + '</div><div class="st-meter-bar"><div class="st-meter-fill" style="width:' + Math.min(100, Math.round(m.held / m.cap * 100)) + '%"></div></div>' +
      (m.atCap ? '<p>' + esc(T('meter.limit', { cap: m.cap })) + ' <a class="st-link" href="plans.html">' + esc(T('meter.upgrade')) + '</a></p>' : '') + '</div>';
  }

  // ------------------------------------------------------------------ data
  function apiFilters() {
    var f = S.f, o = {};
    if (f.status) o.status = f.status;
    if (f.q) o.q = f.q;
    if (f.condition) o.condition = [f.condition];
    if (f.category) o.category = f.category;
    if (f.deleted) o.deleted = 'only';
    o.today = today();
    return o;
  }
  function load(reset) {
    var req = ++S.req; S.loading = true; S.err = null;
    if (reset) { S.rows = []; S.next = null; }
    renderBody();
    return S.api.itemsPage(apiFilters(), 50, reset ? null : S.next).then(function (p) {
      if (req !== S.req) return;
      S.rows = reset ? p.rows : S.rows.concat(p.rows); S.next = p.next_cursor; S.total = p.total; S.loading = false; renderBody();
    }).catch(function (e) { if (req !== S.req) return; S.loading = false; S.err = e; renderBody(); });
  }
  function reloadKeep() {   // after a change: same filters, at least as many rows as were shown
    var req = ++S.req, n = Math.min(200, Math.max(50, S.rows.length));
    return Promise.all([S.api.itemsPage(apiFilters(), n, null), S.api.boot().catch(function () { return null; })]).then(function (r) {
      if (req !== S.req) return;
      S.rows = r[0].rows; S.next = r[0].next_cursor; S.total = r[0].total; if (r[1] && r[1].mode !== 'off') { S.boot = r[1]; S.cats = r[1].categories || S.cats; }
      renderMeter(); renderBody();
    });
  }
  function refresh() { if (S && S.boot && S.boot.mode !== 'off') reloadKeep().catch(function (e) { console.error('SNYPD Stock refresh failed', e); }); }

  // ------------------------------------------------------------------ list
  function renderBody() {
    var el = $('#st-body'); if (!el) return;
    var cnt = $('#st-count'), del = $('#st-del');
    if (del) { del.setAttribute('aria-pressed', S.f.deleted ? 'true' : 'false'); del.textContent = S.f.deleted ? T('deleted.back') : T('deleted.show'); }
    $('#st-chips').style.display = S.f.deleted ? 'none' : '';
    Array.prototype.forEach.call(S.panel.querySelectorAll('.st-chip'), function (b) { var st = b.getAttribute('data-status'); b.setAttribute('aria-pressed', ((S.f.status || []).join(',') === (st === 'stock' ? 'stock,returned' : st) || (!S.f.status && st === '')) ? 'true' : 'false'); });
    if (cnt) cnt.textContent = S.loading || S.err ? '' : T('shown', { n: S.rows.length, total: S.total });
    var h = '';
    if (S.err) h += '<div class="st-err">' + esc(errMsg(S.err)) + ' <button type="button" class="st-btn st-ghost" data-act="retry">' + esc(T('err.retry')) + '</button></div>';
    if (S.f.deleted) h += '<p class="st-note">' + esc(T('deleted.note', { days: C.CAPS.deletedDays })) + '</p>';
    if (S.loading && !S.rows.length) { el.innerHTML = h + '<div class="st-table" role="status" aria-label="' + esc(T('loading')) + '"><div class="st-skel"></div><div class="st-skel"></div><div class="st-skel"></div></div>'; return; }
    if (!S.rows.length && !S.err) {
      var filtered = S.f.status || S.f.q || S.f.condition || S.f.category;
      if (S.f.deleted) h += '<div class="st-empty"><p>' + esc(T('empty.deleted', { days: C.CAPS.deletedDays })) + '</p></div>';
      else if (filtered) h += '<div class="st-empty"><p>' + esc(T('empty.filtered')) + '</p><button type="button" class="st-btn st-ghost" data-act="clear">' + esc(T('clear')) + '</button></div>';
      else h += '<div class="st-empty"><h3>' + esc(T('empty.title')) + '</h3><p>' + esc(T('empty.body')) + '</p><button type="button" class="st-btn st-prim" data-act="add">' + esc(T('empty.add')) + '</button></div>';
      el.innerHTML = h; return;
    }
    h += '<div class="st-table" role="table"><div class="st-th" role="row"><span>' + esc(T('col.item')) + '</span><span>' + esc(T('col.status')) + '</span><span class="st-num">' + esc(T('col.cost')) + '</span><span class="st-num">' + esc(T('col.price')) + '</span><span class="st-num">' + esc(T('col.profit')) + '</span><span class="st-num">' + esc(T('col.age')) + '</span><span>' + esc(T('col.platform')) + '</span></div>';
    var t0 = today();
    S.rows.forEach(function (r) { h += rowHtml(r, t0); });
    h += '</div>';
    if (S.next) h += '<div class="st-more"><button type="button" class="st-btn st-ghost" data-act="more"' + (S.loading ? ' disabled' : '') + '>' + esc(T('more')) + '</button></div>';
    el.innerHTML = h;
  }
  function rowHtml(r, t0) {
    var cost = C.costCents(r), profit = C.saleProfitCents(r), held = C.isHeld({ status: r.status, deleted_at: null });
    var price = r.status === 'sold' ? r.sold_cents : r.list_cents, age = held ? C.ageDays(r, t0) : null;
    var sub = [r.brand, r.size].filter(Boolean).map(esc).join(' &middot; ');
    var pTxt = profit == null ? '<span class="st-miss">--</span>' : '<span class="' + (profit < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(profit)) + '</span>';
    var last = S.f.deleted ? '<button type="button" class="st-btn st-ghost" data-act="restore" data-id="' + esc(r.id) + '">' + esc(T('act.restore')) + '</button>' : esc(r.platform ? T('plat.' + r.platform) : '--');
    return '<div class="st-row" role="row" tabindex="0" data-act="open" data-id="' + esc(r.id) + '">' +
      '<div class="c-item st-item"><b>' + esc(r.title) + '</b>' + (sub ? '<span class="st-sub">' + sub + '</span>' : '') + '</div>' +
      '<div class="c-status"><span class="st-tag ' + esc(r.status) + '">' + esc(statusLabel(r.status)) + '</span></div>' +
      '<div class="c-cost st-num">' + esc(M(cost)) + '</div><div class="c-price st-num">' + esc(M(price)) + '</div><div class="c-profit st-num">' + pTxt + '</div>' +
      '<div class="c-age st-num">' + (age == null ? '<span class="st-miss">--</span>' : esc(T('age.days', { n: age }))) + '</div><div class="c-plat">' + last + '</div>' +
      '<div class="c-meta"><span>' + esc(M(cost)) + '</span><span>' + esc(M(price)) + '</span>' + (profit != null ? '<span class="' + (profit < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(profit)) + '</span>' : '') + (age != null ? '<span>' + esc(T('age.days', { n: age })) + '</span>' : '') + '</div></div>';
  }

  // ------------------------------------------------------------------ events
  function onClick(ev) {
    var el = ev.target.closest('[data-act]'); if (!el || !S) return;
    var act = el.getAttribute('data-act'), id = el.getAttribute('data-id');
    if (act === 'restore') { ev.stopPropagation(); doRestore(id); return; }
    if (el.classList.contains('st-btn') || el.classList.contains('st-chip') || el.classList.contains('st-x') || el.tagName === 'BUTTON' || act === 'open' || act === 'scrim') ev.preventDefault();
    switch (act) {
      case 'add': S.opener = el; openSheet('add'); break;
      case 'chip': { var st = el.getAttribute('data-status'); S.f.status = st === '' ? null : (st === 'stock' ? ['stock', 'returned'] : [st]); load(true); break; }
      case 'deleted': S.f.deleted = !S.f.deleted; S.f.status = null; load(true); break;
      case 'clear': S.f = { status: null, q: '', condition: '', category: '', deleted: false }; $('#st-q').value = ''; $('#st-cond').value = ''; $('#st-cat').value = ''; load(true); break;
      case 'more': load(false); break;
      case 'retry': load(true); break;
      case 'open': S.opener = el; openDetail(id); break;
      case 'close': case 'scrim': closeSheet(); break;
      case 'undo': doUndo(); break;
      case 'qty-': case 'qty+': { var q = $('#sf-quantity'); if (q) { q.value = Math.max(1, Math.min(C.CAPS.quantityPerAdd, (parseInt(q.value, 10) || 1) + (act === 'qty+' ? 1 : -1))); } break; }
      case 'submit': submitSheet(false); break;
      case 'submit-next': submitSheet(true); break;
      case 'do': runDetailAction(el.getAttribute('data-do'), id); break;
      case 'save-detail': saveDetail(id); break;
      default: break;
    }
  }
  function onKey(ev) {
    if (ev.key === 'Escape' && S.sheet) { ev.stopPropagation(); closeSheet(); return; }
    if (ev.key === 'Enter' && ev.target.closest('.st-row') && ev.target.classList.contains('st-row')) { S.opener = ev.target; openDetail(ev.target.getAttribute('data-id')); return; }
    if (ev.key === 'Enter' && S.sheet && S.sheet.kind !== 'detail' && ev.target.tagName === 'INPUT') { ev.preventDefault(); submitSheet(ev.shiftKey && S.sheet.kind === 'add'); }
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
  function showBar(text, canUndo) {
    clearTimeout(S.undoTimer);
    var prev = S.undo && S.undo.canUndo ? S.undo.text : null;
    S.undo = { text: text, canUndo: canUndo };
    var root = $('#st-undo-root'); if (!root) return;
    root.innerHTML = '<div class="st-undo" role="status"><div class="st-undo-row"><span>' + esc(text) + (prev ? '<small>' + esc(T('undo.prev', { what: prev })) + '</small>' : '') + '</span>' + (canUndo ? '<button type="button" class="st-btn st-tert" data-act="undo">' + esc(T('undo')) + '</button>' : '') + '</div><div class="st-undo-bar"></div></div>';
    S.undoTimer = setTimeout(hideBar, canUndo ? 8000 : 4000);
  }
  function hideBar() { clearTimeout(S.undoTimer); S.undo = null; var root = $('#st-undo-root'); if (root) root.innerHTML = ''; }
  function doUndo() {
    if (!S.undo || !S.undo.canUndo) return;
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
      (kind === 'add' ? '<button type="button" class="st-btn st-ghost" data-act="submit-next">' + esc(T('sheet.add.next')) + '</button>' : '') +
      '<button type="button" class="st-btn ' + (kind === 'wo' ? 'st-danger' : 'st-prim') + '" data-act="submit" id="st-go">' + esc(T(go)) + '</button>';
    mountSheet(T(title) + (item ? ': ' + item.title : ''), '<div id="st-sheet-err"></div>' + body, foot);
    var first = $('.st-sheet input:not([type=hidden]), .st-sheet select'); if (first) first.focus();
    if (kind === 'sold') { var upd = function () { previewSold(); }; Array.prototype.forEach.call(S.panel.querySelectorAll('#sf-sold, #sf-ship'), function (i) { i.addEventListener('input', upd); }); upd(); }
    if (kind === 'returned') { var dest = function () { var wo = S.panel.querySelector('input[name=dest]:checked').value === 'wo'; $('#sf-reason-wrap').style.display = wo ? '' : 'none'; }; Array.prototype.forEach.call(S.panel.querySelectorAll('input[name=dest]'), function (i) { i.addEventListener('change', dest); }); dest(); }
  }
  function mountSheet(title, bodyHtml, footHtml) {
    $('#st-ov').innerHTML = '<div class="st-scrim" data-act="scrim"></div><div class="st-sheet" role="dialog" aria-modal="true" aria-label="' + esc(title) + '"><div class="st-sheet-hd"><h2>' + esc(title) + '</h2><button type="button" class="st-x" data-act="close" aria-label="' + esc(T('close')) + '">&times;</button></div><div class="st-sheet-bd">' + bodyHtml + '</div>' + (footHtml ? '<div class="st-sheet-ft">' + footHtml + '</div>' : '') + '</div>';
  }
  function closeSheet() {
    S.sheet = null; var ov = $('#st-ov'); if (ov) ov.innerHTML = '';
    if (S.opener && document.body.contains(S.opener)) S.opener.focus();
  }
  function fld(name, label, control, cls) { return '<div class="st-f' + (cls ? ' ' + cls : '') + '"><label for="sf-' + name + '">' + esc(label) + '</label>' + control + '<div class="st-fe" data-for="' + name + '"></div></div>'; }
  function txt(name, val, ph, extra) { return '<input class="st-in" id="sf-' + name + '" name="' + name + '" value="' + esc(val == null ? '' : val) + '"' + (ph ? ' placeholder="' + esc(ph) + '"' : '') + (extra || '') + ' autocomplete="off">'; }
  function mny(name, cents) { return txt(name, moneyText(cents), moneyExample(), ' inputmode="decimal"'); }
  function dat(name, val, max) { return '<input class="st-in" type="date" id="sf-' + name + '" name="' + name + '" value="' + esc(val || '') + '"' + (max ? ' max="' + esc(max) + '"' : '') + '>'; }
  function formFor(kind, it) {
    var t0 = today();
    if (kind === 'add') {
      return '<div class="st-form">' + fld('title', T('f.title'), txt('title', '', '', ' maxlength="140"'), 'full') + fld('brand', T('f.brand'), txt('brand', '', '', ' maxlength="60"')) + fld('size', T('f.size'), txt('size', '', '', ' maxlength="20"')) +
        fld('condition', T('f.condition'), '<select class="st-in" id="sf-condition">' + condOptions('') + '</select>') + fld('category', T('f.category'), '<select class="st-in" id="sf-category">' + catOptions('') + '</select>') +
        fld('quantity', T('f.quantity'), '<div class="st-qty"><button type="button" data-act="qty-" aria-label="' + esc(T('qty.dec')) + '">-</button><input class="st-in" id="sf-quantity" value="1" inputmode="numeric" maxlength="2"><button type="button" data-act="qty+" aria-label="' + esc(T('qty.inc')) + '">+</button></div>') +
        fld('bought', T('f.bought'), dat('bought', t0, t0)) + fld('buy', T('f.buy'), mny('buy')) + fld('extra', T('f.extra'), mny('extra')) + fld('source', T('f.source'), txt('source', '', T('f.source.ph'), ' maxlength="80"'), 'full') + '</div><p class="st-hint">' + esc(T('sheet.add.hint')) + '</p>';
    }
    if (kind === 'list') return '<div class="st-form">' + fld('platform', T('f.platform'), '<select class="st-in" id="sf-platform">' + platOptions(it.platform) + '</select>') + fld('list', T('f.list'), mny('list', it.list_cents)) + fld('listed', T('f.listed'), dat('listed', t0, t0)) + '</div>';
    if (kind === 'reprice') return '<div class="st-form"><div class="st-f full"><span class="st-lbl">' + esc(T('f.list')) + '</span><b>' + esc(M(it.list_cents)) + '</b></div>' + fld('newprice', T('f.newprice'), mny('newprice'), 'full') + '</div>';
    if (kind === 'sold') {
      return '<div class="st-form">' + fld('sold', T('f.sold'), mny('sold', it.list_cents), 'full') + fld('soldon', T('f.soldon'), dat('soldon', t0, t0)) + fld('platform', T('f.platform'), '<select class="st-in" id="sf-platform">' + platOptions(it.platform) + '</select>') + fld('ship', T('f.ship'), mny('ship'), 'full') + '</div><div class="st-prev" id="st-prev" style="margin-top:14px"></div>';
    }
    if (kind === 'returned') {
      return '<div class="st-form">' + fld('returnedon', T('f.returnedon'), dat('returnedon', t0, t0)) + fld('refund', T('f.refund'), mny('refund', it.sold_cents)) + fld('retship', T('f.retship'), mny('retship'), 'full') +
        '<div class="st-f full"><span class="st-lbl">' + esc(T('f.dest')) + '</span><div class="st-radios"><label><input type="radio" name="dest" value="stock" checked> ' + esc(T('f.dest.stock')) + '</label><label><input type="radio" name="dest" value="wo"> ' + esc(T('f.dest.wo')) + '</label></div></div>' +
        '<div class="st-f full" id="sf-reason-wrap" style="display:none"><label for="sf-reason">' + esc(T('f.reason')) + '</label><select class="st-in" id="sf-reason">' + C.WRITE_OFF_REASONS.map(function (r) { return option(r, T('reason.' + r)); }).join('') + '</select></div></div>';
    }
    if (kind === 'wo') return '<div class="st-form">' + fld('reason', T('f.reason'), '<select class="st-in" id="sf-reason">' + C.WRITE_OFF_REASONS.map(function (r) { return option(r, T('reason.' + r)); }).join('') + '</select>') + fld('date', T('f.date'), dat('date', t0, t0)) + '</div><p class="st-hint">' + esc(T('sheet.wo.note')) + '</p>';
    return '';
  }
  function previewSold() {
    var it = S.sheet.item, box = $('#st-prev'); if (!box) return;
    var sold = C.parseMoneyInput(($('#sf-sold') || {}).value, lang), ship = C.parseMoneyInput(($('#sf-ship') || {}).value, lang), cost = C.costCents(it);
    if (cost == null) { box.innerHTML = esc(T('preview.nocost')); return; }
    if (!sold.ok || sold.cents == null) { box.innerHTML = esc(T('preview.cost', { cost: M(cost) })); return; }
    var p = sold.cents - cost - (ship.ok && ship.cents ? ship.cents : 0);
    box.innerHTML = esc(T('preview.profit')) + '<strong class="' + (p < 0 ? 'st-neg' : 'st-pos') + '">' + esc(MS(p)) + '</strong>';
  }
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

  function submitSheet(andNext) {
    var sh = S.sheet; if (!sh) return;
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
      var sp = readMoney('sold', true), sd = readDate('soldon'), sh2 = readMoney('ship'); if (sp.bad || sd.bad || sh2.bad) return;
      run = function () { return S.api.markSold(item.id, { soldCents: sp.cents, on: sd.v, platform: $('#sf-platform').value || undefined, shipPaidCents: sh2.cents == null ? undefined : sh2.cents }); }; label = T('toast.sold');
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
        $('#sf-title').value = ''; $('#sf-buy').value = ''; $('#sf-extra').value = ''; $('#sf-size').value = ''; $('#sf-quantity').value = '1'; if (go) go.disabled = false; $('#sf-title').focus();
      } else closeSheet();
    });
  }

  // ------------------------------------------------------------------ item detail
  function findRow(id) { return S.rows.filter(function (r) { return r.id === id; })[0]; }
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
    var extra = it.returned_on ? '<p class="st-note" style="margin-top:12px">' + esc(T('detail.returned', { date: fmtDate(it.returned_on) })) + '</p>' : '';
    var foot = '<button type="button" class="st-btn st-tert" data-act="close">' + esc(T('close')) + '</button><button type="button" class="st-btn st-prim" data-act="save-detail" data-id="' + esc(it.id) + '" id="st-go">' + esc(T('save')) + '</button>';
    mountSheet(it.title, '<div id="st-sheet-err"></div><span class="st-tag ' + esc(it.status) + '" style="margin-bottom:12px">' + esc(statusLabel(it.status)) + '</span>' + facts + acts + form + extra + '<div class="st-h3">' + esc(T('detail.history')) + '</div><ul class="st-tl" id="st-tl"><li>...</li></ul>', foot);
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

  window.SNYPD = window.SNYPD || {};
  window.SNYPD.stock = { open: open, refresh: refresh };
})();
