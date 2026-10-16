"""Short investment story with the complete benchmark one level deeper."""
import re
from .export import view_key
from .render import esc,fmt,table


def compose(page,data,print_mode=False):
    n=data['narrative'];profile=n.get('presentation')
    if not profile:return page
    cfg=data['study'];main=cfg['layers'][0]['id'];focal=cfg['focal_brand']
    blocks={m[1]:m[0] for m in re.finditer(r'<section id="([^"]+)">[\s\S]*?</section>',page)}
    # The hero has a class in addition to its ID.
    hero=re.search(r'<section id="view" class="hero">[\s\S]*?</section>',page)[0]
    def v(q):return data['views'][view_key(main,'baseline','question',q,'all')]
    def row(view,brand):return next(r for r in view['rows'] if r['brand']==brand)
    def lead(q,brand):return row(v(q),brand)['first_choice_credit_sum']
    def jump(target,label,q=None):
        return '<a class="explore-link" href="#'+esc(target)+'" data-route="explore"'+(' data-preset-question="'+esc(q)+'"' if q else '')+'>'+esc(label)+' <span aria-hidden="true">↗</span></a>'
    def next_link(target,label):return '<a class="next-chapter" href="#'+target+'">Next: '+esc(label)+' <span aria-hidden="true">↓</span></a>'
    from .atlas import atlas
    from .sources import render_inventory
    from .decisions import challenge, scenario, priorities, monitoring_guide
    sections=profile['chapters']
    hero=hero.replace('<section id="view" class="hero">','<section id="view" class="hero story-chapter" data-chapter="1">')
    if n.get('decision_support'):
        ds=n['decision_support']
        hero=hero.replace('<p class="deck">','<p class="investment-status">'+esc(ds['status'])+'</p><p class="deck">',1)
        hero=hero.replace('<p class="sample">','<p class="investment-action">'+esc(ds['decision'])+'</p><p class="sample">',1)
    hero=hero.replace('<div class="proof-grid">','<div class="reading-guide"><span>Five chapters</span><span>Evidence and investment questions</span></div><div class="proof-grid">')
    for s in n['hero_stats']:
        q=n['metric_bindings'][s['numerator']]['view'].split('|')[3]
        target='stress' if next(qr['kind'] for qr in cfg['questions'] if qr['id']==q)=='branded' else 'needs'
        hero=hero.replace('<a href="#needs">Explore the recorded answers</a>',jump(target,'View the supporting answers',q),1)
    hero=hero.replace('</section>',next_link('story-positioning',sections[1]['label'])+'</section>')
    strength=[]
    for q in profile['positioning_questions']:
        view=v(q);value=lead(q,focal)
        strength.append('<div class="signal-row"><div><span>'+esc(data['labels'][q])+'</span><strong>'+fmt(value)+'<small> / '+str(view['n'])+'</small></strong></div><div class="signal-track"><div style="width:'+str(100*value/view['n'])+'%"></div></div><p class="caption">'+esc(focal)+' overall first-choice credit · '+str(view['no_lead_n'])+' no-overall-lead outcomes</p></div>')
    f=n['findings'][0]
    positioning='<section id="story-positioning" class="story-chapter" data-chapter="2"><div class="section-heading"><span>02 / POSITIONING</span><h2>'+esc(n['needs_title'])+'</h2></div><div class="story-split"><div class="signal-chart" role="img" aria-label="'+esc(focal+' first-choice counts by selected shopper need')+'">'+'<p class="exhibit-caption">Exhibit 1 · '+esc(focal)+' overall first-choice credit</p>'+''.join(strength)+'</div><aside class="story-interpretation"><p class="eyebrow">'+esc(f['implication_label'])+'</p><p>'+esc(f['implication'])+'</p>'+jump('needs','Compare all shopper needs',profile['positioning_questions'][0])+'</aside></div><p class="caption">Baseline main sample. Each row is a separate discovery prompt, with four engines and three passes. The no-overall-lead category includes conditional and unclear outcomes.</p>'+challenge(data,'F1')+next_link('story-competition',sections[2]['label'])+'</section>'
    qs=profile['preview_questions'];brands=[focal]
    positives={r['brand'] for q in qs for r in v(q)['rows'] if r['first_choice_credit_sum']>0}
    brands+=sorted(positives-{focal})
    preview=table(['Overall first choice']+[data['labels'][q] for q in qs],[[esc(brand)]+[fmt(lead(q,brand))+' / '+str(v(q)['n']) for q in qs] for brand in brands])
    gaps=[]
    for qid in qs:
        cv=v(qid)
        rivals=[r for r in cv['rows'] if r['brand']!=focal]
        best=max((r['first_choice_credit_sum'] for r in rivals),default=0)
        winners=[r['brand'] for r in rivals if r['first_choice_credit_sum']==best and best>0]
        if best>lead(qid,focal):gaps.append((best-lead(qid,focal),qid,best,winners))
    annotation=''
    if gaps:
        _,qid,best,winners=max(gaps,key=lambda item:item[0])
        annotation='<p class="exhibit-annotation"><span>'+esc(data['labels'][qid])+'</span> '+esc(' / '.join(winners))+' leads '+fmt(best)+' / '+str(v(qid)['n'])+' answers; '+esc(focal)+' leads '+fmt(lead(qid,focal))+' / '+str(v(qid)['n'])+'. '+esc(n['findings'][1]['implication'])+'</p>'
    competition='<section id="story-competition" class="story-chapter" data-chapter="3"><div class="section-heading"><span>03 / COMPETITORS</span><h2>'+esc(profile['competition_title'])+'</h2></div><p>'+esc(profile['competition_intro'])+'</p><p class="exhibit-caption">Exhibit 2 · Different shopper needs, different leaders</p><div class="compact-comparison">'+preview+'</div>'+annotation+'<p class="caption">Selected discovery questions; baseline, all main engines. Brands shown receive overall first-choice credit in at least one selected question. Conditional/no-lead cases remain in each denominator and are shown in the explorer. These counts do not estimate market share.</p>'+jump('competitors','Explore the full competitor matrix')+challenge(data,'F2')+next_link('story-durability',sections[3]['label'])+'</section>'
    q=profile['pressure_question'];view=v(q);brand=cfg['competitors'][0] if profile['pressure_brand']=='$primary' else profile['pressure_brand'];value=lead(q,brand)
    quote=next(e for e in data['selections'] if e['evidence_id']==profile['quote_id']);obs=data['observations'][quote['observation_id']]
    quote_html='<figure class="story-quote"><blockquote>'+esc(quote['excerpt'])+'</blockquote><figcaption>'+esc(obs['engine']+' · '+data['labels'][obs['question_id']]+' · pass '+obs['repeat'])+'<br>Engine response; product claims have not been independently checked.</figcaption><a href="'+esc(obs['evidence_path'])+'">Read the complete answer</a></figure>'
    durability='<section id="story-durability" class="story-chapter" data-chapter="4"><div class="section-heading"><span>04 / PREMIUM & DURABILITY</span><h2>'+esc(profile['pressure_title'])+'</h2></div><p class="exhibit-caption">Exhibit 3 · Replacement under an assumed stockout</p><div class="story-split"><div><p class="eyebrow">'+esc(data['labels'][q])+' · Branded prompt</p><div class="statement-number">'+fmt(value)+'<span> / '+str(view['n'])+'</span></div><p>'+esc(brand)+' is the overall first choice when the prompt says the usual brand is unavailable.</p><p class="caption">Baseline main sample. '+str(view['no_lead_n'])+' no-overall-lead outcome. Branded answers are separate from discovery.</p>'+jump('stress','View premium, stockout and switching answers',q)+'</div>'+quote_html+'</div><div class="durability-implication"><p class="eyebrow">Could a larger competitor challenge it?</p><p>'+esc(n['durability_close'])+'</p>'+jump('durability','Review the evidence and competitive assumptions')+'</div><p class="caption">'+esc(profile['premium_note'])+'</p>'+challenge(data,'F3')+scenario(data)+next_link('story-diligence',sections[4]['label'])+'</section>'
    agenda=''.join('<article><span class="agenda-number">'+str(i+1).zfill(2)+'</span><h3>'+esc(item['title'])+'</h3><p>'+esc(n['findings'][item['finding_index']]['question'])+'</p><p class="caption">Evidence to request: '+esc(item['evidence'])+'</p></article>' for i,item in enumerate(profile['agenda']))
    if n.get('decision_support'):agenda=priorities(data)
    limits='<p class="story-limits"><strong>Confidence and limits.</strong> '+esc(profile['limits'])+' <a href="#robustness" data-route="explore">Check repeat consistency and context</a> · <a href="#methods" data-route="methodology">Read the methods</a></p>'
    diligence='<section id="story-diligence" class="story-chapter" data-chapter="5"><div class="section-heading"><span>05 / INVESTMENT DILIGENCE</span><h2>'+esc(profile['diligence_title'])+'</h2></div><div class="agenda-grid">'+agenda+'</div><p class="pullquote">'+esc(n['closing'])+'</p>'+challenge(data,'F4')+limits+'<div class="story-destinations">'+jump('competitors','Review the detailed results')+'<a href="#reuse" data-route="methodology">Open the workflow guide ↗</a></div></section>'
    switcher='<div class="reader-shell"><div class="reader-controls" role="group" aria-label="Choose reading view">'+''.join('<button type="button" id="view-button-'+id+'" data-view="'+id+'" aria-controls="panel-'+id+'" aria-pressed="'+('true' if id=='brief' else 'false')+'">'+label+'</button>' for id,label in [('brief','Investment brief'),('explore','Explore the benchmark'),('methodology','Methodology & reuse')])+'</div><nav id="chapter-navigation" class="chapter-navigation" aria-label="Investment brief chapters">'+''.join('<a href="#'+c['id']+'" data-chapter-link="'+str(i+1)+'"'+(' aria-current="step"' if i==0 else '')+'><span>'+str(i+1).zfill(2)+'</span> '+esc(c['label'])+'</a>' for i,c in enumerate(sections))+'</nav><p id="reading-position" class="reading-position" aria-live="polite">Chapter 1 of 5 · '+esc(sections[0]['label'])+'</p></div>'
    explorer_intro='<div class="panel-intro"><p class="eyebrow">EXPLORE THE BENCHMARK</p><h2>Compare brands by shopper need.</h2><p>Compare brand recommendations across engines, check context sensitivity, and read the answers behind each result.</p><nav aria-label="Explorer sections"><a href="#category-map">Shopper-needs map</a><a href="#needs">Detailed comparison</a><a href="#competitors">Competitor matrix</a><a href="#stress">Premium stress</a><a href="#durability">Durability</a><a href="#robustness">Robustness</a></nav></div>'
    methods_intro='<div class="panel-intro"><h2>Running the study again</h2><p>This report uses saved browser answers and reviewed coding. You can rebuild it without collecting anything new. For another brand or quarter, collect answers with the collection workflow, review them, then use the build workflow for the brief.</p></div>'
    workflow='<section id="reuse" class="workflow-guide"><div class="workflow-routes"><article><h3>Rebuild the '+esc(focal)+' report</h3><ol><li>Open <strong>Actions → Build investment brief → Run workflow</strong> in the GitHub repository.</li><li>Choose <code>build-brief</code>. Select this study’s ID from the <a href="code/reviewed_studies/registry.json">reviewed-study registry</a>.</li><li>Download the completed run’s artifact, unzip it, then unzip <code>run.zip</code> and open <code>index.html</code>.</li></ol><p class="caption">The workflow recalculates the metrics and rebuilds the charts, brief and evidence pages from the saved inputs. No API keys are needed.</p></article><article><h3>Start another study</h3><ol><li>Open <strong>Collect engine answers → Run workflow</strong>. Choose the category, brand and competitors. Leave the questions blank to use the category’s defaults, or enter your own. Run <code>preview</code> to check the questions before collecting.</li><li>Add your API keys as repository secrets and choose model IDs. Run <code>collect</code> after confirming that API charges may apply.</li><li>Review the answers, coding and conclusions. Save and register the approved package in the repository, then open <strong>Build investment brief</strong> and run <code>build-brief</code> with the new study’s ID.</li></ol><p class="caption">Review is a separate step. Downloaded files do not sync back to GitHub; the approved inputs must be added to the repository before building.</p></article></div><div class="workflow-output"><h3>What you get back</h3><p>Each brief includes the interactive report, a print version, captured answers, chart tables and the code and configuration used to build it. Unzip the package and open it locally; a public website is optional.</p></div><details class="workflow-setup"><summary>Setting up the GitHub repository</summary><p>Create a private repository and put the contents of <code>code/</code> at its root. Keep both files under <code>.github/workflows/</code> and commit to the default branch. Actions will list Collect engine answers and Build investment brief.</p><p>Only new collection needs API keys. The <a href="code/README.md">setup guide</a> lists the secret names, model settings, request limits and input formats.</p></details><details><summary>What needs to change next quarter?</summary><p>Keep the questions, engine settings and coding rules comparable. Collect a new wave, record any changes in model or collection mode, and review the new conclusions. Keep browser and API results separate.</p><p>For a different category, also change the shopper questions, attributes and competitor roster. The collection code, checks, calculations and report template carry over. The <a href="configuration/birkenstock.example.json">Birkenstock profile</a> shows how the category configuration changes; it has no collected answers.</p><p><a href="configuration/study.json">Current study configuration</a> · <a href="code/README.md">Full operating guide</a></p></details><p class="caption workflow-status">The workflow has been tested locally. A GitHub-hosted run, live API pilot and browser/print visual checks are still to do.</p></section>'
    host=n.get('workflow_host')
    if host:
        workflow=workflow.replace('The workflow has been tested locally. A GitHub-hosted run, live API pilot and browser/print visual checks are still to do.', 'The implementation and both workflows are available in this public submission repository. The public Good Culture build and no-key collection preview have passed hosted checks. Live API collection remains unpiloted. <a href="'+esc(host.get('validated_run_url',host['workflow_url']))+'">'+('View the successful run' if host.get('validated_run_url') else 'Open the build workflow')+'</a>.')
        workflow=workflow.replace('<div class="workflow-routes">','<p class="hosted-workflow"><a href="'+esc(host['workflow_url'])+'">Build investment brief on GitHub</a> · <a href="'+esc(host.get('collection_workflow_url',host['workflow_url']))+'">Collect engine answers</a> · <a href="'+esc(host['repository_url'])+'">Repository</a><br><span class="caption">The code is public. Reading or downloading it needs no account; running Actions requires write access, or your own fork with Actions enabled. The downloaded brief also works locally.</span></p><div class="workflow-routes">',1)
    methods_evidence=blocks['methods'].replace('<p class="notice">',render_inventory(data)+'<p class="notice">',1)
    methodology='<details id="study-details" class="methodology-details"><summary>Study definitions, limitations and evidence</summary>'+methods_evidence+'<h3>Further investment evidence</h3>'+table(['Evidence wanted next','Question it could resolve'],[[esc(c) for c in row] for row in n['future']])+'</details>'
    brief='<div id="panel-brief" class="view-pane" data-panel="brief" aria-labelledby="view-button-brief" tabindex="-1">'+hero+positioning+competition+durability+diligence+'</div>'
    explore='<div id="panel-explore" class="view-pane" data-panel="explore" aria-labelledby="view-button-explore" tabindex="-1">'+explorer_intro+atlas(data)+''.join(blocks[id] for id in ['needs','competitors','stress','durability','robustness'])+'</div>'
    methods='<div id="panel-methodology" class="view-pane" data-panel="methodology" aria-labelledby="view-button-methodology" tabindex="-1">'+methods_intro+workflow+monitoring_guide(data)+'<p class="assignment-link"><a href="methodology/ASSIGNMENT_REVIEW.md">Assignment coverage and remaining limitations</a></p>'+methodology+'</div>'
    old_nav=re.search(r'<nav aria-label="Report sections">[\s\S]*?</nav>',page)[0]
    page=page.replace(old_nav,switcher)
    start=page.index('<main id="main">')+len('<main id="main">');end=page.index('<section class="print-summary">')
    page=page[:start]+brief+explore+methods+page[end:]
    page=page.replace('<script src="assets/report.js"></script>','<script src="assets/report.js"></script><script src="assets/navigation.js"></script><script src="assets/monitoring.js"></script>')
    return page
