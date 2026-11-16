/*
 * Referral bonus days count like a running trial on the dashboard (16 Nov 2026; migration 090 carries
 * profile.referral_bonus_until in dashboard_boot). The REAL dashboard.html in headless Chrome, ops/qa_mock.js
 * standing in for Supabase. Outside requests are blocked.
 *   node ops/test_bonus_days.cjs   (needs Google Chrome; PUPPETEER_DIR may point at another checkout's puppeteer-core)
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require(process.env.PUPPETEER_DIR || 'puppeteer-core');
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
const eq = (a, b, m) => { assert.deepEqual(a, b, m + ' -> ' + JSON.stringify(a)); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function state(q) {
    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844 });
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') || r.url().startsWith('blob:')) ? r.continue() : r.abort());
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#filter-pill', { timeout: 10000 });
    await wait(1800);
    await page.evaluate(() => document.getElementById('filter-pill').click());
    await wait(500);
    const s = await page.evaluate(() => {
      const live = document.querySelector('.fs-row.is-live .fs-row__status-text');
      const locked = document.getElementById('mr-locked');
      return { plan: document.body.dataset.plan, trial: document.body.dataset.trial || '', prFree: document.body.classList.contains('pr-free'),
        locked: !!locked && locked.style.display !== 'none', chip: (document.getElementById('mr-tier-chip') || {}).textContent || '',
        live: live ? live.textContent.trim() : null };
    });
    await page.close();
    return s;
  }
  const OPEN = { plan: 'free', trial: '1', prFree: false, locked: false, chip: 'Trial: 10 price checks', live: 'LIVE' };
  const SHUT = { plan: 'free', trial: '', prFree: true, locked: true, live: 'LIVE WHILE OPEN' };
  const pick = (s, ref) => Object.fromEntries(Object.keys(ref).map(k => [k, s[k]]));

  for (const boot of ['', '&boot=1']) {
    const tag = boot ? ' (boot RPC)' : ' (REST read)';
    let s = await state('plan=free&bonus=1' + boot);
    eq(pick(s, OPEN), OPEN, 'bonus days running: Market open, price lines open, hunt LIVE' + tag);
    s = await state('plan=free' + boot);
    eq(pick(s, SHUT), SHUT, 'plain Free stays locked' + tag);
    s = await state('plan=free&bonus=ended' + boot);
    eq(pick(s, SHUT), SHUT, 'ended bonus days: locked again' + tag);
    s = await state('plan=free&trial=1' + boot);
    eq(pick(s, OPEN), OPEN, 'running trial unchanged' + tag);
    s = await state('plan=free&trial=ended&bonus=1' + boot);
    eq(pick(s, OPEN), OPEN, 'trial ended + bonus days running: open' + tag);
  }
  let s = await state('plan=free&bonus=1&boot=1&pre090=1');
  eq(pick(s, SHUT), SHUT, 'database without migration 090: treated as no bonus, no error');
  s = await state('plan=elite&bonus=1');
  eq({ plan: s.plan, trial: s.trial, prFree: s.prFree, locked: s.locked, live: s.live }, { plan: 'elite', trial: '', prFree: false, locked: false, live: 'LIVE' }, 'paid plan unaffected by bonus days');

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('bonus days: ' + passed + ' checks pass');
})().catch(e => { console.error(e.message || e); process.exit(1); });
