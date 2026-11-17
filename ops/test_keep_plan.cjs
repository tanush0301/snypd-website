/*
 * Keep my plan (14 Nov 2026, website outreach/62 move 6): dashboard card.
 *   node ops/test_keep_plan.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Runs the REAL dashboard.html with ops/qa_mock.js in headless Chrome. The mock answers GET /api/v1/membership from
 * ?keep=off|tech|cost|none|unused and POST /api/v1/membership/keep from ?keepres=ok|409|403|502|net.
 * Checks: shown only to a cancelling recurring plan; never to a Hunt Pass or Free; the fix matches the reason; every
 * answer to the Keep tap; Calm all; Not now for 3 days on this device; 390 px; no page errors.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
  const swap = s => s.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
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
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];

  async function open(q, { seed = {}, vp } = {}) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.evaluateOnNewDocument(seed => {
      try { if (!sessionStorage.getItem('__seeded')) { sessionStorage.setItem('__seeded', '1'); for (const k in seed) localStorage.setItem(k, seed[k]); } } catch (e) {}
    }, seed);
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForSelector('[data-view="market"]', { timeout: 10000 });
    await wait(2600);
    page.ctx = ctx;
    return page;
  }
  const state = p => p.evaluate(() => {
    const t = id => { const e = document.getElementById(id); return e ? e.textContent.trim() : null; };
    const shown = id => { const e = document.getElementById(id); return !!e && e.style.display !== 'none' && e.getClientRects().length > 0; };
    return { shown: shown('keep-plan'), title: t('keep-plan-title'), text: t('keep-plan-text'), note: shown('keep-plan-note') ? t('keep-plan-note') : '',
      keep: shown('keep-plan-keep') ? t('keep-plan-keep') : null, help: shown('keep-plan-help') ? t('keep-plan-help') : null,
      later: shown('keep-plan-later') ? t('keep-plan-later') : null, gets: window.__keepRequests || 0, posts: (window.__keepPosts || []).length };
  });
  const tap = async (p, id) => { await p.$eval('#' + id, e => e.scrollIntoView({ block: 'center' })); await p.click('#' + id); await wait(700); };

  // ---- 1. Not cancelling: the status is asked once, no card
  {
    const p = await open('plan=pro&active=1&keep=off');
    const s = await state(p);
    eq([s.shown, s.gets, s.posts], [false, 1, 0], 'not cancelling: one status read, no card');
    await p.ctx.close();
  }
  // ---- 2. Pro, "too expensive": cheaper plans offered, Keep, Not now
  {
    const p = await open('plan=pro&active=1&keep=cost');
    const s = await state(p);
    ok(s.shown, 'too expensive: card shown');
    ok(/^Your Pro ends on /.test(s.title), 'title names the plan and the end date: ' + s.title);
    ok(/Solo is .5\.99 a month for 1 search, Kickstart .14\.99 for 2/.test(s.text), 'cheaper plans named with their prices');
    ok(/After that the Free plan applies/.test(s.text) && /Keep your plan and nothing else changes/.test(s.text), 'what happens after the end, and what Keep changes');
    eq([s.keep, s.help, s.later], ['Keep my Pro', 'Compare plans', 'Not now'], 'buttons: Keep my Pro, Compare plans, Not now');
    ok(!/pause|discount|% off/i.test(s.text + s.title), 'no pause and no discount offered');
    await p.ctx.close();
  }
  // ---- 3. Solo "too expensive": no cheaper plan line (Solo is the cheapest subscription)
  {
    const p = await open('plan=solo&active=1&keep=cost');
    const s = await state(p);
    ok(s.shown && /^Your Solo ends on /.test(s.title), 'Solo cancelling: card shown');
    eq([/Solo is/.test(s.text), s.help], [false, null], 'Solo: no cheaper-plan line, no Compare plans button');
    await p.ctx.close();
  }
  // ---- 4. Elite, "technical issues" with every-match searches: Calm all
  {
    const p = await open('plan=elite&keep=tech');
    const s = await state(p);
    ok(s.shown && /alerts came too fast/.test(s.text), 'technical issues: the alert-flood fix is offered');
    eq(s.help, 'Calm all my searches', 'Calm all button');
    await tap(p, 'keep-plan-help');
    const after = await state(p);
    ok(/^Done: \d+ search(es)? now send/.test(after.note), 'Calm all: confirmation shown: ' + after.note);
    eq(after.help, null, 'Calm all button hidden after use');
    const modes = await p.evaluate(() => window.__qaDB.user_searches.filter(h => h.is_active).map(h => h.push_mode));
    ok(modes.length > 0 && modes.every(m => m === 'calm'), 'every active search is now Calm');
    await p.ctx.close();
  }
  // ---- 5. No reason given: only the Free-plan line and Keep
  {
    const p = await open('plan=kickstart&active=1&keep=none');
    const s = await state(p);
    ok(s.shown && s.help === null && s.keep === 'Keep my Kickstart', 'no reason: Keep only, no extra fix');
    await p.ctx.close();
  }
  // ---- 6. Keep tap: every answer from the backend
  {
    const p = await open('plan=pro&active=1&keep=cost&keepres=ok');
    await tap(p, 'keep-plan-keep');
    const s = await state(p);
    ok(/^Your Pro stays on$/.test(s.title) && /renews on .*, as before/.test(s.text), 'kept: card says it stays on and renews as before');
    eq([s.keep, s.help, s.later, s.posts], [null, null, 'Close', 1], 'kept: one POST, only Close left');
    const auth = await p.evaluate(() => window.__keepPosts[0].auth);
    ok(/^Bearer \S+/.test(String(auth)), 'the Keep request carries the session token');
    await tap(p, 'keep-plan-later');
    eq((await state(p)).shown, false, 'Close hides the card');
    await p.ctx.close();
  }
  for (const [res, note, keepVisible] of [
    ['409', 'Your plan is no longer set to end.', false],
    ['403', 'We could not change it from here. Write to help@snypd.store and we will do it for you.', false],
    ['502', 'That did not work. Try again in a minute.', true],
    ['net', 'That did not work. Try again in a minute.', true],
  ]) {
    const p = await open('plan=pro&active=1&keep=cost&keepres=' + res);
    await tap(p, 'keep-plan-keep');
    const s = await state(p);
    eq([s.note, s.keep !== null], [note, keepVisible], 'Keep answer ' + res + ': message and button');
    if (keepVisible) ok(!(await p.$eval('#keep-plan-keep', b => b.disabled)), 'Keep answer ' + res + ': button usable again');
    await p.ctx.close();
  }
  // ---- 7. Never for a Hunt Pass or a Free account
  {
    const p = await open('plan=solo&active=1&pass=1&keep=cost');
    eq([(await state(p)).shown, (await state(p)).gets], [false, 0], 'Hunt Pass: no card and no status read');
    await p.ctx.close();
    const f = await open('plan=free&keep=cost');
    eq([(await state(f)).shown, (await state(f)).gets], [false, 0], 'Free account: no card and no status read');
    await f.ctx.close();
  }
  // ---- 8. Not now: hidden, remembered for 3 days on this device
  {
    const p = await open('plan=pro&active=1&keep=cost');
    await tap(p, 'keep-plan-later');
    const s = await state(p);
    const stored = await p.evaluate(() => JSON.parse(localStorage.getItem('snypd_keep_later') || 'null'));
    eq(s.shown, false, 'Not now hides the card');
    ok(stored && Date.now() - stored.t < 60000 && stored.e, 'Not now remembered with the end date');
    await p.ctx.close();
    const q = await open('plan=pro&active=1&keep=cost', { seed: { snypd_keep_later: JSON.stringify({ t: Date.now() - 864e5, e: '2026-12-07T00:36:00Z' }) } });
    eq([(await state(q)).shown, (await state(q)).gets], [false, 0], '1 day after Not now: still hidden, no status read');
    await q.ctx.close();
    const r = await open('plan=pro&active=1&keep=cost', { seed: { snypd_keep_later: JSON.stringify({ t: Date.now() - 4 * 864e5, e: '2026-12-07T00:36:00Z' }) } });
    eq((await state(r)).shown, true, '4 days after Not now: shown again');
    await r.ctx.close();
  }
  // ---- 9. Phone width: card fits, buttons tappable, no sideways scroll
  {
    const p = await open('plan=pro&active=1&keep=cost', { vp: { width: 390, height: 844, isMobile: true, hasTouch: true } });
    const m = await p.evaluate(() => {
      const c = document.getElementById('keep-plan').getBoundingClientRect();
      const b = ['keep-plan-keep', 'keep-plan-help', 'keep-plan-later'].map(id => document.getElementById(id).getBoundingClientRect().height);
      return { right: c.right, sw: document.documentElement.scrollWidth, iw: innerWidth, minH: Math.min(...b) };
    });
    ok(m.right <= m.iw + 1 && m.sw <= m.iw + 1, '390 px: card inside the screen, no sideways scroll');
    ok(m.minH >= 34, '390 px: buttons at the dashboard phone height, 34 px (' + m.minH + ')');
    await p.ctx.close();
  }

  eq(errors, [], 'no page errors');
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' keep-my-plan checks.');
})().catch(e => { console.error(e); process.exit(1); });
