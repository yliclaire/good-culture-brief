"""Registered reviewed study -> checked report data -> offline brief and reproducible ZIP."""
import csv
import html
import json
import os
from pathlib import Path
import shutil
import zipfile
from urllib.parse import urlsplit
from benchmark_tool.config import require, load, sha
from benchmark_tool.evidence import load_evidence, norm
from benchmark_tool.cli import build as build_metrics
from .export import export
from .render import render, esc, table, engine_name

ROOT=Path(__file__).resolve().parents[1]


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def within(path):
    require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'Registry paths must be relative and cannot traverse directories')
    value=(ROOT/path).resolve()
    require(value.is_relative_to(ROOT) and value.is_file(),'Missing or unsafe registered input: '+str(path))
    return value


def registered(study_id):
    registry=json.loads((ROOT/'reviewed_studies/registry.json').read_text())
    require(study_id in registry,'Study is not registered with reviewed evidence: '+study_id)
    entry=registry[study_id]
    review=within(entry['review_manifest'])
    require(sha(review)==entry['review_manifest_sha256'],'Review manifest changed; re-review and register its new hash')
    manifest=json.loads(review.read_text())
    require(manifest.get('status')=='reviewed' and manifest.get('reviewer') and manifest.get('reviewed_at'),'Study review is incomplete')
    for name,digest in manifest['files'].items():
        require(sha(within(name))==digest,'Reviewed input changed: '+name)
    cfg=load(within(entry['config']))
    narrative=json.loads(within(entry['narrative']).read_text())
    for name in [entry['config'],entry['narrative']]:
        require(name in manifest['files'],'Unsealed study or narrative input')
    return cfg,narrative,manifest,entry


def evidence_pages(out,data,source,cfg):
    links=[]
    observations_root=(cfg['_path'].parent/cfg['inputs']['observations']).resolve().parent
    for oid,o in data['observations'].items():
        raw=source['observations'][oid]
        originals=[]
        publication=raw.get('capture_format')=='sanitized_browser_export'
        for field,label in [('evidence_file','Sanitized answer record' if publication else 'Original capture'),('screenshot','Screenshot')]:
            value=raw.get(field)
            if not value:
                continue
            p=Path(value)
            if not p.is_absolute():
                p=(observations_root/p).resolve()
            require(p.is_relative_to(ROOT),'Evidence must be inside the portable repository')
            relative='../code/'+p.relative_to(ROOT).as_posix()
            originals.append('<p><a href="'+esc(relative)+'">'+label+'</a> · SHA-256 <code>'+sha(p)+'</code></p>')
        urls=''.join('<li><a href="'+esc(url)+'" rel="noreferrer">'+esc(url)+'</a></li>' for url in o['observed_urls'] if urlsplit(url).scheme in ['http','https'])
        body='<h1>'+esc(engine_name(o['engine'])+' · '+o['question_id']+' · pass '+o['repeat'])+'</h1><p class="metadata">'+esc(oid+' · '+o['timestamp']+' · '+o['quality'])+'</p><p>'+esc(o['quality_reason'])+'</p><h2>Exact prompt</h2><p class="transcript">'+esc(o['prompt'])+'</p><p class="metadata">'+esc('Model: '+o['model']+' | Mode: '+o['mode']+' | Sign-in: '+o['sign_in'])+'</p><p>'+esc('Visible flags: '+(', '.join(o['flags']) or 'None recorded; not proof of neutrality'))+'</p><h2>Reviewed transcript / retained defective capture</h2><p>Engine statements are not independently fact-verified.</p><div class="transcript">'+esc(o['transcript'])+'</div><details><summary>Full raw captured text, including interface content</summary><pre class="transcript">'+esc(raw['raw_text'])+'</pre></details><h2>Original capture and lineage</h2>'+''.join(originals)+'<p>Archived originals may contain account/interface context. They remain distinct from the reviewed answer boundary.</p><h2>Observed mapped source destinations</h2><p>'+str(o['mapped_claims'])+' / '+str(o['selected_claims'])+' selected claims mapped. These are attachment records, not verified factual support or a complete URL inventory.</p><ul>'+urls+'</ul>'
        if publication:
            body=body.replace('Full raw captured text, including interface content','Publication audit text, including separately labeled coding excerpts')
            body=body.replace('Original capture and lineage','Publication record and lineage')
            body=body.replace('Archived originals may contain account/interface context. They remain distinct from the reviewed answer boundary.','This is a sanitized publication derivative. Original screenshots and interface captures are retained privately. Names/location references are withheld; coding/context flags remain unchanged. The linked JSON distinguishes reviewed answer text from retained audit excerpts.')
        page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(oid)+'</title><link rel="stylesheet" href="../assets/report.css"><body><main><p><a href="../index.html#methods">Back to brief</a> · <a href="index.html">All answers</a></p>'+body+'</main></body></html>'
        (out/o['evidence_path']).parent.mkdir(parents=True,exist_ok=True)
        (out/o['evidence_path']).write_text(page)
        links.append([esc(engine_name(o['engine'])),esc(o['question_id']),esc(o['repeat']),esc(o['quality']),'<a href="'+Path(o['evidence_path']).name+'">Read complete capture</a>'])
    (out/'evidence/index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Evidence index</title><link rel="stylesheet" href="../assets/report.css"><body><main><h1>Complete captured evidence</h1><p><a href="../index.html">Back to brief</a></p>'+table(['Engine','Question','Pass','Quality','Evidence'],links)+'</main></body></html>')


def validate_release(out,data):
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):
            super().__init__();self.links=[];self.ids=set()
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if a.get('id'): self.ids.add(a['id'])
            for key in ['href','src']:
                if a.get(key): self.links.append(a[key])
    checked=0
    for p in list((out/'evidence').glob('*.html'))+list((out/'demonstrations').rglob('*.html'))+[out/'index.html',out/'print.html']:
        parser=Links();parser.feed(p.read_text())
        for link in parser.links:
            if urlsplit(link).scheme in ['https','http','mailto']:
                continue
            if link.startswith('#'):
                require(link[1:] in parser.ids,'Broken section anchor: '+link)
                continue
            target=(p.parent/link.split('#',1)[0]).resolve()
            require(target.is_relative_to(out.resolve()) and target.is_file(),'Broken local asset: '+link)
            checked+=1
    for v in data['views'].values():
        require(len(v['observation_ids'])==v['n'],'View membership count disagrees')
        if v['status']=='ready' and v['scope']=='question':
            require(abs(sum(r['first_choice_credit_sum'] for r in v['rows'])+v['no_lead_n']-v['n'])<1e-8,'First-choice partition does not conserve answers')
        if v['status']!='ready':
            require(not v['rows'],'Unavailable values must not contain plotted zero estimates')
    script=(out/'assets/report.js').read_text()
    require(not any(token in script for token in ['fetch(','XMLHttpRequest','WebSocket','https://']),'Report must work offline')
    return dict(local_links_checked=checked,all_observation_pages=len(data['observations']),view_states=len(data['views']),
        numerical_and_link_checks='passed',actual_browser_accessibility_and_print='pending',hosted_GitHub_run=('verified_prior_run: '+data['narrative']['workflow_host']['validated_run_url']) if data['narrative'].get('workflow_host',{}).get('validated_run_url') else 'pending')


def build_brief(study_id,output):
    cfg,narrative,review,entry=registered(study_id)
    out=Path(output).resolve()
    require(not out.exists(),'Choose a new report release directory; earlier releases are preserved')
    require(not (out.parent/(out.name+'.zip')).exists(),'Release ZIP already exists')
    source=load_evidence(cfg)
    require(cfg.get('study_status')=='ready','Study is not ready for analysis')
    require(len(source['coding'])==len(source['observations']) and all(c['review_status']=='approved' for c in source['coding'].values()),'Coding approval is incomplete')
    require({q['kind'] for q in cfg['questions']}=={'discovery','branded'}, 'This investment-brief template requires reviewed discovery and branded questions. A narrower custom study can still generate measurement outputs.')
    from .export import fingerprint
    require(narrative.get('source_fingerprint')==fingerprint(cfg,source),'Narrative fingerprint does not match reviewed evidence')
    metric_cfg=dict(cfg,run_id='chart_tables',output_root=str(out/'data'))
    build_metrics(metric_cfg)
    data=export(cfg,source,out/'data/chart_tables',narrative)
    save(out/'data/report_data.json',data)
    from .sources import inventory
    save(out/'data/citation_source_inventory.json',dict(scope='recovered citation attachments to selected claims; not representative source frequency or influence',rows=inventory(data)))
    if narrative.get('decision_support'):
        from .monitoring import demo
        monitoring=demo(data)
        save(out/'data/monitoring_demo.json',monitoring)
        save(out/'data/monitoring_baseline.json',monitoring['baseline'])
        from automation.run import execute, parser
        execute(parser().parse_args(['preview','--study','birkenstock','--output',str(out/'demonstrations/birkenstock')]))
        from .reuse import render_preview
        preview_root=out/'demonstrations/birkenstock'
        (preview_root/'index.html').write_text(render_preview(json.loads((preview_root/'study.json').read_text()),json.loads((preview_root/'collection_plan.json').read_text())))
    (out/'assets').mkdir()
    for name in ['report.css','report.js','navigation.js','monitoring.js']:
        shutil.copyfile(Path(__file__).parent/name,out/'assets'/name)
    # Source kit is allowlisted and selected-study inputs remain byte-identical.
    code=out/'code';code.mkdir()
    for directory in ['automation','benchmark_tool','report','.github','tests']:
        shutil.copytree(ROOT/directory,code/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if (ROOT/'docs').is_dir():
        shutil.copytree(ROOT/'docs',code/'docs')
        # The reviewer walkthrough links these checked snapshots. Include them
        # alongside the source so the downloaded guide has no missing files.
        for relative in ['report_data.json','chart_tables/contributions.csv','chart_tables/denominators.csv','chart_tables/membership.csv']:
            target=code/'data'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(out/'data'/relative,target)
    for name in ['README.md','VALIDATION.md','providers.json','.gitignore']:
        shutil.copyfile(ROOT/name,code/name)
    if (ROOT/'WORKSHOP_NOTES.md').is_file():
        shutil.copyfile(ROOT/'WORKSHOP_NOTES.md',code/'WORKSHOP_NOTES.md')
    source_files=set(review['files'])|{entry['review_manifest']}
    for relative in sorted(source_files):
        p=within(relative)
        require(p.name not in ['API_KEYS.local.txt','.env','.env.local'],'Credential files cannot be released')
        dst=code/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    save(code/'reviewed_studies/registry.json',{study_id:entry})
    for name in ['good_culture.json','birkenstock.example.json']:
        (code/'studies').mkdir(exist_ok=True)
        if not (code/'studies'/name).exists(): shutil.copyfile(ROOT/'studies'/name,code/'studies'/name)
    (out/'configuration').mkdir()
    save(out/'configuration/study.json',{k:v for k,v in cfg.items() if not k.startswith('_')})
    shutil.copyfile(ROOT/'studies/birkenstock.example.json',out/'configuration/birkenstock.example.json')
    evidence_pages(out,data,source,cfg)
    (out/'START_HERE.txt').write_text('''Start with index.html

Extract the entire ZIP before opening index.html in your browser. Keep its supporting folders together.

Investment brief: findings, investment implications and prioritized diligence.
Explore the benchmark: shopper needs, competitors, engine comparisons and answer evidence.
Methodology & reuse: study choices, source limitations, workflow links and demonstrations.

print.html is the print-friendly companion. Source code and reviewed inputs are in code/.
GitHub access and API keys are not needed to read this report or rebuild the saved study.
For reuse, see code/README.md. New API collection needs your own keys/models and subsequent review.

The monitoring next-wave examples are synthetic. The Birkenstock example is a collection preview, not footwear findings.
''')
    (out/'index.html').write_text(render(data))
    (out/'print.html').write_text(render(data,True))
    (out/'methodology').mkdir()
    guide='''# Methodology and reproduction

Start with index.html. print.html is the print-friendly companion. All presentation data are embedded; the essential report needs no network or server.

The unit is an engine x exact prompt x collection pass. Discovery and branded questions, main and supplemental layers, and baseline versus fixed matched context remain separate. Questions receive equal weights. Explicit equal overall ties receive 1/k first-choice credit. Conditional, unclear and no-recommendation answers stay in the denominator without first-choice credit. First mention is textual order. Missing comparisons stay unavailable, not zero. Repeats are not independent consumers.

Trace a view through its denominator_ids to chart_tables/denominators.csv and membership.csv, then observation_id and contributions.csv, then the evidence page. The report_data.json includes each view's membership and exact metric binding. Selected excerpts are illustrative; the full contributing answer list is available. Claims/source attachments are not independently fact-verified. Same-assistant review is not independent human coding agreement.

The code folder contains the selected study’s source inputs, evidence records, registered review manifest, calculation/export/render code and both GitHub workflows. The public Good Culture baseline uses explicitly labeled sanitized publication derivatives; original interface captures and screenshots are retained privately. Relative paths avoid dependence on the author’s machine.

From code/, reproduce this release with:

    python automation/run.py build-brief --reviewed-study STUDY_ID --output NEW_OUTPUT_FOLDER

Use a new output folder. No API credentials are needed. GitHub: open Build investment brief, select build-brief and the same reviewed-study registry ID. Collection is a separate operation; new responses require coding and narrative review before registration. Do not reuse this study's narrative for another brand or wave. The review manifest and narrative fingerprint are checked before rendering.
'''.replace('STUDY_ID',study_id)
    (out/'methodology/README.md').write_text(guide)
    shutil.copyfile(Path(__file__).parent/'assignment_review.md',out/'methodology/ASSIGNMENT_REVIEW.md')
    shutil.copyfile(Path(__file__).parent/'monitoring_guide.md',out/'methodology/MONITORING.md')
    (out/'methodology/QA_STATUS.md').write_text('# Verification status\n\nAutomated source, numerical, membership, narrative-binding and local-link checks are performed at build time. Offline runtime dependencies are checked statically. Actual browser/keyboard/responsive/print visual review and GitHub-hosted execution remain pending until performed; this release is for review, not labelled submission-ready. No paid requests or new collection were made.\n')
    if narrative.get('workflow_host',{}).get('validated_run_url'):
        qa=out/'methodology/QA_STATUS.md'
        text=qa.read_text().replace('and GitHub-hosted execution remain pending until performed','remain pending until performed')
        qa.write_text(text+'\nA prior GitHub-hosted brief build is verified: '+narrative['workflow_host']['validated_run_url']+'\n')
    save(out/'release_manifest.json',dict(status='checking'))
    checks=validate_release(out,data)
    save(out/'data/build_checks.json',checks)
    files={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}
    manifest=dict(status='built_for_review_browser_QA_pending',study_id=cfg['study_id'],reviewed_study=study_id,wave=cfg['wave'],
        source_fingerprint=data['source_fingerprint'],review_manifest_sha256=entry['review_manifest_sha256'],counts=data['counts'],
        code_revision=os.getenv('GITHUB_SHA','local'),outputs=files,checks=checks,
        interpretation_review='Same-assistant reviewed synthesis; not independent human agreement',new_collection=False,factual_verification='deferred')
    save(out/'release_manifest.json',manifest)
    archive=out.parent/(out.name+'.zip')
    require(not archive.exists(),'Release ZIP already exists')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out).as_posix())
    return dict(entry_point=str(out/'index.html'),print_companion=str(out/'print.html'),archive=str(archive),counts=data['counts'],checks=checks)
