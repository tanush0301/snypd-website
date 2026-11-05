/*
 * Browser test for the weekly "Your hunts this week" card (Session 66 P6) on the Market tab: the REAL dashboard.html in
 * headless Chrome, ops/qa_mock.js standing in for Supabase and api.snypd.store (/api/v1/hunt-report; ?hr=teaser|empty|error).
 *   node ops/test_hunt_report.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: full report (busiest hunt first, counts, change vs last week, cheapest find + its Vinted link, per-condition typical +
 * range, thin / mixed conditions, other currencies, a hunt with nothing, hunt names escaped, no link for a bad id), the one-line
 * teaser for other plans, empty + error states, one request per visit (5 min), French, 390 px without overflow, no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    if (p === '/plans') return send('<!doctype html>plans', 'text/html');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
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
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(800);
    await page.evaluate(() => {  // wrap the QA mock's fetch (it answers /hunt-report itself)
      window.__hr = 0;
      const f = window.fetch;
      window.fetch = (u, o) => { if (String(u).includes('/hunt-report')) window.__hr++; return f(u, o); };
    });
    await page.evaluate(() => document.querySelector('[data-view="market"]').click());
    await page.waitForFunction(() => { const b = document.getElementById('hr-box'); return b && b.style.display !== 'none' && b.innerText.length > 10; }, { timeout: 8000 });
    await wait(400);
    return page;
  }
  const read = p => p.evaluate(() => {
    const box = document.getElementById('hr-box');
    return {
      text: box.innerText,
      hunts: [...box.querySelectorAll('.hr-h')].map(h => ({
        name: h.querySelector('.hr-name').innerText, nameHtml: h.querySelector('.hr-name').innerHTML,
        top: h.querySelector('.hr-h__top').innerText.replace(/\s+/g, ' '),
        cheap: (h.querySelector('.hr-cheap') || {}).innerText, thin: (h.querySelector('.hr-thin') || {}).innerText || '',
        link: (h.querySelector('.hr-cheap a') || {}).href || null,
        linkAttrs: h.querySelector('.hr-cheap a') ? [h.querySelector('.hr-cheap a').target, h.querySelector('.hr-cheap a').rel] : null,
        conds: [...h.querySelectorAll('.hr-c')].map(c => c.innerText.replace(/\s+/g, ' ').trim()),
      })),
      requests: window.__hr,
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });

  // ---- 1. Elite: the full report
  let page = await open('plan=elite');
  let s = await read(page);
  ok(/^Your hunts this week/.test(s.text) && /12 Nov . 18 Nov/.test(s.text), 'title + dates: ' + s.text.slice(0, 60));
  eq(s.hunts.map(h => h.name), ['carhartt', 'barbour <b>wax</b>', 'lego'], 'hunts in the order the backend sends (busiest first)');
  eq(s.hunts[1].nameHtml.includes('<b>'), false, 'a hunt name is escaped, never HTML');
  eq(s.hunts[0].top, 'carhartt 213 new listings +52% vs last week', 'count + change vs last week');
  ok(/^Cheapest find \u20AC9 \u00b7 Good/.test(s.hunts[0].cheap), 'cheapest find with price + condition: ' + s.hunts[0].cheap);
  eq([s.hunts[0].link, s.hunts[0].linkAttrs], ['https://www.vinted.fr/items/10300009001', ['_blank', 'noopener noreferrer']], 'cheapest find opens on Vinted in a new tab');
  eq(s.hunts[0].conds, ['Very good 210 listings typical \u20AC27.50 \u00b7 \u20AC19.50\u2013\u20AC33 +8% vs last week'], 'per condition: typical, range, change; thin conditions are not listed one by one');
  eq(s.hunts[0].thin, '3 more listings in other conditions: too few to price yet.', 'thin conditions folded into one line');
  ok(/\u00a3/.test(s.hunts[1].conds.join(' ')) && s.hunts[1].link === null, 'GBP prices on a UK hunt; no link for a bad id');
  eq(s.hunts[1].conds[0], 'Muy bueno 40 listings Too mixed for one price', 'mixed condition: no single price, Vinted name kept');
  ok(s.hunts[1].top.endsWith('75 new listings'), 'no change shown without last week: ' + s.hunts[1].top);
  ok(/No new listings this week yet\./.test(s.hunts[2].cheap) && s.hunts[2].conds.length === 0, 'a hunt with nothing says so');
  ok(/Asking prices of the new listings your hunts found in the last 7 days \(UTC days\), not sold prices\./.test(s.text), 'honest note');
  eq(s.requests, 1, 'one request when the Market tab opens');
  await page.evaluate(() => { document.querySelector('[data-view="feed"]').click(); });
  await wait(300);
  await page.evaluate(() => { document.querySelector('[data-view="market"]').click(); });
  await wait(600);
  eq((await read(page)).requests, 1, 'reopening the tab within 5 min does not ask again');
  await page.close();

  // ---- 2. other plans: one line
  page = await open('plan=free');
  s = await read(page);
  ok(/288 new listings found by your hunts\. Cheapest find \u20AC9 \(carhartt\)\./.test(s.text), 'teaser line: ' + s.text);
  ok(/is part of Pro and Elite\. See plans/.test(s.text) && s.hunts.length === 0, 'teaser: upgrade link, no per-hunt rows');
  eq(await page.$eval('#hr-box a', a => new URL(a.href).pathname), '/plans', 'teaser link goes to /plans');
  await page.close();

  // ---- 3. empty + error
  page = await open('plan=elite&hr=empty');
  ok(/No active hunts\. Start a hunt to get this report\./.test((await read(page)).text), 'no hunts -> says so');
  await page.close();
  page = await open('plan=elite&hr=error');
  ok(/Could not load your weekly report right now\./.test((await read(page)).text), '503 -> a plain error line');
  await page.close();

  // ---- 4. French + phone
  page = await open('plan=elite&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await wait(600);
  s = await read(page);
  ok(/^Tes recherches cette semaine/.test(s.text), 'French title: ' + s.text.slice(0, 40));
  eq(s.hunts[0].top, 'carhartt 213 nouvelles annonces +52 % vs semaine derni\u00e8re', 'French count + change');
  ok(await page.$eval('#hr-box .hr-d', e => e.textContent.includes('+52\u00a0%')), 'French: no-break space before %');
  ok(/^Trouvaille la moins ch\u00e8re 9\s\u20AC \u00b7 Bon \u00e9tat Ouvrir sur Vinted$/.test(s.hunts[0].cheap), 'French cheapest line (French money format): ' + s.hunts[0].cheap);
  ok(/^Tr\u00e8s bon \u00e9tat 210 annonces typique 27,50\s\u20AC/.test(s.hunts[0].conds[0]) && s.hunts[0].conds.length === 1 && /^3 autres annonces dans d’autres états\s: encore trop peu pour un prix\.$/.test(s.hunts[0].thin), 'French conditions + folded line: ' + s.hunts[0].conds.join(' | ') + ' / ' + s.hunts[0].thin);
  ok(/pas les prix r\u00e9ellement pay\u00e9s/.test(s.text) && !/prix de vente/i.test(s.text), 'French note, never "prix de vente"');
  ok(s.overflow <= 0, '390 px: no horizontal overflow (' + s.overflow + ')');
  await page.close();
  page = await open('plan=free&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  await wait(600);
  s = await read(page);
  ok(/288 nouvelles annonces trouv\u00e9es par tes recherches\./.test(s.text) && /fait partie de Pro et Elite/.test(s.text), 'French teaser: ' + s.text);
  ok(s.overflow <= 0, '390 px teaser: no overflow');
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' hunt-report checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
