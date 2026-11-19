/*
 * Plan chosen at sign-up (19 Nov 2026): checkout opens only on the user's tap.
 *   node ops/test_plan_after_signup.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Runs the REAL dashboard.html with ops/qa_mock.js in headless Chrome. An account that already has a hunt used to be
 * sent straight into the payment form; now it sees the same plan line as a new account and stays on the dashboard.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const KEY = 'snypd_checkout_after_hunt';

(async () => {
  const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
  const swap = s => s.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
  const server = http.createServer((req, res) => {
    const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
    try {
      if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
      if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
      if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
      const f = path.join(root, p);
      if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
      send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
    } catch (e) { res.writeHead(500); res.end(String(e)); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];

  async function open(q, intent, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument((KEY, intent) => {
      try { if (!sessionStorage.getItem('__seeded')) { sessionStorage.setItem('__seeded', '1'); if (intent) localStorage.setItem(KEY, intent); } } catch (e) {}
    }, KEY, intent ? JSON.stringify(intent) : null);
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await wait(3500);
    page.ctx = ctx;
    return page;
  }
  const state = p => p.evaluate(KEY => {
    const b = document.getElementById('elite-banner');
    const a = b && b.querySelector('a.btn');
    return { path: location.pathname, shown: !!b && b.style.display !== 'none' && b.getClientRects().length > 0,
      title: b ? b.querySelector('.elite-banner__title').textContent : null,
      text: b ? b.querySelector('.elite-banner__text').textContent : null,
      btn: a ? a.textContent : null, href: a ? a.getAttribute('href') : null, stored: localStorage.getItem(KEY),
      overflow: document.documentElement.scrollWidth > window.innerWidth };
  }, KEY);
  const fresh = plan => ({ plan, ts: Date.now() });
  const TITLE = 'Your hunt is live. Keep it running after the trial';

  // ---- 1. account that already has a hunt, picked Solo: stays on the dashboard, plan line shown, checkout on tap
  let page = await open('plan=free&trial=1', fresh('solo'));
  let s = await state(page);
  eq(s.path, '/dashboard.html', 'has a hunt: no redirect into the payment form');
  ok(s.shown, 'plan line shown right away');
  eq(s.title, TITLE, 'title');
  eq(s.text, 'Solo: \u20ac5.99/month, renewed monthly until you cancel. Paid access starts when your payment is activated.', 'Solo line');
  eq([s.btn, s.href], ['Start Solo', '/plans?checkout=solo'], 'button opens the Solo checkout');
  ok(s.stored !== null, 'the choice is kept until the user taps');
  await page.evaluate(() => { document.addEventListener('click', e => e.preventDefault(), true); document.querySelector('#elite-banner a.btn').click(); });
  eq((await state(page)).stored, null, 'tapping the button clears the stored choice');
  await page.ctx.close();

  // ---- 2. Hunt Pass and Pro wording
  page = await open('plan=free&trial=1', fresh('pass'));
  s = await state(page);
  eq([s.path, s.shown, s.btn, s.href], ['/dashboard.html', true, 'Start Hunt Pass', '/plans?checkout=pass'], 'Hunt Pass: shown, no redirect');
  eq(s.text, 'Hunt Pass: \u20ac3.99 once for 30 days, with no automatic renewal. Paid access starts when your payment is activated.', 'Hunt Pass line');
  await page.ctx.close();
  page = await open('plan=free&trial=1', fresh('pro'));
  s = await state(page);
  eq([s.path, s.shown, s.btn, s.href], ['/dashboard.html', true, 'Start Pro', '/plans?checkout=pro'], 'Pro: shown, no redirect');
  eq(s.text, 'You picked Pro at sign-up. Start it now and your hunt keeps running 24/7 when the trial ends.', 'Pro line');
  await page.ctx.close();

  // ---- 3. phone width
  page = await open('plan=free&trial=1', fresh('solo'), { width: 390, height: 844, isMobile: true, hasTouch: true });
  s = await state(page);
  eq([s.path, s.shown, s.overflow], ['/dashboard.html', true, false], '390 px: shown, no sideways scroll');
  await page.ctx.close();

  // ---- 4. new account without a hunt: nothing until the first hunt is saved, then the same line (unchanged behaviour)
  page = await open('plan=free&hunts=0', fresh('solo'));
  s = await state(page);
  eq(s.path, '/dashboard.html', 'no hunt: stays on the dashboard');
  ok(s.title !== TITLE, 'no hunt: plan line waits for the first hunt');
  await page.evaluate(() => window.dispatchEvent(new Event('snypd:hunts-changed')));
  await wait(400);
  s = await state(page);
  eq([s.shown, s.title, s.btn], [true, TITLE, 'Start Solo'], 'first hunt saved: plan line appears');
  await page.ctx.close();

  // ---- 5. never for a paying account, an old choice, or an unknown plan
  page = await open('plan=elite', fresh('solo'));
  s = await state(page);
  eq([s.path, s.stored], ['/dashboard.html', null], 'paid account: choice dropped');
  ok(s.title !== TITLE, 'paid account: no plan line');
  await page.ctx.close();
  page = await open('plan=free&trial=1', { plan: 'solo', ts: Date.now() - 8 * 864e5 });
  s = await state(page);
  eq(s.stored, null, 'choice older than 7 days: dropped');
  ok(s.title !== TITLE, 'old choice: no plan line');
  await page.ctx.close();
  page = await open('plan=free&trial=1', fresh('platinum'));
  s = await state(page);
  eq(s.stored, null, 'unknown plan: dropped');
  ok(s.title !== TITLE, 'unknown plan: no plan line');
  await page.ctx.close();

  // ---- 6. no stored choice: nothing changes
  page = await open('plan=free&trial=1', null);
  s = await state(page);
  eq(s.path, '/dashboard.html', 'no choice: dashboard');
  ok(s.title !== TITLE, 'no choice: no plan line');
  await page.ctx.close();

  eq(errors, [], 'no page errors');
  await browser.close();
  server.close();
  console.log('plan after sign-up: ' + passed + ' checks passed');
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
