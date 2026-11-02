'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require(require.resolve('jsdom', { paths: [path.join(__dirname, 'auth')] }));
const root = process.env.SNYPD_PROFIT_ROOT || path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'assets/profit-calculator.js'), 'utf8');

function boot(t, lang = 'en') {
  const file = lang === 'fr' ? 'fr/calculateur-marge-vinted.html' : 'vinted-profit-calculator.html';
  const dom = new JSDOM(fs.readFileSync(path.join(root, file), 'utf8'), {
    url: 'https://www.snypd.store/' + file.replace(/\.html$/, ''), runScripts: 'outside-only'
  });
  t.after(() => dom.window.close());
  const w = dom.window, requests = [], events = [];
  w.fetch = (...args) => { requests.push(args); throw new Error('Calculator must not request data'); };
  w.gtag = (...args) => events.push(args);
  w.eval(script);
  const form = w.document.querySelector('[data-profit]');
  return {
    w, form, requests, events,
    result: form.querySelector('[data-profit-result]'),
    error: form.querySelector('[data-profit-error]'),
    value: key => form.querySelector('[data-value="' + key + '"]').textContent,
    submit(values = {}) {
      for (const [key, value] of Object.entries(values)) form.elements[key].value = value;
      const ev = new w.Event('submit', { bubbles: true, cancelable: true });
      form.dispatchEvent(ev);
      assert.equal(ev.defaultPrevented, true);
    }
  };
}
test('the worked example has correct profit, margin, ROI, break-even and target budget', t => {
  const h = boot(t);
  assert.equal(h.result.hidden, false);
  assert.equal(h.value('profit'), '€13.00');
  assert.equal(h.value('cost'), '€27.00');
  assert.equal(h.value('margin'), '32.5%');
  assert.equal(h.value('roi'), '48.1%');
  assert.equal(h.value('break-even'), '€27.00');
  assert.equal(h.value('budget'), '€23.00');
  h.submit({ sale: '30' });
  assert.equal(h.value('profit'), '€3.00');
  assert.equal(h.value('budget'), '€13.00');
});
test('cents are exact, French decimal commas work, and amounts remain local', t => {
  const h = boot(t, 'fr');
  h.submit({ sale: '0,30', buy: '0,10', inbound: '0,20', outbound: '0', other: '0', target: '0' });
  assert.match(h.value('profit'), /^0,00\s€$/);
  assert.equal(h.value('margin'), '0%');
  assert.deepEqual(h.requests, []);
  assert.deepEqual(h.events, []);
  assert.equal(h.w.localStorage.length, 0);
});
test('losses and zero denominators are explicit rather than infinite or hidden', t => {
  const h = boot(t);
  h.submit({ sale: '0', buy: '0', inbound: '0', outbound: '0', other: '0', target: '1' });
  assert.equal(h.value('margin'), 'Not defined');
  assert.equal(h.value('roi'), 'Not defined');
  assert.match(h.value('budget'), /No non-negative/);
  h.submit({ buy: '10' });
  assert.match(h.value('profit'), /-.*10\.00/);
  assert.equal(h.value('roi'), '-100%');
});
test('malformed, negative, missing and excessive amounts never leave stale results', t => {
  const h = boot(t);
  for (const bad of ['', '-1', '1e3', '1,000.00', '1.234', 'Infinity', '1000000.01', '<img>']) {
    h.submit({ buy: bad });
    assert.equal(h.result.hidden, true, bad);
    assert.ok(h.error.textContent.length > 0, bad);
    assert.equal(h.form.elements.buy.getAttribute('aria-invalid'), 'true');
    assert.equal(h.w.document.activeElement, h.form.elements.buy);
  }
  h.submit({ buy: '1000000.00' });
  assert.equal(h.result.hidden, false);
  assert.equal(h.error.textContent, '');
  assert.equal(h.form.elements.buy.getAttribute('aria-invalid'), 'false');
});
test('changing currency changes labels and formatting without currency conversion', t => {
  const h = boot(t);
  h.form.elements.currency.value = 'GBP';
  h.form.elements.currency.dispatchEvent(new h.w.Event('change'));
  assert.equal(h.value('profit'), '£13.00');
  assert.equal(h.form.elements.sale.value, '40');
  assert.ok([...h.form.querySelectorAll('[data-currency-label]')].every(e => e.textContent === 'GBP'));
});
test('reset restores the example, clears errors and refreshes currency labels', async t => {
  const h = boot(t);
  h.submit({ buy: '-1', currency: 'GBP' });
  h.form.reset();
  await new Promise(resolve => h.w.setTimeout(resolve, 10));
  assert.equal(h.value('profit'), '€13.00');
  assert.equal(h.error.textContent, '');
  assert.equal(h.result.hidden, false);
  assert.equal(h.form.elements.currency.value, 'EUR');
  assert.ok([...h.form.querySelectorAll('[data-currency-label]')].every(e => e.textContent === 'EUR'));
});
test('French error and impossible-target messages are translated', t => {
  const h = boot(t, 'fr');
  h.submit({ buy: '-1' });
  assert.match(h.error.textContent, /^Entre chaque montant/);
  h.submit({ buy: '1', sale: '0' });
  assert.match(h.value('budget'), /^Même un article gratuit/);
  assert.equal(h.value('margin'), 'Non défini');
});
