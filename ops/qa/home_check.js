// node ops/qa/home_check.js <file-or-url>: homepage overflow + footer links at 390/1440.
const puppeteer = require('puppeteer-core');
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  for (const w of [390, 1440]) {
    const pg = await b.newPage(); await pg.setViewport({ width: w, height: 900 });
    const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto(process.argv[2], { waitUntil: 'networkidle2' });
    const r = await pg.evaluate(() => ({ overflow: document.documentElement.scrollWidth > window.innerWidth,
      foot: [...document.querySelectorAll('a[hreflang]')].map(a => a.getAttribute('href')) }));
    console.log(w, JSON.stringify(r), 'pageerrors', errs.length);
    await pg.close();
  }
  await b.close();
})();
