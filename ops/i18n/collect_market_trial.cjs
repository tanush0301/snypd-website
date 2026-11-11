/*
 * Collector for the trial price-check strings (11 Nov 2026): opens the REAL dashboard.html in French with
 * ?i18n_collect=1 on ops/qa_mock.js, drives every new state, prints window.SNYPD_I18N.missing() as JSON.
 *   node ops/i18n/collect_market_trial.cjs
 */
'use strict';
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const root = path.join(__dirname, '..', '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json' };
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

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--lang=fr-FR'] });
  const all = new Set();
  async function open(q) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    await page.evaluateOnNewDocument(() => { try { localStorage.setItem('snypd_ui_lang', 'fr'); } catch (e) {} });
    await page.goto(base + '/dashboard.html?lang=fr&i18n_collect=1&' + q, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#list .card .mkt-check', { timeout: 10000 });
    await page.click('.view-tab[data-view="market"]');
    return page;
  }
  async function check(page, q) {
    await page.$eval('#mr-query', (e, v) => { e.value = v; }, q);
    await page.click('#mr-go');
    await page.waitForFunction(() => { const r = document.getElementById('mr-result'); return r && !r.querySelector('.mr-loading') && r.innerText.length > 10; }, { timeout: 8000 });
    await new Promise(r => setTimeout(r, 400));
  }
  async function harvest(page) {
    const m = await page.evaluate(() => (window.SNYPD_I18N && window.SNYPD_I18N.missing) ? window.SNYPD_I18N.missing() : null);
    (Array.isArray(m) ? m : Object.keys(m || {})).forEach(s => all.add(s));
  }
  let page = await open('plan=free&trial=1&pr=1');
  await check(page, 'jordan 1 mid'); await harvest(page);
  await check(page, 'zzz_nomatch item'); await harvest(page);
  await page.close();
  page = await open('plan=free&trial=1&trial_used=10&pr=1');
  await check(page, 'adidas samba'); await harvest(page);
  await page.close();
  page = await open('plan=elite&pr=1');
  await check(page, 'medq jacket'); await harvest(page);
  await check(page, 'trackq item'); await harvest(page);
  await page.evaluate(() => window.SNYPD.marketCheckCard({ title: 'Patagonia Synchilla Fleece', brand: 'Patagonia', cond: 'Good', cur: 'USD' }));
  await page.waitForFunction(() => { const b = document.querySelector('.mr-sheet.on .mr-sheet__bd'); return b && !b.querySelector('.mr-loading') && b.innerText.length > 20; }, { timeout: 8000 });
  await new Promise(r => setTimeout(r, 400));
  await harvest(page);
  await page.close();
  await browser.close();
  server.close();
  console.log(JSON.stringify([...all].sort(), null, 1));
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
