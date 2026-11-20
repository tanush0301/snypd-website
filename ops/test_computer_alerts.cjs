/*
 * Browser test for the new-listing signals on an open dashboard (20 Nov 2026): on-page notice, count in the
 * tab title while the window is not in front, a short sound with a Profile switch.
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js (?broad=1 = a feed with listings).
 *   node ops/test_computer_alerts.cjs      (needs Google Chrome at CHROME_PATH or the default Windows path)
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
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
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const errors = [];
  async function open(q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForFunction(() => document.querySelectorAll('#list .card').length > 0, { timeout: 20000 });
    await wait(1500);
    return page;
  }
  // add n fresh listings to the mock's data and refresh the feed
  const arrive = (page, n) => page.evaluate(async n => {
    const DB = window.__qaDB, tpl = DB.current_ads.find(r => r.listing_id === 5000);
    window.__seq = (window.__seq || 0);
    for (let i = 0; i < n; i++) {
      const t = Date.now() - 1000, id = 7000 + (window.__seq++);
      DB.current_ads.push(Object.assign({}, tpl, { listing_id: id, title: 'Fresh arrival ' + id, url: 'https://www.vinted.be/items/' + id,
        fetched_at: new Date(t).toISOString(), created_at: new Date(t).toISOString(), uploaded_ts: Math.floor(t / 1000), uploaded_at_ts: new Date(t).toISOString() }));
    }
    await window.SNYPD.refreshFeed();
  }, n);
  const state = page => page.evaluate(() => {
    const note = document.getElementById('feed-new-note'), sw = document.getElementById('prof-toggle-sound');
    return { title: document.title, noteShown: !!note && !note.hidden, noteText: note ? note.textContent : null,
      beeps: window.__feedBeeps || 0, cards: document.querySelectorAll('#list .card').length,
      fresh: Array.from(document.querySelectorAll('#list .card .t')).filter(e => /Fresh arrival/.test(e.textContent)).length,
      swOn: !!sw && sw.classList.contains('is-on'), swAria: sw ? sw.getAttribute('aria-checked') : null,
      stored: localStorage.getItem('snypd_feed_sound'), overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
  });
  const front = (page, v) => page.evaluate(v => { document.hasFocus = () => v; }, v);

  // 1. page load: no signal for the listings already there
  let p = await open('broad=1');
  let s = await state(p);
  const T = s.title;
  ok(/SNYPD/.test(T), 'title at load: ' + T);
  ok(!s.noteShown, 'no notice at load');
  ok(s.beeps === 0, 'no sound at load');
  ok(s.swOn && s.swAria === 'true', 'sound switch on by default');
  const cards0 = s.cards;

  // 2. window in front: one new listing -> notice + sound, title unchanged
  await p.mouse.click(5, 5);            // first click wakes the audio
  await front(p, true);
  await arrive(p, 1);
  s = await state(p);
  ok(s.fresh === 1 && s.cards === cards0 + 1, 'the new card is in the feed');
  ok(s.noteShown && s.noteText === '1 new listing', 'notice: ' + s.noteText);
  ok(s.title === T, 'title unchanged while in front');
  ok(s.beeps === 1, 'one sound, got ' + s.beeps);
  ok(s.overflow <= 0, 'no sideways scroll');

  // 3. window not in front: title counts up, sound throttled to one per 10 s
  await front(p, false);
  await arrive(p, 2);
  s = await state(p);
  ok(s.title === '(2) ' + T, 'title counts: ' + s.title);
  ok(s.noteText === '2 new listings', 'notice plural: ' + s.noteText);
  ok(s.beeps === 1, 'no second sound within 10 s');
  await arrive(p, 1);
  s = await state(p);
  ok(s.title === '(3) ' + T, 'title adds up: ' + s.title);

  // 4. coming back clears the count
  await p.evaluate(() => window.dispatchEvent(new Event('focus')));
  s = await state(p);
  ok(s.title === T, 'focus resets the title');

  // 5. a refresh with nothing new: no signal
  await front(p, false);
  await p.evaluate(() => window.SNYPD.refreshFeed());
  s = await state(p);
  ok(s.title === T, 'nothing new: title stays');

  // 6. notice hides itself
  await wait(5600);
  s = await state(p);
  ok(!s.noteShown, 'notice hidden after 5 s');

  // 7. sound off in Profile: stored, no sound; back on: test sound
  await p.evaluate(() => document.getElementById('prof-toggle-sound').click());
  s = await state(p);
  ok(!s.swOn && s.swAria === 'false' && s.stored === 'off', 'switch off is stored');
  await wait(5000);                     // past the 10 s throttle since the first sound
  const before = s.beeps;
  await arrive(p, 1);
  s = await state(p);
  ok(s.beeps === before, 'sound off: silent');
  ok(s.noteShown, 'sound off: notice still shown');
  await p.evaluate(() => document.getElementById('prof-toggle-sound').click());
  s = await state(p);
  ok(s.swOn && s.stored === 'on', 'switch back on is stored');
  ok(s.beeps === before + 1, 'turning it on plays one test sound');

  // 8. the choice survives a reload
  await p.evaluate(() => localStorage.setItem('snypd_feed_sound', 'off'));
  await p.reload({ waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => document.querySelectorAll('#list .card').length > 0, { timeout: 20000 });
  s = await state(p);
  ok(!s.swOn && s.swAria === 'false', 'off is remembered after reload');

  // 9. more than 99 unseen
  p = await open('broad=1');
  await front(p, false);
  // a batch bigger than the feed's 60 cards replaces every card on screen: it must still signal (60 are loaded)
  await arrive(p, 120);
  s = await state(p);
  ok(s.title === '(60) ' + T, 'big batch signals what the feed loaded: ' + s.title);
  ok(s.noteText === '60 new listings', 'notice count: ' + s.noteText);
  await arrive(p, 70);
  s = await state(p);
  ok(/^\(99\+\) /.test(s.title), 'title caps at 99+: ' + s.title);

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' computer-alert browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
