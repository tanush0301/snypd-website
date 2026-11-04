/*
 * Browser test for the price check on Feed cards (Session 66, website repo outreach/36): the REAL dashboard.html in headless Chrome,
 * ops/qa_mock.js standing in for Supabase (?pr=1 seeds 9 rated/unrated listings, ?trial=1 a running trial, ?active=1 an active paid plan).
 *   node ops/test_price_check.cjs        (needs Google Chrome at CHROME_PATH or the default Windows path; puppeteer-core is in node_modules)
 * Checks: line text + sub-line, "Pricier than" below 50, gone listing never rated, cheap border, sort best/newest (also for a card that
 * arrives later), cheapest-25% filter + empty note, remembered choice, tiers (Free: one open card + locks, chips go to /plans, a saved
 * filter is ignored; trial / Solo / Elite: every line), no bar without ratings, French, 390 px without horizontal overflow, no page errors.
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
  const u = new URL(req.url, 'http://x'); const p = decodeURIComponent(u.pathname);
  const send = (body, type) => { res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };
  try {
    if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), 'application/javascript');
    if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), 'application/javascript');
    if (p === '/dashboard.html') return send(swap(fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8')), 'text/html; charset=utf-8');
    if (p === '/plans' || p === '/plans.html') return send('<!doctype html><title>plans</title>plans', 'text/html');
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});

let passed = 0;
const ok = (cond, msg) => { assert(cond, msg); passed++; };
const eq = (a, b, msg) => { assert.deepEqual(a, b, msg); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(query, opts) {
    opts = opts || {};
    const page = await browser.newPage();
    await page.setViewport(opts.vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(query + ' pageerror: ' + e.message));
    // every page starts from a clean saved choice (localStorage is shared by all pages of the test origin)
    await page.evaluateOnNewDocument(s => { localStorage.removeItem('snypd_pr_sort'); localStorage.removeItem('snypd_pr_cheap'); for (const k in s) localStorage.setItem(k, s[k]); }, opts.storage || {});
    await page.goto(base + '/dashboard.html?' + query, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
    if (opts.noWait) { await wait(2500); return page; }
    await page.waitForSelector('#list .card[data-pr]', { timeout: 10000 });
    await page.waitForFunction(() => !document.querySelector('#list .card.is-new'), { timeout: 5000 }); // the 1.6 s "just arrived" highlight is mint too
    await wait(200);
    return page;
  }
  const state = page => page.evaluate(() => {
    const vis = e => !!e && getComputedStyle(e).display !== 'none';
    const cards = [...document.querySelectorAll('#list > .card')];
    return {
      free: document.body.classList.contains('pr-free'),
      bar: vis(document.getElementById('pr-bar')),
      order: cards.map(c => c.getAttribute('data-pr') == null ? '-' : c.getAttribute('data-pr')),
      uploaded: cards.map(c => Number(c.getAttribute('data-uploaded-ms'))),
      shownCards: cards.filter(vis).length,
      lines: cards.filter(c => vis(c.querySelector('.pr-line'))).map(c => c.querySelector('.pr-line').innerText.replace(/\s*\n\s*/g, ' | ')),
      locks: cards.filter(c => vis(c.querySelector('.pr-lock'))).length,
      cheapBorders: cards.filter(c => c.hasAttribute('data-pr-cheap') && getComputedStyle(c).borderTopColor === 'rgba(0, 229, 160, 0.45)').length,
      gone: cards.filter(c => c.classList.contains('is-gone')).map(c => !!c.querySelector('.pr-line')),
      chips: [...document.querySelectorAll('#pr-bar .pr-chip')].map(b => b.textContent.trim() + (b.classList.contains('on') ? '*' : '') + (b.classList.contains('is-locked') ? '!' : '')),
      freeLink: vis(document.getElementById('pr-bar-free')),
      empty: vis(document.getElementById('pr-empty')),
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });
  const rated = s => s.order.filter(x => x !== '-');
  const desc = a => a.every((v, i) => i === 0 || a[i - 1] >= v);

  // ---- 1. Elite, English, desktop
  let page = await open('plan=elite&pr=1');
  let s = await state(page);
  eq(s.free, false, 'elite is not on the Free teaser');
  eq(s.bar, true, 'the sort/filter bar shows when cards carry a rating');
  eq(rated(s).length, 5, '5 rated cards (the gone listing rated 90 is not rated on screen)');
  eq(s.lines.length, 5, 'every rated card shows its line on a paid plan');
  ok(s.lines.includes("Cheaper than 82% of this hunt's finds this week | same condition \u00b7 412 finds compared"), 'line + sub-line text: ' + s.lines[0]);
  ok(s.lines.includes("Pricier than 77% of this hunt's finds this week | same condition \u00b7 412 finds compared"), 'below 50 reads "Pricier than (100 - p)%"');
  eq(s.locks, 0, 'no lock chips on a paid plan');
  eq(s.cheapBorders, 2, 'the two cards in the cheapest quarter (82, 80) get the mint border');
  ok(s.gone.length >= 1 && s.gone.every(x => x === false), 'a gone listing never shows a rating');
  ok(desc(s.uploaded), 'default order = newest first (upload time)');
  eq(s.chips, ['Newest*', 'Best price first', 'Cheapest 25% only'], 'chips, Newest selected');

  // sort: best price first
  await page.click('[data-pr-sort="best"]'); await wait(200);
  s = await state(page);
  eq(rated(s), ['82', '80', '68', '58', '23'], 'best price first: rated cards by rating');
  eq(s.order.slice(0, 5), ['82', '80', '68', '58', '23'], 'rated cards come before unrated ones');
  eq(await page.evaluate(() => localStorage.getItem('snypd_pr_sort')), 'best', 'choice remembered');
  // a card that arrives later (the feed prepends new ones) is placed by its rating
  await page.evaluate(() => {
    const c = document.querySelector('#list > .card[data-pr]').cloneNode(true);
    c.setAttribute('data-pr', '95'); c.setAttribute('data-id', '999999'); c.setAttribute('data-uploaded-ms', String(Date.now()));
    document.getElementById('list').insertBefore(c, document.getElementById('list').firstChild);
    const d = document.querySelector('#list > .card:not([data-pr])').cloneNode(true);
    d.setAttribute('data-id', '999998'); d.setAttribute('data-uploaded-ms', String(Date.now() + 1000));
    document.getElementById('list').insertBefore(d, document.getElementById('list').firstChild);
  });
  await wait(200);
  s = await state(page);
  eq(s.order[0], '95', 'a new rated card is moved to its place in best-price order');
  ok(s.order.indexOf('-') > s.order.lastIndexOf('23'), 'a new unrated card goes after the rated ones');
  await page.evaluate(() => { document.querySelector('[data-id="999999"]').remove(); document.querySelector('[data-id="999998"]').remove(); });
  // back to newest
  await page.click('[data-pr-sort="new"]'); await wait(200);
  s = await state(page);
  ok(desc(s.uploaded), 'Newest restores upload-time order');
  // cheapest 25%
  await page.click('#pr-cheap'); await wait(200);
  s = await state(page);
  eq(s.shownCards, 2, 'Cheapest 25% only shows the 2 cards rated 75+');
  eq(s.chips[2], 'Cheapest 25% only*', 'filter chip on');
  eq(s.empty, false, 'no empty note while cheap cards exist');
  await page.evaluate(() => document.querySelectorAll('#list > .card[data-pr-cheap]').forEach(c => c.removeAttribute('data-pr-cheap')));
  await page.evaluate(() => document.getElementById('list').appendChild(document.createElement('span')));
  await wait(200);
  eq((await state(page)).empty, true, 'empty note when the filter hides everything');
  await page.close();

  // ---- 2. remembered filter, then Free with the same saved filter
  page = await open('plan=elite&pr=1', { storage: { snypd_pr_sort: 'best', snypd_pr_cheap: '1' } });
  s = await state(page);
  eq([s.shownCards, rated(s)[0]], [2, '82'], 'saved sort + filter are applied on load');
  await page.close();
  page = await open('plan=free&pr=1', { storage: { snypd_pr_sort: 'best', snypd_pr_cheap: '1' } });
  s = await state(page);
  eq(s.free, true, 'free account after its trial is on the teaser');
  eq(s.lines.length, 1, 'Free: exactly one card shows its line');
  ok(/^Cheaper than 82%/.test(s.lines[0]), 'Free: the open card is the best-rated one');
  eq(s.locks, 4, 'Free: the other rated cards show a lock chip');
  ok(s.shownCards > 2 && desc(s.uploaded), 'Free: a saved sort/filter is ignored (newest order, everything shown)');
  eq(s.chips, ['Newest*', 'Best price first!', 'Cheapest 25% only!'], 'Free: sort and filter chips are locked');
  eq(s.freeLink, true, 'Free: "Solo and up" link in the bar');
  eq(s.cheapBorders, 1, 'Free: only the open card gets the cheap border');
  ok(await page.$eval('#list .card[data-pr] .pr-lock', a => a.getAttribute('href') === '/plans'), 'lock chip links to /plans');
  eq(await page.$eval('#list .card[data-pr]:not(.pr-open) .pr-lock', a => getComputedStyle(a, '::before').content), '"' + String.fromCodePoint(0x1F512) + String.fromCharCode(0xA0) + '"', 'lock icon drawn by CSS before the chip text');
  eq(await page.$eval('[data-pr-sort="best"]', b => getComputedStyle(b, '::after').content), '"' + String.fromCharCode(0xA0) + String.fromCodePoint(0x1F512) + '"', 'lock icon after a locked chip');
  await Promise.all([page.waitForNavigation({ timeout: 5000 }), page.click('[data-pr-sort="best"]')]);
  ok(new URL(page.url()).pathname === '/plans', 'Free: a locked chip opens /plans');
  await page.close();

  // ---- 3. trial and active paid plans see every line
  for (const q of ['plan=free&trial=1&pr=1', 'plan=solo&active=1&pr=1', 'plan=kickstart&active=1&pr=1', 'plan=pro&active=1&pr=1']) {
    page = await open(q);
    s = await state(page);
    eq([s.free, s.lines.length, s.locks], [false, 5, 0], 'every line, no locks for ?' + q);
    await page.close();
  }

  // ---- 4. no ratings -> no bar, no lines
  page = await open('plan=elite&broad=1', { noWait: true }); // 40 stamped listings, none rated
  s = await state(page);
  ok(s.order.length > 0, 'feed rendered without ratings');
  eq([s.bar, s.lines.length, s.locks], [false, 0, 0], 'no bar and no lines when no card is rated');
  await page.close();

  // ---- 5. French + phone width
  page = await open('plan=elite&pr=1&lang=fr', { vp: { width: 390, height: 844, isMobile: true, hasTouch: true } });
  await wait(600);
  s = await state(page);
  ok(s.lines.includes('Moins cher que 82\u00a0% des trouvailles de cette recherche cette semaine | m\u00eame \u00e9tat \u00b7 412 annonces compar\u00e9es'), 'French line: ' + s.lines[0]);
  ok(s.lines.some(l => /^Plus cher que 77\u00a0%/.test(l)), 'French "Pricier than"');
  eq(s.chips, ['Plus r\u00e9centes*', 'Meilleur prix d\u2019abord', 'Les 25\u00a0% les moins ch\u00e8res'], 'French chips');
  ok(s.overflow <= 0, '390 px: no horizontal overflow (' + s.overflow + ')');
  ok(await page.$$eval('#pr-bar .pr-chip', bs => bs.every(b => b.getBoundingClientRect().height >= 32)), '390 px: chips at least 32 px tall');
  await page.close();
  page = await open('plan=free&pr=1&lang=fr', { vp: { width: 390, height: 844, isMobile: true, hasTouch: true } });
  await wait(600);
  ok(await page.$$eval('#list .pr-lock', as => as.some(a => getComputedStyle(a).display !== 'none' && a.innerText.includes('Prix compar\u00e9 \u00b7 d\u00e8s Solo'))), 'French lock chip');
  ok((await state(page)).overflow <= 0, '390 px Free: no horizontal overflow');
  await page.close();

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('all ' + passed + ' price-check checks pass');
})().catch(async e => { console.error('FAIL:', e.message); process.exit(1); });
