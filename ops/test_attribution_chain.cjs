'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {JSDOM}=require(require.resolve('jsdom',{paths:[path.join(__dirname,'auth')]}));
const source=fs.readFileSync(path.join(__dirname,'../assets/consent.js'),'utf8');
const start=source.indexOf('/* Not about consent: keeps campaign tags');
const end=source.indexOf('/* Not about consent: Vercel Web Analytics',start);
assert.ok(start>=0&&end>start);
function page(t,url,href){const dom=new JSDOM('<a href="'+href+'">Continue</a>',{url:new URL(url,'https://www.snypd.store').href,runScripts:'outside-only'});
 t.after(()=>dom.window.close());dom.window.eval(source.slice(start,end));const a=dom.window.document.querySelector('a');
 a.dispatchEvent(new dom.window.Event('pointerdown',{bubbles:true}));return {w:dom.window,url:new URL(a.href)};}
test('a public navigation chain retains its initial path through tools and signup without storage',t=>{
 const first=page(t,'/fr/achat-revente-vinted?utm_source=test','/fr/calculateur-marge-vinted');
 assert.equal(first.url.searchParams.get('from'),'fr.achat-revente-vinted');assert.equal(first.url.searchParams.get('entry_basis'),'nav-v1');
 const second=page(t,first.url,'/signup?lang=fr');assert.equal(second.url.searchParams.get('from'),'fr.achat-revente-vinted');
 assert.equal(second.url.searchParams.get('utm_source'),'test');assert.equal(second.w.localStorage.length,0);assert.equal(second.w.document.cookie,'');
});
test('legacy hints are not relabelled as new first-page observations',t=>{
 const h=page(t,'/vinted-profit-calculator?from=vinted-bot','/signup');
 assert.equal(h.url.searchParams.get('from'),'vinted-bot');assert.equal(h.url.searchParams.has('entry_basis'),false);
});
test('private pages and assets never acquire a first-page breadcrumb',t=>{
 for(const target of ['/dashboard','/account','/assets/data/price-index.json','https://example.com/']){
  const h=page(t,'/vinted-search-builder',target);assert.equal(h.url.searchParams.has('from'),false);}
 for(const origin of ['/dashboard','/account/settings','/admin/users','/login']){
  const h=page(t,origin,'/signup');assert.equal(h.url.searchParams.has('from'),false);}
});
