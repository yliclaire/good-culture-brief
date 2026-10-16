"""Display selection only. Values come from existing checked metric rows."""

def competitive_rows(data, view, metric='first_choice_credit_sum'):
    focal=data['study']['focal_brand']
    rate=metric.endswith('_rate')
    secondary='recommendation_rate' if rate else 'recommended_sum'
    ranked=sorted((r for r in view['rows'] if r['brand']!=focal and (r[metric]>0 or r[secondary]>0)),key=lambda r:(-r[metric],-r[secondary],r['brand']))
    chosen=ranked[:3]
    if len(ranked)>3 and ranked[2][metric]>0:
        chosen += [r for r in ranked[3:] if r[metric]==ranked[2][metric]]
    return [next(r for r in view['rows'] if r['brand']==focal)]+chosen


def matrix_roster(data):
    cfg=data['study'];main=cfg['layers'][0]['id']
    questions=[q['id'] for q in cfg['questions'] if q['kind']=='discovery']
    core=set([cfg['focal_brand']]+cfg['competitors'])
    brands=set()
    for q in questions:
        view=data['views'].get('|'.join([main,'baseline','question',q,'all']))
        if not view or view['status']!='ready':continue
        brands.update(r['brand'] for r in view['rows'] if r['mentioned_sum']>0)
        core.update(r['brand'] for r in view['rows'] if r['first_choice_credit_sum']>0)
        ranked=sorted(view['rows'],key=lambda r:-r['recommended_sum'])
        if len(ranked)>1 and ranked[1]['recommended_sum']>0:
            core.update(r['brand'] for r in ranked if r['recommended_sum']>=ranked[1]['recommended_sum'])
    brands.update(core)
    fixed=[cfg['focal_brand']]+[b for b in cfg['competitors'] if b!=cfg['focal_brand']]
    ordered=fixed+sorted(brands-set(fixed))
    return dict(questions=questions,brands=ordered,core_brands=[b for b in ordered if b in core],
        selection_rule='Core view includes the configured roster, every observed overall leader, and the two most-recommended brands per discovery question (including positive ties). The roster is fixed from the baseline; filters do not change which core brands appear.')
