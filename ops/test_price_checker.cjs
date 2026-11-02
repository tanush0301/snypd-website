'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require(require.resolve('jsdom', { paths: [path.join(__dirname, 'auth')] }));
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'assets/price-checker.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/price-index.json'), 'utf8'));
const flush = () => new Promise(resolve => setImmediate(resolve));
async function boot(t, { file = 'it/stima-prezzo-vinted.html', query = '', fail = false } = {}) {
  const dom = new JSDOM(fs.readFileSync(path.join(root, file), 'utf8'), {
    url: 'https://www.snypd.store/' + file.replace(/\.html$/, '') + '?q=' + encodeURIComponent(query),
    runScripts: 'outside-only'
  });
  t.after(() => dom.window.close());
  const w = dom.window, events = [], requests = [];
  w.gtag = (...args) => events.push(args);
  w.fetch = async url => {
    requests.push(url);
    return { ok: !fail, status: fail ? 503 : 200, json: async () => structuredClone(data) };
  };
  w.eval(script);
  await flush(); await flush();
  return { w, events, requests, box: w.document.querySelector('[data-pc]'), result: w.document.querySelector('.pc-res') };
}
test('Italian lookup uses a verified estimate and the translated pilot guide', async t => {
  const h = await boot(t, { query: 'Samba' });
  assert.equal(h.result.hidden, false);
  assert.match(h.result.querySelector('.pc-big').textContent, /50/);
  assert.ok([...h.result.querySelectorAll('a')].some(a => a.pathname === '/it/prezzi-vinted/adidas-samba'));
  assert.equal(h.events[0][1], 'price_check');
  assert.deepEqual(Object.keys(h.events[0][2]).sort(), ['item_id', 'page_lang']);
  assert.deepEqual(h.requests, ['/assets/data/price-index.json']);
});
test('an unavailable estimate has an explicit explanation, no invented price and no automatic budget', async t => {
  const h = await boot(t, { query: 'Jordan 4' });
  assert.equal(h.result.hidden, false);
  assert.equal(h.result.querySelector('.pc-big'), null);
  assert.match(h.result.textContent, /Non è disponibile una stima/);
  assert.match(h.result.textContent, /INGLESE/);
  assert.equal(h.result.querySelector('a').pathname, '/vinted-price-guide/jordan-4');
  assert.equal(h.result.querySelector('a[href*="/signup"]'), null);
  assert.equal(h.events[0][1], 'price_check_unavailable');
});
test('switching from unavailable to a supported item clears the previous result', async t => {
  const h = await boot(t, { query: 'Jordan 4' });
  const input = h.box.querySelector('input');
  input.value = 'Nike Dunk Low';
  input.dispatchEvent(new h.w.Event('input', { bubbles: true }));
  assert.ok(h.result.querySelector('.pc-big'));
  assert.doesNotMatch(h.result.textContent, /Non è disponibile una stima/);
  assert.equal(h.events.length, 2);
  input.dispatchEvent(new h.w.Event('input', { bubbles: true }));
  assert.equal(h.events.length, 2, 'repeated rendering does not multiply events');
});
test('typed text is displayed safely and is never sent to analytics or the backend', async t => {
  const query = '<img src=x onerror=alert(1)>';
  const h = await boot(t, { query });
  assert.equal(h.box.querySelector('.pc-msg img'), null);
  assert.equal(h.events.length, 0);
  assert.deepEqual(h.requests, ['/assets/data/price-index.json']);
});
test('an index outage preserves the static article instead of claiming a result', async t => {
  const h = await boot(t, { query: 'Samba', fail: true });
  assert.equal(h.box.hidden, true);
  assert.equal(h.events.length, 0);
  assert.match(h.w.document.body.textContent, /Le 34 stime complessive disponibili/);
});
