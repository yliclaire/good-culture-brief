// Reading-view routing checked with a DOM model; layout and scrolling need browser QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..'),release=path.resolve(process.argv[2]);
const data=JSON.parse(fs.readFileSync(path.join(release,'data/report_data.json'),'utf8'));
const html=fs.readFileSync(path.join(release,'index.html'),'utf8');
class El{
 constructor(id,dataset={}){this.id=id;this.dataset=dataset;this.attributes={};this.handlers={};this.hidden=false;this.isConnected=true;this.textContent='';}
 addEventListener(type,fn){(this.handlers[type]??=[]).push(fn);}
 dispatchEvent(event){for(const fn of this.handlers[event.type]||[])fn(event);}
 setAttribute(key,value){this.attributes[key]=value;}
 getAttribute(key){return this.attributes[key];}
 removeAttribute(key){delete this.attributes[key];}
 focus(){this.focused=true;}
 scrollIntoView(){this.scrolled=true;}
 closest(){return this.owner||null;}
}
const nodes={};
for(const m of html.matchAll(/\bid="([^"]+)"/g))nodes[m[1]]=new El(m[1]);
const panes=['brief','explore','methodology'].map(v=>Object.assign(nodes['panel-'+v],{dataset:{panel:v}}));
const buttons=['brief','explore','methodology'].map(v=>Object.assign(nodes['view-button-'+v],{dataset:{view:v}}));
for(const id of ['category-map','needs','competitors','stress','durability','robustness'])nodes[id].owner=panes[1];
for(const id of ['methods','reuse'])nodes[id].owner=panes[2];
nodes['methods'].parentElement={tagName:'DETAILS',open:false};
const links=data.narrative.presentation.chapters.map((c,i)=>{nodes[c.id].owner=panes[0];const l=new El('chapter-'+i,{chapterLink:String(i+1)});l.textContent=String(i+1)+' '+c.label;return l;});
const events={},docEvents={};let observer;
const window={location:{hash:''},history:{replaceState:(a,b,hash)=>window.location.hash=hash},addEventListener:(type,fn)=>events[type]=fn,
 IntersectionObserver:class{constructor(callback){observer=callback;}observe(){}}};
const document={getElementById:id=>nodes[id]||null,addEventListener:(type,fn)=>docEvents[type]=fn,
 querySelectorAll:selector=>({'[data-view]':buttons,'[data-panel]':panes,'[data-chapter-link]':links,'[data-chapter]':data.narrative.presentation.chapters.map(c=>nodes[c.id])}[selector]||[])};
vm.runInNewContext(fs.readFileSync(path.join(root,'report/navigation.js'),'utf8'),{document,window,Event:class{constructor(type){this.type=type;}}});
assert(!panes[0].hidden&&panes[1].hidden&&panes[2].hidden);
for(let i=0;i<buttons.length;i++){
 buttons[i].dispatchEvent({type:'click'});
 panes.forEach((p,k)=>assert.strictEqual(p.hidden,k!==i));
 assert.strictEqual(buttons[i].attributes['aria-pressed'],'true');
 assert(panes[i].focused);
}
buttons[0].dispatchEvent({type:'click'});
nodes['story-competition'].dataset.chapter='3';observer([{isIntersecting:true,target:nodes['story-competition'],boundingClientRect:{top:0}}]);
assert.strictEqual(links[2].attributes['aria-current'],'step');assert(nodes['reading-position'].textContent.includes('Chapter 3 of 5'));
assert.strictEqual(nodes['methods'].parentElement.open,false);
window.location.hash='#methods';events.hashchange();assert(!panes[2].hidden&&panes[0].hidden);assert.strictEqual(nodes['methods'].parentElement.open,true);
let changed=false;nodes['needs-question'].addEventListener('change',()=>changed=true);
const link=new El('deep-link',{route:'explore',presetQuestion:'Q6'});link.attributes.href='#needs';link.closest=()=>link;
docEvents.click({target:link,preventDefault:()=>{}});
assert(!panes[1].hidden);assert.strictEqual(nodes['needs-question'].value,'Q6');assert.strictEqual(nodes['needs-population'].value,'baseline');assert.strictEqual(nodes['needs-engine'].value,'all');assert(changed);
window.location.hash='#category-map';events.hashchange();assert(!panes[1].hidden);
for(const q of data.competitor_matrix.questions){link.dataset.presetQuestion=q;docEvents.click({target:link,preventDefault:()=>{}});assert.strictEqual(nodes['needs-question'].value,q);}
window.location.hash='#story-competition';events.hashchange();assert(!panes[0].hidden);
console.log(JSON.stringify({readingViews:3,chapters:5,activeChapterTracking:true,deepLinks:true,questionPresets:true,collapsedMethodDeepLinks:true,atlasQuestionRoutes:9,verification:'DOM model; real browser and print QA pending'}));
