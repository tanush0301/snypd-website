'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/auth.js'), 'utf8');
const start = source.indexOf('  var signupEventsSent = {};');
const end = source.indexOf('  var qs = ', start);
assert.ok(start >= 0 && end > start);
function harness() {
  const events = [];
  const c = { Date, track: (name, payload) => events.push({ name, payload }) };
  vm.createContext(c);
  vm.runInContext(source.slice(start, end), c);
  return { events, send: c.trackSignUp };
}
const created = '2026-11-02T10:00:00.000Z';
test('empty or unidentified responses never become registrations', () => {
  const h = harness();
  for (const user of [null, {}, { email: 'private@example.test' }, { id: '' }]) h.send(user, 'email');
  assert.equal(h.events.length, 0);
});
test('a real email account is counted once per page without identifying payloads', () => {
  const h = harness(), user = { id: 'account-a', email: 'private@example.test' };
  h.send(user, 'email'); h.send(user, 'email');
  assert.equal(h.events.length, 1);
  assert.equal(JSON.stringify(h.events), '[{"name":"sign_up","payload":{"method":"email"}}]');
});
test('Google first sign-in is distinguishable from a later login within 15 minutes', () => {
  const h = harness();
  h.send({ id: 'first', created_at: created, last_sign_in_at: '2026-11-02T10:00:01.000Z' }, 'google');
  h.send({ id: 'returning', created_at: created, last_sign_in_at: '2026-11-02T10:05:00.000Z' }, 'google');
  assert.equal(h.events.length, 1);
});
test('ambiguous Google timestamps are not counted as proven registrations', () => {
  const h = harness();
  h.send({ id: 'missing', created_at: created }, 'google');
  h.send({ id: 'invalid', created_at: 'invalid', last_sign_in_at: created }, 'google');
  assert.equal(h.events.length, 0);
});
