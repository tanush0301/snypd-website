/* Run: node test_share_hunt.cjs <site root>. No network, no browser.
   Runs the /invite inline script with a stubbed DOM and the dashboard's share helpers extracted from dashboard.html. */
const fs = require('fs'), vm = require('vm'), path = require('path'), assert = require('assert');
const root = process.argv[2] || '.';
let passed = 0;
const ok = (c, m) => { assert(c, m); passed++; };

// ---------- /invite ----------
const inv = fs.readFileSync(path.join(root, 'invite.html'), 'utf8');
const scripts = [...inv.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
const code = scripts[scripts.length - 1];
function el(attrs) {
  const a = Object.assign({}, attrs);
  return { a, textContent: '', getAttribute: k => (k in a ? a[k] : null), setAttribute: (k, v) => { a[k] = String(v); }, removeAttribute: k => { delete a[k]; } };
}
function runInvite(search, stored) {
  const iv = [el({ 'data-iv': 'gift' }), el({ 'data-iv': 'plain', hidden: '' })];
  const cta = [el({ href: '/signup' }), el({ href: '/signup' })];
  const hunt = [el({ hidden: '' }), el({ hidden: '' })];
  const words = el({}), max = el({});
  const fetches = [];
  const ctx = {
    URLSearchParams, JSON, Date, Math, Number, String, encodeURIComponent,
    location: { search },
    localStorage: { getItem: () => (stored ? JSON.stringify(stored) : null) },
    setTimeout: () => 0,
    fetch: (u, o) => { fetches.push(o); return { then: () => {} }; },
    document: {
      visibilityState: 'hidden', addEventListener: () => {}, removeEventListener: () => {},
      querySelectorAll: s => s === '[data-iv]' ? iv : s === '[data-invite-cta]' ? cta : s === '[data-iv-hunt]' ? hunt : [],
      querySelector: s => s === '[data-iv-hunt-words]' ? words : s === '[data-iv-hunt-max]' ? max : null
    }
  };
  vm.runInNewContext(code, ctx);
  return { href: cta[0].a.href, href2: cta[1].a.href, giftShown: !('hidden' in iv[0].a), plainShown: !('hidden' in iv[1].a),
           huntShown: !('hidden' in hunt[0].a) && !('hidden' in hunt[1].a), words: words.textContent, max: max.textContent };
}
let r = runInvite('?ref=ab23cd&src=hunt&hunt=nike%20dunk%20low&max=40');
ok(r.href === '/signup?ref=ab23cd&src=hunt&from=invite&hunt=nike%20dunk%20low&max=40', 'hunt carried: ' + r.href);
ok(r.href2 === r.href, 'both CTAs equal');
ok(r.giftShown && !r.plainShown, 'gift version with a code');
ok(r.huntShown && r.words === 'nike dunk low' && r.max === 'max 40', 'hunt box filled');
r = runInvite('?hunt=jordan%201');
ok(r.href === '/signup?from=invite&hunt=jordan%201', 'no code: plain sign-up keeps the hunt: ' + r.href);
ok(!r.giftShown && r.plainShown && r.huntShown && r.max === '', 'no code: neutral version, hunt shown, no max');
r = runInvite('?ref=ab23cd&hunt=' + encodeURIComponent('<script>alert(1)</script>'));
ok(r.words === '<script>alert(1)</script>', 'script-like words stay text');
ok(r.href.indexOf('<') < 0 && r.href.indexOf('%3Cscript%3E') > 0, 'script-like words are encoded in the link');
r = runInvite('?ref=ab23cd&hunt=' + 'a'.repeat(81));
ok(r.href === '/signup?ref=ab23cd&from=invite' && !r.huntShown, 'over-long words dropped');
r = runInvite('?ref=ab23cd&hunt=' + 'a'.repeat(80));
ok(r.huntShown, '80 chars accepted');
for (const bad of ['-5', 'abc', '0', '1e9', '']) {
  r = runInvite('?ref=ab23cd&hunt=polo&max=' + bad);
  ok(r.href === '/signup?ref=ab23cd&from=invite&hunt=polo' && r.max === '', 'bad max dropped: ' + bad);
}
r = runInvite('?ref=ab23cd&hunt=polo&max=19.6');
ok(/&max=20$/.test(r.href), 'max rounded to whole');
r = runInvite('?ref=ab23cd&src=card');
ok(r.href === '/signup?ref=ab23cd&src=card&from=invite' && !r.huntShown, 'src=card kept, no hunt box');
r = runInvite('?ref=ab23cd&src=bogus');
ok(r.href === '/signup?ref=ab23cd&from=invite', 'unknown src dropped');
r = runInvite('?max=40');
ok(r.href === '/signup?from=invite' && !r.huntShown, 'max without words ignored');
r = runInvite('');
ok(r.href === '/signup?from=invite' && r.plainShown && !r.huntShown, 'bare /invite');
r = runInvite('?hunt=polo', { c: 'zz99zz', s: 'hunt', t: Date.now() });
ok(r.href === '/signup?ref=zz99zz&src=hunt&from=invite&hunt=polo' && r.giftShown, 'stored code + hunt');
r = runInvite('?ref=AB23CD&hunt=%20%20nike%20%20%20tech%20');
ok(r.words === 'nike tech' && /hunt=nike%20tech$/.test(r.href), 'spaces collapsed');

// ---------- dashboard helpers ----------
const dash = fs.readFileSync(path.join(root, 'dashboard.html'), 'utf8').replace(/\r\n/g, '\n');
const grab = (re, name) => { const m = re.exec(dash); assert(m, 'not found: ' + name); return m[0]; };
const helpers = grab(/function huntShareWords\(u\) \{[\s\S]*?\n    \}/, 'huntShareWords') + '\n' + grab(/function huntShareMax\(u\) \{[\s\S]*?\n    \}/, 'huntShareMax')
  + '\n' + grab(/function claimPriceLine\(sp, amount, currency\) \{[\s\S]*?\n  \}/, 'claimPriceLine');
function dashCtx(free) {
  const ctx = { URL, Number, String, Math, isFinite,
    document: { body: { classList: { contains: c => c === 'pr-free' && free } } },
    fmtPrice: (a, c) => c + ' ' + a };
  vm.runInNewContext(helpers + '\nthis.W = huntShareWords; this.M = huntShareMax; this.P = claimPriceLine;', ctx);
  return ctx;
}
const d = dashCtx(false);
ok(d.W('https://www.vinted.fr/catalog?search_text=ralph%20lauren%20jumper&price_to=25') === 'ralph lauren jumper', 'words read');
ok(d.M('https://www.vinted.fr/catalog?search_text=x&price_to=25') === 25, 'max read');
ok(d.M('https://www.vinted.fr/catalog?search_text=x&price_to=19,5') === 20, 'comma max rounded');
ok(d.M('https://www.vinted.fr/catalog?search_text=x') === 0, 'no max = 0');
ok(d.M('https://www.vinted.fr/catalog?search_text=x&price_to=abc') === 0, 'bad max = 0');
ok(d.W('https://www.vinted.fr/catalog?brand_ids[]=53') === '', 'filter-only hunt has no words (no SHARE button)');
ok(d.W('not a url') === '' && d.M('not a url') === 0, 'broken link is safe');
ok(d.W('https://www.vinted.fr/catalog?search_text=' + 'a'.repeat(81)) === '', 'over-long words not shared');
ok(d.P({ p: 80, n: 40, m: 3000 }, 20, 'EUR') === "EUR 10 under this hunt's usual price", 'under usual price');
ok(d.P({ p: 80, n: 40 }, 20, 'EUR') === "Cheaper than 80% of this hunt's finds this week", 'cheaper than');
ok(d.P({ p: 80, n: 40, m: 2050 }, 20, 'EUR') === "Cheaper than 80% of this hunt's finds this week", 'under 1 unit falls back to percent');
ok(d.P({ p: 49, n: 40, m: 3000 }, 20, 'EUR') === '', 'unfavourable rank gives no line');
ok(d.P({ p: 80, n: 29 }, 20, 'EUR') === '', 'too few finds gives no line');
ok(d.P(undefined, 20, 'EUR') === '' && d.P(null, 20, 'EUR') === '' && d.P({}, 20, 'EUR') === '', 'missing price check gives no line');
ok(d.P({ p: 101, n: 40 }, 20, 'EUR') === '' && d.P({ p: '80', n: 40 }, 20, 'EUR') === '', 'malformed rank gives no line');
ok(dashCtx(true).P({ p: 80, n: 40, m: 3000 }, 20, 'EUR') === '', 'Free account gets no price line');

// ---------- wiring ----------
ok((dash.match(/data-fs-share/g) || []).length === 3, 'SHARE button + handler wired');
ok(/src=hunt&hunt=/.test(dash) && /p_src: 'hunt'/.test(dash), 'hunt link + counter');
ok(/src=card'/.test(dash) && /p_src: 'card'/.test(dash), 'card link + counter');
ok(!/drawImage/.test(grab(/function drawFindCard[\s\S]*?\n  \}\n/, 'drawFindCard')), 'find card draws no image (text only)');
for (const f of ['assets/consent.js', 'assets/auth.js', 'invite.html']) {
  ok(/announce\|hunt\|card\)\$/.test(fs.readFileSync(path.join(root, f), 'utf8')), 'src list has hunt + card: ' + f);
}
console.log('share hunt + find card: ' + passed + ' checks pass');
