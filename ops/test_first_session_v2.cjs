/*
 * First-session v2, first search (20 Nov 2026): the REAL dashboard.html in headless Chrome with ops/qa_mock.js.
 *   node ops/test_first_session_v2.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Checks: on a phone (390x664, what a phone browser really shows) the Start button is on the first screen, no minimum
 * price is pre-filled, the wizard has two steps, the SNYPD AI box sits below the Start button, a saved first search goes
 * straight to the alerts step (no alert-style step), the saved link carries no price_from, French step labels, no
 * sideways scroll, no page errors. No network: the mock answers every call. SHOTS=<dir> saves screenshots.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const SHOTS = process.env.SHOTS || '';
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
const PHONE = { width: 390, height: 664, isMobile: true, hasTouch: true, deviceScaleFactor: 2 };

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
    await page.setViewport(vp || PHONE);
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(1500);
    return page;
  }
  const shot = async (p, name) => { if (SHOTS) await p.screenshot({ path: path.join(SHOTS, name + '.png') }); };
  const vis = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.style.display !== 'none' && !e.hidden && e.getClientRects().length > 0; }, sel);
  const box = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return { top: Math.round(r.top), bottom: Math.round(r.bottom) }; }, sel);
  const tc = (p, sel) => p.evaluate(sel => { const e = document.querySelector(sel); return e ? e.textContent.replace(/\s+/g, ' ').trim() : ''; }, sel);
  const hunts = p => p.evaluate(() => window.__qaDB.user_searches.map(h => h.vinted_url));
  const noOverflow = p => p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

  // ---- 1. Phone, English: the first screen of the wizard
  let page = await open('plan=free&hunts=0');
  ok(await vis(page, '#wiz-step-1'), 'the wizard opens for an account without a search');
  eq(await tc(page, '#wiz-step-1 .wiz-eyebrow'), 'Step 1 of 2', 'two steps');
  eq(await page.$eval('#wiz-q-min', e => e.value), '', 'no minimum price is pre-filled');
  const save = await box(page, '#wiz-q-save');
  ok(save && save.top >= 0 && save.bottom <= 664, 'the Start button is on the first phone screen: ' + JSON.stringify(save));
  const ai = await box(page, '#wiz-q-ai');
  ok(ai && ai.top >= save.bottom, 'the SNYPD AI box sits below the Start button: ' + JSON.stringify(ai));
  ok(await vis(page, '#wiz-build-own'), 'the Vinted-link route is still offered');
  ok(await noOverflow(page), 'no sideways scroll');
  await shot(page, 'wizard-step1-390');

  // country change: still no minimum
  await page.select('#wiz-q-site', 'vinted.co.uk'); await wait(300);
  eq(await page.$eval('#wiz-q-min', e => e.value), '', 'no minimum after a country change either');

  // ---- 2. Save with a max: straight to the alerts step, no price_from in the link
  await page.select('#wiz-q-site', 'vinted.be'); await wait(300);
  await page.type('#wiz-q-words', 'ralph lauren jumper');
  await page.type('#wiz-q-max', '30');
  await page.click('#wiz-q-save'); await wait(1500);
  const h = await hunts(page);
  eq(h.length, 1, 'one search saved');
  const q = Object.fromEntries(new URL(h[0]).searchParams);
  eq([q.search_text, q.price_to, q.price_from], ['ralph lauren jumper', '30', undefined], 'saved with the max and without a minimum');
  ok(await vis(page, '#wiz-step-2'), 'the alerts step is shown straight after saving');
  ok(!(await vis(page, '#wiz-step-mode')), 'no alert-style step');
  eq(await tc(page, '#wiz-step-2 .wiz-eyebrow'), 'Step 2 / 2', 'alerts step is step 2 of 2');
  ok(await noOverflow(page), 'no sideways scroll on the alerts step');
  ok(await vis(page, '#wiz-heard'), 'the "How did you find SNYPD?" question is asked on the alerts step');
  await page.select('#wiz-heard-sel', 'chatgpt'); await wait(600);
  const heard = await page.evaluate(() => (window.__qa_auth_updates || []).map(u => u && u.data && u.data.heard_from).filter(Boolean));
  eq(heard, ['chatgpt'], 'the answer is saved on the account');
  await shot(page, 'wizard-step2-390');
  await page.close();

  // ---- 3. A minimum typed by the user is still used
  page = await open('plan=free&hunts=0');
  await page.type('#wiz-q-words', 'nike tech fleece');
  await page.type('#wiz-q-max', '60');
  await page.type('#wiz-q-min', '20');
  await page.click('#wiz-q-save'); await wait(1500);
  const q2 = Object.fromEntries(new URL((await hunts(page))[0]).searchParams);
  eq([q2.price_from, q2.price_to], ['20', '60'], 'a typed minimum is saved');
  await page.close();

  // ---- 4. French
  page = await open('plan=free&hunts=0&lang=fr');
  await wait(600);
  const fr1 = await tc(page, '#wiz-step-1 .wiz-eyebrow');
  ok(/tape 1 sur 2/.test(fr1), 'French step label: ' + fr1);
  const saveFr = await box(page, '#wiz-q-save');
  ok(saveFr && saveFr.bottom <= 664, 'the Start button is on the first phone screen in French: ' + JSON.stringify(saveFr));
  ok(await noOverflow(page), 'no sideways scroll in French');
  await shot(page, 'wizard-step1-390-fr');
  await page.type('#wiz-q-words', 'pull ralph lauren');
  await page.type('#wiz-q-max', '30');
  await page.click('#wiz-q-save'); await wait(1500);
  const fr2 = await tc(page, '#wiz-step-2 .wiz-eyebrow');
  ok(await vis(page, '#wiz-step-2') && /tape 2 \/ 2/.test(fr2), 'French alerts step label: ' + fr2);
  await page.close();

  // ---- 5. Small phone (320x568) and desktop
  page = await open('plan=free&hunts=0', { width: 320, height: 568, isMobile: true, hasTouch: true });
  ok(await noOverflow(page), 'no sideways scroll at 320 px');
  ok(await vis(page, '#wiz-q-save'), 'Start button present at 320 px');
  await shot(page, 'wizard-step1-320');
  await page.close();
  page = await open('plan=free&hunts=0', { width: 1440, height: 900 });
  const saveD = await box(page, '#wiz-q-save');
  ok(saveD && saveD.bottom <= 900, 'the Start button is on the first screen on a computer: ' + JSON.stringify(saveD));
  await shot(page, 'wizard-step1-1440');
  await page.close();

  // ---- 6. First dashboard: one main button at a time (the plans banner's button is quiet while the alerts card shows)
  page = await open('plan=free&hunts=1&boot=1&joined=fresh');
  await wait(2500);
  const bg = sel => page.$eval(sel, e => getComputedStyle(e).backgroundColor);
  const PURPLE = 'rgb(162, 0, 255)';
  ok(await vis(page, '#alerts-setup-card') && await vis(page, '#elite-banner'), 'alerts card and plans banner both show for a new account with a search');
  eq(await bg('#alerts-setup-resume'), PURPLE, '"Set up alerts" is the main button');
  ok((await bg('#elite-banner > a')) !== PURPLE, '"See plans" is quiet while the alerts card shows: ' + await bg('#elite-banner > a'));
  ok(await vis(page, '#elite-banner > a'), '"See plans" is still there');
  await page.click('#alerts-setup-later'); await wait(500);
  ok(!(await vis(page, '#alerts-setup-card')), 'the alerts card closes on "Not now"');
  eq(await bg('#elite-banner > a'), PURPLE, '"See plans" is the main button again once the alerts card is gone');
  await page.close();

  // ---- 6b. Polish (21 Nov 2026): pace wording, no second iPhone notice, plan card button quiet next to the alerts card
  {
    const html = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8');
    ok(!/1 to 5 min/.test(html), 'no "every 1 to 5 min" text left in the page');
    eq((html.match(/about every 30 seconds to a minute/g) || []).length, 3, 'three texts carry the measured pace wording');
    const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
    page = await open('plan=free&hunts=1&boot=1&joined=fresh&trial=1&tfound=5');
    await page.setUserAgent(IPHONE);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(3500);
    const PURPLE2 = 'rgb(162, 0, 255)';
    const shown = sel => page.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.getClientRects().length > 0; }, sel);
    const bg2 = sel => page.$eval(sel, e => getComputedStyle(e).backgroundColor);
    ok(await vis(page, '#alerts-setup-card'), 'iPhone: the alerts card shows');
    ok(/Home Screen/.test(await tc(page, '#notify-note')), 'iPhone: the notice text is still set');
    ok(!(await shown('#notify-note')), 'iPhone: the text-only notice is hidden while the alerts card shows');
    ok(await shown('#first-find-plan'), 'the plan card shows once the trial has a find');
    ok((await bg2('#first-find-plan a.btn-prim')) !== PURPLE2, 'the plan card button is quiet while the alerts card shows: ' + await bg2('#first-find-plan a.btn-prim'));
    eq(await bg2('#alerts-setup-resume'), PURPLE2, '"Set up alerts" is the one purple button');
    await page.click('#alerts-setup-later'); await wait(500);
    ok(await shown('#notify-note'), 'iPhone: the notice comes back once the alerts card is closed');
    eq(await bg2('#first-find-plan a.btn-prim'), PURPLE2, 'the plan card button is the main button once the alerts card is gone');
    await page.close();
  }

  // ---- 6c. The no-channel card also hides the old iPhone notice (one card, not two)
  {
    const IPH = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
    page = await open('plan=free&trial=1&hunts=1&boot=1&devs=0');
    await page.setUserAgent(IPH);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await wait(9000);
    const sh = sel => page.evaluate(sel => { const e = document.querySelector(sel); return !!e && e.getClientRects().length > 0; }, sel);
    ok(await sh('#no-channel-card'), 'iPhone, 24/7, no device: the no-channel card shows');
    ok(!(await sh('#notify-note')), 'the old iPhone notice is hidden next to it');
    await page.close();
  }

  // ---- 7. Claim receipt: one neutral review link, for everyone, no score
  {
    const html = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8');
    eq((html.match(/trustpilot\.com/g) || []).length, 1, 'one Trustpilot link in the page');
    ok(/id="claim-review"[^>]*>(?:(?!<\/div>).)*href="https:\/\/www\.trustpilot\.com\/evaluate\/snypd\.store"/.test(html), 'the review link sits in the claim receipt and points at the review form');
    const inReceipt = html.slice(html.indexOf('id="claim-receipt-overlay"'), html.indexOf('id="claim-receipt-done"'));
    ok(inReceipt.includes('id="claim-review"') && !/display:none/.test(inReceipt.slice(inReceipt.indexOf('id="claim-review"'), inReceipt.indexOf('id="claim-review"') + 80)), 'shown to every user (never hidden by a rule)');
    ok(!/TrustScore|stars?|\d(\.\d)? out of 5|good review|5-star/i.test(inReceipt), 'no score and no request for a good review');
  }

  eq(errors, [], 'no page errors');
  await browser.close(); server.close();
  console.log('PASS: ' + passed + ' first-session v2 checks.');
})().catch(e => { console.error('FAIL after ' + passed + ' checks: ' + (e && e.message)); process.exit(1); });
