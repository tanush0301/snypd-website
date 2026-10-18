// Screenshots + checks for the 18 Oct 2026 SEO release (PL/SV/NL pages, entry-page tracking).
// node ops/qa/shots_1018.js <base> <outdir>
const puppeteer = require('puppeteer-core');
const base = process.argv[2] || 'http://localhost:8956';
const out = process.argv[3] || '.';
const pages = ['/vinted-saved-searches', '/pl/vinted-zapisane-wyszukiwania', '/vinted-price-drop-notifications', '/de/vinted-preis-gesenkt-benachrichtigung', '/sv/vinted-sparade-sokningar', '/'];
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  const res = [];
  for (const p of pages) {
    for (const w of [390, 1440]) {
      const pg = await b.newPage();
      const errs = [];
      pg.on('pageerror', e => errs.push(String(e)));
      pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      await pg.setViewport({ width: w, height: 900 });
      const r = await pg.goto(base + p, { waitUntil: 'networkidle2', timeout: 30000 });
      const info = await pg.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > window.innerWidth,
        title: document.title,
        updated: (document.querySelector('.lg-meta time') || {}).textContent || null,
        signup: [...document.querySelectorAll('a[href^="/signup"]')].map(a => a.getAttribute('href')).slice(0, 2),
        plans: [...document.querySelectorAll('a[href^="/plans"]')].map(a => a.getAttribute('href')).slice(0, 1),
        other: [...document.querySelectorAll('a[href^="/vinted-bot-comparison"],a[href^="/nl/vinted-bot"]')].map(a => a.getAttribute('href')).slice(0, 1),
        ld: [...document.querySelectorAll('script[type="application/ld+json"]')].every(s => { try { JSON.parse(s.textContent); return true; } catch (e) { return false; } }),
      }));
      const name = p.replace(/\//g, '_').replace(/^_/, '') + '-' + w + '.png';
      await pg.screenshot({ path: out + '/' + name, fullPage: w === 390 ? false : false });
      res.push({ p, w, status: r.status(), errs: errs.filter(e => !/favicon|_vercel|googletagmanager|supabase/i.test(e)).length, ...info });
      await pg.close();
    }
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
