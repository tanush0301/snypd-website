// NODE_PATH=<main checkout>/node_modules node ops/social/video/render_v3.js OUT_DIR [keys]
// Steps scene_v3.html frame by frame (FPS env var, default 30; length = window.DURATION) and writes
// OUT_DIR/frames/NNNN.jpg plus OUT_DIR/keyframes/*.png. With "keys" as the second argument only the
// keyframes are written (a quick look before a full render). encode.py turns the frames into an MP4.
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FPS = Number(process.env.FPS || 30), KEY = [0.2, 1.4, 2.6, 4.2, 5.6, 7.4, 9.4, 11.5, 13.0, 15.5];

(async () => {
  const out = process.argv[2], keysOnly = process.argv[3] === 'keys';
  if (!out) { console.error('usage: node render_v3.js OUT_DIR [keys]'); process.exit(1); }
  for (const d of ['frames', 'keyframes']) fs.mkdirSync(path.join(out, d), { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 1 });
  await page.goto('file:///' + path.join(__dirname, process.env.SCENE || 'scene_v3.html').replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  const ok = await page.evaluate(() => document.fonts.check('900 40px Cabinet') && document.fonts.check('400 20px DMMono')
    && [...document.images].every(i => i.complete && i.naturalWidth > 0));
  if (!ok) { console.error('FONTS OR IMAGES NOT LOADED'); process.exit(2); }
  const seconds = await page.evaluate(() => window.DURATION);
  const total = Math.round(FPS * seconds);
  if (!keysOnly) {
    for (let f = 0; f < total; f++) {
      await page.evaluate(t => window.setT(t), f / FPS);
      await page.screenshot({ path: path.join(out, 'frames', String(f).padStart(4, '0') + '.jpg'), type: 'jpeg', quality: 92 });
    }
  }
  const keys = (await page.evaluate(() => window.KEYS)) || KEY;
  for (const f of fs.readdirSync(path.join(out, 'keyframes'))) fs.unlinkSync(path.join(out, 'keyframes', f));   // no stale stills from an older timeline
  for (const t of keys) {
    await page.evaluate(x => window.setT(x), t);
    await page.screenshot({ path: path.join(out, 'keyframes', 't' + t.toFixed(1) + '.png') });
  }
  await browser.close();
  console.log('seconds', seconds, 'frames', keysOnly ? 0 : total, 'keyframes', KEY.length);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
