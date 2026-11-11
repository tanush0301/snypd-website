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
  // Feedback questions (migration 081): ids already answered or skipped, from ?fbdone=A,B1 (empty by default).
  var FB_DONE = (params.get('fbdone') || '').split(',').filter(Boolean);
  // ?hunts=0 seeds an account with no saved searches - the brand-new-user
  // path (first-run wizard, first-hunt empty state). Without this there was
  // no way to exercise either from QA at all.
  var NO_HUNTS = params.get('hunts') === '0';

  var UID = 'qa-user-0000-0000-0000-000000000001';
  var QA_META = {};
  try { QA_META = JSON.parse(params.get('meta') || '{}'); } catch (e) {}
  window.__qa_auth_updates = [];
  function qaUser() {
    // ?joined=new: an account created after the 7 Nov 2026 privacy change (no hunter-statistics notice)
    return { id: UID, email: 'qa-test@example.com', created_at: new Date(params.get('joined') === 'new' ? Date.parse('2026-11-09T10:00:00Z') : Date.now() - 40 * 86400000).toISOString(),
      user_metadata: JSON.parse(JSON.stringify(QA_META)) };
  }

  var DB = {
    users: [
      {
        id: UID,
        subscription_plan: PLAN,
        // ?active=1 makes any paid plan (solo, kickstart, pro) an active Whop membership like elite.
        sub_status: (PLAN === 'elite' || params.get('active') === '1') ? 'active' : 'free',
        billing_provider: (PLAN === 'elite' || params.get('active') === '1') ? 'whop' : null,
        whop_product_id: (PLAN === 'elite' || params.get('active') === '1') ? 'prod_test123' : null,
        whop_manage_url: (PLAN === 'elite' || params.get('active') === '1') ? 'https://whop.com/manage' : null,
        // ?trial=1: a running 72 h trial (migration 061 columns), 2 days left.
        // ?trial=ending: 6 h left; ?trial=ended: ended 20 h ago (trial-end summary, Session 70).
        free_trial_started_at: params.get('trial') === '1' ? new Date(now - 86400000).toISOString()
          : params.get('trial') === 'ending' ? new Date(now - 66 * 3600000).toISOString()
          : params.get('trial') === 'ended' ? new Date(now - 92 * 3600000).toISOString() : null,
        trial_ends_at: params.get('trial') === '1' ? new Date(now + 2 * 86400000).toISOString()
          : params.get('trial') === 'ending' ? new Date(now + 6 * 3600000).toISOString()
          : params.get('trial') === 'ended' ? new Date(now - 20 * 3600000).toISOString() : null,
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
  // ?badhunt=list|brands|long: the active hunt asks Vinted for several things at once (hunt words card, Session 70).
  if (params.get('badhunt')) {
    var bhq = { list: 'Ralph Lauren, Nike, Adidas', brands: 'ralph loren pull nike', long: 'jujutsu kaisen tome 20 a 30' }[params.get('badhunt')] || 'Ralph Lauren, Nike, Adidas';
    DB.user_searches.unshift({ id: 'search-bad', user_id: UID, search_name: bhq, vinted_url: 'https://www.vinted.fr/catalog?search_text=' + encodeURIComponent(bhq) + '&price_to=40&order=newest_first',
      is_active: true, push_mode: 'every', push_calm_minutes: 15, created_at: new Date(now - 86400000).toISOString() });
  }
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

  // ?pr=1: 9 fresh listings of the active seeded hunt carrying the scraper's price check (item_box.snypd_price, Session 66):
  // ratings 82, 58, -, 80, 23, -, -, 68 and one GONE listing rated 90 (never shown). Same stamp as ?broad=1.
  if (params.get('pr') === '1' && DB.user_searches[0]) {
    var u2 = new URL(DB.user_searches[0].vinted_url);
    var pairs2 = Array.from(u2.searchParams).filter(function (p) { return ['page', 'per_page', 'order', 'time', 'search_id'].indexOf(p[0]) < 0 && p[1]; }).sort();
    var sig2 = JSON.stringify([u2.hostname.toLowerCase(), u2.pathname.replace(/\/+$/, '') || '/', pairs2]);
    [[82, 12], [58, 22], [null, 14], [80, 8], [23, 45], [null, 30], [null, 6], [68, 18], [90, 5]].forEach(function (x, i) {
      var t = now - (2 + 2 * i) * min;
      var box = { snypd_filter_contract: { version: 1, search: sig2 } };
      if (x[0] != null) box.snypd_price = { p: x[0], n: 412, c: 'Very good' };
      DB.current_ads.push({
        listing_id: 7000 + i, user_id: UID, title: 'Price check QA listing ' + i,
        price: { amount: x[1], currency_code: 'EUR' }, brand_title: 'Ralph Lauren', size_title: 'M', status: 'Very good',
        url: 'https://www.vinted.fr/items/' + (7000 + i), content_source: 'search', image_url: '',
        item_box: box, 'item_box->snypd_filter_contract->>version': '1',
        fetched_at: new Date(t).toISOString(), created_at: new Date(t).toISOString(),
        uploaded_ts: Math.floor(t / 1000), uploaded_at_ts: new Date(t).toISOString(), is_visible: i !== 8, promoted: false,
      });
    });
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
  //   ?stock_pre073=1        stock_settings has no weekly_email column yet (the Settings switch must stay hidden)
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
      // Returns a real promise like supabase-js does, so builder.then(fn).catch(fn) chains work (the dashboard's
      // snypd:hunts-changed listener uses that form; before 7 Nov 2026 it threw here in the mock only).
      then: function (resolve, reject) {
        var r;
        try { r = Promise.resolve(execute()); } catch (e) { r = Promise.reject(e); }
        return r.then(resolve, reject);
      },
    };

    function execute() {
      var rows = (STOCK && table === 'stock_history') ? STOCK.state.history : (DB[table] || (DB[table] = []));   // Stock history is read-only here, like the real select-own table

      // Column defaults + CHECKs that the real DB has (migrations 043, 064), so
      // the page sees the same row shape after an insert as in production.
      var badPush = function (r) {
        return (r.push_mode !== undefined && ['every', 'calm', 'cheap'].indexOf(r.push_mode) < 0) ||
          (r.push_calm_minutes !== undefined && [15, 30].indexOf(r.push_calm_minutes) < 0);
      };
      // ?coachwrite=error: changing a hunt's link fails (hunt coach apply / undo)
      if (table === 'user_searches' && op === 'update' && payload && 'vinted_url' in payload && params.get('coachwrite') === 'error') {
        return { data: null, error: { message: 'QA mock: link change failed' } };
      }
      if (table === 'user_searches' && (op === 'insert' || op === 'update') && badPush(payload || {})) {
        return { data: null, error: { code: '23514', message: 'new row violates check constraint (push_mode / push_calm_minutes)' } };
      }
      if (STOCK && table === 'stock_settings') {   // own-row select / insert / update / upsert (policies of 065); the CHECKs live in the engine
        if (op === 'select' && params.get('stock_pre073') === '1') return { data: null, error: { code: '42703', message: 'column stock_settings.weekly_email does not exist' } };   // ?stock_pre073=1: production before 073
        if (op === 'select') { var srow = STOCK.settingsRow(); return { data: singleMode ? srow : (srow ? [srow] : []), error: null }; }
        try { var sp = Object.assign({}, payload); delete sp.user_id; STOCK.setSettings(sp); return { data: payload, error: null }; } catch (e) { return { data: null, error: e.pg || { message: String(e) } }; }
      }
      if (STOCK && table === 'stock_items' && op === 'select') rows = STOCK.state.items;   // read-only, like the real select-own table
      if (STOCK && table === 'stock_categories' && op === 'insert') {   // own-row insert policy + the 30-category trigger live in the engine
        try { STOCK.addCategories(Array.isArray(payload) ? payload : [payload]); return { data: payload, error: null }; } catch (e) { return { data: null, error: e.pg || { message: String(e) } }; }
      }
      if (STOCK && table === 'stock_categories' && op === 'update') {   // own-row update policy (065): rename / hide
        var ck = (filters.filter(function (f) { return f.col === 'key' && f.op === 'eq'; })[0] || {}).val;
        try { var cp = Object.assign({}, payload); delete cp.user_id; var cn = STOCK.updateCategories(ck, cp); return { data: null, error: null, count: cn }; } catch (e) { return { data: null, error: e.pg || { message: String(e) } }; }
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
            is_founding_member: u0.is_founding_member, founding_number: u0.founding_number, free_trial_started_at: u0.free_trial_started_at || null, trial_ends_at: u0.trial_ends_at || null, trial_extended_at: null, pass_expires_at: null },
          searches: searches, claims: (DB.user_claims || []).slice(), dq: [], xp_total: (DB.xp_events || []).reduce(function (a, x) { return a + (x.xp || 0); }, 0),
          streak: ((DB.user_streak_state || [])[0] || {}).current_streak || null, quota: { quota_limit: PLAN === 'free' ? 1 : 5, used: searches.length },
          stock_mode: STOCK ? STOCK.mode() : undefined, stock_tab_hidden: STOCK ? STOCK.tabHidden() : false,
          feedback_done: params.get('fb081') === '0' ? undefined : FB_DONE.slice(),
          // ?fbfind=<hours ago> = first find of the trial; ?fbactive=<n> = active days in the last 14 (migration 081 feedback_signals)
          feedback_signals: params.get('fb081') === '0' ? undefined : { first_find_at: params.get('fbfind') ? new Date(Date.now() - Number(params.get('fbfind')) * 36e5).toISOString() : null, active_days_14: Number(params.get('fbactive') || 0) } }, error: null });
      }
      // Feedback questions (migration 081): ?fbdone=A,B1 seeds the answered ids; ?fb081=0 = migration not applied
      // (no feedback_done key, RPC missing, the page must show nothing); ?fbrpc=error makes the save fail.
      if (name === 'feedback_submit' && params.get('fb081') !== '0') {
        window.__fbRpc = (window.__fbRpc || []).concat([args]);
        if (params.get('fbrpc') === 'error') return Promise.resolve({ data: null, error: { message: 'QA mock: feedback save failed' } });
        var fbNew = FB_DONE.indexOf(args.p_question) < 0;
        if (fbNew) FB_DONE.push(args.p_question);
        var fbXp = fbNew && !args.p_skipped && ['A', 'B1', 'C', 'D', 'E1', 'G', 'H'].indexOf(args.p_question) >= 0 ? 25 : 0;
        if (fbXp) (DB.xp_events = DB.xp_events || []).push({ event_type: 'feedback', xp: 25, meta: { question: args.p_question } });
        return Promise.resolve({ data: { saved: fbNew, xp: fbXp }, error: null });
      }
      // Stock RPCs (migrations 065-068) -> the in-memory port, see ops/stock_engine.js. Everything else keeps the old "not implemented" answer.
      if (STOCK && /^stock_/.test(name)) return stockReady.then(function () { return STOCK.rpc(name, args); });
      // Quiet hours (migration 077): own-row RPC, same effect on the users row as the SQL function.
      if (name === 'set_push_quiet_hours') {
        var qu = DB.users[0] || {};
        qu.push_quiet_hours_start = args.p_on ? 23 : null; qu.push_quiet_hours_end = args.p_on ? 8 : null; qu.push_quiet_tz = args.p_on ? args.p_tz : null;
        window.__quietRpc = (window.__quietRpc || []).concat([args]);
        return Promise.resolve({ data: null, error: null });
      }
      // Hunter statistics (migration 079): own-row switch; ?statsrpc=error makes the save fail.
      if (name === 'set_hunter_stats_opt_out') {
        window.__statsRpc = (window.__statsRpc || []).concat([args]);
        if (params.get('statsrpc') === 'error') return Promise.resolve({ data: null, error: { message: 'QA mock: save failed' } });
        (DB.users[0] || {}).hunter_stats_opt_out = !!args.p_out;
        return Promise.resolve({ data: !!args.p_out, error: null });
      }
      return Promise.resolve({ data: null, error: { message: 'QA mock: rpc not implemented, falls back to plan table' } });
    },
  };

  window.supabase = { createClient: function () { return fakeClient; } };

  // Market board fixture (Session 67): made by backend market_board.compute() + for_tier() from the frozen live dump of 5 Nov 2026
  // (9 of its 74 items; hunters = the live top counts). Regenerate with the snippet in website outreach/37 if the shape changes.
  var MB_FULL = {"asof":"2026-11-05","source":{"site":"vinted.be","pool":"EU","currency":"EUR","window_days":7},"counts":{"tracked":98,"shown":9,"rising":1,"falling":4,"mix":1},"tier":"full","items":[{"q":"adidas gazelle","name":"Adidas Gazelle","name_fr":"Adidas Gazelle","cat":"sneakers","typical_cents":3500,"low_cents":2125,"high_cents":5000,"listings":954,"sellers":900,"now_cents":3500,"before_cents":3500,"change_pct":0.0,"signal":null,"mix":false,"cut_pct":0.2,"cutting":false,"series":{"from":"2026-09-29","typical":[3000,3000,3000,3000,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3445,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3800,3500],"low":[2000,2100,2000,2000,2200,2075,2000,2000,2000,2000,2200,2000,2000,2300,2100,2000,2000,2000,2000,2000,2000,2000,2000,2000,2000,2000,2200,2050,2000,2000,2000,2200,2200,2000,2000,2000,2500,2125],"high":[5000,5000,5000,5000,5000,5000,5000,5000,5000,5050,5300,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5300,5500,5000,5000,5000,5000,5424,5000],"listings":[919,852,852,848,848,852,780,883,893,896,973,949,875,942,774,832,824,752,770,771,780,779,783,794,795,787,856,862,861,899,820,898,842,850,848,856,834,954]}},{"q":"adidas handball","name":"Adidas Handball","name_fr":"Adidas Handball","cat":"sneakers","typical_cents":4000,"low_cents":3900,"high_cents":6000,"listings":921,"sellers":523,"now_cents":4000,"before_cents":4995,"change_pct":-19.9,"signal":"falling","mix":false,"cut_pct":0.0,"cutting":false,"series":{"from":"2026-09-29","typical":[5000,5000,5500,5500,5500,5000,5000,5350,5500,5000,5000,5000,4995,5000,4800,4850,4990,5000,4500,4500,4500,4934,4800,5000,4800,5000,5000,5500,5500,5500,5000,5000,5000,4500,4000,4000,4000,4000],"low":[3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3400,3500,3400,3362,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3600,3500,3500,3900,3900,3900,4000,3900,3900,3900,3900,3900],"high":[7375,7500,7500,7600,7500,7500,7000,7500,7500,7000,7000,7000,7000,7000,7000,7000,7000,7500,7000,7000,7000,7000,7000,7500,7000,7500,7500,7500,7500,7500,7000,7000,7000,7000,6500,6500,6000,6000],"listings":[918,846,828,836,835,844,786,858,858,893,969,989,919,988,844,908,904,814,834,847,871,860,877,847,850,843,896,787,868,852,830,908,828,848,957,871,853,921]}},{"q":"bape hoodie","name":"BAPE hoodie","name_fr":"Sweat \u00e0 capuche BAPE","cat":"tops","typical_cents":10000,"low_cents":7498,"high_cents":18125,"listings":128,"sellers":104,"now_cents":11645,"before_cents":13500,"change_pct":-13.7,"signal":"falling","mix":false,"cut_pct":14.1,"cutting":false,"series":{"from":"2026-09-29","typical":[12000,12000,11500,11750,11500,12995,13950,13000,13000,14500,15000,14200,13000,13000,13000,13000,12550,13000,13000,13500,14475,null,14925,14000,13500,13500,13500,13500,12500,12000,11000,11790,12000,12000,11999,11645,11790,10000],"low":[8800,8950,8375,8600,8250,8500,9300,9200,9525,9400,9100,9000,8125,8250,8000,8000,7849,8000,8000,8500,8000,null,8000,7500,7500,7500,7500,7490,7000,7000,6500,7000,7000,7500,7000,7000,7150,7498],"high":[20000,20000,20000,20000,19500,20000,20000,20000,20000,21000,21000,21000,20750,21000,22000,22000,20750,20000,20000,20000,23875,null,23500,22000,20000,20000,20000,20000,19800,18350,16500,17000,17000,17000,17000,17675,18000,18125],"listings":[92,87,80,82,87,100,96,103,106,105,118,116,118,119,109,121,118,116,120,124,114,114,130,125,129,133,147,133,134,131,105,109,113,109,115,110,119,128]}},{"q":"carhartt double knee","name":"Carhartt Double Knee","name_fr":"Carhartt Double Knee","cat":"trousers","typical_cents":5000,"low_cents":3990,"high_cents":6600,"listings":472,"sellers":353,"now_cents":5000,"before_cents":5000,"change_pct":0.0,"signal":null,"mix":false,"cut_pct":1.7,"cutting":false,"series":{"from":"2026-09-29","typical":[5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,4999,5000,5000,4950,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000],"low":[3500,3500,3500,3500,3900,3900,3825,3900,3900,3900,3900,3900,3900,3900,3999,3900,3800,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3861,3900,3900,3980,3950,4000,4000,4000,3994,3990],"high":[6999,7000,6999,6999,7000,7000,7169,7106,7038,7500,7500,7900,7499,7000,7000,7000,7000,7000,6599,6500,6500,6500,6500,6500,6500,6500,6500,6500,7000,7000,7000,7000,6900,6575,6899,6500,6500,6600],"listings":[439,402,364,389,373,317,378,408,367,397,425,392,456,471,445,479,459,470,473,488,411,428,438,455,446,481,479,472,474,436,449,456,477,452,436,465,487,472]}},{"q":"jordan 1 travis scott olive","name":"Jordan 1 Travis Scott Olive","name_fr":"Jordan 1 Travis Scott Olive","cat":"sneakers","typical_cents":42250,"low_cents":22338,"high_cents":57125,"listings":144,"sellers":138,"now_cents":42000,"before_cents":43625,"change_pct":-3.7,"signal":null,"mix":false,"cut_pct":24.3,"cutting":true,"series":{"from":"2026-09-29","typical":[null,null,44950,45000,45000,45000,45000,45000,45000,45000,45000,45000,42750,45000,43000,44000,43000,43000,42250,45000,45000,45000,42000,42000,43500,42000,43750,44750,45000,45000,42000,40000,40000,40000,42000,42000,42000,42250],"low":[null,null,22500,25000,25000,23125,24999,22500,25000,25000,22125,22375,22000,23250,24000,24000,24375,24125,24000,24874,24874,21500,20000,20000,20000,20000,20000,20750,21250,22750,20000,20000,20000,21500,21500,23224,24499,22338],"high":[null,null,62250,63000,62000,62000,63000,60500,60000,60000,60000,60000,59500,60000,58000,59000,60000,59500,60000,60000,60000,60000,60000,60000,60000,60000,60000,60000,61500,60500,60000,60000,60000,60000,60000,60000,60000,57125],"listings":[199,189,188,183,185,190,165,188,191,192,198,200,206,207,219,223,216,222,218,220,216,183,214,220,214,219,216,216,210,176,209,206,204,203,207,203,211,144]}},{"q":"longchamp bag","name":"Longchamp bag","name_fr":"Sac Longchamp","cat":"bags","typical_cents":5500,"low_cents":3200,"high_cents":9000,"listings":159,"sellers":149,"now_cents":5500,"before_cents":7000,"change_pct":-21.4,"signal":"falling","mix":false,"cut_pct":8.8,"cutting":false,"series":{"from":"2026-09-29","typical":[6900,7000,7000,6500,6900,6725,6350,6500,6500,6500,6500,7000,null,null,null,null,null,null,null,null,7700,7500,7000,7000,7000,7200,7200,6500,6250,6900,6900,6000,6000,5900,6000,5500,5500,5500],"low":[4000,4000,4000,4000,4000,4000,4000,4000,4250,4000,4000,4300,null,null,null,null,null,null,null,null,4350,4500,4500,4500,4500,4500,4500,4000,4000,4000,3500,3500,4000,4000,3850,3500,3500,3200],"high":[9500,9750,9500,9000,9650,9125,9000,9650,9900,9850,11000,12600,null,null,null,null,null,null,null,null,12375,12000,11900,10125,10375,10700,10900,10000,10000,11000,10000,10000,10500,10500,9800,9500,9600,9000],"listings":[155,163,165,164,163,148,170,159,155,172,182,176,188,175,186,194,189,164,164,164,142,160,153,148,150,163,165,169,164,153,169,157,167,147,154,159,160,159]}},{"q":"ralph lauren polo bear","name":"Ralph Lauren Polo Bear","name_fr":"Ralph Lauren Polo Bear","cat":"tops","typical_cents":5999,"low_cents":3900,"high_cents":8990,"listings":999,"sellers":722,"now_cents":5900,"before_cents":5150,"change_pct":14.6,"signal":"rising","mix":false,"cut_pct":2.6,"cutting":false,"series":{"from":"2026-09-29","typical":[4995,4900,4999,4999,5000,5000,5000,5000,5295,5100,5290,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5000,5300,5448,5500,5000,5492,5500,5500,5500,5500,5500,5700,5700,5700,5600,5900,5999],"low":[3000,3000,3000,3000,3000,2999,3400,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3500,3740,3786,3955,3900],"high":[7500,7500,7999,8000,8000,8000,8500,8900,9000,9000,9000,9000,8900,8900,8500,8425,8000,8000,8000,8000,8000,8000,8000,8000,8022,8000,8000,8147,8500,8398,8500,8642,8990,9000,8990,9000,9000,8990],"listings":[640,607,577,618,614,597,636,649,723,712,773,731,764,839,800,840,850,859,926,886,878,919,916,912,952,948,1030,1030,1066,1091,1043,1100,1055,1000,1019,943,922,999]}},{"q":"stone island sweater","name":"Stone Island jumper","name_fr":"Pull Stone Island","cat":"tops","typical_cents":8000,"low_cents":5000,"high_cents":10050,"listings":151,"sellers":115,"now_cents":8000,"before_cents":5000,"change_pct":60.0,"signal":null,"mix":true,"cut_pct":0.7,"cutting":false,"series":{"from":"2026-09-29","typical":[8000,8000,8000,8000,7500,7500,7500,7500,7500,7500,7500,7248,7248,7498,7500,7000,6000,5000,5000,4900,4700,4700,4700,4800,5000,5000,6000,6824,7499,7000,7000,6999,6750,7000,7500,7500,8000,8000],"low":[6000,5999,6000,6000,5500,4999,5000,4996,4971,4900,4971,4996,4998,4999,5000,4800,4400,4000,4000,3788,3712,3500,3500,3800,3800,4000,4000,4500,4990,4500,4500,4750,4500,4688,4950,5000,5000,5000],"high":[11999,11999,11999,11999,11900,10575,11000,11000,10525,10500,10996,10000,10000,9999,10000,10000,9500,9000,8950,8000,7896,7500,7500,8000,8500,9500,9972,9792,10000,9890,9500,9500,8999,9992,9990,10000,10000,10050],"listings":[156,141,149,148,145,146,143,146,152,169,164,150,156,156,144,177,193,226,251,276,282,317,288,253,221,205,178,170,141,129,136,129,123,132,137,140,145,151]}},{"q":"stussy tee","name":"Stussy T-shirt","name_fr":"T-shirt Stussy","cat":"tops","typical_cents":2000,"low_cents":1500,"high_cents":3350,"listings":128,"sellers":113,"now_cents":2000,"before_cents":2500,"change_pct":-20.0,"signal":"falling","mix":false,"cut_pct":3.1,"cutting":false,"series":{"from":"2026-09-29","typical":[2500,2500,2500,2500,2500,2500,2500,2500,2300,2000,2000,2500,2500,2000,2000,2000,2000,2000,2200,2100,2500,2500,2500,2500,2500,2500,2500,2500,2400,2300,2350,2499,2300,2000,2000,2000,2000,2000],"low":[1900,1975,1800,1800,1776,1800,1850,1800,1785,1750,1750,1500,1500,1500,1500,1500,1500,1600,1600,1500,1500,1600,1500,1500,1599,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500],"high":[3500,3500,3500,3500,3499,3424,3500,3500,3500,3500,3500,3500,3500,3500,3200,3000,3000,3000,3100,3137,3274,3500,3499,3745,3500,3500,3500,3474,3499,3474,3425,3499,3000,3000,3000,3000,3200,3350],"listings":[141,132,112,105,112,114,118,116,117,121,137,129,117,139,128,135,134,133,129,136,147,149,153,159,177,157,169,154,141,134,120,125,117,112,118,116,113,128]}}],"rising":["ralph lauren polo bear"],"falling":["longchamp bag","stussy tee","adidas handball","bape hoodie"],"hunters":[{"brand":"Nike","hunters":122},{"brand":"Ralph Lauren","hunters":96},{"brand":"Stone Island","hunters":20},{"brand":"Adidas","hunters":17},{"brand":"Levi's","hunters":5}]};
  var MB_TEASER = {"asof":"2026-11-05","source":{"site":"vinted.be","pool":"EU","currency":"EUR","window_days":7},"counts":{"tracked":98,"shown":9,"rising":1,"falling":4,"mix":1},"tier":"teaser","items":[{"q":"ralph lauren polo bear","name":"Ralph Lauren Polo Bear","name_fr":"Ralph Lauren Polo Bear","cat":"tops","typical_cents":5999,"change_pct":14.6,"signal":"rising","cutting":false},{"q":"longchamp bag","name":"Longchamp bag","name_fr":"Sac Longchamp","cat":"bags","typical_cents":5500,"change_pct":-21.4,"signal":"falling","cutting":false}],"rising":["ralph lauren polo bear"],"falling":["longchamp bag"]};
  // ?mbsite=uk: the account's first hunt is on vinted.co.uk (Market board: no EUR maximum is filled in for a non-euro site)
  if (params.get('mbsite') === 'uk' && DB.user_searches && DB.user_searches[0]) { DB.user_searches[0].vinted_url = DB.user_searches[0].vinted_url.replace('www.vinted.be', 'www.vinted.co.uk'); }
  // Hunt coach (7 Nov 2026, website outreach/41): ?coach=busy | peers | quiet | widen | minblock | stale | error; none by
  // default so other suites never see the card. Advice points at the first hunt (search-1) and its exact link.
  window.__qaDB = DB;   // tests read what the page wrote
  var COACH = params.get('coach');
  if ((COACH === 'quiet' || COACH === 'quiethours') && DB.user_searches && DB.user_searches[0]) DB.user_searches[0].vinted_url += '&price_to=8';
  // ?coach=quietlist: the hunt asks Vinted for a list (hunt-words card's job; the coach must stay silent)
  if (COACH === 'quietlist' && DB.user_searches && DB.user_searches[0]) DB.user_searches[0].vinted_url = 'https://www.vinted.be/catalog?search_text=ralph%20lauren%2C%20nike%2C%20adidas';
  if (COACH === 'minblock' && DB.user_searches && DB.user_searches[0]) DB.user_searches[0].vinted_url += '&price_from=30';
  if (params.get('statsout') === '1' && DB.users && DB.users[0]) DB.users[0].hunter_stats_opt_out = true;
  function coachBody() {
    var h = (DB.user_searches || [])[0];
    if (!h || !COACH || COACH === 'none') return { generated_at: '2026-11-07T12:00:00Z', hunts: [], cached: false };
    var base = { id: h.id, name: 'jordan <b>travis</b>', url: h.vinted_url, site: 'vinted.be', currency: 'EUR', current_max: null, current_min: null };
    var peers = { kind: 'jordan', en: 'Jordan', fr: 'Jordan', hunters: 9, typical_max: 30 };
    var a;
    if (COACH === 'busy' || COACH === 'minblock') a = Object.assign(base, { verdict: 'busy', per_day: 2400, per_day_lower_bound: false, peers: peers, suggest: { max: 25, keeps_pct: 26, per_day: 624, source: 'own' } });
    if (COACH === 'stale') a = Object.assign(base, { url: h.vinted_url + '&old=1', verdict: 'busy', per_day: 2400, per_day_lower_bound: false, peers: null, suggest: { max: 25, keeps_pct: 26, per_day: 624, source: 'own' } });
    if (COACH === 'peers') a = Object.assign(base, { verdict: 'busy', per_day: 4517, per_day_lower_bound: true, peers: Object.assign({}, peers, { typical_max: 20 }), suggest: { max: 20, source: 'peers' } });
    if (COACH === 'quiet') a = Object.assign(base, { verdict: 'quiet', finds: 1, days: 3, current_max: 8, peers: Object.assign({}, peers, { typical_max: 20 }), suggest: { max: 20, source: 'peers' } });
    if (COACH === 'widen') a = Object.assign(base, { verdict: 'quiet', finds: 0, days: 4, peers: null, suggest: null });
    if (COACH === 'quiethours') a = Object.assign(base, { verdict: 'quiet', finds: 0, hours: 21, days: 1, current_max: 8, peers: Object.assign({}, peers, { typical_max: 20 }), suggest: { max: 20, source: 'peers' } });
    if (COACH === 'quietlist') a = Object.assign(base, { verdict: 'quiet', finds: 0, hours: 40, days: 2, peers: null, suggest: null });
    return { generated_at: '2026-11-07T12:00:00Z', hunts: a ? [a] : [], cached: false };
  }
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
    if (u.indexOf('/api/v1/push/subscribe') !== -1 || u.indexOf('/api/v1/push/unsubscribe') !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    if (u.indexOf('/api/v1/push/status') !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ status: 'ready', ready: true }), { status: 200 }));
    }
    if (u.indexOf('/api/v1/hunt-coach') !== -1) {
      window.__coachRequests = (window.__coachRequests || 0) + 1;
      if (COACH === 'error') return Promise.resolve(new Response(JSON.stringify({ detail: 'could not check your hunts right now' }), { status: 503 }));
      return Promise.resolve(new Response(JSON.stringify(coachBody()), { status: 200 }));
    }
    // Market board (Session 67): ?mb=full | teaser | empty | error, else full for elite / pro / a running trial (?trial=1), teaser otherwise
    if (u.indexOf('/api/v1/market-board') !== -1) {
      var mbq = new URLSearchParams(location.search).get('mb');
      if (mbq === 'error') return Promise.resolve(new Response(JSON.stringify({ detail: 'could not load the market board right now' }), { status: 503 }));
      var mbFull = mbq === 'full' || (mbq !== 'teaser' && (PLAN === 'elite' || PLAN === 'pro' || params.get('trial') === '1'));
      var mbBody = JSON.parse(JSON.stringify(mbFull ? MB_FULL : MB_TEASER));
      if (mbq === 'empty') {
        mbBody.rising = []; mbBody.falling = [];
        mbBody.items = mbBody.items.filter(function (i) { return !i.signal; }).map(function (i) { return Object.assign(i, { signal: null }); });
        if (!mbFull) mbBody.items = [];
      }
      window.__mbRequests = (window.__mbRequests || 0) + 1;
      return Promise.resolve(new Response(JSON.stringify(mbBody), { status: 200 }));
    }
    // Weekly hunt report (Session 66 P6): ?hr=teaser | empty | error, else the full report for paid/trial plans
    if (u.indexOf('/api/v1/hunt-report') !== -1) {
      var hrq = new URLSearchParams(location.search).get('hr');
      window.__hrRequests = (window.__hrRequests || 0) + 1;
      if (hrq === 'error') return Promise.resolve(new Response(JSON.stringify({ detail: 'could not build your report right now' }), { status: 503 }));
      var hrBase = { days: 7, since: '2026-11-12', until: '2026-11-18', generated_at: '2026-11-18T15:00:00Z', cached: false };
      // Trial-end summary (Session 70): ?trial=ending|ended adds trial_recap like the backend's window does;
      // ?tr=noprice | busy | gbp | noname | smallgap | none vary it.
      var trq = new URLSearchParams(location.search).get('tr'), trw = params.get('trial');
      if ((trw === 'ending' || trw === 'ended') && trq !== 'none') {
        var rcp = { hunt_name: trq === 'noname' ? 'Vinted search' : 'nike <i>running</i>', site: trq === 'gbp' ? 'vinted.co.uk' : 'vinted.fr',
          currency: trq === 'gbp' ? 'GBP' : 'EUR', days: 4, since: '20261104', finds: trq === 'busy' ? 14108 : 1892, busy: trq === 'busy',
          trial_ends_at: '2026-11-07T21:30:00Z',
          price: trq === 'noprice' ? null : { condition: trq === 'noname' ? 'Other condition' : 'Very good', condition_raw: 'Tres bon etat', finds: 940,
            typical_cents: trq === 'smallgap' ? 3300 : 4900, low_cents: trq === 'smallgap' ? 3150 : 3050 } };
        hrBase.trial_recap = rcp;
      }
      if (hrq === 'teaser' || (PLAN !== 'elite' && PLAN !== 'pro' && hrq !== 'full')) {
        return Promise.resolve(new Response(JSON.stringify(Object.assign({ tier: 'teaser', teaser: { finds: 288, hunts: 3, cheapest_cents: 900, currency: 'EUR', hunt_name: 'carhartt' } }, hrBase)), { status: 200 }));
      }
      if (hrq === 'empty') return Promise.resolve(new Response(JSON.stringify(Object.assign({ tier: 'full', hunts: [] }, hrBase)), { status: 200 }));
      return Promise.resolve(new Response(JSON.stringify(Object.assign({ tier: 'full', hunts: [
        { id: 'h1', name: 'carhartt', site: 'vinted.fr', currency: 'EUR', finds: 213, finds_before: 140, finds_change_pct: 52,
          cheapest: { price_cents: 900, condition: 'Good', listing_id: '10300009001', url: 'https://www.vinted.fr/items/10300009001' },
          conditions: [
            { condition: 'Very good', finds: 210, finds_before: 140, status: 'ok', typical_cents: 2750, low_cents: 1950, high_cents: 3300, typical_change_pct: 8 },
            { condition: 'Good', finds: 3, finds_before: null, status: 'few', typical_cents: null, low_cents: null, high_cents: null, typical_change_pct: null }] },
        { id: 'h2', name: 'barbour <b>wax</b>', site: 'vinted.co.uk', currency: 'GBP', finds: 75, finds_before: null, finds_change_pct: null,
          cheapest: { price_cents: 100, condition: 'Muy bueno', listing_id: 'x' },
          conditions: [{ condition: 'Muy bueno', finds: 40, status: 'mixed', typical_cents: null, typical_change_pct: null },
                       { condition: 'Other condition', finds: 35, status: 'ok', typical_cents: 2000, low_cents: 2000, high_cents: 2000, typical_change_pct: null }] },
        { id: 'h3', name: 'lego', site: 'vinted.pl', currency: 'PLN', finds: 0, finds_before: null, finds_change_pct: null, cheapest: null, conditions: [] }] }, hrBase)), { status: 200 }));
    }
    if (u.indexOf('/api/v1/market/snapshot') !== -1) {
      var body = {};
      try { body = JSON.parse(opts && opts.body || '{}'); } catch (e) {}
      var q = (body.q || '').toLowerCase();

      // Trial price checks (11 Nov 2026): ?plan=free&trial=1 gets 10 checks in total, like the backend
      // (market_trial.py). ?trial_used=N starts the count at N. A found price uses one; 'zzz_nomatch' is handed back.
      if (PLAN === 'free' && params.get('trial') === '1') {
        if (window.__mrTrialUsed == null) { window.__mrTrialUsed = Math.max(0, parseInt(params.get('trial_used') || '0', 10) || 0); }
        if (window.__mrTrialUsed >= 10) {
          return Promise.resolve(new Response(JSON.stringify({ detail: { error: 'trial_checks_used',
            message: 'You have used your 10 trial price checks. Price checks are part of Pro and Elite.',
            trial: { used: 10, limit: 10, remaining: 0 } } }), { status: 403 }));
        }
        var trUseful = q.indexOf('zzz_nomatch') === -1;
        if (trUseful) { window.__mrTrialUsed += 1; }
        var trSum = { used: window.__mrTrialUsed, limit: 10, remaining: 10 - window.__mrTrialUsed };
        return Promise.resolve(new Response(JSON.stringify(trUseful ? {
          query: q, sample_size: 240, distinct_sellers: 180, display_verdict: 'ok', confidence: 'high', provisional: false,
          show_headline: true, typical_cents: 8500, range_cents: { low: 6500, high: 11000 }, by_condition: [], flags: [],
          source: { site: 'vinted.be', market: 'EU', currency: 'EUR', window_days: 14 },
          quota: { hour_remaining: 19, hour_limit: 20 }, trial: trSum
        } : {
          query: q, sample_size: 0, display_verdict: 'too_thin', show_headline: false, flags: [],
          quota: { hour_remaining: 19, hour_limit: 20 }, trial: trSum
        }), { status: 200 }));
      }
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
      // 11 Nov 2026: 'trackq' = nothing found but tracking started; 'medq' = an ok price with a warning (confidence medium).
      if (q.indexOf('trackq') !== -1) {
        return Promise.resolve(new Response(JSON.stringify({
          query: q, sample_size: 0, display_verdict: 'too_thin', show_headline: false, tracking: { tracked: true, reason: 'registered' },
          quota: { hour_remaining: 19, hour_limit: 20 },
        }), { status: 200 }));
      }
      if (q.indexOf('medq') !== -1) {
        return Promise.resolve(new Response(JSON.stringify({
          query: q, sample_size: 900, distinct_sellers: 400, display_verdict: 'ok', confidence: 'medium', provisional: false,
          show_headline: true, typical_cents: 12900, range_cents: { low: 9000, high: 18000 }, by_condition: [],
          flags: [{ code: 'price_skew_high', message: 'Prices here skew heavily to the high side.' }],
          quota: { hour_remaining: 19, hour_limit: 20 },
        }), { status: 200 }));
      }
      // Forgiving search (Session 66): the backend says what it compared on and what it ignored. Mirrors the
      // real shape for "size N" queries, "keep" (add back) and one "Try without" case (q containing "travis").
      var mkWords = q.split(/\s+/).filter(Boolean), mkIgn = [], mkOn = [], mkKeep = (body.keep || []).map(function (k) { return String(k).toLowerCase(); });
      for (var mi = 0; mi < mkWords.length; mi++) {
        var mw = mkWords[mi].replace(/[^a-z0-9]/g, '');
        if (!mw) continue;
        if (mkKeep.indexOf(mw) === -1 && (mw === 'size' || (mi > 0 && mkWords[mi - 1] === 'size') || mw === 'black')) mkIgn.push({ word: mw, why: mw === 'black' ? 'colour' : 'size' });
        else mkOn.push(mw);
      }
      if (mkOn.indexOf('tahari') !== -1) { mkOn = mkOn.filter(function (w) { return w !== 'tahari'; }); mkIgn.push({ word: 'tahari', why: 'not_found' }); }
      var mkThinDrop = q.indexOf('p-6000') !== -1 ? ['6000'] : [];
      var mkSearch = { compared_on: mkOn, ignored: mkIgn, offer_drop: q.indexOf('travis') !== -1 ? ['travis'] : mkThinDrop, pinned: mkKeep };
      var mkSource = { site: 'vinted.be', market: 'EU', currency: 'EUR', window_days: 14 };
      // review checks: 'slowq' answers late (two quick taps), 'thinq' is a provisional price (few listings)
      if (q.indexOf('slowq') !== -1) {
        return new Promise(function (res) { setTimeout(function () { res(new Response(JSON.stringify({
          query: q, search: mkSearch, source: mkSource, sample_size: 300, display_verdict: 'ok', provisional: false, show_headline: true,
          typical_cents: 99900, range_cents: { low: 90000, high: 110000 }, by_condition: [], quota: { hour_remaining: 16, hour_limit: 20 },
        }), { status: 200 })); }, 1200); });
      }
      if (q.indexOf('thinq') !== -1) {
        return Promise.resolve(new Response(JSON.stringify({
          query: q, search: mkSearch, source: mkSource, sample_size: 5, display_verdict: 'too_thin', provisional: true, show_headline: true,
          typical_cents: 3000, range_cents: { low: 2500, high: 3500 }, by_condition: [], quota: { hour_remaining: 16, hour_limit: 20 },
        }), { status: 200 }));
      }
      if (q.indexOf('travis') !== -1 || mkThinDrop.length) {
        return Promise.resolve(new Response(JSON.stringify({
          query: q, sample_size: 1, display_verdict: 'too_thin', show_headline: false, search: mkSearch, source: mkSource, quota: { hour_remaining: 18, hour_limit: 20 },
        }), { status: 200 }));
      }
      // Default: a normal, trustworthy result. typical_cents is deliberately
      // NOT a round number (EUR273.70) - this is the exact shape that caught
      // Market Insights' own eur() rounding bug (Session 17): a round number
      // like 4500 would pass even with that bug still present.
      return Promise.resolve(new Response(JSON.stringify({
        query: mkOn.join(' ') || 'jordan 1 mid', search: mkSearch, source: mkSource, sample_size: 5399, distinct_sellers: 812,
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
