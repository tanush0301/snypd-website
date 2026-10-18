const puppeteer = require('puppeteer-core');
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  const pg = await b.newPage();
  pg.on('console', m => { if (m.type() === 'error') console.log('console:', m.text(), JSON.stringify(m.location())); });
  pg.on('requestfailed', r => console.log('failed:', r.url()));
  pg.on('response', r => { if (r.status() >= 400) console.log('http', r.status(), r.url()); });
  await pg.goto(process.argv[2], { waitUntil: 'networkidle2' });
  await b.close();
})();
