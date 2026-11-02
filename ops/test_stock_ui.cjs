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
  const openItems = async p => { await p.waitForSelector('#stock-panel .st-navb', { timeout: 8000 }); await p.evaluate(() => document.querySelector('#stock-panel .st-navb[data-view="items"]').click()); };
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
  await openItems(page);
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
  ok(/^Showing 50 of 21[58]$/.test(await text('#st-showing')), 'footer line (design): ' + await text('#st-showing'));
  ok(/^\d+ held \u00b7 21[58] rows$/.test(await text('#st-itemssub')), 'Items title line: N held . N rows: ' + await text('#st-itemssub'));
  eq(await page.$$eval('.st-th > span', s => s.map(x => x.textContent)), ['Item', 'Status', 'Platform', 'Bought', 'Days in stock', 'Price or profit'], 'table columns (design Ca)');
  { const tiles = await page.$$eval('.st-row .st-tile2', e => e.length); ok(tiles === 50, 'an initials tile on every row (' + tiles + ')'); }
  await setv('#st-q', 'Detroit jacket'); await wait(700); { const stale = await page.$$eval('.st-row .st-tag.stale', e => e.length), amber = await page.$$eval('.st-row .c-age.st-warnv', e => e.length); ok(stale > 0 && stale === amber, 'old held items carry the STALE tag and an amber day count (' + stale + ')'); }
  await setv('#st-q', ''); await wait(600);
  await setv('#st-plat', 'depop'); await wait(600); { const pl = await page.$$eval('#stock-panel .st-row .c-plat', e => e.map(x => x.textContent)); ok(pl.length > 0 && pl.every(x => x === 'Depop'), 'platform filter: only Depop rows (' + pl.length + ')'); }
  await setv('#st-plat', ''); await wait(500);
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
  // ---- 2b. export (step 2): every non-deleted item, design column set, a missing value stays empty
  await page.evaluate(() => { window.__dl = []; const o = URL.createObjectURL.bind(URL); URL.createObjectURL = b => { window.__dl.push(b); return o(b); }; });
  await act('export'); await wait(1500);
  const csvr = await page.evaluate(async () => { const b = window.__dl[0]; if (!b) return null; const u = new Uint8Array(await b.arrayBuffer()); return { bom: u[0] === 0xef && u[1] === 0xbb && u[2] === 0xbf, text: await b.text() }; }), csv = csvr.text;
  const expectN = await page.evaluate(() => window.__qaStock.state.items.filter(i => !i.deleted_at).length);
  ok(!!csv && csvr.bom && /^Item,Brand,Size,Status,Condition,Category,Buy price,Extra costs,Date bought,Source,Platform,List price,Sold price,Date sold,Profit,Notes\r\n/.test(csv), 'export: header row, UTF-8 BOM');
  eq(csv.trim().split('\r\n').length - 1, expectN, 'export: one row per non-deleted item (' + expectN + ')');
  ok(/,Sold,/.test(csv) && !/NaN|undefined|null/.test(csv), 'export: sold rows present, no NaN/undefined/null');
  ok(/Exported \d+ items to snypd-stock-\d{4}-\d{2}-\d{2}\.csv/.test(await text('.st-undo')), 'export: result line: ' + await text('.st-undo'));

  await page.close();

  // ---- 3. French, Free account over the cap, phone width
  page = await open('plan=free&stock=all&stock_seed=acceptance&stock_today=2026-11-02&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.waitForFunction(() => { const t = document.getElementById('bottombar-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#bottombar-tab-stock'); await openItems(page); await page.waitForSelector('#stock-panel .st-row', { timeout: 8000 });
  ok(/ajouter un article/i.test(await page.$eval('#stock-panel .st-navrow', e => e.innerText)), 'French title row');
  ok(/tes articles\s+\d+ \/ 25/i.test(await text('.st-meter')) && /Voir les plans/.test(await text('#st-capmsg')), 'French cap meter: ' + await text('.st-meter') + ' / ' + await text('#st-capmsg'));
  const geo = await page.evaluate(() => ({ vw: innerWidth, sw: document.documentElement.scrollWidth, over: [...document.querySelectorAll('#stock-panel .st-row')].filter(r => r.scrollWidth > r.clientWidth + 1).length,
    small: [...document.querySelectorAll('#stock-panel .st-btn, #stock-panel .st-chip, #stock-panel .st-in')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 43.5).length }));
  eq([geo.sw <= geo.vw, geo.over, geo.small], [true, 0, 0], 'no horizontal overflow, no row overflow, every control >= 44 px at 390: ' + JSON.stringify(geo));
  eq(await page.evaluate(() => getComputedStyle(document.getElementById('filter-pill')).visibility), 'hidden', 'the feed filter pill is hidden on the Stock tab');
  await act('add'); await setv('#sf-title', 'Au-dela de la limite'); await act('submit');
  ok(/Le plan Free garde 25 articles/.test(await text('#st-sheet-err')) && /Voir les plans/.test(await text('#st-sheet-err')), 'French Free-limit error: ' + await text('#st-sheet-err'));
  await setv('#sf-buy', 'abc'); await act('submit'); ok(/Saisis un montant comme 12,50/.test(await page.$eval('.st-fe[data-for="buy"]', e => e.innerText)), 'French amount error');
  eq(await page.evaluate(() => window.__qaErrors.length), 0, 'no window errors (French)');
  await page.close();

  // ---- 4. import (step 4): real files through the real file input
  const os = require('node:os');
  const imp = path.join(root, 'ops/stock/import');
  const tmp = (name, content) => { const p = path.join(os.tmpdir(), 'stock-ui-' + process.pid + '-' + name); fs.writeFileSync(p, content); return p; };
  const upload = async (page, file) => { await page.evaluate(() => document.querySelector('#stock-panel [data-act="import"]').click()); await new Promise(r => setTimeout(r, 300)); const input = await page.$('#im-file'); await input.uploadFile(file); await new Promise(r => setTimeout(r, 900)); };
  const clickA = async (page, a) => { await page.evaluate(a => document.querySelector('#stock-panel [data-act="' + a + '"]').click(), a); await new Promise(r => setTimeout(r, 500)); };
  const sheetText = page => page.$eval('.st-sheet', e => e.innerText.replace(/\n+/g, ' | '));
  const setSel = (page, sel, v) => page.$eval(sel, (e, v) => { e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); }, v);

  page = await open('plan=elite&stock=all&stock_today=2026-11-02&lang=en');
  page.on('dialog', d => d.accept());
  await page.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#view-tab-stock'); await openItems(page); await page.waitForSelector('#stock-panel .st-navrow', { timeout: 8000 });
  await upload(page, path.join(imp, 'template-fr.xlsx'));
  let txt = await sheetText(page);
  ok(/template-fr\.xlsx/.test(txt) && /3 rows make 5 items/.test(txt), 'review: ' + txt.slice(0, 200));
  ok(/comme neuf/i.test(txt) && /vintage/i.test(txt) && /import 5 items/i.test(txt), 'review lists the unknown condition, the new category and the item count: ' + txt);
  ok(!/Dates like/i.test(txt), 'no date-order question: 27/10 makes it certain');
  await setSel(page, '[data-im="cond"]', 'very_good'); await wait(300);
  ok(!/Conditions we do not know/i.test(await sheetText(page)), 'the mapped condition leaves the list');
  const base0 = await page.evaluate(() => window.__qaStock.state.items.length);   // the mock seeds 3 Feed claims that are mirrored into Stock
  await clickA(page, 'im-go'); await wait(900);
  txt = await sheetText(page); ok(/Imported 5 items/.test(txt) && /from 3 rows/.test(txt), 'done: ' + txt.slice(0, 160));
  eq(await page.evaluate(() => window.__qaStock.state.items.filter(i => i.import_id).length), 5, 'five items in the engine');
  eq(await page.evaluate(() => window.__qaStock.state.categories.filter(c => c.key === 'c-vintage').length), 1, 'the new category was created');
  eq(await page.evaluate(() => window.__qaStock.state.items.filter(i => i.condition === 'very_good').length >= 4), true, 'the user\'s condition mapping was applied');
  await clickA(page, 'im-undo'); await wait(700);
  eq(await page.evaluate(() => [window.__qaStock.state.items.length, window.__qaStock.state.items.filter(i => i.import_id).length]), [base0, 0], 'undo this import removes every item of the import and nothing else');
  eq(await rows(), base0, 'and the list is back to what it was');

  // ambiguous dates: the screen asks, the answer decides
  const csv1 = tmp('amb.csv', 'Item;Buy price;Bought\nJacket;12,50;03/04/2026\nTee;5;05/06/2026\n');
  await upload(page, csv1); txt = await sheetText(page);
  ok(/Dates like 03\/04\/2026 can be read two ways/i.test(txt) && /Day first/i.test(txt), 'date-order question for ambiguous dates: ' + txt.slice(0, 300));
  await page.evaluate(() => document.querySelector('[data-im="order"][value="mdy"]').click()); await wait(300);
  await page.evaluate(() => { const r = document.querySelector('[data-im="order"][value="mdy"]'); r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true })); }); await wait(300);
  await clickA(page, 'im-go'); await wait(800);
  eq(await page.evaluate(() => window.__qaStock.state.items.filter(i => i.import_id).map(i => i.bought_on + ':' + i.buy_cents).sort()), ['2026-03-04:1250', '2026-05-06:500'], 'month-first choice applied, ";" file read with decimal commas');
  await page.keyboard.press('Escape'); await wait(200);

  // refusals
  await upload(page, tmp('old.xls', 'not really an xls')); ok(/Old \.xls files are not supported/.test(await sheetText(page)), 'old .xls refused with a clear message');
  await page.evaluate(() => document.querySelector('#im-file').value = ''); await page.keyboard.press('Escape'); await wait(200);
  await upload(page, tmp('notitle.csv', 'Brand,Buy price\nNike,5\n')); ok(/No column looks like the item title/.test(await sheetText(page)), 'a file without a title column is explained');
  await page.keyboard.press('Escape'); await wait(200);
  eq(await page.evaluate(() => window.__qaErrors.length), 0, 'no window errors (import)');
  await page.close();

  // Free account: the cap preview and the partial import
  page = await open('plan=free&stock=all&stock_today=2026-11-02&lang=en');
  page.on('dialog', d => d.accept());
  await page.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#view-tab-stock'); await page.waitForSelector('#stock-panel .st-navrow', { timeout: 8000 });
  await upload(page, tmp('thirty.csv', 'Item,Buy price\n' + Array.from({ length: 30 }, (_, i) => 'Thing ' + i + ',5').join('\n') + '\n'));
  const heldBefore = await page.evaluate(() => window.__qaStock.state.items.filter(i => ['stock', 'listed', 'reserved', 'returned'].includes(i.status) && !i.deleted_at).length), fits = 25 - heldBefore;
  txt = await sheetText(page); ok(new RegExp('The Free plan holds 25 items: ' + fits + ' of your held items fit and ' + (30 - fits) + ' would be left out').test(txt), 'cap preview before importing: ' + txt.slice(0, 260));
  await clickA(page, 'im-go'); await wait(900); txt = await sheetText(page);
  ok(new RegExp('Imported ' + fits + ' items').test(txt) && new RegExp((30 - fits) + ' rows were not imported', 'i').test(txt) && /over the Free plan limit/.test(txt) && /see plans/i.test(txt), 'partial import reported: ' + txt.slice(0, 260));
  eq(await page.evaluate(() => window.__qaStock.state.items.filter(i => ['stock', 'listed', 'reserved', 'returned'].includes(i.status) && !i.deleted_at).length), 25, 'the account holds exactly 25, not 30');
  await page.close();

  // French review on a phone
  page = await open('plan=elite&stock=all&stock_today=2026-11-02&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.waitForFunction(() => { const t = document.getElementById('bottombar-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await page.click('#bottombar-tab-stock'); await page.waitForSelector('#stock-panel .st-navrow', { timeout: 8000 });
  await upload(page, tmp('mix.csv', 'Article;Prix d\'achat\nA;12,50 £\nB;5 $\n'));
  txt = await sheetText(page); ok(/Les montants sont lus en EUR/.test(txt) && /mélange des symboles de devise \(2 montants\)/.test(txt) && /importer 2 articles/i.test(txt), 'French review: ' + txt.slice(0, 260));
  const g2 = await page.evaluate(() => ({ vw: innerWidth, sw: document.documentElement.scrollWidth, sheetSW: document.querySelector('.st-sheet').scrollWidth, sheetCW: document.querySelector('.st-sheet').clientWidth }));
  ok(g2.sw <= g2.vw && g2.sheetSW <= g2.sheetCW + 1, 'import sheet fits at 390: ' + JSON.stringify(g2));
  await page.close();

  // ---- 5. step 5: Overview, Today lanes, first run, persona, settings, History swap, claims mirror
  const tc = (p, sel) => p.$eval(sel, e => e.textContent.trim());
  const waitOv = p => p.waitForSelector('#stock-panel #st-over .st-sec, #stock-panel #st-over .st-first', { timeout: 8000 });
  const fmt = (cents, cur, lng, signed) => `window.SnypdStock.formatMoney(${cents}, '${cur || 'EUR'}', '${lng || 'en'}'${signed ? ', { signed: true }' : ''})`;
  const money = (p, cents, cur, lng, signed) => p.evaluate(`${fmt(cents, cur, lng, signed)}`);
  const clickBy = (p, sel) => p.evaluate(s => { const e = document.querySelector(s); if (!e) throw new Error('no ' + s); e.click(); }, sel);
  const tabVis = (p, sel) => p.evaluate(s => { const e = document.querySelector(s); return !!e && getComputedStyle(e).display !== 'none'; }, sel);
  const wait5 = ms => new Promise(r => setTimeout(r, ms));
  const shown = (p, sel) => p.evaluate(s => { const e = document.querySelector(s); return !!e && e.offsetParent !== null; }, sel);

  // 5a. the design dataset on the Overview (desktop, English): exact acceptance numbers, then every period
  let pg = await open('plan=elite&stock=all&stock_seed=acceptance&stock_today=2026-10-27&stock_claims=0&lang=en');   // the design numbers are exact only without the mock's 3 mirrored Feed claims
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  eq(await tabVis(pg, '.view-tab[data-view="history"]'), false, 'History tab is replaced while Stock is on (top bar)');
  eq(await tabVis(pg, '.bottombar-tab[data-view="history"]'), false, 'History tab is replaced while Stock is on (phone bar)');
  await pg.click('#view-tab-stock'); await waitOv(pg);
  eq(await tc(pg, '#st-hero-held'), '58', 'Overview: 58 items held');
  { const sp = await pg.$eval('#st-over .st-t3:first-child small:last-child', e => e.textContent); ok(/18 in stock .* 36 listed .* 4 reserved/.test(sp), 'Overview: 18 / 36 / 4, got: ' + sp); }
  eq(await tc(pg, '#st-cash'), '€1,124.50', 'Overview: cash tied up EUR 1,124.50');
  eq([await tc(pg, '#st-old'), await tc(pg, '#st-old-sub')], ['12', '€318.00 at cost'], 'Overview: 12 old items, EUR 318.00 at cost');
  eq(await tc(pg, '#st-hero-net'), await money(pg, 61240, 'EUR', 'en'), 'Overview 30 days: net profit EUR 612.40 (unsigned hero, as in the design)');
  eq(await tc(pg, '#st-c-rev b'), await money(pg, 184600), 'Overview 30 days: revenue EUR 1,846.00');
  eq([await tc(pg, '#st-c-sales b'), await tc(pg, '#st-c-sales small'), await tc(pg, '#st-c-rev small')], ['31', 'last 30 days', '31 sales'], 'Overview 30 days: ITEMS SOLD 31 / last 30 days, REVENUE caption 31 sales');
  eq(await tc(pg, '#st-c-avg small'), '29 of 31 have a cost', 'Overview 30 days: 29 of 31 have a cost (never a silent partial)');
  eq(await tc(pg, '#st-partial'), '29 of 31 sold items have a cost, 2 left out until you add one', 'Overview: the design sentence under the hero number');
  eq(await tc(pg, '#st-c-avg b'), await money(pg, 2112, 'EUR', 'en'), 'Overview 30 days: average EUR 21.12');
  eq([await tc(pg, '#st-c-days b'), await tc(pg, '#st-c-days small')], ['18d', 'bought to sold'], 'Overview 30 days: 18d, bought to sold');
  eq(await tc(pg, '#st-delta'), String.fromCharCode(0x25b2) + ' ' + (await money(pg, 6280, 'EUR', 'en', true)) + ' (+11.4%) vs ' + (await money(pg, 54960, 'EUR', 'en')) + ', the 30 days before', 'Overview: the design delta line, +EUR 62.80 (+11.4%) vs 549.60');
  eq(await tc(pg, '#st-num-sub'), 'last 30 days \u00b7 vs the 30 days before', 'The numbers sub-line');
  const periodNet = async d => { await clickBy(pg, '#st-over [data-act="period"][data-days="' + d + '"]'); await pg.waitForFunction(x => document.querySelector('#st-over [data-act="period"][aria-pressed="true"]').getAttribute('data-days') === x, {}, d); await wait5(250); return tc(pg, '#st-hero-net'); };
  eq(await periodNet('7'), await money(pg, 15200, 'EUR', 'en'), '7 days: EUR 152.00');
  eq(await tc(pg, '#st-delta'), String.fromCharCode(0x25bc) + ' ' + (await money(pg, -1220, 'EUR', 'en', true)) + ' (' + String.fromCharCode(0x2212) + '7.4%) vs ' + (await money(pg, 16420, 'EUR', 'en')) + ', the 7 days before', '7 days: down arrow, against 164.20 the 7 days before');
  eq(await periodNet('90'), await money(pg, 154560, 'EUR', 'en'), '90 days: EUR 1,545.60');
  eq(await periodNet('all'), await money(pg, 290770, 'EUR', 'en'), 'all time: EUR 2,907.70');
  eq(await pg.$('#st-delta'), null, 'all time has no "before" period, so no delta line');
  eq(await tc(pg, '#st-num-sub'), 'all time', 'the sub-line follows the period');
  await periodNet('30');
  // the Today lanes against the lane rules computed independently from the items
  const lanes = await pg.evaluate(() => {
    const t0 = Date.UTC(2026, 9, 27), dd = iso => Math.round((t0 - Date.parse(iso + 'T00:00:00Z')) / 86400000), L = { reprice: 0, list: 0, follow: 0, hold: 0 };
    window.__qaStock.state.items.filter(i => !i.deleted_at && ['stock', 'listed', 'reserved', 'returned'].includes(i.status)).forEach(i => {
      const age = dd(i.returned_on || i.bought_on);
      if (i.status === 'listed' && i.listed_on && dd(i.listed_on) >= 30 && i.drops === 0) L.reprice++;
      if ((i.status === 'stock' || i.status === 'returned') && age >= 7) L.list++;
      if (i.status === 'reserved' && i.reserved_on && dd(i.reserved_on) >= 3) L.follow++;
      if ((i.status === 'stock' || i.status === 'returned') && i.src_type === 'hunt' && age >= 14) L.hold++;
    });
    const dom = {}; ['reprice', 'list', 'follow', 'hold'].forEach(k => { dom[k] = +document.querySelector('#st-lane-' + k + ' .st-lane-hd b').textContent; });
    return { want: L, dom, empties: ['reprice', 'list', 'follow', 'hold'].filter(k => !+document.querySelector('#st-lane-' + k + ' .st-lane-hd b').textContent && !document.querySelector('#st-lane-' + k + ' .st-dim')) };
  });
  eq(lanes.dom, lanes.want, 'Today lanes: the four counts follow the lane rules: ' + JSON.stringify(lanes.want));
  ok(lanes.want.reprice + lanes.want.list + lanes.want.follow + lanes.want.hold > 0, 'the dataset has something in the lanes');
  eq(lanes.empties, [], 'an empty lane says so in words');
  eq(await tc(pg, '#st-lanes-sub'), (lanes.want.reprice + lanes.want.list + lanes.want.follow) + ' things worth a minute \u00b7 Tue 27 Oct', 'Today sub-line: the three design lanes counted, with the date');
  { const rows = await pg.$$eval('#st-lane-reprice .st-lane-row', r => r.map(x => x.innerText.replace(/\n+/g, ' | ')));
    ok(rows.length > 0 && rows.every(x => /listed \d+d/.test(x) && /REPRICE/i.test(x)), 'lane rows carry the design meta line and a Reprice action: ' + rows[0]);
    const fr0 = await pg.$eval('#st-lane-follow .st-lane-row', x => x.innerText.replace(/\n+/g, ' | ')); ok(/reserved \d+d/.test(fr0) && /MARK SOLD/i.test(fr0) && /BACK TO ACTIVE/i.test(fr0), 'follow-up rows: Mark sold + Back to active: ' + fr0);
    const meta = await pg.$$eval('#st-lane-reprice .st-lane-row .a', x => x.map(e => e.textContent));
    eq(meta[0], 'Depop \u00b7 \u20ac85.00 \u00b7 listed 90d \u00b7 0 price drops', 'Reprice row meta line (design): platform, list price, days since listed (not since bought), price drops');
    const lm = await pg.$eval('#st-lane-list .st-lane-row .a', e => e.textContent); ok(/^in stock \d+d \u00b7 cost \u20ac\d/.test(lm), 'List row meta line: in stock Nd, cost: ' + lm);
    const fm = await pg.$eval('#st-lane-follow .st-lane-row .a', e => e.textContent); ok(/^[A-Za-z ]+ \u00b7 \u20ac\d+\.\d\d \u00b7 reserved \d+d$/.test(fm), 'Follow-up row meta line: platform, price, reserved Nd: ' + fm);
    // the two charts (migration 069)
    const plat = await pg.$$eval('#st-ch-plat .st-pbars li', x => x.map(e => e.innerText.replace(/\s+/g, ' ').trim()));
    eq(plat, ['Vinted \u20ac292.90 \u00b7 16 sold', 'Facebook Marketplace \u20ac116.70 \u00b7 6 sold', 'Marktplaats \u20ac103.80 \u00b7 3 sold', 'Vestiaire Collective \u20ac46.00 \u00b7 2 sold', 'eBay \u20ac34.50 \u00b7 3 sold', 'Depop \u20ac18.50 \u00b7 1 sold'], 'chart: net profit by platform = the design numbers');
    ok(/Platforms are tracked by hand\. SNYPD isn.t connected to any of them\./.test(await tc(pg, '#st-ch-plat')), 'chart: the honesty line');
    const bars = await pg.$$eval('#st-ch-day svg rect', r => r.length), svgText = await pg.$eval('#st-ch-day svg', e => e.textContent), aria = await pg.$eval('#st-ch-day svg', e => e.getAttribute('aria-label'));
    ok(bars >= 20 && bars <= 30, 'chart: one bar per day with sales (' + bars + ' of 30)'); ok(/cumulative \u20ac612\.40/.test(svgText), 'chart: cumulative \u20ac612.40 on the line: ' + svgText.slice(0, 80)); ok(/\u20ac612\.40/.test(aria) && /28 Sept?|28 Sep/.test(aria), 'chart: accessible summary: ' + aria);
    ok(/30D \u00b7 daily/.test(await tc(pg, '#st-ch-day .st-secsub')), 'chart: 30D . daily');
    await clickBy(pg, '#st-ch-plat [data-act="chart-table"]'); await wait5(250);
    eq(await pg.$$eval('#st-ch-plat table tbody tr', r => r.length), 6, 'chart: the Table toggle shows the same 6 platform rows as a real table');
    await clickBy(pg, '#st-ch-plat [data-act="chart-table"]'); await wait5(250);
    await clickBy(pg, '#st-lane-reprice [data-act="lane-act"][data-do="reprice"]'); await pg.waitForSelector('.st-sheet #sf-newprice, .st-sheet input', { timeout: 5000 });
    ok(/Lower the price/i.test(await tc(pg, '.st-sheet')), 'a lane Reprice button opens the reprice sheet for that item'); await pg.keyboard.press('Escape'); await wait5(300); }
  // a lane item opens its own detail without the Items list having been loaded
  const laneKey = ['list', 'reprice', 'follow', 'hold'].find(k => lanes.want[k] > 0);
  const laneTitle = await pg.$eval('#st-lane-' + laneKey + ' .st-lane-it .t', e => e.textContent);
  await clickBy(pg, '#st-lane-' + laneKey + ' .st-lane-it'); await pg.waitForSelector('.st-sheet', { timeout: 5000 });
  eq(await pg.$eval('.st-sheet-hd h2', e => e.textContent), laneTitle, 'lane item opens its detail (' + laneKey + ')');
  await pg.keyboard.press('Escape'); await wait5(200);
  // old items -> Items filtered, and the note clears it
  await clickBy(pg, '#st-over [data-act="see-old"]'); await pg.waitForSelector('#stock-panel .st-row', { timeout: 5000 }); await wait5(300);
  eq(await pg.$$eval('#stock-panel .st-row', r => r.length), 12, 'See old items: the 12 old items');
  ok(/Showing old items only \(45\+ days\)/.test(await pg.$eval('#st-body', e => e.textContent)), 'the old filter is visible and says how old');
  await clickBy(pg, '#st-body [data-act="clear"]'); await wait5(400);
  ok(await pg.$$eval('#stock-panel .st-row', r => r.length) > 12, 'clearing the old filter brings every item back');
  await clickBy(pg, '#stock-panel .st-navb[data-view="overview"]');

  // 5b. settings: currency relabels and never converts, persona, old threshold, validation
  const sums = () => pg.evaluate(() => window.__qaStock.state.items.reduce((a, i) => a + (i.buy_cents || 0) + (i.sold_cents || 0) + (i.extra_cents || 0), 0));
  const sumBefore = await sums();
  await clickBy(pg, '#stock-panel [data-act="settings"]'); await pg.waitForSelector('.st-sheet #sf-cur', { timeout: 5000 });
  ok(/Your amounts keep their numbers\. Nothing is converted\./.test(await pg.$eval('.st-sheet', e => e.textContent)), 'the settings say nothing is converted');
  await pg.$eval('#sf-old', e => { e.value = '5'; }); await clickBy(pg, '#st-go'); await wait5(300);
  ok(/7 to 365/.test(await pg.$eval('.st-fe[data-for="old"]', e => e.textContent)) && !!(await pg.$('.st-sheet')), 'an old threshold outside 7 to 365 is refused inline and the sheet stays');
  eq(await pg.evaluate(() => window.__qaStock.state.settings), null, 'nothing was saved by the refused form');
  await pg.select('#sf-cur', 'GBP'); await clickBy(pg, '#sf-persona [data-p="resell"]'); await pg.$eval('#sf-old', e => { e.value = '60'; });
  await clickBy(pg, '#st-go'); await pg.waitForFunction(() => !document.querySelector('.st-sheet'), { timeout: 5000 }); await wait5(500);
  eq(await pg.evaluate(() => { const s = window.__qaStock.state.settings; return [s.currency, s.persona, s.old_after_days]; }), ['GBP', 'resell', 60], 'settings saved (currency, persona, old after)');
  eq(await tc(pg, '#st-cash'), await money(pg, 112450, 'GBP', 'en'), 'currency relabelled: the same 1,124.50 now in GBP');
  eq(await sums(), sumBefore, 'no stored amount changed: nothing is converted');
  ok(/Currency set to GBP\. Your amounts kept their numbers\./.test(await tc(pg, '#st-undo-root')), 'toast says the amounts kept their numbers');
  const old60 = await pg.evaluate(() => { const t0 = Date.UTC(2026, 9, 27); return window.__qaStock.state.items.filter(i => !i.deleted_at && ['stock', 'listed', 'reserved', 'returned'].includes(i.status) && Math.round((t0 - Date.parse((i.returned_on || i.bought_on) + 'T00:00:00Z')) / 86400000) >= 60).length; });
  eq(+(await tc(pg, '#st-old')), old60, 'the stale count follows the new threshold: ' + old60);
  ok(/Stale 60d\+/.test(await pg.$eval('#st-over', e => e.textContent)), 'the stale label says 60d+');
  eq(await pg.evaluate(() => window.__qaErrors.length), 0, 'no window errors in the mock (5a, 5b)');

  // 5c. hiding the tab brings History back; Profile brings Stock back; a tapped History link lands on Stock while it replaces History
  eq(await pg.evaluate(() => { window.SNYPD.switchView('history'); return document.querySelector('.view-tab.active').getAttribute('data-view'); }), 'stock', 'a History link lands on Stock while Stock replaces History');
  await clickBy(pg, '#stock-panel [data-act="settings"]'); await pg.waitForSelector('.st-sheet #sf-tab', { timeout: 5000 });
  await pg.$eval('#sf-tab', e => { e.checked = false; }); await clickBy(pg, '#st-go'); await wait5(700);
  eq([await tabVis(pg, '#view-tab-stock'), await tabVis(pg, '.view-tab[data-view="history"]'), await pg.evaluate(() => document.querySelector('.view-tab.active').getAttribute('data-view'))], [false, true, 'feed'], 'Show the Stock tab off: Stock tab gone, History back, the page moves to the Feed');
  eq(await pg.evaluate(() => window.__qaStock.state.settings.tab_hidden), true, 'tab_hidden saved');
  await clickBy(pg, '#topbar-profile-trigger'); await wait5(300);
  eq(await shown(pg, '#prof-stock-row'), true, 'Profile offers the way back');
  await clickBy(pg, '#prof-stock-show'); await pg.waitForFunction(() => document.querySelector('.view-tab.active').getAttribute('data-view') === 'stock', { timeout: 6000 }); await wait5(300);
  eq([await tabVis(pg, '#view-tab-stock'), await tabVis(pg, '.view-tab[data-view="history"]'), await pg.evaluate(() => window.__qaStock.state.settings.tab_hidden)], [true, false, false], 'Show again: Stock tab back, History replaced, saved');
  await pg.close();

  // 5d. the switch off: History is the History tab and Stock is not there at all; a hidden tab at page load comes from dashboard_boot
  pg = await open('plan=elite&stock=off&lang=en');
  await wait5(1500);
  eq([await tabVis(pg, '#view-tab-stock'), await tabVis(pg, '.view-tab[data-view="history"]'), await tabVis(pg, '.bottombar-tab[data-view="history"]')], [false, true, true], 'stock_mode off: History tabs shown, Stock tab hidden');
  await pg.close();
  pg = await open('plan=elite&stock=all&stock_hidden=1&lang=en');
  await wait5(1500);
  eq([await tabVis(pg, '#view-tab-stock'), await tabVis(pg, '.view-tab[data-view="history"]'), await shown(pg, '#prof-stock-row')], [false, true, false], 'tab hidden by the user: History stays, Stock hidden on first paint (Profile row only shows on Profile)');
  await clickBy(pg, '#topbar-profile-trigger'); await wait5(300);
  eq(await shown(pg, '#prof-stock-row'), true, 'and Profile shows the Show button');
  await pg.close();

  // 5e. first run: an empty account sees the import-first screen and the optional persona question
  pg = await open('plan=free&stock=all&stock_claims=0&lang=en');
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  ok(/Your stock is already in a spreadsheet\. Bring it in\./.test(await tc(pg, '#st-first h2')), 'first run: headline from the design');
  eq([!!(await pg.$('#st-first [data-act="import"]')), !!(await pg.$('#st-first [data-act="add"]')), (await pg.$$('#st-pq .st-segb')).length], [true, true, 3], 'first run: Import, Add one item, three persona choices');
  ok(/Free holds up to 25 items\. Exporting your data is free on every plan\./.test(await tc(pg, '#st-first')), 'a Free account sees the design footer line');
  // step 2: design first run (wall, copy, template), sub-nav with count + meter
  eq((await pg.$$('.st-wall .st-tile')).length, 60, 'first run: decorative wall of 60 tiles');
  const frTxt = await tc(pg, '#st-first');
  ok(/IMPORT FROM A SPREADSHEET/i.test(frTxt) && /\.xlsx, \.csv\. In Google Sheets use File > Download > CSV\./.test(frTxt) && /Download our template/.test(frTxt) && /Item name, price paid, date, source\./.test(frTxt) && /STOCK . GET STARTED/i.test(frTxt), 'first run: every line of the design card: ' + frTxt);
  eq([await tc(pg, '#st-navn'), /Your items\s+0 \/ 25/i.test(await tc(pg, '.st-navrow .st-meter')), !!(await pg.$('.st-navrow [data-view="analytics"]'))], ['0', true, false], 'sub-nav: ITEMS 0, YOUR ITEMS 0 / 25 on the right, no Analytics/Reports tab yet');
  await pg.evaluate(() => { window.__dl = []; const o = URL.createObjectURL.bind(URL); URL.createObjectURL = b => { window.__dl.push(b); return o(b); }; });
  await clickBy(pg, '#st-first [data-act="template"]'); await wait5(300);
  const tplr = await pg.evaluate(async () => { const b = window.__dl[0]; if (!b) return null; const u = new Uint8Array(await b.arrayBuffer()); return { bom: u[0] === 0xef && u[1] === 0xbb && u[2] === 0xbf, text: await b.text() }; }), tpl = tplr.text;
  ok(tplr.bom && /^Item,Brand,Size,Condition,Category,Quantity,Bought,Buy price,Extra costs,Source,Platform,List price,Sold price,Sold date,Fees,Shipping paid,Notes\r\n$/.test(tpl), 'template CSV: 17 headers, BOM, nothing else: ' + JSON.stringify(tpl));
  await clickBy(pg, '#st-pq [data-p="resell"]'); await pg.waitForFunction(() => !document.querySelector('#st-pq'), { timeout: 5000 });
  eq(await pg.evaluate(() => window.__qaStock.state.settings.persona), 'resell', 'answering writes the persona once');
  ok(!!(await pg.$('#st-first')) && !(await pg.$('#st-first-light')), 'Resell keeps the import-first screen');
  await clickBy(pg, '#st-first [data-act="add"]'); await pg.waitForSelector('.st-sheet #sf-title', { timeout: 5000 });
  await pg.type('#sf-title', 'First item'); await pg.type('#sf-buy', '10'); await clickBy(pg, '#st-go'); await pg.waitForFunction(() => !document.querySelector('.st-sheet'), { timeout: 5000 }); await wait5(700);
  eq([await tc(pg, '#st-hero-held'), !!(await pg.$('#st-first'))], ['1', false], 'the first item turns the first-run screen into the Overview');
  eq(await pg.$eval('#st-hero-net', e => e.textContent.trim()), '--', 'no sale yet: net profit is -- and says how to get one');
  ok(/Net profit appears when you mark an item sold\./.test(await tc(pg, '#st-over')), 'the empty-profit sentence');
  await pg.close();

  pg = await open('plan=elite&stock=all&stock_claims=0&lang=en');
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  await clickBy(pg, '#st-pq [data-p="buy"]'); await pg.waitForSelector('#st-first-light', { timeout: 5000 });
  ok(/Keep track of what you buy/.test(await tc(pg, '#st-first-light h2')) && !!(await pg.$('#st-first-light [data-act="hide-tab"]')), 'Buy for myself: the light card with Hide the tab');
  await clickBy(pg, '#st-first-light [data-act="hide-tab"]'); await wait5(700);
  eq([await tabVis(pg, '#view-tab-stock'), await pg.evaluate(() => window.__qaStock.state.settings.tab_hidden)], [false, true], 'Hide the tab: hidden and saved');
  await pg.close();

  pg = await open('plan=elite&stock=all&stock_claims=0&lang=en');
  await pg.evaluate(() => { try { localStorage.removeItem('snypd_stock_pq_skipped'); } catch (e) {} });
  await pg.reload({ waitUntil: 'domcontentloaded' });
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  await clickBy(pg, '#st-pq [data-act="pq-skip"]'); await wait5(300);
  eq([!!(await pg.$('#st-pq')), await pg.evaluate(() => window.__qaStock.state.settings)], [false, null], 'Skip hides the question and writes nothing');
  await pg.reload({ waitUntil: 'domcontentloaded' });
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  eq(!!(await pg.$('#st-pq')), false, 'a skipped question is not asked again');
  await pg.evaluate(() => { try { localStorage.removeItem('snypd_stock_pq_skipped'); } catch (e) {} });
  await pg.close();

  // French first run: no English left
  pg = await open('plan=free&stock=all&stock_claims=0&lang=fr');
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  const frText = await pg.$eval('#st-over', e => e.innerText);
  ok(/Ton stock est déjà dans un tableur\. Importe-le\./.test(frText) && /Importer un tableur/i.test(frText) && /Télécharge notre modèle/.test(frText) && /\+ Ajouter un article/i.test(frText) && /Gratuit\s: jusqu.à 25 articles\. Exporter tes données est gratuit avec toutes les formules\./.test(frText) && /Tes articles\s+0 \/ 25/i.test(await pg.$eval('.st-navrow', e => e.innerText)), 'French first run (design pairs): ' + frText.replace(/\n+/g, ' | ').slice(-420));
  ok(!/Start with|Import your|Add one|Resell|I mainly|Skip|Free for|Download our|Your items/i.test(frText), 'French first run has no English left');
  await pg.close();

  // 5f. a claim made in the Feed lands in Stock with its own note
  pg = await open('plan=elite&stock=all&lang=en');
  await pg.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
  await pg.click('#view-tab-stock'); await waitOv(pg);
  const heldPre = +(await tc(pg, '#st-hero-held'));
  await pg.evaluate(() => window.SNYPD.supabase.from('user_claims').insert({ id: 'claim-9', user_id: 'qa-user-0000-0000-0000-000000000001', listing_id: 9009, title: 'Mirror Test Item', brand_title: 'Nike', size_title: 'M', vinted_url: 'https://www.vinted.be/items/9009', bought_price_cents: 1500, status: 'holding', claimed_at: new Date().toISOString() }));
  await pg.evaluate(() => window.SNYPD.openStock()); await wait5(900);
  eq(+(await tc(pg, '#st-hero-held')), heldPre + 1, 'a new Feed claim adds one held item to the Overview');
  await clickBy(pg, '#stock-panel .st-navb[data-view="items"]'); await pg.waitForSelector('#stock-panel .st-row', { timeout: 5000 }); await wait5(300);
  await pg.evaluate(() => { const r = [...document.querySelectorAll('#stock-panel .st-row')].find(x => /Mirror Test Item/.test(x.textContent)); if (!r) throw new Error('claim item not in the list'); r.click(); });
  await pg.waitForSelector('.st-sheet', { timeout: 4000 }); await wait5(300);
  ok(/pressed Claim in the Feed/.test(await pg.$eval('.st-sheet', e => e.textContent)), 'the item says it came from a Feed claim');
  await pg.close();

  // 5g. phone width, English and French: no overflow, every control 44 px
  for (const lng of ['en', 'fr']) {
    pg = await open('plan=free&stock=all&stock_seed=acceptance&stock_today=2026-11-02&stock_claims=0&lang=' + lng, { width: 390, height: 844, isMobile: true, hasTouch: true });
    await pg.waitForFunction(() => { const t = document.getElementById('bottombar-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 8000 });
    await pg.click('#bottombar-tab-stock'); await waitOv(pg); await wait5(400);
    const gm = await pg.evaluate(() => ({ vw: innerWidth, sw: document.documentElement.scrollWidth,
      cut: [...document.querySelectorAll('#st-over .st-card, #st-over .st-lane, #st-over .st-cell')].filter(e => e.scrollWidth > e.clientWidth + 1).length,
      small: [...document.querySelectorAll('#stock-panel .st-btn, #stock-panel .st-chip, #stock-panel .st-navb, #stock-panel .st-segb, #stock-panel .st-lane-it')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 43.5).map(e => e.className + ' ' + e.textContent.trim().slice(0, 20) + ' ' + Math.round(e.getBoundingClientRect().height)) }));
    eq([gm.sw <= gm.vw, gm.cut, gm.small], [true, 0, []], 'Overview at 390 (' + lng + '): no horizontal overflow, nothing cut, every control >= 44 px: ' + JSON.stringify(gm));
    if (lng === 'fr') {
      const frNum = await pg.$eval('#st-over', e => e.innerText);
      ok(/Stock actuel/i.test(frNum) && /Les chiffres/i.test(frNum) && /Aujourd.hui/i.test(frNum) && /Argent immobilisé/i.test(frNum) && !/Stock now|The numbers|Cash tied up|Reprice|Follow up/i.test(frNum), 'French Overview has no English left: ' + frNum.replace(/\n+/g, ' | ').slice(0, 200));
      ok(new RegExp('1.?124,50').test(frNum), 'French money format, comma decimal: ' + frNum.slice(0, 120));
    }
    await pg.close();
  }

  await browser.close(); server.close();
  if (errors.length) { console.log('PAGE ERRORS:\n' + errors.join('\n')); process.exit(1); }
  console.log(`PASS: ${passed} browser checks (Stock tab gating, lazy load, full item lifecycle, undo, history, delete/restore, French + Free cap, import, Overview, lanes, first run, persona, settings, History swap, claims, 390 px)`);
})().catch(async e => { console.error('FAIL', e && e.stack || e); try { server.close(); } catch (x) {} process.exit(1); });
