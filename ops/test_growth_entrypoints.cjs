/* Run: node ops/test_growth_entrypoints.cjs. No network or production writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const plans = fs.readFileSync(path.join(root, 'plans.html'), 'utf8');
let passed = 0;
const tick = () => new Promise(resolve => setImmediate(resolve));
function section(text, start, end) {
  const a = text.indexOf(start), b = text.indexOf(end, a);
  assert(a >= 0 && b > a); return text.slice(a, b);
}
function elements() {
  const map = new Map();
  return id => { if (!map.has(id)) map.set(id, { hidden: true, textContent: '' }); return map.get(id); };
}
const paint = section(home, '  function paintFounding() {', '  /* ---------- nav:');
for (const claimed of [null, undefined, NaN, Infinity, -1, 0.5, '20']) {
  const $ = elements(); vm.runInNewContext(paint + '\npaintFounding();', { $, s: {claimed} });
  assert.equal($('founding-offer').hidden, true);
  assert.equal($('founding-line').textContent, 'Free plan, no card.'); passed++;
}
for (const claimed of [0, 50, 99]) {
  const $ = elements(); vm.runInNewContext(paint + '\npaintFounding();', { $, s: {claimed} });
  assert.equal($('founding-offer').hidden, false);
  assert.match($('founding-badge').textContent, new RegExp((100-claimed) + ' OF 100 SPOTS LEFT')); passed++;
}
for (const claimed of [100, 329]) {
  const $ = elements(); vm.runInNewContext(paint + '\npaintFounding();', { $, s: {claimed} });
  assert.equal($('founding-line').textContent, 'Free plan, no card.');
  assert.equal($('founding-badge').textContent, 'FOUNDING · ALL 100 TAKEN'); passed++;
}
assert.match(home, /id="founding-offer" hidden/);
assert.doesNotMatch(home, /FOUNDING STATUS OPEN/);
assert.match(plans, /id="founding-line" hidden><\/span>/);
assert.match(plans, /<tr data-founding-row hidden>/);
assert.match(fs.readFileSync(path.join(root,'ops/seo/gen_regions.py'),'utf8'), /data-founding-row hidden/);
passed++;
assert(plans.indexOf('data-section="chooser"') < plans.indexOf('data-section="cards"'));
assert.equal((plans.match(/id="q-goal"/g) || []).length, 1); passed++;
const counter = section(plans, '  // ----- Founding counter', '\n})();');
(async () => {
  for (const data of [null, {}, {remaining:-1}, {remaining:101}, {remaining:'5'}, {remaining:1.5}, {remaining:0}, {remaining:15}]) {
    const $ = elements(); const row = {hidden:true};
    vm.runInNewContext(counter, { $, Number, document:{querySelector:()=>row}, FOUNDING_ENDPOINT:'test',
      fetch:async()=>({ok:true,json:async()=>data}) });
    await tick();
    const available = data && data.remaining === 15;
    assert.equal($('founding-line').hidden, !available); assert.equal(row.hidden, !available); passed++;
  }
  for (const fail of [true, false]) {
    const $ = elements(); const row={hidden:true};
    vm.runInNewContext(counter, { $, Number, document:{querySelector:()=>row}, FOUNDING_ENDPOINT:'test',
      fetch:async()=>{ if(fail) throw Error('offline'); return {ok:false}; } });
    await tick(); assert.equal($('founding-line').hidden,true); assert.equal(row.hidden,true); passed++;
  }
  for (const file of ['index.html','plans.html','dashboard.html']) {
    const html=fs.readFileSync(path.join(root,file),'utf8');
    for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
      if (/\bsrc\s*=|application\/ld\+json/i.test(match[1])) continue;
      new vm.Script(match[2], {filename:file});
    }
  }
  new vm.Script(fs.readFileSync(path.join(root,'assets/i18n.js'),'utf8'));
  passed++;
  console.log(`PASS: ${passed} growth entry-point checks, including inline-script parsing.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
