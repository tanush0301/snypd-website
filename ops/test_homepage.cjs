/*
 * Homepage v6/v7 (outreach/54, 55): the hero search box and worked example, the price-check demo, the Market board
 * sample, plan order and links, layout at phone and desktop width.
 *   node ops/test_homepage.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Serves the repo's own files; every request to another host is blocked, so nothing reaches production.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(root, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(root, p + '.html');
  if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f)) { res.writeHead(404); return res.end('nope'); }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(fs.readFileSync(f));
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
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1440, height: 900 });
    page.on('pageerror', e => errors.push((q || '/') + ': ' + e.message));
    await page.setRequestInterception(true);
    // Stay on the homepage: a navigation to /signup is recorded and stopped, other hosts are blocked.
    page.__went = null;
    page.on('request', r => {
      const u = r.url();
      if (r.isNavigationRequest() && r.frame() === page.mainFrame() && /\/signup(\?|$)/.test(u)) { page.__went = u.slice(base.length); return r.abort(); }
      return u.startsWith(base) || u.startsWith('data:') ? r.continue() : r.abort();
    });
    await page.goto(base + '/' + (q || ''), { waitUntil: 'domcontentloaded' });
    await wait(900);
    return { page, ctx };
  }
  const went = async page => { for (let i = 0; i < 30 && !page.__went; i++) await wait(100); const u = page.__went; page.__went = null; return u ? new URL(u, base) : null; };
  const params = u => Object.fromEntries(u.searchParams.entries());

  // ---- the search box -------------------------------------------------------------------------------------
  {
    const { page, ctx } = await open('');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup', 'with nothing typed the button is a plain sign-up link');
    await page.type('#qs-words', '  ralph   lauren jumper ');
    await page.type('#qs-max', '25');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup?hunt=ralph+lauren+jumper&max=25', 'words are tidied and carried with the price limit');
    await page.click('#qs-go');
    let u = await went(page);
    ok(u, 'the button goes to sign-up');
    eq(params(u), { hunt: 'ralph lauren jumper', max: '25', from: 'home', entry_basis: 'nav-v1' }, 'sign-up gets the search and the entry-page tag');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('?utm_source=chatgpt.com&r=abcd23');
    await page.type('#qs-words', 'amazon kindle');
    await page.keyboard.press('Enter');
    const u = await went(page);
    ok(u, 'Enter in the box goes to sign-up');
    eq(params(u), { hunt: 'amazon kindle', r: 'abcd23', utm_source: 'chatgpt.com', from: 'home', entry_basis: 'nav-v1' }, 'Enter keeps the campaign tag and the referral code; no price limit, no max');
    await ctx.close();
  }
  {
    const { page, ctx } = await open('');
    await page.type('#qs-max', '40');
    eq(await page.$eval('#qs-go', a => a.getAttribute('href')), '/signup', 'a price limit without words is not sent');
    await page.type('#qs-words', 'x'.repeat(120));
    const href = await page.$eval('#qs-go', a => a.getAttribute('href'));
    eq(new URL(href, base).searchParams.get('hunt').length, 80, 'words stop at 80 characters, the length sign-up accepts');
    await page.$eval('#qs-max', e => { e.value = '-5'; e.dispatchEvent(new Event('input', { bubbles: true })); });
    ok(!/max=/.test(await page.$eval('#qs-go', a => a.getAttribute('href'))), 'a negative price limit is dropped');
    await ctx.close();
  }

  // ---- sign-up reads what the box sends (the address the price guide already uses) ---------------------------
  {
    const auth = fs.readFileSync(path.join(root, 'assets/auth.js'), 'utf8');
    ok(/qs\.get\('hunt'\)/.test(auth) && /qs\.get\('max'\)/.test(auth) && /snypd_hunt_intent/.test(auth), 'assets/auth.js still stores hunt + max for the first-hunt wizard');
  }

  // ---- plan links, counters, no leftovers from v5 --------------------------------------------------------------
  {
    const { page, ctx } = await open('');
    const links = await page.$$eval('a[href^="/signup"]', as => as.map(a => a.getAttribute('href') + ' | ' + a.textContent.trim()));
    for (const want of ['/signup?plan=pass | GET HUNT PASS', '/signup?plan=solo | START SOLO', '/signup?plan=pro | START PRO', '/signup?plan=kickstart | Kickstart', '/signup?plan=elite | Elite']) {
      ok(links.includes(want), 'plan link present: ' + want);
    }
    ok((await page.$$('#stat-listings')).length === 1 && (await page.$$('#stat-listings-asof')).length === 1, 'one listings figure and one date for prepublish.py');
    const text = await page.evaluate(() => document.body.innerText);
    ok(!/outnumbered|spots left|SEE HOW IT WORKS/i.test(text), 'the v5 hero and founding line are gone');
    ok(/SAMPLE/.test(text), 'the example alerts are labelled as samples');
    const main = await page.$eval('#hero-alert-main', e => e.innerText.replace(/\s+/g, ' '));
    ok(/Cheaper than 76% of this week's finds . Jordan 1 Low Travis Scott . €180/.test(main), 'the worked example: the Travis Scott alert in the wording a real alert uses: ' + main);
    ok(/62 listings in the same condition this week/.test(await page.$eval('#hero-ex', e => e.innerText)), 'the example says what the price line is built on');
    // Pro leads the plans; Free sits next to it; the one-item and one-search plans follow
    const order = await page.$$eval('#pricing .hp-plan', ps => ps.map(p => p.querySelector('.name').textContent.trim()));
    eq(order, ['PRO', 'FREE', 'HUNT PASS', 'SOLO'], 'plan order: Pro first');
    ok(await page.$eval('#price-pro a.hp-btn', a => !a.classList.contains('ghost') && a.getAttribute('href') === '/signup?plan=pro'), 'the Pro card has the solid button');
    ok(/Check a price for any item is Pro and Elite only/.test(await page.$eval('#price-free', e => e.innerText)), 'the Free card says what the trial does not include');
    ok(!/\b(instant|real-time|fastest|undetectable|sold prices)\b/i.test(text), 'no banned claim on the page');
    const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
    ok(!/demo-steps|renderDemo|Homepage v5/.test(html), 'the walkthrough code is gone');
    for (const m of html.matchAll(/<img[^>]+src="(\/[^"]+)"/g)) ok(fs.existsSync(path.join(root, m[1])), 'image exists: ' + m[1]);
    await ctx.close();
  }

  // ---- "Check a price" demo: real numbers from the public price index -----------------------------------------
  {
    const index = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/price-index.json'), 'utf8'));
    const byId = Object.fromEntries(index.items.map(i => [i.id, i]));
    const euro = c => '€' + (c % 100 === 0 ? String(c / 100) : (c / 100).toFixed(2)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    // without script: the first item's numbers are in the HTML and equal the index
    const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
    const stat = id => { const m = html.match(new RegExp('id="' + id + '"[^>]*>([^<]*)<')); return m ? m[1].replace(/&euro;/g, '€') : null; };
    const d0 = byId[(html.match(/id="pc-res" data-id="([a-z0-9-]+)"/) || [])[1]];
    ok(d0, 'the item written into the HTML exists in the price index');
    eq([stat('pc-lo'), stat('pc-mid'), stat('pc-hi')], [euro(d0.p25), euro(d0.typical), euro(d0.p75)], 'HTML numbers of the first item equal the index (no script needed)');
    eq(stat('pc-pay'), euro(Math.round(d0.typical * 0.6)), 'HTML "pay at most" is the typical price less the 40% margin');

    const { page, ctx } = await open('');
    await page.waitForFunction(() => !document.getElementById('pc-item').disabled, { timeout: 8000 });
    eq(await page.$$eval('#pc-item option', o => o.length), index.items.length, 'every item of the index can be picked');
    const read = () => page.evaluate(() => ({ name: document.getElementById('pc-name').textContent, lo: document.getElementById('pc-lo').textContent, mid: document.getElementById('pc-mid').textContent,
      hi: document.getElementById('pc-hi').textContent, pay: document.getElementById('pc-pay').textContent, meta: document.getElementById('pc-meta').textContent,
      alert: document.getElementById('pc-alert').getAttribute('href'), alertText: document.getElementById('pc-alert').innerText.replace(/\s+/g, ' '), more: document.getElementById('pc-more').getAttribute('href') }));
    const it = byId['adidas-samba'];
    await page.select('#pc-item', 'adidas-samba'); await wait(700);
    let r = await read();
    eq([r.name, r.lo, r.mid, r.hi], [it.name.en, euro(it.p25), euro(it.typical), euro(it.p75)], 'picking an item shows its quick-sale, typical and patient price');
    eq(r.pay, euro(Math.round(it.typical * 0.6)), 'pay at most = typical less 40%');
    ok(r.meta.includes(it.n.toLocaleString('en-US') + ' listings') && /vinted\.be/.test(r.meta) && /2026/.test(r.meta), 'it says how many listings, where and when: ' + r.meta);
    eq(r.alert, '/signup?hunt=adidas+samba&max=' + Math.floor(it.p25 / 100), 'the alert button carries the search and the quick-sale price as the limit');
    ok(/ALERT ME UNDER €\d/.test(r.alertText), 'the button reads with a space before the price: ' + r.alertText);
    eq(r.more, it.url.en, 'the second button opens that item in the price guide');
    await page.$eval('#pc-margin', e => { e.value = '50'; e.dispatchEvent(new Event('input', { bubbles: true })); }); await wait(700);
    eq((await read()).pay, euro(Math.round(it.typical * 0.5)), 'changing the margin changes "pay at most"');
    await page.$eval('#pc-margin', e => { e.value = '999'; e.dispatchEvent(new Event('input', { bubbles: true })); }); await wait(700);
    eq((await read()).pay, euro(Math.round(it.typical * 0.1)), 'a silly margin is held at 90%');
    await page.click('#pc-chips button[data-id="nike-dunk-low"]'); await wait(700);
    eq((await read()).name, byId['nike-dunk-low'].name.en, 'the quick-pick buttons work');
    await page.click('#pc-alert');
    const u = await went(page);
    eq(params(u), { hunt: 'nike dunk low', max: String(Math.floor(byId['nike-dunk-low'].p25 / 100)), from: 'home', entry_basis: 'nav-v1' }, 'the alert button goes to sign-up with the search, the limit and the entry-page tag');
    await ctx.close();
  }

  // ---- Market board sample: dated, from the data file; the chart line draws once --------------------------------
  {
    const sample = JSON.parse(fs.readFileSync(path.join(root, 'ops/seo/data/home-market-sample.json'), 'utf8'));
    const last = sample.chart.series[sample.chart.series.length - 1];
    const { page, ctx } = await open('');
    const m = await page.evaluate(() => { const b = document.getElementById('mb-sample'); return { date: b.getAttribute('data-date'),
      lists: [...b.querySelectorAll('ul')].map(u => [...u.querySelectorAll('li')].map(li => li.innerText.replace(/\s+/g, ' ').trim())),
      tiles: [...b.querySelectorAll('.hp-chart-tiles b')].map(e => e.textContent), top: b.querySelector('.hp-mb-top').innerText, line: (b.querySelector('svg .line').getAttribute('d') || '').split('L').length,
      wait: b.querySelector('.hp-chart').classList.contains('wait') }; });
    eq(m.date, sample.board.date, 'the board sample carries its date');
    ok(m.top.includes('11 Nov 2026') || m.top.includes(String(Number(sample.board.date.slice(8)))), 'the date is printed on the page: ' + m.top);
    eq([m.lists[0].length, m.lists[1].length], [sample.board.rising.length, sample.board.falling.length], 'rising and falling rows as in the data file');
    ok(m.lists[1][0].startsWith(sample.board.falling[0].name) && /−20%/.test(m.lists[1][0]), 'falling rows use a real minus sign: ' + m.lists[1][0]);
    eq(m.tiles[0], '€' + (last[1] / 100), 'chart tile "typical now" equals the last day of the series');
    eq(m.line, sample.chart.series.length, 'the line has one point per day of the series');
    ok(m.wait, 'before it is on screen the line waits');
    await page.$eval('.hp-chart', e => e.scrollIntoView({ block: 'center' })); await wait(900);
    ok(await page.$eval('.hp-chart', e => e.classList.contains('draw') && !e.classList.contains('wait')), 'the line draws once the chart is on screen');
    await ctx.close();
    // reduced motion: nothing waits, nothing animates
    const c2 = await browser.createBrowserContext(); const p2 = await c2.newPage();
    await p2.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await p2.setRequestInterception(true); p2.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:')) ? r.continue() : r.abort());
    await p2.goto(base + '/', { waitUntil: 'domcontentloaded' }); await wait(900);
    const rm = await p2.evaluate(() => ({ wait: document.querySelector('.hp-chart').classList.contains('wait'), anim: getComputedStyle(document.getElementById('hero-alert-main')).animationName,
      mark: getComputedStyle(document.getElementById('hero-ex-mark')).animationName }));
    eq(rm, { wait: false, anim: 'none', mark: 'none' }, 'with reduced motion the alert, the marker and the chart line do not move');
    await c2.close();
  }

  // ---- layout: no sideways scroll; on a phone the button is on the first screen ---------------------------------
  for (const [name, vp] of [['phone', { width: 390, height: 844, isMobile: true, hasTouch: true }], ['small phone', { width: 320, height: 640, isMobile: true, hasTouch: true }], ['tablet', { width: 820, height: 1100 }], ['desktop', { width: 1440, height: 900 }]]) {
    const { page, ctx } = await open('', vp);
    const m = await page.evaluate(() => {
      const r = id => document.getElementById(id).getBoundingClientRect();
      return { sw: document.documentElement.scrollWidth, iw: innerWidth, go: Math.round(r('qs-go').bottom), h1: Math.round(r('qs-words').top), ih: innerHeight,
        tap: [...document.querySelectorAll('.hp-btn, #qs-words, #qs-max, #pc-item, #pc-margin, #pc-chips button')].filter(e => e.getClientRects().length).map(e => Math.round(e.getBoundingClientRect().height)) };
    });
    ok(m.sw <= m.iw + 1, name + ': no sideways scroll (' + m.sw + ' vs ' + m.iw + ')');
    ok(m.go <= m.ih, name + ': the "Watch it for me" button is on the first screen (' + m.go + ' of ' + m.ih + ')');
    ok(Math.min(...m.tap) >= 44, name + ': buttons and fields are at least 44 px tall');
    await ctx.close();
  }
  // sticky bar on a phone appears once the hero button has scrolled away
  {
    const { page, ctx } = await open('', { width: 390, height: 844, isMobile: true, hasTouch: true });
    ok(await page.$eval('#sticky-bar', e => e.hidden), 'phone: no sticky bar at the top of the page');
    await page.evaluate(() => scrollTo(0, 1600)); await wait(400);
    ok(!(await page.$eval('#sticky-bar', e => e.hidden)), 'phone: the sticky sign-up bar shows after the hero');
    await ctx.close();
  }

  await browser.close(); server.close();
  eq(errors, [], 'no page error');
  console.log(`PASS: ${passed} homepage checks.`);
})().catch(e => { console.error(e); process.exit(1); });
