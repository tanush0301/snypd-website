/* Run: node ops/test_referral_capture.cjs. No network, no browser: runs the ?ref= capture and the invite bar
   blocks of assets/consent.js in node:vm with fake storage and document (same approach as test_growth_entrypoints). */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'consent.js'), 'utf8');
const a = src.indexOf('/* Referral link (?ref='), b = src.indexOf('/* Not about consent:', a);
assert(a >= 0 && b > a, 'referral blocks not found');
const code = src.slice(a, b);
assert.doesNotMatch(src, /[^\x00-\x7F]/, 'consent.js must stay ASCII');
let passed = 0;
const DAY = 864e5;

function store(init) {
  const m = new Map(Object.entries(init || {}));
  return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), _m: m };
}
function makeEl(tag) {
  const e = { tag, style: {}, attrs: {}, children: [], parentNode: null, textContent: '', listeners: {},
    setAttribute(k, v) { this.attrs[k] = v; }, appendChild(c) { c.parentNode = this; this.children.push(c); },
    removeChild(c) { this.children = this.children.filter(x => x !== c); c.parentNode = null; },
    addEventListener(t, f) { this.listeners[t] = f; } };
  return e;
}
function run({ url = '/', lang = 'en', local = {}, session = {}, now = 1e12 } = {}) {
  const u = new URL('https://www.snypd.store' + url);
  const body = makeEl('body');
  body.insertBefore = (c) => { c.parentNode = body; body.children.unshift(c); };
  Object.defineProperty(body, 'firstChild', { get: () => body.children[0] || null });
  const document = { body, documentElement: { getAttribute: () => lang }, createElement: makeEl,
    getElementById: id => body.children.find(c => c.id === id) || null, addEventListener() {} };
  const ls = store(local), ss = store(session);
  const ctx = { location: { search: u.search, pathname: u.pathname }, localStorage: ls, sessionStorage: ss,
    document, URLSearchParams, JSON, Date: { now: () => now }, Number, String };
  vm.runInNewContext(code, ctx);
  const bar = body.children.find(c => c.id === 'snypd-refer-bar') || null;
  return { ls, ss, bar, text: bar ? bar.children[0].textContent : null };
}
const saved = r => JSON.parse(r.ls.getItem('snypd_refer') || 'null');

// capture
let r = run({ url: '/?ref=ab23cd' });
assert.equal(saved(r).c, 'ab23cd'); assert.equal(saved(r).t, 1e12); passed++;
r = run({ url: '/vinted-bot?ref=AB23CD' });
assert.equal(saved(r).c, 'ab23cd', 'uppercase accepted, stored lower'); passed++;
for (const bad of ['ab23c', 'ab23cde', 'ab0cd1', 'ab cd2', '<scr>1']) {
  r = run({ url: '/?ref=' + encodeURIComponent(bad) }); assert.equal(saved(r), null, bad); passed++;
}
r = run({ url: '/?r=ab23cd' });
assert.equal(saved(r), null, 'outreach ?r= is not a referral'); passed++;
r = run({ url: '/?ref=zz99zz', local: { snypd_refer: JSON.stringify({ c: 'ab23cd', t: 1e12 - 10 * DAY }) } });
assert.equal(saved(r).c, 'ab23cd', 'first touch wins inside 60 days'); passed++;
r = run({ url: '/?ref=zz99zz', local: { snypd_refer: JSON.stringify({ c: 'ab23cd', t: 1e12 - 61 * DAY }) } });
assert.equal(saved(r).c, 'zz99zz', 'expired code replaced'); passed++;

// placement tag (&src=)
r = run({ url: '/?ref=ab23cd&src=receipt' });
assert.equal(saved(r).s, 'receipt', 'known src kept'); passed++;
r = run({ url: '/?ref=ab23cd&src=SUCCESS' });
assert.equal(saved(r).s, 'success', 'src lowercased'); passed++;
for (const bad of ['evil', '<x>', 'receipt2', '']) {
  r = run({ url: '/?ref=ab23cd&src=' + encodeURIComponent(bad) });
  assert.equal(saved(r).s, undefined, 'unknown src dropped: ' + bad); assert.equal(saved(r).c, 'ab23cd'); passed++;
}
r = run({ url: '/?ref=zz99zz&src=hub', local: { snypd_refer: JSON.stringify({ c: 'ab23cd', s: 'receipt', t: 1e12 - DAY }) } });
assert.equal(saved(r).s, 'receipt', 'first touch keeps its src'); passed++;

// invite bar
const fresh = { snypd_refer: JSON.stringify({ c: 'ab23cd', t: 1e12 - DAY }) };
for (const p of ['/', '/index.html', '/signup', '/signup.html']) {
  r = run({ url: p, local: fresh }); assert(r.bar, 'bar on ' + p); assert.match(r.text, /^A friend invited you/); passed++;
}
r = run({ url: '/?ref=ab23cd' });
assert(r.bar, 'bar on the same load as the capture'); passed++;
for (const p of ['/plans', '/dashboard', '/login', '/vinted-bot', '/account']) {
  r = run({ url: p, local: fresh }); assert.equal(r.bar, null, 'no bar on ' + p); passed++;
}
r = run({ url: '/fr/', lang: 'fr', local: fresh });
assert.match(r.text, /^Un ami t’a invité/); passed++;
r = run({ url: '/', local: { snypd_refer: JSON.stringify({ c: 'ab23cd', t: 1e12 - 61 * DAY }) } });
assert.equal(r.bar, null, 'expired code: no bar'); passed++;
r = run({ url: '/' }); assert.equal(r.bar, null, 'no code: no bar'); passed++;
r = run({ url: '/', local: fresh, session: { snypd_refer_bar_closed: '1' } });
assert.equal(r.bar, null, 'dismissed this session'); passed++;
r = run({ url: '/', local: fresh });
r.bar.children[1].listeners.click();
assert.equal(r.ss.getItem('snypd_refer_bar_closed'), '1'); assert.equal(r.bar.parentNode, null, 'close removes'); passed++;
assert.doesNotMatch(code, /innerHTML/, 'bar never uses innerHTML'); passed++;
console.log('referral capture + invite bar: ' + passed + ' checks pass');
