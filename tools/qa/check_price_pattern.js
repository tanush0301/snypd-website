// Verify the new inverted-price pattern compiles and translates correctly,
// reading the real generated assets/i18n.js rather than a copy of fr.py.
const fs = require('fs');

const src = fs.readFileSync('assets/i18n.js', 'utf8');

// Pull the PATTERNS object literal out of the generated runtime.
const marker = 'var PATTERNS = ';
const start = src.indexOf(marker);
if (start === -1) { console.error('FAIL: PATTERNS not found in i18n.js'); process.exit(1); }
let depth = 0, end = -1;
for (let i = start + marker.length; i < src.length; i++) {
  const ch = src[i];
  if (ch === '[' || ch === '{') depth++;
  else if (ch === ']' || ch === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
}
const patterns = JSON.parse(src.slice(start + marker.length, end)).fr;
console.log('patterns loaded:', patterns.length);

const target = patterns.find((p) => p[0].indexOf('lowest price is above') !== -1);
if (!target) { console.error('FAIL: new pattern absent from generated output'); process.exit(1); }
console.log('pattern:', target[0]);

const cases = [
  ['This link asks for items from 5 to 2, so the lowest price is above the highest and Vinted returns nothing. Fix the price range on Vinted and copy the link again.',
   ['5', '2']],
  ['This link asks for items from 150.0 to 30, so the lowest price is above the highest and Vinted returns nothing. Fix the price range on Vinted and copy the link again.',
   ['150.0', '30']],
];

let ok = true;
for (const [input, expect] of cases) {
  const m = input.match(new RegExp(target[0]));
  if (!m) { console.error('FAIL: no match for', input.slice(0, 50)); ok = false; continue; }
  const out = target[1].replace(/\$1/g, m[1]).replace(/\$2/g, m[2]);
  const good = m[1] === expect[0] && m[2] === expect[1] && out.indexOf('$') === -1;
  console.log((good ? 'OK   ' : 'FAIL ') + 'captured=' + m[1] + '/' + m[2]);
  console.log('     FR: ' + out);
  if (!good) ok = false;
}

// A valid range must NOT be caught by this pattern (the dashboard check is what
// rejects it, not the translator).
const valid = 'This link asks for items from 30 to 150, so the lowest price is above the highest and Vinted returns nothing.';
console.log('(control) valid-range text would still match the pattern by design:', !!valid.match(new RegExp(target[0])));

process.exit(ok ? 0 : 1);
