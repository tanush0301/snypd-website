/*
 * "Join the SNYPD Discord" card (16 Nov 2026). The REAL dashboard.html in headless Chrome, ops/qa_mock.js standing in
 * for Supabase and api.snypd.store. Shown once per device, only while a free trial is running.
 *   node ops/test_discord_join.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
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
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const KEY = 'snypd_dc_join_v1';

(async () => {
  const html = fs.readFileSync(path.join(root, 'dashboard.html'));
  ok(html[0] === 0xEF && html[1] === 0xBB && html[2] === 0xBF, 'dashboard.html keeps its BOM');
  const text = html.toString('utf8');
  eq((text.match(/id="dc-join"/g) || []).length, 1, 'one card in the markup');
  ok(/id="dc-join" style="display:none"/.test(text), 'card is hidden in the markup');

  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q, vp) {
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 390, height: 844 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('#dc-join', { timeout: 10000 });
    await wait(1800);
    return page;
  }
  const state = page => page.evaluate(k => {
    const c = document.getElementById('dc-join');
    const go = document.getElementById('dc-join-go');
    return { shown: getComputedStyle(c).display !== 'none', title: document.getElementById('dc-join-title').textContent.trim(),
      href: go.getAttribute('href'), target: go.getAttribute('target'), rel: go.getAttribute('rel'),
      stored: !!localStorage.getItem(k), sw: document.documentElement.scrollWidth, vw: innerWidth, trial: document.body.dataset.trial };
  }, KEY);

  // 1. running trial, phone: shown, right link, no sideways scroll
  let page = await open('plan=free&trial=1');
  let s = await state(page);
  ok(s.shown, 'running trial: card shown');
  eq(s.title, 'Join the SNYPD Discord', 'title');
  eq(s.href, 'https://discord.gg/zESz4DAtP3', 'dashboard invite link');
  eq([s.target, s.rel], ['_blank', 'noopener'], 'opens in a new tab, noopener');
  ok(!s.stored, 'nothing remembered before a choice');
  ok(s.sw <= s.vw, 'no sideways scroll at 390 (' + s.sw + ' > ' + s.vw + ')');

  // 2. Not now: hidden, remembered, stays hidden after a reload
  await page.click('#dc-join-no');
  s = await state(page);
  ok(!s.shown && s.stored, 'Not now hides the card and remembers it');
  await page.close();
  page = await open('plan=free&trial=1');
  s = await state(page);
  ok(!s.shown, 'stays hidden on the next visit');
  await page.evaluate(k => localStorage.removeItem(k), KEY);
  await page.close();

  // 3. never outside a running trial
  for (const q of ['plan=elite', 'plan=free', 'plan=free&trial=ended']) {
    page = await open(q);
    s = await state(page);
    ok(!s.shown, q + ': card not shown');
    ok(!s.stored, q + ': nothing remembered');
    await page.close();
  }

  // 4. Join: remembered too; desktop width
  page = await open('plan=free&trial=1', { width: 1440, height: 900 });
  s = await state(page);
  ok(s.shown, 'running trial at 1440: card shown');
  ok(s.sw <= s.vw, 'no sideways scroll at 1440');
  await page.$eval('#dc-join-go', a => { a.addEventListener('click', e => e.preventDefault()); a.click(); });
  s = await state(page);
  ok(!s.shown && s.stored, 'Join hides the card and remembers it');
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close();
  server.close();
  console.log('discord join card: ' + passed + ' checks passed');
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
