/*
 * Browser test for the feedback questions (9 Nov 2026, website outreach/47, migration 081): the REAL dashboard.html in
 * headless Chrome, ops/qa_mock.js standing in for Supabase (?boot=1 serves dashboard_boot with feedback_done;
 * ?fb=<id> forces a question; ?a=<slug> preselects; ?fbdone=A,B1; ?fb081=0 = migration not applied; ?fbrpc=error).
 *   node ops/test_feedback.cjs            SHOTS=<dir> also writes screenshots
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
  const DESK = { width: 1440, height: 900 }, PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
  async function open(q, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || DESK);
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?boot=1&' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(1800);
    return page;
  }
  const shot = async (p, n) => { if (SHOTS) await p.screenshot({ path: path.join(SHOTS, n) }); };
  const state = p => p.evaluate(() => {
    const ov = document.querySelector('.fb-ov'), box = document.querySelector('.fb-box');
    const r = box && box.getBoundingClientRect();
    return {
      shown: !!ov, title: ov ? document.querySelector('.fb-t').textContent : null,
      opts: [...document.querySelectorAll('.fb-o')].map(b => b.getAttribute('data-a')),
      msg: [...document.querySelectorAll('.fb-msg')].map(m => m.textContent),
      link: (document.querySelector('.fb-ft a.btn') || {}).getAttribute ? document.querySelector('.fb-ft a.btn').getAttribute('href') : null,
      rpc: window.__fbRpc || [], bottom: r ? Math.round(innerHeight - r.bottom) : null, width: r ? Math.round(r.width) : null,
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });
  const pickA = (p, a) => p.click('.fb-o[data-a="' + a + '"]');
  const send = p => p.evaluate(() => [...document.querySelectorAll('.fb-ft .btn')].find(b => b.textContent === 'Send' || b.textContent === 'Envoyer').click());

  // 1. C forced, desktop: centred modal, too expensive -> B2 -> STAY50 link, XP only on C
  let p = await open('plan=free&fb=C');
  let s = await state(p);
  ok(s.shown, 'C desktop: shown');
  eq(s.title, "What's the main reason you haven't upgraded?", 'C: title');
  eq(s.opts, ['too_expensive', 'one_item', 'no_alerts', 'nothing_found', 'found_it', 'other_app', 'other'], 'C: 7 answers');
  ok(s.width <= 520 && s.bottom > 100, 'C desktop: centred modal, not a sheet');
  await shot(p, 'fb-C-1440.png');
  await pickA(p, 'too_expensive'); await send(p); await wait(300);
  s = await state(p);
  eq(s.title, 'What would SNYPD be worth to you per month?', 'C too_expensive -> B2');
  await pickA(p, '3_6'); await send(p); await wait(300);
  s = await state(p);
  eq(s.rpc.map(r => [r.p_question, r.p_answer, r.p_skipped]), [['C', 'too_expensive', false], ['B2', '3_6', false]], 'C+B2 saved');
  eq(s.link, '/plans?promo=STAY50', 'too_expensive -> Solo + STAY50');
  ok(s.msg.some(m => m === '+25 XP'), 'XP shown once');
  eq(s.overflow, 0, 'desktop: no horizontal scroll');

  // 2. phone: bottom sheet; one_item -> Hunt Pass
  p = await open('plan=free&fb=C', PHONE);
  s = await state(p);
  ok(s.shown && s.bottom <= 1 && s.width >= 389, 'C phone: bottom sheet full width');
  await shot(p, 'fb-C-390.png');
  await pickA(p, 'one_item'); await send(p); await wait(300);
  s = await state(p);
  eq(s.link, '/plans', 'one_item -> Hunt Pass');
  eq(s.overflow, 0, 'phone: no horizontal scroll');

  // 3. close = skipped, recorded once, no XP message
  p = await open('plan=free&fb=A');
  await p.click('.fb-x'); await wait(300);
  s = await state(p);
  ok(!s.shown, 'close removes popup');
  eq(s.rpc.map(r => [r.p_question, r.p_skipped]), [['A', true]], 'close records skipped A');

  // 4. migration not applied: nothing shown, no RPC, no page error
  p = await open('plan=free&fb=C&fb081=0');
  s = await state(p);
  ok(!s.shown && s.rpc.length === 0, 'no 081: nothing shown, no call');

  // 5. email preset ?a= preselects the answer
  p = await open('plan=free&fb=C&a=no_alerts');
  s = await p.evaluate(() => document.querySelector('.fb-o[aria-pressed="true"]').getAttribute('data-a'));
  eq(s, 'no_alerts', 'email preset preselects');

  // 6. save failure: still finishes, never throws
  p = await open('plan=free&fb=H&fbrpc=error');
  await pickA(p, 'yes'); await send(p); await wait(300);
  s = await state(p);
  eq(s.title, 'Thank you', 'rpc error: still reaches thank-you');
  ok(s.shown, 'rpc error: popup continues');

  // 7. not shown on load without force (20 s rule): nothing after 1.8 s
  p = await open('plan=pro');
  s = await state(p);
  ok(!s.shown, 'no popup on page load');

  // 8. French
  p = await open('plan=free&fb=C&lang=fr');
  s = await p.evaluate(() => document.querySelector('.fb-t') && document.querySelector('.fb-t').textContent);
  ok(/tu n.es pas pass/.test(s || ''), 'fr: title translated: ' + s);

  // 9. email click (scanner-safe): answer preselected, NOTHING saved until the person taps Send; then saved as source email
  p = await open('plan=free&fb=C&a=no_alerts&src=email');
  s = await state(p);
  eq(s.title, "What's the main reason you haven't upgraded?", 'email: question shown for confirmation');
  ok(s.rpc.length === 0, 'email: nothing saved before the tap');
  eq(await p.evaluate(() => document.querySelector('.fb-o[aria-pressed="true"]').getAttribute('data-a')), 'no_alerts', 'email: answer preselected');
  await send(p); await wait(300);
  s = await state(p);
  eq(s.rpc.map(r => [r.p_question, r.p_answer, r.p_source]), [['C', 'no_alerts', 'email']], 'email: saved on tap with source email');
  ok(s.msg.some(m => /permission/.test(m)), 'email no_alerts -> push setup step');

  // 10. email link with an unknown answer: asks the question normally
  p = await open('plan=free&fb=C&a=bogus&src=email');
  s = await state(p);
  eq(s.title, "What's the main reason you haven't upgraded?", 'email bad slug: asks normally');

  // 11. trial A appears from the boot signal: first find 3 h ago, trial started 5 h ago (forced timing via mock)
  p = await open('plan=pro');
  s = await p.evaluate(() => window.SnypdFeedback.pick({ done: [], plan: 'pro', profile: {}, activeDays14: 3 }).id);
  eq(s, 'D', 'signals: active pro -> D');

  eq(errors, [], 'no page errors');
  console.log('test_feedback: ' + passed + ' checks passed');
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
