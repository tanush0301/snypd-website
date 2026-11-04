/* Simulates sw.js's push handler: the notification must always be shown, in French
 * when the stored UI language is fr, in English otherwise, and in English when the
 * language lookup itself fails.   node ops/i18n/test_sw_push.js */
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', '..', 'sw.js'), 'utf8');

async function fire(payload, { stored, navLang, cachesBroken }) {
  const listeners = {};
  const shown = [];
  const self = {
    addEventListener: (t, f) => { listeners[t] = f; },
    skipWaiting() {}, clients: { claim() {}, matchAll: async () => [], openWindow: async () => {} },
    registration: { showNotification: async (title, opts) => { shown.push({ title, body: opts.body }); } },
    navigator: { language: navLang },
    location: { origin: 'https://www.snypd.store' },
  };
  const caches = cachesBroken ? { open: async () => { throw new Error('no caches'); } } : {
    open: async () => ({ match: async () => (stored ? { text: async () => stored } : undefined) }),
  };
  new Function('self', 'caches', src)(self, caches);
  let p;
  listeners.push({ data: { json: () => payload, text: () => JSON.stringify(payload) }, waitUntil: (x) => { p = x; } });
  await p;
  return shown;
}

(async () => {
  const two = { title: '2 new finds', body: '45.0 EUR — Nike Air (Nike · M) & 1 more' };
  const one = { title: 'New find', body: 'New listing' };
  const cases = [
    [two, { stored: 'fr' }, '2 nouvelles trouvailles', '45.0 EUR — Nike Air (Nike · M) et 1 de plus'],
    [one, { stored: 'fr' }, 'Nouvelle trouvaille', 'Nouvelle annonce'],
    [two, { stored: 'en', navLang: 'fr-FR' }, '2 new finds', two.body],
    [two, { navLang: 'fr-BE' }, '2 nouvelles trouvailles', '45.0 EUR — Nike Air (Nike · M) et 1 de plus'],
    [two, { navLang: 'en-GB' }, '2 new finds', two.body],
    [two, { cachesBroken: true, navLang: 'en-US' }, '2 new finds', two.body],
    [{}, { stored: 'fr' }, 'SNYPD', 'Une nouvelle annonce correspond à ta recherche.'],
    // Calm summary (push.py _build_calm_payload); the hunt name is the user's own text.
    [{ title: '12 new matches - jordan 1', body: 'From 45.0 EUR. Tap to see them.' }, { stored: 'fr' },
      '12 nouvelles annonces - jordan 1', 'Dès 45.0 EUR. Touche pour les voir.'],
    [{ title: '1 new match - New listing hunt', body: 'Tap to see them.' }, { stored: 'fr' },
      '1 nouvelle annonce - New listing hunt', 'Touche pour les voir.'],
    [{ title: '12 new matches - jordan 1', body: 'From 45.0 EUR. Tap to see them.' }, { stored: 'en' },
      '12 new matches - jordan 1', 'From 45.0 EUR. Tap to see them.'],
    // Price check (push.py "rank", Session 66): worded in the user's language, only for 50-100 integers.
    [Object.assign({ rank: 82 }, two), { stored: 'en' }, '2 new finds', "Cheaper than 82% of this week's finds \u00b7 " + two.body],
    [Object.assign({ rank: 82 }, two), { stored: 'fr' }, '2 nouvelles trouvailles',
      'Moins cher que 82\u00a0% des trouvailles de la semaine \u00b7 45.0 EUR \u2014 Nike Air (Nike \u00b7 M) et 1 de plus'],
    [Object.assign({ rank: 40 }, two), { stored: 'en' }, '2 new finds', two.body],
    [Object.assign({ rank: '82' }, two), { stored: 'en' }, '2 new finds', two.body],
    [Object.assign({ rank: 101 }, two), { stored: 'en' }, '2 new finds', two.body],
    [Object.assign({ rank: 90 }, one), { cachesBroken: true, navLang: 'en-US' }, 'New find', "Cheaper than 90% of this week's finds \u00b7 New listing"],
  ];
  let bad = 0;
  for (const [payload, env, wantT, wantB] of cases) {
    const shown = await fire(payload, env);
    const ok = shown.length === 1 && shown[0].title === wantT && shown[0].body === wantB;
    if (!ok) { bad++; console.log('FAIL', JSON.stringify(env), JSON.stringify(shown)); }
  }
  console.log(bad ? bad + ' failure(s)' : 'all ' + cases.length + ' push cases pass (always exactly one notification)');
  process.exit(bad ? 1 : 0);
})();
