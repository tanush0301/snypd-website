/*
 * First-session measurement on the REAL dashboard.html (outreach/53, release R1).
 *   node ops/test_first_session.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * dashboard.html in headless Chrome with ops/qa_mock.js, one browser context per device profile. The browser's
 * notification permission and push subscription are stubbed per profile; everything else is the page's own code.
 * What is checked is what the page sends to Supabase Auth (the mock logs every updateUser in __qa_auth_updates).
 * No production request.
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
let dropModule = false;
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    if (p === '/assets/first-session.js' && dropModule) { res.writeHead(404); return res.end('gone'); }
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
const ANDROID = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36';
const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  // pr: { ua, vp, standalone, grant: 'granted' | 'denied' | 'default' }
  async function open(pr, q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    if (pr.ua) await page.setUserAgent(pr.ua);
    await page.setViewport(pr.vp || { width: 1280, height: 900 });
    await page.emulateTimezone('Europe/Brussels');
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') ? r.continue() : r.abort()));
    await page.evaluateOnNewDocument((standalone, grant) => {
      let perm = 'default', sub = null;
      if (standalone) Object.defineProperty(navigator, 'standalone', { configurable: true, get: () => true });
      Object.defineProperty(Notification, 'permission', { configurable: true, get: () => perm });
      Notification.requestPermission = async () => { perm = grant; return perm; };
      const mk = () => ({ endpoint: 'https://push.example/qa', toJSON() { return { endpoint: this.endpoint, keys: { p256dh: 'a', auth: 'b' } }; }, unsubscribe: async () => { sub = null; return true; } });
      PushManager.prototype.getSubscription = async function () { return sub; };
      PushManager.prototype.subscribe = async function () { if (perm !== 'granted') throw new DOMException('denied', 'NotAllowedError'); sub = mk(); return sub; };
      ServiceWorkerRegistration.prototype.showNotification = async function () {};
    }, !!pr.standalone, pr.grant || 'default');
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(2500);
    return { page, ctx };
  }
  const vis = (p, sel) => p.$eval(sel, e => !e.hidden && e.getClientRects().length > 0).catch(() => false);
  // every fs the page sent, oldest first; the last one is the stored record
  const sent = p => p.evaluate(() => (window.__qa_auth_updates || []).filter(u => u && u.data && u.data.fs).map(u => u.data.fs));
  const allUpdates = p => p.evaluate(() => JSON.stringify(window.__qa_auth_updates || []));
  async function wizard(page, { words, max, clearMin, enable = true, later = true }) {
    ok(await vis(page, '#wiz-step-1'), 'the wizard opens for an account without a hunt');
    await page.type('#wiz-q-words', words);
    if (max) await page.type('#wiz-q-max', String(max));
    if (clearMin) await page.$eval('#wiz-q-min', e => { e.value = ''; e.dispatchEvent(new Event('input', { bubbles: true })); });
    await page.click('#wiz-q-save'); await wait(1500);
    ok(await vis(page, '#wiz-step-mode'), 'alert-style step shown after the hunt is saved; the wizard says: '
      + await page.evaluate(() => ['wiz-q-err', 'wiz-q-hw'].map(i => document.getElementById(i)).map(e => (e && e.getClientRects().length ? e.innerText : '')).join(' / ')));
    await page.click('.wiz-mode'); await wait(200);
    await page.click('#wiz-mode-next'); await wait(1200);
    ok(await vis(page, '#wiz-step-2'), 'alerts step shown');
    if (enable) { await page.click('#wiz-enable-alerts'); await wait(3200); }
    if (later && await vis(page, '#wiz-finish')) { await page.click('#wiz-finish'); await wait(400); }
    await wait(3600);                                             // the tracker's quiet period
  }
  const NEW = 'plan=free&hunts=0&boot=1&joined=fresh';

  // ---- 1. iPhone in Safari: reaches step 3, is shown the Home Screen text, gives up -------------------------
  {
    const { page, ctx } = await open({ ua: IPHONE, vp: PHONE }, NEW);
    ok(typeof await page.evaluate(() => typeof window.SNYPD.fs) === 'string' && await page.evaluate(() => typeof window.SNYPD.fs === 'function'), 'the tracker is on for a fresh account');
    await wizard(page, { words: 'very secret words' });
    const all = await sent(page), last = all[all.length - 1];
    ok(all.length >= 1 && all.length <= 4, 'between 1 and 4 writes for the whole first session, got ' + all.length);
    eq([last.v, last.dev, last.devs, last.wz], [1, 'ios-safari', ['ios-safari'], 3], 'device and wizard step');
    eq([last.max, last.min, last.src], [0, 'def', 'quick'], 'first hunt: no price limit, the pre-filled minimum kept');
    eq([last.al, last.al1, last.al_try, last.later, last.al_on], ['ios', 'ios', 1, 1, undefined], 'alerts: shown the Home Screen text, then "later"');
    eq(last.card, 'shown', 'the set-up card appeared after the wizard');
    ok(last.app === undefined, 'not an installed app');
    const raw = await allUpdates(page);
    ok(!/secret|vinted\.|search_text/i.test(raw), 'no search words and no link ever leave the page in these writes');
    ok(Date.parse(last.t0) > Date.now() - 120000, 't0 is now');
    await ctx.close();
  }

  // ---- 2. Same account, later, inside the installed app: resumes from the card and turns alerts on ----------
  {
    const before = { v: 1, t0: new Date(Date.now() - 600000).toISOString(), dev: 'ios-safari', devs: ['ios-safari'], wz: 3, max: 0, min: 'def', src: 'quick', al_try: 1, al1: 'ios', al: 'ios', later: 1, card: 'shown' };
    const { page, ctx } = await open({ ua: IPHONE, vp: PHONE, standalone: true, grant: 'granted' },
      'plan=free&trial=1&boot=1&joined=fresh&meta=' + encodeURIComponent(JSON.stringify({ fs: before, marketing_opt_in: false })));
    ok(await vis(page, '#alerts-setup-card'), 'installed app with a hunt and no alerts shows the set-up card');
    await page.click('#alerts-setup-resume'); await wait(800);
    await page.click('#wiz-enable-alerts'); await wait(3200);
    await wait(3600);
    const all = await sent(page), last = all[all.length - 1];
    eq([last.dev, last.devs], ['ios-safari', ['ios-safari', 'ios-app']], 'the app is recorded as a second device');
    ok(Date.parse(last.app) > Date.now() - 120000, 'first open as an installed app is stamped');
    eq([last.al, last.al1, last.al_dev, last.al_try, last.card], ['on', 'ios', 'ios-app', 2, 'resume'], 'alerts came on in the app, after the card');
    ok(Date.parse(last.al_on) >= Date.parse(last.app), 'al_on is stamped');
    eq([last.wz, last.max, last.min, last.t0], [3, 0, 'def', before.t0], 'what Safari recorded is kept');
    await ctx.close();
  }

  // ---- 3. Android, permission refused --------------------------------------------------------------------------
  {
    const { page, ctx } = await open({ ua: ANDROID, vp: PHONE, grant: 'denied' }, NEW);
    // A price limit below the pre-filled minimum: step 1 refuses the form until the minimum is cleared.
    await page.type('#wiz-q-words', 'levis 501');
    await page.type('#wiz-q-max', '20');
    await page.click('#wiz-q-save'); await wait(700);
    ok(await vis(page, '#wiz-q-err') && !(await vis(page, '#wiz-step-mode')), 'max 20 with the pre-filled minimum is refused today');
    await page.$eval('#wiz-q-words', e => { e.value = ''; });
    await wizard(page, { words: 'levis 501', clearMin: true });
    const last = (await sent(page)).pop();
    eq([last.dev, last.al, last.al1, last.al_try, last.later], ['android', 'denied', 'denied', 1, 1], 'a refusal is recorded as a refusal');
    eq([last.max, last.min, last.werr], [1, 'none', 1], 'the price limit, the cleared minimum and the one form refusal are recorded');
    await ctx.close();
  }

  // ---- 4. Desktop, allowed; own minimum ------------------------------------------------------------------------
  {
    const { page, ctx } = await open({ grant: 'granted' }, NEW);
    await page.$eval('#wiz-q-min', e => { e.value = '5'; e.dispatchEvent(new Event('input', { bubbles: true })); });
    await wizard(page, { words: 'carhartt jacket', max: 60, later: false });
    const last = (await sent(page)).pop();
    eq([last.dev, last.al, last.al_dev, last.al_try, last.later, last.card], ['desktop', 'on', 'desktop', 1, undefined, undefined], 'alerts on in the wizard: no "later", no card');
    eq([last.max, last.min, last.wz], [1, 'own', 3]);
    await ctx.close();
  }

  // ---- 5. "Set this up later" without trying: no attempt, no refusal ---------------------------------------------
  {
    const { page, ctx } = await open({ ua: ANDROID, vp: PHONE, grant: 'granted' }, NEW);
    await wizard(page, { words: 'nike dunk low', enable: false });
    const last = (await sent(page)).pop();
    eq([last.al, last.al_try, last.later, last.wz], [undefined, undefined, 1, 3], 'never asked: recorded as "later" only');
    await ctx.close();
  }

  // ---- 6. First hunt saved through "I have a Vinted link" (Filters sheet) ----------------------------------------
  {
    const { page, ctx } = await open({ grant: 'granted' }, NEW);
    await page.click('#wiz-build-own'); await wait(800);
    await page.type('#fs-q-words', 'stussy hoodie');
    await page.type('#fs-q-max', '40');
    await page.click('#filter-new-save'); await wait(2500);
    await wait(3600);
    const last = (await sent(page)).pop();
    eq([last.src, last.max], ['sheet', 1], 'a first hunt from the Filters sheet is recorded with its source');
    ok(last.wz >= 1, 'the wizard step it left from is kept');
    await ctx.close();
  }

  // ---- 7. The "too broad" card and the coach card -----------------------------------------------------------------
  {
    let { page, ctx } = await open({ ua: IPHONE, vp: PHONE }, 'plan=free&trial=1&boot=1&joined=fresh&broad=1');
    await page.waitForFunction(() => { const e = document.getElementById('broad-hunt'); return e && !e.hidden && e.getClientRects().length > 0; }, { timeout: 15000 });
    await wait(3600);
    let last = (await sent(page)).pop();
    eq([last.vol, last.vol_k], ['shown', 'broad'], 'broad card shown');
    await page.$eval('#broad-hunt-calm', e => e.click()); await wait(3800);
    last = (await sent(page)).pop();
    eq([last.vol, last.vol_k], ['calm', 'broad'], '"Switch to Calm" recorded');
    // by now the page's own status read (4 s after load) and its write have happened
    eq([last.al, last.al_try], [undefined, undefined], 'an iPhone that never tapped "Turn on alerts" has no alerts result');
    await ctx.close();
    ({ page, ctx } = await open({ ua: IPHONE, vp: PHONE }, 'plan=free&trial=1&boot=1&joined=fresh&coach=busy'));
    await page.waitForFunction(() => { const e = document.getElementById('broad-hunt-apply'); return e && !e.hidden && e.getClientRects().length > 0; }, { timeout: 15000 });
    await wait(3600);
    last = (await sent(page)).pop();
    eq([last.vol, last.vol_k], ['shown', 'coach'], 'coach card shown');
    await page.$eval('#broad-hunt-apply', e => e.click()); await wait(3800);
    last = (await sent(page)).pop();
    eq(last.vol, 'apply', 'the one-tap price limit is recorded');
    await ctx.close();
  }

  // ---- 8. An old account is never measured -----------------------------------------------------------------------
  {
    const { page, ctx } = await open({ grant: 'granted' }, 'plan=free&hunts=0&boot=1');
    eq(await page.evaluate(() => typeof window.SNYPD.fs), 'undefined', 'no tracker for an account older than 7 days');
    await page.type('#wiz-q-words', 'nike dunk low');
    await page.click('#wiz-q-save'); await wait(1500);
    ok(await vis(page, '#wiz-step-mode'), 'the wizard still works without the tracker');
    await wait(3600);
    eq((await sent(page)).length, 0, 'nothing is written for an old account');
    await ctx.close();
  }

  // ---- 9. A record that started 8 days ago is closed, even on a fresh-looking account ----------------------------
  {
    const closed = { v: 1, t0: new Date(Date.now() - 8 * 86400000).toISOString(), dev: 'desktop', devs: ['desktop'], wz: 1 };
    const { page, ctx } = await open({ grant: 'granted' }, 'plan=free&trial=1&boot=1&joined=fresh&meta=' + encodeURIComponent(JSON.stringify({ fs: closed, marketing_opt_in: false })));
    await wait(4200);
    eq((await sent(page)).length, 0, 'a closed record is not written again');
    await ctx.close();
  }

  // ---- 10. Writes fail: the page carries on and nothing breaks ---------------------------------------------------
  {
    const { page, ctx } = await open({ grant: 'granted' }, NEW + '&update_fail=1');
    await wizard(page, { words: 'nike dunk low', max: 30, clearMin: true, later: false });
    ok(!(await vis(page, '#wiz-overlay')), 'the wizard finished although every write failed');
    ok((await page.evaluate(() => window.__qa_auth_updates.length)) <= 8, 'a failing write is not retried in a loop');
    await ctx.close();
  }

  // ---- 11. The module file is missing: the dashboard is unaffected ------------------------------------------------
  {
    dropModule = true;
    const { page, ctx } = await open({ grant: 'granted' }, NEW);
    dropModule = false;
    eq(await page.evaluate(() => typeof window.SNYPD.fs), 'undefined');
    await page.type('#wiz-q-words', 'nike dunk low');
    await page.click('#wiz-q-save'); await wait(1500);
    ok(await vis(page, '#wiz-step-mode'), 'saving the first hunt works without the module');
    await ctx.close();
  }

  await browser.close(); server.close();
  eq(errors, [], 'no page error in any scenario');
  // The module and the injected block stay pure ASCII (dashboard.html carries a BOM).
  ok(!/[^\x00-\x7e]/.test(fs.readFileSync(path.join(root, 'assets/first-session.js'), 'utf8')), 'first-session.js is pure ASCII');
  const html = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8');
  const a = html.indexOf('(function firstSessionMeasure() {'), b = html.indexOf("SNYPD first-session measure', e); }", a);
  ok(a > 0 && b > a && !/[^\x00-\x7e]/.test(html.slice(a, b)), 'the block added to dashboard.html is pure ASCII');
  console.log(`PASS: ${passed} first-session browser checks.`);
})().catch(e => { console.error(e); process.exit(1); });
