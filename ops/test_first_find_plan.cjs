/*
 * Plan card at the first real find, on the REAL dashboard.html (17 Nov 2026).
 *   node ops/test_first_find_plan.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * dashboard.html in headless Chrome with ops/qa_mock.js. No production request.
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

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp, ctx) {
    ctx = ctx || await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') ? r.continue() : r.abort()));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(3000);
    return { page, ctx };
  }
  const vis = (p, sel) => p.$eval(sel, e => !e.hidden && e.getClientRects().length > 0).catch(() => false);
  const card = p => p.evaluate(() => {
    const b = document.getElementById('first-find-plan');
    const a = [...b.querySelectorAll('a.btn')].map(x => [x.getAttribute('data-ffp'), x.classList.contains('btn-prim'), x.getAttribute('href')]);
    return { lead: b.getAttribute('data-lead'), buttons: a, text: b.innerText };
  });
  const TRIAL = 'plan=free&trial=1';

  // ---- 1. UK and US first hunts: Solo leads, Hunt Pass second ----
  for (const site of ['co.uk', 'com']) {
    const { page, ctx } = await open(TRIAL + '&tfound=3&firstsite=' + site);
    ok(await vis(page, '#first-find-plan'), 'card shown during a running trial with finds (vinted.' + site + ')');
    const c = await card(page);
    eq(c.lead, 'solo', 'Solo leads on vinted.' + site);
    eq(c.buttons, [['solo', true, '/plans?checkout=solo'], ['pass', false, '/plans?checkout=pass']], 'Solo is the main button, the Pass the second');
    ok(/5\.99/.test(c.text) && /3\.99/.test(c.text), 'both prices shown: ' + c.text.replace(/\s+/g, ' '));
    ok(await vis(page, '#trial-value'), 'the "your hunt has matched" line is above it');
    await ctx.close();
  }

  // ---- 2. Every other site: Hunt Pass leads ----
  for (const site of ['', 'fr', 'de']) {
    const { page, ctx } = await open(TRIAL + '&tfound=1' + (site ? '&firstsite=' + site : ''));
    ok(await vis(page, '#first-find-plan'), 'card shown with one find (' + (site || 'be') + ')');
    const c = await card(page);
    eq(c.lead, 'pass', 'Hunt Pass leads on vinted.' + (site || 'be'));
    eq(c.buttons, [['pass', true, '/plans?checkout=pass'], ['solo', false, '/plans?checkout=solo']], 'Pass is the main button, Solo the second');
    ok(/no subscription/i.test(c.text), 'says paid once, no subscription');
    await ctx.close();
  }

  // ---- 3. When it must stay hidden ----
  for (const [q, why] of [
    [TRIAL + '&tfound=0', 'no find yet'],
    [TRIAL, 'trial statistics not available'],
    ['plan=free&trial=ending&tfound=5', 'last 24 h of the trial (the trial-end summary has that slot)'],
    ['plan=free&trial=ended&tfound=5', 'trial ended'],
    ['plan=free&tfound=5', 'no trial'],
    ['plan=elite&tfound=5&trial=1', 'paid plan'],
    ['plan=solo&active=1&tfound=5&trial=1', 'Solo plan'],
  ]) {
    const { page, ctx } = await open(q);
    ok(!(await vis(page, '#first-find-plan')), 'hidden: ' + why);
    await ctx.close();
  }

  // ---- 4. "Not now" hides it and it stays hidden on this device ----
  {
    const { page, ctx } = await open(TRIAL + '&tfound=3&firstsite=co.uk');
    ok(await vis(page, '#first-find-plan-no'), '"Not now" offered');
    const prims = () => page.$$eval('#elite-banner a.btn-prim', l => l.filter(e => e.getClientRects().length > 0).map(e => e.getAttribute('href')));
    eq(await prims(), ['/plans?checkout=solo'], 'one main button while the card shows ("See plans" is quiet)');
    await page.click('#first-find-plan-no'); await wait(300);
    ok(!(await vis(page, '#first-find-plan')), 'hidden after "Not now"');
    eq(await prims(), ['/plans'], '"See plans" is the main button again');
    ok(await vis(page, '#elite-banner'), 'the trial banner itself stays');
    await page.close();
    const again = await open(TRIAL + '&tfound=3&firstsite=co.uk', null, ctx);
    ok(!(await vis(again.page, '#first-find-plan')), 'still hidden on the next visit');
    await ctx.close();
  }

  // ---- 5. A plan picked at sign-up keeps its own prompt: no second card ----
  {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) ? r.continue() : r.abort()));
    // The sign-up plan prompt sets this flag when it paints; set before the page's own code runs.
    await page.evaluateOnNewDocument(() => { window.SNYPD_PLAN_PROMPT = true; });
    await page.goto(base + '/dashboard.html?' + TRIAL + '&tfound=3', { waitUntil: 'domcontentloaded' });
    await wait(3000);
    ok(await page.evaluate(() => window.SNYPD_PLAN_PROMPT === true), 'the flag survived page start-up');
    ok(await vis(page, '#trial-value'), 'the matched-listings line is still shown');
    ok(!(await vis(page, '#first-find-plan')), 'hidden while the sign-up plan prompt is showing');
    await ctx.close();
  }

  // ---- 6. Phone width and French ----
  {
    const { page, ctx } = await open(TRIAL + '&tfound=3&firstsite=co.uk', { width: 390, height: 844, isMobile: true, hasTouch: true });
    ok(await vis(page, '#first-find-plan'), 'shown at 390 px');
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'no sideways overflow at 390 px');
    const sizes = await page.$$eval('#first-find-plan a.btn, #first-find-plan button', l => l.map(e => Math.round(e.getBoundingClientRect().right)));
    ok(sizes.every(r => r <= 390), 'every button inside the screen: ' + JSON.stringify(sizes));
    await ctx.close();
  }
  for (const site of ['fr', 'co.uk']) {
    const { page, ctx } = await open(TRIAL + '&tfound=3&lang=fr&firstsite=' + site, { width: 390, height: 844, isMobile: true, hasTouch: true });
    ok(await vis(page, '#first-find-plan'), 'shown in French (' + site + ')');
    const t = (await card(page)).text;
    const left = t.match(/Keep this hunt|Hunt Pass runs|Solo keeps|Not now|month by month|paid once|a month\b|\bonce\b/gi);
    eq(left, null, 'no English left in the French card: ' + JSON.stringify(left) + ' in: ' + t.replace(/\s+/g, ' '));
    ok(/5,99/.test(t) && /3,99/.test(t), 'French prices: ' + t.replace(/\s+/g, ' '));
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'no sideways overflow in French');
    await ctx.close();
  }

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' first-find plan card checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks:', e.message); process.exit(1); });
