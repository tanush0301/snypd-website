/*
 * Keep my plan (14 Nov 2026, website outreach/62 move 6): the /account page.
 *   node ops/test_keep_plan_account.cjs   (needs Google Chrome at CHROME_PATH or the default Windows path)
 * Runs the REAL account.html with ops/qa_mock.js in headless Chrome (?keep=cost marks the Whop membership as set to
 * end; ?keepres=ok|409|403|502|net answers the Keep tap). Checks: "Ends on" + Keep my plan for a cancelling recurring
 * plan, never for a Hunt Pass; every answer to the Keep tap; "Manage subscription" opens the before-Whop step first,
 * with the cheaper-plan line only on Kickstart/Pro/Elite; Back closes it; Continue to Whop leaves for Whop; no page errors.
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
      if (p === '/account.html') return send(swap(fs.readFileSync(path.join(root, 'account.html'), 'utf8')), 'text/html; charset=utf-8');
      const f = path.join(root, p);
      if (!f.startsWith(root) || p.startsWith('/ops/') || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nope'); }
      send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
    } catch (e) { res.writeHead(500); res.end(String(e)); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];

  async function open(q, vp) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp || { width: 1280, height: 900 });
    page.on('pageerror', e => errors.push(q + ': ' + e.message));
    await page.goto(base + '/account.html?' + q, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !!window.__snypdAccountState, { timeout: 10000 });
    await wait(800);
    page.ctx = ctx;
    return page;
  }
  const st = p => p.evaluate(() => {
    const notice = document.querySelector('[data-snypd="notice"]');
    const keep = document.querySelector('[data-snypd-action="keep"]');
    const msg = notice && notice.querySelector('[data-keep-msg]');
    const panel = document.getElementById('manage-panel');
    const fewer = panel && panel.querySelector('[data-mp-only="fewer"]');
    return { notice: notice ? notice.textContent.replace(/\s+/g, ' ').trim() : '', keep: !!keep && keep.style.display !== 'none',
      msg: msg ? msg.textContent : '', label: (document.querySelector('[data-snypd="renewsLabel"]') || {}).textContent,
      panel: !!panel && panel.style.display === 'block', fewer: !!fewer && fewer.style.display !== 'none',
      posts: (window.__keepPosts || []).length };
  });
  const click = async (p, sel) => { await p.$eval(sel, e => e.scrollIntoView({ block: 'center' })); await p.click(sel); await wait(700); };

  // ---- 1. Active Pro, not cancelling: no Keep button, "Renews on"
  {
    const p = await open('plan=pro&active=1&keep=off');
    const s = await st(p);
    eq([s.keep, s.label], [false, 'Renews on'], 'not cancelling: Renews on, no Keep button');
    await p.ctx.close();
  }
  // ---- 2. Cancelling Pro: Ends on + Keep my plan; kept
  {
    const p = await open('plan=pro&active=1&keep=cost&keepres=ok');
    const s = await st(p);
    ok(s.label === 'Ends on' && /set to cancel at period end/.test(s.notice), 'cancelling: Ends on and the period-end line');
    ok(s.keep, 'cancelling: Keep my plan button shown');
    await click(p, '[data-snypd-action="keep"]');
    const a = await st(p);
    ok(/Your plan stays on\. It renews on .*, as before\./.test(a.notice), 'kept: notice says it stays on: ' + a.notice);
    eq([a.label, a.posts], ['Renews on', 1], 'kept: label back to Renews on, one POST');
    const auth = await p.evaluate(() => window.__keepPosts[0].auth);
    ok(/^Bearer \S+/.test(String(auth)), 'the Keep request carries the session token');
    await p.ctx.close();
  }
  // ---- 3. Every other answer to the Keep tap
  for (const [res, msg, keepVisible] of [
    ['409', 'Your plan is no longer set to end.', false],
    ['403', 'We could not change it from here. Write to help@snypd.store and we will do it for you.', false],
    ['502', 'That did not work. Try again in a minute.', true],
    ['net', 'That did not work. Try again in a minute.', true],
  ]) {
    const p = await open('plan=pro&active=1&keep=cost&keepres=' + res);
    await click(p, '[data-snypd-action="keep"]');
    const s = await st(p);
    eq([s.msg, s.keep], [msg, keepVisible], 'Keep answer ' + res + ': message and button');
    if (keepVisible) ok(!(await p.$eval('[data-snypd-action="keep"]', b => b.disabled)), 'Keep answer ' + res + ': button usable again');
    await p.ctx.close();
  }
  // ---- 4. Hunt Pass: never a Keep button
  {
    const p = await open('plan=solo&active=1&pass=1&keep=cost');
    eq((await st(p)).keep, false, 'Hunt Pass: no Keep button');
    await p.ctx.close();
  }
  // ---- 5. Manage subscription opens the before-Whop step first
  for (const [plan, fewer] of [['pro', true], ['kickstart', true], ['elite', true], ['solo', false]]) {
    const p = await open('plan=' + plan + '&active=1&keep=off');
    await click(p, '[data-snypd-action="billing"]');
    const s = await st(p);
    eq([s.panel, s.fewer], [true, fewer], plan + ': Manage opens the before-Whop step; cheaper-plan line ' + (fewer ? 'shown' : 'hidden'));
    if (plan === 'pro') {
      const t = await p.$eval('#manage-panel', e => e.textContent.replace(/\s+/g, ' '));
      ok(/Calm sends one summary every 15 minutes/.test(t) && /help@snypd\.store/.test(t), 'before-Whop step: Calm + max price and help@ lines');
      ok(!/pause|discount|% off/i.test(t), 'before-Whop step: no pause and no discount');
      eq(await p.$eval('#mp-whop', a => a.getAttribute('href')), 'https://whop.com/manage', 'Continue to Whop points at the member\'s Whop page');
      await click(p, '#mp-back');
      eq((await st(p)).panel, false, 'Back closes the step');
      await click(p, '[data-snypd-action="billing"]');
      await Promise.all([p.waitForRequest(r => r.url().startsWith('https://whop.com/manage'), { timeout: 8000 }).catch(() => null), p.click('#mp-whop')]);
      await wait(600);
      ok(p.url().startsWith('https://whop.com/manage') || /whop\.com/.test(p.url()), 'Continue to Whop leaves for Whop: ' + p.url());
    }
    await p.ctx.close();
  }
  // ---- 6. Phone width: no sideways scroll with the step open
  {
    const p = await open('plan=pro&active=1&keep=cost', { width: 390, height: 844, isMobile: true, hasTouch: true });
    await click(p, '[data-snypd-action="billing"]');
    const m = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth }));
    ok(m.sw <= m.iw + 1, '390 px: no sideways scroll (' + m.sw + ' vs ' + m.iw + ')');
    await p.ctx.close();
  }

  eq(errors, [], 'no page errors');
  await browser.close();
  server.close();
  console.log('PASS: ' + passed + ' keep-my-plan /account checks.');
})().catch(e => { console.error(e); process.exit(1); });
