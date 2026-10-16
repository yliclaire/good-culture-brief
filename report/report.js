(function () {
  'use strict';
  const key = (layer, population, scope, name, engine) => [layer, population, scope, name, engine].join('|');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = value => Number.isInteger(Number(value)) ? String(Number(value)) : Number(value).toFixed(1);
  const engineName = value => ({chatgpt:'ChatGPT',claude:'Claude',gemini:'Gemini',perplexity:'Perplexity',google_ai_mode:'Google AI Mode',copilot_search:'Copilot Search',openai:'OpenAI API',anthropic:'Claude API'}[value] || value);
  function selectView(data, question, engine='all', population='baseline', layer=data.study.layers[0].id) {
    return data.views[key(layer, population, 'question', question, engine)];
  }
  function competitiveRows(data,view,metric='first_choice_credit_sum') {
    const focal=data.study.focal_brand, secondary=metric.endsWith('_rate')?'recommendation_rate':'recommended_sum';
    const ranked=view.rows.filter(r=>r.brand!==focal&&(r[metric]>0||r[secondary]>0)).sort((a,b)=>b[metric]-a[metric]||b[secondary]-a[secondary]||(a.brand<b.brand?-1:a.brand>b.brand?1:0));
    const chosen=ranked.slice(0,3);
    if(ranked.length>3&&ranked[2][metric]>0)chosen.push(...ranked.slice(3).filter(r=>r[metric]===ranked[2][metric]));
    return [view.rows.find(r=>r.brand===focal),...chosen];
  }
  function categories(data, view, metric='first_choice_credit_sum') {
    if (!view || view.status !== 'ready') return [];
    const focal=data.study.focal_brand, primary=data.study.competitors[0];
    const top=competitiveRows(data,view,metric),selected=new Set(top.map(r=>r.brand));
    const rows=top.map(r=>({label:r.brand,value:r[metric],color:r.brand===focal?'focal':r.brand===primary?'primary':'other'}));
    if(metric==='first_choice_credit_sum'){
      const other=view.rows.filter(r=>!selected.has(r.brand)).reduce((s,r)=>s+r.first_choice_credit_sum,0);
      if(other>0)rows.push({label:'Remaining named brands',value:other,color:'other'});
      rows.push({label:'No overall lead',value:view.no_lead_n,color:'neutral'});
    }
    return rows;
  }
  function unavailable(view) {
    return 'Unavailable: '+(view?.missing_questions?.length ? 'no complete coverage for '+view.missing_questions.join(', ') : 'required coverage is incomplete')+'. The result is unavailable, rather than zero.';
  }
  function chart(data,view,metric='first_choice_credit_sum') {
    if (!view || view.status!=='ready') return '<p class="notice">'+esc(unavailable(view))+'</p>';
    const rows=categories(data,view,metric);
    return '<div class="bars" role="img" aria-label="'+esc(rows.map(r=>r.label+': '+fmt(r.value)+' of '+view.n).join('; '))+'">'+rows.map(r=>'<div class="bar-row"><span>'+esc(r.label)+'</span><div class="track"><div class="fill '+r.color+'" style="width:'+100*r.value/view.n+'%"></div></div><b>'+fmt(r.value)+'<small> / '+view.n+'</small></b></div>').join('')+'</div>';
  }
  function table(headers,rows) {
    return '<div class="table-scroll"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
  }
  function evidenceRows(data,ids) {
    return table(['Engine / pass','Outcome','Context','Inspect'],ids.map(id=>{
      const o=data.observations[id];
      return [esc(engineName(o.engine)+' / '+o.repeat),esc(o.quality==='exclude'?'Excluded: '+o.quality_reason:o.leading_brands.join(' + ')||o.lead_status.replaceAll('_',' ')),esc(o.flags.join('; ')||'No visible flag'),'<button type="button" data-observation="'+esc(id)+'">Read answer</button>'];
    }));
  }
  const api={key,selectView,competitiveRows,categories,unavailable,chart};
  if (typeof module!=='undefined' && module.exports) module.exports=api;
  if (typeof document==='undefined') return;
  const data=JSON.parse(document.getElementById('report-data').textContent);
  const get=id=>document.getElementById(id);
  const main=data.study.layers[0];
  const state={};
  function renderQuestion(prefix) {
    const q=get(prefix+'-question').value, engine=get(prefix+'-engine').value, pop=get(prefix+'-population').value,metric=get(prefix+'-metric').value;
    const v=selectView(data,q,engine,pop);
    state[prefix]={question:q,engine,population:pop,metric,view:v};
    get(prefix+'-chart').innerHTML=chart(data,v,metric);
    const chosen=v?.status==='ready'?new Set(competitiveRows(data,v,metric).map(r=>r.brand)):new Set();
    const remaining=v?.status==='ready'?v.rows.filter(r=>!chosen.has(r.brand)&&(r[metric]>0||r.recommended_sum>0)).map(r=>r.brand):[];
    get(prefix+'-chart-note').textContent=(metric==='recommended_sum'?'Any recommendation: brands can overlap, so counts must not be added together.':'Overall first choice: explicit lead credits; conditional-only and unclear outcomes remain in no overall lead.')+' Shows the focal brand and the top three competitors on the selected measure, including positive ties. Zero lead does not mean zero recommendation.'+(remaining.length?' More alternatives appear in the detail table: '+remaining.join(', ')+'.':'');
    const p=data.study.questions.find(x=>x.id===q);
    get(prefix+'-prompt').textContent=data.study.context+'\n\n'+p.text;
    get(prefix+'-state').textContent=v?.status==='ready' ? [p.kind==='branded'?'Branded prompt':'Discovery prompt',metric==='recommended_sum'?'Any recommendation':'Overall first choice',pop==='baseline'?'Baseline':'Fixed globally matched context',engine==='all'?'All main engines':engineName(engine),v.n+' included answers','passes '+v.pass_labels.join(', '),v.flagged_n+' visible context flags',v.excluded_n+' excluded'].join(' · ') : unavailable(v);
    if (v?.status==='ready') {
      const rows=v.rows.filter(r=>r.mentioned_sum>0).sort((a,b)=>b.first_choice_credit_sum-a.first_choice_credit_sum||b.recommended_sum-a.recommended_sum);
      get(prefix+'-detail').innerHTML=table(['Brand','Named','Recommended','Lead credit','Substitute'],rows.map(r=>[esc(r.brand),fmt(r.mentioned_sum),fmt(r.recommended_sum),fmt(r.first_choice_credit_sum),fmt(r.substitute_sum)]))+'<p class="caption">Counts / credits out of '+v.n+'. Any recommendations are nonexclusive; conditional-only and unclear outcomes are retained.</p>'+evidenceRows(data,v.observation_ids);
    } else get(prefix+'-detail').innerHTML='<p>'+esc(unavailable(v))+'</p>';
    if (prefix==='stress') {
      const oo=(v?.status==='ready'?v.observation_ids:[]).map(id=>data.observations[id]);
      const conditional=oo.filter(o=>o.premium==='conditional').length;
      get('stress-assessment').textContent=oo.length?'Conditional premium assessments: '+conditional+' / '+oo.length+'. This records conditional support for paying more, separately from the overall purchase choice. It does not estimate switching.':'';
    }
  }
  function visibility() {
    const metric=get('visibility-metric').value,pop=get('visibility-population').value, selected=get('visibility-engine').value;
    const group=data.study.groups.find(g=>g.question_ids.every(qid=>data.study.questions.find(q=>q.id===qid).kind==='discovery'));
    const engines=selected==='all'?main.engines:[selected];
    const vv=engines.map(e=>data.views[key(main.id,pop,'group',group.id,e)]);
    if (vv.some(v=>!v||v.status!=='ready')) {
      get('visibility-chart').innerHTML='<p class="notice">'+esc(unavailable(vv.find(v=>!v||v.status!=='ready')))+'</p>';
      get('visibility-note').textContent='The same matching rule applies across engines. This selection is unavailable because the required questions are missing.';
      return;
    }
    get('visibility-chart').innerHTML=vv.map(v=>'<h4>'+esc(engineName(v.engine))+' · n='+v.n+'</h4><div class="bars" role="img" aria-label="'+esc(engineName(v.engine)+' '+get('visibility-metric').selectedOptions[0].text)+'">'+competitiveRows(data,v,metric).map(r=>{
      const brand=r.brand,percent=100*r[metric],color=brand===data.study.focal_brand?'focal':brand===data.study.competitors[0]?'primary':'other';
      return '<div class="bar-row"><span>'+esc(brand)+'</span><div class="track"><div class="fill '+color+'" style="width:'+percent+'%"></div></div><b>'+percent.toFixed(1)+'%</b></div>';
    }).join('')+'</div><details><summary>All named competitors and contributing answers</summary>'+table(['Brand',get('visibility-metric').selectedOptions[0].text],v.rows.filter(r=>r.mentioned_sum>0).sort((a,b)=>b[metric]-a[metric]).map(r=>[esc(r.brand),(100*r[metric]).toFixed(1)+'%']))+evidenceRows(data,v.observation_ids)+'</details>').join('');
    get('visibility-note').textContent=get('visibility-metric').selectedOptions[0].text+' · '+(pop==='baseline'?'Baseline':'Fixed matched context')+' · Discovery '+vv[0].questions.join(', ')+' · equal question weights. Focal brand and top three competitors per engine, including positive ties. Independent brand bars; do not sum mentions/recommendations.';
  }
  function repeatMatrix() {
    const qs=data.study.questions.filter(q=>q.kind==='discovery'&&main.question_ids.includes(q.id));
    get('repeat-matrix').innerHTML=table(['Shopper need',...main.engines.map(engineName)],qs.map(q=>[esc(data.labels[q.id]||q.text),...main.engines.map(e=>{
      const r=data.repeats.find(r=>r.engine===e&&r.question===q.id);
      const labels=r.outcomes.map(o=>o.brands.join(' + ')||o.status.replaceAll('_',' '));
      return '<span class="'+(r.stable?'stable':'variable')+'">'+esc(r.stable?'Stable':'Varies / incomplete')+'</span><br>'+labels.map((l,i)=>esc(r.outcomes[i].repeat+': '+l)).join('<br>');
    })]));
  }
  let matrixState={};
  function competitorMatrix() {
    const metric=get('matrix-metric').value,engine=get('matrix-engine').value,population=get('matrix-population').value,roster=get('matrix-roster').value;
    matrixState={metric,engine,population,roster};
    const brands=roster==='all'?data.competitor_matrix.brands:data.competitor_matrix.core_brands;
    const qs=data.competitor_matrix.questions;
    const headings='<thead><tr><th scope="col">Brand</th>'+qs.map(q=>'<th scope="col">'+esc(data.labels[q]||q)+'</th>').join('')+'</tr></thead>';
    const body=brands.map(brand=>'<tr><th scope="row">'+esc(brand)+'</th>'+qs.map(q=>{
      const v=selectView(data,q,engine,population);
      if(!v||v.status!=='ready')return '<td class="matrix-missing">Unavailable</td>';
      const r=v.rows.find(r=>r.brand===brand),value=r?r[metric]:0;
      return '<td><button type="button" class="matrix-value" style="--intensity:'+Math.round(22*value/v.n)+'%" data-matrix-question="'+esc(q)+'" data-matrix-brand="'+esc(brand)+'" aria-label="'+esc(brand+', '+(data.labels[q]||q)+', '+fmt(value)+' of '+v.n+', '+(metric==='recommended_sum'?'any recommendation':'overall first choice'))+'">'+fmt(value)+'<span> / '+v.n+'</span></button></td>';
    }).join('')+'</tr>').join('');
    get('matrix-table').innerHTML='<div class="table-scroll"><table class="matrix"><caption class="caption">Discovery questions only · each column has its own denominator</caption>'+headings+'<tbody>'+body+'</tbody></table></div>';
    get('matrix-note').textContent=(metric==='recommended_sum'?'Any recommendation (nonexclusive; do not sum across brands)':'Overall first-choice credits (conditional-only and unclear answers remain included)')+' · '+(engine==='all'?'All main engines':engineName(engine))+' · '+(population==='baseline'?'Baseline':'Fixed globally matched context; missing question coverage stays unavailable')+' · '+brands.length+' brands. Core roster stays fixed across filters.';
  }
  function openMatrixEvidence(question,brand,button) {
    const v=selectView(data,question,matrixState.engine,matrixState.population);
    if(!v||v.status!=='ready')return;
    const metric=matrixState.metric,r=v.rows.find(r=>r.brand===brand),value=r?r[metric]:0;
    if(!get('evidence-dialog').open)opener=button;
    get('evidence-title').textContent=brand+' · '+(data.labels[question]||question);
    get('evidence-body').innerHTML='<p>'+esc((metric==='recommended_sum'?'Any recommendation':'Overall first-choice credit')+': '+fmt(value)+' / '+v.n)+'</p><p class="caption">The list includes every answer in the denominator, including answers that do not recommend this brand.</p><p class="metadata">'+esc(v.denominator_ids.join(' · '))+'</p>'+evidenceRows(data,v.observation_ids);
    if(!get('evidence-dialog').open)get('evidence-dialog').showModal();get('close-evidence').focus();
  }
  function contrast() {
    const id=get('contrast-choice').value,pop=get('contrast-population').value;
    const definition=data.study.contrasts.find(c=>c.id===id);
    if (!definition) {get('contrast-result').innerHTML='<p>No reviewed hypothesis contrast is configured for this question set.</p>';return;}
    const rows=data.contrasts.filter(c=>c.layer===main.id&&c.contrast_id===id&&c.population===pop);
    get('contrast-result').innerHTML='<p class="eyebrow">'+esc(definition.analysis_status==='post_collection_exploratory'?'Post-collection exploratory':'Original hypothesis contrast')+'</p><p class="caption">'+esc(definition.comparison_questions.join(', ')+' minus '+definition.baseline_questions.join(', '))+' · '+esc(pop==='baseline'?'Baseline':'Fixed globally matched context')+' · focal-brand first-choice change in percentage points.</p>'+table(['Engine','First-choice change','Baseline n','Comparison n','Retained passes'],rows.map(r=>[esc(engineName(r.engine)),r.first_choice_rate_difference_pp===null?'Unavailable: no complete common passes':(r.first_choice_rate_difference_pp>0?'+':'')+r.first_choice_rate_difference_pp.toFixed(1)+' pp',esc(r.baseline_n),esc(r.comparison_n),esc(JSON.parse(r.retained_repeat_labels_json).join(', ')||'None')]))+'<p class="caption">One retained pass provides no repeat-variation estimate. A zero change may mean neither prompt chose the focal brand. It does not necessarily mean the brand retained its recommendation.</p>';
  }
  function supplement() {
    const oo=Object.values(data.observations).filter(o=>o.layer!==main.id&&o.quality==='include');
    get('supplement-table').innerHTML=oo.length?table(['Question / engine','Outcome','Context / quality','Evidence'],oo.map(o=>[esc((data.labels[o.question_id]||o.question_id)+' / '+engineName(o.engine)),esc(o.quality==='exclude'?'Excluded':o.leading_brands.join(' + ')||o.lead_status.replaceAll('_',' ')),esc(o.flags.join('; ')||(o.quality==='exclude'?o.quality_reason:'No visible authored flag; recorded session limits still apply')),'<button type="button" data-observation="'+esc(o.id)+'">Read answer</button>'])):'<p>No included supplemental answers.</p>';
  }
  function browse() {
    const engine=get('browse-engine').value,q=get('browse-question').value;
    const ids=Object.values(data.observations).filter(o=>o.quality==='include'&&(engine==='all'||o.engine===engine)&&(q==='all'||o.question_id===q)).map(o=>o.id);
    get('browse-results').innerHTML='<p class="caption">'+ids.length+' included answers.</p>'+evidenceRows(data,ids);
  }
  let opener=null;
  function openEvidence(id,button) {
    const o=data.observations[id];
    if (!o) return;
    if(!get('evidence-dialog').open)opener=button;
    get('evidence-title').textContent=engineName(o.engine)+' · '+(data.labels[o.question_id]||o.question_id)+' · pass '+o.repeat;
    get('evidence-body').innerHTML='<p class="metadata">'+esc(o.id+' · '+o.layer+' · '+o.quality+' · '+o.timestamp)+'</p><h3>Exact prompt</h3><p class="transcript">'+esc(o.prompt)+'</p><p class="metadata">'+esc('Model: '+o.model+' | Recorded mode: '+o.mode+' | Sign-in: '+o.sign_in)+'</p><p>'+esc('Context: '+(o.flags.join('; ')||'No visible flag; not proof of neutrality'))+'</p><details><summary>Capture-stage note (historical)</summary><p>'+esc(o.quality_reason)+'</p></details><h3>'+esc(o.quality==='exclude'?'Excluded partial capture':'Reviewed answer transcript')+'</h3><p class="caption">'+esc(o.quality==='exclude'?'Excluded defective capture; retained for audit, not included in rates.':'Product claims in this response have not been independently verified.')+'</p><div class="transcript">'+esc(o.transcript)+'</div><h3>Citation attachment status</h3><p>'+o.mapped_claims+' / '+o.selected_claims+' selected claims mapped. This covers selected claims, not every citation. The underlying claims have not been independently verified.</p><p><a href="'+esc(o.evidence_path)+'">Answer record, publication notes and hashes</a></p>';
    if(!get('evidence-dialog').open)get('evidence-dialog').showModal();
    get('close-evidence').focus();
  }
  get('close-evidence').addEventListener('click',()=>get('evidence-dialog').close());
  get('evidence-dialog').addEventListener('close',()=>{if(opener?.isConnected)opener.focus();});
  document.addEventListener('click',event=>{const b=event.target.closest('[data-observation]');if(b?.dataset.observation){openEvidence(b.dataset.observation,b);return;}const c=event.target.closest('[data-matrix-question]');if(c?.dataset.matrixQuestion)openMatrixEvidence(c.dataset.matrixQuestion,c.dataset.matrixBrand,c);});
  for (const prefix of ['needs','stress']) {
    for (const control of ['question','metric','engine','population']) get(prefix+'-'+control).addEventListener('change',()=>renderQuestion(prefix));
    get(prefix+'-export').addEventListener('click',()=>{
      const current=state[prefix];
      const blob=new Blob([JSON.stringify({study:data.study.study_id,wave:data.study.wave,source_fingerprint:data.source_fingerprint,filter_state:{question:current.question,engine:current.engine,population:current.population,metric:current.metric},view:current.view},null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob), a=document.createElement('a');a.href=url;a.download=data.study.study_id+'-'+prefix+'-view.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    renderQuestion(prefix);
  }
  for (const id of ['visibility-metric','visibility-engine','visibility-population']) get(id).addEventListener('change',visibility);
  for (const id of ['contrast-choice','contrast-population']) get(id).addEventListener('change',contrast);
  for (const id of ['browse-engine','browse-question']) get(id).addEventListener('change',browse);
  for (const id of ['matrix-metric','matrix-engine','matrix-population','matrix-roster'])get(id).addEventListener('change',competitorMatrix);
  visibility();competitorMatrix();repeatMatrix();contrast();supplement();browse();
})();
