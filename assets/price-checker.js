/* SNYPD Vinted price checker. Searches /assets/data/price-index.json, which holds only the items the
   price guide already publishes (written by ops/seo/gen_price_guide.py). No cookies, no backend calls.
   Words come from the page (<script type="application/json" class="pc-i18n">); this file stays ASCII.
   One GA4 event per item shown ('price_check', item id only, never the typed text); GA4 itself only
   loads after cookie consent (assets/consent.js), so without consent nothing leaves the browser. */
(function () {
  'use strict';
  var box = document.querySelector('[data-pc]');
  if (!box || !window.fetch || !window.URLSearchParams || !String.prototype.normalize) return;
  var lang = box.getAttribute('data-lang') || 'en';
  var T;
  try { T = JSON.parse(box.querySelector('.pc-i18n').textContent); } catch (e) { return; }
  var input = box.querySelector('input');
  var list = box.querySelector('.pc-list');
  var res = box.querySelector('.pc-res');
  var msg = box.querySelector('.pc-msg');
  var items = [];
  var sent = {};
  var SEP = lang === 'en' ? ',' : (lang === 'nl' ? '.' : ' ');

  function fold(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function group(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, SEP); }
  function num(n) { return group(String(n)); }
  function money(c) {
    var v = c % 100 === 0 ? String(Math.floor(c / 100)) : (c / 100).toFixed(2);
    var p = v.split('.');
    var whole = group(p[0]);
    if (lang === 'en') return '€' + whole + (p[1] ? '.' + p[1] : '');
    if (lang === 'nl') return '€ ' + whole + (p[1] ? ',' + p[1] : '');
    return whole + (p[1] ? ',' + p[1] : '') + ' €';
  }
  function t(key, vars) {
    var s = T[key] || '';
    for (var k in vars) { if (vars.hasOwnProperty(k)) s = s.split('{' + k + '}').join(vars[k]); }
    return s;
  }
  function add(parent, tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    parent.appendChild(e);
    return e;
  }
  function name(it) { return it.name[lang] || it.name.en; }
  function url(it) { return it.url[lang] || it.url.en; }

  function match(q) {
    var words = fold(q).split(' ').filter(Boolean);
    if (!words.length) return [];
    var first = words[0];
    return items.filter(function (it) {
      return words.every(function (w) { return it.hay.indexOf(w) !== -1; });
    }).sort(function (a, b) {
      var sa = fold(name(a)).indexOf(first) === 0 ? 0 : 1;
      var sb = fold(name(b)).indexOf(first) === 0 ? 0 : 1;
      return sa - sb || b.n - a.n;
    });
  }

  function track(it) {
    if (sent[it.id]) return;
    sent[it.id] = 1;
    if (typeof window.gtag === 'function') window.gtag('event', 'price_check', { item_id: it.id, page_lang: lang });
  }

  function show(it) {
    res.textContent = '';
    add(res, 'h3', null, name(it).toUpperCase());
    add(res, 'span', 'pc-msg', t('typical'));
    add(res, 'span', 'pc-big', money(it.typical));
    var ul = add(res, 'ul');
    var li = add(ul, 'li');
    add(li, 'strong', null, t('middle') + ' ');
    li.appendChild(document.createTextNode(money(it.p25) + ' – ' + money(it.p75)));
    li = add(ul, 'li');
    add(li, 'strong', null, t('listings') + ' ');
    li.appendChild(document.createTextNode(num(it.n)));
    add(ul, 'li', null, t('where'));
    add(res, 'p', 'ct-note', t('note'));
    var acts = add(res, 'div', 'ct-actions');
    var a = add(acts, 'a', 'ct-btn', t('alert', { p: money(it.p25) }));
    a.href = '/signup?' + new URLSearchParams({ hunt: it.q, max: String(Math.floor(it.p25 / 100)) }).toString();
    a = add(acts, 'a', 'ct-btn ct-ghost', t('page'));
    a.href = url(it);
    res.hidden = false;
    track(it);
  }

  function render() {
    var q = input.value;
    var found = match(q);
    list.textContent = '';
    msg.textContent = '';
    if (!fold(q)) { res.hidden = true; return; }
    if (!found.length) {
      res.hidden = true;
      msg.textContent = t('none', { q: q.slice(0, 40), n: String(items.length) });
      return;
    }
    if (found.length === 1) { show(found[0]); return; }
    res.hidden = true;
    msg.textContent = t('many', { n: String(found.length) });
    found.slice(0, 12).forEach(function (it) {
      var b = add(add(list, 'li'), 'button', null, name(it) + ' · ' + money(it.typical));
      b.type = 'button';
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', function () {
        Array.prototype.forEach.call(list.querySelectorAll('button'), function (x) { x.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        show(it);
      });
    });
  }

  fetch(box.getAttribute('data-index'), { credentials: 'omit' }).then(function (r) {
    if (!r.ok) throw new Error('index ' + r.status);
    return r.json();
  }).then(function (d) {
    items = d.items || [];
    items.forEach(function (it) {
      it.hay = ' ' + fold([it.name.en, it.name.fr, it.name.nl, it.name.de, it.brand, it.q, it.cat].join(' ')) + ' ';
    });
    box.hidden = false;
    input.addEventListener('input', render);
    var q = new URLSearchParams(window.location.search).get('q');
    if (q) { input.value = q.slice(0, 60); render(); }
  }).catch(function () { /* box stays hidden; the page's own list answers without it */ });
})();
