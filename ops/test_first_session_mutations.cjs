/*
 * Mutation check for the first-session measurement: each deliberate break must turn a test red.
 *   node ops/test_first_session_mutations.cjs          (core + browser, about 15 minutes)
 *   node ops/test_first_session_mutations.cjs core     (pure-logic mutations only, seconds)
 *   node ops/test_first_session_mutations.cjs ui "never asked"   (one mutation by name)
 * Edits assets/first-session.js / dashboard.html in place, one mutation at a time, and always restores the file.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.join(__dirname, '..');
const only = process.argv[2] || 'all';
const pick = (process.argv[3] || '').toLowerCase();   // optional: only mutations whose name contains this
const MOD = 'assets/first-session.js', DASH = 'dashboard.html';
const CORE = 'ops/test_first_session_core.cjs', UI = 'ops/test_first_session.cjs';
// [name, file, find, replace, test that must fail]
const M = [
  ['a stale tab overwrites what another device stored (no re-read before writing)', MOD, 'var next = replay(base, batch);', 'base = saved; var next = replay(base, batch);', CORE],
  ['writes at once instead of waiting for a quiet moment', MOD, 'var wait = o.wait == null ? 3000 : o.wait', 'var wait = o.wait == null ? 0 : o.wait', CORE],
  ['no cap on writes per page load', MOD, 'if (!pending.length || writes >= cap) return;', 'if (!pending.length) return;', CORE],
  ['old accounts are measured too', MOD, 'return isFinite(joined) && nowMs - joined >= 0 && nowMs - joined < WINDOW_MS;', 'return true;', CORE],
  ['a second hunt overwrites the first', MOD, 'if (patch.hunt != null && n.max === undefined) {', 'if (patch.hunt != null) {', CORE],
  ['"on" can be undone by a later state', MOD, "if (n.al !== 'on') n.al = patch.al;", 'n.al = patch.al;', CORE],
  ['the wizard step can go down', MOD, 'n.wz = Math.max(Number(n.wz) || 0, wz);', 'n.wz = wz;', CORE],
  ['"shown" replaces a card action', MOD, 'CARD_RANK[patch.card] > (CARD_RANK[n.card] || 0)', 'CARD_RANK[patch.card] > 0', CORE],
  ['the installed app is not stamped', MOD, "if (/-app$/.test(dev) && !n.app) n.app = nowIso;", '', CORE],
  ['the pre-filled minimum is not told apart from an own minimum', MOD, "min = DEFAULT_FLOORS.indexOf(Number(from[1])) >= 0 ? 'def' : 'own';", "min = 'own';", CORE],
  ['the wizard quick form does not report the first hunt', DASH, "if (window.SNYPD.fs) window.SNYPD.fs({ hunt: url, src: 'quick' });", '', UI],
  ['the Filters sheet does not report the first hunt', DASH, "window.SNYPD.fs({ hunt: inserted && inserted.vinted_url, src: 'sheet' });", 'void 0;', UI],
  ['a card hidden behind the wizard counts as shown', DASH, "if (seen($id('wiz-overlay'))) return;\n        if (seen(card))", "if (seen(card))", UI],
  ['a device that never asked is recorded as an alerts result', DASH, "if (al && (tried || al === 'on')) t.track({ al });", 'if (al) t.track({ al });', UI],
  ['"Set this up later" is not recorded', DASH, "if (later) later.addEventListener('click', () => t.track({ later: 1 }));", '', UI],
  ['a refused form is not counted', DASH, "[['wiz-q-err', 'werr'], ['wiz-q-hw', 'hw']]", "[['wiz-q-hw', 'hw']]", UI],
  ['the alerts step tap is not counted', DASH, "t.track({ al_try: 1 });", '', UI],
  ['the tracker ignores the 7-day window in the page', DASH, 'if (!FS.shouldTrack(joinedAt, prev, Date.now())) return;', '', UI],
];
let caught = 0, missed = [], ran = 0;
for (const [name, file, find, repl, test] of M) {
  if (only === 'core' && test !== CORE) continue;
  if (only === 'ui' && test !== UI) continue;
  if (pick && !name.toLowerCase().includes(pick)) continue;
  const full = path.join(root, file);
  const original = fs.readFileSync(full, 'utf8');
  const eol = original.includes('\r\n') ? '\r\n' : '\n';
  const needle = find.replace(/\n/g, eol);
  if (original.split(needle).length !== 2) { console.log('SKIP (pattern not found exactly once): ' + name); missed.push(name + ' [pattern]'); continue; }
  ran++;
  try {
    fs.writeFileSync(full, original.replace(needle, repl.replace(/\n/g, eol)));
    const r = spawnSync(process.execPath, [path.join(root, test)], { cwd: root, encoding: 'utf8', timeout: 600000 });
    if (r.status !== 0) { caught++; console.log('caught: ' + name); } else { missed.push(name); console.log('MISSED: ' + name); }
  } finally {
    fs.writeFileSync(full, original);
  }
}
console.log(`${caught}/${ran} mutations caught` + (missed.length ? '; not caught: ' + missed.join(' | ') : ''));
process.exit(missed.length ? 1 : 0);
