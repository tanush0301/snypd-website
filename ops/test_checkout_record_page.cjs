/*
 * Checkout record on the real /plans page (assets/checkout-record.js + plans.html; website repo outreach/62, move 1).
 *   node ops/test_checkout_record_page.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Serves the repo's own files. supabase-js and Whop's elements.js are replaced by small fakes; every other request
 * to another host is blocked, so nothing reaches production, no account is used and nothing is paid.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(root, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(root, p + '.html');
  if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f)) { res.writeHead(404); return res.end('nope'); }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(fs.readFileSync(f));
});

// Stand-in for supabase-js: one account whose Auth metadata lives in window.__SB (set before the page loads).
const FAKE_SUPABASE = `(function () {
  var S = window.__SB || { signedIn: false };
  S.updates = [];
  S.meta = S.meta || {};
  function user() { return { id: 'test-account', email: 'test@example.invalid', created_at: '2026-11-01T00:00:00Z',
    user_metadata: JSON.parse(JSON.stringify(S.meta)) }; }
  function q(row) { var o = { select: function () { return o; }, eq: function () { return o; },
    maybeSingle: function () { return Promise.resolve({ data: row, error: null }); } }; return o; }
  window.supabase = { createClient: function () { return {
    auth: {
      getSession: function () { return Promise.resolve({ data: { session: S.signedIn ? { user: user() } : null }, error: null }); },
      getUser: function () {
        if (S.serverMeta) { S.meta = S.serverMeta; S.serverMeta = null; }  // another device wrote in the meantime
        return Promise.resolve({ data: { user: S.signedIn ? user() : null }, error: null });
      },
      updateUser: function (p) {
        S.updates.push(JSON.parse(JSON.stringify(p)));
        if (p && p.data) for (var k in p.data) S.meta[k] = p.data[k];
        return Promise.resolve({ data: { user: user() }, error: null });
      },
      onAuthStateChange: function () { return { data: { subscription: { unsubscribe: function () {} } } }; }
    },
    from: function (t) {
      if (t === 'users') return q({ subscription_plan: S.plan || 'free', sub_status: '', whop_manage_url: null, whop_product_id: null, pass_expires_at: null });
      return q({ value: 1234 });
    },
    rpc: function () { return Promise.resolve({ data: null, error: null }); }
  }; } };
})();`;

// Stand-in for Whop Elements: mounts nothing real, reports "loading" then "loaded", and keeps the options so the
// test can call onComplete as a finished payment would.
const FAKE_WHOP = `window.WhopElements = function () { return { checkout: { create: function (opts) {
  (window.__whop = window.__whop || []).push(opts);
  return { create: function () { return { mount: function () {
    setTimeout(function () { if (opts.onLoadingChange) { opts.onLoadingChange(true); setTimeout(function () { opts.onLoadingChange(false); }, 30); } }, 10);
  } }; } };
} } }; };`;

let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1';

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];

  async function open(url, sb, opt = {}) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(opt.viewport || { width: 1280, height: 900 });
    if (opt.ua) await page.setUserAgent(opt.ua);
    page.on('pageerror', e => errors.push(url + ': ' + e.message));
    page.__outside = [];
    page.__whopRequests = 0;
    await page.evaluateOnNewDocument((s, applePay) => {
      window.__SB = s;
      if (applePay) window.ApplePaySession = { canMakePayments: () => true };
    }, sb, !!opt.applePay);
    await page.setRequestInterception(true);
    page.on('request', r => {
      const u = r.url();
      if (u.startsWith(base) || u.startsWith('data:')) return r.continue();
      if (/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js/.test(u)) return r.respond({ status: 200, contentType: 'application/javascript', body: FAKE_SUPABASE });
      if (/cdn\.whop\.com\/elements/.test(u)) {
        page.__whopRequests++;
        if (opt.whopDown) return r.abort();
        return r.respond({ status: 200, contentType: 'application/javascript', body: FAKE_WHOP });
      }
      page.__outside.push(u);
      return r.abort();
    });
    await page.goto(base + url, { waitUntil: 'domcontentloaded' });
    return { page, ctx };
  }
  const updates = page => page.evaluate(() => (window.__SB && window.__SB.updates) || []);
  const lastCo = async page => { const u = await updates(page); return u.length ? u[u.length - 1].data.co : null; };
  const overlayOpen = (page, k) => page.evaluate(k => { const o = document.querySelector('[data-whop-embed-overlay="' + k + '"]'); return !!o && !o.hidden; }, k);
  async function clickCheckout(page, k) {
    const sel = 'a[data-cta="' + k + '"][data-act="checkout"]';
    await page.waitForSelector(sel, { timeout: 8000 });
    await page.$eval(sel, a => a.click());
    for (let i = 0; i < 40 && !(await overlayOpen(page, k)); i++) await wait(50);
  }

  // 1. Signed-in Free account from the homepage: open Pro, form loads, close with Escape.
  let { page, ctx } = await open('/plans?from=home', { signedIn: true, meta: { ui_lang: 'en' } });
  await clickCheckout(page, 'pro');
  ok(await overlayOpen(page, 'pro'), 'Pro checkout opens (existing behaviour)');
  await wait(300);
  await page.keyboard.press('Escape');
  ok(!(await overlayOpen(page, 'pro')), 'Escape closes it (existing behaviour)');
  await wait(2200);
  let u = await updates(page);
  eq(u.length, 1, 'one write for open + loaded + close');
  eq(Object.keys(u[0].data), ['co'], 'only the checkout record is written, no other account field');
  let co = u[0].data.co;
  eq([co.v, co.o, co.p, co.pl, co.src, co.src1, co.d, co.ld, co.c], [1, 1, 'pro', ['pro'], 'site:home', 'site:home', 'desktop', 1, 1],
    'record says: Pro opened from the homepage on a computer, form loaded, closed');
  ok(Number.isInteger(co.cs) && co.cs >= 0 && co.cs < 10, 'seconds open recorded');
  ok(co.ap === undefined, 'no Apple Pay value where the browser cannot tell');
  ok(!JSON.stringify(u).includes('test@example.invalid'), 'the email never enters the record');
  let meta = await page.evaluate(() => window.__SB.meta);
  eq(meta.ui_lang, 'en', 'other account metadata kept');

  // 2. Same page: open the Hunt Pass and pay.
  await clickCheckout(page, 'pass');
  ok(await overlayOpen(page, 'pass'), 'Hunt Pass checkout opens');
  await wait(200);
  await page.evaluate(() => { const o = window.__whop[window.__whop.length - 1]; o.onComplete({ result: 'payment' }); });
  await wait(400);
  co = await lastCo(page);
  eq([co.o, co.p, co.pl, co.r, co.c], [2, 'pass', ['pro', 'pass'], 'paid', 1], 'payment written at once, without waiting');
  ok(typeof co.rt === 'string' && !isNaN(Date.parse(co.rt)), 'payment time stored');
  const before = (await updates(page)).length;
  await page.keyboard.press('Escape');
  await wait(2200);
  co = await lastCo(page);
  eq(co.c, 1, 'closing after a payment is not counted as "closed without paying"');
  ok((await updates(page)).length - before <= 1, 'no stream of writes');
  await ctx.close();

  // 3. Back from a bank page with a failed payment: the note shows, the checkout reopens (existing behaviour),
  //    and the record keeps the failure.
  ({ page, ctx } = await open('/plans?checkout=pass&status=failed', { signedIn: true, meta: {} }));
  await page.waitForFunction(() => !document.getElementById('pay-retry').hidden, { timeout: 5000 });
  ok(true, 'failed-payment note shown (existing behaviour)');
  for (let i = 0; i < 40 && !(await overlayOpen(page, 'pass')); i++) await wait(50);
  ok(await overlayOpen(page, 'pass'), 'checkout reopened after the plan was confirmed (existing behaviour)');
  await wait(2200);
  co = await lastCo(page);
  eq([co.r, co.o, co.p, co.src], ['failed', 1, 'pass', 'direct'], 'failure kept, reopen counted');
  await ctx.close();

  // 4. Signed out: sign-up links, no checkout, no write, Whop never loaded.
  ({ page, ctx } = await open('/plans', { signedIn: false }));
  await page.waitForSelector('a[data-cta="pro"]');
  await wait(1200);
  const href = await page.$eval('a[data-cta="pro"]', a => a.getAttribute('href'));
  ok(/^\/signup\?plan=pro/.test(href), 'signed out: Pro button leads to sign-up (existing behaviour)');
  await page.$eval('a[data-cta="pro"]', a => a.addEventListener('click', e => e.preventDefault(), { once: true }));
  await page.$eval('a[data-cta="pro"]', a => a.click());
  await wait(1800);
  eq((await updates(page)).length, 0, 'signed out: nothing written');
  eq(page.__whopRequests, 0, 'signed out: Whop script never requested');
  await ctx.close();

  // 5. Whop's script cannot load: the hosted fallback shows (existing behaviour) and is counted.
  ({ page, ctx } = await open('/plans', { signedIn: true, meta: {} }, { whopDown: true }));
  await clickCheckout(page, 'solo');
  await page.waitForFunction(() => { const l = document.querySelector('[data-whop-embed-overlay="solo"] [data-hosted-fallback]'); return l && !l.hidden; }, { timeout: 5000 });
  ok(true, 'hosted fallback link shown (existing behaviour)');
  await page.keyboard.press('Escape');
  await wait(2200);
  co = await lastCo(page);
  eq([co.o, co.p, co.fb, co.ld, co.c, co.src], [1, 'solo', 1, undefined, 1, 'direct'], 'fallback counted, no "loaded", closed');
  await ctx.close();

  // 6. Another device wrote since this page loaded: counts continue from the stored record.
  ({ page, ctx } = await open('/plans?promo=STAY50', { signedIn: true,
    meta: { co: { v: 1, t0: '2026-11-10T09:00:00.000Z', o: 1, p: 'solo', pl: ['solo'] } },
    serverMeta: { co: { v: 1, t0: '2026-11-10T09:00:00.000Z', o: 5, p: 'solo', pl: ['solo'], r: 'canceled', rt: '2026-11-13T09:00:00.000Z' } } }));
  await clickCheckout(page, 'kickstart');
  await wait(200);
  await page.keyboard.press('Escape');
  await wait(2200);
  co = await lastCo(page);
  eq([co.o, co.pl, co.r, co.t0, co.src, co.src1], [6, ['solo', 'kickstart'], 'canceled', '2026-11-10T09:00:00.000Z', 'email', 'email'],
    'merged onto the newer stored record; came from the trial-ended email');
  await ctx.close();

  // 7. iPhone with Apple Pay available.
  ({ page, ctx } = await open('/plans', { signedIn: true, meta: {} }, { ua: IPHONE, applePay: true, viewport: { width: 390, height: 844, isMobile: true, hasTouch: true } }));
  await clickCheckout(page, 'pro');
  await wait(200);
  await page.keyboard.press('Escape');
  await wait(2200);
  co = await lastCo(page);
  eq([co.d, co.ap, co.p], ['ios-safari', 1, 'pro'], 'iPhone in Safari, Apple Pay available');
  await ctx.close();

  eq(errors, [], 'no page errors in any scenario');
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' checkout-record page checks.');
})().catch(async (e) => { console.error(e); process.exit(1); });
