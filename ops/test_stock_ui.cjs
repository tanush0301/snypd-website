/*
 * Browser test for the Stock tab (step 3): the REAL dashboard.html + assets/stock*.js in headless Chrome, with ops/qa_mock.js and ops/stock_engine.js
 * standing in for Supabase (the Supabase CDN script tag is swapped on the fly, nothing is written to disk).
 *   node ops/test_stock_ui.cjs          (needs Google Chrome at CHROME_PATH or the default Windows path; puppeteer-core is in node_modules)
 * Checks: tab hidden for stock_mode off / admin-without-admin and nothing loaded; lazy loading; list, search, filters; add; list / reprice /
 * reserve / sold / returned / written off; history timeline; edit; delete + restore; undo; Free cap in French; 390 px layout (no horizontal
 * overflow, 44 px targets); no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.woff2': 'font/woff2' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');

const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'); let p = decodeURIComponent(u.pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/acceptance-fixture.json') return send(fs.readFileSync(path.join(root, 'ops/stock/acceptance-fixture.json')), 'application/json');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});

let passed = 0;
const ok = (cond, msg) => { assert(cond, msg); passed++; };
const eq = (a, b, msg) => { assert.deepEqual(a, b, msg); passed++; };

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(query, vp) {
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(query + ' pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && /SNYPD Stock|stock/i.test(m.text())) errors.push(query + ' console: ' + m.text()); });
    const requested = []; page.on('request', r => { const u = r.url(); if (/stock/.test(u)) requested.push(u.replace(base, '')); });
    await page.goto(base + '/dashboard.html?boot=1&' + query, { waitUntil: 'domcontentloaded' });
    page.requested = requested;
    return page;
  }
  const stockTabShown = page => page.evaluate(() => { const t = document.getElementById('view-tab-stock'); return !!t && getComputedStyle(t).display !== 'none'; });
  const settle = (page, ms) => new Promise(r => setTimeout(r, ms || 1500));

  // ---- 1. switch off / admin: nothing shows, nothing loads
  for (const [q, shown] of [['plan=elite&stock=off', false], ['plan=free&stock=admin', false], ['plan=elite&stock=admin', true], ['plan=free&stock=all', true]]) {
    const page = await open(q); await settle(page, 1800);
    eq(await stockTabShown(page), shown, 'Stock tab visibility for ?' + q);
    eq(page.requested.filter(u => /stock(-core|-i18n)?\.(js|css)/.test(u)), [], 'no Stock asset is requested before the tab is opened (?' + q + ')');
    await page.close();
  }

  // ---- 2. desktop, English, the design dataset
  let page = await open('plan=elite&stock=all&stock_seed=acceptance&stock_today=2026-11-02');
  await page.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#view-tab-stock');
  await page.waitForSelector('#stock-panel .st-row', { timeout: 8000 });
  ok(page.requested.some(u => /stock-core\.js/.test(u)) && page.requested.some(u => /stock\.js/.test(u)) && page.requested.some(u => /stock\.css/.test(u)), 'assets load when the tab opens');
  const text = sel => page.$eval(sel, e => e.innerText.replace(/\n+/g, ' | '));
  const rows = () => page.$$eval('#stock-panel .st-row', r => r.length);
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const setv = (sel, v) => page.$eval(sel, (e, v) => { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }, v);
  const act = async (a, extra) => { await page.evaluate((a, extra) => { const e = document.querySelector('#stock-panel [data-act="' + a + '"]' + (extra || '')); if (!e) throw new Error('no control ' + a + (extra || '')); e.click(); }, a, extra); await wait(350); };
  const firstRow = () => text('#stock-panel .st-row');
  const openFirst = async () => { await page.evaluate(() => document.querySelector('#stock-panel .st-row').click()); await wait(350); };

  eq(await rows(), 50, 'first page is 50 rows');
  ok(/50 of 218/.test(await text('#st-count')) || /50 of 215/.test(await text('#st-count')), 'count line: ' + await text('#st-count'));
  eq(await page.$$eval('#st-chips .st-chip', c => c.length), 7, '7 status chips');
  await page.evaluate(() => document.querySelector('#st-chips [data-status="sold"]').click()); await wait(500);
  ok((await page.$$eval('#stock-panel .st-row .st-tag', t => t.every(x => /sold/i.test(x.className)))), 'Sold chip shows only sold items');
  await page.evaluate(() => document.querySelector('#st-chips [data-status=""]').click()); await wait(400);

  await act('add'); await setv('#sf-title', 'UI flow item'); await setv('#sf-buy', '30'); await act('submit');
  await setv('#st-q', 'UI flow item'); await wait(700);
  eq(await rows(), 1, 'search finds the new item'); ok(/IN STOCK/i.test(await firstRow()) && /30\.00/.test(await firstRow()), 'new item: ' + await firstRow());
  ok(await page.$('.st-undo') !== null, 'undo bar after add');

  await openFirst(); await act('do', '[data-do="list"]'); await setv('#sf-platform', 'vinted'); await setv('#sf-list', '80'); await act('submit');
  ok(/LISTED/i.test(await firstRow()) && /80\.00/.test(await firstRow()), 'listed: ' + await firstRow());
  await openFirst(); await act('do', '[data-do="reprice"]'); await setv('#sf-newprice', '90'); await act('submit');
  ok((await page.$eval('.st-fe[data-for="newprice"]', e => e.innerText)).length > 0, 'a higher price is refused inline');
  await setv('#sf-newprice', '70'); await act('submit'); ok(/70\.00/.test(await firstRow()), 'repriced: ' + await firstRow());
  await openFirst(); await act('do', '[data-do="reserve"]'); ok(/RESERVED/i.test(await firstRow()), 'reserved');
  await openFirst(); await act('do', '[data-do="sold"]'); await setv('#sf-sold', '65,00'); await setv('#sf-soldon', '2026-11-02');
  ok(/35\.00/.test(await text('#st-prev')), 'live profit preview: ' + await text('#st-prev'));
  await act('submit'); ok(/SOLD/i.test(await firstRow()) && /35\.00/.test(await firstRow()), 'sold with profit: ' + await firstRow());
  await act('undo'); await wait(300); ok(/RESERVED/i.test(await firstRow()), 'undo takes the sale back: ' + await firstRow());
  await openFirst(); await act('do', '[data-do="sold"]'); await setv('#sf-sold', '65,00'); await setv('#sf-soldon', '2026-11-02'); await act('submit');
  await openFirst(); await act('do', '[data-do="returned"]'); await setv('#sf-returnedon', '2026-11-02'); await setv('#sf-retship', '4,50'); await act('submit');
  ok(/RETURNED/i.test(await firstRow()), 'returned: ' + await firstRow());
  await openFirst(); await wait(300);
  const hist = await page.$$eval('#st-tl li', l => l.map(x => x.className + ':' + x.innerText.replace(/\n+/g, ' ')));
  eq(hist.map(h => h.split(':')[0]), ['bought', 'listed', 'sale', 'return'], 'timeline kinds in order');
  ok(/39\.50/.test(hist[3]) && /REVERSAL/.test(hist[3]), 'reversal -39.50 on the return row: ' + hist[3]);
  await act('do', '[data-do="wo"]'); await setv('#sf-reason', 'damaged'); await act('submit'); ok(/WRITTEN OFF/i.test(await firstRow()), 'written off');
  await openFirst(); await setv('#sf-title', 'UI flow item edited'); await setv('#sf-brand', 'Barbour'); await act('save-detail'); await wait(300);
  ok(/UI flow item edited/.test(await firstRow()) && /Barbour/.test(await firstRow()), 'edit saved: ' + await firstRow());
  await openFirst(); await act('do', '[data-do="delete"]'); eq(await rows(), 0, 'deleted item leaves the list');
  await act('deleted'); ok(/UI flow item edited/.test(await firstRow()), 'it is in Recently deleted'); await act('restore'); await act('deleted'); eq(await rows(), 1, 'restored');
  await act('add'); await page.keyboard.press('Escape'); await wait(200); eq(await page.$('.st-sheet'), null, 'Escape closes the sheet');
  eq(await page.evaluate(() => window.__qaErrors.length), 0, 'no window errors in the mock');
  await page.close();

  // ---- 3. French, Free account over the cap, phone width
  page = await open('plan=free&stock=all&stock_seed=acceptance&stock_today=2026-11-02&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.waitForFunction(() => { const t = document.getElementById('bottombar-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#bottombar-tab-stock'); await page.waitForSelector('#stock-panel .st-row', { timeout: 8000 });
  ok(/ajouter un article/i.test(await page.$eval('#stock-panel .st-head', e => e.innerText)), 'French title row');
  ok(/articles sur 25/.test(await text('.st-meter')) && /Voir les plans/.test(await text('.st-meter')), 'French cap meter: ' + await text('.st-meter'));
  const geo = await page.evaluate(() => ({ vw: innerWidth, sw: document.documentElement.scrollWidth, over: [...document.querySelectorAll('#stock-panel .st-row')].filter(r => r.scrollWidth > r.clientWidth + 1).length,
    small: [...document.querySelectorAll('#stock-panel .st-btn, #stock-panel .st-chip, #stock-panel .st-in')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 43.5).length }));
  eq([geo.sw <= geo.vw, geo.over, geo.small], [true, 0, 0], 'no horizontal overflow, no row overflow, every control >= 44 px at 390: ' + JSON.stringify(geo));
  eq(await page.evaluate(() => getComputedStyle(document.getElementById('filter-pill')).visibility), 'hidden', 'the feed filter pill is hidden on the Stock tab');
  await act('add'); await setv('#sf-title', 'Au-dela de la limite'); await act('submit');
  ok(/Le plan Free garde 25 articles/.test(await text('#st-sheet-err')) && /Voir les plans/.test(await text('#st-sheet-err')), 'French Free-limit error: ' + await text('#st-sheet-err'));
  await setv('#sf-buy', 'abc'); await act('submit'); ok(/Saisis un montant comme 12,50/.test(await page.$eval('.st-fe[data-for="buy"]', e => e.innerText)), 'French amount error');
  eq(await page.evaluate(() => window.__qaErrors.length), 0, 'no window errors (French)');
  await page.close();

  await browser.close(); server.close();
  if (errors.length) { console.log('PAGE ERRORS:\n' + errors.join('\n')); process.exit(1); }
  console.log(`PASS: ${passed} browser checks (Stock tab gating, lazy load, full item lifecycle, undo, history, delete/restore, French + Free cap, 390 px)`);
})().catch(async e => { console.error('FAIL', e && e.stack || e); try { server.close(); } catch (x) {} process.exit(1); });
