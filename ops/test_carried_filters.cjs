/*
 * Filters carried from a Vinted search page (browser extension, 22 Nov 2026): the REAL dashboard.html in headless
 * Chrome with ops/qa_mock.js.   node ops/test_carried_filters.cjs
 * Checks: a stored intent with f fills the first-search form, shows the "filters are kept" line, and the saved link
 * carries the filters; another Vinted site drops them; an intent without f behaves as before; a malformed f is
 * refused as a whole. No network: the mock answers every call.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    const f = path.join(root, p);
    if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const F = 'brand_ids:53,88;size_ids:207;status_ids:6';

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(intent, q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    const close = page.close.bind(page);
    page.close = async () => { await close(); await ctx.close(); };
    await page.setViewport({ width: 390, height: 664, isMobile: true, hasTouch: true });
    page.on('pageerror', e => errors.push(e.message));
    if (intent) await page.evaluateOnNewDocument(v => { try { localStorage.setItem('snypd_hunt_intent', JSON.stringify(Object.assign({ t: Date.now() }, v))); } catch (e) {} }, intent);
    await page.goto(base + '/dashboard.html?plan=free&hunts=0' + (q || ''), { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(1500);
    return page;
  }
  const form = p => p.evaluate(() => {
    const k = document.getElementById('wiz-q-carried');
    return { words: document.getElementById('wiz-q-words').value, site: document.getElementById('wiz-q-site').value, max: document.getElementById('wiz-q-max').value,
      note: k ? k.textContent : null, noteShown: !!k && k.style.display !== 'none' && k.getClientRects().length > 0,
      intentLeft: localStorage.getItem('snypd_hunt_intent'), over: document.documentElement.scrollWidth > window.innerWidth };
  });
  const save = async p => { await p.evaluate(() => document.getElementById('wiz-q-save').click()); await wait(1200); return p.evaluate(() => window.__qaDB.user_searches.map(h => h.vinted_url)); };
  const params = u => { const x = new URL(u); return { brand: x.searchParams.getAll('brand_ids[]'), size: x.searchParams.getAll('size_ids[]'), status: x.searchParams.getAll('status_ids[]'),
    q: x.searchParams.get('search_text'), max: x.searchParams.get('price_to'), order: x.searchParams.get('order'), host: x.hostname, path: x.pathname, keys: [...new Set([...x.searchParams.keys()])] }; };

  // 1. carried filters are kept
  let page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40', f: F });
  let s = await form(page);
  eq([s.words, s.site, s.max], ['nike tech fleece', 'vinted.fr', '40'], 'the form is filled from the carried search');
  ok(s.noteShown && /filters .* are kept/.test(s.note), 'the "filters are kept" line shows: ' + s.note);
  eq(s.intentLeft, null, 'the stored search is removed once the form has opened');
  ok(!s.over, 'no sideways scroll');
  let urls = await save(page);
  eq(urls.length, 1, 'one search saved');
  let u = params(urls[0]);
  eq([u.brand, u.size, u.status], [['53', '88'], ['207'], ['6']], 'the saved link carries the filters');
  eq([u.q, u.max, u.order, u.host, u.path], ['nike tech fleece', '40', 'newest_first', 'www.vinted.fr', '/catalog'], 'words, price, order and site are right');
  ok(u.keys.every(k => ['search_text', 'price_to', 'brand_ids[]', 'size_ids[]', 'status_ids[]', 'order'].includes(k)), 'no unexpected parameter: ' + u.keys.join(','));
  await page.close();

  // 2. another Vinted site: filter ids belong to the site they came from, so they are dropped
  page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40', f: F });
  await page.evaluate(() => { const e = document.getElementById('wiz-q-site'); e.value = 'vinted.be'; e.dispatchEvent(new Event('change', { bubbles: true })); });
  await wait(300);
  s = await form(page);
  ok(!s.noteShown, 'the line hides when the site changes');
  urls = await save(page);
  u = params(urls[0]);
  eq([u.brand, u.size, u.status, u.host], [[], [], [], 'www.vinted.be'], 'no filters on another site');
  await page.close();

  // 3. back to the original site: kept again
  page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40', f: F });
  await page.evaluate(() => { const e = document.getElementById('wiz-q-site'); e.value = 'vinted.be'; e.dispatchEvent(new Event('change', { bubbles: true })); e.value = 'vinted.fr'; e.dispatchEvent(new Event('change', { bubbles: true })); });
  await wait(300);
  ok((await form(page)).noteShown, 'the line returns with the original site');
  u = params((await save(page))[0]);
  eq(u.brand, ['53', '88'], 'filters kept after switching back');
  await page.close();

  // 4. an intent without filters behaves as before
  page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40' });
  s = await form(page);
  eq([s.words, s.note], ['nike tech fleece', null], 'no line without carried filters');
  u = params((await save(page))[0]);
  eq(u.keys.sort(), ['order', 'price_to', 'search_text'], 'the saved link is the plain one');
  await page.close();

  // 5. malformed filters: the whole carried search is refused, nothing is filled
  for (const bad of ['brand_ids:53;evil:1', 'brand_ids:<script>', 'search_text:1', 'brand_ids:53;brand_ids:54']) {
    page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40', f: bad });
    s = await form(page);
    eq([s.words, s.note, s.intentLeft], ['', null, null], 'refused: ' + bad);
    await page.close();
  }

  // 6. French
  page = await open({ q: 'nike tech fleece', site: 'vinted.fr', min: '', max: '40', f: F }, '&lang=fr');
  await wait(800);
  s = await form(page);
  ok(/filtres Vinted/.test(s.note || ''), 'the line is in French: ' + s.note);
  ok(!s.over, 'no sideways scroll (French)');
  await page.close();

  assert.deepEqual(errors, [], 'no page errors'); passed++;
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' carried-filter checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks: ' + (e && e.message)); process.exit(1); });
