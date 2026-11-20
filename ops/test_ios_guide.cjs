/*
 * iPhone Home Screen guide on the REAL dashboard.html (17 Nov 2026).
 *   node ops/test_ios_guide.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * dashboard.html in headless Chrome with ops/qa_mock.js, one browser context per device profile.
 * navigator.share is stubbed and logged; nothing leaves the machine.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
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
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const IPHONE_IG = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 350.0.0.0';
const IPHONE_TT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly_36.0.0 BytedanceWebview';
const ANDROID = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36';
const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
const SMALL = { width: 320, height: 568, isMobile: true, hasTouch: true };

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(pr, q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setUserAgent(pr.ua);
    await page.setViewport(pr.vp || PHONE);
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') ? r.continue() : r.abort()));
    await page.evaluateOnNewDocument((grant, share) => {
      let perm = 'default', sub = null;
      window.__shares = [];
      if (share) navigator.share = async d => { window.__shares.push(d); };
      else { try { delete Navigator.prototype.share; } catch (e) {} try { Object.defineProperty(navigator, 'share', { configurable: true, value: undefined }); } catch (e) {} }
      Object.defineProperty(Notification, 'permission', { configurable: true, get: () => perm });
      Notification.requestPermission = async () => { perm = grant; return perm; };
      const mk = () => ({ endpoint: 'https://push.example/qa', toJSON() { return { endpoint: this.endpoint, keys: { p256dh: 'a', auth: 'b' } }; }, unsubscribe: async () => { sub = null; return true; } });
      PushManager.prototype.getSubscription = async function () { return sub; };
      PushManager.prototype.subscribe = async function () { if (perm !== 'granted') throw new DOMException('denied', 'NotAllowedError'); sub = mk(); return sub; };
      ServiceWorkerRegistration.prototype.showNotification = async function () {};
    }, pr.grant || 'granted', pr.share !== false);
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(2500);
    return { page, ctx };
  }
  const vis = (p, sel) => p.$eval(sel, e => !e.hidden && e.getClientRects().length > 0).catch(() => false);
  const sent = p => p.evaluate(() => (window.__qa_auth_updates || []).filter(u => u && u.data && u.data.fs).map(u => u.data.fs));
  async function toAlertsStep(page) {
    await page.type('#wiz-q-words', 'nike tech');
    await page.type('#wiz-q-max', '40');
    await page.click('#wiz-q-save'); await wait(1500);
    ok(await vis(page, '#wiz-step-2'), 'alerts step shown');
  }
  const NEW = 'plan=free&hunts=0&boot=1&joined=fresh';

  // ---- 1. iPhone Safari, wizard: the guide opens with three steps and a share button ----
  for (const vp of [PHONE, SMALL]) {
    const { page, ctx } = await open({ ua: IPHONE, vp }, NEW);
    ok(!(await vis(page, '#ios-guide')), 'guide hidden on load (' + vp.width + ')');
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(1200);
    ok(await vis(page, '#ios-guide'), 'guide opens after "turn on alerts" on iPhone Safari');
    eq(await page.$$eval('#ios-guide-steps li', l => l.length), 3, 'three steps');
    eq(await page.$$eval('#ios-guide-steps svg', l => l.length), 3, 'each step has a drawing');
    ok(!(await vis(page, '#ios-guide-inapp')), 'no in-app note in Safari');
    ok(await vis(page, '#ios-guide-share'), 'share button offered');
    const box = await page.$eval('#ios-guide .filter-sheet', e => { const r = e.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, w: e.scrollWidth - e.clientWidth }; });
    ok(box.top >= 0 && box.bottom <= vp.height + 1, 'the whole sheet fits the screen at ' + vp.width + 'x' + vp.height + ': ' + JSON.stringify(box));
    ok(box.w <= 0 && await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'no sideways overflow');
    const txt = await page.$eval('#wiz-alert-result', e => e.textContent);
    ok(txt.length < 110 && /Home Screen/.test(txt), 'wizard shows one short line, got ' + txt.length + ' chars');
    eq(await page.$eval('#wiz-enable-alerts', e => e.textContent), 'Show the steps again', 'no looping "Try again"');
    await page.click('#ios-guide-share'); await wait(300);
    const shares = await page.evaluate(() => window.__shares);
    eq(shares.length, 1, 'share sheet opened once');
    ok(/\/dashboard$/.test(shares[0].url) && !/\?/.test(shares[0].url), 'shares the clean dashboard address: ' + shares[0].url);
    ok(await vis(page, '#ios-guide'), 'steps stay on screen after the share sheet');
    await page.click('#ios-guide-later'); await wait(300);
    ok(!(await vis(page, '#ios-guide')), '"Later" closes the guide');
    ok(await vis(page, '#wiz-step-2'), 'the wizard is still there');
    await page.click('#wiz-enable-alerts'); await wait(1200);
    ok(await vis(page, '#ios-guide'), '"Show the steps again" reopens it');
    await page.mouse.click(vp.width / 2, 8); await wait(300);
    ok(!(await vis(page, '#ios-guide')), 'tapping the dimmed area closes it');
    await wait(3600);
    const all = await sent(page), last = all[all.length - 1];
    eq([last.ig, last.al, last.dev], ['share', 'ios', 'ios-safari'], 'record: guide reached the share step');
    await ctx.close();
  }

  // ---- 2. iPhone inside Instagram / TikTok: told to open Safari first, no share button ----
  for (const ua of [IPHONE_IG, IPHONE_TT]) {
    const { page, ctx } = await open({ ua }, NEW);
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(1200);
    ok(await vis(page, '#ios-guide'), 'guide opens in an in-app browser');
    ok(await vis(page, '#ios-guide-inapp'), 'in-app note shown');
    ok(/Safari/.test(await page.$eval('#ios-guide-inapp', e => e.textContent)), 'it says to open Safari');
    ok(!(await vis(page, '#ios-guide-share')), 'no share button (that sheet has no Add to Home Screen)');
    eq((await page.evaluate(() => window.__shares)).length, 0, 'nothing shared');
    ok(!(await vis(page, '#ios-guide-share-hint')), 'no "button below" sentence when there is no button');
    ok(!/button below/i.test(await page.$eval('#ios-guide', e => e.innerText)), 'the guide never mentions a button it does not show');
    await ctx.close();
  }
  {
    const { page, ctx } = await open({ ua: IPHONE }, NEW);
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(1200);
    ok(await vis(page, '#ios-guide-share-hint'), 'Safari: the "button below" sentence is shown with the button');
    await ctx.close();
  }

  // ---- 3. iPhone Safari without navigator.share: steps only ----
  {
    const { page, ctx } = await open({ ua: IPHONE, share: false }, NEW);
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(1200);
    ok(await vis(page, '#ios-guide') && !(await vis(page, '#ios-guide-share')), 'guide without a share button when the browser has none');
    await ctx.close();
  }

  // ---- 4. Android: alerts simply come on, the guide never appears ----
  {
    const { page, ctx } = await open({ ua: ANDROID }, NEW);
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(3000);
    ok(!(await vis(page, '#ios-guide')), 'no iPhone guide on Android');
    ok(!(await vis(page, '#wiz-step-2')), 'wizard closed: alerts are on');
    await wait(3600);
    const all = await sent(page), last = all[all.length - 1];
    eq([last.al, last.ig], ['on', undefined], 'record: alerts on, no guide');
    await ctx.close();
  }

  // ---- 5. iPhone Safari, existing account: the header button opens the guide ----
  {
    const { page, ctx } = await open({ ua: IPHONE }, 'plan=free&hunts=1&boot=1');
    ok(!(await vis(page, '#ios-guide')), 'guide hidden on load for an existing account');
    ok(await page.$eval('#btn-notify', e => e.classList.contains('btn-cta-instruct')), 'header button is the iPhone instruction button');
    await page.$eval('#btn-notify', e => e.click()); await wait(600);
    ok(await vis(page, '#ios-guide'), 'header button opens the guide');
    eq((await page.evaluate(() => window.__shares)).length, 0, 'the share sheet waits for the button inside the guide');
    await ctx.close();
  }

  // ---- 5b. Small phone (375x553 visible): the wizard scrolls, starts at its top, and the save button works ----
  {
    const { page, ctx } = await open({ ua: IPHONE, vp: { width: 375, height: 553, isMobile: true, hasTouch: true } }, NEW);
    const m = await page.evaluate(() => {
      const ov = document.getElementById('wiz-overlay'), s = document.getElementById('wiz-step-1');
      return { flow: getComputedStyle(ov).overflowY, top: s.getBoundingClientRect().top, ch: ov.clientHeight, sh: ov.scrollHeight };
    });
    ok(m.flow === 'auto' || m.flow === 'scroll', 'the wizard overlay scrolls: ' + JSON.stringify(m));
    ok(m.top >= 0, 'the first step starts on screen, not cut off above it: ' + JSON.stringify(m));
    ok(m.sh > m.ch, 'the step is taller than this screen, so scrolling is what makes it usable');
    await toAlertsStep(page);
    await ctx.close();
  }

  // ---- 6. French: every part of the guide is translated (Safari and in-app) ----
  for (const ua of [IPHONE, IPHONE_IG]) {
    const { page, ctx } = await open({ ua }, NEW + '&lang=fr');
    await toAlertsStep(page);
    await page.click('#wiz-enable-alerts'); await wait(1500);
    ok(await vis(page, '#ios-guide'), 'guide opens in French');
    const t = await page.$eval('#ios-guide', e => e.innerText);
    ok(/Touche Partager/.test(t) && /cran d.accueil/.test(t) && /nouvelle ic/.test(t) && /Plus tard/i.test(t), 'French steps shown: ' + t.slice(0, 200));
    const left = t.match(/Tap |Home Screen|Open SNYPD|Later|About 1 minute|Scroll down|Share menu|sign in|inside another/gi);
    eq(left, null, 'no English left in the guide: ' + JSON.stringify(left) + ' in: ' + t);
    const line = await page.$eval('#wiz-alert-result', e => e.textContent);
    ok(/Sur iPhone/.test(line), 'wizard line in French: ' + line);
    ok(/Revoir/.test(await page.$eval('#wiz-enable-alerts', e => e.textContent)), 'button in French');
    const box = await page.$eval('#ios-guide .filter-sheet', e => { const r = e.getBoundingClientRect(); return { top: r.top, bottom: r.bottom }; });
    ok(box.top >= 0 && box.bottom <= 845, 'the French sheet fits 390x844: ' + JSON.stringify(box));
    await ctx.close();
  }

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' iPhone guide checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks:', e.message); process.exit(1); });
