// node ops/social/render.js OUT_DIR  -- renders every <set>/deck.html under OUT_DIR to
// <set>/01.png, 02.png ... at 1080x1350 (Instagram portrait / TikTok photo mode).
// Uses the repo's puppeteer-core and the locally installed Chrome; fonts load from the repo.
const fs = require('fs');
const path = require('path');
const puppeteer = require(path.join(__dirname, '..', '..', 'node_modules', 'puppeteer-core'));
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

(async () => {
  const out = process.argv[2];
  if (!out) { console.error('usage: node render.js OUT_DIR'); process.exit(1); }
  const sets = fs.readdirSync(out).filter(d => fs.existsSync(path.join(out, d, 'deck.html')));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--allow-file-access-from-files'] });
  let total = 0;
  for (const s of sets) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 1 });
    await page.goto('file:///' + path.join(out, s, 'deck.html').replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
    await page.evaluate(() => document.fonts.ready);
    const fontsOk = await page.evaluate(() => document.fonts.check('900 40px Cabinet') && document.fonts.check('400 20px DMMono'));
    if (!fontsOk) { console.error('FONTS NOT LOADED for', s); process.exit(2); }
    const slides = await page.$$('section.slide');
    for (let i = 0; i < slides.length; i++) {
      const overflow = await slides[i].evaluate(el => [...el.querySelectorAll('*')].some(c => {
        const r = c.getBoundingClientRect(), p = el.getBoundingClientRect();
        return r.right > p.right + 1 || r.bottom > p.bottom + 1;
      }));
      if (overflow) console.error('WARNING overflow', s, i + 1);
      await slides[i].screenshot({ path: path.join(out, s, String(i + 1).padStart(2, '0') + '.png') });
      total++;
    }
    await page.close();
    console.log('rendered', s, slides.length);
  }
  await browser.close();
  console.log('total', total);
})();
