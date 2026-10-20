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

function fixture(store = {}) {
  const els = {};
  const el = id => (els[id] ||= { id, style: { display: 'none' }, textContent: '', listeners: {},
    addEventListener(t, cb) { (this.listeners[t] ||= []).push(cb); }, click() { (this.listeners.click || []).forEach(cb => cb()); } });
  const g = { console, URL, JSON, Math, Map, Set, Date, document: { getElementById: el },
    localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } } };
  g.window = g;
  const ctx = vm.createContext(g);
  vm.runInContext(sigFn + '\n' + broad + '\n;globalThis.noteBroadHunt = noteBroadHunt; globalThis.savedSearchSignature = savedSearchSignature;', ctx);
  return { g, el, store };
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
let f = fixture();
f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
assert.equal(f.el('broad-hunt').style.display, '');
assert.match(f.el('broad-hunt-text').textContent, /^About 120 new listings an hour match "ralph lauren": /);
passed++;

// 2. A quiet hunt: 10 in 30 min -> nothing.
f = fixture();
f.g.noteBroadHunt(feed(f.g, 10, [[PS5, 10]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 3. Two hunts, the feed shows only a sample (60 of 200): the broad one is named, its share scaled.
f = fixture();
f.g.noteBroadHunt(feed(f.g, 200, [[RL, 57], [PS5, 3]]));
assert.match(f.el('broad-hunt-text').textContent, /^About 380 new listings an hour match "ralph lauren"/);
passed++;

// 4. Two hunts where neither reaches the threshold on its own share -> nothing.
f = fixture();
f.g.noteBroadHunt(feed(f.g, 30, [[RL, 15], [PS5, 15]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 5. "Keep it" remembers this hunt on this device; the next feed refresh shows nothing.
f = fixture();
// the wiring IIFE ran at load with the same element objects
f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
f.el('broad-hunt-keep').click();
assert.equal(f.el('broad-hunt').style.display, 'none');
assert(JSON.parse(f.store.snypd_broad_ok)[f.g.savedSearchSignature(RL)]);
f.g.noteBroadHunt(feed(f.g, 80, [[RL, 60]]));
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 6. "Edit hunt" opens the Filters sheet and hides the notice.
f = fixture();
let opened = 0;
f.el('filter-pill').addEventListener('click', () => { opened++; });
f.g.noteBroadHunt(feed(f.g, 60, [[RL, 60]]));
f.el('broad-hunt-edit').click();
assert.equal(opened, 1);
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

// 7. Rows from paused/deleted hunts (not active) are ignored; empty feeds never throw.
f = fixture();
const other = feed(f.g, 60, [[RL, 60]]);
other.activeSearches = new Set();
f.g.noteBroadHunt(other);
f.g.noteBroadHunt({ rows: [], eligibleCount: 0, activeSearches: new Set() });
f.g.noteBroadHunt(null);
assert.equal(f.el('broad-hunt').style.display, 'none');
passed++;

console.log(`PASS: ${passed} broad-hunt scenarios; no network.`);
