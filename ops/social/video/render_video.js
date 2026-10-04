// node ops/social/video/render_video.js OUT_DIR  -- steps scene.html frame by frame (30 fps, 15 s)
// and writes OUT_DIR/frames/NNNN.jpg plus OUT_DIR/keyframes/*.png for review. encode.py turns the
// frames into an H.264 MP4. Same puppeteer-core + local Chrome as ../render.js.
const fs = require('fs');
const path = require('path');
const puppeteer = require(path.join(__dirname, '..', '..', '..', 'node_modules', 'puppeteer-core'));
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FPS = 30, SECONDS = 15, KEY = [0, 1.8, 3.0, 4.8, 6.6, 9.0, 10.8, 12.2, 14.0];

(async () => {
  const out = process.argv[2];
  if (!out) { console.error('usage: node render_video.js OUT_DIR'); process.exit(1); }
  for (const d of ['frames', 'keyframes']) fs.mkdirSync(path.join(out, d), { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file:///' + path.join(__dirname, 'scene.html').replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  const ok = await page.evaluate(() => document.fonts.check('900 40px Cabinet') && document.fonts.check('400 20px DMMono')
    && [...document.images].every(i => i.complete && i.naturalWidth > 0));
  if (!ok) { console.error('FONTS OR IMAGES NOT LOADED'); process.exit(2); }
  const total = FPS * SECONDS;
  for (let f = 0; f < total; f++) {
    await page.evaluate(t => window.setT(t), f / FPS);
    await page.screenshot({ path: path.join(out, 'frames', String(f).padStart(4, '0') + '.jpg'), type: 'jpeg', quality: 95 });
  }
  for (const t of KEY) {
    await page.evaluate(x => window.setT(x), t);
    await page.screenshot({ path: path.join(out, 'keyframes', 't' + t.toFixed(1) + '.png') });
  }
  await browser.close();
  console.log('frames', total, 'keyframes', KEY.length);
})();
