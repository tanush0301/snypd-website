// Contact form on /support: real page in headless Chrome, backend answers simulated. No production requests.
const fs = require('fs'), path = require('path'), http = require('http'), assert = require('assert');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const chrome = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/usr/bin/chromium'].find(p => fs.existsSync(p));
const API = 'https://api.snypd.store/api/v1/support/contact';
const MAIL = 'heysnypd@gmail.com';
let checks = 0;
const ok = (c, name) => { assert(c, name); checks++; };

(async () => {
  const server = http.createServer((req, res) => {
    const f = path.join(root, req.url.split('?')[0] === '/support' ? 'support.html' : req.url.split('?')[0]);
    if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/octet-stream' });
    res.end(fs.readFileSync(f));
  }).listen(0);
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new' });
  const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': 'POST, OPTIONS' };

  async function open(width, height, answer) {
    const page = await browser.newPage();
    const state = { posts: [], errors: [], outside: [] };
    page.on('pageerror', e => state.errors.push(String(e)));
    await page.setViewport({ width, height });
    await page.setRequestInterception(true);
    page.on('request', req => {
      const u = req.url();
      if (u.startsWith(base)) return req.continue();
      if (u === API) {
        if (req.method() === 'OPTIONS') return req.respond({ status: 204, headers: cors });
        state.posts.push(JSON.parse(req.postData()));
        const a = answer();
        if (a === 'abort') return req.abort();
        return req.respond({ status: a.status, headers: cors, contentType: 'application/json', body: JSON.stringify(a.body) });
      }
      state.outside.push(u); req.abort();
    });
    await page.goto(base + '/support', { waitUntil: 'domcontentloaded' });
    return { page, state };
  }
  async function fill(page, email, msg, topic) {
    await page.evaluate((e, m, t) => { const f = document.getElementById('sf'); f.email.value = e; f.message.value = m; if (t) f.topic.value = t; }, email, msg, topic || '');
    await page.evaluate(() => document.getElementById('sf-send').click());
  }
  const status = page => page.$eval('#sf-status', n => ({ text: n.textContent, cls: n.className }));
  const settled = page => page.waitForFunction(() => { const n = document.getElementById('sf-status'); return n.textContent && n.textContent !== 'Sending...'; }, { timeout: 5000 });

  // layout at phone and desktop width
  for (const [w, h] of [[390, 844], [1440, 900]]) {
    const { page, state } = await open(w, h, () => ({ status: 200, body: { ok: true } }));
    const m = await page.evaluate(() => {
      const r = id => { const b = document.getElementById(id).getBoundingClientRect(); return { w: Math.round(b.width), h: Math.round(b.height) }; };
      const hp = document.querySelector('.sf-hp').getBoundingClientRect();
      return { over: document.documentElement.scrollWidth - window.innerWidth, email: r('sf-email'), topic: r('sf-topic'), msg: r('sf-msg'), send: r('sf-send'),
        hpLeft: hp.right, opts: document.querySelectorAll('#sf-topic option').length, toc: !!document.querySelector('a[href="#write"]'),
        font: getComputedStyle(document.getElementById('sf-email')).fontSize, labels: document.querySelectorAll('#sf label[for]').length };
    });
    ok(m.over <= 0, w + ': no sideways scroll');
    ok(m.email.h >= 44 && m.topic.h >= 44 && m.send.h >= 44, w + ': fields and button at least 44 px tall');
    ok(m.msg.h >= 120, w + ': message box is roomy');
    ok(m.email.w <= w - 32, w + ': field fits the screen');
    ok(m.hpLeft < 0, w + ': bot trap is off screen');
    ok(m.opts === 7, w + ': seven topics');
    ok(m.toc, w + ': page index links to the form');
    ok(parseFloat(m.font) >= 16, w + ': 16 px text (no zoom on iPhone)');
    ok(m.labels === 3, w + ': every field has a label');
    ok(state.errors.length === 0, w + ': no page errors');
    ok(state.posts.length === 0, w + ': nothing sent on load');
    await page.close();
  }

  // refused before sending
  {
    const { page, state } = await open(390, 844, () => ({ status: 200, body: { ok: true } }));
    await fill(page, '', 'My alerts stopped this morning.');
    let s = await status(page);
    ok(/email address/i.test(s.text) && /err/.test(s.cls) && state.posts.length === 0, 'empty address: message, nothing sent');
    await fill(page, 'not-an-address', 'My alerts stopped this morning.');
    ok(state.posts.length === 0, 'bad address: nothing sent');
    await fill(page, 'buyer@example.com', 'short');
    s = await status(page);
    ok(/little more/i.test(s.text) && state.posts.length === 0, 'short message: message, nothing sent');
    await page.close();
  }

  // success
  {
    const { page, state } = await open(390, 844, () => ({ status: 200, body: { ok: true } }));
    await fill(page, ' buyer@example.com ', 'My alerts stopped this morning.', 'discord');
    await settled(page);
    const s = await status(page);
    ok(state.posts.length === 1, 'one request');
    const p = state.posts[0];
    ok(p.email === 'buyer@example.com' && p.topic === 'discord' && p.message === 'My alerts stopped this morning.', 'request carries address, topic, message');
    ok(p.website === '' && p.page === '/support', 'bot trap empty, page sent');
    ok(/Message sent/.test(s.text) && /within 24 hours/.test(s.text) && /ok/.test(s.cls), 'success message');
    const after = await page.evaluate(() => ({ e: document.getElementById('sf').email.value, m: document.getElementById('sf').message.value, d: document.getElementById('sf-send').disabled }));
    ok(after.e === '' && after.m === '' && after.d === false, 'form cleared, button usable');
    ok(state.errors.length === 0, 'no page errors');
    await page.close();
  }

  // every failure shows the address and never says "sent"
  const fails = [
    ['daily limit', () => ({ status: 429, body: { detail: { error: 'busy', email: MAIL } } }), /limit for today/i],
    ['sender limit', () => ({ status: 429, body: { detail: { error: 'too_many', email: MAIL } } }), /several messages/i],
    ['send failed', () => ({ status: 502, body: { detail: { error: 'send_failed', email: MAIL } } }), /could not send/i],
    ['switched off', () => ({ status: 503, body: { detail: { error: 'unavailable', email: MAIL } } }), /could not send/i],
    ['too long', () => ({ status: 422, body: { detail: { error: 'message_too_long', email: MAIL } } }), /too long/i],
    ['network down', () => 'abort', /could not send/i],
    ['200 without ok', () => ({ status: 200, body: {} }), /could not send/i],
    ['odd body', () => ({ status: 500, body: 'oops' }), /could not send/i],
  ];
  for (const [name, answer, expect] of fails) {
    const { page, state } = await open(390, 844, answer);
    await fill(page, 'buyer@example.com', 'My alerts stopped this morning.');
    await settled(page);
    const s = await status(page);
    ok(expect.test(s.text), name + ': right message');
    ok(s.text.includes(MAIL), name + ': shows the address');
    ok(!/Message sent/.test(s.text) && /err/.test(s.cls), name + ': never claims success');
    const kept = await page.evaluate(() => ({ m: document.getElementById('sf').message.value, d: document.getElementById('sf-send').disabled }));
    ok(kept.m === 'My alerts stopped this morning.' && kept.d === false, name + ': message kept, can retry');
    ok(state.errors.length === 0, name + ': no page errors');
    await page.close();
  }

  // source checks
  const html = fs.readFileSync(path.join(root, 'support.html'), 'utf8');
  ok(html.includes(API), 'page posts to the backend route');
  ok(html.includes('mailto:' + MAIL) && html.includes('discord.gg/gjKD4auXhK'), 'email and Discord still offered');
  ok(!html.includes('help@snypd.store'), 'old address absent');
  ok(/id="discord"/.test(html) && html.includes('/link'), 'Discord alerts section present');
  ok(/<form[^>]*id="sf"[\s\S]*discord\.gg\/gjKD4auXhK[\s\S]*<\/form>/.test(html), 'Discord link inside the form');

  // French page: same form, same topic keys, French texts
  const fr = fs.readFileSync(path.join(root, 'fr/support.html'), 'utf8');
  const keys = h => (h.match(/<option value="[a-z]+"/g) || []).join(',');
  ok(/<html[^>]*lang="fr"/.test(fr) && fr.includes('id="sf"') && fr.includes(API), 'French page has the form');
  ok(keys(fr) === keys(html) && keys(fr).split(',').length === 7, 'French topics use the same keys');
  ok(/<form[^>]*id="sf"[\s\S]*discord\.gg\/gjKD4auXhK[\s\S]*<\/form>/.test(fr), 'French form carries the Discord link');
  ok(fr.includes('ENVOYER LE MESSAGE') && fr.includes('Message envoy') && fr.includes('mailto:' + MAIL), 'French texts and address');
  ok(fr.includes('hreflang="en" href="https://www.snypd.store/support"') && html.includes('hreflang="fr" href="https://www.snypd.store/fr/support"'), 'pages link to each other');
  ok(!fr.includes('@@') && !html.includes('@@'), 'no unfilled placeholders');

  await browser.close(); server.close();
  console.log('PASS: ' + checks + ' support-form checks; no production requests.');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
