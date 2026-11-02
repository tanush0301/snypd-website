'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { JSDOM } = require(require.resolve('jsdom', { paths: [path.join(__dirname, 'auth')] }));
const root = process.env.SNYPD_EXPANSION_ROOT || path.join(__dirname,'..');
const contract = fs.readFileSync(path.join(root,'assets/search-contract.js'),'utf8');
const script = fs.readFileSync(path.join(root,'assets/search-builder.js'),'utf8');
function boot(t, {lang='en',query='',clipboard=false}={}) {
  const file=lang==='fr'?'fr/creer-recherche-vinted.html':'vinted-search-builder.html';
  const dom=new JSDOM(fs.readFileSync(path.join(root,file),'utf8'),{url:'https://www.snypd.store/'+file.replace(/\.html$/,'')+query,runScripts:'outside-only'});
  t.after(()=>dom.window.close());
  const w=dom.window,events=[],requests=[],copies=[];
  w.gtag=(...args)=>events.push(args);w.fetch=(...args)=>requests.push(args);
  if(clipboard)w.navigator.clipboard={writeText:async value=>copies.push(value)};
  w.eval(contract);w.eval(script);
  const form=w.document.querySelector('[data-search-builder]');
  return {w,form,events,requests,copies,output:form.querySelector('[data-builder-url]'),result:form.querySelector('[data-builder-result]'),
    submit(values={}){for(const [k,v] of Object.entries(values))form.elements[k].value=v;form.dispatchEvent(new w.Event('submit',{cancelable:true,bubbles:true}));}};
}
test('all 26 marketplace/currency mappings match the reviewed dashboard contract',()=>{
  const c={URL,URLSearchParams};vm.runInNewContext(contract,c);
  const dash=fs.readFileSync(path.join(__dirname,'../dashboard.html'),'utf8');
  const supported=JSON.parse(dash.match(/const SUPPORTED_VINTED = (\[[\s\S]*?\]);/)[1].replace(/'/g,'"'));
  const currencies=JSON.parse(dash.match(/const SITE_CURRENCY = (\{[\s\S]*?\});/)[1].replace(/'/g,'"'));
  assert.deepEqual(c.SNYPDSearch.markets.map(m=>m[0]).sort().join(','),supported.sort().join(','));
  for(const m of c.SNYPDSearch.markets){assert.equal(m[3],currencies[m[0]]||'EUR');const u=new URL(c.SNYPDSearch.build({site:m[0],q:'A & B / <test>',min:'1,25',max:'23.45'}));
    assert.equal(u.hostname,'www.'+m[0]);assert.equal(u.searchParams.get('search_text'),'A & B / <test>');
    assert.equal(u.searchParams.get('price_from'),'1.25');assert.equal(u.searchParams.get('price_to'),'23.45');assert.equal(u.searchParams.has('currency'),false);}
});
test('the actual dashboard URL constructor does not round a decimal maximum upward',()=>{
  const dash=fs.readFileSync(path.join(__dirname,'../dashboard.html'),'utf8');
  const code=dash.slice(dash.indexOf('    function vqBuild('),dash.indexOf('    window.SNYPD = window.SNYPD || {};',dash.indexOf('    function vqBuild(')));
  const c={URL};vm.runInNewContext(code,c);const u=new URL(c.vqBuild('vinted.co.uk','coat','23.45',1.25));
  assert.equal(u.searchParams.get('price_to'),'23.45');assert.equal(u.searchParams.get('price_from'),'1.25');
});
test('builder is useful without login, preserves decimals and shares only categorical custom events',t=>{
  const h=boot(t);h.submit({words:'Nike & Adidas',site:'vinted.co.uk',min:'1,25',max:'23.45'});
  assert.equal(h.result.hidden,false);const url=new URL(h.output.value);
  assert.equal(url.hostname,'www.vinted.co.uk');assert.equal(url.searchParams.get('price_to'),'23.45');
  const signup=new URL(h.form.querySelector('[data-builder-monitor]').href);
  assert.equal(signup.searchParams.get('site'),'vinted.co.uk');assert.equal(signup.searchParams.get('min'),'1.25');
  assert.equal(signup.searchParams.get('max'),'23.45');assert.deepEqual(h.requests,[]);assert.equal(h.w.localStorage.length,0);
  assert.equal(JSON.stringify(h.events),'[["event","search_builder_generate",{"page_lang":"en"}]]');
});
test('invalid or inverted amounts and arbitrary hosts never produce usable output',t=>{
  const h=boot(t);for(const [min,max] of [['20','20'],['30','20'],['-1','20'],['','1e3'],['','1,000.00'],['','0'],['','1000000.01']]){
    h.submit({words:'Nike',min,max});assert.equal(h.result.hidden,true);assert.ok(h.form.querySelector('[role=alert]').textContent);}
  h.submit({words:'Nike',site:'evil.example',min:'',max:''});assert.equal(h.result.hidden,true);
});
test('a currency switch clears prices and stale results',t=>{
  const h=boot(t);h.submit({words:'jacket',max:'30'});h.form.elements.site.value='vinted.pl';
  h.form.elements.site.dispatchEvent(new h.w.Event('change'));assert.equal(h.result.hidden,true);assert.equal(h.form.elements.max.value,'');
  assert.ok([...h.form.querySelectorAll('[data-builder-currency]')].every(e=>e.textContent==='PLN'));
});
test('French clipboard success and unavailable clipboard both have an accessible result',async t=>{
  for(const clipboard of [true,false]){const h=boot(t,{lang:'fr',clipboard});h.submit({words:'veste',max:'30'});
    h.form.querySelector('[data-builder-copy]').click();await new Promise(r=>setImmediate(r));
    assert.match(h.form.querySelector('[role=status]').textContent,clipboard ? /Lien copié/ : /Copie le lien sélectionné/);
    assert.equal(h.copies.length,clipboard?1:0);}
});
test('profit-budget prefill uses the displayed currency and rejects a mismatch',t=>{
  const h=boot(t,{query:'?currency=GBP&max=23.45'});assert.equal(h.form.elements.site.value,'vinted.co.uk');assert.equal(h.form.elements.max.value,'23.45');
  const bad=boot(t,{query:'?currency=GBP&site=vinted.fr&max=23.45'});assert.equal(bad.form.elements.max.value,'');
});
test('generated builder prefill scrub runs before consent scripts and preserves campaign attribution',t=>{
  const h=boot(t,{query:'?q=private&max=23.45&currency=GBP&utm_source=test&from=home&entry_basis=nav-v1'});
  const text=fs.readFileSync(path.join(root,'vinted-search-builder.html'),'utf8');
  const early=text.match(/<script>(\(function\(\)\{window.SNYPD_BUILDER_PREFILL=[\s\S]*?)<\/script>/)[1];
  assert.ok(text.indexOf(early)<text.indexOf('/assets/consent.js'));h.w.eval(early);
  assert.equal(h.w.location.search,'?utm_source=test&from=home&entry_basis=nav-v1');assert.match(h.w.SNYPD_BUILDER_PREFILL,/private/);
});
