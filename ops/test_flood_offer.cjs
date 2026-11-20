/*
 * Browser test for the flood offer link (20 Nov 2026): a push link ?flood=<saved search id> opens the
 * busy-search card for that search, with the existing Calm / cheap-only / Edit / Keep buttons.
 * The REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_flood_offer.cjs      (needs Google Chrome at CHROME_PATH or the default Windows path)
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
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForFunction(() => document.querySelectorAll('#list .card').length > 0, { timeout: 20000 }).catch(() => {});
    await wait(2500);
    return page;
  }
  const state = page => page.evaluate(() => {
    const vis = id => { const e = document.getElementById(id); return !!e && e.style.display !== 'none' && e.offsetParent !== null; };
    const card = document.getElementById('broad-hunt');
    const row = id => (window.__qaDB.user_searches.find(r => r.id === id) || {});
    return {
      card: vis('broad-hunt'), kind: card.dataset.kind || '',
      title: document.getElementById('broad-hunt-title').textContent,
      text: document.getElementById('broad-hunt-text').textContent,
      calm: vis('broad-hunt-calm'), cheap: vis('broad-hunt-cheap'), edit: vis('broad-hunt-edit'), keep: vis('broad-hunt-keep'),
      apply: vis('broad-hunt-apply'), calmall: vis('broad-hunt-calmall'), undo: vis('broad-hunt-undo'),
      search: location.search, free: document.body.classList.contains('pr-free'),
      mode1: row('search-1').push_mode, min1: row('search-1').push_calm_minutes, mode2: row('search-2').push_mode,
      kept: localStorage.getItem('snypd_broad_ok') || '',
    };
  });

  // 1. the link opens the card for that search
  let p = await open('flood=search-1&src=push');
  let s = await state(p);
  ok(s.card && s.kind === 'flood', 'card shown for the linked search');
  ok(s.title === 'This search is very busy', 'title: ' + s.title);
  ok(/^"jordan travis scott" sent you a lot of alerts in the last hour\. Calm sends at most one summary every 15 min\. Or get an alert only for the cheap finds\.$/.test(s.text), 'text: ' + s.text);
  ok(s.calm && s.cheap && s.edit && s.keep, 'Calm, cheap-only, Edit and Keep offered');
  ok(!s.apply && !s.calmall && !s.undo, 'no max-price, Calm-all or Undo button');
  ok(!/flood=/.test(s.search) && /src=push/.test(s.search), 'flood removed from the address, the rest kept: ' + s.search);
  ok(s.mode1 === 'every', 'nothing changed before a tap');

  // 2. Calm: one tap saves it
  await p.click('#broad-hunt-calm');
  await wait(600);
  s = await state(p);
  ok(s.mode1 === 'calm' && s.min1 === 15, 'Calm saved on that search');
  ok(/^Done: "jordan travis scott" now sends at most one summary every 15 min\./.test(s.text), 'confirmation: ' + s.text);
  ok(!s.calm && !s.cheap && !s.edit && !s.keep, 'buttons gone after the switch');
  ok(s.mode2 === 'calm', 'the other search untouched');

  // 3. cheap-only: one tap saves it
  p = await open('flood=search-1');
  await p.click('#broad-hunt-cheap');
  await wait(600);
  s = await state(p);
  ok(s.mode1 === 'cheap', 'cheap-only saved on that search');
  ok(/now sends a push only for the cheap finds/.test(s.text), 'confirmation: ' + s.text);

  // 4. Keep: card closes, nothing changes
  p = await open('flood=search-1');
  await p.click('#broad-hunt-keep');
  await wait(300);
  s = await state(p);
  ok(!s.card && s.mode1 === 'every', 'Keep closes the card and changes nothing');
  ok(s.kept.length > 2, 'Keep is remembered');

  // 5. Free plan after the trial: no cheap-only button, no sentence about it
  p = await open('flood=search-1&plan=free&trial=ended');
  s = await state(p);
  ok(s.free, 'mock account is on Free');
  ok(s.card && s.calm && !s.cheap, 'Free: Calm offered, cheap-only not');
  ok(!/cheap/.test(s.text), 'Free: no cheap sentence: ' + s.text);

  // 6. a search that is already Calm (and inactive), an unknown id, the fallback value: nothing shown
  for (const id of ['search-2', 'nope', '1']) {
    p = await open('flood=' + id);
    s = await state(p);
    ok(!s.card, 'flood=' + id + ': no card');
    ok(!/flood=/.test(s.search), 'flood=' + id + ': removed from the address');
  }
  p = await open('seedcalm=1&flood=search-1');
  s = await state(p);
  ok(!s.card, 'linked search already Calm: no card');

  // 7. no link: no card
  p = await open('x=1');
  s = await state(p);
  ok(!s.card, 'no flood link: no card');

  // 8. the feed-based "very broad" card does not replace the offer
  p = await open('broad=1&flood=search-1');
  await wait(1500);
  s = await state(p);
  ok(s.card && s.kind === 'flood' && s.title === 'This search is very busy', 'offer keeps the card on a busy feed: ' + s.title);
  ok(!s.apply && !s.calmall, 'no buttons from the other card');

  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' flood-offer browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
