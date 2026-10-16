"""Build HTML from checked report data. No external runtime dependencies."""
import html
import json
import re
from .export import view_key
from .competition import competitive_rows

def esc(value):
    return html.escape(str(value),quote=True)


def fmt(value):
    return str(int(value)) if float(value).is_integer() else f'{value:.1f}'


def tokens(text,data):
    def replace(match):
        name=match[1]
        if name not in data['numbers']:
            raise ValueError('Unbound narrative number: '+name)
        return '<strong data-metric="'+esc(name)+'">'+fmt(data['numbers'][name])+'</strong>'
    return re.sub(r'\{\{([a-zA-Z0-9_]+)\}\}',replace,esc(text))


def table(headers,rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in r)+'</tr>' for r in rows)+'</tbody></table></div>'


def engine_name(engine):
    return {'chatgpt':'ChatGPT','claude':'Claude','gemini':'Gemini','perplexity':'Perplexity','google_ai_mode':'Google AI Mode','copilot_search':'Copilot Search','anthropic':'Claude API','openai':'OpenAI API'}.get(engine,engine.replace('_',' ').title())


def option(value,label,selected=False):
    return '<option value="'+esc(value)+'"'+(' selected' if selected else '')+'>'+esc(label)+'</option>'


def static_chart(data,qid,layer=None):
    layer=layer or data['study']['layers'][0]['id']
    v=data['views'][view_key(layer,'baseline','question',qid,'all')]
    if v['status']!='ready':
        return '<p class="notice">Unavailable: '+esc(', '.join(v['missing_questions']) or v['status'])+'</p>'
    focal=data['study']['focal_brand']; primary=data['study']['competitors'][0]
    top=competitive_rows(data,v)
    displayed={r['brand'] for r in top}
    vals=[(r['brand'],r['first_choice_credit_sum'],'focal' if r['brand']==focal else 'primary' if r['brand']==primary else 'other') for r in top]
    other=sum(r['first_choice_credit_sum'] for r in v['rows'] if r['brand'] not in displayed)
    if other>0:vals.append(('Remaining named brands',other,'other'))
    vals.append(('No overall lead',v['no_lead_n'],'neutral'))
    return '<div class="bars" role="img" aria-label="'+esc('; '.join(label+': '+fmt(value)+' of '+str(v['n']) for label,value,color in vals))+'">'+''.join('<div class="bar-row"><span>'+esc(label)+'</span><div class="track"><div class="fill '+color+'" style="width:'+str(100*value/v['n'])+'%"></div></div><b>'+fmt(value)+'<small> / '+str(v['n'])+'</small></b></div>' for label,value,color in vals)+'</div>'


def finding(data,index):
    f=data['narrative']['findings'][index]
    return '<div class="finding"><p>'+tokens(f['body'],data)+'</p><div class="implication"><span class="eyebrow">'+esc(f['implication_label'])+'</span><p>'+esc(f['implication'])+'</p><p class="question">'+esc(f['question'])+'</p></div></div>'


def static_matrix(data):
    cfg=data['study']; main=cfg['layers'][0]['id']; roster=data['competitor_matrix']
    rows=[]
    for brand in roster['core_brands']:
        cells=[esc(brand)]
        for q in roster['questions']:
            v=data['views'][view_key(main,'baseline','question',q,'all')]
            value=next((r['first_choice_credit_sum'] for r in v['rows'] if r['brand']==brand),0) if v['status']=='ready' else None
            cells.append('Unavailable' if value is None else fmt(value)+' / '+str(v['n']))
        rows.append(cells)
    return table(['Brand']+[data['labels'].get(q,q) for q in roster['questions']],rows)


def selectors(data,prefix,branded=False):
    main=data['study']['layers'][0]
    questions=[q for q in data['study']['questions'] if q['id'] in main['question_ids'] and q['kind']==('branded' if branded else 'discovery')]
    default=data['default_branded_question'] if branded else data['default_question']
    return '<div class="controls"><label>Shopper question<select id="'+prefix+'-question">'+''.join(option(q['id'],data['labels'].get(q['id'],q['text']),q['id']==default) for q in questions)+'</select></label><label>Measure<select id="'+prefix+'-metric">'+option('first_choice_credit_sum','Overall first choice')+option('recommended_sum','Any recommendation')+'</select></label><label>Engine<select id="'+prefix+'-engine">'+option('all','All main engines')+''.join(option(e,engine_name(e)) for e in main['engines'])+'</select></label><label>Population<select id="'+prefix+'-population">'+option('baseline','Baseline: all usable answers')+option('matched_context','Matched: no visible context flags')+'</select></label></div>'


def render_long(data,print_mode=False):
    cfg=data['study']; n=data['narrative']; main=cfg['layers'][0]
    esc_title=esc(cfg['focal_brand'])+' through AI answer engines'
    selected_cards=''.join('<article class="proof"><div class="eyebrow">'+esc(s['label'])+'</div><div class="proof-value">'+fmt(data['numbers'][s['numerator']])+'<span> / '+fmt(data['numbers'][s['denominator']])+'</span></div><p>'+esc(s['description'])+'</p><a href="#needs">Explore the recorded answers</a></article>' for s in n['hero_stats'])
    durability=table(['Position','Captured evidence','Competitive inference','What to investigate'],[[esc(c) for c in row] for row in n['durability']])
    tools=table(['Tool / method','Contribution','Why / trade-off'],[[esc(c) for c in row] for row in n['tools']])
    future=table(['Evidence wanted next','Question it could resolve'],[[esc(c) for c in row] for row in n['future']])
    counts=data['counts']
    surface='browser' if 'browser' in cfg.get('collection_protocol',{}).get('mode','') else 'API'
    coverage=table(['Layer','Engine','Included answers','Mapped / selected claims'],[[esc(r['layer']),esc(engine_name(r['engine'])),esc(r['included_answers_n']),esc(r['mapped_selected_claims_n'])+' / '+esc(r['selected_claims_n'])] for r in data['citations']])
    vi=[]
    discovery=next(g for g in cfg['groups'] if all(next(q for q in cfg['questions'] if q['id']==qid)['kind']=='discovery' for qid in g['question_ids']))
    for e in main['engines']:
        v=data['views'][view_key(main['id'],'baseline','group',discovery['id'],e)]
        r=next(r for r in v['rows'] if r['brand']==cfg['focal_brand'])
        vi.append([esc(engine_name(e)),str(v['n'])]+[f'{100*r[k]:.1f}%' for k in ['mention_rate','recommendation_rate','first_mention_rate','first_choice_rate']])
    overview=table(['Engine','Answers','Named','Recommended','First mention','Overall first choice'],vi)
    qmap={q['id']:q for q in cfg['questions']}
    print_charts=''.join('<article class="print-finding"><h3>'+esc(data['labels'].get(qid,qid))+'</h3><p class="caption">'+esc(qmap[qid]['kind'].title())+' prompt · '+esc(cfg['context']+' '+qmap[qid]['text'])+'</p>'+static_chart(data,qid)+'</article>' for qid in n['print_questions'])
    excerpts=''.join('<details class="excerpt"><summary>'+esc(e['evidence_id']+' · '+engine_name(data['observations'][e['observation_id']]['engine'])+' · '+data['labels'].get(data['observations'][e['observation_id']]['question_id'],''))+'</summary><blockquote>'+esc(e['excerpt'])+'</blockquote><p>'+esc(e['role'].replace('_',' '))+' · Engine response; factual claims have not been independently checked.</p><a href="'+esc(data['observations'][e['observation_id']]['evidence_path'])+'">Complete answer and source record</a></details>' for e in data['selections'])
    dialogs='''<dialog id="evidence-dialog" aria-labelledby="evidence-title"><div class="dialog-head"><h2 id="evidence-title">Captured answer</h2><button type="button" id="close-evidence">Close</button></div><div id="evidence-body"></div></dialog>'''
    data_json=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    subtitle=esc(n['subtitle'])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>{esc_title}</title><link rel="stylesheet" href="assets/report.css"></head>
<body class="{'print-document' if print_mode else ''}"><a class="skip" href="#main">Skip to report</a><header class="masthead"><a class="brand" href="#main">ANSWER ENGINE / INVESTMENT STUDY</a><div>{esc(cfg['wave'])} · {esc(cfg['market'])}</div><a href="{'index.html' if print_mode else 'print.html'}">{'Interactive brief' if print_mode else 'Print-friendly brief'}</a></header>
<nav aria-label="Report sections"><a href="#view">Investment view</a><a href="#needs">Shopper needs</a><a href="#competitors">Competitors</a><a href="#stress">Premium stress</a><a href="#durability">Durability</a><a href="#robustness">Robustness</a><a href="#methods">Evidence & methods</a><a href="#reuse">Reuse</a></nav>
<main id="main"><section id="view" class="hero"><p class="eyebrow">{esc_title} · Evidence {esc(n['evidence_date'])}</p><h1>{esc(n['headline'])}</h1><p class="deck">{esc(n['opening'])}</p><p class="sample">{subtitle}</p><div class="proof-grid">{selected_cards}</div><p class="caption">These results describe the saved engine answers. They do not measure consumer demand, sales, price elasticity or the strength of a moat.</p></section>
<section id="needs"><div class="section-heading"><span>01 / POSITIONING</span><h2>{esc(n['needs_title'])}</h2></div>{finding(data,0)}<div class="interactive-only">{selectors(data,'needs')}<div id="needs-state" class="state-note" aria-live="polite"></div><div id="needs-chart">{static_chart(data,data['default_question'])}</div><p id="needs-chart-note" class="caption"></p><details><summary>Exact prompt and measurement</summary><p id="needs-prompt"></p><p>Explicit overall purchase leads receive credit; equal ties split credit. Conditional-only, unclear and no-recommendation answers remain in the denominator.</p></details><details><summary>Named brands and contributing answers</summary><div id="needs-detail"></div></details><button class="secondary" id="needs-export" type="button">Download this view</button></div></section>
<section id="competitors"><div class="section-heading"><span>COMPETITORS</span><h2>Brands recommended for each shopper need.</h2></div><p>Compare overall first choices with any recommendation across discovery questions. Counts describe the engine answers and do not estimate market share.</p><div class="interactive-only"><div class="controls"><label>Measure<select id="matrix-metric">{option('first_choice_credit_sum','Overall first choice')+option('recommended_sum','Any recommendation')}</select></label><label>Engine<select id="matrix-engine">{option('all','All main engines')+''.join(option(e,engine_name(e)) for e in main['engines'])}</select></label><label>Population<select id="matrix-population">{option('baseline','Baseline')+option('matched_context','Fixed matched context')}</select></label><label>Brand roster<select id="matrix-roster">{option('core','Core competitors and observed leaders')+option('all','Full comparison roster')}</select></label></div><p id="matrix-note" class="caption" aria-live="polite"></p><div id="matrix-table" class="competitor-matrix">{static_matrix(data)}</div><p class="caption">Select a number to inspect the contributing answers. Color indicates frequency within that question; it is not a cross-question score.</p></div><div class="print-only"><p class="caption">Baseline, all main engines, overall first choice. Each column is a separate discovery question.</p>{static_matrix(data)}</div><noscript>{static_matrix(data)}</noscript><details><summary>Which brands are shown?</summary><p>{esc(data['competitor_matrix']['selection_rule'])}</p><p>The full roster and evidence tables retain every recorded brand and value. The selection rule controls which rows are visible; it does not rank the market or change the hypotheses.</p></details></section>
<section id="stress"><div class="section-heading"><span>02 / PREMIUM STRESS</span><h2>{esc(n['stress_title'])}</h2></div>{finding(data,1)}{finding(data,2)}<div class="interactive-only"><p class="eyebrow">Branded prompts · kept separate from discovery</p>{selectors(data,'stress',True)}<div id="stress-state" class="state-note" aria-live="polite"></div><div id="stress-chart">{static_chart(data,data['default_branded_question'])}</div><p id="stress-chart-note" class="caption"></p><p id="stress-assessment"></p><details><summary>Exact prompt, named brands and contributing answers</summary><p id="stress-prompt"></p><div id="stress-detail"></div></details><button class="secondary" id="stress-export" type="button">Download this view</button></div></section>
<section id="durability"><div class="section-heading"><span>03 / COMPETITIVE DURABILITY</span><h2>{esc(n['durability_title'])}</h2></div><p>{esc(n['durability_intro'])}</p>{durability}<p class="pullquote">{esc(n['durability_close'])}</p></section>
<section id="robustness"><div class="section-heading"><span>04 / CONFIDENCE & LIMITS</span><h2>{esc(n['robustness_title'])}</h2></div>{finding(data,3)}<h3>Visibility and purchase choice</h3>{overview}<div class="interactive-only"><div class="controls"><label>Visibility metric<select id="visibility-metric">{''.join(option(k,l,k=='first_choice_rate') for k,l in [('mention_rate','Named'),('recommendation_rate','Any recommendation'),('first_mention_rate','First textual mention'),('first_choice_rate','Overall first choice')])}</select></label><label>Engine<select id="visibility-engine">{option('all','All main engines')+''.join(option(e,engine_name(e)) for e in main['engines'])}</select></label><label>Population<select id="visibility-population">{option('baseline','Baseline')+option('matched_context','Matched context sensitivity')}</select></label></div><div id="visibility-chart"></div><p id="visibility-note" class="caption" aria-live="polite"></p></div><p class="caption">Equal question weights are design choices, not demand weights. First mention is textual order, not endorsement. Engine answer format contributes to no-overall-lead differences.</p><h3>Do the same questions keep the same lead?</h3><p>{tokens(n['repeat_summary'],data)}</p><div id="repeat-matrix"></div><h3>Hypotheses and context sensitivity</h3><p>{esc(n['hypothesis_note'])}</p><div class="controls interactive-only"><label>Contrast<select id="contrast-choice">{''.join(option(c['id'],c['label']) for c in cfg['contrasts'])}</select></label><label>Population<select id="contrast-population">{option('baseline','Baseline')+option('matched_context','Fixed matched context')}</select></label></div><div id="contrast-result"></div><h3>Separate search supplement</h3><p>{esc(n['supplement_note'])}</p><div id="supplement-table"></div></section>
<section id="methods"><div class="section-heading"><span>05 / EVIDENCE & APPROACH</span><h2>Evidence and study limitations.</h2></div><p>{tokens(n['citation_summary'],data)}</p>{coverage}<p class="notice">A citation link does not verify a claim or show that the source influenced the recommendation. An unmapped claim may still have a citation. Some original chats are inaccessible, although their answers were saved. Product, medical and price claims have not been independently verified.</p><details><summary>Reviewed excerpts, counterexamples and conflicting claims</summary>{excerpts}</details><details><summary>Browse included answers</summary><div class="controls"><label>Engine<select id="browse-engine">{option('all','All engines')+''.join(option(e,engine_name(e)) for l in cfg['layers'] for e in l['engines'])}</select></label><label>Question<select id="browse-question">{option('all','All questions')+''.join(option(q['id'],data['labels'].get(q['id'],q['text'])) for q in cfg['questions'])}</select></label></div><div id="browse-results"></div><noscript><p><a href="evidence/index.html">Complete evidence index</a></p></noscript></details><h3>Research choices and trade-offs</h3>{''.join('<p>'+esc(p)+'</p>' for p in n['methods'])}{tools}<p><a href="methodology/README.md">Definitions, exclusions and reproduction guide</a> · <a href="data/chart_tables/brand_metrics.csv">Metric table</a> · <a href="data/report_data.json">Report data</a> · <a href="evidence/index.html">Complete evidence index</a></p></section>
<section id="reuse"><div class="section-heading"><span>06 / REUSABLE CAPABILITY</span><h2>Rerun the study or change the brand.</h2></div><p>{esc(n['reuse_intro'])}</p><ol class="pipeline"><li>Configure</li><li>Collect</li><li>Review</li><li>Calculate</li><li>Build brief</li></ol><p>{esc(n['reuse_boundary'])}</p><div class="columns"><article><h3>Current study</h3><p>{esc(cfg['focal_brand'])} · {esc(cfg['category'])} · {counts['included']} included answers</p><p>Rebuild from saved, reviewed {surface} evidence. No API keys or new engine calls are needed.</p></article><article><h3>Another category</h3><p>Change the brand roster, category prompts, attributes and reviewed interpretation. Keep validation, measurement, evidence and rendering components.</p><p>Birkenstock example: <strong>design only; no responses collected.</strong></p></article></div><p><a href="code/README.md">Run the GitHub workflow</a> · <a href="configuration/study.json">Current study configuration</a> · <a href="configuration/birkenstock.example.json">Uncollected category example</a></p><h3>Additional evidence for the investment decision</h3>{future}<p class="pullquote">{esc(n['closing'])}</p></section>
<section class="print-summary"><h2>Principal question results</h2><p>Baseline main study. Each chart shows a single question, four engines and three collection passes. Credits are explicit overall leads; no-overall-lead remains included.</p>{print_charts}</section>
<footer><p>{counts['collected']} captures · {counts['included']} included · {counts['excluded']} excluded · {counts['pending']} pending. Review provenance: {esc(n["reviewer"])}.</p><p>The reviewed interpretation is tied to this version of the data. This build made no new queries or external factual checks.</p><p><a href="release_manifest.json">Release manifest</a> · <a href="methodology/QA_STATUS.md">Verification status</a></p></footer></main>{dialogs}<script type="application/json" id="report-data">{data_json}</script><script src="assets/report.js"></script></body></html>'''


def render(data,print_mode=False):
    from .editorial import compose
    return compose(render_long(data,print_mode),data,print_mode)
