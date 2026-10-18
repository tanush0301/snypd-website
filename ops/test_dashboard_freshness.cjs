const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');
let scripts = 0;
for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) {
  if (match[1].trim()) {
    new vm.Script(match[1]);
    scripts++;
  }
}

function section(start, end) {
  const from = html.indexOf(start);
  const to = html.indexOf(end, from);
  assert(from >= 0 && to > from, `Missing source section: ${start}`);
  return html.slice(from, to);
}

const now = Date.now();
const minutesAgo = n => new Date(now - n * 60000).toISOString();
const context = vm.createContext({
  Date, Intl, URL, console, Set, navigator: { standalone: false },
  DASHBOARD_MAX_AGE_MIN: 30,
  claimedIds: new Set(),
  firstSeenPriceByListing: new Map(),
  derivePrice: () => ({ amount: 50, currency: 'EUR' }),
  fmtPrice: () => 'EUR 50',
  deriveTotalPrice: () => null,
  getImageUrl: () => '',
  esc: value => String(value ?? ''),
  relativeTime: () => '2m ago',
});
vm.runInContext(section('  function knownUploadTimeMs(', '  // -------- helpers for mapping'), context);
vm.runInContext(section('  function vintedListingUrl(', '  // E3:'), context);

const recent = { listing_id: 1, title: 'Jordan 4', created_at: minutesAgo(2),
  fetched_at: minutesAgo(0), uploaded_at_ts: null, uploaded_ts: null };
const stale = { ...recent, created_at: minutesAgo(90) };
const known = { ...recent, uploaded_at_ts: minutesAgo(5) };
assert.equal(context.isFreshListing(recent), true);
assert.equal(context.isFreshListing(stale), false, 'Refetching must not renew first-seen age');
assert.equal(context.isFreshListing({ ...recent, uploaded_at_ts: minutesAgo(90) }), false);
assert.equal(context.isFreshListing(known), true);
assert.equal(context.knownUploadTimeMs({ uploaded_ts: Math.floor(now / 1000) }),
  Math.floor(now / 1000) * 1000);
assert.equal(context.uploadedTimeMs(recent), Date.parse(recent.created_at));
assert(context.sortNewestUploadedFirst(recent, stale) < 0);
context.row = recent;
let card = vm.runInContext('cardHTML(row)', context);
assert(card.includes('First seen by SNYPD at '));
assert(card.includes('Seen 2m ago'));
assert(!card.includes('card-badge--new'));
assert(card.includes('href="https://www.vinted.be/items/1"'));
assert.equal(context.vintedListingUrl({ listing_id: 1, url: '/items/1-jordan' }),
  'https://www.vinted.be/items/1-jordan');
assert.equal(context.vintedListingUrl({ listing_id: 1, url: 'https://www.vinted.fr/items/1' }),
  'https://www.vinted.fr/items/1');
assert.equal(context.vintedListingUrl({ listing_id: 1, url: 'javascript:alert(1)' }),
  'https://www.vinted.be/items/1');
assert.equal(context.vintedListingUrl({ listing_id: 1, url: '//example.com/items/1' }),
  'https://www.vinted.be/items/1');
for (const url of ['https://vinted.evil.tld/items/1', 'https://www.vinted.be.evil.tld/items/1',
  'https://user:password@www.vinted.be/items/1', 'https://www.vinted.be/member/signup']) {
  assert.equal(context.vintedListingUrl({ listing_id: 1, url }), 'https://www.vinted.be/items/1');
}
assert.equal(context.vintedLinkTarget(), '_blank');
context.navigator.standalone = true;
assert.equal(context.vintedLinkTarget(), '_self');
assert(vm.runInContext('cardHTML(row)', context).includes('target="_self"'));
context.navigator.standalone = false;
const hunt = 'https://www.vinted.be/catalog?search_text=jordan&price_from=150&currency=EUR&size_ids[]=784';
const signature = context.savedSearchSignature(hunt);
assert.equal(signature, context.savedSearchSignature(hunt + '&time=123&search_id=5&order=newest_first'));
const active = new Set([signature]);
assert.equal(context.matchesActiveSearch({}, active), false, 'Legacy rows must not reach the feed');
assert.equal(context.matchesActiveSearch({ item_box: { snypd_filter_contract: {
  version: 1, search: signature } } }, active), true);
assert.equal(context.matchesActiveSearch({ item_box: { snypd_filter_contract: {
  version: 1, search: signature } } }, new Set()), false, 'Paused/deleted searches must not match');
context.row = known;
card = vm.runInContext('cardHTML(row)', context);
assert(card.includes('Uploaded on Vinted at '));
assert(card.includes('card-badge--new'));

const calls = [];
// adsQuery(columns, ids): the legacy REST fallback's full-row read (the feed
// itself is the dashboard_feed RPC since 18 Oct 2026). Hard 30-minute gate on
// uploaded_at_ts only -- no created_at fallback (fail-closed, see the source).
const builder = Object.fromEntries(['select', 'in', 'eq', 'gte', 'or', 'order', 'limit'].map(method =>
  [method, (...args) => { calls.push([method, ...args]); return builder; }]));
context.sb = { from: table => { assert.equal(table, 'current_ads'); return builder; } };
context.uid = 'test-user';
context.cutoffIso = minutesAgo(30);
vm.runInContext(section('      function adsQuery(', '      // is_suspicious'), context);
context.adsQuery('listing_id', [1, 2]);
assert(calls.some(c => c[0] === 'in' && c[1] === 'listing_id' && c[2].join() === '1,2'));
assert(calls.some(c => c[0] === 'eq' && c[1] === 'user_id' && c[2] === 'test-user'));
assert(calls.some(c => c[0] === 'eq' && c[1] === 'item_box->snypd_filter_contract->>version' && c[2] === '1'));
assert(calls.some(c => c[0] === 'gte' && c[1] === 'uploaded_at_ts' && c[2] === context.cutoffIso));
assert(!calls.some(c => c[0] === 'or'), 'created_at must not let an old upload pass as fresh');
console.log(`PASS: ${scripts} inline scripts parse; timestamp fallbacks, stale rows, labels, badges, ordering and user-scoped query.`);
