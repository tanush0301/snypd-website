/* Run: node ops/test_growth_entrypoints.cjs. No network or production writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const home = read('index.html');
const plans = read('plans.html');
let passed = 0;

/* The founding counter is gone (10 Nov 2026): all 100 numbers were issued, and the endpoint kept
   answering "4 remaining" because it counts rows and 4 founding accounts were deleted. No public
   page may advertise places or call the endpoint again. */
const COUNTER = /founding-members|SPOTS LEFT|spots left|paintFounding|FOUNDING_ENDPOINT|FOUNDING_URL|founding-offer|founding-line|data-founding-row|places sur les 100/;
for (const file of ['index.html', 'plans.html', 'signup.html', 'login.html', 'assets/auth.js', 'ops/seo/gen_regions.py',
  'vinted-bot-comparison.html', 'fr/comparatif-bot-vinted.html']) {
  assert.doesNotMatch(read(file), COUNTER, file + ' still carries the founding counter'); passed++;
}
// Homepage v6: the hero carries the search box, whose button is a real link to sign-up (works without script).
assert.match(home, /<form id="qs" class="hp-qs" action="\/signup" method="get"/);
assert.match(home, /<input id="qs-words" name="hunt"[^>]*maxlength="80"/);
assert.match(home, /<a id="qs-go" class="hp-btn" href="\/signup">/); passed++;
assert.doesNotMatch(home, /FOUNDING STATUS OPEN/);
// The FAQ still explains the promise to the people who hold it, and says the places are gone.
assert.match(plans, /What is a founding member\?<\/summary><p>The first 100 SNYPD accounts, free accounts included\. All of those places are taken\./); passed++;
assert.doesNotMatch(read('vinted-bot-comparison.html'), /counted live on the/);
assert.doesNotMatch(read('fr/comparatif-bot-vinted.html'), /affiché en direct sur la/); passed++;
// The heading must state the number of reason cards actually on the page.
for (const [file, re] of [['vinted-bot-comparison.html', /<h2>(\d+) reasons resellers choose SNYPD<\/h2>/], ['fr/comparatif-bot-vinted.html', /<h2>(\d+) raisons de choisir SNYPD<\/h2>/]]) {
  const html = read(file), m = html.match(re);
  assert(m, file + ': reasons heading not found');
  assert.equal((html.match(/class="rs-card"/g) || []).length, Number(m[1]), file + ': heading count != cards'); passed++;
}

assert(plans.indexOf('data-section="chooser"') < plans.indexOf('data-section="cards"'));
assert.equal((plans.match(/id="q-goal"/g) || []).length, 1); passed++;

for (const file of ['index.html', 'plans.html', 'dashboard.html']) {
  const html = read(file);
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    if (/\bsrc\s*=|application\/ld\+json/i.test(match[1])) continue;
    new vm.Script(match[2], { filename: file });
  }
}
new vm.Script(read('assets/i18n.js'));
new vm.Script(read('assets/auth.js'));
passed++;
console.log(`PASS: ${passed} growth entry-point checks, including inline-script parsing.`);
