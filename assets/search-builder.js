(function () {
  'use strict';
  var form = document.querySelector('[data-search-builder]'), api = window.SNYPDSearch;
  if (!form || !api) return;
  var fr = document.documentElement.lang === 'fr';
  var error = form.querySelector('[data-builder-error]'), result = form.querySelector('[data-builder-result]');
  var copy = form.querySelector('[data-builder-copy]'), message = form.querySelector('[data-builder-message]');
  var output = form.querySelector('[data-builder-url]'), open = form.querySelector('[data-builder-open]');
  var monitor = form.querySelector('[data-builder-monitor]');
  api.markets.slice().sort(function (a, b) { return a[fr ? 2 : 1].localeCompare(b[fr ? 2 : 1]); }).forEach(function (m) {
    var option = document.createElement('option'); option.value = m[0]; option.textContent = m[fr ? 2 : 1] + ' — ' + m[3];
    form.elements.site.appendChild(option);
  });
  form.elements.site.value = fr ? 'vinted.fr' : 'vinted.be';
  var params = new URLSearchParams(window.SNYPD_BUILDER_PREFILL || location.search);
  // Prefills are editable; unsupported countries or currency mismatches do not silently change a budget.
  var preSite = params.get('site'), preCurrency = params.get('currency');
  if (api.market(preSite)) form.elements.site.value = preSite;
  else if (preCurrency === 'GBP') form.elements.site.value = 'vinted.co.uk';
  if (params.get('q')) form.elements.words.value = params.get('q').slice(0, 80);
  if (params.has('max') && preCurrency === api.market(form.elements.site.value)[3]) {
    try { form.elements.max.value = api.normalize({ site: form.elements.site.value, q: 'prefill', max: params.get('max') }).max; } catch (e) {}
  }
  function currency() {
    var code = api.market(form.elements.site.value)[3];
    form.querySelectorAll('[data-builder-currency]').forEach(function (el) { el.textContent = code; });
  }
  function invalidate() { result.hidden = true; error.textContent = ''; message.textContent = ''; }
  function event(name) {
    if (typeof window.gtag === 'function') window.gtag('event', name, { page_lang: fr ? 'fr' : 'en' });
  }
  form.elements.site.addEventListener('change', function () {
    form.elements.min.value = ''; form.elements.max.value = ''; currency(); invalidate();
    message.textContent = fr ? 'Les prix ont été effacés : saisis ton budget dans la devise de ce marché.' : 'Prices were cleared. Enter your budget in this marketplace’s currency.';
  });
  form.addEventListener('input', invalidate);
  form.addEventListener('submit', function (ev) {
    ev.preventDefault(); invalidate();
    var value;
    try {
      value = api.normalize({ site: form.elements.site.value, q: form.elements.words.value, min: form.elements.min.value, max: form.elements.max.value });
    } catch (e) {
      var messages = fr ? {
        words: 'Saisis entre 1 et 80 caractères pour ta recherche.', site: 'Choisis un marché proposé.',
        amount: 'Saisis des prix valides, avec deux décimales maximum. Le maximum doit être positif. Pas de séparateur de milliers.',
        range: 'Le prix minimum doit être inférieur au maximum.'
      } : { words: 'Enter 1–80 characters for your search.', site: 'Choose a listed marketplace.',
        amount: 'Enter valid prices with at most two decimals. The maximum must be positive. No thousands separators.',
        range: 'The minimum price must be below the maximum.' };
      error.textContent = messages[e.message] || messages.amount;
      (e.message === 'words' ? form.elements.words : e.message === 'site' ? form.elements.site : form.elements.max).focus();
      return;
    }
    output.value = api.build(value); open.href = output.value; monitor.href = api.signup(value, fr ? 'fr' : 'en');
    result.hidden = false; event('search_builder_generate');
  });
  copy.addEventListener('click', async function () {
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('clipboard');
      await navigator.clipboard.writeText(output.value);
      message.textContent = fr ? 'Lien copié.' : 'Link copied.'; event('search_builder_copy');
    } catch (e) {
      output.focus(); output.select();
      message.textContent = fr ? 'Copie le lien sélectionné avec le menu de ton appareil.' : 'Copy the selected link using your device’s copy menu.';
    }
  });
  monitor.addEventListener('click', function () { event('search_builder_monitor'); });
  form.hidden = false; currency();
})();
