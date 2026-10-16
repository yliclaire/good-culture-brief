// Exercises the real monitoring script in a DOM model; not visual browser QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const release=path.resolve(process.argv[2]);
const demo=JSON.parse(fs.readFileSync(path.join(release,'data/monitoring_demo.json'),'utf8'));
const html=fs.readFileSync(path.join(release,'index.html'),'utf8');
const embedded=JSON.parse(html.match(/<script type="application\/json" id="monitor-data">([\s\S]*?)<\/script>/)[1]);
assert.deepStrictEqual(embedded,demo);
const choice={value:'unchanged',addEventListener:(type,fn)=>choice.change=fn};
const result={children:[],replaceChildren(){this.children=[];},appendChild(child){this.children.push(child);}};
const nodes={'monitor-data':{textContent:JSON.stringify(demo)},'monitor-case':choice,'monitor-result':result};
const document={getElementById:id=>nodes[id],createElement:()=>({textContent:''})};
vm.runInNewContext(fs.readFileSync(path.join(release,'assets/monitoring.js'),'utf8'),{document});
assert(result.children.map(p=>p.textContent).join(' ').includes('NO_ALERT'));
for(const [key,entry] of Object.entries(demo.cases)){
 choice.value=key;choice.change();
 const text=result.children.map(p=>p.textContent).join(' ');
 assert(text.includes('Observed baseline: 12 / 12'));
 assert(text.includes('Synthetic next wave:'));
 assert(text.includes(entry.result.message));
 if(key==='decline')assert(text.includes('-25 percentage points · REVIEW'));
 if(key==='model_change'){assert(text.includes('Change withheld · HOLD'));assert(!text.includes('-25 percentage points'));}
}
console.log(JSON.stringify({syntheticCases:3,metadataHold:true,verification:'DOM model; visual QA pending'}));
