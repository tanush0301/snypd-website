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
  /* Extra Vinted filters carried from a search page (browser extension): "brand_ids:53,88;size_ids:207;catalog:1206".
     Only id lists the dashboard's link check accepts (catalog and *_ids, digits only). Returns the canonical text. */
  function filters(text) {
    var s = String(text == null ? '' : text).trim();
    if (!s) return '';
    if (s.length > 600) throw new Error('filters');
    var seen = {}, total = 0;
    return s.split(';').map(function (part) {
      var m = /^(catalog|[a-z][a-z0-9_]{0,30}_ids):([0-9]{1,12}(,[0-9]{1,12})*)$/.exec(part);
      if (!m || seen[m[1]]) throw new Error('filters');
      seen[m[1]] = true;
      total += m[2].split(',').length;
      if (total > 40) throw new Error('filters');
      return m[1] + ':' + m[2];
    }).join(';');
  }
  /* The same list as [name, id] pairs in Vinted's own parameter form, for building a link. */
  function filterPairs(text) {
    var out = [];
    filters(text).split(';').forEach(function (part) {
      if (!part) return;
      var i = part.indexOf(':');
      part.slice(i + 1).split(',').forEach(function (id) { out.push([part.slice(0, i) + '[]', id]); });
    });
    return out;
  }
  function normalize(value) {
    if (!value || !market(value.site)) throw new Error('site');
    var q = String(value.q || '').trim().replace(/\s+/g, ' ');
    if (!q || q.length > 80 || /[\x00-\x1f\x7f]/.test(q)) throw new Error('words');
    var min = amount(value.min, true), max = amount(value.max, false);
    if (min !== '' && max !== '' && Number(min) >= Number(max)) throw new Error('range');
    var out = { q: q, site: value.site, min: min, max: max }, f = filters(value.f);
    if (f) out.f = f;
    return out;
  }
  function build(value) {
    var v = normalize(value), u = new URL('https://www.' + v.site + '/catalog');
    u.searchParams.set('search_text', v.q);
    if (v.min !== '') u.searchParams.set('price_from', v.min);
    if (v.max !== '') u.searchParams.set('price_to', v.max);
    filterPairs(v.f).forEach(function (pair) { u.searchParams.append(pair[0], pair[1]); });
    u.searchParams.set('order', 'newest_first');
    return u.toString();
  }
  function fromParams(qs) {
    return normalize({ q: qs.get('hunt'), site: qs.get('site'), min: qs.get('min'), max: qs.get('max'), f: qs.get('f') });
  }
  function signup(value, lang) {
    var v = normalize(value), qs = new URLSearchParams({ hunt: v.q, site: v.site, min: v.min, lang: lang === 'fr' ? 'fr' : 'en' });
    if (v.max !== '') qs.set('max', v.max);
    if (v.f) qs.set('f', v.f);
    return '/signup?' + qs.toString();
  }
  root.SNYPDSearch = { markets: markets, market: market, normalize: normalize, filters: filters, filterPairs: filterPairs, build: build, fromParams: fromParams, signup: signup };
})(typeof window !== 'undefined' ? window : globalThis);
