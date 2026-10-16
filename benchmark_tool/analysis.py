"""Shared eligibility, equal-question metrics and descriptive contrasts."""
import collections
import json
from .config import planned
from .evidence import array


def populations(cfg, data):
    ledger = []
    for cell in planned(cfg):
        oid = cell['observation_id']
        obs = data['observations'].get(oid)
        code = data['coding'].get(oid, {})
        reviewed = code.get('review_status') == 'approved'
        included = bool(obs) and reviewed and code.get('quality_decision') == 'include'
        flags = array(code, 'context_flags_json') if code else []
        ledger.append(cell | dict(collected=bool(obs), reviewed=reviewed,
                                 excluded=bool(obs) and reviewed and code.get('quality_decision') == 'exclude',
                                 pending=bool(obs) and not reviewed, baseline_eligible=included,
                                 context_flagged=bool(flags), context_flags_json=json.dumps(flags),
                                 quality_reason=code.get('quality_reason', ''),
                                 captured_at_utc=(obs or {}).get('captured_at_utc', ''),
                                 model=(obs or {}).get('model') or 'undisclosed',
                                 privacy_mode=(obs or {}).get('privacy_mode') or 'undisclosed',
                                 evidence_file=(obs or {}).get('evidence_file', ''),
                                 evidence_line=(obs or {}).get('evidence_line', ''),
                                 screenshot=(obs or {}).get('screenshot', '')))
    strata = collections.defaultdict(list)
    for row in ledger:
        strata[row['layer'], row['question_id'], row['repeat']].append(row)
    for rows in strata.values():
        reasons = []
        for row in rows:
            reason = 'missing' if not row['collected'] else 'pending' if row['pending'] else 'excluded' if row['excluded'] else 'context_flagged' if row['context_flagged'] else ''
            if reason:
                reasons.append(row['engine'] + ':' + reason)
        for row in rows:
            row['matched_context_eligible'] = not reasons
            row['matched_removal_reasons'] = '; '.join(reasons)
    denoms, members = [], []
    qorder = {q['id']: i for i, q in enumerate(cfg['questions'])}
    for layer in cfg['layers']:
        rows = [r for r in ledger if r['layer'] == layer['id']]
        for population in ['baseline', 'matched_context']:
            key = population + '_eligible'
            retained = {}
            for contrast in cfg['contrasts']:
                if layer['id'] not in contrast['layers']:
                    continue
                needed = set(contrast['baseline_questions'] + contrast['comparison_questions'])
                retained[contrast['id']] = []
                for repeat in map(str, layer['repeat_labels']):
                    check = [r for r in rows if r['question_id'] in needed and r['repeat'] == repeat]
                    if len(check) == len(needed) * len(layer['engines']) and all(r[key] for r in check):
                        retained[contrast['id']].append(repeat)
            for engine in layer['engines']:
                erows = [r for r in rows if r['engine'] == engine]
                specs = [dict(scope='question', name=q, questions=[q], repeat='all', allowed=None, contrast_id='', arm='', analysis_status='descriptive') for q in layer['question_ids']]
                for group in cfg['groups']:
                    qs = group['question_ids']
                    if group['coverage'] == 'planned_within_layer':
                        qs = [q for q in qs if q in layer['question_ids']]
                    if not qs:
                        continue
                    for repeat in ['all'] + list(map(str, layer['repeat_labels'])):
                        specs.append(dict(scope='group' if repeat == 'all' else 'group_repeat', name=group['id'], questions=qs, repeat=repeat, allowed=None, contrast_id='', arm='', analysis_status='descriptive'))
                for contrast in cfg['contrasts']:
                    if contrast['id'] not in retained:
                        continue
                    for arm, field in [('baseline', 'baseline_questions'), ('comparison', 'comparison_questions')]:
                        specs.append(dict(scope='contrast_arm', name=contrast['id'] + '.' + arm, questions=contrast[field], repeat='all', allowed=retained[contrast['id']], contrast_id=contrast['id'], arm=arm, analysis_status=contrast['analysis_status']))
                for spec in specs:
                    qs = spec['questions']
                    rr = [r for r in erows if r['question_id'] in qs and (spec['repeat'] == 'all' or r['repeat'] == spec['repeat'])]
                    eligible = [r for r in rr if r[key] and (spec['allowed'] is None or r['repeat'] in spec['allowed'])]
                    counts = collections.Counter(r['question_id'] for r in eligible)
                    missing_questions = sorted(set(qs) - counts.keys(), key=qorder.get)
                    status = 'ready'
                    if any(r['pending'] or not r['collected'] for r in rr):
                        status = 'coverage_only_missing_or_pending'
                    if missing_questions:
                        status = 'not_estimable_missing_question_coverage'
                    if spec['allowed'] == []:
                        status = 'not_estimable_no_complete_comparison_repeat'
                    # A complete contrast may retain some repeats despite missing
                    # other passes. Only its retained matched passes are estimated.
                    if spec['scope'] == 'contrast_arm' and spec['allowed']:
                        status = 'ready'
                    did = '/'.join([layer['id'], engine, population, spec['scope'], spec['name'], spec['repeat']])
                    included = [r for r in rr if r['baseline_eligible']]
                    denoms.append(dict(denominator_id=did, layer=layer['id'], engine=engine,
                                       population=population, scope=spec['scope'], group_or_question=spec['name'],
                                       repeat_label=spec['repeat'], analysis_status=spec['analysis_status'],
                                       contrast_id=spec['contrast_id'], arm=spec['arm'],
                                       required_questions_json=json.dumps(qs),
                                       required_not_planned_json=json.dumps([q for q in qs if q not in layer['question_ids']]),
                                       question_counts_json=json.dumps(dict(counts)),
                                       missing_questions_json=json.dumps(missing_questions),
                                       planned_n=len(rr), collected_n=sum(r['collected'] for r in rr),
                                       missing_n=sum(not r['collected'] for r in rr),
                                       included_n=len(included), excluded_n=sum(r['excluded'] for r in rr),
                                       pending_n=sum(r['pending'] for r in rr),
                                       context_flagged_n=sum(r['context_flagged'] for r in included),
                                       matched_unflagged_peer_loss_n=sum(not r['context_flagged'] and not r['matched_context_eligible'] for r in included) if population == 'matched_context' else 0,
                                       denominator_used_n=len(eligible),
                                       eligible_repeat_labels_json=json.dumps(sorted({r['repeat'] for r in eligible})),
                                       retained_comparison_repeats_json=json.dumps(spec['allowed']) if spec['allowed'] is not None else '',
                                       question_weighting='equal_question', status=status))
                    for row in eligible:
                        members.append(dict(denominator_id=did, observation_id=row['observation_id'], question_id=row['question_id'], repeat=row['repeat'],
                                            weight=1 / (len(qs) * counts[row['question_id']]) if status == 'ready' else '', status=status))
    return ledger, denoms, members


def calculate(cfg, data, ledger, denoms, members):
    """All-brand calculations; zero first credit never implies brand rejection."""
    brands = sorted(set([cfg['focal_brand']] + cfg.get('competitors', []) + [b['brand'] for b in data['brands']]))
    contributions = []
    lookup = {}
    for row in ledger:
        if not row['baseline_eligible']:
            continue
        c = data['coding'][row['observation_id']]
        mentioned, rec, first, subs = (array(c, k) for k in ['mentioned_brands_json', 'recommended_brands_json', 'first_recommendations_json', 'substitutes_json'])
        for brand in brands:
            result = dict(observation_id=row['observation_id'], brand=brand,
                          mentioned=int(brand in mentioned), recommended=int(brand in rec),
                          first_choice_credit=1 / len(first) if brand in first else 0,
                          first_mentioned=int(c['first_brand_mentioned'] == brand),
                          substitute=int(brand in subs), overall_lead_status=c['overall_lead_status'])
            contributions.append(result)
            lookup[row['observation_id'], brand] = result
    mm = collections.defaultdict(list)
    for member in members:
        mm[member['denominator_id']].append(member)
    metrics = []
    fields = ['mentioned', 'recommended', 'first_choice_credit', 'first_mentioned', 'substitute']
    rates = ['mention_rate', 'recommendation_rate', 'first_choice_rate', 'first_mention_rate', 'substitute_rate']
    for d in denoms:
        selected = mm[d['denominator_id']]
        for brand in brands:
            values = [lookup[m['observation_id'], brand] for m in selected]
            row = {k: d[k] for k in ['denominator_id', 'layer', 'engine', 'population', 'scope', 'group_or_question', 'repeat_label', 'analysis_status', 'contrast_id', 'arm', 'status', 'denominator_used_n', 'required_questions_json']}
            row['brand'] = brand
            row['no_overall_lead_n'] = sum(v['overall_lead_status'] in ['conditional_only', 'no_recommendation', 'unclear'] for v in values)
            for field, rate in zip(fields, rates):
                row[field + '_sum'] = sum(v[field] for v in values)
                row[rate] = sum(lookup[m['observation_id'], brand][field] * m['weight'] for m in selected) if d['status'] == 'ready' else ''
            metrics.append(row)
    index = {(r['layer'], r['engine'], r['population'], r['contrast_id'], r['arm'], r['brand']): r for r in metrics if r['scope'] == 'contrast_arm'}
    contrasts = []
    for d in denoms:
        if d['scope'] != 'contrast_arm' or d['arm'] != 'baseline':
            continue
        repeats = json.loads(d['retained_comparison_repeats_json'])
        for brand in brands:
            k = (d['layer'], d['engine'], d['population'], d['contrast_id'])
            a, b = index[k + ('baseline', brand)], index[k + ('comparison', brand)]
            ready = a['status'] == b['status'] == 'ready'
            row = dict(layer=d['layer'], engine=d['engine'], population=d['population'],
                       contrast_id=d['contrast_id'], analysis_status=d['analysis_status'], brand=brand,
                       status='ready' if ready else d['status'],
                       retained_repeat_labels_json=json.dumps(repeats), retained_repeats_n=len(repeats),
                       baseline_n=a['denominator_used_n'], comparison_n=b['denominator_used_n'],
                       baseline_denominator_id=a['denominator_id'], comparison_denominator_id=b['denominator_id'],
                       interpretation='descriptive_prompt_contrast_not_causal',
                       repeat_limitation='single_repeat_no_repeat_variation' if len(repeats) == 1 else 'repeats_are_collection_passes_not_consumers')
            for rate in rates:
                row[rate + '_difference_pp'] = 100 * (b[rate] - a[rate]) if ready else ''
            contrasts.append(row)
    citation_coverage = []
    for layer in cfg['layers']:
        for engine in layer['engines']:
            included = {r['observation_id'] for r in ledger if r['layer'] == layer['id'] and r['engine'] == engine and r['baseline_eligible']}
            claims = [c for c in data['claims'] if c['observation_id'] in included and c['review_status'] == 'approved']
            mapped = [c for c in claims if c['citation_status'] == 'engine_citation_mapped']
            citation_coverage.append(dict(layer=layer['id'], engine=engine, included_answers_n=len(included), selected_claims_n=len(claims), mapped_selected_claims_n=len(mapped), unmapped_selected_claims_n=len(claims) - len(mapped),
                                         selected_claim_mapping_rate=len(mapped) / len(claims) if claims else '',
                                         interpretation='selected_claim_attachment_coverage_not_factual_support_or_engine_citation_prevalence'))
    return contributions, metrics, contrasts, citation_coverage
