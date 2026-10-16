(function(){
 'use strict';
 const source=document.getElementById('monitor-data');
 if(!source)return;
 const demo=JSON.parse(source.textContent), choice=document.getElementById('monitor-case'), result=document.getElementById('monitor-result');
 function render(){
  const selected=demo.cases[choice.value], baseline=demo.baseline, future=selected.future, assessment=selected.result;
  const delta=assessment.delta_pp===null?'Change withheld':(assessment.delta_pp>0?'+':'')+assessment.delta_pp+' percentage points';
  result.replaceChildren();
  for(const text of [baseline.focal_brand+' · '+baseline.question_label,'Observed baseline: '+baseline.first_choice_credit+' / '+baseline.n+' overall first-choice credit.','Synthetic next wave: '+future.first_choice_credit+' / '+future.n+'.',delta+' · '+assessment.status.toUpperCase(),assessment.message]){
   const p=document.createElement('p');p.textContent=text;result.appendChild(p);
  }
 }
 choice.addEventListener('change',render);render();
})();
