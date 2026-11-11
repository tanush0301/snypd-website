/*
 * Market in the dashboard's phone bottom bar (11 Nov 2026). The REAL dashboard.html in headless Chrome, ops/qa_mock.js
 * standing in for Supabase and api.snypd.store.
 *   node ops/test_market_bottom_bar.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
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
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const html = fs.readFileSync(path.join(root, 'dashboard.html'));
  ok(html[0] === 0xEF && html[1] === 0xBB && html[2] === 0xBF, 'dashboard.html keeps its BOM');

  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp) {
    const page = await browser.newPage();
    await page.setViewport(vp);
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('#bottombar .bottombar-tab[data-view="market"]', { timeout: 10000 });
    await wait(1200);
    return page;
  }
  const barState = page => page.evaluate(() => {
    const nav = document.getElementById('bottombar');
    const tabs = Array.from(nav.querySelectorAll('.bottombar-tab')).filter(t => getComputedStyle(t).display !== 'none');
    const shown = id => { const e = document.getElementById(id); return !!e && getComputedStyle(e).display !== 'none'; };
    return { navShown: getComputedStyle(nav).display !== 'none', labels: tabs.map(t => t.textContent.trim()), views: tabs.map(t => t.dataset.view),
      widths: tabs.map(t => Math.round(t.getBoundingClientRect().width)), heights: tabs.map(t => Math.round(t.getBoundingClientRect().height)),
      active: tabs.filter(t => t.classList.contains('active')).map(t => t.dataset.view),
      sw: document.documentElement.scrollWidth, vw: innerWidth,
      market: shown('market-panel') || (function () { const m = document.querySelector('[id^="market"][id$="panel"], #view-market'); return !!m && getComputedStyle(m).display !== 'none'; })(),
      board: (function () { const b = document.getElementById('mb-box'); return !!b && b.style.display !== 'none' && b.getBoundingClientRect().height > 0 && b.innerText.length > 10; })() };
  });
  const tap = (page, view) => page.evaluate(v => document.querySelector('#bottombar .bottombar-tab[data-view="' + v + '"]').click(), view);

  // ---- phone: four tabs, Market second ----------------------------------------------------------------------
  {
    const page = await open('plan=pro&stock=off', { width: 390, height: 844, isMobile: true, hasTouch: true });
    let s = await barState(page);
    ok(s.navShown, 'the bottom bar shows on a phone');
    eq(s.views, ['feed', 'market', 'history', 'profile'], 'tabs in order: Feed, Market, History, Profile');
    eq(s.labels.map(l => l.toUpperCase()), ['FEED', 'MARKET', 'HISTORY', 'PROFILE'], 'labels');
    ok(Math.max(...s.widths) - Math.min(...s.widths) <= 1, 'four tabs share the width equally ' + s.widths);
    ok(new Set(s.heights).size === 1 && s.heights[0] >= 44, 'every label on one line, tall enough to tap ' + s.heights);
    eq(s.active, ['feed'], 'Feed is active first');
    ok(s.sw <= s.vw, 'no sideways scroll at 390');
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'mtab-390-feed.png') });

    await tap(page, 'market');
    await page.waitForFunction(() => { const b = document.getElementById('mb-box'); return b && b.style.display !== 'none' && b.innerText.length > 10; }, { timeout: 8000 });
    s = await barState(page);
    eq(s.active, ['market'], 'tapping Market makes it the active tab');
    ok(s.board, 'the Market board is on screen after the tap');
    eq(await page.evaluate(() => Array.from(document.querySelectorAll('.view-tab.active')).map(t => t.dataset.view)), ['market'], 'the top row follows');
    ok(s.sw <= s.vw, 'no sideways scroll on the Market tab at 390');
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'mtab-390-market.png') });

    await tap(page, 'profile');
    await wait(300);
    eq((await barState(page)).active, ['profile'], 'Profile still works');
    await tap(page, 'feed');
    await wait(300);
    s = await barState(page);
    eq(s.active, ['feed'], 'back to Feed');
    ok(!s.board, 'the Market board is hidden again on Feed');
    await page.close();
  }

  // ---- narrow phone ------------------------------------------------------------------------------------------
  {
    const page = await open('plan=free&stock=off', { width: 320, height: 640, isMobile: true, hasTouch: true });
    const s = await barState(page);
    eq(s.views.length, 4, '320: four tabs');
    ok(new Set(s.heights).size === 1, '320: every label on one line ' + s.heights);
    ok(s.sw <= s.vw, '320: no sideways scroll');
    await page.close();
  }

  // ---- with Stock on: it takes History's place, still four tabs ------------------------------------------------
  {
    const page = await open('plan=pro&stock=all&boot=1', { width: 390, height: 844, isMobile: true, hasTouch: true });
    await page.waitForFunction(() => { const t = document.getElementById('bottombar-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
    const s = await barState(page);
    eq(s.views, ['feed', 'market', 'stock', 'profile'], 'with Stock on: Feed, Market, Stock, Profile');
    ok(Math.max(...s.widths) - Math.min(...s.widths) <= 1, 'with Stock on the four tabs are still equal ' + s.widths);
    await page.close();
  }

  // ---- French ---------------------------------------------------------------------------------------------------
  {
    const page = await open('plan=pro&stock=off&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
    await wait(600);
    const s = await barState(page);
    eq(s.labels.map(l => l.toUpperCase()), ['FLUX', 'MARKET', 'HISTORIQUE', 'PROFIL'], 'French labels (Market keeps its name, like "Market Insights")');
    ok(new Set(s.heights).size === 1, 'French: every label on one line ' + s.heights);
    ok(s.sw <= s.vw, 'French: no sideways scroll');
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'mtab-390-fr.png') });
    await page.close();
  }

  // ---- desktop: no bottom bar -------------------------------------------------------------------------------------
  {
    const page = await open('plan=pro&stock=off', { width: 1280, height: 900 });
    const s = await barState(page);
    ok(!s.navShown, 'desktop never shows the bottom bar');
    eq(await page.evaluate(() => Array.from(document.querySelectorAll('.view-tab')).filter(t => getComputedStyle(t).display !== 'none').map(t => t.dataset.view)), ['feed', 'history', 'market'], 'desktop top row unchanged');
    await page.close();
  }

  await browser.close();
  server.close();
  eq(errors, [], 'no page errors');
  console.log('market bottom bar: ' + passed + ' checks passed');
})().catch(e => { console.error(e); process.exit(1); });
