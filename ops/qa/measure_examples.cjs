/* Measure example-card sizes on a dashboard file: node ops/qa/measure_examples.cjs <dashboard.html> <label> <shotdir> */
'use strict';
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..', '..');
const [dash, label, shots] = process.argv.slice(2);
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const swap = h => h.replace(/<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@2[^"]*"><\/script>/, '<script src="/__stock_engine.js"></script><script src="/__qa_mock.js"></script>');
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const send = (b, t) => { res.writeHead(200, { 'content-type': t }); res.end(b); };
  if (p === '/__qa_mock.js') return send(fs.readFileSync(path.join(root, 'ops/qa_mock.js')), MIME['.js']);
  if (p === '/__stock_engine.js') return send(fs.readFileSync(path.join(root, 'ops/stock_engine.js')), MIME['.js']);
  if (p === '/dashboard.html') return send(swap(fs.readFileSync(dash, 'utf8')), 'text/html; charset=utf-8');
  const f = path.join(root, p);
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  send(fs.readFileSync(f), MIME[path.extname(f)] || 'application/octet-stream');
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  fs.mkdirSync(shots, { recursive: true });
  for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844, isMobile: true, hasTouch: true }]) {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.setViewport(vp);
    await page.goto(base + '/dashboard.html?feed=empty&ex=4', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => document.querySelectorAll('#examples-list .card').length >= 1, { timeout: 15000 });
    await new Promise(r => setTimeout(r, 1200));
    const m = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#examples-list .card')];
      const thumbs = cards.map(c => c.querySelector('.thumb'));
      return {
        n: cards.length,
        cardW: cards.map(c => Math.round(c.getBoundingClientRect().width)),
        thumbH: thumbs.map(t => t ? Math.round(t.getBoundingClientRect().height) : 0),
        rowsTop: [...new Set(cards.map(c => Math.round(c.getBoundingClientRect().top)))].length,
        overflow: document.documentElement.scrollWidth > innerWidth,
        exTop: Math.round(document.getElementById('examples').getBoundingClientRect().top + scrollY),
      };
    });
    await page.evaluate(() => document.getElementById('examples').scrollIntoView());
    await page.screenshot({ path: path.join(shots, `${label}-${vp.width}.png`) });
    console.log(label, vp.width, JSON.stringify(m), 'errors', errs.length);
    await ctx.close();
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
