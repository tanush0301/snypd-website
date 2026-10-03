// node ops/social/render_ads.js OUT_DIR  -- Meta ad versions of every <set>/deck.html under OUT_DIR:
//   <set>/ad/NN-4x5.png   1440x1800, Feed placements
//   <set>/ad/NN-9x16.png  1440x2560, Stories/Reels: the 4:5 slide scaled into Meta's text-safe zone
//                         (top 14%, bottom 35%, 6% each side kept free -- Meta ads guide, Reels specs)
// The "1/4" slide counter is hidden because each image can also run alone as a single-image ad.
// Same puppeteer-core + local Chrome as render.js; fonts load from the repo.
const fs = require('fs');
const path = require('path');
const puppeteer = require(path.join(__dirname, '..', '..', 'node_modules', 'puppeteer-core'));
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BG = '#0A0A0B';
const W = 1080, H = 1350, SH = 1920, DPR = 4 / 3;
const SAFE = { top: 0.14 * SH, bottom: 0.35 * SH, side: 0.06 * W };

(async () => {
  const out = process.argv[2];
  if (!out) { console.error('usage: node render_ads.js OUT_DIR'); process.exit(1); }
  const sets = fs.readdirSync(out).filter(d => fs.existsSync(path.join(out, d, 'deck.html')));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--allow-file-access-from-files'] });
  const scale = Math.min((SH - SAFE.top - SAFE.bottom) / H, (W - 2 * SAFE.side) / W);
  const w = W * scale, h = H * scale;
  let total = 0;
  for (const s of sets) {
    const adDir = path.join(out, s, 'ad');
    fs.mkdirSync(adDir, { recursive: true });
    const page = await browser.newPage();
    await page.setViewport({ width: W, height: H, deviceScaleFactor: DPR });
    await page.goto('file:///' + path.join(out, s, 'deck.html').replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
    await page.evaluate(() => {  // page.addStyleTag hung on these file:// decks
      const st = document.createElement('style');
      st.textContent = '.foot span:last-child { visibility: hidden; }';
      document.head.appendChild(st);
    });
    await page.evaluate(() => document.fonts.ready);
    const fontsOk = await page.evaluate(() => document.fonts.check('900 40px Cabinet') && document.fonts.check('400 20px DMMono'));
    if (!fontsOk) { console.error('FONTS NOT LOADED for', s); process.exit(2); }
    const slides = await page.$$('section.slide');
    const feeds = [];
    for (let i = 0; i < slides.length; i++) {
      feeds.push(path.join(adDir, String(i + 1).padStart(2, '0') + '-4x5.png'));
      await slides[i].screenshot({ path: feeds[i] });
    }
    // Same tab for the 9:16 composites: resizing a second, background tab hangs in headless Chrome.
    await page.setViewport({ width: W, height: SH, deviceScaleFactor: DPR });
    for (const feed of feeds) {
      const src = 'data:image/png;base64,' + fs.readFileSync(feed).toString('base64');
      await page.setContent(`<body style="margin:0;background:${BG}"><img src="${src}" style="position:absolute;`
        + `top:${SAFE.top}px;left:${(W - w) / 2}px;width:${w}px;height:${h}px"></body>`, { waitUntil: 'load' });
      await page.screenshot({ path: feed.replace('-4x5.png', '-9x16.png'), clip: { x: 0, y: 0, width: W, height: SH } });
      total += 2;
    }
    await page.close();
    console.log('rendered ads', s, slides.length * 2);
  }
  await browser.close();
  console.log('total', total);
})();
