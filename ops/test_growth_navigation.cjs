/* Run: node ops/test_growth_navigation.cjs. No network. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
const plans = fs.readFileSync(path.join(root, 'plans.html'), 'utf8');
const consent = fs.readFileSync(path.join(root, 'assets/consent.js'), 'utf8');
const code = plans.slice(plans.indexOf('  function signupContext('), plans.indexOf('  function paintCta('));
function context(search, lang='fr') {
  const scope = {URL, URLSearchParams, location:{origin:'https://www.snypd.store',search}, window:{SNYPD_I18N:{lang}}};
  vm.runInNewContext(code, scope); return scope.signupContext;
}
let checks=0;
for (const plan of ['free','pass','solo','kickstart','pro','elite']) {
  const f=context('?from=fr.bot-vinted&utm_source=creator&utm_campaign=october&a=partner');
  const url=new URL(f('/signup'+(plan==='free'?'':'?plan='+plan)), 'https://www.snypd.store');
  assert.equal(url.searchParams.get('from'),'fr.bot-vinted');
  assert.equal(url.searchParams.get('lang'),'fr');
  assert.equal(url.searchParams.get('utm_source'),'creator');
  assert.equal(url.searchParams.get('a'),'partner');
  assert.equal(url.searchParams.get('plan'),plan==='free'?null:plan); checks++;
}
assert.equal(context('?from=https://bad.test&utm_source=user@example.com')('/signup'),'/signup?lang=fr'); checks++;
assert.equal(context('?from=home','en')('/signup?lang=fr&from=existing#form'),'/signup?lang=fr&from=existing#form'); checks++;
assert.equal(context('?from=home')('https://whop.com/checkout/example'),'https://whop.com/checkout/example'); checks++;
assert.match(plans,/if \(h && c.act === 'signup'\) h = signupContext\(h\)/); checks++;
const start=consent.indexOf('/* Not about consent: a visitor reading a French page');
const end=consent.indexOf('/* Not about consent: keeps campaign tags',start);
const decorate=consent.slice(start,end);
for (const [href,expected] of [
  ['/plans?from=fr.bot-vinted#card-pass','/plans?from=fr.bot-vinted&lang=fr#card-pass'],
  ['/plans?lang=en','/plans?lang=en'],
  ['https://outside.example/plans','https://outside.example/plans'],
  ['/signup','/signup?lang=fr'],
]) {
  let actual=href; const on={};
  const a={getAttribute:()=>actual,setAttribute:(k,v)=>{actual=v;}};
  vm.runInNewContext(decorate,{URL,location:{href:'https://www.snypd.store/fr/bot-vinted',origin:'https://www.snypd.store'},
    document:{documentElement:{getAttribute:()=> 'fr',hasAttribute:()=>false},readyState:'complete',querySelectorAll:()=>[a],
      addEventListener:(t,f)=>{on[t]=f;}}});
  assert.equal(actual,href,'href must stay clean until the link is used'); checks++;
  for (const t of ['pointerdown','focusin','click']) assert.equal(typeof on[t],'function');
  on.pointerdown({target:{closest:()=>a}}); on.click({target:{closest:()=>a}});
  assert.equal(actual,expected); checks++;
}
const tagStart=end, tagEnd=consent.indexOf('/* Not about consent: Vercel Web Analytics',tagStart);
const tagging=consent.slice(tagStart,tagEnd);
for (const [search,pathname,href,expected] of [
  ['?utm_source=chatgpt.com&a=partner','/vinted-bot','/signup','/signup?utm_source=chatgpt.com&a=partner&from=vinted-bot&entry_basis=nav-v1'],
  ['','/fr/bot-vinted','/plans#card-pass','/plans?from=fr.bot-vinted&entry_basis=nav-v1#card-pass'],
  ['','/vinted-bot','/faq','/faq?from=vinted-bot&entry_basis=nav-v1'],
  ['?from=fr.guide-prix-vinted','/signup','/login','/login?from=fr.guide-prix-vinted'],
  ['','/vinted-bot','/dashboard','/dashboard'],
  ['','/vinted-bot','https://example.com/','https://example.com/'],
]) {
  let actual=href; const on={};
  const a={getAttribute:()=>actual,setAttribute:(k,v)=>{actual=v;}};
  vm.runInNewContext(tagging,{URL,URLSearchParams,window:{},location:{search,pathname,href:'https://www.snypd.store'+pathname+search,origin:'https://www.snypd.store'},
    document:{readyState:'complete',querySelectorAll:()=>[a],addEventListener:(t,f)=>{on[t]=f;}}});
  assert.equal(actual,href,'href must stay clean until the link is used'); checks++;
  on.focusin({target:{closest:()=>a}});
  assert.equal(actual,expected); checks++;
}
const auth = fs.readFileSync(path.join(root, 'assets/auth.js'), 'utf8');
const planNames = {};
vm.runInNewContext(auth.match(/var PLAN_NAMES = [^;]+;/)[0], planNames);
assert.equal(planNames.PLAN_NAMES.pass, 'HUNT PASS'); checks++;
console.log(`PASS: ${checks} growth navigation checks.`);
