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
  Date, Intl, URL, console,
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
context.row = known;
card = vm.runInContext('cardHTML(row)', context);
assert(card.includes('Uploaded on Vinted at '));
assert(card.includes('card-badge--new'));

const calls = [];
const builder = Object.fromEntries(['select', 'eq', 'or', 'order', 'limit'].map(method =>
  [method, (...args) => { calls.push([method, ...args]); return builder; }]));
context.sb = { from: table => { assert.equal(table, 'current_ads'); return builder; } };
context.uid = 'test-user';
context.cutoffIso = minutesAgo(30);
vm.runInContext(section('      function adsQuery(', '      // is_suspicious'), context);
context.adsQuery('listing_id');
assert(calls.some(c => c[0] === 'eq' && c[1] === 'user_id' && c[2] === 'test-user'));
assert(calls.some(c => c[0] === 'or' && c[1] ===
  `uploaded_at_ts.gte.${context.cutoffIso},and(uploaded_at_ts.is.null,created_at.gte.${context.cutoffIso})`));
assert(calls.some(c => c[0] === 'limit' && c[1] === 80));
console.log(`PASS: ${scripts} inline scripts parse; timestamp fallbacks, stale rows, labels, badges, ordering and user-scoped query.`);
