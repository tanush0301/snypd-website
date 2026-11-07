/*
 * Browser test for the trial-end summary card (Session 70, outreach/42) in the trial banner: the REAL dashboard.html in
 * headless Chrome, ops/qa_mock.js standing in for Supabase and api.snypd.store (/api/v1/hunt-report -> trial_recap with
 * ?trial=ending|ended and ?tr=noprice|busy|gbp|noname|smallgap|none).
 *   node ops/test_trial_recap.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: shown only in the window (24 h before -> 72 h after the end) and only for Free, no request outside it,
 * typical + cheapest quarter + gap, no gap when it is small, busy line, other currencies, hunt name escaped, unnamed hunt
 * and unknown condition left out, nothing without a price, Solo + Pass links, French, 390 px without overflow, no errors.
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
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(1500);
    return page;
  }
  const read = p => p.evaluate(() => {
    const box = document.getElementById('trial-recap');
    const ban = document.getElementById('elite-banner');
    return {
      shown: !!box && box.style.display !== 'none' && ban.style.display !== 'none' && ban.offsetHeight > 0,
      text: box ? box.innerText.replace(/[ \t]+/g, ' ') : '',
      head: (box.querySelector('.trial-recap__h') || {}).innerText || '',
      headHtml: (box.querySelector('.trial-recap__h') || {}).innerHTML || '',
      price: ((box.querySelector('.trial-recap__p') || {}).innerText || '').replace(/\s+/g, ' ').trim(),
      links: [...box.querySelectorAll('.trial-recap__a a')].map(a => [a.textContent.trim(), new URL(a.href).pathname + new URL(a.href).search]),
      requests: window.__hrRequests || 0,
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });

  // ---- 1. 6 h before the end
  let page = await open('plan=free&trial=ending');
  let s = await read(page);
  ok(s.shown, 'card shown 6 h before the end');
  ok(/^YOUR TRIAL IN NUMBERS/i.test(s.text), 'heading: ' + s.text.slice(0, 40));
  eq(s.head, 'nike <i>running</i> \u00b7 Very good', 'hunt name (as text) + condition');
  eq(s.headHtml.includes('<i>'), false, 'hunt name escaped, never HTML');
  eq(s.price, 'Typical asking price \u20AC49 \u00b7 the cheapest quarter \u20AC30.50 or less (about \u20AC18.50 under typical)', 'prices + gap');
  ok(/SNYPD rated each find against these prices\. Solo or a Hunt Pass keeps that price check/.test(s.text), 'what keeps it');
  ok(!/cheapest quarter \(Only the cheap ones\)/.test(s.text), 'no busy line for a normal hunt');
  eq(s.links, [['Keep it: Solo \u20AC5.99/month', '/plans?checkout=solo'], ['Hunt Pass \u20AC3.99 once', '/plans?checkout=pass']], 'Solo + Pass links');
  eq(s.requests, 1, 'one hunt-report request on load');
  ok(!/listing_id|\/items\//.test(await page.$eval('#trial-recap', e => e.innerHTML)), 'no single listing on the card');
  await page.close();

  // ---- 2. 20 h after the end (offer window)
  page = await open('plan=free&trial=ended');
  s = await read(page);
  ok(s.shown && /Typical asking price/.test(s.price), 'card shown after the end');
  ok(/50% off your first month/.test(await page.$eval('#elite-banner', e => e.innerText)), 'the STAY50 offer text stays');
  await page.close();

  // ---- 3. outside the window / not Free: nothing, and no request
  for (const q of ['plan=free&trial=1', 'plan=free', 'plan=elite&trial=ending', 'plan=solo&active=1&trial=ending']) {
    page = await open(q);
    s = await read(page);
    eq([s.shown, s.requests], [false, 0], q + ': no card, no request');
    await page.close();
  }

  // ---- 4. variants
  page = await open('plan=free&trial=ending&tr=noprice');
  s = await read(page);
  eq([s.shown, s.requests], [false, 1], 'no usable price -> no card');
  await page.close();
  page = await open('plan=free&trial=ending&tr=none');
  eq((await read(page)).shown, false, 'no recap at all -> no card');
  await page.close();
  page = await open('plan=free&trial=ending&tr=busy');
  ok(/Solo can alert you only for the cheapest quarter \(Only the cheap ones\)\./.test((await read(page)).text), 'busy hunt -> cheap-only line');
  await page.close();
  page = await open('plan=free&trial=ending&tr=smallgap');
  s = await read(page);
  eq(s.price, 'Typical asking price \u20AC33 \u00b7 the cheapest quarter \u20AC31.50 or less', 'small gap (< 10%) -> no "about" clause');
  await page.close();
  page = await open('plan=free&trial=ending&tr=gbp');
  ok(/\u00a349 .*\u00a330\.50/.test((await read(page)).price), 'GBP hunt -> pounds');
  await page.close();
  page = await open('plan=free&trial=ending&tr=noname');
  s = await read(page);
  eq(s.head, 'Your hunt', 'unnamed hunt + unknown condition -> "Your hunt", nothing else');
  await page.close();
  page = await open('plan=free&trial=ending&activated=solo');
  eq((await read(page)).shown && /Typical asking price/.test((await read(page)).text), false, 'back from checkout (activating) -> no card');
  await page.close();

  // ---- 5. French + phone
  page = await open('plan=free&trial=ending&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await wait(600);
  s = await read(page);
  ok(/^TON ESSAI EN CHIFFRES/i.test(s.text), 'French heading: ' + s.text.slice(0, 40));
  ok(/Tr\u00e8s bon \u00e9tat$/.test(s.head), 'French condition: ' + s.head);
  ok(/^Prix demand\u00e9 typique 49\s\u20AC \u00b7 le quart le moins cher 30,50\s\u20AC ou moins \(environ 18,50\s\u20AC de moins que le prix typique\)$/.test(s.price), 'French prices: ' + s.price);
  ok(/Solo ou un Pass 30 jours garde ce contr\u00f4le de prix/.test(s.text), 'French explanation');
  ok(/^Le garder\s:\sSolo 5,99\s\u20AC\/mois$/.test(s.links[0][0]) && /^Pass 30 jours 3,99\s\u20AC une fois$/.test(s.links[1][0]), 'French buttons: ' + s.links.map(l => l[0]).join(' | '));
  ok(s.overflow <= 0, '390 px: no horizontal overflow (' + s.overflow + ')');
  await page.screenshot({ path: path.join(require('os').tmpdir(), 'qa_trial_recap_fr_390.png') });
  await page.close();
  page = await open('plan=free&trial=ending&tr=busy', { width: 390, height: 844, isMobile: true, hasTouch: true });
  s = await read(page);
  ok(s.shown && s.overflow <= 0, '390 px EN busy: no overflow');
  await page.screenshot({ path: path.join(require('os').tmpdir(), 'qa_trial_recap_en_390.png') });
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' trial-recap checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
