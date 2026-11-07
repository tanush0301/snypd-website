/*
 * Unit tests for assets/hunt-words.js (Session 70, outreach/43): the check that spots quick searches Vinted cannot
 * answer (every word must be in one listing). Cases are the real zero-find trial hunts of 6-7 Nov 2026 plus the
 * searches that must stay untouched.   node ops/test_hunt_words_core.cjs
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const W = require('../assets/hunt-words.js');
let passed = 0;
const eq = (a, b, m) => { assert.deepEqual(a, b, m); passed++; };
const k = s => W.check(s).kind;

// real zero-find trial hunts (7 Nov 2026)
eq(W.check("Ralph Lauren, Nike, Adidas, Levi's, Lacoste, Gant").options, ['Ralph Lauren', 'Nike', 'Adidas', "Levi's", 'Lacoste', 'Gant'], 'comma list -> each part');
eq(k('babyalarmen,voksi poser'), 'list', 'list without spaces');
eq(W.check('comfrt, hollister camo hoodie, hollister joggers,abercrombie').options.length, 4, 'four parts');
eq(W.check('vintage mohair jumper , vintage leather jacket, humberto,').options, ['vintage mohair jumper', 'vintage leather jacket', 'humberto'], 'trailing comma ignored');
eq(W.check('Ralph lauren, Lacoste, sto').kind, 'list', 'SE list');
eq(W.check('ralph loren pull nike'), { kind: 'brands', options: ['Ralph Lauren pull', 'Nike pull'], fixed: null, brands: ['Ralph Lauren', 'Nike'], words: 'ralph loren pull nike' }, 'two brands, typo fixed, item kept');
eq(W.check('Ralph Lauren Nike adidas Under armour Lacoste éden park').brands, ['Ralph Lauren', 'Nike', 'Adidas', 'Under Armour', 'Lacoste', 'Eden Park'], 'six brands, accent folded');
eq(W.check('rauph lauren Nike Denim tears spired hoodies').kind, 'brands', 'typo + brands');
eq(k('jujutsu kaisen tome 20 a 30'), 'long', 'six words');
eq(k('Hollister, Abercrombie and fitch, Coach'), 'list', 'list with "and" inside a brand');
// typos (only brands of 8+ letters)
eq(W.check('carhart jacket').fixed, 'Carhartt jacket', 'carhart -> Carhartt');
eq(W.check('ralph laurent pull').fixed, 'Ralph Lauren pull', 'laurent -> Lauren');
eq(W.check('Ralp lauren').options, ['Ralph Lauren'], 'ralp lauren');
// must stay untouched
for (const s of ['nike jordan 4', 'polo ralph lauren', 'nike 42,5', 'ralph lauren 1/2 zip', '3d emblem t shirt', 'fred perry jacke',
  'nikes air max', 'abercrombie & fitch hoodie', 'h&m jeans', 'carhartt wip detroit jacket', 'levis 501', 'the north face nuptse',
  'stone island', 'lego star wars', 'adidas samba 42', 'zara', '', '   ', 'pokemon cards', 'jordan 1 travis scott', 'tommy hilfiger polo']) {
  eq(k(s), '', 'untouched: "' + s + '"');
}
eq(k('supreme north face'), 'brands', 'a collab is flagged but only as a suggestion (the page always offers Keep as typed)');
eq(k('stone island / cp company'), 'list', 'spaced slash = list');
eq(k('nike + adidas'), 'list', 'spaced plus = list');
eq(W.check('a, a, A').kind, '', 'duplicates -> one part -> nothing');
eq(W.check('x'.repeat(200) + ', nike').options[0].length, 40, 'options capped at 40 characters');
eq(W.check('a,b,c,d,e,f,g,h').options.length, 6, 'at most 6 options');
eq(W._lev('kitten', 'sitting', 5), 3, 'edit distance');
const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'hunt-words.js'), 'latin1');
eq(/[^\x09\x0a\x0d\x20-\x7e]/.test(src), false, 'pure ASCII');
console.log('all ' + passed + ' hunt-words core checks pass');
