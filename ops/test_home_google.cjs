/*
 * Homepage "Continue with Google" (24 Nov 2026).   node ops/test_home_google.cjs
 * Serves the repo's own files; every other host is blocked except the sign-in library. The request that would leave
 * for Google (the sign-in service's /auth/v1/authorize address) is recorded and stopped: no sign-in is ever made.
 * Checks: the button is a real link that carries the typed search; hidden inside in-app browsers; phone layout;
 * /signup?with=google starts Google once per tab for a signed-out visitor, not on a reload, not inside an in-app
 * browser, and never without the marker; the typed search is stored for the first-search form.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4' };
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
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const INSTA = IPHONE + ' Instagram 300.0.0.0';

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(url, opts) {
    opts = opts || {};
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    if (opts.ua) await page.setUserAgent(opts.ua);
    await page.setViewport(opts.vp || { width: 1440, height: 900 });
    page.on('pageerror', e => errors.push(url + ': ' + e.message));
    const oauth = [];
    await page.setRequestInterception(true);
    page.on('request', r => {
      const u = r.url();
      // 204 = "no content": the browser stays on the page, so nothing ever reaches Google
      if (/\/auth\/v1\/authorize/.test(u)) { oauth.push(u); return r.respond({ status: 204, body: '' }); }
      return (u.startsWith(base) || u.startsWith('data:') || /^https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@/.test(u)) ? r.continue() : r.abort();
    });
    await page.goto(base + url, { waitUntil: 'domcontentloaded' });
    return { page, ctx, oauth };
  }

  // ---- homepage, desktop -----------------------------------------------------------------------------------
  {
    const { page, ctx } = await open('/');
    await wait(900);
    const b = await page.$eval('#qs-google', a => ({ tag: a.tagName, href: a.getAttribute('href'), text: a.textContent.replace(/\s+/g, ' ').trim(), svg: !!a.querySelector('svg'), h: Math.round(a.getBoundingClientRect().height), shown: getComputedStyle(a).display !== 'none' }));
    eq([b.tag, b.href, b.text, b.svg, b.shown], ['A', '/signup?with=google', 'CONTINUE WITH GOOGLE', true, true], 'the button is a real link to sign-up with the Google marker');
    ok(b.h >= 44, 'the button is at least 44 px tall (' + b.h + ')');
    const edges = await page.evaluate(() => { const r = i => document.getElementById(i).getBoundingClientRect(); return [Math.round(r('qs-google').left), Math.round(r('qs-google').right), Math.round(r('qs').left), Math.round(r('qs').right)]; });
    ok(edges[0] === edges[2] && edges[1] === edges[3], 'the button is exactly as wide as the search box (' + edges + ')');
    await page.type('#qs-words', 'nike tech fleece');
    await page.type('#qs-max', '40');
    eq(await page.$eval('#qs-google', a => a.getAttribute('href')), '/signup?with=google&hunt=nike+tech+fleece&max=40', 'the typed words and price ride on the Google link');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup?hunt=nike+tech+fleece&max=40', 'the main button is unchanged');
    const order = await page.evaluate(() => { const r = id => document.getElementById(id).getBoundingClientRect(); return [Math.round(r('qs-go').bottom), Math.round(r('qs-google').top), Math.round(r('qs-google').bottom), Math.round(r('hero-trial').top), innerHeight, document.documentElement.scrollWidth <= innerWidth + 1]; });
    ok(order[1] >= order[0] && order[3] >= order[2], 'desktop: main button, then Google, then the trial line');
    ok(order[2] <= order[4] && order[5], 'desktop: the Google button is in the first screen, no sideways scroll');
    await ctx.close();
  }
  // ---- homepage, phones ------------------------------------------------------------------------------------
  for (const [w, h] of [[390, 664], [390, 844], [320, 568]]) {
    const { page, ctx } = await open('/', { ua: IPHONE, vp: { width: w, height: h, isMobile: true, hasTouch: true } });
    await page.waitForSelector('.snc-bar', { timeout: 8000 }); await wait(500);
    const m = await page.evaluate(() => { const r = s => document.querySelector(s).getBoundingClientRect(); return { go: Math.round(r('#qs-go').bottom), gTop: Math.round(r('#qs-google').top), gBot: Math.round(r('#qs-google').bottom), gH: Math.round(r('#qs-google').height), vid: Math.round(r('#vid-el').top), bar: Math.round(r('.snc-bar').top), over: document.documentElement.scrollWidth > innerWidth + 1, inCard: !!document.querySelector('.hp-hero-card #watch') }; });
    const name = 'phone ' + w + 'x' + h + ': ';
    ok(m.go <= m.bar, name + 'the main button stays above the cookie bar (' + m.go + ' of ' + m.bar + ')');
    ok(m.gTop >= m.go && m.gH >= 44, name + 'the Google button sits under the main button and is 44 px or taller (' + m.gH + ')');
    ok(m.inCard && m.vid >= m.gBot, name + 'the video sits under the Google button');
    ok(!m.over, name + 'no sideways scroll');
    await ctx.close();
  }
  // ---- homepage inside an in-app browser: no Google button -----------------------------------------------
  {
    const { page, ctx } = await open('/', { ua: INSTA, vp: { width: 390, height: 844, isMobile: true, hasTouch: true } });
    await wait(900);
    ok(await page.$eval('#qs-google', a => a.hidden && getComputedStyle(a).display === 'none'), 'inside Instagram the Google button is hidden');
    ok(await page.$eval('.hp-hero-card #watch #vid-el', v => !!v), 'inside Instagram the video still sits in the first card');
    await ctx.close();
  }

  // ---- sign-up page: the marker starts Google once -------------------------------------------------------
  {
    const { page, ctx, oauth } = await open('/signup?with=google&hunt=nike+tech+fleece&max=40&utm_source=test');
    await page.waitForSelector('#au-form', { timeout: 8000 });
    for (let i = 0; i < 40 && !oauth.length; i++) await wait(150);
    eq(oauth.length, 1, 'a signed-out visitor with the marker is sent to Google once');
    const u = new URL(oauth[0]);
    eq(u.searchParams.get('provider'), 'google', 'the provider is Google');
    const back = new URL(u.searchParams.get('redirect_to'));
    ok(back.pathname === '/login' && back.searchParams.get('utm_source') === 'test', 'Google returns to /login with the campaign tag (' + back.pathname + back.search + ')');
    const intent = await page.evaluate(() => JSON.parse(localStorage.getItem('snypd_hunt_intent') || 'null'));
    eq([intent && intent.q, intent && intent.max], ['nike tech fleece', 40], 'the typed search is stored for the first-search form');
    // the Back button from Google reloads this page in the same tab: the form shows, no second trip
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 8000 }); await wait(1500);
    eq(oauth.length, 1, 'a reload in the same tab does not start Google again');
    ok(await page.$eval('#au-form [data-act="google"]', b => !b.disabled), 'after the reload the form shows with its own Google button usable');
    await ctx.close();
  }
  // ---- sign-up page without the marker: nothing starts ---------------------------------------------------
  {
    const { page, ctx, oauth } = await open('/signup?hunt=nike+tech+fleece');
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 8000 }); await wait(1500);
    eq(oauth.length, 0, 'without the marker the sign-up page never starts Google by itself');
    await ctx.close();
  }
  // ---- login page with the marker: nothing starts --------------------------------------------------------
  {
    const { page, ctx, oauth } = await open('/login?with=google');
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 8000 }); await wait(1500);
    eq(oauth.length, 0, 'the marker does nothing on the login page');
    await ctx.close();
  }
  // ---- sign-up page inside an in-app browser: nothing starts, the note shows ------------------------------
  {
    const { page, ctx, oauth } = await open('/signup?with=google', { ua: INSTA, vp: { width: 390, height: 844, isMobile: true, hasTouch: true } });
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 8000 }); await wait(1500);
    eq(oauth.length, 0, 'inside Instagram the marker does not start Google');
    ok(/Google sign-in does not work here/.test(await page.$eval('#au-form', f => f.textContent)), 'inside Instagram the form explains that Google does not work there');
    await ctx.close();
  }

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' homepage Google button checks.');
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
