/*
 * SNYPD AI hunt helper (16 Nov 2026): the REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_hunt_ai.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks the box in the first-hunt wizard and in the Filters sheet: describe -> options from POST /api/v1/hunt-ai ->
 * a pick fills the words and the max price; busy option; nothing found / not available / rate limited; malformed
 * options; HTML shown as text; French on a phone; no page errors. No network: the mock answers every call.
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
  const hunts = p => p.evaluate(() => window.__qaDB.user_searches.map(h => ({ id: h.id, url: h.vinted_url })));
  const vis = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.style.display !== 'none' && e.getClientRects().length > 0; }, sel);
  const text = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return e ? e.innerText.replace(/\s+/g, ' ').trim() : ''; }, sel);
  const val = (p, sel) => p.$eval(sel, e => e.value);
  const reqs = p => p.evaluate(() => window.__aiRequests || []);
  const qOf = u => { try { return Object.fromEntries(new URL(u).searchParams); } catch (e) { return {}; } };
  const describe = async (p, box, t) => {
    await p.$eval(box + ' [data-ai-text]', (e, t) => { e.value = t; }, t);
    await p.$eval(box + ' [data-ai-go]', e => e.click());
    await wait(500);
  };

  // ---- 1. Wizard: the box, a description, three options, a pick fills words + max, the hunt saves
  let page = await open('plan=free&hunts=0');
  ok(await vis(page, '#wiz-q-ai'), 'wizard: SNYPD AI box shown');
  let t = await text(page, '#wiz-q-ai');
  ok(/^SNYPD AI/.test(t) && /Describe what you want in your own words/.test(t) && /Suggest a search/i.test(t), 'box text: ' + t);
  await page.$eval('#wiz-q-ai [data-ai-go]', e => e.click()); await wait(300);
  eq((await reqs(page)).length, 0, 'empty description: no request');
  await describe(page, '#wiz-q-ai', 'jordan 4 military black size 43');
  const site = await val(page, '#wiz-q-site');
  eq(await reqs(page), [{ text: 'jordan 4 military black size 43', site: site }], 'one request with the text and the chosen Vinted site');
  let o = await page.$$eval('#wiz-q-ai [data-ai-pick]', bs => bs.map(b => b.innerText.replace(/\s+/g, ' ').trim()));
  eq(o.length, 3, 'three options');
  ok(/^jordan 4 military black 209 listings in 14 days · max €80$/.test(o[0]), 'option with our count and max: ' + o[0]);
  ok(o[1].includes('jordan 4 <b>x</b>') && (await page.$$eval('#wiz-q-ai [data-ai-pick] b b', x => x.length)) === 0, 'HTML in an option is shown as text');
  ok(/^jordan sneakers very busy search$/.test(o[2]), 'busy option has no count and no max: ' + o[2]);
  ok(/Suggested by AI, checked against our Vinted listings\. It can be wrong\./.test(await text(page, '#wiz-q-ai')), 'AI note shown');
  await page.click('#wiz-q-ai [data-ai-pick="0"]'); await wait(300);
  const minNow = await val(page, '#wiz-q-min');   // the wizard's default minimum for this site (below 80)
  ok(Number(minNow) > 0 && Number(minNow) < 80, 'default minimum is below the picked max: ' + minNow);
  eq([await val(page, '#wiz-q-words'), await val(page, '#wiz-q-max')], ['jordan 4 military black', '80'], 'pick fills words + max; a minimum below the max stays');
  eq((await hunts(page)).length, 0, 'a pick saves nothing by itself');
  await page.click('#wiz-q-save'); await wait(1200);
  let h = await hunts(page);
  eq([h.length, qOf(h[0].url).search_text, qOf(h[0].url).price_to], [1, 'jordan 4 military black', '80'], 'the hunt saves with the picked words and max');
  ok(!(await vis(page, '#wiz-q-mx')), 'no max-price nudge: the max is already set');
  await page.close();

  // ---- 2. Wizard: busy pick leaves the max alone; a max below the default minimum clears the minimum; malformed options ignored
  page = await open('plan=free&hunts=0');
  await describe(page, '#wiz-q-ai', 'jordan sneakers');
  await page.click('#wiz-q-ai [data-ai-pick="2"]'); await wait(300);
  eq([await val(page, '#wiz-q-words'), await val(page, '#wiz-q-max')], ['jordan sneakers', ''], 'busy pick: words filled, no max invented');
  await page.click('#wiz-q-ai [data-ai-back]'); await wait(200);
  ok(await page.$('#wiz-q-ai [data-ai-text]'), '"Describe something else" brings the text box back');
  await describe(page, '#wiz-q-ai', 'aibad levis');
  o = await page.$$eval('#wiz-q-ai [data-ai-pick]', bs => bs.map(b => b.innerText.replace(/\s+/g, ' ').trim()));
  eq(o, ['levis 501 993 listings in 14 days · max €22'], 'malformed options ignored, the good one shown');
  await page.click('#wiz-q-ai [data-ai-pick="0"]'); await wait(300);
  eq([await val(page, '#wiz-q-words'), await val(page, '#wiz-q-max'), await val(page, '#wiz-q-min')], ['levis 501', '22', ''], 'max 22 below the default minimum 30: the minimum is cleared');
  await page.close();

  // ---- 3. Fallbacks: nothing found, not available, rate limited. The form keeps working.
  page = await open('plan=free&hunts=0');
  await describe(page, '#wiz-q-ai', 'nomatch thing');
  ok(/No clear match in our listings/.test(await text(page, '#wiz-q-ai')) && (await val(page, '#wiz-q-ai [data-ai-text]')) === 'nomatch thing', 'nothing found: says so and keeps the text');
  await describe(page, '#wiz-q-ai', 'aidown please');
  ok(/not available right now\. Type your search in the box above\./.test(await text(page, '#wiz-q-ai')), 'not available: says so');
  await describe(page, '#wiz-q-ai', 'ailimit please');
  ok(/used the SNYPD AI a lot just now/.test(await text(page, '#wiz-q-ai')), 'rate limited: says so');
  eq(await val(page, '#wiz-q-words'), '', 'fallbacks never touch the search box');
  await page.$eval('#wiz-q-words', e => { e.value = 'levis 501'; e.dispatchEvent(new Event('input', { bubbles: true })); });
  await page.$eval('#wiz-q-max', e => { e.value = '25'; e.dispatchEvent(new Event('input', { bubbles: true })); });
  await page.click('#wiz-q-save'); await wait(1200);
  eq((await hunts(page)).length, 1, 'the plain form still saves a hunt after a fallback');
  await page.close();

  // ---- 4. Filters sheet: the same box fills the quick search and the link
  page = await open('plan=elite');
  const before = (await hunts(page)).length;
  await page.click('#filter-pill'); await wait(600);
  ok(await vis(page, '#fs-q-ai'), 'sheet: SNYPD AI box shown');
  await describe(page, '#fs-q-ai', 'jordan 4 military black');
  await page.$eval('#fs-q-ai [data-ai-pick="0"]', e => e.click()); await wait(300);
  eq([await val(page, '#fs-q-words'), await val(page, '#fs-q-max')], ['jordan 4 military black', '80'], 'sheet: pick fills words + max');
  const link = qOf(await val(page, '#filter-new-url'));
  eq([link.search_text, link.price_to], ['jordan 4 military black', '80'], 'sheet: the link field follows');
  await page.click('#filter-new-save'); await wait(1200);
  h = await hunts(page);
  eq(h.length, before + 1, 'sheet: the hunt saves');
  ok(h.some(x => qOf(x.url).search_text === 'jordan 4 military black' && qOf(x.url).price_to === '80'), 'sheet: saved with the picked words and max');
  await page.close();

  // ---- 5. French on a phone
  page = await open('plan=free&hunts=0&lang=fr', PHONE);
  await wait(500);
  t = await text(page, '#wiz-q-ai');
  ok(/^SNYPD AI/.test(t) && /Décris ce que tu veux avec tes propres mots/.test(t) && /Proposer une recherche/i.test(t), 'French box: ' + t);
  await describe(page, '#wiz-q-ai', 'jordan 4 military black');
  await wait(500);
  t = await text(page, '#wiz-q-ai');
  ok(/209 annonces en 14 jours/.test(t) && /recherche très chargée/.test(t) && /Elle peut se tromper\./.test(t), 'French options: ' + t);
  ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), '390 px: no sideways scroll with the options open');
  await page.close();

  await browser.close(); server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS: ' + passed + ' SNYPD AI hunt-helper checks.');
})().catch(e => { console.error(e); process.exit(1); });
