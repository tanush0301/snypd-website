/*
 * Browser test for the live feed wait (20 Nov 2026): the open dashboard holds one request to
 * /api/v1/feed/wait and refreshes the feed the moment a find is queued, instead of on its 20 s timer.
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js (?fw=404 | retry | error).
 *   node ops/test_feed_wait.cjs      (needs Google Chrome at CHROME_PATH or the default Windows path)
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
  async function open(q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForFunction(() => document.querySelectorAll('#list .card').length > 0, { timeout: 20000 });
    await wait(2500);
    return page;
  }
  // a find is saved and the server-side marker moves, as the scraper does
  const arrive = (page, stamp) => page.evaluate(stamp => {
    const DB = window.__qaDB, tpl = DB.current_ads.find(r => r.listing_id === 5000);
    window.__seq = (window.__seq || 0);
    const t = Date.now() - 1000, id = 7000 + (window.__seq++);
    DB.current_ads.push(Object.assign({}, tpl, { listing_id: id, title: 'Fresh arrival ' + id, url: 'https://www.vinted.be/items/' + id,
      fetched_at: new Date(t).toISOString(), created_at: new Date(t).toISOString(), uploaded_ts: Math.floor(t / 1000), uploaded_at_ts: new Date(t).toISOString() }));
    if (stamp) window.__feedTick = Date.now();
  }, stamp);
  const state = page => page.evaluate(() => ({
    reqs: (window.__fwRequests || []).length,
    auth: ((window.__fwRequests || [])[0] || {}).auth || null,
    sinces: (window.__fwRequests || []).map(r => r.since),
    loads: window.__feedWaitLoads || 0,
    fresh: Array.from(document.querySelectorAll('#list .card .t')).filter(e => /Fresh arrival/.test(e.textContent)).length,
    note: (document.getElementById('feed-new-note') || {}).textContent || '',
  }));

  // 1. the loop runs, signed in, and does not reload the feed while nothing is new
  let p = await open('broad=1');
  let s = await state(p);
  ok(s.reqs >= 1, 'wait request sent, got ' + s.reqs);
  ok(/^Bearer /.test(s.auth || ''), 'request carries the login');
  ok(s.sinces[0] === 0, 'first request asks since 0');
  ok(s.loads === 0, 'no reload while nothing is new');
  ok(s.fresh === 0, 'no fresh card yet');

  // 2. a find arrives: the feed shows it within about 2 s (the timer alone would take up to 20 s)
  const t0 = Date.now();
  await arrive(p, true);
  await p.waitForFunction(() => Array.from(document.querySelectorAll('#list .card .t')).some(e => /Fresh arrival/.test(e.textContent)), { timeout: 6000 });
  const took = Date.now() - t0;
  s = await state(p);
  ok(took < 3000, 'fresh card shown fast: ' + took + ' ms');
  ok(s.loads === 1, 'one reload from the wait, got ' + s.loads);
  ok(s.note === '1 new listing', 'the new-listing notice fired: ' + s.note);
  await wait(2500);
  s = await state(p);
  ok(s.loads === 1, 'no repeat reload for the same marker');
  ok(s.sinces[s.sinces.length - 1] > 0, 'later requests ask since the last marker');

  // 3. a second find: again fast, exactly one more reload
  await arrive(p, true);
  await p.waitForFunction(() => Array.from(document.querySelectorAll('#list .card .t')).filter(e => /Fresh arrival/.test(e.textContent)).length === 2, { timeout: 6000 });
  s = await state(p);
  ok(s.loads === 2, 'second find: second reload');

  // 4. a marker that was already set before the page opened does not cause a reload at start
  const ctx = await browser.createBrowserContext();
  const q = await ctx.newPage();
  await q.setViewport({ width: 1280, height: 900 });
  q.on('pageerror', e => errors.push('preset: ' + e.message));
  await q.evaluateOnNewDocument(() => { window.__feedTick = 12345; });
  await q.goto(base + '/dashboard.html?broad=1', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(() => document.querySelectorAll('#list .card').length > 0, { timeout: 20000 });
  await wait(3000);
  s = await state(q);
  ok(s.reqs >= 2 && s.loads === 0, 'old marker at start: no reload (requests ' + s.reqs + ', loads ' + s.loads + ')');
  ok(s.sinces[1] === 12345, 'then waits from that marker');

  // 5. older backend (404), refusal (retry) and error: one request, then quiet; the page works
  for (const mode of ['404', 'retry', 'error']) {
    p = await open('broad=1&fw=' + mode);
    await wait(3000);
    s = await state(p);
    ok(s.reqs === 1, 'fw=' + mode + ': one request then a pause, got ' + s.reqs);
    ok(s.loads === 0, 'fw=' + mode + ': no reload');
    await arrive(p, true);
    await p.evaluate(() => window.SNYPD.refreshFeed());
    s = await state(p);
    ok(s.fresh === 1, 'fw=' + mode + ': the normal refresh still shows the find');
  }

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' feed-wait browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
