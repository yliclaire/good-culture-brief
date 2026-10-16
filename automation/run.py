#!/usr/bin/env python3
"""Single entry point for GitHub and local execution. Offline unless collect is explicit."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmark_tool.config import load, planned, require, sha, StudyError
from benchmark_tool.cli import prepare, build
from automation.providers import KEYS, specification, normalize, post


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def study(args):
    registry = {'good_culture': 'good_culture.json', 'birkenstock': 'birkenstock.example.json'}
    cfg = load(ROOT / 'studies' / registry[args.study])
    if args.operation == 'build-browser':
        require(args.study == 'good_culture', 'Only Good Culture has reviewed baseline evidence')
        require(not (args.brand or args.competitors or args.questions), 'Browser rebuild cannot change brands or questions')
        return cfg
    cfg = {k: copy.deepcopy(v) for k, v in cfg.items() if not k.startswith('_')}
    old_brand = cfg['focal_brand']
    old_competitor = cfg['competitors'][0]
    if args.brand:
        require(bool(args.competitors), 'Supply competitors when changing focal brand')
        cfg['focal_brand'] = args.brand.strip()
    if args.competitors:
        cfg['competitors'] = [b.strip() for b in args.competitors.split(',') if b.strip()]
    require(bool(cfg['focal_brand']) and cfg['competitors'] and cfg['focal_brand'] not in cfg['competitors'], 'Supply a distinct focal brand and at least one competitor')
    require(len(set(cfg['competitors'])) == len(cfg['competitors']), 'Duplicate competitors')
    cfg['study_id'] = re.sub('[^a-z0-9]+', '_', cfg['focal_brand'].lower()).strip('_')
    require(bool(cfg['study_id']), 'Brand needs an alphanumeric name')
    if args.questions.strip():
        questions = json.loads(args.questions)
        require(isinstance(questions, list) and bool(questions), 'Questions must be a nonempty JSON array')
        for q in questions:
            require(isinstance(q, dict) and all(isinstance(q.get(k), str) and q[k].strip() for k in ['id', 'kind', 'text']), 'Each question needs id, kind and text')
            require(q['kind'] in ['discovery', 'branded'], 'Question kind must be discovery or branded')
            q.setdefault('theme', 'custom')
        cfg['questions'] = questions
        cfg['contrasts'] = []  # Do not invent hypothesis definitions for custom questions.
    else:
        # Simultaneous replacement avoids collisions when a new brand contains an old name.
        replacements = {old_brand: cfg['focal_brand'], old_competitor: cfg['competitors'][0]}
        pattern = re.compile('|'.join(re.escape(k) for k in sorted(replacements, key=len, reverse=True)))
        for q in cfg['questions']:
            q['text'] = pattern.sub(lambda m: replacements[m.group()], q['text'])
    qids = [q['id'] for q in cfg['questions']]
    engines = [p.strip() for p in args.providers.split(',') if p.strip()]
    require(engines and len(engines) == len(set(engines)) and set(engines) <= KEYS.keys(), 'Choose distinct supported API providers')
    require(1 <= args.repeats <= 10, 'Repeats must be between 1 and 10')
    cfg['layers'] = [dict(id='api', engines=engines, question_ids=qids, repeat_labels=[str(i+1) for i in range(args.repeats)])]
    cfg['groups'] = [dict(id=kind, label=kind.title(), question_ids=[q['id'] for q in cfg['questions'] if q['kind'] == kind], coverage='planned_within_layer') for kind in ['discovery', 'branded'] if any(q['kind'] == kind for q in cfg['questions'])]
    for c in cfg['contrasts']:
        c['layers'] = ['api']
    cfg.pop('inputs', None)
    cfg.update(study_status='draft', wave='new_api_collection', run_id='api_collection', output_root='metrics')
    cfg['collection_protocol'] = dict(mode='direct_provider_api', fresh_request_per_question=True, search_policy='enabled_provider_decides', automatic_retries=False)
    cfg['limitations'] = ['New direct API series: do not pool with consumer browser captures.', 'Prompt framework is adapted from a saved category profile; preview and review before collection.', 'All captured responses require coding review; factual verification is separate.', 'API availability, model support, retention and billing depend on provider accounts.']
    return cfg


def verify_baseline():
    relocation = ROOT / 'data/browser_baseline/relocation.json'
    source = json.loads(relocation.read_text())
    for item in source['sources'].values():
        path = (ROOT / item['path']).resolve()
        require(path.is_relative_to(ROOT) and sha(path) == item['sha256'], 'Bundled provenance changed')
    expected = json.loads((ROOT / 'data/browser_baseline/baseline_integrity.json').read_text())
    for name, digest in expected.items():
        require(sha(ROOT / name) == digest, 'Frozen browser baseline changed: ' + name)


def execute(args):
    if args.operation == 'build-brief':
        require(not(args.brand or args.competitors or args.questions), 'Build brief selects reviewed evidence; brand/question overrides are for preview or collection')
        from report.build import build_brief
        return build_brief(args.reviewed_study, args.output)
    cfg = study(args)
    output = Path(args.output).resolve()
    require(not output.exists(), 'Choose a new output folder; earlier runs are preserved')
    if args.operation == 'build-browser':
        verify_baseline()
        cfg['run_id'] = output.name
        cfg['output_root'] = str(output.parent)
        result = build(cfg)
        require(result['collected'] == 156 and result['included'] == 155 and result['excluded'] == 1 and result['pending'] == 0, 'Baseline coverage changed')
        save(output / 'WORKFLOW_STATUS.json', dict(operation=args.operation, collection_surface='saved_browser_evidence', new_api_calls=0, counts=result,
            report_stage='Measurement report; final investment brief template is a separate presentation build'))
        return result
    jobs = list(planned(cfg))
    require(1 <= args.max_calls <= 500 and len(jobs) <= args.max_calls, f'{len(jobs)} requests exceed the limit; increase max_calls deliberately or reduce scope')
    models = json.loads((ROOT / 'providers.json').read_text())
    for engine in {j['engine'] for j in jobs}:
        env_name = engine.upper() + '_MODEL'
        models[engine] = os.getenv(env_name) or models.get(engine, '')
    if args.operation == 'collect':
        require(args.confirm_paid, 'Live collection requires explicit confirmation that API charges may apply')
        missing = [KEYS[p] for p in {j['engine'] for j in jobs} if not os.getenv(KEYS[p])]
        missing += [p.upper() + '_MODEL' for p in {j['engine'] for j in jobs} if not models.get(p)]
        require(not missing, 'Configure selected providers before collection: ' + ', '.join(sorted(missing)))
    output.mkdir(parents=True)
    save(output / 'study.json', cfg)
    save(output / 'collection_study.json', cfg)
    cfg = load(output / 'study.json')
    prepare(cfg, output / 'review')
    (output / 'review/COLLECTION.md').write_text(
        '# API collection and review\n\n'
        'This collection uses fresh direct provider API requests, not consumer browser chats. '
        'The plan and raw request/response files are preserved alongside normalized records. '
        'API records have capture_format=direct_provider_api and no screenshot. '
        'Citations, grounding segments, source lists and usage metadata remain in the raw responses and normalized attempt records. '
        'These are observed attachments, not verified factual support.\n\n'
        'A preview contains no collected answers. After collection, fill coding.csv, brands.csv and claims.csv under a reviewed codebook. '
        'Do not mark incomplete/error responses approved by default. Preserve attempts; review any re-collection separately. '
        'The saved study remains draft until design, coverage and coding are reviewed. '
        'Use the supplied benchmark_tool build function only after configuring and approving the reviewed study. '
        'After review and registration, use Build investment brief. Collect engine answers does not auto-approve coding or launch a report build.\n')
    random.Random(20261016).shuffle(jobs)
    save(output / 'collection_plan.json', dict(planned_requests=len(jobs), jobs=jobs, models={p: models.get(p, '') for p in {j['engine'] for j in jobs}},
        note='Each request is fresh. Request limit is not a dollar spending cap. Search is enabled but not guaranteed. No supplemental Google AI Mode or Copilot API is implied.'))
    manifest = dict(operation=args.operation, started_at=stamp(), planned_requests=len(jobs), attempted=0, captured=0, issues=0,
        input_file='collection_study.json', input_sha256=sha(output / 'collection_study.json'), source_sha256={p.name: sha(p) for p in Path(__file__).parent.glob('*.py')},
        commit=os.getenv('GITHUB_SHA', 'local'), status='preview_only', collection_surface='direct_provider_api')
    if args.operation == 'preview':
        save(output / 'manifest.json', manifest)
        return manifest
    manifest['status'] = 'running'
    observations = output / 'review/observations.jsonl'
    save(output / 'manifest.json', manifest)
    try:
        for number, job in enumerate(jobs, 1):
            provider = job['engine']
            model = models[provider]
            record = dict(job, provider=provider, requested_model=model, started_at=stamp(), status='error')
            stem = f'{number:04d}'  # User IDs never become file paths.
            url, body = specification(provider, model, job['exact_prompt'])
            save(output / 'attempts' / (stem + '.request.json'), dict(job=job, url=url, body=body))
            started = time.monotonic()
            manifest['attempted'] += 1
            try:
                raw = post(provider, url, body)
                raw_path = output / 'attempts' / (stem + '.raw.json')
                save(raw_path, raw)  # Preserve original before parsing.
                record.update(normalize(provider, raw))
                if record['answer'].strip():
                    row = dict(job, raw_text=record['answer'], captured_at_utc=record['started_at'],
                        model=record['returned_model'], requested_model=model, privacy_mode='direct_api_fresh_request_provider_policy',
                        capture_format='direct_provider_api', evidence_file='../attempts/' + stem + '.raw.json',
                        screenshot='', collection_status=record['status'])
                    with observations.open('a') as stream:
                        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    manifest['captured'] += 1
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError) as error:
                # Neither raw server error bodies nor credentials enter logs.
                record.update(status='error', error_type=type(error).__name__, http_status=getattr(error, 'code', None))
            record.update(finished_at=stamp(), elapsed_seconds=round(time.monotonic()-started, 3))
            save(output / 'attempts' / (stem + '.record.json'), record)
            if record['status'] != 'captured_pending_coding':
                manifest['issues'] += 1
                manifest['status'] = 'stopped_for_review'
                break
            save(output / 'manifest.json', manifest)
        else:
            manifest['status'] = 'collected_pending_coding'
    finally:
        if manifest['status'] == 'running':
            manifest['status'] = 'interrupted_review_required'
        manifest['finished_at'] = stamp()
        save(output / 'manifest.json', manifest)
    # Wire real API evidence to review tables, but never mark it approved automatically.
    cfg = {k: v for k,v in cfg.items() if not k.startswith('_')}
    cfg['inputs'] = dict(adapter='reviewed_v2', observations='review/observations.jsonl', coding='review/coding.csv', brands='review/brands.csv', claims='review/claims.csv')
    save(output / 'study.json', cfg)
    manifest['review_study_sha256'] = sha(output / 'study.json')
    manifest['attempt_files_sha256'] = {str(p.relative_to(output)): sha(p) for p in sorted((output / 'attempts').glob('*.json'))}
    save(output / 'manifest.json', manifest)
    require(manifest['status'] == 'collected_pending_coding', 'Collection stopped for review; inspect the preserved artifact before any retry')
    return manifest


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['build-brief', 'build-browser', 'preview', 'collect'])
    p.add_argument('--reviewed-study', default=os.getenv('REVIEWED_STUDY','good_culture_browser_2026_q4'))
    p.add_argument('--study', choices=['good_culture', 'birkenstock'], default='good_culture')
    p.add_argument('--brand', default=os.getenv('FOCAL_BRAND', ''))
    p.add_argument('--competitors', default=os.getenv('COMPETITORS', ''))
    p.add_argument('--questions', default=os.getenv('QUESTIONS_JSON', ''), help='Optional JSON list with id, kind, text')
    p.add_argument('--providers', default=os.getenv('PROVIDERS', 'openai,anthropic,gemini,perplexity'))
    p.add_argument('--repeats', type=int, default=int(os.getenv('REPEATS', '3')))
    p.add_argument('--max-calls', type=int, default=int(os.getenv('MAX_CALLS', '144')))
    p.add_argument('--confirm-paid', action='store_true', default=os.getenv('CONFIRM_PAID') == 'true')
    p.add_argument('--output', required=True)
    return p


if __name__ == '__main__':
    p = parser()
    try:
        print(json.dumps(execute(p.parse_args()), indent=2))
    except (StudyError, OSError, ValueError, KeyError) as error:
        p.exit(2, 'Workflow stopped: ' + str(error) + '\n')
