// Real dashboard screenshots at phone size for the homepage product video (v3, 23 Nov 2026),
// taken against ops/qa_mock.js (never production):
//   python ops/social/video/qa_server_v3.py
//   NODE_PATH=<main checkout>/node_modules node ops/social/video/capture_v3.js [query]
// -> shots/v3_feed.png (first screen of the feed) and prints what the page shows.
const path = require('path');
const puppeteer = require('puppeteer-core');
const OUT = path.join(__dirname, 'shots');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const QUERY = process.argv[2] || 'plan=elite&pr=1';

(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  const p = await b.newPage();
  await p.setViewport({ width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  await p.goto('http://127.0.0.1:8902/dashboard.qa.html?' + QUERY, { waitUntil: 'networkidle2', timeout: 30000 });
  await p.mouse.move(200, 400); await p.mouse.wheel({ deltaY: 30 });   // the feed only starts on real activity
  await sleep(3500);
  // dismiss the notices the way a user would (their own buttons), so the feed is on the first screen
  const dismissed = [];
  for (const sel of ['#alerts-setup-later', '#email-optin-no', '#stats-note-ok']) {
    const vis = await p.evaluate(s => { const e = document.querySelector(s); return !!(e && e.offsetParent !== null); }, sel);
    if (vis) { await p.evaluate(s => document.querySelector(s).click(), sel); dismissed.push(sel); await sleep(400); }
  }
  await p.evaluate(() => window.scrollTo(0, 0));
  await sleep(600);
  await p.screenshot({ path: path.join(OUT, 'v3_feed.png') });
  const info = await p.evaluate(() => {
    const cards = [...document.querySelectorAll('.card')].filter(e => e.offsetHeight > 60);
    const r = (e) => { const b = e.getBoundingClientRect(); return { top: Math.round(b.top), h: Math.round(b.height), w: Math.round(b.width) }; };
    const above = [...document.querySelectorAll('#elite-banner, #alerts-setup-card, #email-optin-card, #stats-note, #dc-join, #claim-hint, #broad-hunt')]
      .filter(e => e.offsetParent !== null).map(e => e.id + ':' + Math.round(e.getBoundingClientRect().height));
    return {
      errors: (window.__qaErrors || []).length,
      cards: cards.length,
      rated: cards.filter(c => c.querySelector('.pr-line')).length,
      first: cards[0] ? r(cards[0]) : null,
      firstText: cards[0] ? cards[0].innerText.replace(/\s+/g, ' ').slice(0, 220) : null,
      stillAbove: above
    };
  });
  // video shots: claim hint closed by its own button, then the screen with the first card in view, and two single cards
  const hintClosed = await p.evaluate(() => {
    const h = document.querySelector('#claim-hint'); if (!h || h.offsetParent === null) return false;
    const btn = [...h.querySelectorAll('button, a')].find(e => /got it/i.test(e.textContent)); if (!btn) return false;
    btn.click(); return true;
  });
  await sleep(400);
  const shots = [];
  for (const i of [0, 1, 3]) {
    const box = await p.evaluate((n) => {
      const c = [...document.querySelectorAll('.card')].filter(e => e.offsetHeight > 60)[n];
      if (!c) return null;
      window.scrollTo(0, window.scrollY + c.getBoundingClientRect().top - 112);
      return true;
    }, i);
    if (!box) continue;
    await sleep(700);
    const r = await p.evaluate((n) => {
      const c = [...document.querySelectorAll('.card')].filter(e => e.offsetHeight > 60)[n];
      const b = c.getBoundingClientRect();
      return { x: b.left, y: b.top, width: b.width, height: b.height, text: c.innerText.replace(/\s+/g, ' ').slice(0, 160) };
    }, i);
    if (i === 0) {
      // the phone screen first, before any element screenshot can move the page
      await p.screenshot({ path: path.join(OUT, 'v3_screen.png') });
      const pr = await p.evaluate(() => {
        const c = [...document.querySelectorAll('.card')].filter(e => e.offsetHeight > 60)[0];
        const b = c.querySelector('.pr-line').getBoundingClientRect();
        const f = document.querySelector('#filter-pill'); const fb = f ? f.getBoundingClientRect() : null;
        const pc = (v, of) => Math.round(v / of * 1000) / 10;
        return { ring: { left: pc(b.left, innerWidth), top: pc(b.top, innerHeight), width: pc(b.width, innerWidth), height: pc(b.height, innerHeight) },
          pillTop: fb ? pc(fb.top, innerHeight) : null, pillBottom: fb ? pc(fb.bottom, innerHeight) : null };
      });
      console.log('PR_LINE_PERCENT', JSON.stringify(pr));
    }
    const handle = (await p.$$('.card'))[await p.evaluate((n) => {
      const all = [...document.querySelectorAll('.card')];
      return all.indexOf(all.filter(e => e.offsetHeight > 60)[n]);
    }, i)];
    await handle.screenshot({ path: path.join(OUT, 'v3_card' + i + '.png') });   // the element itself, not a page clip
    shots.push({ i, top: Math.round(r.y), h: Math.round(r.height), text: r.text });
  }
  await b.close();
  console.log(JSON.stringify({ dismissed, hintClosed, shots, ...info }, null, 1));
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
