/*
 * Cookie banner (assets/consent.js): compact on phones (11 Nov 2026), unchanged behaviour.
 *   node ops/test_cookie_banner.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Serves the repo's own files; every request to another host is recorded and blocked, so nothing reaches
 * production and "nothing loads before consent" can be checked from the request log.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(root, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(root, p + '.html');
  if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f)) { res.writeHead(404); return res.end('nope'); }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(fs.readFileSync(f));
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const TRACKERS = /googletagmanager\.com|google-analytics\.com|connect\.facebook\.net|facebook\.com\/tr|whop\.com/;
const SHORT = 'We only store what keeps you signed in. With your OK we also measure visits and sign-ups (Google, Whop, Meta).';
const PHONE_MAX = 170;      // px at 390 wide, English (it was about 260)
const PHONE_MAX_FR = 190;   // French runs one line longer

(async () => {
  const src = fs.readFileSync(path.join(root, 'assets', 'consent.js'), 'utf8');
  ok(!/[^\x00-\x7F]/.test(src), 'consent.js stays pure ASCII');

  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(url, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp);
    page.on('pageerror', e => errors.push(url + ': ' + e.message));
    page.__outside = [];
    await page.setRequestInterception(true);
    page.on('request', r => {
      const u = r.url();
      if (u.startsWith(base) || u.startsWith('data:')) return r.continue();
      page.__outside.push(u);
      return r.abort();
    });
    await page.goto(base + url, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.snc-bar', { timeout: 6000 });
    await wait(400);
    return { page, ctx };
  }
  const bar = page => page.evaluate(() => {
    const b = document.querySelector('.snc-bar'), r = b.getBoundingClientRect();
    const box = s => { const e = b.querySelector(s), q = e.getBoundingClientRect(), c = getComputedStyle(e); return { w: Math.round(q.width), h: Math.round(q.height), top: Math.round(q.top), right: q.right, left: q.left, color: c.color, bg: c.backgroundColor, border: c.borderTopColor, size: c.fontSize, weight: c.fontWeight, text: e.textContent.trim() }; };
    const shown = s => { const e = b.querySelector(s); return !!e && getComputedStyle(e).display !== 'none'; };
    return { h: Math.round(r.height), bottom: Math.round(r.bottom), vh: innerHeight, vw: innerWidth, sw: document.documentElement.scrollWidth,
      reject: box('[data-snc="reject"]'), accept: box('[data-snc="accept"]'), settings: box('[data-snc="settings"]'),
      long: shown('.snc-long'), short: shown('.snc-short'), shortText: (b.querySelector('.snc-short') || {}).textContent,
      policy: (b.querySelector('a[href="/cookies"]') || {}).textContent, pad: parseFloat(document.body.style.paddingBottom) || 0 };
  });
  const sameLook = (a, b) => a.w === b.w && a.h === b.h && a.color === b.color && a.bg === b.bg && a.border === b.border && a.size === b.size && a.weight === b.weight;

  // ---- phone, English: three pages ------------------------------------------------------------------------
  for (const url of ['/', '/signup', '/plans']) {
    const { page, ctx } = await open(url, { width: 390, height: 844 });
    const b = await bar(page);
    ok(b.h <= PHONE_MAX, url + ' 390: bar is ' + b.h + ' px, at most ' + PHONE_MAX);
    ok(b.bottom === b.vh, url + ' 390: bar sits at the bottom edge');
    ok(b.short && !b.long, url + ' 390: the short sentence is the one shown');
    eq(b.shortText, SHORT, url + ' 390: short sentence text');
    eq(b.policy, 'Cookie policy', url + ' 390: cookie policy link is there');
    ok(sameLook(b.reject, b.accept), url + ' 390: Reject and Accept have the same size and style ' + JSON.stringify([b.reject, b.accept]));
    ok(b.reject.h >= 44 && b.settings.h >= 36, url + ' 390: tap heights');
    ok(b.reject.top === b.accept.top && b.settings.top <= b.reject.top + b.reject.h, url + ' 390: one row of choices');
    ok(b.sw <= b.vw, url + ' 390: no sideways scroll');
    ok(b.settings.right <= b.vw && b.reject.left >= 0, url + ' 390: nothing cut off');
    ok(Math.abs(b.pad - b.h) <= 1, url + ' 390: the page keeps room for the bar (' + b.pad + ' vs ' + b.h + ')');
    eq(page.__outside.filter(u => TRACKERS.test(u)), [], url + ': nothing from Google, Meta or Whop is requested before a choice');
    await ctx.close();
  }

  // ---- narrow phones --------------------------------------------------------------------------------------
  for (const w of [320, 360, 375]) {
    const { page, ctx } = await open('/', { width: w, height: w === 320 ? 568 : 700 });
    const b = await bar(page);
    ok(sameLook(b.reject, b.accept), w + ': Reject and Accept equal');
    ok(b.sw <= b.vw && b.settings.right <= b.vw + 0.5, w + ': fits the screen');
    ok(b.reject.top === b.accept.top && Math.abs((b.settings.top + b.settings.h / 2) - (b.reject.top + b.reject.h / 2)) <= 2, w + ': Settings sits on the button row');
    ok(b.reject.h >= 44 && b.settings.h >= 44, w + ': tap heights ' + b.reject.h + ' / ' + b.settings.h);
    ok(b.h <= PHONE_MAX, w + ': height ' + b.h + ', at most ' + PHONE_MAX);
    await ctx.close();
  }

  // ---- phone, French --------------------------------------------------------------------------------------
  for (const w of [390, 360, 320]) {
    const { page, ctx } = await open('/fr/bot-vinted', { width: w, height: 844 });
    await wait(500);
    const b = await bar(page);
    if (w === 390) {
      ok(/^On n.enregistre que ce qu.il faut/.test(b.shortText), 'French short sentence is shown: ' + b.shortText);
      eq([b.reject.text, b.accept.text], ['TOUT REFUSER', 'TOUT ACCEPTER'], 'French buttons');
      ok(b.h <= PHONE_MAX_FR, 'French 390: bar is ' + b.h + ' px, at most ' + PHONE_MAX_FR);
    }
    ok(sameLook(b.reject, b.accept), 'French ' + w + ': Reject and Accept equal ' + JSON.stringify([b.reject.w, b.accept.w]));
    ok(Math.abs((b.settings.top + b.settings.h / 2) - (b.reject.top + b.reject.h / 2)) <= 2, 'French ' + w + ': Settings sits on the button row');
    ok(b.h <= PHONE_MAX_FR, 'French ' + w + ': height ' + b.h + ', at most ' + PHONE_MAX_FR);
    ok(b.sw <= b.vw && b.settings.right <= b.vw + 0.5, 'French ' + w + ': fits the screen');
    await ctx.close();
  }

  // ---- wide screens are as before --------------------------------------------------------------------------
  for (const w of [820, 1440]) {
    const { page, ctx } = await open('/', { width: w, height: 900 });
    const b = await bar(page);
    ok(b.long && !b.short, w + ': the full sentence is shown');
    ok(sameLook(b.reject, b.accept), w + ': Reject and Accept equal');
    ok(b.reject.h >= 46, w + ': button height unchanged');
    await ctx.close();
  }

  // ---- wide screens, French: the two choices are the same size too (they were sized by their words) -----------
  for (const w of [820, 1440]) {
    const { page, ctx } = await open('/fr/bot-vinted', { width: w, height: 900 });
    await wait(500);
    const b = await bar(page);
    eq([b.reject.text, b.accept.text], ['TOUT REFUSER', 'TOUT ACCEPTER'], 'French ' + w + ': buttons are in French');
    ok(sameLook(b.reject, b.accept), 'French ' + w + ': Reject and Accept equal ' + JSON.stringify([b.reject.w, b.accept.w]));
    ok(b.sw <= b.vw, 'French ' + w + ': no sideways scroll');
    await ctx.close();
  }

  // ---- behaviour: reject, accept, settings ------------------------------------------------------------------
  {
    const { page, ctx } = await open('/', { width: 390, height: 844 });
    await page.click('.snc-bar [data-snc="reject"]');
    await wait(500);
    ok(!(await page.$('.snc-bar')), 'Reject closes the bar');
    const c = await page.evaluate(() => JSON.parse(localStorage.getItem('snypd_consent')));
    ok(c && c.analytics === false && c.marketing === false, 'Reject is stored as no analytics, no marketing: ' + JSON.stringify(c));
    eq(page.__outside.filter(u => TRACKERS.test(u)), [], 'after Reject nothing from Google, Meta or Whop is requested');
    eq(await page.evaluate(() => document.body.style.paddingBottom), '', 'page padding is given back');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('/', { width: 390, height: 844 });
    await page.click('.snc-bar [data-snc="accept"]');
    await wait(900);
    ok(!(await page.$('.snc-bar')), 'Accept closes the bar');
    const c = await page.evaluate(() => JSON.parse(localStorage.getItem('snypd_consent')));
    ok(c && c.analytics === true && c.marketing === true, 'Accept is stored as analytics + marketing');
    ok(page.__outside.some(u => /googletagmanager\.com/.test(u)), 'after Accept the Google tag is requested');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('/', { width: 390, height: 844 });
    await page.click('.snc-bar [data-snc="settings"]');
    await wait(300);
    ok(!!(await page.$('.snc-panel')), 'Settings opens the panel');
    eq(await page.$$eval('.snc-panel input[type=checkbox]', a => a.map(i => i.checked + ':' + i.disabled)), ['true:true', 'false:false', 'false:false'], 'panel: necessary locked on, the other two off');
    await page.keyboard.press('Escape');
    await wait(300);
    ok(!(await page.$('.snc-panel')) && !!(await page.$('.snc-bar')), 'Escape closes the panel and the bar stays (no choice made)');
    eq(await page.evaluate(() => localStorage.getItem('snypd_consent')), null, 'nothing stored without a choice');
    await ctx.close();
  }

  await browser.close();
  server.close();
  eq(errors, [], 'no page errors');
  console.log('cookie banner: ' + passed + ' checks passed');
})().catch(e => { console.error(e); process.exit(1); });
