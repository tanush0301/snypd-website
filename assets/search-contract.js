/* Public search construction and explicit user-requested onboarding intent.
   Supported sites mirror dashboard.html's catalogue contract; regression-tested.
   Does not send requests, create hunts, request permissions or store anything. */
(function (root) {
  'use strict';
  var markets = [
    ['vinted.be', 'Belgium', 'Belgique', 'EUR'], ['vinted.co.uk', 'United Kingdom', 'Royaume-Uni', 'GBP'],
    ['vinted.com', 'United States', 'États-Unis', 'USD'], ['vinted.fr', 'France', 'France', 'EUR'],
    ['vinted.nl', 'Netherlands', 'Pays-Bas', 'EUR'], ['vinted.lu', 'Luxembourg', 'Luxembourg', 'EUR'],
    ['vinted.de', 'Germany', 'Allemagne', 'EUR'], ['vinted.at', 'Austria', 'Autriche', 'EUR'],
    ['vinted.it', 'Italy', 'Italie', 'EUR'], ['vinted.es', 'Spain', 'Espagne', 'EUR'],
    ['vinted.pt', 'Portugal', 'Portugal', 'EUR'], ['vinted.ie', 'Ireland', 'Irlande', 'EUR'],
    ['vinted.fi', 'Finland', 'Finlande', 'EUR'], ['vinted.sk', 'Slovakia', 'Slovaquie', 'EUR'],
    ['vinted.lt', 'Lithuania', 'Lituanie', 'EUR'], ['vinted.lv', 'Latvia', 'Lettonie', 'EUR'],
    ['vinted.ee', 'Estonia', 'Estonie', 'EUR'], ['vinted.hr', 'Croatia', 'Croatie', 'EUR'],
    ['vinted.si', 'Slovenia', 'Slovénie', 'EUR'], ['vinted.gr', 'Greece', 'Grèce', 'EUR'],
    ['vinted.pl', 'Poland', 'Pologne', 'PLN'], ['vinted.cz', 'Czechia', 'Tchéquie', 'CZK'],
    ['vinted.se', 'Sweden', 'Suède', 'SEK'], ['vinted.dk', 'Denmark', 'Danemark', 'DKK'],
    ['vinted.hu', 'Hungary', 'Hongrie', 'HUF'], ['vinted.ro', 'Romania', 'Roumanie', 'RON']
  ];
  function market(site) { return markets.find(function (m) { return m[0] === site; }); }
  function amount(value, allowZero) {
    var s = String(value == null ? '' : value).trim();
    if (!s) return '';
    if (!/^\d{1,7}([.,]\d{1,2})?$/.test(s)) throw new Error('amount');
    var n = Number(s.replace(',', '.'));
    if (n > 1000000 || (!allowZero && n <= 0)) throw new Error('amount');
    return String(n);
  }
  function normalize(value) {
    if (!value || !market(value.site)) throw new Error('site');
    var q = String(value.q || '').trim().replace(/\s+/g, ' ');
    if (!q || q.length > 80 || /[\x00-\x1f\x7f]/.test(q)) throw new Error('words');
    var min = amount(value.min, true), max = amount(value.max, false);
    if (min !== '' && max !== '' && Number(min) >= Number(max)) throw new Error('range');
    return { q: q, site: value.site, min: min, max: max };
  }
  function build(value) {
    var v = normalize(value), u = new URL('https://www.' + v.site + '/catalog');
    u.searchParams.set('search_text', v.q);
    if (v.min !== '') u.searchParams.set('price_from', v.min);
    if (v.max !== '') u.searchParams.set('price_to', v.max);
    u.searchParams.set('order', 'newest_first');
    return u.toString();
  }
  function fromParams(qs) {
    return normalize({ q: qs.get('hunt'), site: qs.get('site'), min: qs.get('min'), max: qs.get('max') });
  }
  function signup(value, lang) {
    var v = normalize(value), qs = new URLSearchParams({ hunt: v.q, site: v.site, min: v.min, lang: lang === 'fr' ? 'fr' : 'en' });
    if (v.max !== '') qs.set('max', v.max);
    return '/signup?' + qs.toString();
  }
  root.SNYPDSearch = { markets: markets, market: market, normalize: normalize, build: build, fromParams: fromParams, signup: signup };
})(typeof window !== 'undefined' ? window : globalThis);
