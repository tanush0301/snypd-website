/*
 * First-session v2, alerts choice (20 Nov 2026): the REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_alert_choice.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * On an iPhone in Safari (no Home Screen app) with Discord available and not linked, the alerts step shows two equal
 * choices, "On this iPhone" and "In Discord"; the main button follows the choice. Everywhere else the step is unchanged.
 * No network: the mock answers every call (?dc=linked | off, Discord calls counted in window.__dcCalls).
 * SHOTS=<dir> saves screenshots.
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
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36';
const NEW = 'plan=free&hunts=0&boot=1&joined=fresh';

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(ua, q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 390, height: 664, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
    await page.setUserAgent(ua);
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') ? r.continue() : r.abort()));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(2500);
    return { page, ctx };
  }
  const vis = (p, sel) => p.$eval(sel, e => !e.hidden && e.style.display !== 'none' && e.getClientRects().length > 0).catch(() => false);
  const tc = (p, sel) => p.$eval(sel, e => e.textContent.replace(/\s+/g, ' ').trim()).catch(() => '');
  const shot = async (p, name) => { if (SHOTS) await p.screenshot({ path: path.join(SHOTS, name + '.png') }); };
  async function toAlertsStep(page) {
    await page.type('#wiz-q-words', 'nike tech');
    await page.type('#wiz-q-max', '40');
    await page.click('#wiz-q-save'); await wait(1800);
    ok(await vis(page, '#wiz-step-2'), 'alerts step shown');
  }

  // ---- 1. iPhone Safari, Discord available: two equal choices, iPhone preselected
  {
    const { page, ctx } = await open(IPHONE, NEW);
    await toAlertsStep(page);
    ok(await vis(page, '#wiz-alert-choice'), 'the two choices are shown on an iPhone in Safari');
    ok(!(await vis(page, '#wiz-alert-rows')), 'the switch rows are hidden there');
    eq(await page.$$eval('#wiz-alert-choice [data-alert-choice]', bs => bs.map(b => b.dataset.alertChoice + ':' + b.getAttribute('aria-checked'))), ['iphone:true', 'discord:false'], 'iPhone is preselected');
    const sizes = await page.$$eval('#wiz-alert-choice [data-alert-choice]', bs => bs.map(b => Math.round(b.getBoundingClientRect().width)));
    eq(sizes[0], sizes[1], 'both choices are the same width');
    ok(/show me how/i.test(await tc(page, '#wiz-enable-alerts')), 'main button for the iPhone choice: ' + await tc(page, '#wiz-enable-alerts'));
    const b = await page.$eval('#wiz-enable-alerts', e => Math.round(e.getBoundingClientRect().bottom));
    ok(b <= 664, 'the main button is on the first phone screen: ' + b);
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'no sideways scroll');
    await shot(page, 'alert-choice-iphone');
    await page.click('#wiz-enable-alerts'); await wait(1500);
    ok(await vis(page, '#ios-guide'), 'the iPhone choice opens the drawn Home Screen guide');
    eq(await page.evaluate(() => (window.__dcCalls || []).filter(c => /discord\/code/.test(c)).length), 0, 'no Discord code requested for the iPhone choice');
    await ctx.close();
  }

  // ---- 2. iPhone Safari: picking Discord changes the button and starts the Discord link
  {
    const { page, ctx } = await open(IPHONE, NEW);
    await toAlertsStep(page);
    await page.click('#wiz-alert-choice [data-alert-choice="discord"]'); await wait(300);
    eq(await page.$$eval('#wiz-alert-choice [data-alert-choice]', bs => bs.map(b => b.getAttribute('aria-checked'))), ['false', 'true'], 'Discord is selected after a tap');
    ok(/connect discord/i.test(await tc(page, '#wiz-enable-alerts')), 'main button for the Discord choice: ' + await tc(page, '#wiz-enable-alerts'));
    await shot(page, 'alert-choice-discord');
    await page.click('#wiz-enable-alerts'); await wait(1800);
    ok(!(await vis(page, '#ios-guide')), 'no iPhone guide for the Discord choice');
    ok(!(await vis(page, '#wiz-overlay')), 'the wizard closes');
    ok(await page.evaluate(() => (window.__dcCalls || []).some(c => /discord\/code/.test(c))), 'a Discord link code is requested');
    ok(/QA7K2M/.test(await page.evaluate(() => document.body.innerText)), 'the code is shown on the page');
    await page.click('#wiz-alert-choice [data-alert-choice="iphone"]').catch(() => {});
    await ctx.close();
  }

  // ---- 3. Android: unchanged step
  {
    const { page, ctx } = await open(ANDROID, NEW);
    await toAlertsStep(page);
    ok(!(await vis(page, '#wiz-alert-choice')), 'no choice cards on Android');
    ok(await vis(page, '#wiz-alert-rows'), 'the switch rows stay on Android');
    ok(/turn on alerts/i.test(await tc(page, '#wiz-enable-alerts')), 'main button unchanged on Android: ' + await tc(page, '#wiz-enable-alerts'));
    await ctx.close();
  }

  // ---- 4. iPhone Safari, Discord already linked: nothing to choose
  {
    const { page, ctx } = await open(IPHONE, NEW + '&dc=linked');
    await toAlertsStep(page);
    ok(!(await vis(page, '#wiz-alert-choice')), 'no choice cards when Discord is already linked');
    ok(await vis(page, '#wiz-alert-rows'), 'the switch rows show the linked state');
    ok(/turn on alerts/i.test(await tc(page, '#wiz-enable-alerts')), 'main button unchanged when linked');
    await ctx.close();
  }

  // ---- 5. iPhone Safari, Discord switched off on the server: still offered (the page only learns it on the tap),
  //         and the tap answers honestly with no code, as the Discord row always did
  {
    const { page, ctx } = await open(IPHONE, NEW + '&dc=off');
    await toAlertsStep(page);
    ok(await vis(page, '#wiz-alert-choice'), 'off: the choice is still offered');
    await page.click('#wiz-alert-choice [data-alert-choice="discord"]'); await wait(300);
    await page.click('#wiz-enable-alerts'); await wait(1500);
    const body = await page.evaluate(() => document.body.innerText);
    ok(/Discord alerts are not available right now\./.test(body), 'off: the page says Discord alerts are not available');
    ok(!/QA7K2M/.test(body), 'off: no code shown');
    eq(await page.evaluate(() => (window.__dcCalls || []).filter(c => /discord\/code/.test(c)).length), 1, 'off: one code request, refused');
    await ctx.close();
  }

  // ---- 6. French
  {
    const { page, ctx } = await open(IPHONE, NEW + '&lang=fr');
    await toAlertsStep(page);
    const txt = await tc(page, '#wiz-alert-choice');
    ok(/Sur cet iPhone/.test(txt) && /Dans Discord/.test(txt) && !/On this iPhone|Home Screen/.test(txt), 'choice cards in French: ' + txt.slice(0, 120));
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'no sideways scroll in French');
    await shot(page, 'alert-choice-iphone-fr');
    await ctx.close();
  }

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' alert-choice checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks: ' + (e && e.message)); process.exit(1); });
