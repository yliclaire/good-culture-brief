"""Prepare presentation states from validated metrics; no calculations in the browser."""
import collections
import hashlib
import json
from pathlib import Path
from benchmark_tool.config import require, sha
from benchmark_tool.evidence import norm, readcsv

RATE_FIELDS = ['mention_rate','recommendation_rate','first_choice_rate','first_mention_rate','substitute_rate']
SUM_FIELDS = ['mentioned_sum','recommended_sum','first_choice_credit_sum','first_mentioned_sum','substitute_sum']


def fingerprint(cfg, data):
    keys = ['study_id','wave','focal_brand','category','market','context','codebook_version','attributes','questions','layers','groups','contrasts']
    value = dict(study={k:cfg[k] for k in keys}, inputs=sorted(data['hashes'].values()),
                 calculations=sha(Path(__file__).resolve().parents[1]/'benchmark_tool/analysis.py'))
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def view_key(layer, population, scope, name, engine):
    return '|'.join([layer,population,scope,name,engine])


def export(cfg, data, metrics_dir, narrative):
    require(narrative.get('review_status') == 'reviewed' and narrative.get('reviewer') and narrative.get('reviewed_at'), 'Narrative has not been reviewed')
    require(narrative.get('source_fingerprint') == fingerprint(cfg,data), 'Narrative is stale or belongs to another study/wave. Review the interpretation before building a brief.')
    root = Path(metrics_dir)
    denoms = readcsv(root/'denominators.csv')
    members = readcsv(root/'membership.csv')
    metrics = readcsv(root/'brand_metrics.csv')
    ledger = readcsv(root/'eligibility.csv')
    contrib = readcsv(root/'contributions.csv')
    by_d = collections.defaultdict(list)
    by_m = collections.defaultdict(list)
    for r in metrics:
        by_d[r['denominator_id']].append(r)
    for m in members:
        by_m[m['denominator_id']].append(m)
    views = {}
    for d in denoms:
        if d['scope'] not in ['question','group'] or d['repeat_label'] != 'all':
            continue
        oid = [m['observation_id'] for m in by_m[d['denominator_id']]]
        rows = []
        if d['status'] == 'ready':
            for r in by_d[d['denominator_id']]:
                rows.append(dict(brand=r['brand'], **{k:float(r[k]) for k in RATE_FIELDS+SUM_FIELDS}))
        nolead = int(by_d[d['denominator_id']][0]['no_overall_lead_n'])
        v = dict(layer=d['layer'], population=d['population'], scope=d['scope'], name=d['group_or_question'], engine=d['engine'],
            status=d['status'], n=int(d['denominator_used_n']), denominator_ids=[d['denominator_id']],
            questions=json.loads(d['required_questions_json']), missing_questions=json.loads(d['missing_questions_json']),
            pass_labels=json.loads(d['eligible_repeat_labels_json']), observation_ids=oid,
            flagged_n=sum(bool(json.loads(data['coding'][o].get('context_flags_json') or '[]')) for o in oid),
            no_lead_n=nolead, rows=rows, planned_n=int(d['planned_n']), excluded_n=int(d['excluded_n']), pending_n=int(d['pending_n']))
        views[view_key(d['layer'],d['population'],d['scope'],d['group_or_question'],d['engine'])] = v
    # Equal engine means of the already equal-question metrics; never re-match.
    for layer in cfg['layers']:
        bases = {(v['population'],v['scope'],v['name']) for v in views.values() if v['layer']==layer['id']}
        for pop, scope, name in bases:
            parts = [views[view_key(layer['id'],pop,scope,name,e)] for e in layer['engines']]
            ready = all(p['status']=='ready' for p in parts)
            brands = sorted({r['brand'] for p in parts for r in p['rows']})
            rows = []
            if ready:
                for brand in brands:
                    rr = [next(r for r in p['rows'] if r['brand']==brand) for p in parts]
                    rows.append(dict(brand=brand, **{k:sum(r[k] for r in rr)/len(rr) for k in RATE_FIELDS}, **{k:sum(r[k] for r in rr) for k in SUM_FIELDS}))
            v = dict(layer=layer['id'],population=pop,scope=scope,name=name,engine='all',status='ready' if ready else 'not_estimable',
                n=sum(p['n'] for p in parts), denominator_ids=sum([p['denominator_ids'] for p in parts],[]),
                questions=parts[0]['questions'], missing_questions=sorted({q for p in parts for q in p['missing_questions']}),
                pass_labels=sorted({r for p in parts for r in p['pass_labels']}), observation_ids=sum([p['observation_ids'] for p in parts],[]),
                flagged_n=sum(p['flagged_n'] for p in parts), no_lead_n=sum(p['no_lead_n'] for p in parts), rows=rows,
                planned_n=sum(p['planned_n'] for p in parts),excluded_n=sum(p['excluded_n'] for p in parts),pending_n=sum(p['pending_n'] for p in parts))
            views[view_key(layer['id'],pop,scope,name,'all')] = v
    citations = readcsv(root/'citation_coverage.csv')
    observations = {}
    ledger_by_id = {o['observation_id']:o for o in ledger}
    for oid,o in data['observations'].items():
        c = data['coding'].get(oid,{})
        claims = [r for r in data['claims'] if r['observation_id']==oid]
        urls = sorted({url for r in claims for url in json.loads(r.get('observed_source_urls_json') or '[]')})
        observations[oid] = dict(id=oid,layer=o['layer'],engine=o['engine'],question_id=o['question_id'],repeat=str(o['repeat']),
            prompt=o['exact_prompt'],model=o.get('model') or 'Undisclosed',timestamp=o['captured_at_utc'],
            mode=o.get('privacy_mode') or 'Not recorded',sign_in=o.get('sign_in_status') or 'Not recorded',
            quality=c.get('quality_decision','pending'),quality_reason=c.get('quality_reason','Not recorded'),
            flags=json.loads(c.get('context_flags_json') or '[]'),context_excerpts=json.loads(c.get('context_evidence_json') or '[]'),
            lead_status=c.get('overall_lead_status','Not coded'),leading_brands=json.loads(c.get('first_recommendations_json') or '[]'),
            premium=c.get('premium_assessment','Not coded'),transcript=c.get('cleaned_answer') or o['raw_text'],
            mapped_claims=sum(r['citation_status']=='engine_citation_mapped' for r in claims), selected_claims=len(claims),
            observed_urls=urls,evidence_path='evidence/'+hashlib.sha256(oid.encode()).hexdigest()[:16]+'.html',
            matched_context=ledger_by_id[oid]['matched_context_eligible']=='True')
    selections = narrative['evidence_selections']
    for e in selections:
        require(e['observation_id'] in observations, 'Selected evidence has no observation')
        require(norm(e['excerpt']) in norm(data['observations'][e['observation_id']]['raw_text']), 'Selected excerpt absent from original answer')
    repeats = []
    main = cfg['layers'][0]
    for engine in main['engines']:
        for q in cfg['questions']:
            if q['id'] not in main['question_ids']:
                continue
            oo = [o for o in observations.values() if o['layer']==main['id'] and o['engine']==engine and o['question_id']==q['id'] and o['quality']=='include']
            signatures=[(o['lead_status'],tuple(sorted(o['leading_brands']))) for o in oo]
            complete=len(oo)==len(main['repeat_labels']) and len(oo)>1
            repeats.append(dict(engine=engine,question=q['id'],kind=q['kind'],n=len(oo),stable=complete and len(set(signatures))==1,
                complete=complete,outcomes=[dict(observation_id=o['id'],repeat=o['repeat'],status=o['lead_status'],brands=o['leading_brands']) for o in oo]))
    counts = dict(planned=len(ledger),collected=len(observations),included=sum(o['quality']=='include' for o in observations.values()),excluded=sum(o['quality']=='exclude' for o in observations.values()),pending=sum(o['quality'] not in ['include','exclude'] for o in observations.values()))
    numbers = dict(included=counts['included'],excluded=counts['excluded'],collected=counts['collected'],
        mapped_claims=sum(int(r['mapped_selected_claims_n']) for r in citations),selected_claims=sum(int(r['selected_claims_n']) for r in citations),
        stable_discovery=sum(r['stable'] for r in repeats if r['kind']=='discovery'),discovery_cells=sum(r['kind']=='discovery' for r in repeats))
    for name,spec in narrative['metric_bindings'].items():
        v = views[spec['view']]
        require(v['status']=='ready', 'Narrative references unavailable metric: '+name)
        if spec['field']=='n':
            numbers[name]=v['n']
        elif spec['field']=='no_lead_n':
            numbers[name]=v['no_lead_n']
        elif spec['field'].startswith('premium:'):
            numbers[name]=sum(observations[o]['premium']==spec['field'].split(':',1)[1] for o in v['observation_ids'])
        elif spec['field'].startswith('lead_status:'):
            numbers[name]=sum(observations[o]['lead_status']==spec['field'].split(':',1)[1] for o in v['observation_ids'])
        else:
            brand=cfg['focal_brand'] if spec['brand']=='$focal' else cfg['competitors'][0] if spec['brand']=='$primary' else spec['brand']
            matched=[r for r in v['rows'] if r['brand']==brand]
            require(len(matched)==1, 'Narrative brand binding does not match the coded brand: '+brand)
            numbers[name]=matched[0][spec['field']]
    contrasts=[]
    for c in readcsv(root/'contrasts.csv'):
        if c['brand'] != cfg['focal_brand']:
            continue
        contrasts.append({k:(float(v) if k.endswith('_difference_pp') and v else None if k.endswith('_difference_pp') else v) for k,v in c.items()})
    result=dict(schema_version='1.1',study={k:v for k,v in cfg.items() if not k.startswith('_') and k!='inputs'},counts=counts,
        numbers=numbers,metric_bindings=narrative['metric_bindings'],views=views,observations=observations,repeats=repeats,
        contrasts=contrasts,citations=citations,selections=selections,narrative=narrative,
        source_fingerprint=narrative['source_fingerprint'],default_question=narrative['default_question'],
        default_branded_question=narrative['default_branded_question'],labels=narrative.get('question_labels',{}))
    from .competition import matrix_roster
    result['competitor_matrix']=matrix_roster(result)
    return result
