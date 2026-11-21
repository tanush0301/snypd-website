/*
 * Auth pages on small phones (21 Nov 2026): the submit button sits above the cookie bar on a first visit.
 *   node ops/test_auth_small_phone.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Serves the repo's own files; every request to another host is blocked, so nothing reaches production.
 * Sizes are what a phone browser really shows (address bar taken off the screen height).
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
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
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
const wait = ms => new Promise(r => setTimeout(r, ms));
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const SIZES = [[320, 568], [339, 600], [340, 600], [360, 640], [375, 553], [389, 664], [390, 664]];
const PAGES = ['/signup', '/signup?lang=fr', '/login', '/login?lang=fr'];

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  for (const [w, h] of SIZES) for (const u of PAGES) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setUserAgent(IPHONE);
    await page.setViewport({ width: w, height: h, isMobile: true, hasTouch: true });
    page.on('pageerror', e => errors.push(u + ': ' + e.message));
    await page.setRequestInterception(true);
    // The sign-in library is the one outside file allowed: without it the page shows a "Couldn't reach SNYPD" notice
    // that a real visitor does not see, and that notice changes the layout being measured.
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') || /^https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@/.test(r.url()) ? r.continue() : r.abort()));
    await page.goto(base + u, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.snc-bar', { timeout: 6000 });
    await page.waitForSelector('#au-form button[type=submit]', { timeout: 6000 });
    await wait(500);
    const m = await page.evaluate(() => {
      const s = [...document.querySelectorAll('#au-form button[type=submit]')].find(e => e.getClientRects().length);
      const g = document.querySelector('#au-form button[data-act="google"]');
      return { submit: Math.round(s.getBoundingClientRect().bottom), bar: Math.round(document.querySelector('.snc-bar').getBoundingClientRect().top),
        google: g ? Math.round(g.getBoundingClientRect().height) : 0, h1: document.querySelector('#au-form h1').textContent,
        over: document.documentElement.scrollWidth > window.innerWidth };
    });
    const tag = w + 'x' + h + ' ' + u;
    ok(m.submit <= m.bar, tag + ': the submit button is above the cookie bar (' + m.submit + ' vs ' + m.bar + ')');
    ok(!m.over, tag + ': no sideways scroll');
    ok(m.google >= 44, tag + ': the Google button keeps a 44 px tap height (' + m.google + ')');
    if (/lang=fr/.test(u)) ok(/Commence|Se connecter/.test(m.h1), tag + ': the page is in French (' + m.h1 + ')');
    if (SHOTS && w === 320) await page.screenshot({ path: path.join(SHOTS, 'auth-320' + u.replace(/[^a-z]+/gi, '_') + '.png') });
    await ctx.close();
  }
  assert.deepEqual(errors, [], 'no page errors'); passed++;
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' small-phone auth checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks: ' + (e && e.message)); process.exit(1); });
