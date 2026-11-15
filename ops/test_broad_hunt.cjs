/* Runs the real dashboard broad-hunt notice (Phase 1, 20 Oct 2026) against stubbed feed results.
 * No network, no browser. Run: node ops/test_broad_hunt.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');
function section(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert(a >= 0 && b > a, 'section not found: ' + start);
  return html.slice(a, b);
}
const sigFn = section('  function savedSearchSignature(value) {', '  function matchesActiveSearch(');
const broad = section('  const BROAD_PER_30MIN = ', '  async function loadAds() {');

// A tiny stand-in for the page: elements keep child text (the card paints one span per sentence), clicks return the
// handlers' promises, and every user_searches update is recorded (failIds: ids whose update fails).
function fixture(store = {}, modeRows = [], failIds = []) {
  const els = {};
  const mk = id => ({ id, style: { display: 'none' }, dataset: {}, _t: '', children: [], listeners: {}, disabled: false,
    get textContent() { return this.children.length ? this.children.map(c => c.textContent).join('') : this._t; },
    set textContent(v) { this._t = String(v); this.children = []; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(t, cb) { (this.listeners[t] ||= []).push(cb); },
    click() { return Promise.all((this.listeners.click || []).map(cb => cb())); } });
  const el = id => (els[id] ||= mk(id));
  const writes = [];
  const sb = { from: t => ({
    select: () => ({ eq: async () => ({ data: modeRows, error: null }) }),
    update: patch => ({ eq: (c1, v1) => ({ eq: async (c2, v2) => {
      writes.push({ t, patch, id: v1, user: v2 });
      if (failIds.includes(v1)) return { error: { message: 'stub: update failed' } };
      const r = modeRows.find(x => x.id === v1); if (r) Object.assign(r, patch);
      return { error: null };
    } }) }),
  }) };
  const g = { sb, uid: 'test-account',
    console, URL, JSON, Math, Map, Set, Date, document: { getElementById: el, createElement: () => mk(), createTextNode: t => ({ textContent: String(t) }) },
    localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } },
    fmtMoney: (n, c) => (c === 'GBP' ? 'GBP ' : 'EUR ') + n,
    setTimeout: () => 0, clearTimeout: () => {}, Event: class { constructor(type) { this.type = type; } }, dispatchEvent: () => true };
  g.window = g;
  const ctx = vm.createContext(g);
  vm.runInContext(sigFn + '\n' + broad + '\n;globalThis.noteBroadHunt = noteBroadHunt; globalThis.savedSearchSignature = savedSearchSignature;', ctx);
  return { g, el, store, writes };
}
const RL = 'https://www.vinted.fr/catalog?search_text=ralph+lauren&order=newest_first';
const PS5 = 'https://www.vinted.fr/catalog?search_text=ps5&price_to=250';
function feed(g, eligible, perHunt) {
  const rows = [];
  for (const [url, n] of perHunt) {
    const sig = g.savedSearchSignature(url);
    for (let i = 0; i < n; i++) rows.push({ item_box: { snypd_filter_contract: { version: 1, search: sig } } });
  }
  return { rows, eligibleCount: eligible, activeSearches: new Set(perHunt.map(([u]) => g.savedSearchSignature(u))), huntUrls: perHunt.map(([u]) => u) };
}
let passed = 0;

// 1. One broad hunt: 60 eligible in 30 min -> notice with ~120/hour and the hunt's words.
(async () => {
let f = fixture();
await f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
assert.equal(f.el('broad-hunt').style.display, '');
assert.match(f.el('broad-hunt-text').textContent, /^About 120 new listings an hour match "ralph lauren": /);
passed++;

// 2. A quiet hunt: 10 in 30 min -> nothing.
f = fixture();
await f.g.noteBroadHunt(feed(f.g, 10, [[PS5, 10]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 3. Two hunts, the feed shows only a sample (60 of 200): the broad one is named, its share scaled.
f = fixture();
await f.g.noteBroadHunt(feed(f.g, 200, [[RL, 57], [PS5, 3]]));
assert.match(f.el('broad-hunt-text').textContent, /^About 380 new listings an hour match "ralph lauren"/);
passed++;

// 4. Two hunts where neither reaches the threshold on its own share -> nothing.
f = fixture();
await f.g.noteBroadHunt(feed(f.g, 30, [[RL, 15], [PS5, 15]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 5. "Keep it" remembers this hunt on this device; the next feed refresh shows nothing.
f = fixture();
// the wiring IIFE ran at load with the same element objects
await f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
f.el('broad-hunt-keep').click();
assert.equal(f.el('broad-hunt').style.display, 'none');
assert(JSON.parse(f.store.snypd_broad_ok)[f.g.savedSearchSignature(RL)]);
await f.g.noteBroadHunt(feed(f.g, 80, [[RL, 60]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 6. "Edit hunt" opens the Filters sheet and hides the notice.
f = fixture();
let opened = 0;
f.el('filter-pill').addEventListener('click', () => { opened++; });
await f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
f.el('broad-hunt-edit').click();
assert.equal(opened, 1);
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 7. Rows from paused/deleted hunts (not active) are ignored; empty feeds never throw.
f = fixture();
const other = feed(f.g, 60, [[RL, 60]]);
other.activeSearches = new Set();
await f.g.noteBroadHunt(other);
await f.g.noteBroadHunt({ rows: [], eligibleCount: 0, activeSearches: new Set() });
await f.g.noteBroadHunt(null);
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 8. A hunt already in Calm never shows the broad-hunt notice.
f = fixture({}, [{id:'calm-hunt',is_active:true,vinted_url:RL,push_mode:'calm'}]);
await f.g.noteBroadHunt(feed(f.g,60,[[RL,60]]));
assert.equal(f.el('broad-hunt').style.display,'none'); passed++;

// 8b. A cheap-only hunt (migration 074) already pushes little: no broad-hunt notice either.
f = fixture({}, [{id:'cheap-hunt',is_active:true,vinted_url:RL,push_mode:'cheap'}]);
await f.g.noteBroadHunt(feed(f.g,60,[[RL,60]]));
assert.equal(f.el('broad-hunt').style.display,'none'); passed++;

// 9. A known every-match hunt offers the Calm action.
f = fixture({}, [{id:'every-hunt',is_active:true,vinted_url:RL,push_mode:'every'}]);
await f.g.noteBroadHunt(feed(f.g,60,[[RL,60]]));
assert.equal(f.el('broad-hunt').style.display,'');
assert.equal(f.el('broad-hunt-calm').style.display,''); passed++;

// ----- website outreach/62 move 3: a max price from the hunt's own matches, Calm all, Keep it on a suggestion
function pricedFeed(g, eligible, perHunt) {
  const rows = [];
  for (const [url, n, from, cur] of perHunt) {
    const sig = g.savedSearchSignature(url);
    for (let i = 0; i < n; i++) rows.push({ item_box: { snypd_filter_contract: { version: 1, search: sig } }, price: from == null ? null : { amount: from + i, currency_code: cur || 'EUR' } });
  }
  return { rows, eligibleCount: eligible, activeSearches: new Set(perHunt.map(([u]) => g.savedSearchSignature(u))), huntUrls: perHunt.map(([u]) => u) };
}
const NIKE = 'https://www.vinted.co.uk/catalog?search_text=nike&order=newest_first';
const shown = (f, id) => f.el(id).style.display !== 'none';

// 10. Busy every-match hunt with priced matches: the cheapest quarter's price is offered as a max; Edit makes room.
f = fixture({}, [{ id: 'h-rl', is_active: true, vinted_url: RL, push_mode: 'every' }]);
await f.g.noteBroadHunt(pricedFeed(f.g, 60, [[RL, 60, 10]]));   // prices 10..69: quarter at 24
assert.equal(shown(f, 'broad-hunt'), true);
assert.equal(f.el('broad-hunt-apply').textContent, 'Set max EUR 24');
assert.equal(shown(f, 'broad-hunt-apply'), true); assert.equal(shown(f, 'broad-hunt-edit'), false);
assert.equal(shown(f, 'broad-hunt-calm'), true); assert.equal(shown(f, 'broad-hunt-calmall'), false);
assert.equal(f.el('broad-hunt-text').textContent, 'About 120 new listings an hour match "ralph lauren": more than anyone can open. A max price of EUR 24 keeps the cheapest quarter of them. Or switch to Calm: at most one summary every 15 min.');
assert.equal(f.el('broad-hunt').dataset.kind, 'broad');
passed++;

// 11. Set max writes the hunt's own link with price_to through the coach's apply; Undo restores it.
await f.el('broad-hunt-apply').click();
assert.equal(f.writes.length, 1);
assert.equal(f.writes[0].id, 'h-rl'); assert.equal(f.writes[0].user, 'test-account');
assert.equal(f.writes[0].patch.vinted_url, RL + '&price_to=24');
assert.match(f.el('broad-hunt-text').textContent, /Done: "ralph lauren" now has a max price of EUR 24\./);
assert.equal(shown(f, 'broad-hunt-undo'), true);
await f.el('broad-hunt-undo').onclick();
assert.equal(f.writes[1].patch.vinted_url, RL);
passed++;

// 12-14. No suggestion when the link's max is already at or below the quarter, the minimum is at or above it, or fewer than 8 prices.
for (const [url, rows, why] of [[RL + '&price_to=20', 60, 'max already lower'], [RL + '&price_from=30', 60, 'minimum above'], [RL, 7, 'too few prices']]) {
  f = fixture({}, [{ id: 'h', is_active: true, vinted_url: url, push_mode: 'every' }]);
  await f.g.noteBroadHunt(pricedFeed(f.g, 60, [[url, rows, 10]]));
  assert.equal(shown(f, 'broad-hunt'), true, why);
  assert.equal(shown(f, 'broad-hunt-apply'), false, why);
  assert.equal(shown(f, 'broad-hunt-edit'), true, why);
  assert.doesNotMatch(f.el('broad-hunt-text').textContent, /A max price of/, why);
  passed++;
}

// 15. Two busy every-match hunts: Calm all 2, the count is said.
const two = () => fixture({}, [{ id: 'h-rl', is_active: true, vinted_url: RL, push_mode: 'every' }, { id: 'h-nike', is_active: true, vinted_url: NIKE, push_mode: 'every' }]);
f = two();
await f.g.noteBroadHunt(pricedFeed(f.g, 220, [[RL, 60, 10], [NIKE, 50, 5, 'GBP']]));
assert.equal(shown(f, 'broad-hunt-calmall'), true);
assert.equal(f.el('broad-hunt-calmall').textContent, 'Calm all 2');
assert.match(f.el('broad-hunt-text').textContent, / 2 of your hunts are this busy\.$/);
passed++;

// 16. Calm all switches both, remembers both, and says so.
await f.el('broad-hunt-calmall').click();
assert.deepEqual(f.writes.map(w => [w.id, w.patch.push_mode, w.patch.push_calm_minutes]), [['h-rl', 'calm', 15], ['h-nike', 'calm', 15]]);
const keptAll = JSON.parse(f.store.snypd_broad_ok);
assert(keptAll[f.g.savedSearchSignature(RL)] && keptAll[f.g.savedSearchSignature(NIKE)]);
assert.equal(f.el('broad-hunt-text').textContent, 'Done: 2 hunts now send at most one summary every 15 min. Change it anytime in Filters.');
assert.equal(shown(f, 'broad-hunt-calmall'), false);
passed++;

// 17. One update fails: the card says how many switched and the button stays usable.
f = fixture({}, [{ id: 'h-rl', is_active: true, vinted_url: RL, push_mode: 'every' }, { id: 'h-nike', is_active: true, vinted_url: NIKE, push_mode: 'every' }], ['h-nike']);
await f.g.noteBroadHunt(pricedFeed(f.g, 220, [[RL, 60, 10], [NIKE, 50, 5, 'GBP']]));
await f.el('broad-hunt-calmall').click();
assert.equal(f.el('broad-hunt-text').textContent, 'Switched 1 of 2 hunts to Calm. Try again for the rest, or change them in Filters.');
assert.equal(f.el('broad-hunt-calmall').disabled, false);
passed++;

// 18. Keep it on a suggestion remembers the busy hunt as well as the suggestion.
f = fixture({}, [{ id: 'h-rl', is_active: true, vinted_url: RL, push_mode: 'every' }]);
await f.g.noteBroadHunt(pricedFeed(f.g, 60, [[RL, 60, 10]]));
await f.el('broad-hunt-keep').click();
assert(JSON.parse(f.store.snypd_broad_ok)[f.g.savedSearchSignature(RL)]);
assert(f.store.snypd_coach_ok && /h-rl:busy:24/.test(f.store.snypd_coach_ok));
assert.equal(shown(f, 'broad-hunt'), false);
passed++;

// 19. A busy hunt already on Calm is not counted: no Calm all for a single every-match hunt.
f = fixture({}, [{ id: 'h-rl', is_active: true, vinted_url: RL, push_mode: 'every' }, { id: 'h-nike', is_active: true, vinted_url: NIKE, push_mode: 'calm' }]);
await f.g.noteBroadHunt(pricedFeed(f.g, 220, [[RL, 60, 10], [NIKE, 50, 5, 'GBP']]));
assert.equal(shown(f, 'broad-hunt-calmall'), false);
assert.doesNotMatch(f.el('broad-hunt-text').textContent, /of your hunts are this busy/);
passed++;

console.log(`PASS: ${passed} broad-hunt scenarios; no network.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
