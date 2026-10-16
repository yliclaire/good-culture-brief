"""Offline commands. No network access, credentials or automated engine queries."""
import argparse
import collections
import html
import json
import pathlib
import sys
from . import __version__
from .config import StudyError, load, planned, require, resolve, semantic_fingerprint, sha
from .evidence import load_evidence, readcsv, writecsv
from .analysis import populations, calculate


def inventory(cfg):
    return dict(study_id=cfg['study_id'], run_id=cfg['run_id'], focal_brand=cfg['focal_brand'],
                status=cfg.get('study_status', 'draft'), planned_observations=len(list(planned(cfg))),
                layers=[dict(id=l['id'], engines=l['engines'], questions=len(l['question_ids']), repeats=len(l['repeat_labels']), planned=len(l['engines']) * len(l['question_ids']) * len(l['repeat_labels'])) for l in cfg['layers']],
                message='Plan only. Exact prompts are configured; evidence collection and reviewed coding are separate steps.')


def prepare(cfg, target):
    target = pathlib.Path(target).resolve()
    require(not target.exists() or not any(target.iterdir()), 'Preparation directory must be new or empty; existing evidence is never overwritten')
    target.mkdir(parents=True, exist_ok=True)
    writecsv(target / 'collection_plan.csv', planned(cfg))
    # A thin adapter contract matches the existing reviewed table format.
    coding_fields = ['observation_id', 'review_status', 'quality_decision', 'quality_reason', 'reviewer', 'reviewed_at_utc', 'cleaned_answer', 'supporting_excerpt', 'mentioned_brands_json', 'recommended_brands_json', 'first_recommendations_json', 'first_brand_mentioned', 'overall_lead_status', 'reason_tags_json', 'substitutes_json', 'context_flags_json', 'context_evidence_json', 'context_review_status', 'premium_assessment', 'premium_evidence_json', 'notes']
    brand_fields = ['observation_id', 'brand', 'recommendation_type', 'is_substitute', 'mention_evidence', 'recommendation_evidence', 'lead_evidence', 'substitute_evidence', 'review_status']
    claim_fields = ['claim_id', 'observation_id', 'brand', 'claim_type', 'value', 'evidence_excerpt', 'citation_status', 'observed_source_urls_json', 'fact_check_status', 'verification_source_url', 'verification_note', 'review_status']
    for name, fields in [('coding.csv', coding_fields), ('brands.csv', brand_fields), ('claims.csv', claim_fields)]:
        writecsv(target / name, [], fields)
    (target / 'observations.jsonl').write_text('')
    (target / 'COLLECTION.md').write_text('# Evidence collection\n\nThis folder contains a plan and empty review tables, not collected answers.\n\n1. Review the proposed competitors, exact prompts, attributes and contrast definitions. Freeze the configuration before collecting.\n2. For every planned cell, use a fresh chat; record browser experience, displayed model, privacy/sign-in mode, timestamp and conversation URL. Incognito alone does not guarantee context neutrality.\n3. Save the complete answer, screenshot and original DOM/accessibility evidence. Capture the attached citation destination immediately; distinguish related links, ads and product cards. Preserve failed attempts separately.\n4. Add one normalized observation per cell to observations.jsonl, with observation_id, layer, engine, question_id, repeat, exact_prompt, raw_text, captured_at_utc, model, privacy_mode, evidence_file, evidence_line and screenshot. Relative evidence paths resolve from this folder.\n5. Review coding.csv, brands.csv and claims.csv under a category-specific codebook. Blank templates do not constitute review. Keep missing, excluded, no-recommendation and unclear results distinct.\n6. Configure inputs paths and set study_status to ready after study design review. Validate before build; pending/missing evidence suppresses affected rates. A build does not independently verify claims.\n\nUse the existing Good Culture reviewed files as a format reference, not as evidence for this study. No engine collection or AI coding is automated by this command.\n')
    (target / 'CODING_GUIDE.md').write_text(
        '# Coding setup for ' + cfg['focal_brand'] + '\n\n'
        + 'Category: ' + cfg['category'] + '. Market: ' + cfg['market'] + '. Codebook: ' + cfg['codebook_version'] + '.\n\n'
        + 'Initial comparison roster: ' + ', '.join([cfg['focal_brand']] + cfg.get('competitors', [])) + '. Preserve additional brands that appear; do not collapse them into Other. Resolve aliases explicitly and preserve the mapping source.\n\n'
        + 'Allowed answer-level attributes: ' + ', '.join(cfg['attributes']) + '. Brand-specific reasons belong in linked claim rows, with exact evidence excerpts; answer-level tags alone do not attribute a reason to a brand.\n\n'
        + 'Calibrate a small sample spanning engines and question types before full coding. Record the exact AI-coder instructions, model, review time and adjudications. Assistant review is not independent human agreement.\n\n'
        + 'Separate mention, purchase recommendation, first textual mention and explicit overall purchase lead. Only an explicit equal overall tie earns 1/k first-choice credit. Conditional-only, unclear and no-recommendation outcomes stay in the included denominator without first-choice credit. Exclude defective captures with reasons, not unfavorable answers.\n\n'
        + 'Record authored personal/location context with exact excerpts. Retain usable flagged answers in baseline; the shared tool also constructs common question/repeat strata without visible flags across every planned engine. No visible flag does not prove neutrality.\n\n'
        + 'Only mark engine_citation_mapped after checking attachment to the claim/paragraph and saving the observed destination. Keep citation attachment separate from factual verification and source influence. Source panels and nearby product links are not automatically claim citations.\n\n'
        + 'Question, group and contrast definitions come from study configuration. Do not change definitions or replace selected answers after seeing results; use a new version and label exploratory checks.\n')
    return dict(prepared=str(target), planned_observations=len(list(planned(cfg))), collected_observations=0)


def report(cfg, ledger, denoms, metrics, citations, warnings):
    esc = lambda x: html.escape(str(x))
    counts = collections.defaultdict(collections.Counter)
    for r in ledger:
        c = counts[r['layer'], r['engine']]
        c['planned'] += 1
        for key in ['collected', 'excluded', 'pending', 'baseline_eligible', 'matched_context_eligible']:
            c[key] += int(r[key])
        c['context_flags'] += int(r['baseline_eligible'] and r['context_flagged'])
    def table(headers, rows):
        return '<table><thead><tr>' + ''.join('<th>' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'
    coverage = table(['Layer', 'Engine', 'Planned', 'Collected', 'Included', 'Excluded', 'Pending', 'Context flags', 'Matched included'],
                     [[l, e, c['planned'], c['collected'], c['baseline_eligible'], c['excluded'], c['pending'], c['context_flags'], c['matched_context_eligible']] for (l, e), c in counts.items()])
    source = table(['Layer', 'Engine', 'Selected claims', 'Mapped attachments', 'Unmapped'], [[c['layer'], c['engine'], c['selected_claims_n'], c['mapped_selected_claims_n'], c['unmapped_selected_claims_n']] for c in citations])
    focal = [m for m in metrics if m['brand'] == cfg['focal_brand'] and m['scope'] == 'group' and m['population'] == 'baseline']
    descriptive = table(['Layer', 'Engine', 'Group', 'Included n', 'Mention', 'Recommended', 'First choice', 'Status'],
                        [[m['layer'], m['engine'], m['group_or_question'], m['denominator_used_n']] + [f"{m[k]:.1%}" if isinstance(m[k], (float, int)) else 'Unavailable' for k in ['mention_rate', 'recommendation_rate', 'first_choice_rate']] + [m['status']] for m in focal])
    unavailable = sum(d['status'] != 'ready' for d in denoms)
    notes = cfg.get('limitations', []) + warnings
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(cfg['focal_brand'])} benchmark</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1200px;margin:36px auto;padding:0 24px;color:#172331}}h1,h2{{line-height:1.2}}table{{border-collapse:collapse;display:block;overflow-x:auto;margin:16px 0 30px}}th,td{{padding:9px 12px;border-bottom:1px solid #d7dfe6;text-align:left;white-space:nowrap}}th{{background:#eef3f6}}a{{color:#165c9a}}.note{{background:#f3f6f8;padding:16px}}small{{color:#536577}}</style>
<h1>{esc(cfg['focal_brand'])}: answer-engine benchmark</h1><p>{esc(cfg['category'])} · {esc(cfg['market'])} · {esc(cfg['wave'])}</p>
<p class="note">Generated measurement output for analyst review. This page reports the saved sample, not consumer demand, market share or an investment conclusion. Main and supplemental experiences stay separate. Repeats are collection passes, not independent consumers.</p>
<h2>Evidence coverage</h2>{coverage}<p>{unavailable} analysis populations are unavailable or coverage-only. Unavailable rates are blank in the calculation files; they are never converted to zero. Counts across alternative populations must not be added together.</p>
<h2>Focal-brand descriptive results</h2>{descriptive}<p>Groups use equal question weights. Explicit equal first-choice ties receive 1/k credit. Conditional-only, unclear and no-recommendation answers remain in the denominator with zero first-choice credit. First mention is separate from recommendation.</p>
<h2>Citation mapping coverage</h2>{source}<p>These counts concern selected coded claims and visible citation attachments. They do not establish factual support, complete citation inventories, representative source shares or causal source influence. Factual verification is a separate step.</p>
<h2>Calculation files</h2><ul>{''.join('<li><a href="'+name+'">'+label+'</a></li>' for name,label in [('brand_metrics.csv','All-brand metrics by question, group and repeat'),('contrasts.csv','Configured descriptive contrasts, with exploratory labels'),('denominators.csv','Denominators, coverage and exclusions'),('membership.csv','Exact observation membership and equal-question weights'),('contributions.csv','Per-answer brand contributions'),('eligibility.csv','All planned observations and evidence references'),('selected_claims.csv','Selected claim evidence and citation status'),('citation_coverage.csv','Citation attachment coverage'),('run_manifest.json','Configuration, input/output hashes and tool version')])}</ul>
<h2>Interpretation still required</h2><p>Explain where the focal brand wins or loses, to whom and why; assess substitution and competitive durability using the captured answers. Close each substantive finding with investment confidence, a diligence risk or a management question. This tool does not generate a moat score or write unsupported conclusions.</p>
{('<h2>Study limitations</h2><ul>'+''.join('<li>'+esc(w)+'</li>' for w in notes)+'</ul>') if notes else ''}
<p><small>Study {esc(cfg['study_id'])}; run {esc(cfg['run_id'])}; codebook {esc(cfg['codebook_version'])}; tool {__version__}. Review the full configuration in study.json.</small></p></html>'''


def build(cfg):
    require(cfg.get('study_status') == 'ready', 'Study is a draft. Review its design and collect/review evidence; plan/prepare do not create results.')
    data = load_evidence(cfg)
    ledger, denoms, members = populations(cfg, data)
    contributions, metrics, contrasts, citations = calculate(cfg, data, ledger, denoms, members)
    target = resolve(cfg, cfg['output_root']) / cfg['run_id']
    inputs = data['hashes'] | {str(cfg['_path']): sha(cfg['_path'])}
    code = {p.name: sha(p) for p in sorted(pathlib.Path(__file__).parent.glob('*.py'))}
    lock = dict(inputs=inputs, code=code, tool_version=__version__)
    manifest_path = target / 'run_manifest.json'
    if target.exists() and any(target.iterdir()):
        require(manifest_path.exists(), 'Nonempty output folder has no run manifest; choose a new run_id')
        prior = json.loads(manifest_path.read_text())
        require(prior['lock'] == lock, 'Inputs or tool code changed. Choose a new run_id; prior outputs are preserved.')
    target.mkdir(parents=True, exist_ok=True)
    files = []
    for name, rows, fields in [('eligibility.csv', ledger, None), ('denominators.csv', denoms, None), ('membership.csv', members, ['denominator_id', 'observation_id', 'question_id', 'repeat', 'weight', 'status']), ('contributions.csv', contributions, ['observation_id', 'brand', 'mentioned', 'recommended', 'first_choice_credit', 'first_mentioned', 'substitute', 'overall_lead_status']), ('brand_metrics.csv', metrics, None), ('contrasts.csv', contrasts, ['layer', 'engine', 'population', 'contrast_id', 'analysis_status', 'brand', 'status', 'retained_repeat_labels_json', 'retained_repeats_n', 'baseline_n', 'comparison_n', 'baseline_denominator_id', 'comparison_denominator_id', 'interpretation', 'repeat_limitation'] + [k + '_difference_pp' for k in ['mention_rate', 'recommendation_rate', 'first_choice_rate', 'first_mention_rate', 'substitute_rate']]), ('citation_coverage.csv', citations, None), ('selected_claims.csv', data['claims'], list(data['claims'][0]) if data['claims'] else ['claim_id', 'observation_id', 'brand', 'evidence_excerpt', 'citation_status'])]:
        writecsv(target / name, rows, fields)
        files.append(name)
    public_cfg = {k: v for k, v in cfg.items() if not k.startswith('_')}
    (target / 'study.json').write_text(json.dumps(public_cfg, indent=2, ensure_ascii=False) + '\n')
    (target / 'index.html').write_text(report(cfg, ledger, denoms, metrics, citations, data['warnings']))
    files += ['study.json', 'index.html']
    manifest = dict(study_id=cfg['study_id'], run_id=cfg['run_id'], wave=cfg['wave'],
                    tool_version=__version__, measurement_fingerprint=semantic_fingerprint(cfg), lock=lock,
                    outputs={name: sha(target / name) for name in files}, warnings=data['warnings'],
                    counts=dict(planned=len(ledger), collected=sum(r['collected'] for r in ledger), included=sum(r['baseline_eligible'] for r in ledger), excluded=sum(r['excluded'] for r in ledger), pending=sum(r['pending'] for r in ledger), matched_included=sum(r['matched_context_eligible'] for r in ledger)),
                    metric_definition='Equal question means; 1/k explicit first-choice ties; no-lead answers retained; unavailable is blank.')
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    return dict(output=str(target), entry_point=str(target / 'index.html'), **manifest['counts'])


def compare(old, new, output):
    old, new = pathlib.Path(old).resolve(), pathlib.Path(new).resolve()
    runs = []
    for path in [old, new]:
        manifest = json.loads((path / 'run_manifest.json').read_text())
        for name, digest in manifest['outputs'].items():
            require(sha(path / name) == digest, 'Run output modified: ' + str(path / name))
        runs.append(manifest)
    a, b = [json.loads((p / 'study.json').read_text()) for p in [old, new]]
    for key in ['focal_brand', 'category', 'market', 'context', 'codebook_version', 'attributes']:
        require(a[key] == b[key], 'Not directly comparable: ' + key + ' changed. Reconcile definitions first.')
    require(runs[0]['tool_version'] == runs[1]['tool_version'], 'Tool metric version changed')
    require(runs[0]['lock']['code'] == runs[1]['lock']['code'], 'Tool code changed; reconcile calculation versions before comparison')
    q = [{x['id']: x for x in cfg['questions']} for cfg in [a, b]]
    qdiff = {qid for qid in q[0].keys() & q[1].keys() if (q[0][qid]['text'], q[0][qid]['kind']) != (q[1][qid]['text'], q[1][qid]['kind'])}
    def metadata(path):
        d = collections.defaultdict(set)
        for r in readcsv(path / 'eligibility.csv'):
            if r['collected'] == 'True':
                d[r['layer'], r['engine'], r['question_id']].add((r['model'], r['privacy_mode']))
        return d
    meta = [metadata(p) for p in [old, new]]
    denom = [{r['denominator_id']: r for r in readcsv(p / 'denominators.csv')} for p in [old, new]]
    def cells(path):
        rows = readcsv(path / 'brand_metrics.csv')
        return {(r['layer'], r['engine'], r['population'], r['group_or_question'], r['brand']): r for r in rows if r['scope'] == 'question'}
    cells_a, cells_b = cells(old), cells(new)
    results = []
    rate_fields = ['mention_rate', 'recommendation_rate', 'first_choice_rate', 'first_mention_rate', 'substitute_rate']
    for key in sorted(cells_a.keys() | cells_b.keys()):
        x, y = cells_a.get(key), cells_b.get(key)
        status = 'ready'
        if not x or not y:
            status = 'not_comparable_missing_cell_or_brand'
        elif key[3] in qdiff:
            status = 'not_comparable_prompt_changed'
        elif x['status'] != 'ready' or y['status'] != 'ready':
            status = 'not_estimable'
        setup_changed = meta[0][key[:2] + (key[3],)] != meta[1][key[:2] + (key[3],)]
        old_repeats = denom[0].get((x or {}).get('denominator_id'), {}).get('eligible_repeat_labels_json', '[]')
        new_repeats = denom[1].get((y or {}).get('denominator_id'), {}).get('eligible_repeat_labels_json', '[]')
        coverage_changed = bool(x and y) and (x['denominator_used_n'] != y['denominator_used_n'] or set(json.loads(old_repeats)) != set(json.loads(new_repeats)))
        if status == 'ready' and setup_changed:
            status = 'descriptive_only_model_or_privacy_changed'
        elif status == 'ready' and coverage_changed:
            status = 'descriptive_only_coverage_changed'
        row = dict(layer=key[0], engine=key[1], population=key[2], question_id=key[3], brand=key[4], status=status,
                   old_n=(x or {}).get('denominator_used_n', ''), new_n=(y or {}).get('denominator_used_n', ''),
                   old_model_privacy_json=json.dumps(sorted(meta[0][key[:2] + (key[3],)])), new_model_privacy_json=json.dumps(sorted(meta[1][key[:2] + (key[3],)])),
                   coverage_changed=coverage_changed, old_eligible_repeats_json=old_repeats, new_eligible_repeats_json=new_repeats,
                   setup_changed=setup_changed, model_identity_note='Undisclosed identities cannot establish unchanged model setup' if any('undisclosed' in str(v) for v in [meta[0][key[:2] + (key[3],)], meta[1][key[:2] + (key[3],)]]) else '')
        for rate in rate_fields:
            row[rate + '_difference_pp'] = 100 * (float(y[rate]) - float(x[rate])) if status in ['ready', 'descriptive_only_model_or_privacy_changed', 'descriptive_only_coverage_changed'] else ''
        results.append(row)
    output = pathlib.Path(output).resolve()
    require(not output.exists(), 'Comparison output already exists; choose a new filename')
    output.parent.mkdir(parents=True, exist_ok=True)
    writecsv(output, results)
    return dict(output=str(output), comparison_rows=len(results), changed_prompt_ids=sorted(qdiff), note='Question-level same-engine comparisons only. Different question mixes are not silently pooled; counts, setup changes and unavailable cells are explicit.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['plan', 'prepare', 'validate', 'build']:
        p = sub.add_parser(command)
        p.add_argument('--config', required=True, type=pathlib.Path)
        if command == 'prepare':
            p.add_argument('--output', required=True, type=pathlib.Path)
    p = sub.add_parser('compare')
    p.add_argument('--old', required=True)
    p.add_argument('--new', required=True)
    p.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'compare':
            result = compare(args.old, args.new, args.output)
        else:
            cfg = load(args.config)
            if args.command == 'plan':
                result = inventory(cfg)
            elif args.command == 'prepare':
                result = prepare(cfg, args.output)
            elif args.command == 'build':
                result = build(cfg)
            else:
                result = inventory(cfg)
                if cfg.get('inputs'):
                    data = load_evidence(cfg)
                    ledger, denoms, _ = populations(cfg, data)
                    result.update(collected=len(data['observations']), included=sum(r['baseline_eligible'] for r in ledger), unavailable_populations=sum(d['status'] != 'ready' for d in denoms), warnings=data['warnings'])
                else:
                    result['data_status'] = 'not_collected_no_results'
        print(json.dumps(result, indent=2))
    except (StudyError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, 'Benchmark error: ' + str(error) + '\n')
