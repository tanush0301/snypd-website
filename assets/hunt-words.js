/* SNYPD hunt words check (Session 70, 7 Nov 2026; website repo outreach/43).
 *
 * Vinted's search only returns listings that contain EVERY word typed. A quick search like
 * "Ralph Lauren, Nike, Adidas" therefore asks for all three brands in one listing and finds almost nothing
 * (live 7 Nov 2026: 18 of 110 trials found zero listings; most had typed a list like that). This file spots
 * those searches before they are saved, and on saved hunts, and offers one-tap alternatives. It never blocks:
 * the page always lets the user keep the words as typed (collabs like "supreme north face" are real).
 *
 *   SnypdHuntWords.check(words) -> { kind, options, fixed, brands, words }
 *     kind    'list'   several things separated by , ; / | or " + "     options = each part (typo-fixed)
 *             'brands' 2+ different brands with no separator             options = each brand (+ the other words)
 *             'typo'   one brand misspelt (only brands of 8+ letters)    fixed   = the corrected words
 *             'long'   6+ words and nothing above                        no options
 *             ''       nothing to say
 * Pure, no DOM, pure ASCII (non-ASCII letters only as escapes). UMD: window.SnypdHuntWords / module.exports.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdHuntWords = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Display name -> extra spellings that mean the same brand. Matching is on folded text (lower case, no accents,
  // "&" and "'" removed). Sub-brands that are normally searched WITH their parent are not here on purpose
  // (jordan, yeezy, polo, wip), so "nike jordan 4" or "polo ralph lauren" stay one brand.
  var BRANDS = [
    ['Ralph Lauren'], ['Nike'], ['Adidas'], ['Lacoste'], ['Gant'], ['Hollister'], ['Abercrombie', 'abercrombie and fitch', 'abercrombie fitch', 'a&f'],
    ["Levi's", 'levis', 'levi'], ['Tommy Hilfiger', 'tommy'], ['Calvin Klein'], ['Stone Island'], ['The North Face', 'north face', 'tnf'],
    ['Carhartt'], ['Under Armour'], ['New Balance'], ['Puma'], ['Reebok'], ['Asics'], ['Converse'], ['Vans'], ['Fila'], ['Kappa'],
    ['Champion'], ['Fred Perry'], ['Barbour'], ['Timberland'], ['Dr. Martens', 'dr martens', 'doc martens'], ['Ugg'], ['Moncler'],
    ['Burberry'], ['Gucci'], ['Prada'], ['Louis Vuitton', 'lv'], ['Dior'], ['Chanel'], ['Balenciaga'], ['Armani', 'emporio armani'],
    ['Hugo Boss', 'boss'], ['Diesel'], ['Napapijri'], ['Columbia'], ['Patagonia'], ["Arc'teryx", 'arcteryx'], ['Supreme'], ['Stussy'],
    ['Zara'], ['H&M', 'hm'], ['Mango'], ['Uniqlo'], ['Michael Kors'], ['Longchamp'], ['Coach'], ['Eden Park'], ['Denim Tears'],
    ['Comfrt'], ['Corteiz'], ['Trapstar'], ['Salomon'], ['Birkenstock'], ['Veja'], ['Dickies'], ['Ellesse'], ['Lyle & Scott', 'lyle scott'],
    ['Superdry'], ['Jack & Jones', 'jack jones'], ['Pandora'], ['Swarovski'], ['Lego'], ['Pokemon'], ['Nintendo'], ['Playstation', 'ps5', 'ps4']
  ];
  var WORDS_LONG = 6;

  function fold(s) {
    s = String(s == null ? '' : s);
    try { s = s.normalize('NFKD').replace(/[\u0300-\u036f]/g, ''); } catch (e) {}
    return s.toLowerCase().replace(/[&']/g, ' ').replace(/[^a-z0-9.\s-]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function tokens(s) { return fold(s).split(' ').filter(Boolean); }

  // folded spelling (as a token list) -> display name; longest spellings first
  var SPELL = [];
  BRANDS.forEach(function (b) {
    var name = b[0];
    var all = [name].concat(b.slice(1));
    all.forEach(function (sp) {
      var t = tokens(sp);
      if (t.length) SPELL.push({ toks: t, flat: t.join(' '), name: name });
    });
  });
  SPELL.sort(function (a, b) { return b.toks.length - a.toks.length || b.flat.length - a.flat.length; });

  function lev(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i];
      var best = cur[0];
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (cur[j] < best) best = cur[j];
      }
      if (best > max) return max + 1;
      prev = cur;
    }
    return prev[b.length];
  }
  // Typos are only judged on spellings of 8+ letters: short words have too many real neighbours ("nikes", "gents").
  function allowed(flat) { return flat.length >= 11 ? 2 : (flat.length >= 8 ? 1 : 0); }

  // Brands found in a token list, left to right: [{name, from, to, typo}]
  function findBrands(toks) {
    var out = [], i = 0;
    while (i < toks.length) {
      var hit = null;
      for (var k = 0; k < SPELL.length && !hit; k++) {
        var sp = SPELL[k], n = sp.toks.length;
        if (i + n > toks.length) continue;
        var flat = toks.slice(i, i + n).join(' ');
        if (flat === sp.flat) { hit = { name: sp.name, from: i, to: i + n, typo: false }; break; }
        var lim = allowed(sp.flat);
        if (lim && lev(flat, sp.flat, lim) <= lim && flat.charAt(0) === sp.flat.charAt(0)) hit = { name: sp.name, from: i, to: i + n, typo: true };
      }
      if (hit) { out.push(hit); i = hit.to; } else { i++; }
    }
    return out;
  }
  // The words with every misspelt brand replaced by its display name (other words kept as typed, lower-cased only
  // when they came from a fixed span).
  function fixTypos(words) {
    var raw = String(words || '').replace(/\s+/g, ' ').trim();
    var toks = tokens(raw);
    var found = findBrands(toks);
    if (!found.some(function (f) { return f.typo; })) return null;
    var out = [], i = 0;
    found.forEach(function (f) {
      while (i < f.from) out.push(toks[i++]);
      out.push(f.typo ? f.name : toks.slice(f.from, f.to).join(' '));
      i = f.to;
    });
    while (i < toks.length) out.push(toks[i++]);
    return out.join(' ');
  }
  function clean(part) { return String(part || '').replace(/\s+/g, ' ').replace(/^[\s.,;:+\-]+|[\s.,;:+\-]+$/g, '').trim(); }

  function check(words) {
    var raw = String(words || '').replace(/\s+/g, ' ').trim();
    var res = { kind: '', options: [], fixed: null, brands: [], words: raw };
    if (!raw) return res;
    // 1. a list: separators between things
    // "42,5" (a European half size) and "1/2 zip" are not lists: protect digit,digit and digit/digit first.
    var guarded = raw.replace(/(\d)\s*([,\/])\s*(\d)/g, function (m, a, sep, b) { return a + (sep === ',' ? '\u0001' : '\u0002') + b; });
    var parts = guarded.split(/\s*(?:[,;|\/\n]|\s\+\s)\s*/)
      .map(function (p) { return clean(p.replace(/\u0001/g, ',').replace(/\u0002/g, '/')); })
      .filter(function (p) { return tokens(p).length > 0; });
    if (parts.length >= 2) {
      var seen = {};
      res.kind = 'list';
      parts.forEach(function (p) {
        var v = (fixTypos(p) || p).slice(0, 40).trim();
        var key = fold(v);
        if (key && !seen[key] && res.options.length < 6) { seen[key] = 1; res.options.push(v); }
      });
      if (res.options.length >= 2) return res;
      res.kind = ''; res.options = [];
    }
    var toks = tokens(raw);
    var found = findBrands(toks);
    var names = [];
    found.forEach(function (f) { if (names.indexOf(f.name) < 0) names.push(f.name); });
    res.brands = names;
    // 2. several brands in one search
    if (names.length >= 2) {
      var used = {};
      found.forEach(function (f) { for (var t = f.from; t < f.to; t++) used[t] = 1; });
      var rest = toks.filter(function (t, idx) { return !used[idx]; });
      var tail = rest.length && rest.length <= 3 ? ' ' + rest.join(' ') : '';
      res.kind = 'brands';
      res.options = names.slice(0, 6).map(function (n) { return (n + tail).slice(0, 40); });
      return res;
    }
    // 3. one misspelt brand
    var fixed = fixTypos(raw);
    if (fixed && fold(fixed) !== fold(raw)) { res.kind = 'typo'; res.fixed = fixed; res.options = [fixed]; return res; }
    // 4. many words
    if (toks.length >= WORDS_LONG) res.kind = 'long';
    return res;
  }

  return { check: check, fold: fold, _findBrands: function (s) { return findBrands(tokens(s)); }, _lev: lev, BRANDS: BRANDS };
}));
