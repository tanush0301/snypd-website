/*
 * Paying customer's first days (14 Nov 2026, website outreach/62 move 2).
 *   node ops/test_paid_check.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Part A runs the real activation poller in a sandbox: confirming a paid plan starts the 72 h check on this device.
 * Part B runs the REAL dashboard.html with ops/qa_mock.js in headless Chrome: the three rows in every state, their
 * actions, Done, the 72 h window, plans, the referral card waiting for the check, French, 390 px, no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const vm = require('node:vm');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const html = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8');
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  // ---------------------------------------------------------------- Part A: the activation poller starts the window
  {
    const a = html.indexOf('  (function activationWatch() {'), b = html.indexOf('  // Topbar founding badge', a);
    assert(a > 0 && b > a, 'activation poller found');
    const local = {}, session = {}, replaced = [];
    let tick = null;
    const el = () => ({ style: {}, textContent: '', querySelector: () => ({ style: {}, textContent: '' }) });
    const g = {
      URLSearchParams, location: { search: '?activated=pro', replace: u => replaced.push(u) }, effectivePlan: 'free', eliteBanner: el(),
      document: { getElementById: () => el() }, window: {}, uid: 'test-account', Date, JSON,
      ACTIVE_STATUSES: new Set(['active', 'trialing', 'past_due', 'unpaid']),
      sb: { from: () => ({ select: () => ({ eq: () => ({ maybeSingle: async () => ({ data: { subscription_plan: 'pro', sub_status: 'active' } }) }) }) }) },
      setInterval: fn => { tick = fn; return 1; }, clearInterval: () => {},
      sessionStorage: { setItem: (k, v) => { session[k] = String(v); } }, localStorage: { setItem: (k, v) => { local[k] = String(v); } },
    };
    vm.runInNewContext(html.slice(a, b), g);
    ok(typeof tick === 'function', 'poller scheduled');
    const before = Date.now();
    await tick();
    const mark = JSON.parse(local.snypd_paid_check || 'null');
    ok(mark && mark.p === 'pro' && mark.t >= before && mark.t <= Date.now() && !mark.done, 'paid plan confirmed: the 72 h check starts on this device');
    eq([session.snypd_just_activated, replaced], ['pro', ['/dashboard']], 'existing behaviour kept: referral marker + reload to the dashboard');
  }

  // ---------------------------------------------------------------- Part B: the real dashboard
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
  const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1';
  const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
  const H = 3600000;
  // A fresh private context per page; seed = what this device stored before (marker, referral marker).
  async function open(q, { seed = {}, session = {}, ua, vp } = {}) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    if (ua) await page.setUserAgent(ua);
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument((seed, session) => {
      if (window.__seeded) return;
      window.__seeded = true;
      try { if (!sessionStorage.getItem('__seeded')) { sessionStorage.setItem('__seeded', '1'); for (const k in seed) localStorage.setItem(k, seed[k]); for (const k in session) sessionStorage.setItem(k, session[k]); } } catch (e) {}
    }, seed, session);
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(2200);
    page.ctx = ctx;
    return page;
  }
  const mark = (hoursAgo, plan = 'elite', done) => JSON.stringify(Object.assign({ p: plan, t: Date.now() - hoursAgo * H }, done ? { done: 1 } : {}));
  const vis = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.style.display !== 'none' && !e.hidden && e.getClientRects().length > 0; }, sel);
  const card = p => p.evaluate(() => {
    const c = document.getElementById('paid-check');
    const rows = [...document.querySelectorAll('#paid-check-list li')].map(li => ({ ok: li.classList.contains('pc-ok'),
      text: [...li.querySelectorAll('.pc-body > span')].map(s => s.textContent).join(' '), acts: [...li.querySelectorAll('[data-pc-act]')].map(b => b.getAttribute('data-pc-act')) }));
    return { shown: !!c && c.style.display !== 'none', title: (document.getElementById('paid-check-title') || {}).textContent, done: (document.getElementById('paid-check-done') || {}).textContent, rows };
  });
  // The alert state and device come from the page; tests pin the alert state, then repaint.
  const paint = (p, state) => p.evaluate(async state => { window.SNYPD.alertsStatus = async () => ({ ready: true, state }); await window.SNYPD.paintPaidCheck(); }, state);

  // ---- 1. Elite on a computer, 1 h after paying, alerts on this computer: searches ok, alerts + volume to do
  let page = await open('plan=elite', { seed: { snypd_paid_check: mark(1) } });
  ok((await card(page)).shown, 'check shown in the first 72 h');
  await paint(page, 'on');
  let c = await card(page);
  eq(c.title, 'Your plan is live: three quick checks', 'title');
  eq(c.done, 'Done', 'button');
  eq(c.rows.map(r => r.ok), [true, false, false], 'searches ok, alerts and volume to do');
  eq(c.rows[0].text, '1 search is running 24/7. Your plan allows 10.', 'searches row');
  eq(c.rows[0].acts, ['add'], 'add a search offered while below the plan limit');
  eq(c.rows[1].text, 'Alerts reach this computer only while the browser runs. On your phone, open snypd.store/dashboard, sign in and turn alerts on.', 'computer-only alerts row');
  eq(c.rows[2].text, '1 of your searches has no max price and alerts on every match: it can bring more alerts than anyone can open.', 'volume row');
  eq(c.rows[2].acts, ['review'], 'review offered');
  // Review them opens the Filters sheet
  await page.click('#paid-check [data-pc-act="review"]'); await wait(800);
  ok(await vis(page, '#fs-q-words'), '"Review them" opens the Filters sheet');
  await page.keyboard.press('Escape'); await wait(300);
  // Alerts off: Turn on alerts calls the real enable path, then repaints
  await page.evaluate(() => { window.__enable = 0; window.SNYPD.enableAlerts = async () => { window.__enable++; return { ok: true, state: 'on' }; }; });
  await paint(page, 'off');
  c = await card(page);
  eq([c.rows[1].text, c.rows[1].acts], ['Alerts are off on this device.', ['alerts']], 'alerts off row');
  await page.$eval('#paid-check [data-pc-act="alerts"]', b => b.click()); await wait(600);
  eq(await page.evaluate(() => window.__enable), 1, '"Turn on alerts" uses the dashboard\'s own enable path');
  for (const [state, text, acts] of [
    ['ios-install', 'On iPhone, alerts need SNYPD on the Home Screen first.', ['guide']],
    ['denied', 'Notifications are blocked in this browser. Allow them in the browser settings for this site.', []],
    ['unsupported', 'This browser cannot show alerts. Use Chrome or Safari on your phone.', []],
  ]) {
    await paint(page, state);
    c = await card(page);
    eq([c.rows[1].ok, c.rows[1].text, c.rows[1].acts], [false, text, acts], 'alerts row for ' + state);
  }
  // A search on Calm without a max price does not flood the phone: the volume row is fine.
  await page.evaluate(() => { window.__qaDB.user_searches.forEach(h => { h.push_mode = 'calm'; }); });
  await paint(page, 'on');
  c = await card(page);
  eq([c.rows[2].ok, c.rows[2].text], [true, 'Every search has a max price or Calm alerts.'], 'Calm searches without a max are fine');
  await page.ctx.close();

  // ---- 2. iPhone app with alerts on, every search capped: all set; Send a test uses the dashboard's test; Done sticks
  page = await open('plan=elite', { seed: { snypd_paid_check: mark(5) }, ua: IPHONE, vp: PHONE });
  await page.evaluate(() => {
    window.__qaDB.user_searches.forEach(h => { h.vinted_url = h.vinted_url + '&price_to=60'; });
    window.__tests = 0; window.SNYPD.testDevice = () => { window.__tests++; };
  });
  await paint(page, 'on');
  c = await card(page);
  eq([c.title, c.done, c.rows.map(r => r.ok)], ['All set: your plan is working', 'Close', [true, true, true]], 'all three fine');
  eq([c.rows[1].text, c.rows[1].acts, c.rows[2].text], ['Alerts are on for this phone.', ['test'], 'Every search has a max price or Calm alerts.'], 'phone rows');
  await page.$eval('#paid-check [data-pc-act="test"]', b => b.click()); await wait(300);
  eq(await page.evaluate(() => window.__tests), 1, '"Send a test" uses the dashboard\'s test');
  ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'no sideways scroll at 390 px');
  await page.$eval('#paid-check-done', b => b.click()); await wait(300);
  ok(!(await card(page)).shown, 'Done hides it');
  ok(JSON.parse(await page.evaluate(() => localStorage.getItem('snypd_paid_check'))).done === 1, 'Done is remembered on this device');
  await page.reload({ waitUntil: 'domcontentloaded' }); await wait(2600);
  ok(!(await card(page)).shown, 'stays hidden after a reload');
  await page.ctx.close();

  // ---- 3. When it must not show: after 72 h, without a marker, on Free, already done
  for (const [q, seed, why] of [
    ['plan=elite', { snypd_paid_check: mark(73) }, 'more than 72 h after the plan went live'],
    ['plan=elite', {}, 'a paying account without the marker (paid before this release, or on another device)'],
    ['plan=free', { snypd_paid_check: mark(1, 'pro') }, 'the plan is no longer paid'],
    ['plan=elite', { snypd_paid_check: mark(1, 'elite', true) }, 'already done'],
  ]) {
    page = await open(q, { seed });
    ok(!(await card(page)).shown, 'not shown: ' + why);
    await page.ctx.close();
  }

  // ---- 4. The referral "plan is live" card waits for the check, then shows when it is done
  page = await open('plan=elite&refcode=1', { seed: { snypd_paid_check: mark(0.01) }, session: { snypd_just_activated: 'elite' } });
  ok((await card(page)).shown && !(await vis(page, '#ref-live-card')), 'check first, referral card waits');
  eq(await page.evaluate(() => localStorage.getItem('snypd_ref_live_later')), 'elite', 'referral kept for later');
  await page.$eval('#paid-check-done', b => b.click()); await wait(1200);
  ok(await vis(page, '#ref-live-card'), 'referral card shows once the check is done');
  eq(await page.evaluate(() => localStorage.getItem('snypd_ref_live_later')), null, 'referral marker used once');
  await page.ctx.close();
  page = await open('plan=elite&refcode=1', { session: { snypd_just_activated: 'elite' } });
  ok(await vis(page, '#ref-live-card') && !(await card(page)).shown, 'without the check the referral card shows as before');
  await page.ctx.close();

  // ---- 5. French
  page = await open('plan=elite&lang=fr', { seed: { snypd_paid_check: mark(1) }, vp: PHONE });
  await paint(page, 'on');
  await wait(400);
  c = await card(page);
  ok(/^Ton plan est actif\s:\strois vérifications rapides$/.test(c.title), 'French title: ' + c.title);
  ok(/^1 recherche tourne 24h\/24\. Ton plan en permet 10\.$/.test(c.rows[0].text), 'French searches row: ' + c.rows[0].text);
  ok(/^1 de tes recherches n’a pas de prix max/.test(c.rows[2].text), 'French volume row: ' + c.rows[2].text);
  ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'French: no sideways scroll at 390 px');
  await page.ctx.close();

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' paid-check checks.');
})().catch(e => { console.error(e); process.exit(1); });
