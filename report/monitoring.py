"""One-question quarterly comparison contract; synthetic demos never enter study metrics."""
import copy
import hashlib
import json
from .export import view_key


def snapshot(data, question):
    cfg=data['study']; main=cfg['layers'][0]; focal=cfg['focal_brand']
    view=data['views'][view_key(main['id'],'baseline','question',question,'all')]
    if view['status']!='ready':raise ValueError('Monitoring baseline is unavailable')
    obs=[data['observations'][oid] for oid in view['observation_ids']]
    metadata={key:sorted(set(str(o[key]) for o in obs)) for key in ['engine','model','mode','sign_in']}
    metadata['engine_settings']={engine:sorted(set((str(o['model']),str(o['mode']),str(o['sign_in']),','.join(sorted(o['flags']))) for o in obs if o['engine']==engine)) for engine in main['engines']}
    protocol=dict(question=next(q['text'] for q in cfg['questions'] if q['id']==question),context=cfg['context'],market=cfg['market'],focal_brand=focal,layer=main['id'],population='baseline',metric='first_choice_credit_sum',codebook=cfg['codebook_version'],engines=main['engines'],repeat_labels=main['repeat_labels'],metadata=metadata,collection_protocol=cfg.get('collection_protocol',{}))
    protocol=json.loads(json.dumps(protocol))
    digest=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    credit=next(r['first_choice_credit_sum'] for r in view['rows'] if r['brand']==focal)
    return dict(schema_version=1,wave=cfg['wave'],question_id=question,question_label=data['labels'][question],focal_brand=focal,protocol=protocol,protocol_hash=digest,n=view['n'],first_choice_credit=credit,synthetic=False,observation_ids=view['observation_ids'])


def compare(baseline, future, threshold_pp=25):
    if threshold_pp<=0:raise ValueError('Monitoring threshold must be positive')
    for record in [baseline,future]:
        if record['n']<=0 or not 0<=record['first_choice_credit']<=record['n']:raise ValueError('Invalid monitoring numerator or denominator')
    # Compare content, not a caller-supplied hash; stale hashes cannot bypass the gate.
    mismatches=[key for key in sorted(set(baseline['protocol'])|set(future['protocol'])) if baseline['protocol'].get(key)!=future['protocol'].get(key)]
    if baseline['question_id']!=future['question_id']:mismatches.append('question_id')
    if baseline['n']!=future['n']:mismatches.append('denominator')
    if mismatches:return dict(status='hold',delta_pp=None,changed_fields=mismatches,message='Hold comparison: collection/design metadata changed ('+', '.join(mismatches)+'). Inspect and establish a comparable series before interpreting a brand trend.')
    delta=100*(future['first_choice_credit']/future['n']-baseline['first_choice_credit']/baseline['n'])
    status='review' if abs(delta)>=threshold_pp else 'no_alert'
    return dict(status=status,delta_pp=round(delta,2),changed_fields=[],message=('Review the answers, pass variation and competitive changes before drawing an investment conclusion.' if status=='review' else 'No alert under the illustrative rule. This does not establish stability in consumer demand.'))


def demo(data):
    question=data['narrative']['presentation']['positioning_questions'][0]
    baseline=snapshot(data,question)
    cases={}
    for key,label in [('unchanged','Same recorded setup; unchanged result'),('decline','Same recorded setup; illustrative decline'),('model_change','Model metadata changes; hold comparison')]:
        future=copy.deepcopy(baseline)
        future.update(wave='synthetic_next_wave',synthetic=True,observation_ids=[])
        if key!='unchanged':future['first_choice_credit']=max(0,baseline['first_choice_credit']-baseline['n']/4)
        if key=='model_change':future['protocol']['metadata']['model']=['SYNTHETIC_CHANGED_MODEL']
        cases[key]=dict(label=label,future=future,result=compare(baseline,future))
    return dict(kind='synthetic_demonstration',baseline=baseline,cases=cases,threshold_pp=25)


if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser(description='Compare two reviewed one-question monitoring snapshots; no engine calls.')
    p.add_argument('baseline');p.add_argument('future');p.add_argument('output');args=p.parse_args()
    result=compare(json.loads(Path(args.baseline).read_text()),json.loads(Path(args.future).read_text()))
    target=Path(args.output)
    if target.exists():raise ValueError('Choose a new output file')
    target.write_text(json.dumps(result,indent=2)+'\n')
