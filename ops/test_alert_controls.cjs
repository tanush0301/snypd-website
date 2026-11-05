/*
 * Live-review fixes (Session 67, 5 Nov 2026): what the Feed shows about alerts, the phone status line, quiet hours in
 * Profile, the Start button while running, and the XP unclaim reversal.
 *   node ops/test_alert_controls.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js; the browser's notification permission and push
 * subscription are stubbed per scenario (off / denied / on), everything else is the page's own code.
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
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

async function xpUnit() {
  // The function itself, cut out of dashboard.html and run against a fake ledger.
  const html = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8').replace(/\r\n/g, '\n');
  const start = html.indexOf('    const reversingItems = new Set();');
  const end = html.indexOf('\n    }\n', html.indexOf('reversingItems.delete(itemId);')) + 6;
  ok(start > 0 && end > start, 'XP reversal function found');
  const src = html.slice(start, end);
  function ledger(rows) {
    const sb = { from: () => {
      const q = { _f: {}, select() { return q; }, eq(k, v) { q._f[k] = v; return q; }, in(k, v) { q._in = v; return q; },
        then(res) { return Promise.resolve({ data: rows.filter(r => r.item_id === q._f.item_id && q._in.includes(r.event_type)), error: null }).then(res); },
        insert: async row => { await new Promise(r => setTimeout(r, 5)); rows.push(row); return { error: null }; } };
      return q;
    } };
    const ctx = { sb, uid: 'u1', Date, console: { error() {} }, Number, Set, Promise, setTimeout };
    vm.createContext(ctx);
    vm.runInContext(src + '\nthis.reverse = reverseClaimXPIfWithin24h;', ctx);
    return ctx.reverse;
  }
  const now = new Date().toISOString();
  let rows = [{ item_id: 'i1', event_type: 'claim', xp: 25 }, { item_id: 'i1', event_type: 'first_claim', xp: 25 }];
  let rev = ledger(rows);
  for (let k = 0; k < 5; k++) await rev('i1', now);
  eq(rows.filter(r => r.event_type === 'unclaim_reversal').map(r => r.xp), [-50], 'five unclaims in a row take back 50 once (was 5 x -50)');
  rows = [{ item_id: 'i2', event_type: 'claim', xp: 25 }, { item_id: 'i2', event_type: 'deal_quality_bonus', xp: 21 }];
  rev = ledger(rows);
  await Promise.all([rev('i2', now), rev('i2', now), rev('i2', now)]);
  eq(rows.filter(r => r.event_type === 'unclaim_reversal').map(r => r.xp), [-46], 'three unclaims at the same moment: one reversal');
  rows = [{ item_id: 'i3', event_type: 'claim', xp: 25 }, { item_id: 'i3', event_type: 'first_claim', xp: 25 },
    ...Array(5).fill({ item_id: 'i3', event_type: 'unclaim_reversal', xp: -50 }), { item_id: 'i3', event_type: 'reconcile', xp: 200 }];
  rev = ledger(rows);
  await rev('i3', now);
  eq(rows.length, 8, 'the corrected 6 Sept item gets no new reversal');
  rows = [{ item_id: 'i4', event_type: 'claim', xp: 25 }];
  rev = ledger(rows);
  await rev('i4', new Date(Date.now() - 25 * 3600000).toISOString());
  eq(rows.length, 1, 'older than 24 h: nothing reversed (unchanged rule)');
}

(async () => {
  await xpUnit();
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, mode, vp, ctx) {
    const page = await (ctx || browser).newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    await page.emulateTimezone('Europe/Brussels');
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument(m => {
      Object.defineProperty(Notification, 'permission', { configurable: true, get: () => (m === 'denied' ? 'denied' : m === 'on' ? 'granted' : 'default') });
      const sub = { endpoint: 'https://push.example/qa', toJSON() { return { endpoint: this.endpoint, keys: { p256dh: 'a', auth: 'b' } }; }, unsubscribe: async () => true };
      PushManager.prototype.getSubscription = async function () { return m === 'on' ? sub : null; };
      ServiceWorkerRegistration.prototype.showNotification = async function () { window.__shown = (window.__shown || 0) + 1; };
    }, mode);
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('#list .card', { timeout: 10000 });
    await page.waitForFunction(() => window.SNYPD && window.SNYPD.alertsStatus, { timeout: 8000 });
    await page.evaluate(() => window.SNYPD.alertsStatus());
    await wait(700);
    return page;
  }
  const vis = (p, sel) => p.$eval(sel, e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length) && getComputedStyle(e).visibility !== 'hidden').catch(() => false);
  const read = async p => ({
    card: await vis(p, '#alerts-setup-card'), chip: await vis(p, '#alerts-chip'), chipText: await p.$eval('#alerts-chip', e => e.textContent),
    chipHref: await p.$eval('#alerts-chip', e => e.getAttribute('href')), test: await vis(p, '#btn-notify-test'), notify: await vis(p, '#btn-notify'),
    guide: await vis(p, '#alerts-guide-link'), note: await p.$eval('#notify-note', e => e.style.display === 'none' ? '' : e.textContent),
    start: await vis(p, '#btn-start'), stop: await vis(p, '#btn-stop'), state: (await p.evaluate(() => window.SNYPD.alertsStatus())).state,
  });

  // ---- 1. not set up yet: one card with "Not now"; no chip, no buttons
  const ctx1 = await browser.createBrowserContext();
  let page = await open('plan=elite&pr=1', 'off', null, ctx1);
  let s = await read(page);
  eq(s.state, 'off', 'state off');
  eq([s.card, s.chip, s.test, s.notify, s.guide], [true, false, false, false, false], 'off: only the setup card');
  ok(/Get a push when your hunts find something, without keeping SNYPD open\./.test(await page.$eval('#alerts-setup-card', e => e.innerText)), 'card says what it is for (no stale "Your hunt is saved")');
  eq([s.start, s.stop], [false, true], 'running: Stop only (no greyed "Running..." button)');
  await page.click('#alerts-setup-later'); await wait(200);
  eq((await read(page)).card, false, 'Not now hides the card');
  ok(Number(await page.evaluate(() => localStorage.getItem('snypd_alerts_card_snooze'))) > Date.now() + 29 * 86400000, 'snoozed for 30 days on this device');
  await page.close();
  page = await open('plan=elite&pr=1', 'off', null, ctx1);
  eq((await read(page)).card, false, 'still hidden after a reload');
  await page.close();
  await ctx1.close();

  // ---- 2. blocked by the browser: one warning chip with the guide, nothing else
  page = await open('plan=elite&pr=1', 'denied');
  s = await read(page);
  eq([s.state, s.card, s.chip, s.chipText, s.chipHref, s.test, s.notify, s.guide, s.note],
    ['denied', false, true, 'Alerts blocked: how to fix', '/vinted-alerts-on-your-phone', false, false, false, ''], 'denied: one chip linking to the guide');
  await page.close();

  // ---- 3. alerts on: chip; Test this device until a test succeeded here, then only in Profile
  const ctx3 = await browser.createBrowserContext();
  page = await open('plan=elite&pr=1', 'on', null, ctx3);
  s = await read(page);
  eq([s.state, s.card, s.chip, s.chipText, s.chipHref, s.test, s.notify, s.guide, s.note], ['on', false, true, 'Alerts on', null, true, false, false, ''], 'on: chip + one Test button');
  await page.click('#btn-notify-test'); await wait(300);
  eq(await page.evaluate(() => window.__shown), 1, 'test notification shown');
  eq((await read(page)).test, false, 'after a successful test the button leaves the Feed');
  await page.close();
  page = await open('plan=elite&pr=1', 'on', null, ctx3);
  eq((await read(page)).test, false, 'and stays gone after a reload');
  await page.click('#topbar-profile-trigger'); await wait(900);
  ok(await vis(page, '#prof-push-test'), 'Profile keeps "Send a test notification"');
  ok(!(await vis(page, '#prof-alerts-guide')), 'no guide link in Profile while alerts are on');
  await page.click('#prof-push-test'); await wait(300);
  eq(await page.evaluate(() => window.__shown), 1, 'Profile test shows a notification');
  ok(/Test sent\./.test(await page.$eval('#prof-notify-result', e => e.textContent)), 'Profile says the test was sent');

  // ---- 4. quiet hours: saved through the RPC with the browser's time zone
  ok(/your time/.test(await page.$eval('#prof-quiet-note', e => e.textContent)), 'quiet hours are in the user\'s own time');
  await page.click('#prof-toggle-quiet'); await wait(400);
  eq(await page.evaluate(() => window.__quietRpc), [{ p_on: true, p_tz: 'Europe/Brussels' }], 'switch on -> set_push_quiet_hours(true, Europe/Brussels)');
  eq(await page.$eval('#prof-toggle-quiet', e => e.getAttribute('aria-checked')), 'true', 'switch stays on');
  eq(await page.$eval('#prof-quiet-note', e => e.textContent), 'No alerts 23:00 - 08:00 (Europe/Brussels), then one summary.', 'note names the time zone');
  await page.click('#prof-toggle-quiet'); await wait(400);
  eq((await page.evaluate(() => window.__quietRpc))[1], { p_on: false, p_tz: 'Europe/Brussels' }, 'switch off -> RPC off');
  await page.close();
  await ctx3.close();

  // ---- 5. phone: listings first, details on demand
  page = await open('plan=elite&pr=1', 'on', { width: 390, height: 844, isMobile: true, hasTouch: true });
  const ph = await page.evaluate(() => ({
    plan: getComputedStyle(document.getElementById('plan-banner')).display, tick: getComputedStyle(document.getElementById('tick-chip')).display,
    stats: getComputedStyle(document.getElementById('feed-stats')).display, more: getComputedStyle(document.getElementById('status-more')).display,
    card: Math.round(document.querySelector('#list .card').getBoundingClientRect().top), h: innerHeight,
    overflow: document.documentElement.scrollWidth - innerWidth,
  }));
  eq([ph.plan, ph.tick, ph.stats], ['none', 'none', 'none'], 'phone: plan, last check and stats folded away');
  ok(ph.more !== 'none' && ph.card < ph.h, 'phone: Details button, first listing on the first screen (top ' + ph.card + ' of ' + ph.h + ')');
  ok(ph.overflow <= 0, 'phone: no horizontal overflow');
  await page.click('#status-more'); await wait(150);
  eq(await page.evaluate(() => [getComputedStyle(document.getElementById('feed-stats')).display !== 'none', document.getElementById('status-more').textContent, document.getElementById('status-more').getAttribute('aria-expanded')]),
    [true, 'Hide details', 'true'], 'Details opens the stats');
  await page.close();
  page = await open('plan=elite&pr=1', 'on');
  eq(await page.evaluate(() => [getComputedStyle(document.getElementById('status-more')).display, getComputedStyle(document.getElementById('feed-stats')).display !== 'none']), ['none', true], 'desktop: unchanged, no Details button');
  await page.close();

  // ---- 6. French
  page = await open('plan=elite&pr=1&lang=fr', 'denied');
  eq(await page.$eval('#alerts-chip', e => [e.textContent, e.getAttribute('href')]), ['Alertes bloqu\u00e9es\u00a0: comment corriger', '/fr/alertes-vinted-telephone'], 'French chip + French guide');
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' alert-control checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
