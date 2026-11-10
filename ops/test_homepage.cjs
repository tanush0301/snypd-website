/*
 * Homepage v6 (outreach/54): the hero search box, the plan links, layout at phone and desktop width.
 *   node ops/test_homepage.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Serves the repo's own files; every request to another host is blocked, so nothing reaches production.
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

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1440, height: 900 });
    page.on('pageerror', e => errors.push((q || '/') + ': ' + e.message));
    await page.setRequestInterception(true);
    // Stay on the homepage: a navigation to /signup is recorded and stopped, other hosts are blocked.
    page.__went = null;
    page.on('request', r => {
      const u = r.url();
      if (r.isNavigationRequest() && r.frame() === page.mainFrame() && /\/signup(\?|$)/.test(u)) { page.__went = u.slice(base.length); return r.abort(); }
      return u.startsWith(base) || u.startsWith('data:') ? r.continue() : r.abort();
    });
    await page.goto(base + '/' + (q || ''), { waitUntil: 'domcontentloaded' });
    await wait(900);
    return { page, ctx };
  }
  const went = async page => { for (let i = 0; i < 30 && !page.__went; i++) await wait(100); const u = page.__went; page.__went = null; return u ? new URL(u, base) : null; };
  const params = u => Object.fromEntries(u.searchParams.entries());

  // ---- the search box -------------------------------------------------------------------------------------
  {
    const { page, ctx } = await open('');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup', 'with nothing typed the button is a plain sign-up link');
    await page.type('#qs-words', '  ralph   lauren jumper ');
    await page.type('#qs-max', '25');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup?hunt=ralph+lauren+jumper&max=25', 'words are tidied and carried with the price limit');
    await page.click('#qs-go');
    let u = await went(page);
    ok(u, 'the button goes to sign-up');
    eq(params(u), { hunt: 'ralph lauren jumper', max: '25', from: 'home', entry_basis: 'nav-v1' }, 'sign-up gets the search and the entry-page tag');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('?utm_source=chatgpt.com&r=abcd23');
    await page.type('#qs-words', 'amazon kindle');
    await page.keyboard.press('Enter');
    const u = await went(page);
    ok(u, 'Enter in the box goes to sign-up');
    eq(params(u), { hunt: 'amazon kindle', r: 'abcd23', utm_source: 'chatgpt.com', from: 'home', entry_basis: 'nav-v1' }, 'Enter keeps the campaign tag and the referral code; no price limit, no max');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('');
    await page.type('#qs-max', '40');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup', 'a price limit without words is not sent');
    await page.type('#qs-words', 'x'.repeat(120));
    const href = await page.$eval('#qs-go', a => a.getAttribute('href'));
    eq(new URL(href, base).searchParams.get('hunt').length, 80, 'words stop at 80 characters, the length sign-up accepts');
    await page.$eval('#qs-max', e => { e.value = '-5'; e.dispatchEvent(new Event('input', { bubbles: true })); });
    ok(!/max=/.test(await page.$eval('#qs-go', a => a.getAttribute('href'))), 'a negative price limit is dropped');
    await ctx.close();
  }

  // ---- sign-up reads what the box sends (the address the price guide already uses) ---------------------------
  {
    const auth = fs.readFileSync(path.join(root, 'assets/auth.js'), 'utf8');
    ok(/qs\.get\('hunt'\)/.test(auth) && /qs\.get\('max'\)/.test(auth) && /snypd_hunt_intent/.test(auth), 'assets/auth.js still stores hunt + max for the first-hunt wizard');
  }

  // ---- plan links, counters, no leftovers from v5 --------------------------------------------------------------
  {
    const { page, ctx } = await open('');
    const links = await page.$$eval('a[href^="/signup"]', as => as.map(a => a.getAttribute('href') + ' | ' + a.textContent.trim()));
    for (const want of ['/signup?plan=pass | GET HUNT PASS', '/signup?plan=solo | START SOLO', '/signup?plan=pro | START PRO', '/signup?plan=kickstart | Kickstart', '/signup?plan=elite | Elite']) {
      ok(links.includes(want), 'plan link present: ' + want);
    }
    ok((await page.$$('#stat-listings')).length === 1 && (await page.$$('#stat-listings-asof')).length === 1, 'one listings figure and one date for prepublish.py');
    const text = await page.evaluate(() => document.body.innerText);
    ok(!/outnumbered|TRAVIS SCOTT|spots left|SEE HOW IT WORKS/i.test(text), 'the v5 hero, sneaker samples and founding line are gone');
    ok(/SAMPLE/.test(text), 'the example alerts are labelled as samples');
    ok(!/\b(instant|real-time|fastest|undetectable|sold prices)\b/i.test(text), 'no banned claim on the page');
    const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
    ok(!/demo-steps|renderDemo|Homepage v5/.test(html), 'the walkthrough code is gone');
    for (const m of html.matchAll(/<img[^>]+src="(\/[^"]+)"/g)) ok(fs.existsSync(path.join(root, m[1])), 'image exists: ' + m[1]);
    await ctx.close();
  }

  // ---- layout: no sideways scroll; on a phone the button is on the first screen ---------------------------------
  for (const [name, vp] of [['phone', { width: 390, height: 844, isMobile: true, hasTouch: true }], ['small phone', { width: 320, height: 640, isMobile: true, hasTouch: true }], ['tablet', { width: 820, height: 1100 }], ['desktop', { width: 1440, height: 900 }]]) {
    const { page, ctx } = await open('', vp);
    const m = await page.evaluate(() => {
      const r = id => document.getElementById(id).getBoundingClientRect();
      return { sw: document.documentElement.scrollWidth, iw: innerWidth, go: Math.round(r('qs-go').bottom), h1: Math.round(r('qs-words').top), ih: innerHeight,
        tap: [...document.querySelectorAll('.hp-btn, #qs-words, #qs-max')].filter(e => e.getClientRects().length).map(e => Math.round(e.getBoundingClientRect().height)) };
    });
    ok(m.sw <= m.iw + 1, name + ': no sideways scroll (' + m.sw + ' vs ' + m.iw + ')');
    ok(m.go <= m.ih, name + ': the "Watch it for me" button is on the first screen (' + m.go + ' of ' + m.ih + ')');
    ok(Math.min(...m.tap) >= 44, name + ': buttons and fields are at least 44 px tall');
    await ctx.close();
  }
  // sticky bar on a phone appears once the hero button has scrolled away
  {
    const { page, ctx } = await open('', { width: 390, height: 844, isMobile: true, hasTouch: true });
    ok(await page.$eval('#sticky-bar', e => e.hidden), 'phone: no sticky bar at the top of the page');
    await page.evaluate(() => scrollTo(0, 1600)); await wait(400);
    ok(!(await page.$eval('#sticky-bar', e => e.hidden)), 'phone: the sticky sign-up bar shows after the hero');
    await ctx.close();
  }

  await browser.close(); server.close();
  eq(errors, [], 'no page error');
  console.log(`PASS: ${passed} homepage checks.`);
})().catch(e => { console.error(e); process.exit(1); });
