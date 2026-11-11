/*
 * Browser test for trial price checks (11 Nov 2026): the REAL dashboard.html in headless Chrome, ops/qa_mock.js standing
 * in for Supabase and api.snypd.store (?plan=free&trial=1 = running trial, 10 checks; ?trial_used=N starts the count).
 *   node ops/test_market_trial.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: a running trial sees the panel unlocked with its own chip; a priced answer counts one and shows "N of 10 trial
 * price checks left"; a lookup with nothing found is handed back; the 10th check shows 0 left and the 11th the upgrade
 * card; a Feed card tap opens the sheet for a trial; Free without a trial stays locked and sends nothing; Elite keeps
 * the hourly line; no page errors.
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

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, waitSel) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument(() => { try { localStorage.removeItem('snypd_mr_recent'); } catch (e) {} });
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector(waitSel || '#list .card .mkt-check', { timeout: 10000 });
    await page.evaluate(() => {
      window.__mk = 0;
      const f = window.fetch;
      window.fetch = (u, o) => { if (String(u).includes('/market/snapshot')) window.__mk++; return f(u, o); };
    });
    return page;
  }
  async function toMarket(page) {
    await page.click('.view-tab[data-view="market"]');
    await page.waitForFunction(() => getComputedStyle(document.getElementById('market-panel')).display !== 'none', { timeout: 5000 });
  }
  async function check(page, q) {
    await page.$eval('#mr-query', (e, v) => { e.value = v; }, q);
    await page.click('#mr-go');
    await page.waitForFunction(() => { const r = document.getElementById('mr-result'); return r && !r.querySelector('.mr-loading') && r.innerText.length > 10; }, { timeout: 8000 });
  }
  const panel = p => p.evaluate(() => ({
    controls: getComputedStyle(document.getElementById('mr-controls')).display !== 'none',
    locked: getComputedStyle(document.getElementById('mr-locked')).display !== 'none',
    chip: document.getElementById('mr-tier-chip').textContent.trim(),
    quota: (document.getElementById('mr-quota').style.display !== 'none') ? document.getElementById('mr-quota').textContent.trim() : '',
    result: document.getElementById('mr-result').innerText,
    trial: document.body.dataset.trial,
    req: window.__mk,
  }));

  // ---- 1. running trial: unlocked, counts, hand-back
  let page = await open('plan=free&trial=1&pr=1');
  await toMarket(page);
  let s = await panel(page);
  ok(s.trial === '1', 'body[data-trial] set for a running trial');
  ok(s.controls && !s.locked, 'trial sees the search box, not the locked card');
  ok(s.chip === 'Trial: 10 price checks', 'trial chip: ' + s.chip);
  await check(page, 'jordan 1 mid');
  s = await panel(page);
  ok(/85/.test(s.result), 'trial gets a price: ' + s.result.slice(0, 80));
  ok(s.quota === '9 of 10 trial price checks left', 'quota after 1: ' + s.quota);
  await check(page, 'zzz_nomatch item');
  s = await panel(page);
  ok(s.quota === '9 of 10 trial price checks left', 'nothing found is handed back: ' + s.quota);
  await page.close();

  // ---- 2. last check, then the upgrade card
  page = await open('plan=free&trial=1&trial_used=9&pr=1');
  await toMarket(page);
  await check(page, 'adidas samba');
  s = await panel(page);
  ok(s.quota === '0 of 10 trial price checks left', '10th check: ' + s.quota);
  ok(!/used your 10 trial/.test(s.result), '10th check still answers');
  await check(page, 'adidas gazelle');
  s = await panel(page);
  ok(/You have used your 10 trial price checks/.test(s.result), 'upgrade card after 10: ' + s.result.slice(0, 80));
  ok(await page.$eval('#mr-result a.btn', a => a.getAttribute('href')) === '/plans', 'upgrade card links to /plans');
  ok(s.controls, 'search box stays visible after the trial checks are used');
  await page.close();

  // ---- 3. Feed card tap for a trial opens the sheet with an answer
  page = await open('plan=free&trial=1&pr=1');
  await page.click('#list .card .mkt-check');
  await page.waitForFunction(() => { const b = document.querySelector('.mr-sheet.on .mr-sheet__bd'); return b && !b.querySelector('.mr-loading') && b.innerText.length > 20; }, { timeout: 8000 });
  ok(await page.evaluate(() => window.__mk) === 1, 'feed tap sends one lookup for a trial');
  await page.close();

  // ---- 4. Free without a trial: locked, no request
  page = await open('plan=free&pr=1');
  await page.click('#list .card .mkt-check');
  await new Promise(r => setTimeout(r, 600));
  s = await panel(page);
  ok(!s.trial, 'no trial flag on plain Free');
  ok(s.locked && !s.controls, 'plain Free stays locked');
  ok(s.req === 0, 'plain Free sends no lookup');
  await page.close();

  // ---- 5. Elite unchanged
  page = await open('plan=elite&pr=1');
  await toMarket(page);
  s = await panel(page);
  ok(s.chip !== 'Trial: 10 price checks' && !s.trial, 'elite has no trial chip');
  await check(page, 'jordan 1 mid');
  s = await panel(page);
  ok(/left this hour/.test(s.quota), 'elite keeps the hourly line: ' + s.quota);
  await page.close();

  // ---- 5b. badge + tracking copy (11 Nov 2026)
  page = await open('plan=elite&pr=1');
  await toMarket(page);
  await check(page, 'medq jacket');
  let badge = await page.$eval('#mr-result .mr-badge', e => ({ t: e.textContent.trim(), c: e.className }));
  ok(badge.t === 'Check the warning below' && /warn/.test(badge.c), 'ok price with a warning is not "Trusted price": ' + JSON.stringify(badge));
  await check(page, 'jordan 1 mid');
  badge = await page.$eval('#mr-result .mr-badge', e => e.textContent.trim());
  ok(badge === 'Trusted price', 'clean ok price keeps "Trusted price": ' + badge);
  await check(page, 'trackq item');
  s = await panel(page);
  ok(/started watching this search/.test(s.result), 'tracked zero result says it started watching');
  await check(page, 'zzz_nomatch item');
  s = await panel(page);
  ok(!/started watching/.test(s.result) && /brand and model/.test(s.result), 'untracked zero result makes no watching promise');
  await page.close();

  // ---- 6. non-EU label: a card priced in USD says the prices come from the EU site; a euro card does not
  // The mock's default Feed (which seeds a USD card) renders no cards in this harness, and the rated Feed (?pr=1)
  // is all EUR. So: check the real buttons carry their currency, then open the sheet through the same entry point
  // the button's click handler calls (window.SNYPD.marketCheckCard) with a USD and a EUR card.
  async function sheetFor(cur) {
    const p = await open('plan=elite&pr=1');
    const curs = await p.$$eval('#list .card .mkt-check', bs => bs.map(b => b.dataset.marketCur));
    await p.evaluate(c => window.SNYPD.marketCheckCard({ title: 'Patagonia Synchilla Fleece', brand: 'Patagonia', cond: 'Good', cur: c }), cur);
    await p.waitForFunction(() => { const b = document.querySelector('.mr-sheet.on .mr-sheet__bd'); return b && !b.querySelector('.mr-loading') && b.innerText.length > 20; }, { timeout: 8000 });
    const t = await p.$eval('.mr-sheet .mr-sheet__bd', e => e.innerText);
    await p.close();
    return { t: t, curs: curs };
  }
  const usd = await sheetFor('USD');
  ok(usd.curs.length > 0 && usd.curs.every(c => c === 'EUR'), 'Feed buttons carry their card currency: ' + usd.curs.join(','));
  ok(/priced in USD/.test(usd.t) && /may differ/.test(usd.t), 'USD card shows the non-EU label: ' + usd.t.slice(0, 120));
  const eurT = await sheetFor('EUR');
  ok(!/priced in/.test(eurT.t), 'EUR card has no non-EU label');

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('all ' + passed + ' market-trial checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
