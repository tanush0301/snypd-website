/*
 * Browser test for the Market board (Session 67, website outreach/37) on the Market tab: the REAL dashboard.html in headless
 * Chrome, ops/qa_mock.js standing in for Supabase and api.snypd.store (/api/v1/market-board; ?mb=full|teaser|empty|error,
 * ?trial=1, ?mbsite=uk). The mock's board comes from the backend's own market_board.compute() on the frozen live dump.
 *   node ops/test_market_board.cjs            (needs Google Chrome at CHROME_PATH or the default Windows path)
 *   SHOTS=<dir> node ops/test_market_board.cjs   also writes screenshots
 * Checks: order of the Market tab (Your hunts -> Check a price -> What's moving), 3 rising / 3 falling for Pro/Elite/trial,
 * 1 + 1 and one upgrade card for other plans, mix + price-cut wording, See all list + category filter, chart sheet (series,
 * gaps, numbers, meaning, Pay at most follows the margin), Hunt this below (opens the hunt sheet filled; EUR site only),
 * teaser rows open the upgrade sheet, What hunters watch, empty + error states, one request per visit, French, 390 px,
 * names escaped, no page errors.
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
const EUR = '\u20AC', MINUS = '\u2212';
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
  async function open(q, vp) {
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(800);
    await page.evaluate(() => document.querySelector('[data-view="market"]').click());
    await page.waitForFunction(() => { const b = document.getElementById('mb-box'); return b && b.style.display !== 'none' && b.innerText.length > 10; }, { timeout: 8000 });
    await wait(400);
    return page;
  }
  const shot = async (page, name, full) => { if (SHOTS) { await page.screenshot({ path: path.join(SHOTS, name), fullPage: !!full }); } };
  const read = p => p.evaluate(() => {
    const box = document.getElementById('mb-box');
    const col = k => [...box.querySelectorAll('.mb-col')][k];
    const rows = el => el ? [...el.querySelectorAll('.mb-row')].map(r => r.innerText.replace(/\s+/g, ' ').trim()) : [];
    const panel = document.getElementById('market-panel');
    const pos = id => { const e = document.getElementById(id); return e ? e.getBoundingClientRect().top + scrollY : -1; };
    return {
      text: box.innerText.replace(/\s+/g, ' '),
      rising: rows(col(0)), falling: rows(col(1)),
      allRows: rows(box.querySelector('.mb-all')),
      cats: [...box.querySelectorAll('.mb-cat')].map(c => c.innerText.trim()),
      hunters: [...box.querySelectorAll('.mb-hunt__r')].map(r => r.innerText.replace(/\s+/g, ' ').trim()),
      up: (box.querySelector('.mb-up') || {}).innerText || '',
      order: [pos('hr-box'), pos('mr-controls'), pos('mr-locked'), pos('mb-box')],
      hrShown: document.getElementById('hr-box').style.display !== 'none',
      requests: window.__mbRequests || 0,
      overflow: document.documentElement.scrollWidth - innerWidth,
      inPanel: panel.contains(box),
    };
  });
  const sheet = p => p.evaluate(() => {
    const s = document.querySelector('.mr-sheet.on');
    if (!s) return null;
    const svg = s.querySelector('svg.mb-chart');
    return {
      title: s.querySelector('.mr-sheet__t').textContent,
      text: s.querySelector('.mr-sheet__bd').innerText.replace(/\s+/g, ' '),
      dots: svg ? svg.querySelectorAll('circle').length : 0, bars: svg ? svg.querySelectorAll('rect').length : 0,
      bands: svg ? svg.querySelectorAll('polygon').length : 0, gaps: svg ? (svg.querySelector('path').getAttribute('d').match(/M/g) || []).length : 0,
      nums: [...s.querySelectorAll('.mb-nums > div')].map(d => d.innerText.replace(/\s+/g, ' ').trim()),
      max: (s.querySelector('[data-mr-max]') || {}).textContent,
      hunt: s.querySelector('[data-mb-hunt]') ? [s.querySelector('[data-mb-hunt]').textContent.replace(/\s+/g, ' ').trim(), s.querySelector('[data-mb-hunt]').getAttribute('data-mb-max')] : null,
      note: (s.querySelector('[data-mb-hunt-note]') || {}).innerText || '',
      up: (s.querySelector('.mb-up') || {}).innerText || '',
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });
  const tap = (p, sel) => p.evaluate(s => { const e = document.querySelector(s); if (!e) throw new Error('no ' + s); e.click(); }, sel);

  // ---- 1. Elite: full board
  let page = await open('plan=elite');
  let s = await read(page);
  ok(s.inPanel && s.hrShown, 'board inside the Market panel, weekly report shown');
  ok(await page.evaluate(() => !document.querySelector('#market-panel .hd #hr-box') && document.getElementById('hr-box').getBoundingClientRect().bottom < document.getElementById('mr-controls').getBoundingClientRect().top), 'weekly report stands above the price search, not beside it');
  ok(s.order[0] < s.order[1] && s.order[1] < s.order[3], 'order: Your hunts -> Check a price -> What\'s moving ' + s.order);
  ok(/^What's moving EU asking prices \(EUR\) \u00b7 5 Nov/.test(s.text), 'title + EU label + date: ' + s.text.slice(0, 60));
  eq(s.rising, ['Ralph Lauren Polo Bear ' + EUR + '59.99 +15% Tops & knitwear'], 'rising: the one riser with its typical price and change');
  eq(s.falling.length, 3, 'falling: top 3 of 4');
  ok(/^Longchamp bag \u20AC55 \u221221% Bags$/.test(s.falling[0]) && /^Stussy T-shirt/.test(s.falling[1]) && /^Adidas Handball/.test(s.falling[2]), 'falling: steepest first, minus sign: ' + s.falling.join(' | '));
  ok(/1 item hidden: the mix of listings changed too much to call a direction\./.test(s.text), 'mix count said, not shown as a signal');
  ok(/See all 9 items/.test(s.text) && s.allRows.length === 0, 'See all link, list closed');
  ok(/Asking prices, not sold prices: a description, not a forecast\./.test(s.text), 'honest note');
  ok(!/\bbuy\b|\bsell\b|sold prices|will rise/i.test(s.text.replace('not sold prices', '')), 'no buy/sell/forecast words');
  eq(s.hunters, ['Nike 122 hunters', 'Ralph Lauren 96 hunters', 'Stone Island 20 hunters', 'Adidas 17 hunters', "Levi's 5 hunters"], 'what hunters watch, counts only');
  ok(/counted once per user/.test(s.text), 'hunters note');
  eq(s.requests, 1, 'one request when the tab opens');
  eq(await page.$eval('#filter-pill', e => getComputedStyle(e).visibility), 'hidden', 'the floating Filters button of the Feed is hidden on the Market tab');
  await shot(page, 'mb-desktop-elite.png', true);
  await tap(page, '[data-mb-all]'); await wait(200);
  s = await read(page);
  eq(s.allRows.length, 9, 'See all: every item');
  eq(s.cats, ['All', 'Sneakers', 'Tops & knitwear', 'Trousers', 'Bags'], 'category chips only for categories present');
  ok(s.allRows.some(r => /^Jordan 1 Travis Scott Olive .* Sneakers Price cuts$/.test(r)), 'price-cut tag on a steady item: ' + s.allRows.join(' | '));
  ok(s.allRows.some(r => /^Stone Island jumper \u20AC\S+ Tops & knitwear$/.test(r)), 'mix item listed without a direction');
  ok(await page.$$eval('.mb-all .mb-spark', e => e.length) === 9, 'sparkline per row');
  await tap(page, '[data-mb-cat="bags"]'); await wait(150);
  eq((await read(page)).allRows.map(r => r.split(' ')[0]), ['Longchamp'], 'category filter');
  await tap(page, '[data-mb-cat=""]'); await wait(150);
  eq((await read(page)).allRows.length, 9, 'All again');
  await tap(page, '[data-mb-all]'); await wait(150);
  eq((await read(page)).allRows.length, 0, 'Hide the list');

  // ---- 2. chart sheet
  await tap(page, '.mb-col [data-mb-q="longchamp bag"]'); await wait(400);
  let sh = await sheet(page);
  ok(sh && sh.title === 'Longchamp bag', 'sheet opens on the item');
  ok(/Bags \u00b7 EU asking prices \(EUR\) \u00b7 Search words: longchamp bag \u00b7 \u221221%/.test(sh.text), 'sheet header: ' + sh.text.slice(0, 90));
  ok(sh.dots >= 20 && sh.dots <= 38 && sh.bars >= 30 && sh.bands >= 1, 'chart: typical dots, listings bars, range band (' + [sh.dots, sh.bars, sh.bands] + ')');
  eq(sh.nums.slice(0, 3), [EUR + '55 Typical now', EUR + '32–' + EUR + '90 Normal range', '159 Listings (7 days)'], 'numbers: typical, range (p25-p75 of today), listings');
  ok(/Listings \(7 days\)$/.test(sh.nums[2]) && /Sellers$/.test(sh.nums[3]) && /Price cuts this week$/.test(sh.nums[4]), 'numbers: listings, sellers, price cuts');
  ok(/Sellers now ask 21% less than 8 to 21 days ago \(\u20AC70 to \u20AC55\)\. Cheaper to source now, but check it's not fading/.test(sh.text), 'meaning for a faller: ' + sh.text);
  eq(sh.max, EUR + '33', 'Pay at most = typical x (100 - 40%)');
  await page.evaluate(() => { const i = document.querySelector('.mr-sheet.on [data-mr-margin]'); i.value = '50'; i.dispatchEvent(new Event('input', { bubbles: true })); });
  eq((await sheet(page)).max, EUR + '27.50', 'Pay at most follows the margin');
  await page.evaluate(() => { localStorage.removeItem('snypd_mr_margin'); });
  ok(sh.hunt && /^Hunt this below \u20AC\d+$/.test(sh.hunt[0]) && Number(sh.hunt[1]) > 0, 'Hunt this below the quick-sale price: ' + sh.hunt);
  ok(/only a quarter of listings ask less/.test(sh.note), 'hunt note');
  await shot(page, 'mb-desktop-sheet.png');
  const maxEur = sh.hunt[1];
  await tap(page, '.mr-sheet.on [data-mb-hunt]'); await wait(600);
  let fs1 = await page.evaluate(() => ({
    open: document.getElementById('filter-sheet-overlay') && getComputedStyle(document.getElementById('filter-sheet-overlay')).display !== 'none',
    words: document.getElementById('fs-q-words').value, max: document.getElementById('fs-q-max').value, site: document.getElementById('fs-q-site').value,
    url: document.getElementById('filter-new-url').value, name: document.getElementById('filter-new-name').value,
    sheetClosed: !document.querySelector('.mr-sheet.on'),
  }));
  ok(fs1.open && fs1.sheetClosed, 'hunt sheet opens, chart sheet closes');
  eq([fs1.words, fs1.max, fs1.site, fs1.name], ['longchamp bag', maxEur, 'vinted.be', 'longchamp bag'], 'filled: words, max, the first hunt\'s site, name');
  ok(/^https:\/\/www\.vinted\.be\/catalog\?search_text=longchamp\+bag&price_to=\d+&order=newest_first$/.test(fs1.url), 'link built by the quick search: ' + fs1.url);
  await page.close();

  // ---- 3. rising + steady + mix meanings
  page = await open('plan=pro');
  await tap(page, '.mb-col [data-mb-q="ralph lauren polo bear"]'); await wait(300);
  sh = await sheet(page);
  ok(/Sellers now ask 15% more than 8 to 21 days ago \(\u20AC51\.50 to \u20AC59\)\. Good time to list if you hold some\./.test(sh.text), 'meaning for a riser');
  await page.evaluate(() => document.querySelector('.mr-sheet.on .mr-sheet__x').click());
  await tap(page, '[data-mb-all]'); await wait(150);
  await tap(page, '.mb-all [data-mb-q="stone island sweater"]'); await wait(300);
  ok(/The mix of listings changed a lot, so we don't call a direction\./.test((await sheet(page)).text), 'meaning for a mix item');
  await page.evaluate(() => document.querySelector('.mr-sheet.on .mr-sheet__x').click());
  await tap(page, '.mb-all [data-mb-q="jordan 1 travis scott olive"]'); await wait(300);
  sh = await sheet(page);
  ok(/Asking prices held steady: within 10% of 8 to 21 days ago\. 24% of listings had a price cut this week: buyers are taking their time\./.test(sh.text), 'steady + price cuts: ' + sh.text);
  await page.close();

  // ---- 4. trial = full; free / solo / kickstart = teaser
  page = await open('plan=free&trial=1');
  ok((await read(page)).hunters.length === 5, 'running trial gets the full board');
  await page.close();
  for (const plan of ['free', 'solo', 'kickstart']) {
    page = await open('plan=' + plan);
    s = await read(page);
    eq([s.rising.length, s.falling.length], [1, 1], plan + ': 1 rising + 1 falling');
    ok(/^Longchamp bag/.test(s.falling[0]), plan + ': the steepest faller');
    ok(/9 items on the board today\. See every tracked item with its 5-week trend, price cuts and what hunters watch: part of Pro and Elite\. See plans/.test(s.up), plan + ': one upgrade card');
    ok(s.hunters.length === 0 && !/See all/.test(s.text) && !/hidden/.test(s.text), plan + ': no list, no hunters, no mix line');
    if (plan === 'free') {
      eq(await page.$eval('#mb-box .mb-up a', a => new URL(a.href).pathname), '/plans', 'upgrade link');
      await tap(page, '.mb-col [data-mb-q="longchamp bag"]'); await wait(300);
      sh = await sheet(page);
      ok(sh && /part of Pro and Elite/.test(sh.up) && sh.dots === 0 && !sh.hunt, 'teaser row opens the upgrade sheet, no chart');
      await shot(page, 'mb-desktop-free.png', true);
    }
    await page.close();
  }

  // ---- 5. non-euro first hunt: words only
  page = await open('plan=elite&mbsite=uk');
  await tap(page, '.mb-col [data-mb-q="longchamp bag"]'); await wait(500);
  sh = await sheet(page);
  eq(sh.hunt, ['Hunt this item', null], 'UK account: no EUR maximum on the button');
  ok(/non-euro Vinted site/.test(sh.note), 'UK note');
  await tap(page, '.mr-sheet.on [data-mb-hunt]'); await wait(600);
  fs1 = await page.evaluate(() => ({ words: document.getElementById('fs-q-words').value, max: document.getElementById('fs-q-max').value, site: document.getElementById('fs-q-site').value }));
  eq(fs1, { words: 'longchamp bag', max: '', site: 'vinted.co.uk' }, 'UK: words only, on the UK site');
  await page.close();

  // ---- 6. empty + error + one request per visit
  page = await open('plan=elite&mb=empty');
  s = await read(page);
  ok(/Nothing rising by 10% or more right now\./.test(s.text) && /Nothing falling by 10% or more right now\./.test(s.text), 'no movers -> says so');
  await page.close();
  page = await open('plan=free&mb=empty');
  ok(/Nothing rising/.test((await read(page)).text), 'teaser with no movers');
  await page.close();
  page = await open('plan=elite&mb=error');
  ok(/Could not load what is moving right now\./.test((await read(page)).text), '503 -> a plain error line');
  await page.close();
  page = await open('plan=elite');
  await page.evaluate(() => document.querySelector('[data-view="feed"]').click()); await wait(300);
  await page.evaluate(() => document.querySelector('[data-view="market"]').click()); await wait(500);
  eq((await read(page)).requests, 1, 'reopening the tab within 30 min does not ask again');
  await page.close();

  // ---- 7. French + phone
  page = await open('plan=elite&lang=fr', PHONE);
  await wait(500);
  s = await read(page);
  ok(/^Ce qui bouge Prix demand\u00e9s UE \(EUR\)/.test(s.text), 'French title: ' + s.text.slice(0, 50));
  ok(/^Sac Longchamp 55\s\u20AC \u221221\s% Sacs$/.test(s.falling[0]) && await page.$eval('.mb-col .mb-ch.down', e => e.textContent.endsWith('\u00a0%')), 'French row (FR name, money, % spacing, category): ' + s.falling[0]);
  ok(/1 article masqu\u00e9/.test(s.text) && /Voir les 9 articles/.test(s.text) && /Ce que surveillent les utilisateurs/i.test(s.text), 'French mix line, See all, hunters');
  ok(/Prix demand\u00e9s, pas les prix r\u00e9ellement pay\u00e9s/.test(s.text) && !/prix de vente/i.test(s.text), 'French note, never "prix de vente"');
  ok(s.overflow <= 0, '390 px: no horizontal overflow (' + s.overflow + ')');
  await shot(page, 'mb-phone-fr.png', true);
  const tapH = await page.$eval('.mb-row', e => e.getBoundingClientRect().height);
  ok(tapH >= 44, 'phone: rows are at least 44 px tall (' + tapH + ')');
  await tap(page, '.mb-col [data-mb-q="longchamp bag"]'); await wait(400);
  sh = await sheet(page);
  ok(sh.title === 'Sac Longchamp' && /Vendeurs|Les vendeurs demandent maintenant 21\u00a0% de moins/.test(sh.text), 'French sheet: ' + sh.text.slice(0, 200));
  ok(/Chercher en dessous de \d+\s\u20AC/.test(sh.hunt[0]), 'French hunt button: ' + sh.hunt[0]);
  ok(sh.overflow <= 0, '390 px sheet: no overflow');
  await shot(page, 'mb-phone-fr-sheet.png');
  await page.close();
  page = await open('plan=free', PHONE);
  ok((await read(page)).overflow <= 0, '390 px teaser: no overflow');
  await shot(page, 'mb-phone-free.png', true);
  await page.close();

  // ---- 8. escaping
  page = await open('plan=elite');
  await page.evaluate(() => {
    const d = JSON.parse(JSON.stringify(window.__mbProbe || {}));
    return d;
  });
  const esc = await page.evaluate(async () => {
    const f = window.fetch;
    window.fetch = async (u, o) => {
      const r = await f(u, o);
      if (!String(u).includes('/market-board')) return r;
      const b = await r.json();
      b.items[0].name = '<img src=x onerror=window.__xss=1>'; b.items[0].name_fr = '<img src=x onerror=window.__xss=2>'; b.items[0].q = '"><b>q</b>';
      b.hunters[0].brand = '<i>brand</i>';
      b.rising = [b.items[0].q];
      return new Response(JSON.stringify(b), { status: 200 });
    };
    await window.SNYPD.loadBoard(true);
    await new Promise(r => setTimeout(r, 300));
    const box = document.getElementById('mb-box');
    return { xss: !!window.__xss, img: box.querySelectorAll('img').length, i: box.querySelectorAll('.mb-hunt__r i:not([style])').length, b: box.querySelectorAll('b').length };
  });
  eq(esc, { xss: false, img: 0, i: 0, b: 0 }, 'names, queries and brands are escaped, never HTML');
  await page.close();

  // ---- 9. the page never shows a teaser more than 1 + 1, even if handed more
  page = await open('plan=free');
  const cap = await page.evaluate(async () => {
    const f = window.fetch;
    window.fetch = async (u, o) => {
      const r = await f(u, o);
      if (!String(u).includes('/market-board')) return r;
      const b = await r.json();
      b.rising = ['ralph lauren polo bear', 'longchamp bag', 'stussy tee']; b.falling = ['longchamp bag', 'stussy tee', 'adidas handball'];
      b.items = [{ q: 'ralph lauren polo bear', name: 'A', name_fr: 'A', cat: 'tops', typical_cents: 100, change_pct: 15, signal: 'rising' },
        { q: 'longchamp bag', name: 'B', name_fr: 'B', cat: 'bags', typical_cents: 100, change_pct: -21, signal: 'falling' },
        { q: 'stussy tee', name: 'C', name_fr: 'C', cat: 'tops', typical_cents: 100, change_pct: -20, signal: 'falling' },
        { q: 'adidas handball', name: 'D', name_fr: 'D', cat: 'sneakers', typical_cents: 100, change_pct: -20, signal: 'falling' }];
      return new Response(JSON.stringify(b), { status: 200 });
    };
    await window.SNYPD.loadBoard(true);
    await new Promise(r => setTimeout(r, 300));
    return [...document.querySelectorAll('#mb-box .mb-col')].map(c => c.querySelectorAll('.mb-row').length);
  });
  eq(cap, [1, 1], 'teaser: at most 1 rising + 1 falling drawn');
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' market-board checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
