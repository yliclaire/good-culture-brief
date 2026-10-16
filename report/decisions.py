"""Render reviewed decision support without embedding brand-specific conclusions."""
from .render import esc, table, engine_name


def challenge(data, finding):
    cfg=data['narrative'].get('decision_support',{})
    item=next((c for c in cfg.get('challenges',[]) if c['finding']==finding),None)
    if not item:return ''
    excerpts=[]
    for eid in item['evidence_ids']:
        selection=next(e for e in data['selections'] if e['evidence_id']==eid)
        obs=data['observations'][selection['observation_id']]
        excerpts.append('<figure><blockquote>'+esc(selection['excerpt'])+'</blockquote><figcaption>'+esc(engine_name(obs['engine'])+' · '+data['labels'][obs['question_id']]+' · pass '+obs['repeat'])+' · <a href="'+esc(obs['evidence_path'])+'">Complete answer</a></figcaption></figure>')
    return '<details class="evidence-challenge"><summary>Challenge the finding · '+esc(item['title'])+'</summary>'+''.join(excerpts)+'<p class="caption">Illustrative captured engine statements; factual product and price claims are not independently verified.</p><p class="challenge-verdict">'+esc(item['conclusion'])+'</p></details>'


def scenario(data):
    cfg=data['narrative'].get('decision_support')
    if not cfg:return ''
    return '<div id="competitive-scenario" class="competitive-scenario"><p class="eyebrow">Competitive attack scenario</p><h3>'+esc(cfg['scenario_title'])+'</h3><p class="caption">'+esc(cfg['scenario_assumption'])+'</p>'+table(['Attack surface','Observed evidence','Conditional inference','Test next'],[[esc(c) for c in row] for row in cfg['scenario_rows']])+'<p>'+esc(cfg['scenario_conclusion'])+'</p></div>'


def priorities(data):
    cfg=data['narrative'].get('decision_support')
    if not cfg:return ''
    rows=[]
    for i,item in enumerate(cfg['priorities'],1):
        rows.append([str(i)+' · '+esc(item['title']),esc(item['request']),'<p class="decision-direction">Strengthens the case</p>'+esc(item['stronger'])+'<p class="decision-direction">Weakens the case</p>'+esc(item['weaker']),esc(item['decision'])])
    return '<p class="caption">Ordered by decision importance. These are proposed diligence tests, not results. Directional interpretation requires comparable products and controls for availability, promotions and buyer mix; no numerical pass/fail thresholds are claimed.</p><div class="priority-table">'+table(['Priority','Evidence to request','What would change our view','Investment decision'],rows)+'</div>'


def monitoring_guide(data):
    if not data['narrative'].get('decision_support'):return ''
    from .monitoring import demo
    import json
    payload=demo(data)
    encoded=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
    return '<details id="monitoring-demo" class="monitoring-demo"><summary>See how a quarterly check would work</summary><p class="notice">Synthetic demonstration. Only the baseline is observed. The possible future outcomes below are invented to demonstrate review routing; they are excluded from every study metric and evidence page.</p><label for="monitor-case">Illustrative next-wave scenario</label><select id="monitor-case">'+''.join('<option value="'+esc(key)+'">'+esc(case['label'])+'</option>' for key,case in payload['cases'].items())+'</select><div id="monitor-result" aria-live="polite"></div><noscript><p>'+esc(payload['cases']['decline']['result']['message'])+'</p></noscript><p class="caption">The alert rule is illustrative: an absolute change of at least 25 percentage points triggers review. It is not a statistical significance test or an investment threshold. Matching recorded metadata cannot eliminate hidden account/retrieval differences.</p><p><a href="data/monitoring_demo.json">Synthetic cases and comparison results</a> · <a href="data/monitoring_baseline.json">Observed baseline snapshot</a> · <a href="methodology/MONITORING.md">Comparison contract and rerun instructions</a></p><script type="application/json" id="monitor-data">'+encoded+'</script></details><details><summary>Birkenstock reuse example</summary><p>Category profile and exact prompts for an uncollected footwear study.</p><p><a href="demonstrations/birkenstock/index.html">Study design and exact prompts</a> · <a href="demonstrations/birkenstock/collection_plan.json">Request plan (JSON)</a> · <a href="demonstrations/birkenstock/study.json">Category configuration</a> · <a href="demonstrations/birkenstock/manifest.json">Preview execution record</a></p><p class="caption">Brand, competitors, category questions, attributes and reviewed interpretation change. Validation, collection, calculation and rendering components are reused. Live API collection remains unpiloted.</p></details>'
