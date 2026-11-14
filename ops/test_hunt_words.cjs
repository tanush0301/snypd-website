/*
 * Browser test for the hunt words check (Session 70, outreach/43): the REAL dashboard.html in headless Chrome with
 * ops/qa_mock.js. First-hunt wizard (?hunts=0), the Filters sheet, and the card for a saved hunt (?badhunt=list|brands|long).
 *   node ops/test_hunt_words.cjs
 * Checks: one-thing placeholder, panel instead of saving for a list / several brands / typo / long search, a chip saves
 * that one thing, Keep as typed saves the words unchanged, a normal search saves directly, plan line only on Free/Solo,
 * the sheet path, no default minimum at or above a link's own max, the saved-hunt card (chip rewrites the hunt, Undo,
 * Keep it remembered), French, 390 px, no page errors.
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
    await wait(1500);
    return page;
  }
  const hunts = p => p.evaluate(() => window.__qaDB.user_searches.map(h => ({ id: h.id, name: h.search_name, q: new URL(h.vinted_url).searchParams.get('search_text'), url: h.vinted_url })));
  const box = (p, id) => p.evaluate(id => {
    const b = document.getElementById(id);
    return { shown: !!b && b.style.display !== 'none' && b.offsetHeight > 0, text: b ? b.innerText.replace(/\s+/g, ' ').trim() : '',
      chips: b ? [...b.querySelectorAll('[data-hw-pick]')].map(c => c.textContent.trim()) : [], plan: !!(b && b.querySelector('.hw-box__plan')),
      html: b ? b.innerHTML : '' };
  }, id);
  // The max-price nudge (website outreach/62 move 3) follows the words check for a search without a max price.
  // These scenarios test other things, so they answer it with "Start without a max".
  async function passMax(p, id = 'wiz-q-mx') {
    const shown = await p.evaluate(id => { const b = document.getElementById(id); return !!b && b.style.display !== 'none' && b.offsetHeight > 0; }, id);
    if (shown) { await p.click('#' + id + ' [data-mx-act="keep"]'); await wait(900); }
    return shown;
  }
  async function wizType(p, words) {
    await p.evaluate(w => { const i = document.getElementById('wiz-q-words'); i.value = w; i.dispatchEvent(new Event('input')); }, words);
    await p.click('#wiz-q-save');
    await wait(700);
  }
  const modeStep = p => p.evaluate(() => { const s = document.getElementById('wiz-step-mode'); return !!s && s.style.display !== 'none'; });

  // ---- 1. wizard: placeholder + list -> panel, chip saves that one thing
  let page = await open('plan=free&hunts=0');
  eq(await page.$eval('#wiz-q-words', e => e.placeholder), 'e.g. ralph lauren jumper', 'one-thing placeholder (was a comma list)');
  await wizType(page, 'Ralph Lauren, Nike, Adidas');
  let b = await box(page, 'wiz-q-hw');
  ok(b.shown && /This search needs every word in one listing/.test(b.text), 'panel instead of saving: ' + b.text.slice(0, 80));
  ok(/contain all of: Ralph Lauren \+ Nike \+ Adidas\. That finds almost nothing\./.test(b.text), 'explains with the parts');
  eq(b.chips, ['Ralph Lauren', 'Nike', 'Adidas'], 'one chip per part');
  ok(b.plan && /Kickstart watches 2 searches, Pro 5\./.test(b.text), 'plan line on Free');
  eq((await hunts(page)).length, 0, 'nothing saved yet');
  await page.evaluate(() => [...document.querySelectorAll('#wiz-q-hw [data-hw-pick]')].find(c => c.textContent.trim() === 'Nike').click());
  await wait(900);
  ok(await passMax(page), 'a chip without a max price meets the max-price nudge');
  let h = await hunts(page);
  eq([h.length, h[0] && h[0].q, h[0] && h[0].name], [1, 'Nike', 'Nike'], 'chip saved "Nike"');
  ok(await modeStep(page), 'wizard moves on to the alert step');
  ok(!/<script|onerror/i.test(b.html), 'no markup injection');
  await page.close();

  // ---- 2. Keep as typed saves the words unchanged
  page = await open('plan=free&hunts=0');
  await wizType(page, 'ralph loren pull nike');
  b = await box(page, 'wiz-q-hw');
  eq(b.chips, ['Ralph Lauren pull', 'Nike pull'], 'two brands -> each brand with the item, typo fixed');
  await page.click('#wiz-q-hw [data-hw-act="keep"]');
  await wait(900);
  await passMax(page);
  h = await hunts(page);
  eq([h.length, h[0] && h[0].q], [1, 'ralph loren pull nike'], 'kept as typed');
  await page.close();

  // ---- 3. typo, long, normal, editing the words resets the panel
  page = await open('plan=free&hunts=0');
  await wizType(page, 'carhart jacket');
  b = await box(page, 'wiz-q-hw');
  ok(/Check the spelling/.test(b.text) && b.chips[0] === 'Carhartt jacket' && !b.plan, 'typo -> did you mean, no plan line');
  await page.evaluate(() => { const i = document.getElementById('wiz-q-words'); i.value = 'jujutsu kaisen tome 20 a 30'; i.dispatchEvent(new Event('input')); });
  eq((await box(page, 'wiz-q-hw')).shown, false, 'typing again hides the panel');
  await page.click('#wiz-q-save'); await wait(700);
  b = await box(page, 'wiz-q-hw');
  ok(/Long searches find little/.test(b.text) && b.chips.length === 0, 'long -> advice, no chips');
  await page.evaluate(() => { const i = document.getElementById('wiz-q-words'); i.value = 'nike jordan 4'; i.dispatchEvent(new Event('input')); });
  await page.click('#wiz-q-save'); await wait(900);
  await passMax(page);
  h = await hunts(page);
  eq([h.length, h[0] && h[0].q, (await box(page, 'wiz-q-hw')).shown], [1, 'nike jordan 4', false], 'normal search saves (after the max-price nudge)');
  await page.close();

  // ---- 3b. HTML typed into a list part stays text
  page = await open('plan=free&hunts=0');
  await wizType(page, '<img src=x onerror=window.__pwn=1>, nike');
  b = await box(page, 'wiz-q-hw');
  ok(b.shown && !/<img/i.test(b.html) && /&lt;img/.test(b.html) && !(await page.evaluate(() => window.__pwn)), 'list parts are escaped: ' + b.html.slice(0, 160));
  await page.close();

  // ---- 4. Elite: no plan line
  page = await open('plan=elite&hunts=0');
  await wizType(page, 'Ralph Lauren, Nike');
  b = await box(page, 'wiz-q-hw');
  ok(b.shown && !b.plan, 'no plan line on Elite');
  await page.close();

  // ---- 5. Filters sheet: quick search list -> panel, chip saves; pasted link max 30 keeps no min 30
  page = await open('plan=elite');
  await page.click('#filter-pill'); await wait(600);
  await page.evaluate(() => { const i = document.getElementById('fs-q-words'); i.value = 'Ralph Lauren, Nike'; i.dispatchEvent(new Event('input')); });
  const before = (await hunts(page)).length;
  await page.click('#filter-new-save'); await wait(700);
  b = await box(page, 'fs-q-hw');
  ok(b.shown && b.chips.join('|') === 'Ralph Lauren|Nike', 'sheet panel with chips: ' + b.chips.join('|'));
  eq((await hunts(page)).length, before, 'sheet: nothing saved yet');
  await page.evaluate(() => [...document.querySelectorAll('#fs-q-hw [data-hw-pick]')].find(c => c.textContent.trim() === 'Ralph Lauren').click());
  await wait(1000);
  ok(await passMax(page, 'fs-q-mx'), 'sheet: a chip without a max price meets the max-price nudge');
  h = await hunts(page);
  const saved = h.find(x => x.q === 'Ralph Lauren');
  ok(h.length === before + 1 && saved && saved.name === 'Ralph Lauren', 'sheet chip saved "Ralph Lauren": ' + JSON.stringify(h.map(x => x.q)));
  await page.evaluate(() => {
    const u = document.getElementById('filter-new-url'); u.value = 'https://www.vinted.de/catalog?search_text=fred%20perry%20jacke&price_to=30&order=newest_first'; u.dispatchEvent(new Event('input'));
    const m = document.getElementById('filter-new-minprice'); if (m) { m.value = '30'; m.dispatchEvent(new Event('input')); }
  });
  await page.click('#filter-new-save'); await wait(1000);
  h = await hunts(page);
  const fp = h.find(x => x.q === 'fred perry jacke');
  ok(fp && !/price_from=/.test(fp.url), 'default minimum 30 not added to a link with max 30: ' + (fp && fp.url));
  await page.close();

  // ---- 6. saved hunt card: chip rewrites the hunt, Undo restores, Keep it is remembered
  page = await open('plan=free&badhunt=list');
  b = await box(page, 'words-card');
  ok(b.shown && /This search needs every word in one listing/.test(b.text) && /Ralph Lauren, Nike, Adidas/.test(b.text), 'card for the saved list hunt');
  eq(b.chips, ['Ralph Lauren', 'Nike', 'Adidas'], 'card chips');
  ok(/Edit hunt/i.test(b.text) && /Keep it/i.test(b.text), 'card buttons');
  await page.evaluate(() => [...document.querySelectorAll('#words-card [data-hw-pick]')].find(c => c.textContent.trim() === 'Adidas').click());
  await wait(800);
  let bad = (await hunts(page)).find(x => x.id === 'search-bad');
  eq([bad.q, bad.name, /price_to=40/.test(bad.url)], ['Adidas', 'Adidas', true], 'hunt rewritten to "Adidas", rest of the link kept');
  ok(/Done: this hunt now watches Adidas/.test((await box(page, 'words-card')).text), 'done line');
  await page.click('#words-card [data-hw-act="undo"]'); await wait(800);
  bad = (await hunts(page)).find(x => x.id === 'search-bad');
  eq([bad.q, bad.name], ['Ralph Lauren, Nike, Adidas', 'Ralph Lauren, Nike, Adidas'], 'Undo restores words and name');
  await page.close();
  page = await open('plan=free&badhunt=brands');
  b = await box(page, 'words-card');
  eq(b.chips, ['Ralph Lauren pull', 'Nike pull'], 'brands card');
  await page.click('#words-card [data-hw-act="keep"]'); await wait(300);
  eq((await box(page, 'words-card')).shown, false, 'Keep it hides');
  await page.reload({ waitUntil: 'domcontentloaded' }); await wait(1800);
  eq((await box(page, 'words-card')).shown, false, 'Keep it remembered after reload');
  await page.close();
  page = await open('plan=free&badhunt=long');
  b = await box(page, 'words-card');
  ok(b.shown && /Long searches|Try 2 or 3 words/.test(b.text) && b.chips.length === 0, 'long card, no chips');
  await page.close();
  page = await open('plan=free');
  eq((await box(page, 'words-card')).shown, false, 'normal hunts -> no card');
  await page.close();

  // ---- 7. French + phone
  page = await open('plan=free&hunts=0&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  eq(await page.$eval('#wiz-q-words', e => e.placeholder), 'ex. pull ralph lauren', 'French placeholder');
  await wizType(page, 'Ralph Lauren, Nike, Adidas');
  b = await box(page, 'wiz-q-hw');
  ok(/Il faut tous les mots dans une seule annonce/.test(b.text) && /Vinted ne montre que les annonces qui contiennent tous ces mots\s?:/.test(b.text), 'French panel: ' + b.text.slice(0, 160));
  ok(/Kickstart surveille 2 recherches, Pro 5\./.test(b.text) && /Garder tel quel/i.test(b.text), 'French plan line + keep');
  ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, '390 px: no overflow');
  await page.screenshot({ path: path.join(require('os').tmpdir(), 'qa_hunt_words_fr_390.png') });
  await page.close();
  page = await open('plan=free&badhunt=list&lang=fr', { width: 390, height: 844, isMobile: true, hasTouch: true });
  b = await box(page, 'words-card');
  ok(/Il faut tous les mots dans une seule annonce/.test(b.text) && /Modifier la recherche/i.test(b.text), 'French card: ' + b.text.slice(0, 120));
  ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, '390 px card: no overflow');
  await page.evaluate(() => document.getElementById('words-card').scrollIntoView());
  await page.screenshot({ path: path.join(require('os').tmpdir(), 'qa_hunt_words_card_fr_390.png') });
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' hunt-words browser checks pass');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
