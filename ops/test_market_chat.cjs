/*
 * SNYPD AI chat in the Market tab (17 Nov 2026): the REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_market_chat.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: the box shows only where the price check is open; a price, trend, ideas and "other" answer; numbers come
 * from the server answer; HTML shown as text; "Full price check" runs the price check; history is sent; fallbacks
 * (unavailable, rate limited, too broad, checks used); Free plan has no box; French on a phone; no page errors.
 * No network: the mock answers every call.
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
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('#list .card', { timeout: 10000 });
    await page.evaluate(() => {
      window.__mk = [];
      const f = window.fetch;
      window.fetch = (u, o) => { if (String(u).includes('/market/snapshot')) window.__mk.push(JSON.parse((o && o.body) || '{}')); return f(u, o); };
      document.querySelector('[data-view="market"]').click();
    });
    await page.waitForFunction(() => getComputedStyle(document.getElementById('market-panel')).display !== 'none', { timeout: 5000 });
    await wait(400);
    return page;
  }
  const reqs = p => p.evaluate(() => window.__mcRequests || []);
  const shown = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return !!e && getComputedStyle(e).display !== 'none' && e.getClientRects().length > 0; }, sel);
  const msgs = p => p.$$eval('#mc-log .mc-msg', ms => ms.map(m => (m.classList.contains('mc-msg--u') ? 'U: ' : 'A: ') + m.innerText.replace(/\s+/g, ' ').trim()));
  const say = async (p, t) => {
    const n = (await reqs(p)).length;
    await p.$eval('#mc-text', (e, t) => { e.value = t; }, t);
    await p.$eval('#mc-send', e => e.click());
    await p.waitForFunction(n => (window.__mcRequests || []).length > n && !document.getElementById('mc-send').disabled, { timeout: 6000 }, n);
    await wait(150);
    const all = await msgs(p);
    return all[all.length - 1];
  };

  // ---- 1. Elite, English, desktop
  let page = await open('plan=elite&pr=1');
  ok(await shown(page, '#mc-box'), 'chat box shown where the price check is open');
  let t = await page.$eval('#mc-box', e => e.innerText.replace(/\s+/g, ' '));
  ok(/^SNYPD AI/.test(t) && /Ask about an item/.test(t) && /Answers come from our own Vinted listings\. Asking prices, not sold prices\./.test(t), 'box text: ' + t.slice(0, 120));
  await page.$eval('#mc-send', e => e.click()); await wait(300);
  eq((await reqs(page)).length, 0, 'empty message: no request');
  await page.$eval('#mc-text', e => { e.value = 'x'; }); await page.$eval('#mc-send', e => e.click()); await wait(300);
  eq((await reqs(page)).length, 0, 'one character: no request');

  let a = await say(page, 'jordan 4 military black');
  ok(/^A: jordan 4 military black Typical asking price: €80 · Range: €45 - €135 · 207 listings Full price check$/.test(a), 'price answer from the server numbers: ' + a);
  eq((await reqs(page))[0], { text: 'jordan 4 military black', history: [], site: '' }, 'first request: text, empty history');
  eq((await msgs(page))[0], 'U: jordan 4 military black', 'the user message is shown');

  a = await say(page, 'is the carhartt jacket rising');
  ok(/^A: Carhartt <b>jacket<\/b> Price rising · \+12% against the weeks before Typical asking price: €79\.95 · 1357 listings Sellers are cutting prices\. Full price check$/.test(a), 'trend answer: ' + a);
  eq(await page.$$eval('#mc-log .mc-msg--a b b', x => x.length), 0, 'HTML in an item name is shown as text');
  eq((await reqs(page))[1].history, [{ text: 'jordan 4 military black' }], 'the earlier message is sent as history');

  a = await say(page, 'mixq samba');
  ok(/The listings changed too much to call a trend\./.test(a) && !/-17%/.test(a) && !/Price (rising|falling)/.test(a), 'data mix: no direction and no percentage: ' + a);

  a = await say(page, 'idk what to resell');
  ok(/^A: Ideas from Vinted right now\. Tap one for its price\. palace hoodie 106 listings in 7 days · max €65 · price rising levis <i>501<\/i> 534 listings in 7 days · max €22$/.test(a), 'ideas answer; malformed entries ignored: ' + a);
  eq(await page.$$eval('#mc-log .mc-msg--a i', x => x.length), 0, 'HTML in an idea is shown as text');

  a = await say(page, 'write me a poem');
  ok(/^A: I can only answer about Vinted prices/.test(a), 'off-topic: says what it can do: ' + a);
  a = await say(page, 'chatdown now');
  ok(/^A: SNYPD AI cannot answer right now\. Use the price check above\.$/.test(a), 'unavailable: ' + a);
  a = await say(page, 'chatlimit now');
  ok(/^A: Too many messages just now\. Try again later\.$/.test(a), 'rate limited: ' + a);
  a = await say(page, 'broadq nike');
  ok(/^A: These words match too many different things for one price\. Add a model name\.$/.test(a), 'too broad: ' + a);
  a = await say(page, 'spreadq jordan');
  ok(/^A: jordan 4 military black 209 listings \u00b7 Their prices are too far apart for one typical price\. Open the full price check to see the range\. Full price check$/.test(a) && !/Add a model name/.test(a), 'spread prices: says so, with the count, no "add a model name": ' + a);
  a = await say(page, 'hugeq nike');
  ok(/These words match too many different things for one price\. Add a model name\./.test(a) && !/too far apart/.test(a), 'a huge match keeps the "add a model name" answer: ' + a);
  a = await say(page, 'usedup please');
  ok(/^A: You have used your price checks for now\. Try again later\.$/.test(a), 'price checks used: ' + a);
  a = await say(page, 'notrend dickies 874');
  ok(/We do not track a trend for this item yet\./.test(a) && /Typical asking price: €80/.test(a), 'no trend for this item: says so and gives the price: ' + a);
  eq((await reqs(page)).slice(-1)[0].history.length, 4, 'at most four earlier messages are sent');
  ok(!(await msgs(page)).some(m => /sold for|sells in|sold in/i.test(m)), 'no answer claims a sale');

  // Enter sends; "Full price check" runs the price check on that item
  await page.$eval('#mc-text', e => { e.value = 'levis 501'; e.focus(); });
  let n = (await reqs(page)).length;
  await page.keyboard.press('Enter');
  await page.waitForFunction(n => (window.__mcRequests || []).length > n && !document.getElementById('mc-send').disabled, { timeout: 6000 }, n);
  eq((await reqs(page)).length, n + 1, 'Enter sends the message');
  eq(await page.$eval('#mc-text', e => e.value), '', 'the input is cleared after sending');
  await page.evaluate(() => { window.__mk.length = 0; });
  await page.$eval('#mc-log .mc-msg--a:last-child [data-mc-full]', e => e.click());
  await page.waitForFunction(() => window.__mk.length === 1 && !document.querySelector('#mr-result .mr-loading'), { timeout: 6000 });
  eq(await page.evaluate(() => window.__mk[0].q), 'levis 501', '"Full price check" runs the price check on the item');
  eq(await page.$eval('#mr-query', e => e.value), 'levis 501', 'and fills the price check box');
  ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, 'desktop: no horizontal overflow');
  await page.close();

  // ---- 2. Free plan: the price check is locked, so there is no chat box and no request
  page = await open('plan=free&pr=1');
  ok(!(await shown(page, '#mc-box')), 'Free: no chat box');
  ok(await shown(page, '#mr-locked'), 'Free: the locked card is shown instead');
  eq((await reqs(page)).length, 0, 'Free: no chat request');
  await page.close();

  // ---- 3. French on a phone
  page = await open('plan=elite&pr=1&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await wait(500);
  t = await page.$eval('#mc-box', e => e.innerText.replace(/\s+/g, ' '));
  ok(/Pose une question sur un article/.test(t) && /Demander/i.test(t) && /pas les prix réellement payés/.test(t) && !/prix de vente/.test(t), 'French box: ' + t.slice(0, 160));
  a = await say(page, 'jordan 4 military black');
  await wait(400);
  a = (await msgs(page)).slice(-1)[0];
  ok(/Prix demandé typique\s?: 80\s?€/.test(a) && /Fourchette/.test(a) && /207 annonces/.test(a) && /Vérification de prix complète/.test(a), 'French price answer: ' + a);
  a = await say(page, 'is it rising');
  await wait(400);
  a = (await msgs(page)).slice(-1)[0];
  ok(/Prix en hausse/.test(a) && /par rapport aux semaines précédentes/.test(a) && /Les vendeurs baissent leurs prix\./.test(a), 'French trend answer: ' + a);
  ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, '390 px: no horizontal overflow with answers shown');
  const box = await page.$eval('#mc-send', e => Math.round(e.getBoundingClientRect().height));
  ok(box >= 32, '390 px: the Ask button is tall enough to tap: ' + box);
  await page.close();

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' SNYPD AI market-chat checks.');
})().catch(e => { console.error(e); process.exit(1); });
