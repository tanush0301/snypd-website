/* Regression test for assets/i18n.js: runs real English on-screen texts through the
 * generated engine (in a minimal fake DOM) and compares with the expected French.
 *   node ops/i18n/test_i18n.js
 * Exit code 1 on any mismatch. Add a case whenever a pattern or tricky string changes.
 */
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', '..', 'assets', 'i18n.js'), 'utf8');

const store = { snypd_ui_lang: 'fr' };
const html = { attrs: { 'data-i18n-app': '' }, hasAttribute: (k) => k in html.attrs, getAttribute: (k) => html.attrs[k] || null,
  setAttribute: (k, v) => { html.attrs[k] = v; } };
const g = {
  document: { documentElement: html, readyState: 'complete', querySelectorAll: () => [], addEventListener() {}, head: { appendChild() {} }, createElement: () => ({}) },
  location: { search: '', href: 'http://x/dashboard' },
  localStorage: { getItem: (k) => store[k] || null, setItem: (k, v) => { store[k] = v; } },
  navigator: { languages: ['fr-FR'], language: 'fr-FR' },
  MutationObserver: function () { this.observe = () => {}; },
  URLSearchParams, URL, Promise,
  confirm: () => true, alert: () => {},
};
g.window = g;
new Function(...Object.keys(g), src)(...Object.values(g));
const t = g.window.SNYPD_I18N.t;

const NB = ' ';
const cases = [
  ['Feed', 'Flux'],
  ['Forgot password?', 'Mot de passe oublié' + NB + '?'],
  ['Nike • M • Très bon état • Promoted • Seen 5m ago', 'Nike • M • Très bon état • Sponsorisé • vu il y a 5 min'],
  ['Levis • 32 • 2h ago', 'Levis • 32 • il y a 2 h'],
  ['€62.50', '62,50' + NB + '€'],
  ['€1,250.00 incl. protection', '1 250,00' + NB + '€ protection incluse'],
  ['(€30 – €60)', '(30' + NB + '€ – 60' + NB + '€)'],
  ['Last sync 17:05 · 1 min ago', 'Dernière synchro 17:05 · il y a 1 min'],
  ['Quiet right now — last match under a minute ago.', 'Calme pour l’instant — dernière annonce il y a moins d’une minute.'],
  ['Quiet right now — last match 3 hours ago.', 'Calme pour l’instant — dernière annonce il y a 3 heures.'],
  ['12 new matches', '12 nouvelles annonces'],
  ['1 new match', '1 nouvelle annonce'],
  ['Free 24/7 trial: 1 day left', 'Essai Free 24h/24' + NB + ': encore 1 jour'],
  ['Free 24/7 trial: 6 days left', 'Essai Free 24h/24' + NB + ': encore 6 jours'],
  ['Could not turn alerts on: unknown error.', 'Impossible d’activer les alertes' + NB + ': erreur inconnue.'],
  ['FOUNDING · 22 of the first 100 spots left', 'FONDATEUR · encore 22 places sur les 100 premières'],
  ['As of 9 Oct 2026', 'Au 9 oct. 2026'],
  ['Status: running', 'Statut' + NB + ': en cours'],
  ['1 OF 10 · ELITE', '1 SUR 10 · ELITE'],
  ['Day 9 of the hunt', 'Jour 9 de traque'],
  ['230 XP to Bronze Hunter', 'encore 230 XP pour Bronze Hunter'],
  ['Create one free', 'Crées-en un gratuitement'],
  ['Claim', 'J’ai acheté'],
  ['3 items held 45 days or more — still yours?', '3 articles en stock depuis 45 jours ou plus — tu les as encore' + NB + '?'],
  ['Held 10d', 'En stock depuis 10 j'],
  ['For the 2 selected', 'Pour les 2 sélectionnés'],
  ['17 of 20 price checks left this hour', 'encore 17 vérifications de prix sur 20 cette heure-ci'],
  ['Most sit between 38 € and 52 €', 'La plupart entre 38 € et 52 €'],
  ['under 38 € · priced to move fast', 'moins de 38 € · se vend vite'],
  ['· 120 listings', '· 120 annonces'],
  ['12% of listings have already dropped their price since we started watching.', '12' + NB + '% des annonces ont déjà baissé leur prix depuis qu’on les surveille.'],
  ['New, with tag', 'Neuf avec étiquette'],
  ['Found 120 listings, but', 'On a trouvé 120 annonces, mais'],
  ['SNYPD cannot read the "foo_bar" filter in this link yet, so it would never run. Remove that filter on Vinted and copy the link again.',
   'SNYPD ne sait pas lire le filtre «' + NB + 'foo_bar' + NB + '» de ce lien, la recherche ne tournerait donc jamais. Retire ce filtre sur Vinted et copie à nouveau le lien.'],
  ['5,399', '5 399'],
  ['Recent', 'Récentes'],
  // untranslated text must come back unchanged
  ['Hello world untranslated', 'Hello world untranslated'],
  ['GOLD HUNTER · 1,283 XP', 'GOLD HUNTER · 1,283 XP'],
  // surrounding whitespace is kept
  [' tab, where you can later mark it sold, mark it still listed, or remove it if you claimed it by mistake.', ' — tu pourras ensuite le marquer vendu, toujours en vente, ou le retirer si tu l’as marqué par erreur.'],
];

let bad = 0;
for (const [en, want] of cases) {
  const got = t(en);
  if (got !== want) { bad++; console.log('FAIL', JSON.stringify(en), '\n  got ', JSON.stringify(got), '\n  want', JSON.stringify(want)); }
}
// Banned words must never appear in any French value (fact-sheet rules).
const dict = JSON.parse(src.match(/var DICT = (.*);/)[1]).fr;
const pats = JSON.parse(src.match(/var PATTERNS = (.*);/)[1]).fr;
const all = Object.values(dict).concat(pats.map((p) => p[1])).join('\n').toLowerCase();
for (const w of [/instantan/, /temps réel/, /le plus rapide/, /sûr/, /autorisé par vinted/, /prix de vente/, /vendu (pour|à) (\$|\d|€)/, /se vend à/]) {
  if (w.test(all)) { bad++; console.log('BANNED WORD in French text:', w); }
}
console.log(bad ? bad + ' problem(s)' : 'all ' + cases.length + ' cases pass, no banned words');
process.exit(bad ? 1 : 0);
