/* Run: node ops/test_purchase_flow.cjs. Executes deployed flow functions without
 * network calls, real accounts, payments, or notification permissions. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const auth = read('assets/auth.js'), plans = read('plans.html'), dashboard = read('dashboard.html');
function between(src, from, to) {
  const a = src.indexOf(from), b = src.indexOf(to, a);
  assert(a >= 0 && b > a, `Missing source section: ${from}`);
  return src.slice(a, b);
}
const names = auth.match(/  var PLAN_NAMES = [^;]+;/)[0];
const terms = between(auth, '  var PLAN_TERMS = {', '  var LAST_EMAIL_KEY');
const choose = between(auth, "  var plan = (qs.get('plan')", '  /* A price-guide');
const header = between(auth, '  function tpl() {', "    if (v === 'forgot')") + '\nreturn out.join(\'\');\n}';
let checks = 0;
function signupHeader(plan, view = 'signup') {
  const scope = {plan, H1:'', STACK:'', S:{view, status:'idle',errors:{},founding:null}};
  vm.runInNewContext(names + terms + header, scope);
  return scope.tpl();
}
for (const view of ['signup','login','verify']) {
  const pass = signupHeader('pass',view), solo = signupHeader('solo',view);
  assert.match(pass, /HUNT PASS/);
  assert.match(pass, /€3\.99 once · 30 days · no automatic renewal/);
  assert.doesNotMatch(pass, /€5\.99|upgrade in one click/);
  assert.match(solo, /€5\.99\/month · renews monthly until you cancel/);
  assert.match(pass, /Creating your account does not take a payment/);
  checks++;
}
assert.doesNotMatch(signupHeader(''),/data-selected-offer/); checks++;
const now=Date.now();
for (const [saved, expected] of [
  [{plan:'pass',ts:now},'pass'], [{plan:'solo',ts:now},'solo'],
  [{plan:'pass',ts:now-8*864e5},''], [{plan:'pass',ts:now+864e5},''],
  [{plan:'unknown',ts:now},''], [{plan:'pass'},''], [null,'']
]) {
  const scope={qs:new URLSearchParams(),PAGE:'login',Date,lsGet:()=>JSON.stringify(saved)};
  vm.runInNewContext(names+choose,scope);
  assert.equal(scope.plan,expected);checks++;
}
const explicit={qs:new URLSearchParams('plan=solo'),PAGE:'login',Date,
  lsGet:()=>JSON.stringify({plan:'pass',ts:now})};
vm.runInNewContext(names+choose,explicit);
assert.equal(explicit.plan,'solo');checks++;

const openRequested=between(plans,'  function openRequested() {','\n  paintAll();');
const openCheckout=between(plans,'  function openCheckout(k, fallbackHref) {','  function closeCheckouts()');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  for (const [want,id] of [['pass','plan_zLbAN08OXSJYo'],['solo','plan_zYBunt6RBlsUg']]) {
    let clicked=false;
    const scope={URLSearchParams,auth:{signedIn:true,plan:'free'},WHOP_PLANS:{[want]:id},
      norm:p=>p===want?p:null,location:{search:'?checkout='+want,pathname:'/plans',hash:'',href:''},
      history:{replaceState(){}},SNYPD:{},track(){},withAff:url=>url+'?a=partner',
      document:{activeElement:{},body:{style:{}},querySelector:()=>({hidden:true,querySelector:()=>({focus(){clicked=true;}})})},
      mountCheckout:()=>Promise.reject(Error('script unavailable'))};
    vm.runInNewContext(openCheckout+openRequested+'\nopenRequested();',scope);
    await tick();
    assert(clicked);
    assert.equal(scope.location.href,'https://whop.com/checkout/'+id+'?a=partner');checks++;
  }
  // Never open another paid checkout automatically over an active paid plan.
  for (const plan of ['pass','solo','kickstart','pro','elite']) {
    let opened=false;
    vm.runInNewContext(openRequested+'\nopenRequested();',{
      URLSearchParams,auth:{signedIn:true,plan},WHOP_PLANS:{pass:'known'},norm:()=> 'pass',
      location:{search:'?checkout=pass',pathname:'/plans',hash:''},history:{replaceState(){}},
      SNYPD:{},openCheckout(){opened=true;},withAff:x=>x
    });
    assert.equal(opened,false);checks++;
  }
  const renewal=between(dashboard,'  const passEndMs = Date.parse(profile.pass_expires_at',
    '  // Plan chosen at sign-up');
  for (const [days,visible] of [[4,true],[6,false],[-1,false]]) {
    const nodes={'.elite-banner__title':{},'.elite-banner__text':{},'a.btn':{}};
    const banner={style:{display:'none'},querySelector:q=>nodes[q]};
    vm.runInNewContext(renewal,{Date,Intl,Number,profile:{pass_expires_at:new Date(now+days*864e5).toISOString()},
      effectivePlan:'solo',eliteBanner:banner,uiFr:()=>false});
    assert.equal(banner.style.display==='',visible);
    if(visible){
      assert.equal(nodes['a.btn'].href,'/plans#card-solo');
      assert.equal(nodes['a.btn'].textContent,'See options');
      assert.match(nodes['.elite-banner__text'].textContent,/after this one expires/);
    }
    checks++;
  }
  // The homepage's purchase path retains the selected Pass, like the other offers.
  assert.match(read('index.html'),/href="\/signup\?plan=pass"[^>]*>GET HUNT PASS<\/a>/);checks++;
  const g={document:{documentElement:{hasAttribute:()=>true,getAttribute:()=>null,setAttribute(){}},
      readyState:'complete',querySelectorAll:()=>[],addEventListener(){},head:{appendChild(){}},createElement:()=>({})},
    location:{search:'?lang=fr',href:'https://www.snypd.store/signup?plan=pass&lang=fr'},
    localStorage:{getItem:()=>null,setItem(){}},navigator:{languages:['fr-FR']},
    MutationObserver:function(){this.observe=()=>{};},URLSearchParams,URL,Promise};
  g.window=g;
  vm.runInNewContext(read('assets/i18n.js'),g);
  for(const text of ['SELECTED OFFER',
    '€3.99 once · 30 days · no automatic renewal',
    '€5.99/month · renews monthly until you cancel',
    'Account first, then your hunt and secure checkout. Creating your account does not take a payment.',
    'See options']) {
    assert.notEqual(g.SNYPD_I18N.t(text),text);checks++;
  }
  console.log(`PASS: ${checks} purchase-flow scenarios; no production requests.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
