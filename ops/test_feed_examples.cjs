/*
 * Browser test for the example listings under an empty feed (19 Nov 2026): the REAL dashboard.html in headless
 * Chrome, ops/qa_mock.js standing in for Supabase and api.snypd.store (?feed=empty; /api/v1/hunt-examples:
 * ?ex=N | 0 | error | bad | html). Each case runs in its own browser context.
 *   node ops/test_feed_examples.cjs              (needs Google Chrome at CHROME_PATH or the default Windows path)
 *   SHOTS=<dir> node ops/test_feed_examples.cjs  also writes screenshots
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const SHOTS = process.env.SHOTS || '';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
  async function open(q, vp, needRequest) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    if (needRequest !== false) await page.waitForFunction(() => (window.__exRequests || []).length >= 1, { timeout: 15000 });
    else await wait(4000);
    await wait(800);
    return page;
  }
  const state = p => p.evaluate(() => {
    const box = document.getElementById('examples');
    const shown = !!box && box.style.display !== 'none' && box.offsetParent !== null;
    const cards = Array.from(document.querySelectorAll('#examples-list .card'));
    const empty = document.getElementById('empty');
    return {
      shown, n: cards.length,
      titles: cards.map(c => (c.querySelector('.t') || {}).textContent || ''),
      prices: cards.map(c => (c.querySelector('.p') || {}).textContent || ''),
      links: cards.map(c => (c.querySelector('a.card-link') || {}).href || ''),
      claimButtons: document.querySelectorAll('#examples .claim-btn, #examples [data-listing]').length,
      marketButtons: document.querySelectorAll('#examples [data-market-check]').length,
      heading: (document.getElementById('examples-title') || {}).textContent || '',
      sub: (document.getElementById('examples-sub') || {}).textContent || '',
      emptyShown: !!empty && empty.style.display !== 'none',
      emptyText: empty ? empty.textContent : '',
      feedCards: document.querySelectorAll('#list .card').length,
      requests: (window.__exRequests || []).length,
      auth: ((window.__exRequests || [])[0] || {}).auth || null,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      xss: window.__xss || 0,
      injected: document.querySelectorAll('#examples-list img[src="x"]').length,
    };
  });

  // 1. Empty feed: three examples under the empty message.
  let p = await open('feed=empty');
  let s = await state(p);
  if (SHOTS) await p.screenshot({ path: path.join(SHOTS, 'examples-desktop.png') });
  ok(s.emptyShown, 'empty message still shown');
  ok(s.shown && s.n === 3, 'three example cards shown, got ' + s.n);
  ok(/already on vinted/i.test(s.heading), 'heading says already on Vinted');
  ok(/only new ones send an alert/i.test(s.sub), 'explains that only new listings alert');
  ok(s.titles[0] === 'Example jumper 1' && /11/.test(s.prices[0]), 'title and price drawn');
  ok(s.links.every(h => /^https:\/\/www\.vinted\.[a-z.]+\/items\/900\d-example$/.test(h)), 'links open the listing on Vinted: ' + s.links[0]);
  ok(s.claimButtons === 0, 'no Claim button on an example');
  ok(s.marketButtons === 0, 'no price-check button on an example');
  ok(s.feedCards === 0, 'examples are not in the feed list');
  ok(/^Bearer /.test(s.auth || ''), 'request carries the login');
  ok(s.requests === 1, 'one request, got ' + s.requests);
  ok(s.overflow <= 0, 'no sideways scroll on desktop');
  await wait(45000);   // two more 20 s feed refreshes: still one request (60 s cache), cards unchanged
  s = await state(p);
  ok(s.requests === 1 && s.n === 3 && s.shown, 'feed refreshes do not refetch within a minute');

  // 2. Phone.
  p = await open('feed=empty', PHONE);
  s = await state(p);
  if (SHOTS) await p.screenshot({ path: path.join(SHOTS, 'examples-phone.png') });
  ok(s.shown && s.n === 3, 'phone: three cards');
  ok(s.overflow <= 0, 'phone: no sideways scroll, overflow ' + s.overflow);

  // 3. A feed with listings: no examples, no request.
  p = await open('broad=1', null, false);
  s = await state(p);
  ok(s.feedCards > 0, 'feed has cards');
  ok(!s.shown && s.requests === 0, 'no examples and no request when the feed has listings');

  // 4. Nothing to show / route fails / malformed rows.
  p = await open('feed=empty&ex=0');
  s = await state(p);
  ok(!s.shown && s.emptyShown, 'no examples: block hidden, empty message stays');
  p = await open('feed=empty&ex=error');
  s = await state(p);
  ok(!s.shown && s.emptyShown, 'route error: block hidden, empty message stays');
  p = await open('feed=empty&ex=bad');
  s = await state(p);
  ok(s.shown && s.n === 1 && s.titles[0] === 'Example jumper 1', 'malformed rows skipped, the good one shown');
  p = await open('feed=empty&ex=25');
  s = await state(p);
  ok(s.n === 10, 'at most ten cards, got ' + s.n);

  // 5. Markup in a title is shown as text.
  p = await open('feed=empty&ex=html');
  s = await state(p);
  ok(s.n === 1 && s.xss === 0 && s.injected === 0, 'title markup not executed');
  ok(s.titles[0].indexOf('<img') === 0, 'title markup shown as text');

  // 6. No saved hunt: the "No hunts yet" screen, no examples.
  p = await open('feed=empty&hunts=0', null, false);
  s = await state(p);
  ok(!s.shown && s.requests === 0, 'no hunts: no examples, no request');

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' feed-example browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
