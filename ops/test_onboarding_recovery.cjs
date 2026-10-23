/* Executes the actual dashboard wizard and push closures with isolated DOM/API
 * doubles. No production traffic, account writes or browser permissions.
 * Run: node ops/test_onboarding_recovery.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');
function section(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert(a >= 0 && b > a);
  return html.slice(a, b);
}
const wizard = section('  // ----------------- FIRST-RUN WIZARD', '  // ----------------- HISTORY');
// Trial-end helpers (migration 061) live with the banner code; the wizard calls them.
const trialHelpers = section('  function trialEndMs(p) {', '  const uiFr = ');
const push = section('/* Web push registration.', '</script>');
const tick = () => new Promise(resolve => setImmediate(resolve));
class Element {
  constructor(id) {
    this.id = id; this.style = { display: 'none' }; this.listeners = {}; this.attrs = {};
    this.value = ''; this.disabled = false; this.textContent = ''; this.dataset = {};
    const classes = new Set(id === 'wiz-toggle-push' ? ['is-on'] : []);
    this.classList = { add: x => classes.add(x), remove: x => classes.delete(x),
      contains: x => classes.has(x), toggle: x => classes.has(x) ? classes.delete(x) : classes.add(x) };
  }
  addEventListener(type, cb) { (this.listeners[type] ||= []).push(cb); }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k]; }
  querySelectorAll() { return []; }
  focus() {}
  async click() { if (!this.disabled) for (const cb of this.listeners.click || []) await cb({}); }
}
function base() {
  const elements = new Map(), events = {};
  const el = id => { if (!elements.has(id)) elements.set(id, new Element(id)); return elements.get(id); };
  const g = { console: { error() {}, warn() {}, log() {} }, Date, Promise, Number, String, Uint8Array,
    Event: class { constructor(type) { this.type = type; } },
    document: { getElementById: el, querySelectorAll: () => [] },
    localStorage: { getItem: () => null, removeItem() {} },
    addEventListener: (name, cb) => (events[name] ||= []).push(cb),
    dispatchEvent: event => { for (const cb of events[event.type] || []) cb(event); },
    SNYPD: {}, navigator: { userAgent: 'QA desktop', platform: 'Linux', maxTouchPoints: 0 },
    location: { href: 'https://www.snypd.store/dashboard' },
    matchMedia: () => ({ matches: false }), atob: s => Buffer.from(s, 'base64').toString('binary'),
  };
  g.window = g;
  return { g, el, context: vm.createContext(g), events };
}
async function wizardFixture({count = 0, status = 'off', insertError = null, xpFails = false, pendingInsert = null, trialStart = null, trialEnds = null, boot = null, insertedRow = {id: 'h1'}} = {}) {
  const f = base(); let inserts = 0, countValue = count, countReads = 0;
  // dashboard_boot snapshot (migration 054): the wizard takes its hunt count from it once.
  f.g.fromBoot = reader => { assert.equal(reader, 'wizard'); const b = boot; boot = null; return b; };
  f.g.uid = 'test-user'; f.g.profile = {}; f.g.effectivePlan = 'free'; f.g.eliteBanner = null;
  f.g.xpEventExistsEver = async () => { if (xpFails) throw new Error('XP down'); return false; };
  f.g.awardXP = async () => 20;
  f.g.SNYPD.alertsStatus = async () => ({state: status});
  f.g.SNYPD.enableAlerts = async () => ({ok: false, state: 'error', message: 'Retry safely'});
  f.g.SNYPD.vq = { fillSites() {}, currencyFor: () => 'EUR', floorFor: () => 30, build: () => 'https://www.vinted.fr/catalog?search_text=carhartt' };
  f.g.sb = { from() { return {
    select() { return this; }, eq() { return this; },
    then(resolve, reject) { countReads++; return Promise.resolve({count:countValue,error:null}).then(resolve,reject); },
    maybeSingle() { return Promise.resolve({data:{free_trial_started_at:trialStart, trial_ends_at:trialEnds},error:null}); },
    // Like supabase-js: insert() is a chainable builder (.select('*').single()) that runs once when awaited.
    insert() { let run = null; const b = { select() { return b; }, single() { return b; },
      then(resolve, reject) { run ||= (async () => { inserts++; if (pendingInsert) await pendingInsert; if (!insertError) countValue++;
        return {data: insertError ? null : insertedRow, error: insertError}; })(); return run.then(resolve, reject); } }; return b; },
  }; } };
  vm.runInContext(trialHelpers, f.context); f.g.paintTrialValue = async () => {};
  await vm.runInContext(wizard, f.context); await tick();
  f.inserts = () => inserts;
  f.countReads = () => countReads;
  f.setInsertError = value => { insertError = value; };
  f.setStatus = value => { status = value; f.g.dispatchEvent(new f.g.Event('snypd:alerts-changed')); };
  return f;
}
async function pushFixture({sub = true, registerStatus = 200, permission = 'granted', ios = false, standalone = false, statusReady = true} = {}) {
  const f = base(); let permissionCalls = 0, subscribeCalls = 0, unsubscribes = 0, statusCalls = 0;
  const subscription = { toJSON: () => ({ endpoint: 'https://push.invalid/test', keys: {auth:'fake', p256dh:'fake'} }), unsubscribe: async () => { unsubscribes++; return true; } };
  const reg = { pushManager: { getSubscription: async () => sub ? subscription : null, subscribe: async () => { subscribeCalls++; sub = true; return subscription; } } };
  f.g.Notification = { permission, requestPermission: async () => { permissionCalls++; f.g.Notification.permission = 'granted'; return 'granted'; } };
  f.g.PushManager = function() {};
  f.g.navigator.standalone = standalone;
  if (ios) f.g.navigator.userAgent = 'iPhone';
  f.g.navigator.serviceWorker = { register: async () => reg, ready: Promise.resolve(reg), addEventListener() {} };
  f.g.SNYPD.supabase = { auth: { getSession: async () => ({data:{session:{access_token:'fake'}}}) } };
  f.g.fetch = async (url, opts) => {
    if (url.endsWith('/status')) { statusCalls++; return {status:200, json:async()=>({ready:statusReady})}; }
    if (url.endsWith('/key')) return {status:200, json:async()=>({key:'AAAA'})};
    assert(url.endsWith('/subscribe') || url.endsWith('/unsubscribe'));
    assert.equal(opts.method, 'POST');
    return {status: registerStatus, json:async()=>({})};
  };
  vm.runInContext(push, f.context);
  await f.g.SNYPD.alertsStatus();
  f.metrics = () => ({permissionCalls,subscribeCalls,unsubscribes,statusCalls});
  f.setRegisterStatus = value => { registerStatus = value; };
  f.setStatusReady = value => { statusReady = value; };
  return f;
}
(async () => {
  let passed = 0;
  // A rejected insert must not advance, must retain input and must be retryable.
  let f = await wizardFixture({insertError:{message:'quota or network error'}});
  f.el('wiz-step-1').style.display = ''; f.el('wiz-q-words').value = 'carhartt';
  await f.el('wiz-q-save').click();
  assert.equal(f.el('wiz-step-1').style.display, '');
  assert.equal(f.el('wiz-step-2').style.display, 'none');
  assert.equal(f.el('wiz-q-save').disabled, false);
  assert.equal(f.el('wiz-q-words').value, 'carhartt');
  assert.equal(f.el('wiz-q-err').style.display, 'block');
  f.setInsertError(null); await f.el('wiz-q-save').click();
  assert.equal(f.el('wiz-step-2').style.display, ''); assert.equal(f.inserts(),2); passed++;

  // Calm mode (migration 064): a saved row that has push_mode gets the alert-style step
  // before alerts, with Continue disabled until a style is picked. A row without it
  // (column missing) goes straight to alerts, which every case above covers.
  f = await wizardFixture({insertedRow: {id: 'h1', push_mode: 'every', push_calm_minutes: 15}});
  f.el('wiz-step-1').style.display = ''; f.el('wiz-q-words').value = 'carhartt';
  await f.el('wiz-q-save').click();
  assert.equal(f.el('wiz-step-mode').style.display, ''); assert.equal(f.el('wiz-step-2').style.display, 'none');
  assert.equal(f.el('wiz-step-mode').dataset.huntId, 'h1'); assert.equal(f.el('wiz-mode-next').disabled, true);
  await f.el('wiz-mode-next').click();
  assert.equal(f.el('wiz-step-2').style.display, 'none'); assert.equal(f.inserts(), 1); passed++;

  // Existing hunters get a visible resume action without an automatic modal.
  f = await wizardFixture({count:1});
  assert.equal(f.el('wiz-overlay').style.display, 'none');
  assert.equal(f.el('alerts-setup-card').style.display, '');
  await f.el('alerts-setup-resume').click();
  assert.equal(f.el('wiz-step-2').style.display, ''); assert.equal(f.inserts(),0);
  f.setStatus('on'); await tick(); assert.equal(f.el('alerts-setup-card').style.display,'none'); passed++;

  // Analytics/XP failure after a successful insert is not a failed hunt save.
  f = await wizardFixture({xpFails:true}); f.el('wiz-q-words').value = 'jordan';
  await f.el('wiz-q-save').click(); await tick();
  assert.equal(f.el('wiz-step-2').style.display,''); assert.equal(f.inserts(),1); passed++;

  // Two presses cannot create two requests while the first insert is pending.
  let release; const pending = new Promise(resolve=>{release=resolve;});
  f = await wizardFixture({pendingInsert:pending}); f.el('wiz-q-words').value='nike';
  const saving=f.el('wiz-q-save').click(); await f.el('wiz-q-save').click();
  assert.equal(f.inserts(),1); release(); await saving; passed++;

  // Failed enabling remains retryable; "later" is the explicit separate exit.
  f=await wizardFixture({count:1}); await f.el('alerts-setup-resume').click();
  await f.el('wiz-enable-alerts').click(); await f.el('wiz-enable-alerts').click();
  assert.equal(f.el('wiz-overlay').style.display,'flex');
  assert.equal(f.el('wiz-enable-alerts').textContent,'Try again');
  await f.el('wiz-finish').click(); assert.equal(f.el('wiz-overlay').style.display,'none'); passed++;

  // Boot snapshot: no hunts opens the wizard, one hunt does not; neither reads the count again.
  f=await wizardFixture({count:5, boot:{searches:[]}});
  assert.equal(f.el('wiz-overlay').style.display,'flex'); assert.equal(f.countReads(),0); passed++;
  f=await wizardFixture({count:0, boot:{searches:[{id:'s1',is_active:true}]}});
  assert.equal(f.el('wiz-overlay').style.display,'none'); assert.equal(f.el('alerts-setup-card').style.display,''); assert.equal(f.countReads(),0); passed++;

  f=await wizardFixture({count:null});
  assert.equal(f.el('wiz-overlay').style.display,'none'); assert.equal(f.inserts(),0); passed++;

  // Legacy hunts without a trial stamp are never promised another seven days.
  f=await wizardFixture({count:1}); await f.el('alerts-setup-resume').click(); await tick();
  assert(f.el('wiz-trial-note').textContent.includes('only while it is open')); passed++;

  // A newly saved hunt re-reads the database trigger's timestamp immediately.
  f=await wizardFixture({trialStart:new Date().toISOString()}); f.el('wiz-q-words').value='nike';
  await f.el('wiz-q-save').click(); await tick();
  assert(f.el('wiz-trial-note').textContent.includes('Your Free trial runs 24/7'));
  assert(f.el('wiz-trial-note').textContent.includes('Enable alerts on this device')); passed++;

  // 061: a 72 h trial that already ended is not promised 24/7 (trial_ends_at wins over start + 7 days).
  f=await wizardFixture({trialStart:new Date(Date.now()-4*864e5).toISOString(), trialEnds:new Date(Date.now()-864e5).toISOString()});
  f.el('wiz-q-words').value='nike'; await f.el('wiz-q-save').click(); await tick();
  assert(!f.el('wiz-trial-note').textContent.includes('Your Free trial runs 24/7')); passed++;
  // ...and one still running (extended or not) is.
  f=await wizardFixture({trialStart:new Date(Date.now()-4*864e5).toISOString(), trialEnds:new Date(Date.now()+864e5).toISOString()});
  f.el('wiz-q-words').value='nike'; await f.el('wiz-q-save').click(); await tick();
  assert(f.el('wiz-trial-note').textContent.includes('Your Free trial runs 24/7')); passed++;

  // Browser subscription + rejected server registration must not say "on".
  f=await pushFixture({registerStatus:503});
  assert.equal((await f.g.SNYPD.alertsStatus()).state,'error');
  assert.equal(f.el('btn-notify').textContent,'Enable alerts');
  f.setRegisterStatus(200); assert.equal((await f.g.SNYPD.enableAlerts()).ok,true);
  assert.equal(f.metrics().permissionCalls,0); passed++;

  // A rejected unsubscribe must preserve the local subscription and status.
  f=await pushFixture(); f.setRegisterStatus(503);
  assert.equal((await f.g.SNYPD.disableAlerts()).ok,false);
  assert.equal(f.metrics().unsubscribes,0);
  assert.equal((await f.g.SNYPD.alertsStatus()).state,'on'); passed++;

  // iPhone tab requires installation even if PushManager happens to exist.
  f=await pushFixture({ios:true,standalone:false,sub:false,permission:'default'});
  assert.equal((await f.g.SNYPD.alertsStatus()).state,'ios-install');
  assert.equal((await f.g.SNYPD.enableAlerts()).ok,false);
  assert.equal(f.metrics().permissionCalls,0); passed++;

  // On an installed device, permission must be requested in the click stack.
  f=await pushFixture({ios:true,standalone:true,sub:false,permission:'default'});
  const enabling=f.g.SNYPD.enableAlerts();
  assert.equal(f.metrics().permissionCalls,1); assert.equal((await enabling).ok,true); passed++;

  // Recovery from unavailable startup requires a fresh click for permission.
  f=await pushFixture({statusReady:false,sub:false,permission:'default'});
  f.setStatusReady(true); let result=await f.g.SNYPD.enableAlerts();
  assert.equal(result.ok,false); assert.equal(result.state,'off');
  assert.equal(f.metrics().permissionCalls,0);
  assert.equal((await f.g.SNYPD.enableAlerts()).ok,true); passed++;

  console.log(`PASS: ${passed} onboarding/push recovery scenarios; no production requests.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
