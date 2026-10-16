(function(){
  'use strict';
  const get=id=>document.getElementById(id);
  if(!get('panel-brief'))return;
  const buttons=Array.from(document.querySelectorAll('[data-view]'));
  const panes=Array.from(document.querySelectorAll('[data-panel]'));
  const chapterLinks=Array.from(document.querySelectorAll('[data-chapter-link]'));
  let current='brief';
  function chapter(number){
    chapterLinks.forEach(link=>{if(link.dataset.chapterLink===String(number))link.setAttribute('aria-current','step');else link.removeAttribute('aria-current');});
    const link=chapterLinks.find(l=>l.dataset.chapterLink===String(number));
    get('reading-position').textContent='Chapter '+number+' of '+chapterLinks.length+' · '+(link?link.textContent.trim().replace(/^\d+\s*/, ''):'Investment brief');
  }
  function show(view,target,move=true){
    if(!panes.some(p=>p.dataset.panel===view))return;
    current=view;
    panes.forEach(p=>p.hidden=p.dataset.panel!==view);
    buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
    get('chapter-navigation').hidden=view!=='brief';get('reading-position').hidden=view!=='brief';
    if(view==='brief'&&!target)chapter(1);
    const destination=target?get(target):get('panel-'+view);
    for(let node=destination;node;node=node.parentElement){if(node.tagName==='DETAILS')node.open=true;}
    if(move&&destination){destination.scrollIntoView?.({block:'start',behavior:'auto'});get('panel-'+view).focus({preventScroll:true});}
  }
  function hashRoute(move=true){
    let id;try{id=decodeURIComponent(window.location.hash.slice(1));}catch{return;}
    const target=get(id);const pane=target?.closest('[data-panel]');
    if(pane)show(pane.dataset.panel,id,move);
  }
  function setHash(id){try{window.history.replaceState(null,'','#'+id);}catch{window.location.hash='#'+id;}}
  buttons.forEach(button=>button.addEventListener('click',()=>{const view=button.dataset.view;show(view,null);setHash(view==='brief'?'view':view==='explore'?'category-map':'reuse');}));
  chapterLinks.forEach(link=>link.addEventListener('click',()=>chapter(link.dataset.chapterLink)));
  document.addEventListener('click',event=>{
    const link=event.target.closest('[data-route]');
    if(!link)return;
    event.preventDefault();
    const id=link.getAttribute('href').slice(1),q=link.dataset.presetQuestion;
    if(q&&['needs','stress'].includes(id)){
      get(id+'-question').value=q;get(id+'-engine').value='all';get(id+'-population').value='baseline';get(id+'-metric').value='first_choice_credit_sum';
      get(id+'-question').dispatchEvent(new Event('change'));
    }
    show(link.dataset.route,id);
    setHash(id);
  });
  window.addEventListener('hashchange',()=>hashRoute());
  show('brief',null,false);hashRoute(false);
  if('IntersectionObserver' in window){
    const observer=new window.IntersectionObserver(entries=>{
      if(current!=='brief')return;
      const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top);
      if(visible.length)chapter(visible[0].target.dataset.chapter);
    },{rootMargin:'-18% 0px -55% 0px',threshold:0});
    document.querySelectorAll('[data-chapter]').forEach(section=>observer.observe(section));
  }
})();
