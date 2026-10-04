// Real dashboard screenshots for scene.html, taken against ops/qa_mock.js (never production):
//   python ops/social/video/qa_server.py        (serves the repo + /dashboard.qa.html on 127.0.0.1:8900)
//   node   ops/social/video/capture.js          -> shots/paste_form.png, shots/hunt_0.png
// Then: node render_video.js OUT_DIR && python encode.py OUT_DIR
const path = require('path');
const puppeteer = require(path.join(__dirname, '..', '..', '..', 'node_modules', 'puppeteer-core'));
const OUT = path.join(__dirname, 'shots');
const URL_UK = 'https://www.vinted.co.uk/catalog?search_text=nike%20dunk%20low&price_to=45&currency=GBP&status_ids[]=2&status_ids[]=3&order=newest_first';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  const p = await b.newPage();
  await p.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
  await p.goto('http://127.0.0.1:8900/dashboard.qa.html?plan=elite', { waitUntil: 'networkidle2', timeout: 30000 });
  await p.mouse.move(400, 400); await p.mouse.wheel({ deltaY: 50 });  // the feed only starts on real activity
  await sleep(2500);
  await p.click('#filter-pill');
  await sleep(1200);
  await p.click('#filter-new-name'); await p.keyboard.type('Nike Dunk Low under 45', { delay: 10 });
  await p.click('#filter-new-url'); await p.keyboard.type(URL_UK, { delay: 2 });
  await sleep(800);
  await p.evaluate(() => { const u = document.querySelector('#filter-new-url'); u.blur(); u.scrollLeft = 0; u.setSelectionRange(0, 0); });
  await (await p.$('.filter-sheet__new-form')).screenshot({ path: path.join(OUT, 'paste_form.png') });
  await p.click('#filter-new-save');
  await sleep(1500);
  await (await p.$('#filter-sheet-list > *')).screenshot({ path: path.join(OUT, 'hunt_0.png') });
  const errors = await p.evaluate(() => (window.__qaErrors || []).length);
  await b.close();
  console.log('shots written, page errors:', errors);
  if (errors) process.exit(3);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
