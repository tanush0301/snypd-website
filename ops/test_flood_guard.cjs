/*
 * Flood guard (14 Nov 2026, website outreach/62 move 3): the REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_flood_guard.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: the max-price nudge in the first-hunt wizard and the Filters sheet (use a max, start without one, once per
 * search), the untouched default minimum no longer refuses a lower max (a typed minimum still does), the busy-hunt card
 * offers a max price from the hunt's own matches (apply + Undo) and Calm all for several busy hunts, French, 390 px,
 * no page errors. No network: the mock answers every call.
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
    const f = path.join(root, p);
    if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  // A fresh private context per page: "Keep it" / Calm all remember hunts in localStorage, which must not leak between scenarios.
  async function open(q, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    const close = page.close.bind(page);
    page.close = async () => { await close(); await ctx.close(); };
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(1500);
    return page;
  }
  const hunts = p => p.evaluate(() => window.__qaDB.user_searches.map(h => ({ id: h.id, url: h.vinted_url, mode: h.push_mode })));
  const vis = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.style.display !== 'none' && !e.hidden && e.getClientRects().length > 0; }, sel);
  const text = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return e ? e.innerText.replace(/\s+/g, ' ').trim() : ''; }, sel);
  const tc = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return e ? e.textContent.replace(/\s+/g, ' ').trim() : ''; }, sel);   // buttons are uppercased by CSS
  const setVal = (p, sel, v, typed) => p.evaluate((sel, v, typed) => { const e = document.querySelector(sel); e.value = v; if (typed) e.dispatchEvent(new Event('input', { bubbles: true })); }, sel, v, typed);
  const qOf = u => { try { return Object.fromEntries(new URL(u).searchParams); } catch (e) { return {}; } };

  // ---- 1. Wizard: no max -> nudge; "Use this max" saves with it and drops the untouched default minimum
  let page = await open('plan=free&hunts=0');
  await setVal(page, '#wiz-q-words', 'levis 501', true);
  await page.click('#wiz-q-save'); await wait(700);
  ok(await vis(page, '#wiz-q-mx'), 'nudge shown for a search without a max price');
  let t = await text(page, '#wiz-q-mx');
  ok(/Add a max price\?/.test(t) && /About half of the searches saved without one bring more than 1,000 matches a day/.test(t), 'nudge says why: ' + t.slice(0, 120));
  eq((await hunts(page)).length, 0, 'nothing saved while the nudge is open');
  await page.type('#wiz-q-mx [data-mx-in]', '0');
  await page.click('#wiz-q-mx [data-mx-act="use"]'); await wait(600);
  ok(await vis(page, '#wiz-q-mx') && (await hunts(page)).length === 0, 'a max of 0 is not accepted: the nudge stays, nothing saved');
  await page.$eval('#wiz-q-mx [data-mx-in]', e => { e.value = ''; });
  await page.type('#wiz-q-mx [data-mx-in]', '25');
  await page.click('#wiz-q-mx [data-mx-act="use"]'); await wait(1200);
  let h = await hunts(page);
  eq([h.length, qOf(h[0].url).price_to, qOf(h[0].url).price_from], [1, '25', undefined], 'saved with max 25, the default minimum 30 dropped');
  ok(await vis(page, '#wiz-step-mode'), 'wizard moves on');
  ok(!(await vis(page, '#wiz-q-err')), 'no form refusal');
  await page.close();

  // ---- 2. Wizard: "Start without a max" saves unchanged (default minimum kept); once per words
  page = await open('plan=free&hunts=0');
  await setVal(page, '#wiz-q-words', 'carhartt detroit', true);
  const defMin = await page.$eval('#wiz-q-min', e => e.value);   // the site's pre-filled minimum (30 EUR, 35 USD ...)
  ok(Number(defMin) > 0, 'a default minimum is pre-filled: ' + defMin);
  await page.click('#wiz-q-save'); await wait(700);
  await page.click('#wiz-q-mx [data-mx-act="keep"]'); await wait(1200);
  h = await hunts(page);
  eq([h.length, qOf(h[0].url).price_to, qOf(h[0].url).price_from], [1, undefined, defMin], 'saved without a max, default minimum kept');
  ok(await vis(page, '#wiz-step-mode'), 'wizard moves on after "Start without a max"');
  await page.close();

  // ---- 3. Wizard: a max typed below the untouched default minimum saves directly (no nudge, no refusal)
  page = await open('plan=free&hunts=0');
  await setVal(page, '#wiz-q-words', 'nike tech fleece', true);
  await setVal(page, '#wiz-q-max', '20', true);
  await page.click('#wiz-q-save'); await wait(1200);
  h = await hunts(page);
  eq([h.length, qOf(h[0].url).price_to, qOf(h[0].url).price_from], [1, '20', undefined], 'max 20 saved; the untouched minimum 30 cleared');
  ok(!(await vis(page, '#wiz-q-mx')) && !(await vis(page, '#wiz-q-err')), 'no nudge, no refusal');
  await page.close();

  // ---- 4. Wizard: a minimum the user typed at or above the max is still refused
  page = await open('plan=free&hunts=0');
  await setVal(page, '#wiz-q-words', 'nike tech fleece', true);
  const typedMin = await page.$eval('#wiz-q-min', e => e.value);   // retyped by the user: the same value as the default
  await setVal(page, '#wiz-q-min', typedMin, true);
  await setVal(page, '#wiz-q-max', String(Number(typedMin) - 10), true);
  await page.click('#wiz-q-save'); await wait(800);
  ok(await vis(page, '#wiz-q-err'), 'a minimum typed by the user (' + typedMin + ') above the max: refused');
  eq((await hunts(page)).length, 0, 'nothing saved');
  await page.close();

  // ---- 5. Filters sheet: quick search without a max -> nudge -> max 40 saved
  page = await open('plan=elite');
  let before = (await hunts(page)).length;
  await page.click('#filter-pill'); await wait(600);
  await setVal(page, '#fs-q-words', 'stone island', true);
  await page.click('#filter-new-save'); await wait(700);
  ok(await vis(page, '#fs-q-mx'), 'sheet: nudge shown');
  eq((await hunts(page)).length, before, 'sheet: nothing saved yet');
  await page.type('#fs-q-mx [data-mx-in]', '40');
  await page.click('#fs-q-mx [data-mx-act="use"]'); await wait(1200);
  h = await hunts(page);
  let si = h.find(x => qOf(x.url).search_text === 'stone island');
  ok(h.length === before + 1 && si && qOf(si.url).price_to === '40', 'sheet: saved with max 40: ' + (si && si.url));

  // ---- 6. Filters sheet: a pasted link without a max -> nudge -> "Start without a max" saves it unchanged
  before = h.length;
  await setVal(page, '#filter-new-url', 'https://www.vinted.de/catalog?search_text=fred%20perry&order=newest_first', true);
  await page.click('#filter-new-save'); await wait(700);
  ok(await vis(page, '#fs-q-mx'), 'sheet: nudge for a pasted link');
  await page.click('#fs-q-mx [data-mx-act="keep"]'); await wait(1200);
  h = await hunts(page);
  const fp = h.find(x => qOf(x.url).search_text === 'fred perry');
  ok(h.length === before + 1 && fp && !qOf(fp.url).price_to, 'sheet: pasted link saved without a max: ' + (fp && fp.url));
  await page.close();

  // ---- 7. Busy-hunt card: a max price from the hunt's own matches, applied through the coach's path, Undo restores
  page = await open('plan=elite&broad=1');
  await page.waitForFunction(() => { const c = document.getElementById('broad-hunt'), t = document.getElementById('broad-hunt-text'); return c && c.style.display !== 'none' && t && t.textContent.length > 0; }, { timeout: 8000 });
  ok(await vis(page, '#broad-hunt'), 'busy-hunt card shown');
  t = await text(page, '#broad-hunt-text');
  ok(/^About \d+ new listings an hour match "jordan travis scott": more than anyone can open\. A max price of €29 keeps the cheapest quarter of them\. Or switch to Calm: at most one summary every 15 min\.$/.test(t), 'card text: ' + t);
  eq([await vis(page, '#broad-hunt-apply'), await tc(page, '#broad-hunt-apply'), await vis(page, '#broad-hunt-edit'), await vis(page, '#broad-hunt-calm'), await vis(page, '#broad-hunt-calmall')],
    [true, 'Set max €29', false, true, false], 'buttons: Set max, Calm, Keep; no Calm all for one busy hunt');
  eq(await page.$eval('#broad-hunt', e => e.dataset.kind), 'broad', 'card stamps its kind');
  const orig = (await hunts(page)).find(x => x.id === 'search-1').url;
  await page.click('#broad-hunt-apply'); await wait(900);
  let s1 = (await hunts(page)).find(x => x.id === 'search-1');
  eq(qOf(s1.url).price_to, '29', 'hunt now has max 29');
  ok(/Done: "jordan travis scott" now has a max price of €29\./.test(await text(page, '#broad-hunt-text')) && await vis(page, '#broad-hunt-undo'), 'done line + Undo');
  await page.click('#broad-hunt-undo'); await wait(900);
  s1 = (await hunts(page)).find(x => x.id === 'search-1');
  eq(s1.url, orig, 'Undo restores the link');
  await page.close();

  // ---- 8. Two busy hunts: Calm all 2 switches both
  page = await open('plan=elite&broad=2');
  await page.waitForFunction(() => { const c = document.getElementById('broad-hunt'), t = document.getElementById('broad-hunt-text'); return c && c.style.display !== 'none' && t && t.textContent.length > 0; }, { timeout: 8000 });
  ok(await vis(page, '#broad-hunt-calmall') && await tc(page, '#broad-hunt-calmall') === 'Calm all 2', 'Calm all 2 offered');
  ok(/ 2 of your hunts are this busy\.$/.test(await text(page, '#broad-hunt-text')), 'count said');
  await page.click('#broad-hunt-calmall'); await wait(1200);
  h = await hunts(page);
  eq([h.find(x => x.id === 'search-1').mode, h.find(x => x.id === 'search-busy2').mode], ['calm', 'calm'], 'both busy hunts now Calm');
  eq(await text(page, '#broad-hunt-text'), 'Done: 2 hunts now send at most one summary every 15 min. Change it anytime in Filters.', 'done line');
  await page.close();

  // ---- 9. French + phone: the nudge and the card read in French and fit 390 px
  page = await open('plan=free&hunts=0&lang=fr', PHONE);
  await setVal(page, '#wiz-q-words', 'levis 501', true);
  await page.click('#wiz-q-save'); await wait(700);
  t = await text(page, '#wiz-q-mx');
  ok(/Ajouter un prix max\s\?/.test(t) && /Environ la moitié des recherches enregistrées sans prix max/.test(t) && /Utiliser ce max/i.test(t) && /Lancer sans prix max/i.test(t), 'French nudge: ' + t.slice(0, 140));
  const fit = await page.$eval('#wiz-q-mx', e => e.scrollWidth <= e.clientWidth + 1 && e.getBoundingClientRect().right <= window.innerWidth + 1);
  ok(fit, 'nudge fits 390 px');
  ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'no sideways scroll at 390 px');
  await page.close();
  page = await open('plan=elite&broad=1&lang=fr', PHONE);
  await page.waitForFunction(() => { const c = document.getElementById('broad-hunt'), t = document.getElementById('broad-hunt-text'); return c && c.style.display !== 'none' && t && t.textContent.length > 0; }, { timeout: 8000 });
  t = await text(page, '#broad-hunt-text');
  ok(/^Environ \d+ nouvelles annonces par heure correspondent à/.test(t) && /Un prix max de .*29.* garde le quart le moins cher\./.test(t) && /Ou passe en Calme/.test(t), 'French card: ' + t);
  await page.close();

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' flood-guard browser checks.');
})().catch(e => { console.error(e); process.exit(1); });
