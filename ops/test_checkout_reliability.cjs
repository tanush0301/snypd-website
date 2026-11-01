/* Run: node ops/test_checkout_reliability.cjs. No network, real users or payments. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'plans.html'), 'utf8');
function section(from, to) {
  const a = html.indexOf(from), b = html.indexOf(to, a);
  assert(a >= 0 && b > a, 'Missing source section: ' + from);
  return html.slice(a, b);
}
const load = section('  function norm(p) {', '  // Homepage START');
const requested = section('  function openRequested() {', '\n  paintAll();');
const startup = section('  paintAll();\n  loadPlan()', '  // ----- Phone sticky bar');
const cta = section('  function ctaFor(k) {', '  // These CTAs');
let checks = 0;
async function journey(responses, options = {}) {
  const calls = { reads: 0, opens: 0, history: 0, metadata: 0 };
  const user = { id: 'test-account', email: options.noEmail ? null : 'test@example.invalid', user_metadata: {} };
  const sb = {
    auth: {
      getSession: async () => options.sessionError ? {error: new Error('session unavailable')} : { data: { session: options.loggedOut ? null : {user} } },
      updateUser: async () => { calls.metadata++; return {}; }
    },
    from: () => ({select: () => ({eq: () => ({maybeSingle: async () => {
      const response = responses[Math.min(calls.reads++, responses.length - 1)];
      if (response instanceof Error) throw response;
      return response;
    }})})})
  };
  const g = {
    SNYPD: {sbReady: Promise.resolve(sb), supabase: sb},
    auth: {signedIn: false, plan: null, planError: false},
    ALL: ['free','solo','kickstart','pro','elite','pass'],
    ACTIVE: ['active','trialing','past_due','unpaid'],
    NAMES: {free:'FREE',solo:'SOLO',pass:'HUNT PASS'},
    MANAGE: 'https://whop.com/@me/settings/orders/',
    AFF_RE: /^[A-Za-z0-9_.-]{1,60}$/, aff: null, affFromUrl: false,
    storedEmail: null, WHOP_PLANS: {pass:'plan_test'}, URLSearchParams, Date,
    location: {pathname:'/plans',search:'?checkout=pass&lang=fr',hash:''},
    history: {replaceState(){calls.history++;}},
    withAff: x => x, paintAll(){}, openCheckout(){calls.opens++;}
  };
  await vm.runInNewContext(load + requested + cta + startup, g);
  return {g,calls};
}
(async () => {
  const free = {data:{subscription_plan:'free',sub_status:'free'},error:null};
  const failure = {data:null,error:{message:'database unavailable'}};
  for (const responses of [[failure], [{data:null,error:null}], [new Error('network unavailable')],
    [{data:{subscription_plan:'unknown'},error:null}]]) {
    const {g,calls} = await journey(responses);
    assert.equal(g.auth.plan,null);
    assert.equal(g.auth.planError,true);
    assert.equal(calls.opens,0);
    assert.equal(calls.history,0); // Keep the requested offer available after reload.
    assert.equal(calls.metadata,0);
    const action = g.ctaFor('pass');
    assert.equal(action.act,'retry');
    assert.equal(action.href,'/plans?checkout=pass&lang=fr');
    checks++;
  }
  for (const options of [{sessionError:true},{noEmail:true}]) {
    const {g,calls} = await journey([free],options);
    assert.equal(g.auth.planError,true); assert.equal(calls.opens,0); checks++;
  }
  const out = await journey([free],{loggedOut:true});
  assert.equal(out.calls.opens,0); assert.equal(out.g.ctaFor('pass').act,'signup'); checks++;
  for (const responses of [[free],[failure,free]]) {
    const {g,calls} = await journey(responses);
    assert.equal(g.auth.plan,'free'); assert.equal(calls.opens,1);
    assert.equal(g.storedEmail,'test@example.invalid'); checks++;
  }
  for (const plan of ['solo','kickstart','pro','elite']) {
    const {g,calls} = await journey([{data:{subscription_plan:plan,sub_status:'active',whop_product_id:'prod_test'},error:null}]);
    assert.equal(g.auth.plan,plan); assert.equal(calls.opens,0); checks++;
  }
  const pass = await journey([{data:{subscription_plan:'solo',sub_status:'active',whop_product_id:'prod_test',pass_expires_at:new Date(Date.now()+86400000).toISOString()},error:null}]);
  assert.equal(pass.g.auth.plan,'pass'); assert.equal(pass.calls.opens,0); checks++;

  // The actual fallback preserves visible account and offer instructions, without
  // leaking the email into a URL or silently leaving the page.
  const fallbackCode = section('  function checkoutText(text) {','  function openCheckout(k, fallbackHref) {');
  for (const plan of ['solo','pass']) {
    const loading={hidden:true,textContent:''}, mount={hidden:false};
    let link=null, appends=0;
    const overlay={querySelector(selector){
      if(selector==='[data-whop-loading]')return loading;
      if(selector==='[data-hosted-fallback]')return link;
      if(selector==='.whop-embed-box')return {appendChild(el){link=el;appends++;}};
      return mount;
    }};
    const g={window:{},storedEmail:'test@example.invalid',promo:'STAY50',PROMO_PLANS:{solo:true},
      document:{createElement:()=>({setAttribute(){}})}};
    vm.runInNewContext(fallbackCode,g);
    g.showHostedFallback(plan,'https://whop.com/checkout/plan_test?a=partner',overlay);
    g.showHostedFallback(plan,'https://whop.com/checkout/plan_test?a=partner',overlay);
    assert.equal(appends,1); assert.equal(loading.hidden,false); assert.equal(mount.hidden,true);
    assert.match(loading.textContent,/test@example\.invalid/);
    assert.equal(loading.textContent.includes('STAY50'),plan==='solo');
    assert.equal(link.href,'https://whop.com/checkout/plan_test?a=partner');
    assert(!link.href.includes('test@example.invalid'));
    assert.equal(link.textContent,'CONTINUE TO WHOP'); checks++;
  }
  const open = section('  function openCheckout(k, fallbackHref) {','  function closeCheckouts()');
  for (const auth of [{signedIn:false,plan:null},{signedIn:true,plan:null},{signedIn:true,plan:'free'}]) {
    const g={auth,storedEmail:null,document:{querySelector(){throw Error('Checkout must not be touched');}}};
    vm.runInNewContext(open,g);
    assert.equal(g.openCheckout('pass','https://whop.com/checkout/plan_test'),false); checks++;
  }
  // Failure/cancellation returns must not open a checkout before profile verification.
  const returned=section('  (function checkoutReturn() {','\n  document.addEventListener(\'click\'');
  for(const status of ['failed','canceled']) {
    const retry={hidden:true}; let opens=0,replaces=0;
    vm.runInNewContext(returned,{URLSearchParams,WHOP_PLANS:{pass:'plan_test'},
      location:{search:'?checkout=pass&status='+status,replace(){replaces++;}},
      track(){},$:()=>retry,openCheckout(){opens++;}});
    assert.equal(retry.hidden,false);assert.equal(opens,0);assert.equal(replaces,0);checks++;
  }
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    if(!/\bsrc\s*=|application\/ld\+json/i.test(match[1]))new vm.Script(match[2]);
  }
  assert(!html.includes('snypd@gmail.com')); checks++;
  const generator=fs.readFileSync(path.join(root,'ops/seo/gen_regions.py'),'utf8');
  assert(!generator.includes('snypd@gmail.com')); checks++;
  // Source and generated dictionaries must include every new visible string.
  const fr=fs.readFileSync(path.join(root,'ops/i18n/fr.py'),'utf8');
  const asset=fs.readFileSync(path.join(root,'assets/i18n.js'),'utf8');
  const dictionary=JSON.parse(asset.match(/  var DICT = (.*);\n/)[1]).fr;
  for(const key of ['RELOAD TO CHECK PLAN','CHECKING YOUR PLAN','PLAN UNAVAILABLE',
    'Checkout could not load here. Continue on Whop using your SNYPD account email:',
    'Enter promo code','and check the total before paying.','CONTINUE TO WHOP']) {
    assert(fr.includes(key));assert(dictionary[key]);assert.notEqual(dictionary[key],key);checks++;
  }
  console.log('PASS: '+checks+' checkout reliability scenarios; no production requests.');
})().catch(error=>{console.error(error);process.exitCode=1;});
