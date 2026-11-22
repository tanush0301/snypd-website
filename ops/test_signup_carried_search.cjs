/*
 * Sign-up page shows the carried search (22 Nov 2026).   node ops/test_signup_carried_search.cjs
 * Serves the repo's own files; every other host is blocked except the sign-in library (as in test_auth_small_phone).
 * Checks: the "YOUR SEARCH" line shows words, site and price; markup in the words stays text; the filters are stored;
 * a malformed filter list stores nothing and shows no line; no line without a search; French label; on phones the line is
 * left out (it pushed the submit button under the cookie bar) and the button stays above the bar; no sideways scroll; no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(root, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(root, p + '.html');
  if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f)) { res.writeHead(404); return res.end('nope'); }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(fs.readFileSync(f));
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const F = 'brand_ids:53,88;size_ids:207';

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(query, w, h) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    if (w) await page.setUserAgent(IPHONE);
    await page.setViewport(w ? { width: w, height: h, isMobile: true, hasTouch: true } : { width: 1280, height: 800 });
    page.on('pageerror', e => errors.push(query + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') || /^https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@/.test(r.url()) ? r.continue() : r.abort()));
    await page.goto(base + '/signup' + query, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 8000 });
    await page.waitForSelector('.snc-bar', { timeout: 8000 });
    await wait(500);
    const r = await page.evaluate(() => {
      const c = document.querySelector('[data-carried-search]');
      const s = [...document.querySelectorAll('#au-form button[type=submit]')].find(e => e.getClientRects().length);
      return { line: c ? c.textContent.replace(/\s+/g, ' ').trim() : null, kids: c ? c.querySelectorAll('img,script,b,i').length : 0,
        lineH: c ? Math.round(c.getBoundingClientRect().height) : 0,
        intent: JSON.parse(localStorage.getItem('snypd_hunt_intent') || 'null'),
        submit: Math.round(s.getBoundingClientRect().bottom), bar: Math.round(document.querySelector('.snc-bar').getBoundingClientRect().top),
        over: document.documentElement.scrollWidth > window.innerWidth };
    });
    await ctx.close();
    return r;
  }
  const enc = encodeURIComponent;
  const Q = '?hunt=nike+tech&site=vinted.co.uk&min=10&max=45.5&lang=en&f=' + enc(F) + '&utm_source=chrome-extension&utm_medium=extension';

  // 1. the line and the stored search
  let r = await open(Q);
  eq(r.line, 'YOUR SEARCH nike tech \u00b7 vinted.co.uk \u00b7 min 10 \u00b7 max 45.5', 'the line shows words, site and price');
  eq([r.intent.q, r.intent.site, r.intent.min, r.intent.max, r.intent.f], ['nike tech', 'vinted.co.uk', '10', '45.5', F], 'the search and its filters are stored');
  ok(!r.over, 'no sideways scroll');

  // 2. markup in the words stays text
  r = await open('?hunt=' + enc('<img src=x onerror=alert(1)><b>x</b>') + '&site=vinted.fr&min=&lang=en');
  ok(r.line && r.line.indexOf('<img src=x onerror=alert(1)><b>x</b>') > 0 && r.kids === 0, 'markup shown as text: ' + r.line);

  // 3. malformed filters: nothing stored, no line
  r = await open('?hunt=nike&site=vinted.fr&min=&lang=en&f=' + enc('brand_ids:53;evil:1'));
  eq([r.line, r.intent], [null, null], 'a malformed filter list stores nothing');

  // 4. no carried search: no line (unchanged page)
  r = await open('');
  eq([r.line, r.intent], [null, null], 'no line without a search');

  // 5. legacy price-guide link (words + max, no site)
  r = await open('?hunt=adidas+samba&max=25');
  eq(r.line, 'YOUR SEARCH adidas samba \u00b7 max 25', 'legacy link shows words and max');

  // 6. French
  r = await open(Q.replace('lang=en', 'lang=fr'));
  ok(/^TA RECHERCHE nike tech/.test(r.line || ''), 'French label: ' + r.line);

  // 7. phones: the submit button stays above the cookie bar with the line present (longest allowed words too)
  const LONG = '?hunt=' + enc('ralph lauren polo bear knit jumper navy blue vintage 90s rare xl') + '&site=vinted.co.uk&min=10&max=45.5&f=' + enc(F);
  for (const [w, h] of [[320, 568], [339, 600], [360, 640], [375, 553], [390, 664]]) for (const [name, q] of [['short', Q], ['long', LONG], ['short fr', Q.replace('lang=en', 'lang=fr')], ['long fr', LONG + '&lang=fr']]) {
    r = await open(q, w, h);
    ok(r.line === null && r.intent && r.intent.q, w + 'x' + h + ' ' + name + ': no line on a phone, the search is still stored');
    ok(r.submit <= r.bar, w + 'x' + h + ' ' + name + ': submit above the cookie bar (' + r.submit + ' vs ' + r.bar + ', line ' + r.lineH + ' px)');
    ok(!r.over, w + 'x' + h + ' ' + name + ': no sideways scroll');
  }

  assert.deepEqual(errors, [], 'no page errors'); passed++;
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' carried-search sign-up checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks: ' + (e && e.message)); process.exit(1); });
