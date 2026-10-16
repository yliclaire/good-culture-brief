"""Readable category preview generated from the same configuration and request plan."""
from collections import Counter
from .render import esc, table, engine_name


def render_preview(study, plan):
    jobs = plan['jobs']
    if plan['planned_requests'] != len(jobs):
        raise ValueError('Preview request count disagrees with jobs')
    grouped = {}
    for job in jobs:
        grouped.setdefault(job['question_id'], []).append(job)
    if set(grouped) != {q['id'] for q in study['questions']}:
        raise ValueError('Preview questions disagree with configuration')
    providers = sorted({job['engine'] for job in jobs})
    repeats = sorted({job['repeat'] for job in jobs})
    rows = []
    for question in study['questions']:
        batch = grouped[question['id']]
        prompts = {job['exact_prompt'] for job in batch}
        cells = Counter((job['engine'], job['repeat']) for job in batch)
        if len(prompts) != 1 or len(cells) != len(providers)*len(repeats) or any(n != 1 for n in cells.values()):
            raise ValueError('Preview must contain one exact prompt per provider/pass cell')
        rows.append([esc(question['kind'].title()), esc(question['id']), esc(next(iter(prompts))), str(len(batch))])
    brand = esc(study['focal_brand'])
    body = ('<h1>'+brand+' reuse example</h1>'
            '<p class="deck">A category change uses a new study profile. The collection and reporting pipeline stays the same.</p>'
            '<p class="notice">Preview only · '+str(len(jobs))+' planned requests · 0 collected answers. No footwear findings or live API compatibility claims.</p>'
            '<h2>Study specification</h2>'
            +table(['Field','Preview value'], [
                ['Brand / category',brand+' / '+esc(study['category'])],
                ['Proposed competitors',esc(', '.join(study['competitors']))],
                ['Market',esc(study['market'])],
                ['Attributes',esc(', '.join(study['attributes']))],
                ['Plan',str(len(grouped))+' prompts × '+str(len(providers))+' API providers × '+str(len(repeats))+' passes'],
                ['Providers',esc(', '.join(engine_name(p) for p in providers))]])
            +'<p class="caption">Competitors, prompts and attribute definitions require category review. The roster is a proposed comparison set.</p>'
            '<h2>Exact prompts</h2><p>Each row includes the shared shopping context and is repeated across providers and passes.</p>'
            +table(['Type','Question ID','Exact request','Calls'],rows)
            +'<h2>Reuse boundary</h2>'
            +table(['Change for the category','Reuse'],[
                ['Prompts, competitor roster, attributes and contrasts','Runner, provider adapters and evidence schema'],
                ['Reviewed coding and investment interpretation','Eligibility, denominators, metric calculations and report renderer'],
                ['Wave metadata, input hashes and narrative bindings','Registry validation, source kit and two GitHub workflows']])
            +'<p>Next: review the category profile, configure provider keys and model IDs, pilot live requests, then collect. Coding and interpretation require review and registration before a brief can build. API evidence forms a separate series from the browser baseline.</p>'
            '<p><a href="collection_plan.json">Download request plan (JSON)</a> · <a href="study.json">Study profile (JSON)</a> · <a href="manifest.json">Preview execution record (JSON)</a></p>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>'+brand+' reuse example</title><link rel="stylesheet" href="../../assets/report.css"></head>'
            '<body><main><p><a href="../../index.html#reuse">Methodology &amp; reuse</a></p>'+body+'</main></body></html>')
