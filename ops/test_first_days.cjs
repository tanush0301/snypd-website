/*
 * Browser test for the first-days layout (19 Nov 2026): for 3 days after sign-up the email-news card, the
 * Discord card and the claim hint sit below the feed, and the alerts card is compact on phones.
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js (?joined=fresh = account 1 hour old).
 *   node ops/test_first_days.cjs              (needs Google Chrome at CHROME_PATH or the default Windows path)
 *   SHOTS=<dir> node ops/test_first_days.cjs  also writes screenshots
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
const MOVED = ['email-optin-card', 'dc-join', 'claim-hint'];
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  const PHONE = { width: 390, height: 664, isMobile: true, hasTouch: true };
  async function open(q, vp, shot) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(6000);
    if (SHOTS && shot) await page.screenshot({ path: path.join(SHOTS, shot), fullPage: true });
    return page.evaluate(MOVED => {
      const vis = el => !!el && el.offsetParent !== null && getComputedStyle(el).display !== 'none';
      const top = el => Math.round(el.getBoundingClientRect().top + window.scrollY);
      const list = document.getElementById('list');
      const first = document.querySelector('#list .card, #examples-list .card');
      const setup = document.getElementById('alerts-setup-card');
      const setupText = setup && setup.querySelector('.elite-banner__text');
      const out = {
        flag: document.body.getAttribute('data-first-days'),
        firstInList: !!first && !!first.closest('#list'), firstInExamples: !!first && !!first.closest('#examples-list'),
        listTop: top(list), firstTop: first && vis(first) ? top(first) : null,
        setupShown: vis(setup), setupTextShown: vis(setupText), setupHeight: vis(setup) ? Math.round(setup.getBoundingClientRect().height) : 0,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        cards: {},
      };
      MOVED.forEach(id => {
        const el = document.getElementById(id);
        out.cards[id] = {
          exists: !!el, shown: vis(el), top: el && vis(el) ? top(el) : null,
          afterList: !!el && !!(list.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING),
          inFeedPanel: !!el && el.parentNode === document.getElementById('msg').parentNode,
        };
      });
      return out;
    }, MOVED);
  }
  const brief = s => JSON.stringify({ first: s.firstTop, list: s.listTop, setup: s.setupHeight, shown: MOVED.filter(id => s.cards[id].shown) });

  // 1. Account 1 hour old, phone, feed with listings.
  let s = await open('joined=fresh&trial=1&broad=1', PHONE, 'first-days-phone.png');
  console.log('fresh phone      ', brief(s));
  ok(s.flag === '1', 'new account is flagged');
  MOVED.forEach(id => {
    ok(s.cards[id].exists && s.cards[id].afterList && s.cards[id].inFeedPanel, id + ' sits after the feed list, inside the feed panel');
    if (s.cards[id].shown) ok(s.cards[id].top > s.listTop, id + ' is drawn below the top of the feed');
  });
  if (s.setupShown) ok(!s.setupTextShown, 'phone: alerts card is compact (no second line)');
  ok(s.firstTop != null && s.firstInList, 'a feed listing is drawn');
  ok(s.overflow <= 0, 'phone: no sideways scroll');
  const freshFirst = s.firstTop;

  // 2. Same account, empty feed: the examples come up the same way.
  s = await open('joined=fresh&trial=1&feed=empty', PHONE, 'first-days-phone-empty.png');
  console.log('fresh phone empty', brief(s));
  ok(s.flag === '1', 'empty feed: flagged');
  ok(s.firstTop != null && s.firstInExamples, 'empty feed: an example is drawn');
  MOVED.forEach(id => { if (s.cards[id].shown && s.firstTop != null) ok(s.cards[id].top > s.firstTop, 'empty feed: ' + id + ' below the first example'); });
  ok(s.overflow <= 0, 'empty feed: no sideways scroll');

  // 3. Older account, phone: nothing moves.
  s = await open('trial=1&broad=1', PHONE, 'old-account-phone.png');
  console.log('old phone        ', brief(s));
  ok(s.flag === null, 'older account is not flagged');
  ok(s.firstInList, 'older account: a feed listing is drawn');
  MOVED.forEach(id => ok(s.cards[id].exists && !s.cards[id].afterList, id + ' stays above the feed for an older account'));
  if (s.setupShown) ok(s.setupTextShown, 'older account: alerts card keeps its second line');
  if (s.firstTop != null && MOVED.some(id => s.cards[id].shown)) ok(freshFirst < s.firstTop, 'new account sees its first listing higher (' + freshFirst + ' vs ' + s.firstTop + ')');

  // 4. New account on a computer: cards move, the alerts card keeps its text.
  s = await open('joined=fresh&trial=1&broad=1', null, 'first-days-desktop.png');
  console.log('fresh desktop    ', brief(s));
  ok(s.flag === '1', 'desktop: flagged');
  MOVED.forEach(id => ok(s.cards[id].afterList, 'desktop: ' + id + ' after the feed'));
  if (s.setupShown) ok(s.setupTextShown, 'desktop: alerts card keeps its second line');
  ok(s.overflow <= 0, 'desktop: no sideways scroll');

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' first-days browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
