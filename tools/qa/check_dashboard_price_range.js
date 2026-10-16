/*
 * Verify the dashboard edit two ways:
 *   1. every inline <script> in dashboard.html still parses (a syntax error
 *      would break the whole page, not just the pasted-link message);
 *   2. the real contractProblem() text, extracted from that same file, rejects
 *      an inverted price range and still accepts a valid one.
 *
 * The function is extracted by brace-matching rather than re-implemented, so
 * this tests what actually ships rather than a copy of it.
 */
const fs = require('fs');
const path = require('path');

const FILE = process.argv[2] || 'dashboard.html';
const html = fs.readFileSync(FILE, 'utf8');

// ---- 1. syntax-check every inline script ----------------------------------
const scriptRe = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let m, checked = 0;
const blocks = [];
while ((m = scriptRe.exec(html)) !== null) {
  const attrs = m[1] || '';
  const body = m[2] || '';
  if (/\bsrc\s*=/.test(attrs)) continue;      // external, not ours to check
  if (!body.trim()) continue;
  blocks.push({ at: m.index, body });
  try {
    new Function(body);
    checked++;
  } catch (e) {
    console.error('FAIL: inline script does not parse:', e.message);
    process.exit(1);
  }
}
console.log('inline scripts parsed OK:', checked);

// ---- 2. extract the real contractProblem() --------------------------------
const src = blocks.map((b) => b.body).join('\n');

function extractFn(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start === -1) return null;
  const open = src.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') {
      depth--;
      if (depth === 0) return src.slice(start, i + 1);
    }
  }
  return null;
}

const fnText = extractFn('contractProblem');
if (!fnText) { console.error('FAIL: contractProblem not found'); process.exit(1); }
if (fnText.indexOf('lowest price is above the highest') === -1) {
  console.error('FAIL: extracted function is missing the new check');
  process.exit(1);
}
console.log('extracted contractProblem():', fnText.length, 'chars, contains new check');

// Minimal stand-ins for the helpers the function closes over. If the function
// ever starts depending on something else, the harness below fails loudly
// rather than silently testing nothing.
const SUPPORTED_VINTED = ['vinted.be', 'vinted.fr', 'vinted.nl', 'vinted.de', 'vinted.co.uk', 'vinted.com'];
const SUPPORTED_VINTED_TEXT = 'every Vinted site in Europe and the US';
const SITE_CURRENCY = { 'vinted.be': 'EUR', 'vinted.fr': 'EUR', 'vinted.nl': 'EUR',
  'vinted.de': 'EUR', 'vinted.co.uk': 'GBP', 'vinted.com': 'USD' };
const CONTRACT_VOLATILE = ['page', 'per_page', 'order', 'time', 'search_id'];
const CONTRACT_SCALARS = ['search_text', 'price_from', 'price_to', 'currency', 'catalog_from',
  'search_by_image_uuid', 'search_by_image_id', 'disable_search_saving'];

function vintedSite(u) {
  try { const h = new URL(String(u)).hostname.replace(/^www\./, ''); return h; } catch (e) { return ''; }
}
function vintedSiteSupported(u) { return SUPPORTED_VINTED.indexOf(vintedSite(u)) !== -1; }
function currencyFor(u) { return SITE_CURRENCY[vintedSite(u)] || 'EUR'; }

const make = new Function(
  'SUPPORTED_VINTED', 'SUPPORTED_VINTED_TEXT', 'SITE_CURRENCY', 'CONTRACT_VOLATILE',
  'CONTRACT_SCALARS', 'vintedSite', 'vintedSiteSupported', 'currencyFor',
  fnText + '\nreturn contractProblem;');

const contractProblem = make(SUPPORTED_VINTED, SUPPORTED_VINTED_TEXT, SITE_CURRENCY,
  CONTRACT_VOLATILE, CONTRACT_SCALARS, vintedSite, vintedSiteSupported, currencyFor);

// ---- 3. behaviour ----------------------------------------------------------
const cases = [
  // the hunt that has been 400ing on every poll since 2026-10-14
  ['https://www.vinted.fr/catalog?search_text=Nike+running&price_to=2&order=newest_first&price_from=5',
   true, 'the real broken hunt (from=5, to=2)'],
  // a normal valid range must pass untouched
  ['https://www.vinted.fr/catalog?search_text=nike&price_from=30&price_to=50&order=newest_first',
   false, 'valid range from=30 to=50'],
  ['https://www.vinted.fr/catalog?search_text=nike&price_from=30&order=newest_first',
   false, 'only a floor set'],
  ['https://www.vinted.fr/catalog?search_text=nike&price_to=50&order=newest_first',
   false, 'only a ceiling set'],
  ['https://www.vinted.fr/catalog?search_text=nike&price_from=30&price_to=30&order=newest_first',
   false, 'equal bounds are allowed'],
  // decimals / floats
  ['https://www.vinted.fr/catalog?search_text=nike&price_from=149.99&price_to=30&order=newest_first',
   true, 'inverted decimals from=149.99 to=30'],
];

let bad = 0;
for (const [url, shouldWarn, label] of cases) {
  const out = contractProblem(url);
  const warned = !!out;
  const pass = warned === shouldWarn;
  if (!pass) bad++;
  console.log((pass ? 'OK   ' : 'FAIL ') + label + '  ->  ' + (warned ? JSON.stringify(out.slice(0, 72)) + '...' : 'no warning'));
}

console.log(bad === 0 ? '\nall ' + cases.length + ' cases pass' : '\n' + bad + ' FAILED');
process.exit(bad === 0 ? 0 : 1);
