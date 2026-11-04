/*
 * QA mock for dashboard.html - a Supabase + backend-API stand-in for driving
 * the real dashboard in a browser without touching production.
 *
 * WHY THIS EXISTS
 * Reading dashboard.html's source, or testing it against a mock that never
 * enforces real constraints, has both independently missed real bugs in this
 * project before - a migration's CHECK constraint rejecting a value a mock
 * happily accepted; an empty image_url that hid the <img> path for the
 * product's entire history; a stale claimedIds set that only a reload-shaped
 * test would ever exercise. Driving the real file against seeded data that
 * covers the actual edge cases, and actually clicking through it, is what
 * has caught bugs static reading alone did not (see CLAUDE.md Session 17).
 *
 * GOTCHA: select() hands back the LIVE row objects, not copies. Two reads
 * taken either side of a write therefore point at the same object and both
 * show the final value, which can make a write that did work look like it
 * did nothing. Snapshot the field you care about (or JSON.parse(JSON.
 * stringify(...))) rather than holding two result references. Cost me a
 * wrong "quiet hours does not persist" conclusion on 2026-09-22.
 *
 * HOW TO USE
 * 1. Copy dashboard.html next to this file (or vice versa) and swap its
 *    Supabase CDN <script> tag for this one:
 *      <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 *    becomes
 *      <script src="qa_mock.js"></script>
 *    It must load in the exact same spot - BEFORE the inline <script> that
 *    calls window.supabase.createClient(...) a few lines later in <head>.
 * 2. Also copy sw.js and manifest.webmanifest next to the copy, or the
 *    service-worker registration will fail with console noise while you're
 *    hunting for a real error (harmless either way - the page's own code
 *    already degrades that to a disabled "Alerts unavailable" button).
 * 3. Serve the folder over plain HTTP, e.g. `python3 -m http.server 8900`
 *    from that folder - a file:// URL will not execute inline <script>
 *    blocks in most browser-automation/preview tooling.
 * 4. Open /dashboard.html?plan=elite or ?plan=free to pick which plan the
 *    seeded user is on (default: elite). Elite unlocks Market Insights and
 *    the deal-quality-bonus path; free shows the upsell banner instead.
 * 5. The feed's own auto-start is activity-gated (mousemove/scroll/click/
 *    keydown - see dashboard.html's own touchActivity()), so a pure
 *    JS-evaluation call (no synthetic DOM event) will never trigger it.
 *    Dispatch a real scroll or click through whatever browser-automation
 *    tool you're driving this with, not raw script injection alone.
 * 6. Bump a ?v=N query on the <script src="qa_mock.js?v=N"> tag (or restart
 *    the static server) whenever you edit this file - a plain http.server
 *    plus normal browser caching can otherwise silently keep serving a
 *    stale copy, which cost real debugging time to figure out once.
 *
 * WHAT'S MOCKED
 * - window.supabase.createClient(): a generic postgrest-style query builder
 *   (.select/.eq/.neq/.gte/.lte/.in/.not/.order/.limit/.single/.maybeSingle/
 *   .insert/.update/.delete, thenable directly like the real client - no
 *   explicit terminal call needed, `await sb.from(...).select(...)` just
 *   works) over the in-memory DB object below. Extend matchRow()/
 *   makeBuilder() if dashboard.html grows a query shape this doesn't cover.
 * - window.fetch(): only for api.snypd.store paths (heartbeat, push/key,
 *   push/status, market/snapshot) - everything else falls through to the
 *   real fetch, which will fail from a non-snypd.store origin (expected;
 *   those calls aren't part of what this harness is testing).
 * - window.__qaErrors: every window 'error'/'unhandledrejection' since this
 *   script loaded gets pushed here, so a driving session can check
 *   `window.__qaErrors` at the end instead of only trusting "the page
 *   looked fine on screen."
 *
 * WHAT'S SEEDED (see the DB object below - edit freely per test)
 * current_ads covers: a normal fresh listing with a buyer-protection line, a
 * DROP badge (needs its own listing_first_seen row, see below), a
 * suspicious-photo flag, a gone (is_visible=false) listing, a null price, a
 * very long title (card-width/overflow stress), a non-EUR currency, and a
 * listing that already has a prior claim - the exact case that catches a
 * stale, un-seeded claimedIds regression (a claimed-but-still-listed item
 * silently reappearing with a live Claim button after a reload). Ages are
 * relative to `now` at load time and MUST stay inside dashboard.html's own
 * 30-minute feed cutoff (DASHBOARD_MAX_AGE_MIN) or the row silently will not
 * appear in the feed at all - no error, it just will not be there. That cost
 * real time to debug once; do not repeat it.
 *
 * user_claims covers a fresh holding item (<45 days - single MARK SOLD),
 * a stale holding item (>=45 days - STILL LISTED/SOLD split), and a sold
 * item (a real gain, to check the History profit figure). xp_events seeds a
 * real deal_quality_bonus row linked to a claim, to check the "pending" ->
 * real-amount card flip. user_streak_state seeds a real streak day.
 *
 * This is a test tool, not part of the shipped product - never reference it
 * from dashboard.html itself. This repo has no build step, so Vercel would
 * otherwise serve any committed file at its own path exactly like every
 * other page here - ops/ is excluded via .vercelignore specifically so this
 * (and anything else added under ops/ later) never ships to production.
 * Keep any working dashboard.qa.html copy itself outside the repo entirely
 * (e.g. a scratch dir), not just under ops/ - only this mock script is
 * meant to live here.
 */
(function () {
  window.__qaErrors = [];
  window.addEventListener('error', function (e) { window.__qaErrors.push(String((e.error && e.error.stack) || e.message)); });
  window.addEventListener('unhandledrejection', function (e) { window.__qaErrors.push('UNHANDLED: ' + String((e.reason && e.reason.stack) || e.reason)); });

  var now = Date.now();
  var min = 60 * 1000;

  // ---- toggle plan via ?plan=free|elite in the test URL ----
  var params = new URLSearchParams(location.search);
  var PLAN = params.get('plan') || 'elite';
  // ?hunts=0 seeds an account with no saved searches - the brand-new-user
  // path (first-run wizard, first-hunt empty state). Without this there was
  // no way to exercise either from QA at all.
  var NO_HUNTS = params.get('hunts') === '0';

  var UID = 'qa-user-0000-0000-0000-000000000001';
  var QA_META = {};
  try { QA_META = JSON.parse(params.get('meta') || '{}'); } catch (e) {}
  window.__qa_auth_updates = [];
  function qaUser() {
    return { id: UID, email: 'qa-test@example.com', created_at: new Date(Date.now() - 40 * 86400000).toISOString(),
      user_metadata: JSON.parse(JSON.stringify(QA_META)) };
  }

  var DB = {
    users: [
      {
        id: UID,
        subscription_plan: PLAN,
        sub_status: PLAN === 'elite' ? 'active' : 'free',
        billing_provider: PLAN === 'elite' ? 'whop' : null,
        whop_product_id: PLAN === 'elite' ? 'prod_test123' : null,
        whop_manage_url: PLAN === 'elite' ? 'https://whop.com/manage' : null,
        is_founding_member: true,
        founding_number: 7,
      },
    ],
    current_ads: [
      // 1. Normal fresh listing (NEW badge), EUR, has a buyer-protection line.
      {
        listing_id: 1001, user_id: UID, title: 'Nike Air Max 90 Infrared',
        price: { amount: 62, currency_code: 'EUR' },
        total_item_price: { amount: 65.7, currency_code: 'EUR' },
        brand_title: 'Nike', size_title: '42', url: 'https://www.vinted.be/items/1001',
        status: 'Very good', content_source: 'search', image_url: 'https://picsum.photos/seed/1001/600/600',
        item_box: null, fetched_at: new Date(now - 2 * min).toISOString(),
        created_at: new Date(now - 2 * min).toISOString(), uploaded_ts: Math.floor((now - 2 * min) / 1000),
        uploaded_at_ts: new Date(now - 2 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 1, view_count: 10, is_suspicious: false,
      },
      // 2. DROP badge: current price below its own first-seen price (listing_first_seen below).
      {
        listing_id: 1002, user_id: UID, title: 'Jordan 1 Mid Chicago',
        price: { amount: 70, currency_code: 'EUR' },
        total_item_price: { amount: 74.2, currency_code: 'EUR' },
        brand_title: 'Jordan', size_title: '43', url: 'https://www.vinted.be/items/1002',
        status: 'Good', content_source: 'search', image_url: 'https://picsum.photos/seed/1002/600/600',
        item_box: null, fetched_at: new Date(now - 20 * min).toISOString(),
        created_at: new Date(now - 20 * min).toISOString(), uploaded_ts: Math.floor((now - 20 * min) / 1000),
        uploaded_at_ts: new Date(now - 20 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 3, view_count: 40, is_suspicious: false,
      },
      // 3. Suspicious (Vinted photo-moderation flag).
      {
        listing_id: 1003, user_id: UID, title: 'Off-White Hoodie Diagonal',
        price: { amount: 140, currency_code: 'EUR' }, total_item_price: { amount: 146.7, currency_code: 'EUR' },
        brand_title: 'Off-White', size_title: 'M', url: 'https://www.vinted.be/items/1003',
        status: 'New with tags', content_source: 'search', image_url: 'https://picsum.photos/seed/1003/600/600',
        item_box: null, fetched_at: new Date(now - 22 * min).toISOString(),
        created_at: new Date(now - 22 * min).toISOString(), uploaded_ts: Math.floor((now - 22 * min) / 1000),
        uploaded_at_ts: new Date(now - 22 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 0, view_count: 5, is_suspicious: true,
      },
      // 4. Gone (is_visible=false) - should render dimmed, no Claim, no badges, no delta.
      {
        listing_id: 1004, user_id: UID, title: 'Carhartt Detroit Jacket',
        price: { amount: 95, currency_code: 'EUR' }, total_item_price: { amount: 99.7, currency_code: 'EUR' },
        brand_title: 'Carhartt', size_title: 'L', url: 'https://www.vinted.be/items/1004',
        status: 'Good', content_source: 'search', image_url: 'https://picsum.photos/seed/1004/600/600',
        item_box: null, fetched_at: new Date(now - 20 * min).toISOString(),
        created_at: new Date(now - 20 * min).toISOString(), uploaded_ts: Math.floor((now - 20 * min) / 1000),
        uploaded_at_ts: new Date(now - 20 * min).toISOString(), is_visible: false, promoted: false,
        favourite_count: 2, view_count: 20, is_suspicious: false,
      },
      // 5. Null price ("Price unavailable" state) - still has a title, so Check price should show.
      {
        listing_id: 1005, user_id: UID, title: 'Stone Island Sweater Badge',
        price: null, total_item_price: null,
        brand_title: 'Stone Island', size_title: 'M', url: 'https://www.vinted.be/items/1005',
        status: 'Very good', content_source: 'search', image_url: '',
        item_box: null, fetched_at: new Date(now - 25 * min).toISOString(),
        created_at: new Date(now - 25 * min).toISOString(), uploaded_ts: Math.floor((now - 25 * min) / 1000),
        uploaded_at_ts: new Date(now - 25 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 0, view_count: 1, is_suspicious: false,
      },
      // 6. Very long title (overflow/ellipsis + card-width stress, README 4.7).
      {
        listing_id: 1006, user_id: UID,
        title: 'Nike Air Jordan 1 Retro High OG Chicago Lost and Found 2022 Deadstock Size 43 EU Rare Colorway With Original Box',
        price: { amount: 1499.99, currency_code: 'EUR' }, total_item_price: { amount: 1499.99, currency_code: 'EUR' },
        brand_title: 'Jordan', size_title: '43', url: 'https://www.vinted.be/items/1006',
        status: 'New without tags', content_source: 'search', image_url: 'https://picsum.photos/seed/1006/600/600',
        item_box: null, fetched_at: new Date(now - 5 * min).toISOString(),
        created_at: new Date(now - 5 * min).toISOString(), uploaded_ts: Math.floor((now - 5 * min) / 1000),
        uploaded_at_ts: new Date(now - 5 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 9, view_count: 99, is_suspicious: false,
      },
      // 7. Non-EUR currency (USD) - checks symbol derivation from the real field.
      {
        listing_id: 1007, user_id: UID, title: 'Patagonia Synchilla Fleece',
        price: { amount: 55, currency_code: 'USD' }, total_item_price: { amount: 58.4, currency_code: 'USD' },
        brand_title: 'Patagonia', size_title: 'M', url: 'https://www.vinted.be/items/1007',
        status: 'Good', content_source: 'search', image_url: 'https://picsum.photos/seed/1007/600/600',
        item_box: null, fetched_at: new Date(now - 10 * min).toISOString(),
        created_at: new Date(now - 10 * min).toISOString(), uploaded_ts: Math.floor((now - 10 * min) / 1000),
        uploaded_at_ts: new Date(now - 10 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 1, view_count: 8, is_suspicious: false,
      },
      // 8. Already-claimed-elsewhere-before (matching a user_claims seed row
      // below) - on a correct load this should show "Claimed" disabled
      // immediately, with NO extra click needed. This is the exact case the
      // missing claimedIds-seeding bug (Session 17) got wrong.
      {
        listing_id: 1008, user_id: UID, title: 'Arc teryx Beta Jacket',
        price: { amount: 230, currency_code: 'EUR' }, total_item_price: { amount: 240, currency_code: 'EUR' },
        brand_title: "Arc'teryx", size_title: 'L', url: 'https://www.vinted.be/items/1008',
        status: 'Very good', content_source: 'search', image_url: 'https://picsum.photos/seed/1008/600/600',
        item_box: null, fetched_at: new Date(now - 28 * min).toISOString(),
        created_at: new Date(now - 28 * min).toISOString(), uploaded_ts: Math.floor((now - 28 * min) / 1000),
        uploaded_at_ts: new Date(now - 28 * min).toISOString(), is_visible: true, promoted: false,
        favourite_count: 4, view_count: 44, is_suspicious: false,
      },
    ],
    listing_first_seen: [
      { user_id: UID, listing_id: 1002, first_seen_price: { amount: 95, currency_code: 'EUR' } },
    ],
    user_searches: [
      { id: 'search-1', user_id: UID, search_name: 'Jordan 1 Travis Scott', vinted_url: 'https://www.vinted.be/catalog?search_text=jordan%20travis%20scott', is_active: true, push_mode: 'every', push_calm_minutes: 15, created_at: new Date(now - 5 * 86400000).toISOString() },
      { id: 'search-2', user_id: UID, search_name: 'Off-White', vinted_url: 'https://www.vinted.be/catalog?search_text=off%20white', is_active: false, push_mode: 'calm', push_calm_minutes: 30, created_at: new Date(now - 4 * 86400000).toISOString() },
    ],
    user_claims: [
      // Holding, < 45 days -> single full-width MARK SOLD.
      {
        id: 'claim-1', user_id: UID, listing_id: 1008, title: 'Arc teryx Beta Jacket', brand_title: "Arc'teryx",
        size_title: 'L', image_url: 'https://picsum.photos/seed/1008/600/600', vinted_url: 'https://www.vinted.be/items/1008',
        bought_price_cents: 23000, under_market_cents: null, status: 'holding',
        claimed_at: new Date(now - 10 * 86400000).toISOString(), sold_price_cents: null, sold_at: null,
      },
      // Holding, >= 45 days -> STILL LISTED / SOLD split per README 5.4.5.
      {
        id: 'claim-2', user_id: UID, listing_id: 2002, title: 'Vintage Levis 501', brand_title: 'Levis',
        size_title: '32', image_url: '', vinted_url: 'https://www.vinted.be/items/2002',
        bought_price_cents: 4000, under_market_cents: null, status: 'holding',
        claimed_at: new Date(now - 61 * 86400000).toISOString(), sold_price_cents: null, sold_at: null,
      },
      // Sold (a real gain - +30 - so History's profit figure has something
      // real to render; flip sold_price_cents below bought_price_cents on a
      // copy of this row to test the loss/negative-profit sign instead).
      {
        id: 'claim-3', user_id: UID, listing_id: 2003, title: 'Adidas Samba OG', brand_title: 'Adidas',
        size_title: '44', image_url: 'https://picsum.photos/seed/2003/600/600', vinted_url: 'https://www.vinted.be/items/2003',
        bought_price_cents: 6000, under_market_cents: 1500, status: 'sold',
        claimed_at: new Date(now - 20 * 86400000).toISOString(), sold_price_cents: 9000,
        sold_at: new Date(now - 5 * 86400000).toISOString(),
      },
    ],
    xp_events: [
      { id: 'xp-1', user_id: UID, event_type: 'claim', xp: 1265, item_id: 'claim-1', meta: null, created_at: new Date(now - 10 * 86400000).toISOString() },
      // Real deal-quality bonus for claim-1 (Elite only) - should flip its
      // History card from "pending" to "+18 XP quality bonus".
      { id: 'xp-2', user_id: UID, event_type: 'deal_quality_bonus', xp: 18, item_id: 'claim-1', meta: { median_cents: 28000, bought_cents: 23000 }, created_at: new Date(now - 10 * 86400000).toISOString() },
    ],
    user_streak_state: [
      { user_id: UID, current_streak: 9 },
    ],
  };

  if (NO_HUNTS) { DB.user_searches = []; DB.user_claims = []; DB.xp_events = []; }
  if (params.get('stock_claims') === '0') DB.user_claims = [];   // an account that never claimed anything: Stock's first-run screen

  // ?broad=1: 40 fresh listings stamped for the active seeded hunt (search-1), enough for the dashboard's
  // "This hunt is very broad" card (>= 25 matches in 30 min). The stamp mirrors dashboard savedSearchSignature();
  // the literal 'item_box->...->>version' key lets matchRow() pass the feed's JSON-path filter.
  // ?seedcalm=1: the active seeded hunt starts on Calm / 15 (a calm hunt never gets the broad card).
  if (params.get('seedcalm') === '1' && DB.user_searches[0]) {
    DB.user_searches[0].push_mode = 'calm'; DB.user_searches[0].push_calm_minutes = 15;
  }
  if (params.get('broad') === '1' && DB.user_searches[0]) {
    var u = new URL(DB.user_searches[0].vinted_url);
    var pairs = Array.from(u.searchParams).filter(function (p) { return ['page', 'per_page', 'order', 'time', 'search_id'].indexOf(p[0]) < 0 && p[1]; }).sort();
    var sig = JSON.stringify([u.hostname.toLowerCase(), u.pathname.replace(/\/+$/, '') || '/', pairs]);
    for (var i = 0; i < 40; i++) {
      var t = now - (i % 25 + 1) * min;
      DB.current_ads.push({
        listing_id: 5000 + i, user_id: UID, title: 'Broad QA listing ' + i,
        price: { amount: 20 + i, currency_code: 'EUR' }, brand_title: 'Jordan', size_title: '42', status: 'Good',
        url: 'https://www.vinted.be/items/' + (5000 + i), content_source: 'search', image_url: '',
        item_box: { snypd_filter_contract: { version: 1, search: sig } }, 'item_box->snypd_filter_contract->>version': '1',
        fetched_at: new Date(t).toISOString(), created_at: new Date(t).toISOString(),
        uploaded_ts: Math.floor(t / 1000), uploaded_at_ts: new Date(t).toISOString(), is_visible: true, promoted: false,
      });
    }
  }

  function matchRow(row, filters) {
    return filters.every(function (f) {
      var val = row[f.col];
      if (f.op === 'eq') return val === f.val;
      if (f.op === 'neq') return val !== f.val;
      if (f.op === 'gte') return val != null && val >= f.val;
      if (f.op === 'lte') return val != null && val <= f.val;
      if (f.op === 'in') return f.val.indexOf(val) !== -1;
      if (f.op === 'not_is_null') return val != null;
      return true;
    });
  }

  // ---- Stock (migrations 065-068): an in-memory port of the RPCs with the same names, arguments, CHECKs and error codes ----
  // Needs <script src="stock_engine.js"></script> BEFORE this file (copy ops/stock_engine.js next to the page). Without it Stock RPCs fall through.
  //   ?stock=off|admin|all   runtime_config.stock_mode (default all; admin = visible only to the elite QA user)
  //   ?stock_seed=acceptance loads the frozen design dataset (215 items, 580 history rows): copy ops/stock/acceptance-fixture.json next to the page
  //   ?stock_today=YYYY-MM-DD fixes the engine's "today" (the dataset's own today is 2026-10-27)
  //   ?stock_paid=0          a Free account (25 held items); default follows ?plan=
  //   ?stock_pre072=1        the engine answers like production before migration 072 (no expense functions, series without expenses)
  //   ?stock_pre071=1        the engine answers like production before migration 071 (Items page ignores sort, rows without image_url)
  //   ?stock_claims=0        no Feed claims (an empty Stock: first-run screen); ?stock_hidden=1 the user already hid the Stock tab
  // Feed claims in this mock's user_claims are mirrored into Stock like trigger 067 does (insert / update / delete).
  var STOCK = null, stockReady = Promise.resolve();
  if (window.SnypdStockEngine) {
    STOCK = window.SnypdStockEngine.createEngine({
      uid: UID, mode: params.get('stock') || 'all', admin: PLAN === 'elite', paid: params.get('stock_paid') ? params.get('stock_paid') !== '0' : PLAN !== 'free',
      searches: DB.user_searches || [], pre071: params.get('stock_pre071') === '1', pre072: params.get('stock_pre072') === '1', today: params.get('stock_today') ? function () { return params.get('stock_today'); } : null
    });
    window.__qaStock = STOCK;
    window.SNYPD = window.SNYPD || {}; if (params.get('stock_today')) window.SNYPD.stockToday = function () { return params.get('stock_today'); };   // the page's Stock UI asks for this "today" like the engine does
    if (params.get('stock_hidden') === '1') STOCK.setSettings({ tab_hidden: true });   // the user hid the Stock tab earlier: dashboard_boot().stock_tab_hidden is true
    var seedClaims = function () { (DB.user_claims || []).forEach(function (c) { try { STOCK.mirrorClaim(c); } catch (e) { console.warn('QA stock claim mirror failed', e); } }); };
    if (params.get('stock_seed') === 'acceptance') {
      stockReady = fetch('acceptance-fixture.json').then(function (r) { return r.json(); }).then(function (fx) { STOCK.loadFixture(fx); seedClaims(); })
        .catch(function (e) { window.__qaErrors.push('QA stock seed failed: ' + e); });
    } else seedClaims();
    // Stands in for dashboard_boot().stock_mode (this mock does not implement that RPC): shows the Stock tab when the switch is admin / all.
    if (params.get('boot') !== '1') STOCK.rpc('stock_boot').then(function (r) {
      if (!r.data || r.data.mode === 'off') return;
      var tries = 0, t = setInterval(function () { if (window.SNYPD && window.SNYPD.onStockMode) { clearInterval(t); window.SNYPD.onStockMode(r.data.mode); } else if (++tries > 200) clearInterval(t); }, 50);
    });
  }

  function makeBuilder(table) {
    var filters = [];
    var order = [];
    var limitN = null;
    var op = 'select';
    var payload = null;
    var singleMode = null; // 'single' | 'maybeSingle'
    var countHead = false;

    var builder = {
      select: function (cols, opts) {
        if (opts && opts.head) countHead = true;
        return builder;
      },
      eq: function (col, val) { filters.push({ col: col, op: 'eq', val: val }); return builder; },
      neq: function (col, val) { filters.push({ col: col, op: 'neq', val: val }); return builder; },
      gte: function (col, val) { filters.push({ col: col, op: 'gte', val: val }); return builder; },
      lte: function (col, val) { filters.push({ col: col, op: 'lte', val: val }); return builder; },
      in: function (col, vals) { filters.push({ col: col, op: 'in', val: vals }); return builder; },
      not: function (col, kind, val) {
        if (kind === 'is' && val === null) filters.push({ col: col, op: 'not_is_null' });
        return builder;
      },
      order: function (col, opts) { order.push({ col: col, asc: !opts || opts.ascending !== false }); return builder; },
      limit: function (n) { limitN = n; return builder; },
      single: function () { singleMode = 'single'; return builder; },
      maybeSingle: function () { singleMode = 'maybeSingle'; return builder; },
      insert: function (data) { op = 'insert'; payload = data; return builder; },
      update: function (data) { op = 'update'; payload = data; return builder; },
      delete: function () { op = 'delete'; return builder; },
      upsert: function (data) { op = 'upsert'; payload = data; return builder; },
      then: function (resolve, reject) {
        try { resolve(execute()); } catch (e) { if (reject) reject(e); else throw e; }
      },
    };

    function execute() {
      var rows = (STOCK && table === 'stock_history') ? STOCK.state.history : (DB[table] || (DB[table] = []));   // Stock history is read-only here, like the real select-own table

      // Column defaults + CHECKs that the real DB has (migrations 043, 064), so
      // the page sees the same row shape after an insert as in production.
      var badPush = function (r) {
        return (r.push_mode !== undefined && ['every', 'calm'].indexOf(r.push_mode) < 0) ||
          (r.push_calm_minutes !== undefined && [15, 30].indexOf(r.push_calm_minutes) < 0);
      };
      if (table === 'user_searches' && (op === 'insert' || op === 'update') && badPush(payload || {})) {
        return { data: null, error: { code: '23514', message: 'new row violates check constraint (push_mode / push_calm_minutes)' } };
      }
      if (STOCK && table === 'stock_settings') {   // own-row select / insert / update / upsert (policies of 065); the CHECKs live in the engine
        if (op === 'select') { var srow = STOCK.settingsRow(); return { data: singleMode ? srow : (srow ? [srow] : []), error: null }; }
        try { var sp = Object.assign({}, payload); delete sp.user_id; STOCK.setSettings(sp); return { data: payload, error: null }; } catch (e) { return { data: null, error: e.pg || { message: String(e) } }; }
      }
      if (STOCK && table === 'stock_items' && op === 'select') rows = STOCK.state.items;   // read-only, like the real select-own table
      if (STOCK && table === 'stock_categories' && op === 'insert') {   // own-row insert policy + the 30-category trigger live in the engine
        try { STOCK.addCategories(Array.isArray(payload) ? payload : [payload]); return { data: payload, error: null }; } catch (e) { return { data: null, error: e.pg || { message: String(e) } }; }
      }
      if (op === 'insert') {
        var toInsert = Array.isArray(payload) ? payload : [payload];
        var inserted = toInsert.map(function (r) {
          var withDefaults = Object.assign({
            id: 'qa-' + table + '-' + Math.random().toString(36).slice(2, 10),
            created_at: new Date().toISOString(),
          }, table === 'user_searches' ? { show_all_results: true, push_mode: 'every', push_calm_minutes: 15 } : {}, r);
          rows.push(withDefaults);
          return withDefaults;
        });
        if (STOCK && table === 'user_claims') inserted.forEach(function (c) { try { STOCK.mirrorClaim(c); } catch (e) { console.warn('QA stock claim mirror failed', e); } });
        if (singleMode) return { data: inserted[0], error: null };
        return { data: inserted, error: null };
      }

      if (op === 'update') {
        var matched = rows.filter(function (r) { return matchRow(r, filters); });
        matched.forEach(function (r) {
          var oldPrice = r.bought_price_cents;
          Object.assign(r, payload);
          if (STOCK && table === 'user_claims') { try { STOCK.mirrorClaimUpdate(r, oldPrice); } catch (e) { console.warn('QA stock claim mirror failed', e); } }
        });
        return { data: matched, error: null };
      }

      if (op === 'delete') {
        var toRemove = rows.filter(function (r) { return matchRow(r, filters); });
        if (STOCK && table === 'user_claims') toRemove.forEach(function (c) { STOCK.mirrorClaimDelete(c.id); });
        DB[table] = rows.filter(function (r) { return !matchRow(r, filters); });
        return { data: toRemove, error: null };
      }

      // select
      var result = rows.filter(function (r) { return matchRow(r, filters); });
      order.forEach(function (o) {
        result.sort(function (a, b) {
          var av = a[o.col], bv = b[o.col];
          if (av === bv) return 0;
          if (av == null) return 1;
          if (bv == null) return -1;
          return o.asc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
        });
      });
      if (limitN != null) result = result.slice(0, limitN);

      if (countHead) return { data: null, error: null, count: result.length };
      if (singleMode === 'single') return { data: result[0] || null, error: result[0] ? null : { message: 'No rows found' } };
      if (singleMode === 'maybeSingle') return { data: result[0] || null, error: null };
      return { data: result, error: null };
    }

    return builder;
  }

  var fakeClient = {
    auth: {
      getSession: function () {
        // ?nosession=1: logged out (sign-up / login pages).
        if (params.get('nosession') === '1') return Promise.resolve({ data: { session: null }, error: null });
        return Promise.resolve({
          data: {
            session: {
              access_token: 'qa-fake-token',
              user: qaUser(),
            },
          },
          error: null,
        });
      },
      signOut: function () { return Promise.resolve({ error: null }); },
      // ?meta=<json> seeds user_metadata (e.g. {} = no marketing choice yet). getUser reads the
      // live copy; updateUser merges like Supabase Auth and logs to window.__qa_auth_updates;
      // ?update_fail=1 makes updateUser return an error.
      getUser: function () { return Promise.resolve({ data: { user: qaUser() }, error: null }); },
      updateUser: function (attrs) {
        window.__qa_auth_updates.push(JSON.parse(JSON.stringify(attrs)));
        if (params.get('update_fail') === '1') return Promise.resolve({ data: null, error: { message: 'QA mock: update failed' } });
        Object.assign(QA_META, (attrs && attrs.data) || {});
        return Promise.resolve({ data: { user: qaUser() }, error: null });
      },
    },
    from: function (table) { return makeBuilder(table); },
    rpc: function (name, args) {
      // ?boot=1 serves dashboard_boot() like migration 054/068 (profile, searches, claims, dq, xp_total, streak, quota + stock_mode), so the page's REAL boot path
      // (including its Stock hook) is exercised. Off by default: the usual QA flows keep using the separate REST reads.
      if (name === 'dashboard_boot' && params.get('boot') === '1') {
        var u0 = DB.users[0] || {}, searches = (DB.user_searches || []).slice().sort(function (a, b) { return String(b.created_at).localeCompare(String(a.created_at)); });
        return Promise.resolve({ data: {
          profile: { subscription_plan: u0.subscription_plan, sub_status: u0.sub_status, billing_provider: u0.billing_provider, whop_product_id: u0.whop_product_id, whop_manage_url: u0.whop_manage_url,
            is_founding_member: u0.is_founding_member, founding_number: u0.founding_number, free_trial_started_at: null, trial_ends_at: null, trial_extended_at: null, pass_expires_at: null },
          searches: searches, claims: (DB.user_claims || []).slice(), dq: [], xp_total: (DB.xp_events || []).reduce(function (a, x) { return a + (x.xp || 0); }, 0),
          streak: ((DB.user_streak_state || [])[0] || {}).current_streak || null, quota: { quota_limit: PLAN === 'free' ? 1 : 5, used: searches.length },
          stock_mode: STOCK ? STOCK.mode() : undefined, stock_tab_hidden: STOCK ? STOCK.tabHidden() : false }, error: null });
      }
      // Stock RPCs (migrations 065-068) -> the in-memory port, see ops/stock_engine.js. Everything else keeps the old "not implemented" answer.
      if (STOCK && /^stock_/.test(name)) return stockReady.then(function () { return STOCK.rpc(name, args); });
      return Promise.resolve({ data: null, error: { message: 'QA mock: rpc not implemented, falls back to plan table' } });
    },
  };

  window.supabase = { createClient: function () { return fakeClient; } };

  // ---- fetch() interception for the backend API ----
  var realFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    var u = String(url);
    if (u.indexOf('api.snypd.store') === -1) return realFetch(url, opts);

    if (u.indexOf('/api/v1/heartbeat') !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    if (u.indexOf('/api/v1/push/key') !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ vapid_public_key: 'QA_FAKE_KEY' }), { status: 200 }));
    }
    if (u.indexOf('/api/v1/push/status') !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ status: 'ready' }), { status: 200 }));
    }
    if (u.indexOf('/api/v1/market/snapshot') !== -1) {
      var body = {};
      try { body = JSON.parse(opts && opts.body || '{}'); } catch (e) {}
      var q = (body.q || '').toLowerCase();

      if (PLAN !== 'elite') {
        return Promise.resolve(new Response(JSON.stringify({ detail: 'elite_required' }), { status: 403 }));
      }
      if (q.indexOf('nike') !== -1 && q.indexOf(' ') === -1) {
        return Promise.resolve(new Response(JSON.stringify({ detail: 'nike alone appears in 447,950 listings - add a model name or colourway.' }), { status: 503 }));
      }
      if (q.indexOf('zzz_nomatch') !== -1) {
        return Promise.resolve(new Response(JSON.stringify({
          query: q, sample_size: 0, display_verdict: 'too_thin', show_headline: false, quota: { hour_remaining: 19, hour_limit: 20 },
        }), { status: 200 }));
      }
      // Default: a normal, trustworthy result. typical_cents is deliberately
      // NOT a round number (EUR273.70) - this is the exact shape that caught
      // Market Insights' own eur() rounding bug (Session 17): a round number
      // like 4500 would pass even with that bug still present.
      return Promise.resolve(new Response(JSON.stringify({
        query: q || 'jordan 1 mid', sample_size: 5399, distinct_sellers: 812,
        display_verdict: 'ok', provisional: false, show_headline: true,
        typical_cents: 27370, range_cents: { low: 3800, high: 5200 },
        by_condition: [
          { condition_label: 'New with tags', verdict: 'ok', typical_cents: 8500, range_cents: { low: 7000, high: 9500 }, sample_size: 120, provisional: false },
          { condition_label: 'Very good', verdict: 'ok', typical_cents: 4200, range_cents: { low: 3500, high: 5000 }, sample_size: 900, provisional: false },
          { condition_label: 'Satisfactory', verdict: 'ok', typical_cents: 1800, range_cents: { low: 1200, high: 2400 }, sample_size: 40, provisional: false },
        ],
        positioning: {
          bands: [
            { key: 'cheap', label: 'Cheapest quarter', note: 'priced to move fast', upto_cents: 3800 },
            { key: 'mid1', label: 'Below median', note: 'competitive', upto_cents: 4500 },
            { key: 'mid2', label: 'Above median', note: 'patient sellers', upto_cents: 5200 },
            { key: 'top', label: 'Most expensive quarter', note: 'likely to sit unsold', upto_cents: 5200 },
          ],
        },
        price_drift: { message: '12% of listings have already dropped their price since we started watching.' },
        coverage_note: null, flags: [], quota: { hour_remaining: 17, hour_limit: 20 },
      }), { status: 200 }));
    }
    return realFetch(url, opts);
  };

  console.log('[QA MOCK] active. plan=' + PLAN + ' uid=' + UID);
})();
