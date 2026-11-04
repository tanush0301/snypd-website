/*
 * Browser test for the Market price fix (Session 66): the REAL dashboard.html in headless Chrome, ops/qa_mock.js standing
 * in for Supabase and api.snypd.store (?pr=1 seeds rated Feed cards; the mock's market/snapshot returns search + source).
 *   node ops/test_market_fix.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: one tap on a Feed card opens the answer in a sheet (no tab switch) with brand + title sent and the card's condition
 * used; three asking prices + max buy price (40% default, editable, remembered); "Compared on" / ignored chips add a word
 * back; "Try without" re-runs without it; source line; Escape closes; Free keeps the old locked path with no request;
 * French; 390 px without horizontal overflow; no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    if (p === '/plans') return send('<!doctype html>plans', 'text/html');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp) {
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument(() => { try { localStorage.removeItem('snypd_mr_margin'); } catch (e) {} });
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('#list .card .mkt-check', { timeout: 10000 });
    await page.evaluate(() => {
      window.__mk = [];
      const f = window.fetch;
      window.fetch = (u, o) => { if (String(u).includes('/market/snapshot')) window.__mk.push(JSON.parse((o && o.body) || '{}')); return f(u, o); };
    });
    return page;
  }
  const sheetText = p => p.$eval('.mr-sheet .mr-sheet__bd', e => e.innerText);
  const waitAnswer = p => p.waitForFunction(() => { const b = document.querySelector('.mr-sheet.on .mr-sheet__bd'); return b && !b.querySelector('.mr-loading') && b.innerText.length > 20; }, { timeout: 8000 });

  // ---- 1. Pro: one tap on a Feed card
  let page = await open('plan=elite&pr=1');
  const card = await page.$eval('#list .card .mkt-check', b => ({ t: b.dataset.marketCheck, brand: b.dataset.marketBrand, cond: b.dataset.marketCond }));
  ok(card.brand === 'Ralph Lauren' && card.cond === 'Very good', 'card button carries brand + condition: ' + JSON.stringify(card));
  await page.click('#list .card .mkt-check');
  await waitAnswer(page);
  let st = await page.evaluate(() => ({
    sheet: document.querySelector('.mr-sheet').classList.contains('on'),
    marketShown: getComputedStyle(document.getElementById('market-panel')).display !== 'none',
    req: window.__mk.slice(),
    tiles: [...document.querySelectorAll('.mr-sheet .mr-3 .v')].map(e => e.textContent),
    labels: [...document.querySelectorAll('.mr-sheet .mr-3 .l')].map(e => e.textContent),
    max: (document.querySelector('.mr-sheet [data-mr-max]') || {}).textContent,
    margin: (document.querySelector('.mr-sheet [data-mr-margin]') || {}).value,
    mine: [...document.querySelectorAll('.mr-sheet .mr-cond-row.is-mine .mr-cond-name')].map(e => e.innerText),
  }));
  eq([st.sheet, st.marketShown], [true, false], 'answer opens in a sheet over the Feed, no tab switch');
  eq(st.req, [{ q: 'Ralph Lauren ' + card.t, keep: [] }], 'brand is put in front of the title, nothing typed');
  eq(st.labels, ['Quick sale', 'Typical', 'Patient'], 'three labelled asking prices');
  eq(st.tiles, ['\u20AC35', '\u20AC42', '\u20AC50'], 'prices are the card condition (Very good) row, not the overall');
  eq([st.max, st.margin], ['\u20AC25.20', '40'], 'max buy price = typical x (100 - 40%)');
  ok(st.mine.length === 1 && /Very good/.test(st.mine[0]) && /this item/.test(st.mine[0]), 'the item own condition is marked in the ladder');
  let txt = await sheetText(page);
  ok(/Asking prices, not sold prices\./.test(txt), 'says asking, not sold');
  ok(/Asking prices on vinted\.be \(EU listings\), in EUR, last 14 days\./.test(txt), 'source line');
  ok(/Compared on: /.test(txt), 'compared-on line');
  // margin edit
  await page.$eval('.mr-sheet [data-mr-margin]', e => { e.value = '30'; e.dispatchEvent(new Event('input', { bubbles: true })); });
  eq(await page.$eval('.mr-sheet [data-mr-max]', e => e.textContent), '\u20AC29.40', 'margin 30% -> max buy updates in place');
  eq(await page.evaluate(() => localStorage.getItem('snypd_mr_margin')), '30', 'margin remembered');
  await page.keyboard.press('Escape');
  ok(!(await page.$eval('.mr-sheet', e => e.classList.contains('on'))), 'Escape closes the sheet');
  // reopen: remembered margin used
  await page.evaluate(() => { window.__mk.length = 0; });
  await page.click('#list .card .mkt-check');
  await waitAnswer(page);
  eq(await page.$eval('.mr-sheet [data-mr-margin]', e => e.value), '30', 'reopened answer uses the remembered margin');
  await page.click('.mr-sheet .mr-sheet__x');
  ok(!(await page.$eval('.mr-sheet', e => e.classList.contains('on'))), 'close button closes the sheet');

  // ---- 2. Market panel: ignored words + add back + try without
  await page.evaluate(() => { document.querySelector('[data-view="market"]').click(); });
  await page.waitForFunction(() => getComputedStyle(document.getElementById('market-panel')).display !== 'none', { timeout: 5000 });
  await page.$eval('#mr-query', e => { e.value = 'nike p6000 size 8'; });
  await page.evaluate(() => { window.__mk.length = 0; });
  await page.click('#mr-go');
  await page.waitForSelector('#mr-result [data-mr-keep]', { timeout: 6000 });
  st = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#mr-result [data-mr-keep]')].map(b => b.innerText.replace(/\s+/g, ' ')),
    on: (document.querySelector('#mr-result .mr-cmp b') || {}).textContent, req: window.__mk.slice() }));
  eq(st.on, 'nike p6000', 'compared on the cleaned words');
  eq(st.chips, ['+ size size', '+ 8 size'].map(s => s.replace('+ ', '')), 'ignored words shown with the reason');
  await page.click('#mr-result [data-mr-keep="8"]');
  await page.waitForFunction(() => window.__mk.length === 2 && !document.querySelector('#mr-result .mr-loading'), { timeout: 6000 });
  st = await page.evaluate(() => ({ req: window.__mk[1], on: (document.querySelector('#mr-result .mr-cmp b') || {}).textContent }));
  eq(st.req, { q: 'nike p6000 size 8', keep: ['8'] }, 'tap on an ignored word re-runs with it kept');
  eq(st.on, 'nike p6000 8', 'the kept word is now compared on');
  await page.$eval('#mr-query', e => { e.value = 'jordan 1 travis'; });
  await page.click('#mr-go');
  await page.waitForSelector('#mr-result [data-mr-drop="travis"]', { timeout: 6000 });
  txt = await page.$eval('#mr-result', e => e.innerText);
  ok(/Try without:/.test(txt), 'thin answer offers "Try without"');
  await page.click('#mr-result [data-mr-drop="travis"]');
  await page.waitForFunction(() => !document.querySelector('#mr-result .mr-loading') && document.querySelector('#mr-result .mr-3'), { timeout: 6000 });
  eq(await page.$eval('#mr-query', e => e.value), 'jordan 1', 'try without updates the search box');
  eq(await page.evaluate(() => window.__mk[window.__mk.length - 1]), { q: 'jordan 1', keep: [] }, 'and re-runs without the word');
  await page.close();

  // ---- 3. Free: old path, no request, locked panel
  page = await open('plan=free&pr=1');
  await page.click('#list .card .mkt-check');
  await wait(600);
  st = await page.evaluate(() => ({ sheet: !!document.querySelector('.mr-sheet.on'), req: window.__mk.length,
    locked: getComputedStyle(document.getElementById('mr-locked')).display !== 'none',
    marketShown: getComputedStyle(document.getElementById('market-panel')).display !== 'none' }));
  eq(st, { sheet: false, req: 0, locked: true, marketShown: true }, 'Free: no sheet, no request, the locked Market panel as before');
  await page.close();

  // ---- 4. French + phone
  page = await open('plan=elite&pr=1&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.click('#list .card .mkt-check');
  await waitAnswer(page);
  await wait(500);
  txt = await sheetText(page);
  ok(/Vente rapide/i.test(txt) && /Typique/i.test(txt) && /Comparé sur/i.test(txt) && /Prix demandés sur vinted\.be \(annonces UE\), en EUR, 14 derniers jours\./.test(txt), 'French answer: ' + txt.slice(0, 160));
  ok(/Paie au maximum/i.test(txt) && /cet article/i.test(txt), 'French max-buy line + this-item mark');
  ok(!/prix de vente/i.test(txt), 'French never says "prix de vente"');
  ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, '390 px: no horizontal overflow with the sheet open');
  const box = await page.$eval('.mr-sheet__box', e => { const r = e.getBoundingClientRect(); return { w: r.width, b: r.bottom }; });
  ok(box.w <= 390 && box.b <= 845, '390 px: sheet fits the screen as a bottom sheet ' + JSON.stringify(box));
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' market-fix checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
