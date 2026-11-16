/*
 * Discord row in the first-hunt wizard's alerts step (16 Nov 2026). The REAL dashboard.html in headless Chrome,
 * ops/qa_mock.js standing in for Supabase and api.snypd.store (?dc=linked | off, calls counted in window.__dcCalls).
 * The row hands off to the Profile Discord block and must only ever connect, never disconnect.
 *   node ops/test_wizard_discord.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
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
    const f = path.join(root, p); if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
    send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const NEW = 'plan=free&hunts=0&boot=1&joined=fresh';

(async () => {
  const text = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8');
  eq((text.match(/id="wiz-discord-row"/g) || []).length, 1, 'one wizard Discord row in the markup');
  ok(/id="wiz-discord-row" style="display:none"/.test(text), 'the row is hidden in the markup until the linked state is known');

  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(q) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 390, height: 844 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:') ? r.continue() : r.abort()));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await wait(2500);
    return { page, ctx };
  }
  const vis = (p, sel) => p.$eval(sel, e => !e.hidden && e.getClientRects().length > 0).catch(() => false);
  // Drives the real wizard: save a first hunt, pick an alert style, land on the alerts step.
  async function toAlertsStep(page) {
    ok(await vis(page, '#wiz-step-1'), 'the wizard opens for an account without a hunt');
    await page.type('#wiz-q-words', 'ralph lauren jumper');
    await page.type('#wiz-q-max', '40');
    await page.click('#wiz-q-save'); await wait(1500);
    const mx = await page.evaluate(() => { const b = document.getElementById('wiz-q-mx'); return !!b && b.style.display !== 'none' && b.offsetHeight > 0; });
    if (mx) { await page.click('#wiz-q-mx [data-mx-act="keep"]'); await wait(900); }
    ok(await vis(page, '#wiz-step-mode'), 'alert-style step shown after the hunt is saved');
    await page.click('.wiz-mode'); await wait(200);
    await page.click('#wiz-mode-next'); await wait(1200);
    ok(await vis(page, '#wiz-step-2'), 'alerts step shown');
  }
  const row = page => page.evaluate(() => {
    const g = id => document.getElementById(id);
    const shown = e => !!e && !e.hidden && e.getClientRects().length > 0;
    return { row: shown(g('wiz-discord-row')), btn: shown(g('wiz-discord-btn')), btnText: g('wiz-discord-btn').textContent.trim(),
      title: g('wiz-label-discord').textContent.trim(), note: g('wiz-discord-note').textContent.trim(),
      overlay: getComputedStyle(g('wiz-overlay')).display !== 'none',
      code: shown(g('prof-discord-code')) ? g('prof-discord-code').textContent.trim() : null,
      profNote: g('prof-discord-note').textContent.trim(), profBtn: g('prof-discord-btn').textContent.trim(),
      calls: (window.__dcCalls || []).slice(), sw: document.documentElement.scrollWidth, vw: innerWidth };
  });

  // ---- 1. Not linked: the row offers Discord, the tap opens Profile with a code --------------------------------
  {
    const { page, ctx } = await open(NEW);
    await toAlertsStep(page);
    let s = await row(page);
    ok(s.row && s.btn, 'not linked: row and button shown');
    eq([s.title, s.btnText], ['Discord alerts', 'Connect Discord'], 'title and button text');
    eq(s.note, 'In a private thread in the SNYPD Discord. No Home Screen step on iPhone.', 'note');
    ok(await vis(page, '#wiz-toggle-push') && await vis(page, '#wiz-enable-alerts'), 'the push row and its button are still there');
    eq(s.calls, [], 'nothing is sent before a tap');
    ok(s.sw <= s.vw, 'no sideways scroll at 390 (' + s.sw + ' > ' + s.vw + ')');
    await page.click('#wiz-discord-btn'); await wait(1200);
    s = await row(page);
    ok(!s.overlay, 'the wizard closes');
    eq(s.code, 'QA7K2M', 'Profile shows the link code');
    ok(await vis(page, '#prof-discord-open'), 'Profile shows Open Discord');
    eq(s.calls, ['/api/v1/discord/code'], 'exactly one request: a link code');
    await ctx.close();
  }

  // ---- 2. Already linked: state only, no button, and nothing can disconnect from here --------------------------
  {
    const { page, ctx } = await open(NEW + '&dc=linked');
    await toAlertsStep(page);
    let s = await row(page);
    ok(s.row, 'linked: row shown');
    ok(!s.btn, 'linked: no button');
    eq(s.note, 'Connected as qa_hunter.', 'linked: says who is connected');
    eq(s.profBtn, 'Disconnect', 'Profile button is Disconnect for a linked account');
    await page.evaluate(() => document.getElementById('wiz-discord-btn').click()); await wait(800);
    s = await row(page);
    eq(s.calls, [], 'a forced click on the hidden wizard button sends nothing (no disconnect)');
    ok(s.overlay, 'and the wizard stays open');
    eq(s.profBtn, 'Disconnect', 'still linked');
    await ctx.close();
  }

  // ---- 3. Discord alerts switched off on the backend: an honest message, no code -------------------------------
  {
    const { page, ctx } = await open(NEW + '&dc=off');
    await toAlertsStep(page);
    await page.click('#wiz-discord-btn'); await wait(1200);
    const s = await row(page);
    eq(s.code, null, 'off: no code');
    eq(s.profNote, 'Discord alerts are not available right now.', 'off: Profile says so');
    eq(s.calls, ['/api/v1/discord/code'], 'off: one request, no disconnect');
    await ctx.close();
  }

  // ---- 4. French ------------------------------------------------------------------------------------------------
  {
    const { page, ctx } = await open(NEW + '&lang=fr');
    await toAlertsStep(page);
    const s = await row(page);
    ok(s.row && s.btn, 'fr: row and button shown');
    eq([s.title, s.btnText], ['Alertes Discord', 'Connecter Discord'], 'fr: title and button');
    eq(s.note, 'Dans un fil priv\u00e9 du Discord SNYPD. Sans passer par l\u2019\u00e9cran d\u2019accueil sur iPhone.', 'fr: note');
    ok(s.sw <= s.vw, 'fr: no sideways scroll at 390 (' + s.sw + ' > ' + s.vw + ')');
    await ctx.close();
  }

  await browser.close();
  server.close();
  eq(errors, [], 'no page errors');
  console.log('PASS test_wizard_discord: ' + passed + ' checks');
})().catch(e => { console.error('FAIL test_wizard_discord:', e.message); process.exit(1); });
