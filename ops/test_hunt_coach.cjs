/*
 * Browser test for the hunt coach, the hunter-statistics switch and the one-time notice (7 Nov 2026, website outreach/41):
 * the REAL dashboard.html in headless Chrome, ops/qa_mock.js standing in for Supabase and api.snypd.store
 * (/api/v1/hunt-coach: ?coach=busy|peers|quiet|widen|minblock|stale|error; ?coachwrite=error; ?statsout=1; ?statsrpc=error;
 * ?joined=new). Each case runs in its own browser context (own localStorage).
 *   node ops/test_hunt_coach.cjs              (needs Google Chrome at CHROME_PATH or the default Windows path)
 *   SHOTS=<dir> node ops/test_hunt_coach.cjs  also writes screenshots
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
const EUR = '\u20AC', NB = '\u00A0';
const FE = n => n + NB + EUR;   // French money after i18n.js ("25 EUR" order)
const URL0 = 'https://www.vinted.be/catalog?search_text=jordan%20travis%20scott';
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  const PHONE = { width: 390, height: 844, isMobile: true, hasTouch: true };
  async function open(q, vp, ctx) {
    ctx = ctx || await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/dashboard.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' });
    await page.waitForFunction(() => (window.__coachRequests || 0) >= 1, { timeout: 12000 });
    await wait(700);
    page.ctx = ctx;
    return page;
  }
  const shot = async (page, name) => { if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name) }); };
  const card = p => p.evaluate(() => {
    const c = document.getElementById('broad-hunt');
    const vis = id => { const b = document.getElementById(id); return !!b && b.style.display !== 'none' && b.offsetParent !== null; };
    const t = document.getElementById('broad-hunt-text');
    return {
      shown: c.style.display !== 'none',
      title: document.getElementById('broad-hunt-title').innerText.trim(),
      spans: [...t.querySelectorAll('span')].map(s => s.textContent),
      text: t.innerText.replace(/[ \t\n\r]+/g, ' ').trim(),   // not \s: it would flatten the French no-break spaces
      apply: vis('broad-hunt-apply') ? document.getElementById('broad-hunt-apply').textContent.trim() : null,
      undo: vis('broad-hunt-undo'), calm: vis('broad-hunt-calm'), edit: vis('broad-hunt-edit'), keep: vis('broad-hunt-keep'),
      tags: t.querySelectorAll('b').length,
      url: window.__qaDB.user_searches[0].vinted_url,
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });

  // ---- 1. busy hunt, own prices: card, apply, undo
  let p = await open('coach=busy');
  let c = await card(p);
  ok(c.shown, 'busy: card shown');
  eq(c.title, 'This hunt finds too much', 'busy: title');
  eq(c.spans, ['About 2400 new listings a day match "jordan <b>travis</b>": too many to open.',
    'A max price of ' + EUR + '25 keeps its cheapest 26%, about 624 a day.',
    '9 other hunters of Jordan set a max price of about ' + EUR + '30.'], 'busy: sentences');
  eq(c.tags, 0, 'busy: hunt name escaped (no <b> element)');
  eq(c.apply, 'Set max ' + EUR + '25', 'busy: apply label');
  ok(!c.calm && !c.edit && c.keep && !c.undo, 'busy: only Set max + Keep it');
  await shot(p, 'coach-busy-1280.png');
  await p.click('#broad-hunt-apply');
  await p.waitForFunction(() => document.getElementById('broad-hunt-undo').style.display !== 'none');
  c = await card(p);
  eq(c.url, URL0 + '&price_to=25', 'apply: only price_to appended, rest of the link byte-identical');
  eq(c.spans, ['Done: "jordan <b>travis</b>" now has a max price of ' + EUR + '25.', 'New matches can take a few minutes to show.'], 'apply: done text');
  ok(c.undo && !c.keep && c.apply === null, 'apply: only Undo left');
  ok(await p.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('snypd_coach_ok') || '{}')).includes('search-1:busy:25')), 'apply: remembered');
  await p.click('#broad-hunt-undo');
  await wait(300);
  c = await card(p);
  eq(c.url, URL0, 'undo: link restored exactly');
  eq(c.spans, ['Undone: "jordan <b>travis</b>" is back as it was.'], 'undo: text');
  await p.reload({ waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => (window.__coachRequests || 0) >= 1, { timeout: 12000 });
  await wait(700);
  ok(!(await card(p)).shown, 'after apply: the same advice is not shown again on this device');
  await p.ctx.close();

  // ---- 2. Keep it
  p = await open('coach=busy');
  await p.click('#broad-hunt-keep');
  ok(!(await card(p)).shown, 'keep: card hidden');
  await p.reload({ waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => (window.__coachRequests || 0) >= 1, { timeout: 12000 });
  await wait(700);
  ok(!(await card(p)).shown, 'keep: not shown again');
  eq((await card(p)).url, URL0, 'keep: hunt untouched');
  await p.ctx.close();

  // ---- 3. busy paused Free hunt, peers' max
  p = await open('coach=peers');
  c = await card(p);
  eq(c.spans, ['At least 4517 new listings a day matched "jordan <b>travis</b>" while it was paused: too many to open.',
    '9 other hunters of Jordan set a max price of about ' + EUR + '20.'], 'peers: sentences');
  eq(c.apply, 'Set max ' + EUR + '20', 'peers: apply label');
  await p.ctx.close();

  // ---- 4. quiet hunt: raise to the peers' max (replaces the existing price_to)
  p = await open('coach=quiet');
  c = await card(p);
  eq(c.title, 'This hunt finds almost nothing', 'quiet: title');
  eq(c.spans, ['"jordan <b>travis</b>" found 1 new listing in 3 days.',
    '9 other hunters of Jordan set a max price of about ' + EUR + '20; yours is ' + EUR + '8.'], 'quiet: sentences');
  eq(c.apply, 'Raise max to ' + EUR + '20', 'quiet: apply label');
  await p.click('#broad-hunt-apply');
  await p.waitForFunction(() => document.getElementById('broad-hunt-undo').style.display !== 'none');
  eq((await card(p)).url, URL0 + '&price_to=20', 'quiet apply: price_to replaced, not added twice');
  await p.ctx.close();

  // ---- 5. quiet without a suggestion
  p = await open('coach=widen');
  c = await card(p);
  eq(c.spans, ['"jordan <b>travis</b>" found nothing new in 4 days.', 'Widen it: fewer words, fewer sizes or a higher max price.'], 'widen: sentences');
  ok(c.apply === null && c.edit && c.keep, 'widen: Edit hunt + Keep it');
  await p.ctx.close();

  // ---- 6. never shown: min price would invert the range, stale link, backend error, no advice
  for (const q of ['coach=minblock', 'coach=stale', 'coach=error', 'coach=none', '']) {
    p = await open(q);
    ok(!(await card(p)).shown, 'no card for ?' + q);
    eq(await p.evaluate(() => window.__coachRequests), 1, 'one coach request per page load (' + q + ')');
    await p.ctx.close();
  }

  // ---- 7. write fails
  p = await open('coach=busy&coachwrite=error');
  await p.click('#broad-hunt-apply');
  await wait(300);
  c = await card(p);
  eq(c.spans, ['Could not change this hunt. Try again, or change it in Filters.'], 'write error: message');
  eq(c.url, URL0, 'write error: hunt untouched');
  ok(c.apply === 'Set max ' + EUR + '25', 'write error: can try again');
  await p.ctx.close();

  // ---- 8. French
  p = await open('coach=busy&lang=fr');
  await wait(400);
  c = await card(p);
  eq(c.title, 'Cette recherche trouve trop', 'fr: title');
  eq(c.text, 'Environ 2400 nouvelles annonces par jour correspondent \u00e0 \u00ab' + NB + 'jordan <b>travis</b>' + NB + '\u00bb' + NB + ': trop pour tout ouvrir. '
    + 'Un prix max de ' + FE(25) + ' garde ses 26' + NB + '% les moins chers, environ 624 par jour. '
    + '9 autres chasseurs de Jordan fixent un prix max d\u2019environ ' + FE(30) + '.', 'fr: text');
  eq(c.apply, 'Prix max ' + FE(25), 'fr: button');
  await p.ctx.close();
  p = await open('coach=quiet&lang=fr');
  await wait(400);
  c = await card(p);
  eq(c.text, '\u00ab' + NB + 'jordan <b>travis</b>' + NB + '\u00bb a trouv\u00e9 1 nouvelle annonce en 3 jours. 9 autres chasseurs de Jordan fixent un prix max d\u2019environ '
    + FE(20) + NB + '; le tien est de ' + FE(8) + '.', 'fr: quiet text');
  eq(c.apply, 'Monter le max \u00e0 ' + FE(20), 'fr: quiet button');
  await p.ctx.close();

  // ---- 9. phone
  p = await open('coach=busy', PHONE);
  c = await card(p);
  ok(c.shown && c.overflow <= 0, 'phone: card shown, no horizontal overflow (' + c.overflow + ')');
  const box = await p.evaluate(() => { const r = document.getElementById('broad-hunt-apply').getBoundingClientRect(); return { w: r.width, h: r.height, right: r.right }; });
  ok(box.h >= 32 && box.right <= 390, 'phone: apply button inside the screen (' + JSON.stringify(box) + ')');
  await shot(p, 'coach-busy-390.png');
  await p.ctx.close();

  // ---- 10. one-time notice
  const note = pg => pg.evaluate(() => { const n = document.getElementById('stats-note'); return { shown: n.style.display !== 'none', text: n.innerText.replace(/\s+/g, ' ') }; });
  p = await open('');
  let n = await note(p);
  ok(n.shown && /5 or more users/.test(n.text) && /leave these statistics in Profile/.test(n.text), 'notice: shown to an older account');
  await p.click('#stats-note-ok');
  ok(!(await note(p)).shown, 'notice: OK hides it');
  await p.reload({ waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => (window.__coachRequests || 0) >= 1, { timeout: 12000 });
  ok(!(await note(p)).shown, 'notice: not shown again');
  await p.ctx.close();
  p = await open('joined=new');
  ok(!(await note(p)).shown, 'notice: not shown to accounts created after the change');
  await p.ctx.close();
  p = await open('lang=fr');
  await wait(400);
  n = await note(p);
  ok(/^Statistiques des chasseurs SNYPD affiche maintenant des totaux anonymes/.test(n.text) && /Ouvrir le profil/i.test(n.text), 'notice: French (' + n.text.slice(0, 80) + ')');
  await p.ctx.close();

  // ---- 11. Profile switch
  const sw = pg => pg.evaluate(() => {
    const t = document.getElementById('prof-toggle-stats'), r = document.getElementById('prof-stats-result');
    return { checked: t.getAttribute('aria-checked'), disabled: t.disabled, result: r.style.display === 'none' ? '' : r.innerText.trim(),
             rpc: window.__statsRpc || [], visible: t.offsetParent !== null };
  });
  p = await open('');
  await p.click('#stats-note-profile');
  await p.waitForFunction(() => { const t = document.getElementById('prof-toggle-stats'); return t && !t.disabled && t.offsetParent !== null; }, { timeout: 8000 });
  let s = await sw(p);
  ok(s.visible && s.checked === 'true' && !(await note(p)).shown, 'profile: Open Profile from the notice; switch on (counted), notice gone');
  await p.click('#prof-toggle-stats');
  await wait(300);
  s = await sw(p);
  eq([s.checked, s.rpc], ['false', [{ p_out: true }]], 'profile: switch off -> set_hunter_stats_opt_out(true)');
  ok(/left out of hunter statistics/.test(s.result), 'profile: confirmation shown');
  await p.click('#prof-toggle-stats');
  await wait(300);
  s = await sw(p);
  eq([s.checked, s.rpc.length, s.rpc[1]], ['true', 2, { p_out: false }], 'profile: back on -> (false)');
  await shot(p, 'coach-profile-1280.png');
  await p.ctx.close();
  const openProfile = async q => {
    const pg = await open(q);
    await pg.evaluate(() => document.querySelector('[data-view="profile"]').click());
    await pg.waitForFunction(() => { const t = document.getElementById('prof-toggle-stats'); return t && !t.disabled; }, { timeout: 8000 });
    return pg;
  };
  p = await openProfile('statsout=1');
  eq((await sw(p)).checked, 'false', 'profile: an opted-out account shows the switch off');
  await p.ctx.close();
  p = await openProfile('statsrpc=error');
  await p.click('#prof-toggle-stats');
  await wait(300);
  s = await sw(p);
  eq([s.checked, s.result], ['true', 'Could not save this setting. Try again.'], 'profile: failed save puts the switch back');
  await p.ctx.close();

  eq(errors, [], 'no page errors');
  await browser.close();
  server.close();
  console.log('hunt coach UI: ' + passed + ' checks passed');
})().catch(e => { console.error(e); process.exit(1); });
