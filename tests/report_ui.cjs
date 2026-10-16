// Real report script executed against a minimal DOM model. Not browser/visual QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');
const root=path.resolve(__dirname,'..');
const release=path.resolve(process.argv[2]);
const html=fs.readFileSync(path.join(release,'index.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(release,'data/report_data.json'),'utf8'));
const script=fs.readFileSync(path.join(root,'report/report.js'),'utf8');
const api=require(path.join(root,'report/report.js'));
for (const view of Object.values(data.views)) {
  if (view.status==='ready'&&view.scope==='question') {
    const rows=api.categories(data,view);
    assert(Math.abs(rows.reduce((s,r)=>s+r.value,0)-view.n)<1e-8);
  }
  if (view.status!=='ready')assert(api.chart(data,view).includes('Unavailable'));
}
class Element {
  constructor(id){this.id=id;this.value='';this.textContent='';this.innerHTML='';this.handlers={};this.options=[];this.isConnected=true;this.focused=false;}
  get selectedOptions(){return this.options.filter(o=>o.value===this.value);}
  addEventListener(name,fn){(this.handlers[name]??=[]).push(fn);}
  fire(name){for(const fn of this.handlers[name]||[])fn({target:this});}
  focus(){this.focused=true;}
  showModal(){this.open=true;}
  close(){this.open=false;this.fire('close');}
  click(){this.clicked=true;}
}
const elements={};
for(const m of html.matchAll(/\bid="([^"]+)"/g))elements[m[1]]=new Element(m[1]);
for(const m of html.matchAll(/<select id="([^"]+)">([\s\S]*?)<\/select>/g)){
 const e=elements[m[1]];
 for(const o of m[2].matchAll(/<option value="([^"]*)"([^>]*)>([\s\S]*?)<\/option>/g)){
  e.options.push({value:o[1],text:o[3]});if(!e.value||o[2].includes('selected'))e.value=o[1];
 }
}
elements['report-data'].textContent=JSON.stringify(data);
const handlers={};
const document={getElementById:id=>{assert(elements[id],'Missing queried element '+id);return elements[id];},
 addEventListener:(name,fn)=>handlers[name]=fn,createElement:tag=>new Element(tag)};
const context={document,console,Blob,URL,setTimeout,clearTimeout};
vm.runInNewContext(script,context,{filename:'report.js'});
let questionStates=0;
for(const prefix of ['needs','stress']){
 const q=elements[prefix+'-question'],e=elements[prefix+'-engine'],p=elements[prefix+'-population'],m=elements[prefix+'-metric'];
 for(const qo of q.options)for(const eo of e.options)for(const po of p.options)for(const mo of m.options){
  q.value=qo.value;e.value=eo.value;p.value=po.value;m.value=mo.value;q.fire('change');
  const v=api.selectView(data,qo.value,eo.value,po.value);
  const chart=elements[prefix+'-chart'].innerHTML;
  if(v.status==='ready'){
   assert(elements[prefix+'-state'].textContent.includes(v.n+' included answers'));
   assert(elements[prefix+'-prompt'].textContent.includes(data.study.questions.find(q=>q.id===qo.value).text));
   for(const oid of v.observation_ids)assert(elements[prefix+'-detail'].innerHTML.includes(oid));
   if(mo.value==='recommended_sum'){
    assert(!api.categories(data,v,mo.value).some(r=>r.label==='No overall lead'||r.label==='Remaining named brands'));
    assert(elements[prefix+'-chart-note'].textContent.includes('must not be added'));
   }
  }else{assert(chart.includes('Unavailable'));assert(!chart.includes('bar-row'));}
  questionStates++;
 }
}
let visibilityStates=0;
for(const m of elements['visibility-metric'].options)for(const e of elements['visibility-engine'].options)for(const p of elements['visibility-population'].options){
 elements['visibility-metric'].value=m.value;elements['visibility-engine'].value=e.value;elements['visibility-population'].value=p.value;elements['visibility-metric'].fire('change');
 if(p.value==='matched_context'){assert(elements['visibility-chart'].innerHTML.includes('Unavailable'));assert(!elements['visibility-chart'].innerHTML.includes('bar-row'));}
 else assert(elements['visibility-note'].textContent.includes(m.text));
 visibilityStates++;
}
let contrastStates=0;
for(const c of elements['contrast-choice'].options)for(const p of elements['contrast-population'].options){
 elements['contrast-choice'].value=c.value;elements['contrast-population'].value=p.value;elements['contrast-choice'].fire('change');
 const def=data.study.contrasts.find(x=>x.id===c.value);
 if(def.analysis_status==='post_collection_exploratory')assert(elements['contrast-result'].innerHTML.includes('Post-collection exploratory'));
 if(def.analysis_status==='prespecified'&&p.value==='matched_context')assert(elements['contrast-result'].innerHTML.includes('Unavailable'));
 contrastStates++;
}
let matrixStates=0;
for(const m of elements['matrix-metric'].options)for(const e of elements['matrix-engine'].options)for(const p of elements['matrix-population'].options)for(const r of elements['matrix-roster'].options){
 elements['matrix-metric'].value=m.value;elements['matrix-engine'].value=e.value;elements['matrix-population'].value=p.value;elements['matrix-roster'].value=r.value;elements['matrix-metric'].fire('change');
 const brands=r.value==='all'?data.competitor_matrix.brands:data.competitor_matrix.core_brands;
 for(const brand of brands)assert(elements['matrix-table'].innerHTML.includes(brand.replaceAll('&','&amp;').replaceAll("'",'&#39;')));
 if(p.value==='matched_context')assert(elements['matrix-table'].innerHTML.includes('Unavailable'));
 if(m.value==='recommended_sum')assert(elements['matrix-note'].textContent.includes('nonexclusive'));
 matrixStates++;
}
elements['matrix-metric'].value='first_choice_credit_sum';elements['matrix-engine'].value='all';elements['matrix-population'].value='baseline';elements['matrix-metric'].fire('change');
const matrixButton=new Element('matrix-cell');matrixButton.dataset={matrixQuestion:'Q6',matrixBrand:'Private label: Great Value'};matrixButton.closest=selector=>selector==='[data-matrix-question]'?matrixButton:null;
handlers.click({target:matrixButton});assert(elements['evidence-dialog'].open);assert(elements['evidence-body'].innerHTML.includes('9 / 12'));
assert(elements['evidence-body'].innerHTML.includes('main/chatgpt/Q6/1'));elements['close-evidence'].fire('click');assert(matrixButton.focused);
for(const o of Object.values(data.observations)){
 const button=new Element('trigger');button.dataset={observation:o.id};button.closest=()=>button;
 handlers.click({target:button});assert(elements['evidence-dialog'].open);
 assert(elements['evidence-body'].innerHTML.includes(api.chart?o.model.replaceAll('&','&amp;'):'unused'));
 elements['close-evidence'].fire('click');assert(!elements['evidence-dialog'].open);assert(button.focused);
}
for(const o of Object.values(data.observations).filter(o=>o.quality==='exclude')){assert(!elements['supplement-table'].innerHTML.includes('data-observation="'+o.id+'"'));}
let browseStates=0;
for(const e of elements['browse-engine'].options)for(const q of elements['browse-question'].options){
 elements['browse-engine'].value=e.value;elements['browse-question'].value=q.value;elements['browse-engine'].fire('change');
 const n=Object.values(data.observations).filter(o=>o.quality==='include'&&(e.value==='all'||o.engine===e.value)&&(q.value==='all'||o.question_id===q.value)).length;
 assert(elements['browse-results'].innerHTML.includes(n+' included answers'));
 for(const o of Object.values(data.observations).filter(o=>o.quality==='exclude'))assert(!elements['browse-results'].innerHTML.includes('data-observation="'+o.id+'"'));
 browseStates++;
}
console.log(JSON.stringify({verification:'DOM model and data checks; not real browser QA',questionStates,visibilityStates,matrixStates,contrastStates,browseStates,evidenceDialogs:Object.keys(data.observations).length}));
