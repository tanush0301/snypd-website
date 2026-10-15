/* Run: cd ops/auth && npm ci && npm test. No live API calls or real accounts. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { JSDOM } = require('jsdom');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../assets/auth.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
const verified = (email = 'new@example.com') => ({ data: { session: { user: { email, email_confirmed_at: '2026-10-15T00:00:00Z' } } } });

async function boot(t, { url = '/login?verify=1', page = 'login', auth = {}, saved = '', french = false } = {}) {
  const dom = new JSDOM('<html data-i18n-app lang="en"><body><form id="au-form" novalidate></form></body></html>', { url: 'https://www.snypd.store' + url });
  t.after(() => dom.window.close());
  const w = dom.window, calls = [], timers = new Map(), redirects = [];
  let clock = 0;
  const location = { hostname: 'www.snypd.store', origin: 'https://www.snypd.store', pathname: '', search: '', hash: '', replace: value => redirects.push(value) };
  const setUrl = value => { const u = new URL(value, location.origin); Object.assign(location, { pathname: u.pathname, search: u.search, hash: u.hash }); };
  setUrl(url);
  const defaults = { getSession: () => ({ data: { session: null } }), onAuthStateChange: () => ({}), verifyOtp: () => verified(), resend: () => ({}), signUp: () => ({ data: { user: { identities: [{}] } } }), signInWithPassword: () => verified(), resetPasswordForEmail: () => ({}), updateUser: () => ({}) };
  const api = {};
  for (const key of Object.keys(defaults)) api[key] = (...args) => { calls.push([key, ...args]); return Promise.resolve((auth[key] || defaults[key])(...args)); };
  w.SNYPD = { supabase: { auth: api } };
  w.SNYPD_AUTH_URL = { search: location.search, hash: location.hash };
  w.sessionStorage.setItem('snypd_verify_email', saved);
  Object.defineProperty(w.document, 'currentScript', { value: { getAttribute: () => page } });
  const context = { window: w, document: w.document, navigator: w.navigator, location, history: { replaceState: (_, __, value) => setUrl(value) }, localStorage: w.localStorage, sessionStorage: w.sessionStorage, URLSearchParams, console, fetch: async () => ({ ok: false }), setTimeout: (fn, ms) => { const id = ++clock; timers.set(id, { fn, ms }); return id; }, clearTimeout: id => timers.delete(id), setInterval: (fn, ms) => { const id = ++clock; timers.set(id, { fn, ms, repeat: true }); return id; }, clearInterval: id => timers.delete(id) };
  vm.runInNewContext(source, context);
  await flush();
  const form = w.document.querySelector('form');
  const input = (field, value) => { const el = form.querySelector('[data-f="' + field + '"]'); assert.ok(el, field + ' input exists'); el.value = value; el.dispatchEvent(new w.Event('input', { bubbles: true })); };
  const click = act => { const el = form.querySelector('[data-act="' + act + '"]'); assert.ok(el, act + ' button exists'); el.click(); };
  const submit = async () => { form.dispatchEvent(new w.Event('submit', { bubbles: true, cancelable: true })); await flush(); };
  const tick = async ms => { for (const [id, task] of [...timers]) if (task.ms === ms) { if (!task.repeat) timers.delete(id); task.fn(); } await flush(); };
  if (french) {
    w.localStorage.setItem('snypd_ui_lang', 'fr');
    Object.assign(context, { MutationObserver: w.MutationObserver, NodeFilter: w.NodeFilter });
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../assets/i18n.js'), 'utf8'), context);
    w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
    await flush();
  }
  return { w, form, calls, input, click, submit, tick, redirects, location, text: () => form.textContent };
}

test('neutral email landing never consumes a token or redirects a cached account', async t => {
  const h = await boot(t, { auth: { getSession: () => verified('other@example.com') } });
  assert.match(h.text(), /Confirm your email/);
  assert.equal(h.calls.length, 0);
  await h.tick(600); assert.deepEqual(h.redirects, []);
});
test('code verification preserves leading zeros and forwards only verified matching user', async t => {
  const h = await boot(t); h.input('email', ' new@example.com '); h.input('code', '001 234'); await h.submit();
  assert.equal(h.calls[0][0], 'verifyOtp');
  assert.equal(h.calls[0][1].token, '001234'); assert.equal(h.calls[0][1].type, 'email');
  assert.match(h.text(), /Signed in/); await h.tick(600); assert.deepEqual(h.redirects, ['/dashboard']);
  assert.equal(h.w.sessionStorage.getItem('snypd_verify_email'), '');
});
for (const outcome of ['expired', 'wrong-email', 'unconfirmed', 'missing-session', 'throw', 'network', 'rate-limit']) {
  test('verification recovery: ' + outcome, async t => {
    const answers = { expired: { error: { code: 'otp_expired' } }, 'wrong-email': verified('other@example.com'), unconfirmed: { data: { session: { user: { email: 'new@example.com' } } } }, 'missing-session': { data: {} }, network: { error: { name: 'AuthRetryableFetchError' } }, 'rate-limit': { error: { status: 429 } } };
    const h = await boot(t, { auth: { verifyOtp: () => { if (outcome === 'throw') throw new Error('backend failure'); return answers[outcome]; }, getSession: () => verified('other@example.com') } });
    h.input('email', 'new@example.com'); h.input('code', '123456'); await h.submit(); await h.tick(600);
    assert.deepEqual(h.redirects, []); assert.ok(h.form.querySelector('[data-f="code"]'));
    assert.ok(h.form.querySelector('[data-act="resend"]')); assert.equal(h.calls.filter(c => c[0] === 'getSession').length, 0);
    assert.match(h.text(), outcome === 'network' ? /connection/ : outcome === 'rate-limit' ? /Too many/ : /latest email/);
  });
}
test('validation blocks malformed code and email without network requests', async t => {
  const h = await boot(t); h.input('email', 'bad'); h.input('code', 'bad'); await h.submit();
  assert.equal(h.calls.length, 0); assert.match(h.text(), /Enter a full email/);
});
test('resend validates email, clears replaced code and prevents duplicate requests', async t => {
  let finish; const h = await boot(t, { auth: { resend: () => new Promise(r => { finish = r; }) } });
  h.click('resend'); assert.equal(h.calls.length, 0);
  h.input('email', 'new@example.com'); h.input('code', '123456'); h.click('resend'); h.click('resend');
  assert.equal(h.calls.length, 1); finish({}); await flush();
  assert.equal(h.form.querySelector('[data-f="code"]').value, ''); assert.match(h.text(), /latest email/);
  h.click('resend'); assert.equal(h.calls.length, 1);
});
test('simultaneous verification submits make one request and timeout is recoverable', async t => {
  const h = await boot(t, { auth: { verifyOtp: () => new Promise(() => {}) } });
  h.input('email', 'new@example.com'); h.input('code', '123456'); await h.submit(); await h.submit();
  assert.equal(h.calls.length, 1); await h.tick(8000); assert.match(h.text(), /Still working/);
  await h.tick(30000); assert.match(h.text(), /connection/); assert.ok(!h.form.querySelector('[type="submit"]').disabled);
});
test('signup enters confirmation with email and refresh-safe neutral URL', async t => {
  const h = await boot(t, { url: '/signup', page: 'signup' });
  h.input('email', 'new@example.com'); h.input('pw', 'test-password'); await h.submit();
  assert.match(h.text(), /CONFIRMATION CODE/); assert.equal(h.form.querySelector('[data-f="email"]').value, 'new@example.com');
  assert.equal(h.location.pathname + h.location.search, '/login?verify=1'); assert.equal(h.w.sessionStorage.getItem('snypd_verify_email'), 'new@example.com');
});
test('unconfirmed login goes directly to confirmation without automatically resending', async t => {
  const h = await boot(t, { url: '/login', auth: { signInWithPassword: () => ({ error: { code: 'email_not_confirmed' } }) } });
  h.input('email', 'new@example.com'); h.input('pw', 'test-password'); await h.submit();
  assert.match(h.text(), /CONFIRMATION CODE/); assert.equal(h.calls.filter(c => c[0] === 'resend').length, 0);
});
for (const tokenResult of ['returned-error', 'thrown-error', 'valid']) {
  test('legacy token-hash callback: ' + tokenResult, async t => {
    const h = await boot(t, { url: '/login?token_hash=test-only&type=signup', auth: { getSession: () => verified('other@example.com'), verifyOtp: () => { if (tokenResult === 'thrown-error') throw new Error('network'); return tokenResult === 'valid' ? verified() : { error: { code: 'otp_expired' } }; } } });
    assert.equal(h.calls.filter(c => c[0] === 'getSession').length, 0);
    await h.tick(600); assert.deepEqual(h.redirects, tokenResult === 'valid' ? ['/dashboard'] : []);
    if (tokenResult !== 'valid') assert.match(h.text(), /latest email/);
  });
}
test('hosted verify error gives recovery even with stale session', async t => {
  const h = await boot(t, { url: '/login#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired', auth: { getSession: () => verified('other@example.com') } });
  assert.match(h.text(), /CONFIRMATION CODE/); assert.equal(h.calls.filter(c => c[0] !== 'onAuthStateChange').length, 0);
  h.click('login'); assert.equal(h.location.search, ''); assert.match(h.text(), /LOG IN/);
});
test('ordinary login and existing session still open dashboard', async t => {
  const h = await boot(t, { url: '/login', auth: { getSession: () => verified() } });
  await h.tick(600); assert.deepEqual(h.redirects, ['/dashboard']);
});
test('OAuth cancellation remains an explicit login error', async t => {
  const h = await boot(t, { url: '/login#error=access_denied&error_description=User+cancelled' });
  assert.match(h.text(), /Google sign-in was cancelled/); assert.ok(h.form.querySelector('[data-f="pw"]'));
});
test('password recovery still uses recovery type and renders password form', async t => {
  const h = await boot(t, { page: 'reset', url: '/reset-password?token_hash=test-only' });
  assert.equal(h.calls[0][1].type, 'recovery'); assert.match(h.text(), /Set a new password/);
});
test('confirmation UI and error copy translate into French', async t => {
  const h = await boot(t, { french: true });
  assert.match(h.text(), /Confirme ton e-mail/); assert.match(h.text(), /CODE DE CONFIRMATION/);
  assert.doesNotMatch(h.text(), /Enter your account email/);
});
test('email template has a code and neutral link, no consumable credential URL', () => {
  const template = fs.readFileSync(path.join(__dirname, 'confirm-signup-email.html'), 'utf8');
  assert.match(template, /{{ \.Token }}/); assert.match(template, /login\?verify=1/);
  assert.doesNotMatch(template, /ConfirmationURL|TokenHash|token_hash|\/auth\/v1\/verify/);
});
