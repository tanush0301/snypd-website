/*
 * Browser test for the design-check gaps 1-6 (outreach/38-stock-design-check-2026-11-05.md in the website folder): the REAL dashboard.html +
 * assets/stock*.js in headless Chrome, ops/qa_mock.js + ops/stock_engine.js standing in for Supabase, the frozen design dataset, today = 27 Oct 2026.
 *   node ops/test_stock_design.cjs
 * 1 phone item cards (full title, price on the right, 16 px gutter)  2 write off / mark returned (reason buttons, "What this changes" numbers)
 * 3 item detail (tags, timeline, money, closed edit form)  4 display font + green profit  5 Items values (buy price, "--" when not on sale)
 * 6 Quick add condition buttons + Manage categories (rename, hide, show, add; Enter never submits the sheet). EN + FR.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.woff2': 'font/woff2' };
const swap = html => html.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), MIME['.js']);
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), MIME['.js']);
    if (p === '/acceptance-fixture.json') return send(fs.readFileSync(path.join(root, 'ops/stock/acceptance-fixture.json')), MIME['.json']);
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const H0 = '5c8c8530-a343-cd02-1db8-33fc7b07df5b';   // design h0: Carhartt WIP Detroit jacket, brown, L. Not listed, buy 49.00 + extra 4.40, old list price 88.00
const H54 = 'f2746a6a-e221-9c43-6122-221fd0982af6';  // design h54: reserved, bought 29 Sep, listed 30 Sep, reserved 26 Oct, buy 26.50, list 92.00

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(lang, vp) {
    const page = await browser.newPage(); await page.setViewport(vp || { width: 1440, height: 900 });
    page.on('pageerror', e => errors.push(lang + ' pageerror: ' + e.message));
    await page.goto(base + '/dashboard.html?boot=1&plan=elite&stock=all&stock_seed=acceptance&stock_today=2026-10-27&stock_claims=0&lang=' + lang, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => { const t = document.getElementById('view-tab-stock'); return t && getComputedStyle(t).display !== 'none'; }, { timeout: 10000 });
    await page.evaluate(() => document.getElementById('view-tab-stock').click());
    await page.waitForSelector('#st-hero-net', { timeout: 10000 }); await wait(500);
    page.act = async (a, extra) => { await page.evaluate((a, extra) => { const e = document.querySelector('#stock-panel [data-act="' + a + '"]' + (extra || '')); if (!e) throw new Error('no control ' + a + (extra || '')); e.click(); }, a, extra); await wait(350); };
    page.txt = s => page.$eval(s, e => e.innerText.replace(/\s+/g, ' ').trim());
    page.items = async () => { await page.evaluate(() => document.querySelector('#stock-panel .st-navb[data-view="items"]').click()); await page.waitForSelector('#stock-panel .st-row', { timeout: 8000 }); await wait(400); };
    page.find = async q => { await page.$eval('#st-q', (e, q) => { e.value = q; e.dispatchEvent(new Event('input', { bubbles: true })); }, q); await wait(900); };
    page.row = id => page.$eval('#stock-panel .st-row[data-id="' + id + '"]', e => ({ cost: e.querySelector('.c-cost').innerText.trim(), pop: e.querySelector('.c-pop').innerText.trim() }));
    page.openItem = async id => { await page.evaluate(id => document.querySelector('#stock-panel .st-row[data-id="' + id + '"]').click(), id); await page.waitForSelector('.st-sheet #st-dmoney', { timeout: 5000 }); await wait(400); };
    return page;
  }

  // ---- 4. display font + green profit
  let pg = await open('en');
  eq(await pg.$eval('#st-hero-net', e => [e.textContent.trim(), e.classList.contains('st-pos'), /Cabinet Grotesk/.test(getComputedStyle(e).fontFamily)]), ['€612.40', true, true], 'gap 4: hero net profit €612.40 in green, Cabinet Grotesk first in the font stack');
  ok(await pg.evaluate(async () => { await document.fonts.ready; return [...document.fonts].some(f => f.family.replace(/["']/g, '') === 'Cabinet Grotesk' && f.weight === '900' && f.status === 'loaded'); }), 'gap 4: the self-hosted Cabinet Grotesk Black face loaded');

  // ---- 5. Items values (design Ca): BOUGHT = buy price, PRICE "--" for items not on sale
  await pg.items();
  await pg.find('Detroit jacket, brown');
  eq(await pg.row(H0), { cost: '€49.00', pop: '--' }, 'gap 5: a not-listed item shows its buy price (not 53.40 with extras) and "--" (not its old 88.00 list price)');
  eq(await pg.row(H54), { cost: '€26.50', pop: '€92.00' }, 'gap 5: a reserved item keeps its list price');

  // ---- 3. item detail (design Cb)
  await pg.openItem(H54);
  eq(await pg.$$eval('.st-sheet .st-dtags .st-tag', t => t.map(x => x.innerText.trim().toUpperCase())), ['RESERVED', 'GOOD', 'OUTERWEAR'], 'gap 3: tags = status, condition, category');
  eq(await pg.txt('#st-dmeta'), 'Carhartt WIP · M · Vinted', 'gap 3: brand · size · platform');
  eq(await pg.$$eval('#st-steps li', l => l.map(x => [x.querySelector('b').innerText.trim().toUpperCase(), (x.querySelector('em') || { innerText: '' }).innerText.trim(), x.querySelector('span:last-child').innerText.trim(), x.className])),
    [['BOUGHT', '', '29 Sept 2026', 'on'], ['LISTED', '+1d', '30 Sept 2026', 'on'], ['RESERVED', '+26d', '26 Oct 2026', 'on'], ['SOLD', '--', '--', '']], 'gap 3: timeline bought -> listed +1d -> reserved +26d -> sold --');
  eq(await pg.$$eval('#st-dmoney tr', r => r.map(x => x.innerText.replace(/\s+/g, ' ').trim())), ['Buy price €26.50', 'Extra costs --', 'List price €92.00', 'Sold price --', 'Platform fee --', 'Net profit --'], 'gap 3: money table');
  eq(await pg.$eval('#st-editbox', e => e.open), false, 'gap 3: the edit form starts closed');
  eq(await pg.$$eval('.st-sheet-ft .st-btn', b => b.map(x => x.innerText.trim().toUpperCase())), ['CLOSE', 'MARK SOLD'], 'gap 3: one primary action, Mark sold');
  await pg.waitForFunction(() => document.querySelectorAll('#st-tl li.bought').length === 1, { timeout: 5000 });
  ok(true, 'gap 3: the history list still loads');
  await pg.act('close');

  // ---- 2. write off (design Ib): reasons as 4 buttons, real numbers
  await pg.openItem(H54); await pg.act('do', '[data-do="wo"]');
  eq(await pg.$$eval('.st-reasons [data-act="wo-reason"]', b => b.map(x => x.innerText.trim() + (x.getAttribute('aria-checked') === 'true' ? '*' : ''))), ['Lost*', 'Damaged', 'Unsellable', 'Given away'], 'gap 2: 4 reason buttons, Lost first');
  await pg.act('wo-reason', '[data-r="given_away"]');
  eq(await pg.$eval('#sf-reason', e => e.value), 'given_away', 'gap 2: a reason button sets the value');
  eq(await pg.$$eval('#st-effect li', l => l.map(x => x.innerText.trim())), [
    '€26.50 counted as a loss on 27 Oct 2026, on its own Write-offs line.',
    'Leaves In stock: held 58 → 57, cash tied up €1,124.50 → €1,098.00.',
    'Leaves aging and the Today lanes.',
    'Net profit, last 30 days: €612.40 → €585.90, write-offs included and labelled.'], 'gap 2: "What this changes" with the dataset numbers');
  await pg.$eval('#sf-date', e => { e.value = '2026-09-01'; e.dispatchEvent(new Event('input', { bubbles: true })); }); await wait(150);
  ok(!/Net profit/.test(await pg.txt('#st-effect')), 'gap 2: a date outside the last 30 days does not claim to move the 30-day net');
  await pg.act('close');
  // Mark returned on the dataset's newest sale
  const sold = await pg.evaluate(() => { const s = window.__qaStock.state.items.filter(i => i.status === 'sold' && !i.deleted_at && i.buy_cents != null && i.sold_cents != null).sort((a, b) => a.sold_on < b.sold_on ? 1 : -1)[0]; return { id: s.id, title: s.title, cost: s.buy_cents + (s.extra_cents || 0), sold: s.sold_cents }; });
  await pg.act('chip', '[data-status="sold"]'); await wait(500); await pg.find(sold.title); await pg.openItem(sold.id); await pg.act('do', '[data-do="returned"]');
  const money = c => '€' + (Math.abs(c) / 100).toLocaleString('en-GB', { minimumFractionDigits: 2 });
  const rev = sold.cost - sold.sold, net = 61240 + rev, sign = c => (c < 0 ? '−' : '+') + money(c);
  { const L = await pg.$$eval('#st-effect li', l => l.map(x => x.innerText.trim()));
    eq([L[0], L[L.length - 1]], ['On 27 Oct 2026: revenue −' + money(sold.sold) + ', profit ' + sign(rev) + '.', 'Net profit, last 30 days: €612.40 → ' + money(net) + ', write-offs included and labelled.'], 'gap 2: return effect = reversal (cost - refund) and the new 30-day net'); }
  eq(await pg.$eval('#sf-reason-wrap', e => getComputedStyle(e).display), 'none', 'gap 2: no reason while it goes back to stock');
  await pg.evaluate(() => document.querySelector('.st-dest input[value="wo"]').click()); await wait(200);
  eq(await pg.$eval('#sf-reason-wrap', e => getComputedStyle(e).display !== 'none' && e.querySelectorAll('[data-act="wo-reason"]').length), 4, 'gap 2: "Write off instead" shows the 4 reason buttons');
  ok((await pg.txt('#st-effect')).includes('Net profit, last 30 days: €612.40 → ' + money(net - sold.cost)), 'gap 2: written off after the return also takes the cost off the net');
  await pg.act('close');

  // ---- 6. Quick add: condition buttons + Manage categories
  await pg.act('add');
  eq(await pg.$$eval('[data-act="cond-pick"]', b => b.map(x => x.innerText.trim())), ['New, with tag', 'New, no tag', 'Very good', 'Good', 'Satisfactory'], 'gap 6: 5 condition buttons, best to worst');
  await pg.act('cond-pick', '[data-c="very_good"]'); eq(await pg.$eval('#sf-condition', e => e.value), 'very_good', 'gap 6: a button sets the condition');
  await pg.act('cond-clear'); eq(await pg.$eval('#sf-condition', e => e.value), '', 'gap 6: Clear empties it');
  ok(await pg.$$eval('[data-act="cond-pick"]', b => b.every(x => x.getAttribute('aria-checked') === 'false')), 'gap 6: and unpresses every button');
  await pg.act('cat-manage');
  ok(await pg.$('#st-catman .st-catline') !== null && /Rename, add or hide/.test(await pg.txt('#st-catman')), 'gap 6: Manage categories opens the panel');
  await pg.$eval('#st-catman [data-cat="tops"]', e => { e.value = 'Hoodies'; e.dispatchEvent(new Event('change', { bubbles: true })); }); await wait(300);
  eq(await pg.evaluate(() => [window.__qaStock.state.categories.find(c => c.key === 'tops').name, [...document.querySelectorAll('#sf-category option')].find(o => o.value === 'tops').textContent]), ['Hoodies', 'Hoodies'], 'gap 6: rename saves to the account and relabels the select');
  await pg.act('cat-hide', '[data-key="shoes"]');
  eq(await pg.evaluate(() => [window.__qaStock.state.categories.find(c => c.key === 'shoes').hidden, !![...document.querySelectorAll('#sf-category option')].find(o => o.value === 'shoes')]), [true, false], 'gap 6: hide saves and leaves the select');
  await pg.act('cat-hide', '[data-key="shoes"]');
  eq(await pg.evaluate(() => window.__qaStock.state.categories.find(c => c.key === 'shoes').hidden), false, 'gap 6: show brings it back');
  await pg.type('#st-catnew', 'Vintage tees'); await pg.focus('#st-catnew'); await pg.keyboard.press('Enter'); await wait(500);
  eq(await pg.evaluate(() => [!!document.querySelector('.st-sheet'), (window.__qaStock.state.categories.find(c => c.name === 'Vintage tees') || {}).key, document.getElementById('sf-category').value]), [true, 'c-vintage-tees', 'c-vintage-tees'], 'gap 6: Enter adds the category (sheet stays open) and selects it');
  await pg.$eval('#st-catman [data-cat="tops"]', e => { e.value = ' '; e.dispatchEvent(new Event('change', { bubbles: true })); }); await wait(200);
  eq(await pg.evaluate(() => window.__qaStock.state.categories.find(c => c.key === 'tops').name), 'Hoodies', 'gap 6: an empty rename is ignored');
  await pg.act('cond-pick', '[data-c="good"]'); await pg.type('#sf-title', 'Design check tee'); await pg.type('#sf-buy', '7');
  await pg.act('submit'); await wait(500);
  eq(await pg.evaluate(() => { const i = window.__qaStock.state.items.find(x => x.title === 'Design check tee'); return i && [i.condition, i.category, i.buy_cents]; }), ['good', 'c-vintage-tees', 700], 'gap 6: the item is saved with the picked condition and the new category');
  await pg.close();

  // ---- 1. phone cards (390): full title, price on the right, 16 px gutter; edit sheet keeps the condition buttons
  pg = await open('en', { width: 390, height: 844 });
  await pg.items();
  { const r = await pg.$eval('#stock-panel .st-row[data-id]', e => { const b = e.querySelector('.st-item b'), rb = e.getBoundingClientRect(), pop = e.querySelector('.c-pop'); return { x: Math.round(rb.left), right: Math.round(window.innerWidth - rb.right), cut: b.scrollHeight > b.clientHeight + 1 || b.scrollWidth > b.clientWidth + 1, ws: getComputedStyle(b).whiteSpace, pop: getComputedStyle(pop).display !== 'none' && pop.getBoundingClientRect().right > rb.right - 40 }; });
    eq([r.x, r.right, r.cut, r.pop], [16, 16, false, true], 'gap 1: 16 px gutters, title not cut, price on the right: ' + JSON.stringify(r)); eq(r.ws, 'normal', 'gap 1: titles wrap instead of an ellipsis'); }
  { const cut = await pg.$$eval('#stock-panel .st-row .st-item b', l => l.filter(b => b.scrollHeight > b.clientHeight + 1).length); eq(cut, 0, 'gap 1: no title on the page is cut'); }
  eq(await pg.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), 0, 'gap 1: no horizontal page scroll at 390');
  await pg.find('Detroit jacket, brown, M'); await pg.openItem(H54);
  ok(await pg.$$eval('#stock-panel .st-sheet button, #stock-panel .st-sheet summary', b => b.filter(x => x.offsetParent !== null).every(x => x.getBoundingClientRect().height >= 44)), 'phone: every visible control in the detail is at least 44 px tall');
  await pg.evaluate(() => { document.getElementById('st-editbox').open = true; }); await wait(150);
  eq(await pg.$eval('#sf-condition', e => e.value), 'good', 'detail edit form: condition buttons start on the item\'s condition');
  await pg.act('cond-pick', '[data-c="very_good"]'); await pg.act('save-detail'); await wait(400);
  eq(await pg.evaluate(id => window.__qaStock.state.items.find(i => i.id === id).condition, H54), 'very_good', 'detail edit form: a new condition saves');
  await pg.close();

  // ---- French
  pg = await open('fr');
  await pg.items(); await pg.find('Detroit jacket, brown, M'); await pg.openItem(H54);
  eq(await pg.$$eval('#st-steps b', b => b.map(x => x.innerText.trim().toUpperCase())), ['ACHETÉ', 'EN VENTE', 'RÉSERVÉ', 'VENDU'], 'FR: timeline');
  ok((await pg.txt('#st-steps')).includes('+26 j') && /Argent/i.test(await pg.txt('.st-sheet')) && /Modifier les détails/i.test(await pg.txt('#st-editbox')), 'FR: +26 j, Argent, Modifier les détails');
  await pg.act('close'); await pg.act('add');
  ok(/Gérer les catégories/i.test(await pg.txt('.st-sheet')) && /État · facultatif/i.test(await pg.txt('.st-sheet')) && /Effacer/.test(await pg.txt('.st-condhd')), 'FR: Quick add condition + categories');
  await pg.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' design-gap checks (phone cards, write off / return effect, item detail, display font, Items values, condition buttons + Manage categories, EN/FR)');
})().catch(e => { console.error(e); process.exit(1); });
