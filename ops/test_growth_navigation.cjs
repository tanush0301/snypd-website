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
  let actual=href;
  const a={getAttribute:()=>actual,setAttribute:(k,v)=>{actual=v;}};
  vm.runInNewContext(decorate,{URL,location:{href:'https://www.snypd.store/fr/bot-vinted',origin:'https://www.snypd.store'},
    document:{documentElement:{getAttribute:()=> 'fr',hasAttribute:()=>false},readyState:'complete',querySelectorAll:()=>[a]}});
  assert.equal(actual,expected); checks++;
}
console.log(`PASS: ${checks} growth navigation checks.`);
