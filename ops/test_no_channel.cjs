/*
 * Browser test for the "your finds are not reaching you" notice (21 Nov 2026): shown only to an account that is
 * checked 24/7, has an active search, has no push device anywhere and no Discord link.
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js (?devs=<n>|err = devices on the account).
 *   node ops/test_no_channel.cjs              (needs Google Chrome at CHROME_PATH or the default Windows path)
 *   SHOTS=<dir> node ops/test_no_channel.cjs  also writes screenshots
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
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
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
const wait = ms => new Promise(r => setTimeout(r, ms));
const PHONE = { width: 390, height: 664, isMobile: true, hasTouch: true };
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(10000);
    return page;
  }
  const state = page => page.evaluate(() => {
    const vis = el => !!el && el.offsetParent !== null && getComputedStyle(el).display !== 'none';
    const card = document.getElementById('no-channel-card');
    return {
      exists: !!card, shown: vis(card), setup: vis(document.getElementById('alerts-setup-card')),
      title: card ? card.querySelector('.elite-banner__title').textContent : '',
      buttons: card ? Array.from(card.querySelectorAll('button')).filter(vis).length : 0,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      wizard: (o => !!o && getComputedStyle(o).display !== 'none' && o.getBoundingClientRect().height > 0)(document.getElementById('wiz-overlay')),   // fixed overlay: offsetParent is null
      discordRow: vis(document.getElementById('prof-discord-row')),
      hide: Number(localStorage.getItem('snypd_no_channel_hide') || 0),
      statusCalls: window.__pushStatusCalls || 0,
    };
  });
  async function shownFor(q, vp) { const p = await open(q, vp); const s = await state(p); await p.close(); return s; }

  // 1. Shown: paying account, active search, no device anywhere, no Discord.
  let page = await open('plan=elite&devs=0');
  let s = await state(page);
  ok(s.exists && s.shown, 'paid account without any channel sees the notice');
  ok(/not reaching you/i.test(s.title), 'the notice says the finds are not reaching the user');
  ok(s.buttons === 3, 'three actions: alerts, Discord, hide for today');
  ok(!s.setup, 'the per-device alerts card steps aside while the notice shows');
  ok(s.overflow <= 0, 'no sideways overflow on desktop');
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'no-channel-desktop.png') });
  // "Turn on alerts" opens the existing alerts step.
  await page.click('#no-channel-alerts'); await wait(600);
  ok((await state(page)).wizard, 'Turn on alerts opens the alerts step');
  await page.close();

  // 2. "Use Discord" goes to the Discord row on the Profile screen.
  page = await open('plan=elite&devs=0');
  await page.click('#no-channel-discord'); await wait(1200);
  ok((await state(page)).discordRow, 'Use Discord shows the Discord row');
  await page.close();

  // 3. "Hide for today": hidden for 24 hours on this device, never longer; the per-device card returns.
  page = await open('plan=elite&devs=0');
  const before = Date.now();
  await page.click('#no-channel-later'); await wait(1500);
  s = await state(page);
  ok(!s.shown, 'Hide for today hides the notice');
  ok(s.hide > before + 23 * 3600000 && s.hide < before + 25 * 3600000, 'hidden for 24 hours, not longer');
  ok(s.setup, 'the per-device alerts card is back after hiding the notice');
  await page.reload({ waitUntil: 'domcontentloaded' }); await wait(10000);
  ok(!(await state(page)).shown, 'still hidden after a reload within the day');
  await page.evaluate(() => localStorage.setItem('snypd_no_channel_hide', String(Date.now() - 1000)));
  await page.reload({ waitUntil: 'domcontentloaded' }); await wait(10000);
  ok((await state(page)).shown, 'back once the 24 hours are over');
  await page.close();

  // 4. Hidden whenever the account has a channel, or anything is unknown.
  ok(!(await shownFor('plan=elite&devs=2')).shown, 'an account with devices never sees it');
  ok(!(await shownFor('plan=elite&devs=1')).shown, 'one device elsewhere on the account is enough');
  ok(!(await shownFor('plan=elite&devs=0&dc=linked')).shown, 'a Discord link is a channel');
  ok(!(await shownFor('plan=elite&devs=err')).shown, 'a failed status call keeps it hidden');
  ok(!(await shownFor('plan=elite&devs=flaky')).shown, 'one wrong "no devices" answer is not enough: it asks twice');
  s = await shownFor('plan=elite');
  ok(!s.shown, 'a status answer without a device list keeps it hidden');
  ok(s.setup, 'and the per-device card behaves as before');
  ok(!(await shownFor('plan=elite&devs=0&hunts=0')).shown, 'no search, no notice');

  // 5. Who is checked 24/7: paid plans and running trials, not Free after the trial.
  ok((await shownFor('plan=solo&active=1&devs=0')).shown, 'Solo without a channel sees it');
  ok((await shownFor('plan=free&trial=1&devs=0')).shown, 'a running trial without a channel sees it');
  s = await shownFor('plan=free&trial=ended&devs=0');
  ok(!s.shown, 'Free after the trial does not (its searches only run while the dashboard is open)');
  ok(s.statusCalls <= 1, 'and no extra status call is made for it (got ' + s.statusCalls + ')');
  ok(!(await shownFor('plan=free&devs=0')).shown, 'Free without a trial does not');

  // 6. Phone.
  page = await open('plan=free&trial=1&devs=0', PHONE);
  s = await state(page);
  ok(s.shown && s.overflow <= 0, 'phone: shown, no sideways overflow');
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'no-channel-phone.png') });
  await page.close();

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' no-channel browser checks.');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
