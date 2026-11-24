/*
 * Homepage v11 preview pages (ops/preview/home-a|b|c.html): the video autoplays muted on a first visit once in view,
 * not on a later visit or with reduced motion; the Play button works; no page errors, no sideways scroll.
 *   node ops/test_home_variants.cjs [screenshot folder]
 * Serves the repo's own files; every request to another host is blocked.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const root = path.join(__dirname, '..');
const shots = process.argv[2] || null;
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const m = p.match(/^\/pv\/([abc])$/);
  if (m) p = '/ops/preview/home-' + m[1] + '.html';
  else if (p.startsWith('/ops/')) { res.writeHead(404); return res.end('nope'); }
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(root, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(root, p + '.html');
  if (!f.startsWith(root) || !fs.existsSync(f)) { res.writeHead(404); return res.end('nope'); }
  const size = fs.statSync(f).size;
  const type = MIME[path.extname(f)] || 'application/octet-stream';
  const r = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range || '');
  if (r) {
    const a = +r[1], b = r[2] ? Math.min(+r[2], size - 1) : size - 1;
    res.writeHead(206, { 'content-type': type, 'accept-ranges': 'bytes', 'content-range': 'bytes ' + a + '-' + b + '/' + size, 'content-length': b - a + 1 });
    return fs.createReadStream(f, { start: a, end: b }).pipe(res);
  }
  res.writeHead(200, { 'content-type': type, 'accept-ranges': 'bytes', 'content-length': size, 'cache-control': 'no-store' });
  fs.createReadStream(f).pipe(res);
});
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const errors = [];
  async function open(v, vp, opts) {
    opts = opts || {};
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport(vp);
    if (opts.reduce) await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    if (opts.seen) await page.evaluateOnNewDocument(() => { try { localStorage.setItem('snypd_vid_seen', '1'); } catch (e) {} });
    page.on('pageerror', e => errors.push(v + ': ' + e.message));
    await page.setRequestInterception(true);
    page.on('request', r => (r.url().startsWith(base) || r.url().startsWith('data:')) ? r.continue() : r.abort());
    await page.goto(base + '/pv/' + v, { waitUntil: 'domcontentloaded' });
    await wait(900);
    return { page, ctx };
  }
  const state = page => page.evaluate(() => {
    const v = document.getElementById('vid-el'), b = document.getElementById('vid-play');
    const r = v.getBoundingClientRect();
    return { t: v.currentTime, paused: v.paused, src: !!v.getAttribute('src'), muted: v.muted, btnHidden: b.hidden,
      top: Math.round(r.top + scrollY), h: Math.round(r.height), w: Math.round(r.width),
      over: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      auto: document.documentElement.getAttribute('data-vid-auto'), on: document.querySelectorAll('[data-pt].on').length };
  });
  const toVideo = page => page.evaluate(() => document.getElementById('vid-el').scrollIntoView({ block: 'center' }));

  for (const v of ['a', 'b', 'c']) {
    for (const [name, vp] of [['desktop', { width: 1440, height: 900 }], ['phone', { width: 390, height: 812 }]]) {
      const tag = v.toUpperCase() + ' ' + name + ': ';
      // first visit
      let { page, ctx } = await open(v, vp);
      let s = await state(page);
      ok(s.over <= 0, tag + 'no sideways scroll');
      ok(s.auto === 'on', tag + 'autoplay is on for a first visit');
      ok(s.muted, tag + 'the video is muted');
      console.log(tag + 'video top ' + s.top + 'px of ' + vp.height + ', size ' + s.w + 'x' + s.h + (s.top + s.h / 2 <= vp.height ? ' (half or more in the first screen)' : ' (below the first screen)'));
      if (shots) await page.screenshot({ path: path.join(shots, v + '-' + name + '-top.png') });
      await toVideo(page); await wait(2600);
      s = await state(page);
      ok(s.src && !s.paused && s.t > 0.5, tag + 'the video plays by itself once in view (t=' + s.t.toFixed(1) + ')');
      ok(s.btnHidden, tag + 'the Play button is hidden while it plays');
      ok(s.on === 1, tag + 'one point is lit while it plays');
      if (shots) await page.screenshot({ path: path.join(shots, v + '-' + name + '-video.png') });
      if (shots && name === 'desktop') await page.screenshot({ path: path.join(shots, v + '-desktop-full.png'), fullPage: true });
      // scrolled away: pauses
      await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight)); await wait(700);
      s = await state(page);
      ok(s.paused, tag + 'the video pauses when out of view');
      await ctx.close();
      // later visit: no autoplay, Play works
      ({ page, ctx } = await open(v, vp, { seen: true }));
      await toVideo(page); await wait(1500);
      s = await state(page);
      ok(s.auto === 'off' && s.paused && !s.src && !s.btnHidden, tag + 'a later visit shows the poster and Play, nothing loads');
      await page.evaluate(() => document.getElementById('vid-play').click()); await wait(2200);
      s = await state(page);
      ok(!s.paused && s.t > 0.3 && s.btnHidden, tag + 'Play starts the video');
      await ctx.close();
      // reduced motion
      ({ page, ctx } = await open(v, vp, { reduce: true }));
      await toVideo(page); await wait(1500);
      s = await state(page);
      ok(s.auto === 'off' && s.paused && !s.src && !s.btnHidden, tag + 'reduced motion: no autoplay');
      await ctx.close();
    }
  }
  // two plays, then rest with Replay (design A, desktop; the video is about 14 s)
  {
    const { page, ctx } = await open('a', { width: 1440, height: 900 });
    await toVideo(page); await wait(2000);
    await page.evaluate(() => { const v = document.getElementById('vid-el'); v.currentTime = v.duration - 0.4; }); await wait(1800);
    let s = await state(page);
    ok(!s.paused && s.t < 5, 'after the first play it starts once more');
    await page.evaluate(() => { const v = document.getElementById('vid-el'); v.currentTime = v.duration - 0.4; }); await wait(1800);
    s = await state(page);
    const label = await page.$eval('#vid-play .hp-vid-btn', e => e.textContent);
    ok(s.paused && !s.btnHidden && /REPLAY/.test(label), 'after the second play it rests with a Replay button');
    await ctx.close();
  }
  ok(errors.length === 0, 'no page errors: ' + errors.join(' | '));
  await browser.close(); server.close();
  console.log('home variants: ' + passed + ' checks passed');
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
