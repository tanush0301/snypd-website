/* Local arithmetic only. No requests, storage or analytics of entered amounts. */
(function () {
  'use strict';
  var form = document.querySelector('[data-profit]');
  if (!form) return;
  var fr = document.documentElement.lang === 'fr';
  var error = form.querySelector('[data-profit-error]');
  var result = form.querySelector('[data-profit-result]');
  var names = ['sale', 'buy', 'inbound', 'outbound', 'other', 'target'];

  function cents(raw) {
    var s = String(raw).trim();
    if (!/^\d{1,7}([.,]\d{1,2})?$/.test(s)) return null;
    var p = s.replace(',', '.').split('.');
    var n = Number(p[0]) * 100 + Number(((p[1] || '') + '00').slice(0, 2));
    return n <= 100000000 ? n : null;
  }
  function money(n) {
    return new Intl.NumberFormat(fr ? 'fr-FR' : 'en-GB', {
      style: 'currency', currency: form.elements.currency.value
    }).format(n / 100);
  }
  function percent(n) {
    return new Intl.NumberFormat(fr ? 'fr-FR' : 'en-GB', { maximumFractionDigits: 1 }).format(n) + '%';
  }
  function put(key, text) { result.querySelector('[data-value="' + key + '"]').textContent = text; }
  function calculate(ev) {
    if (ev) ev.preventDefault();
    error.textContent = '';
    var v = {}, bad = null;
    names.forEach(function (key) {
      var input = form.elements[key], n = cents(input.value);
      input.setAttribute('aria-invalid', n === null ? 'true' : 'false');
      if (n === null && !bad) bad = input;
      v[key] = n;
    });
    if (bad) {
      result.hidden = true;
      error.textContent = fr ? 'Entre chaque montant entre 0 et 1 000 000, avec deux décimales au maximum et sans séparateur de milliers.' : 'Enter every amount from 0 to 1,000,000, with at most two decimal places and no thousands separators.';
      if (ev) bad.focus();
      return;
    }
    var total = v.buy + v.inbound + v.outbound + v.other;
    var profit = v.sale - total;
    var budget = v.sale - v.inbound - v.outbound - v.other - v.target;
    var na = fr ? 'Non défini' : 'Not defined';
    put('profit', money(profit));
    put('cost', money(total));
    put('margin', v.sale > 0 ? percent(profit / v.sale * 100) : na);
    put('roi', total > 0 ? percent(profit / total * 100) : na);
    put('break-even', money(total));
    put('budget', budget >= 0 ? money(budget) : (fr ? 'Même un article gratuit ne permet pas cet objectif.' : 'No non-negative buying price meets this target.'));
    result.hidden = false;
  }
  form.addEventListener('submit', calculate);
  form.elements.currency.addEventListener('change', function () {
    form.querySelectorAll('[data-currency-label]').forEach(function (e) { e.textContent = form.elements.currency.value; });
    calculate();
  });
  form.addEventListener('reset', function () {
    result.hidden = true;
    error.textContent = '';
    form.querySelectorAll('[aria-invalid]').forEach(function (e) { e.removeAttribute('aria-invalid'); });
    setTimeout(function () {
      form.querySelectorAll('[data-currency-label]').forEach(function (e) { e.textContent = form.elements.currency.value; });
      calculate();
    }, 0);
  });
  calculate();
})();
