"""Create a reviewable Pages package without copying the private source release.

This command prepares files only. It never uploads or publishes them.
"""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit

from .render import render, esc, table, engine_name
from .sources import inventory


PERSONAL_CONTEXT = re.compile(r"\bExampleName\s+in\s+ExampleTown\b|\bExampleName\b|\bExampleTown(?:,\s*NC)?\b", re.I)
PRIVATE_MARKERS = re.compile(r"/Users/|/private/var/|API_KEYS\.local|\bExampleName\b|\bExampleTown\b|[\w.+-]+@(?:gmail|hotmail|outlook)\.com|-----BEGIN .*PRIVATE KEY-----|\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}", re.I)
ASSETS = ('report.css', 'report.js', 'navigation.js', 'monitoring.js')
TABLES = ('brand_metrics.csv', 'denominators.csv', 'contributions.csv',
          'citation_coverage.csv', 'eligibility.csv', 'membership.csv', 'contrasts.csv')


def clean(value):
    if isinstance(value, str):
        return PERSONAL_CONTEXT.sub('[name and location withheld]', value)
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def public_data(original):
    data = clean(copy.deepcopy(original))
    data['study'].pop('output_root', None)
    for oid, obs in data['observations'].items():
        obs['context_excerpts'] = []
        obs['publication_note'] = ('Reviewed answer text; personal name/location references are withheld where present. '
                                   'Original interface captures and screenshots are retained in the private research repository.')
        if obs['quality'] == 'exclude':
            obs['transcript'] = 'Excluded incomplete answer. Original partial capture retained in the private audit archive.'
    # All counts, views, memberships and metric bindings remain unchanged.
    assert data['views'] == original['views']
    assert data['numbers'] == original['numbers']
    assert data['counts'] == original['counts']
    return data


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def document(title, body, parent=False):
    root = '../' if parent else ''
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>' + esc(title) + '</title>'
            '<link rel="stylesheet" href="' + root + 'assets/report.css"></head>'
            '<body><main><p><a href="' + root + 'index.html">Investment brief</a> · '
            '<a href="' + root + 'reviewer-guide.html">Pipeline &amp; reuse</a></p>' + body + '</main></body></html>')


def implementation_guide(repo_url):
    repo = esc(repo_url.rstrip('/'))
    return (
        '<h1>Pipeline &amp; reuse</h1>'
        '<p>Study configuration → collection → reviewed coding and narrative → registered inputs → metrics → HTML brief.</p>'
        '<p><a href="'+repo+'">Repository</a> · <a href="'+repo+'/blob/main/docs/REVIEWER_GUIDE.md">Research &amp; implementation</a> · <a href="'+repo+'/blob/main/docs/OPERATING_GUIDE.md">Run configuration</a></p>'
        '<h2>Execution</h2>'
        '<table><thead><tr><th>Workflow</th><th>Operation</th><th>Output</th></tr></thead><tbody>'
        '<tr><td><a href="'+repo+'/actions/workflows/collect-answers.yml">Collect engine answers</a></td><td><code>preview</code> / <code>collect</code></td><td>Exact request plan, or API answers and draft coding templates</td></tr>'
        '<tr><td><a href="'+repo+'/actions/workflows/build-brief.yml">Build investment brief</a></td><td><code>build-brief</code> / <code>build-browser</code></td><td>Validated brief and source kit, or measurement tables only</td></tr>'
        '</tbody></table>'
        '<p>Saved-study build: <code>reviewed_study = good_culture_browser_2026_q4</code>. No engine calls or API keys. Actions require write access or a fork with workflows enabled. Artifacts contain <code>run.zip</code>; <code>index.html</code> is the report entry point. Publication is a separate step.</p>'
        '<h2>Review contract</h2>'
        '<p>New collection requires approved coding, context/exclusion decisions and interpretation. Registered packages seal input hashes and bind the narrative to the evidence, configuration and calculation fingerprint. Build-time validation checks those bindings. Approved inputs must be committed before building.</p>'
        '<h2>Configuration changes</h2>'
        '<p>Quarterly runs retain comparable prompts, context, repeat plans and coding rules, with model/mode changes recorded. A category change replaces prompts, competitors, attributes and reviewed interpretation; collection, validation, calculations and rendering carry over.</p>'
        '<p>The <a href="demonstrations/birkenstock/collection_plan.json">Birkenstock plan</a> is an uncollected category example. API and browser evidence remain separate series. Live API collection is unpiloted; adapters use offline fixture tests.</p>'
        '<h2>Publication baseline</h2>'
        '<p>Sanitized answer text, coding, chart tables and citation attachments preserve the reviewed numeric results. Original interface captures remain private. Citation mapping is selective; factual verification is deferred. Monitoring scenarios are synthetic. <a href="PUBLICATION.md">Publication record</a>.</p>'
    )


def render_public(data, repo_url, print_mode=False):
    page = render(data, print_mode)
    replacements = {
        'code/README.md': 'reviewer-guide.html',
        'code/reviewed_studies/registry.json': repo_url + '/blob/main/reviewed_studies/registry.json',
        'methodology/README.md': 'methodology/index.html',
        'methodology/ASSIGNMENT_REVIEW.md': 'methodology/assignment.html',
        'methodology/QA_STATUS.md': 'methodology/verification.html',
        'methodology/MONITORING.md': 'methodology/monitoring.html',
    }
    for before, after in replacements.items():
        page = page.replace('href="' + before + '"', 'href="' + after + '"')
    page = page.replace('The truncated supplemental answer is excluded with a recorded reason and remains available for inspection.',
                        'The truncated supplemental answer is excluded with a recorded reason; its partial text is retained in the private audit archive.')
    page = page.replace('The downloaded brief works locally.',
                        'This website opens without GitHub access. Running or inspecting the private implementation requires repository access.')
    page = page.replace('Each brief includes the interactive report, a print version, captured answers, chart tables and the code and configuration used to build it. Unzip the package and open it locally; a public website is optional.',
                        'The website contains the interactive brief, print version, reviewed answer text and chart tables. The public repository contains the full source code, sanitized reproducible baseline and both reusable workflows. Original captures remain in a private archive.')
    page = page.replace('Create a private repository and put the contents of <code>code/</code> at its root.',
                        'Open the public implementation repository linked in this guide, or use its source kit to create your own copy.')
    page = page.replace('<head>', '<head><meta name="robots" content="noindex,nofollow">', 1)
    page = page.replace('<footer>', '<footer><p><a href="reviewer-guide.html">Pipeline &amp; reuse</a> · <a href="PUBLICATION.md">What this web edition contains</a></p>', 1)
    return page


def check_site(root):
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.links=[]; self.ids=set()
        def handle_starttag(self, tag, attrs):
            attrs=dict(attrs)
            if attrs.get('id'): self.ids.add(attrs['id'])
            for key in ('href', 'src'):
                if attrs.get(key): self.links.append(attrs[key])
    count=0
    for file in root.rglob('*.html'):
        parsed=Links(); parsed.feed(file.read_text())
        for link in parsed.links:
            parts=urlsplit(link)
            if parts.scheme in ('https','http','mailto'): continue
            if not parts.path:
                if parts.fragment and unquote(parts.fragment) not in parsed.ids:
                    raise ValueError('Missing section: '+str(file)+': '+link)
                continue
            target=(file.parent/unquote(parts.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                raise ValueError('Broken link: '+str(file)+': '+link)
            count+=1
    for file in root.rglob('*'):
        if not file.is_file(): continue
        if file.suffix.lower() in ('.png','.jpg','.jpeg','.zip','.pdf'):
            raise ValueError('Unexpected binary in public export: '+str(file))
        text=file.read_text()
        if PRIVATE_MARKERS.search(text):
            raise ValueError('Private marker requires review in '+str(file.relative_to(root)))
    return dict(html_files=len(list(root.rglob('*.html'))), local_links_checked=count,
                private_marker_scan='passed; pattern checks are not a guarantee of anonymity',
                metric_parity='exact views, numbers and counts unchanged',
                actual_browser_review='pending', publication='not performed by exporter')


def build(release, output, site_url, repo_url):
    source=Path(release).resolve(); out=Path(output).resolve()
    if out.exists(): raise ValueError('Choose a new web-export directory')
    manifest=json.loads((source/'release_manifest.json').read_text())
    for name,digest in manifest['outputs'].items():
        file=(source/name).resolve()
        if not file.is_relative_to(source) or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
            raise ValueError('Source release integrity check failed: '+name)
    original=json.loads((source/'data/report_data.json').read_text())
    data=public_data(original)
    out.mkdir(parents=True)
    (out/'assets').mkdir()
    for name in ASSETS:
        content=(source/'assets'/name).read_text()
        content=content.replace('Original capture, screenshot when available, and hashes', 'Reviewed answer and recorded source URLs')
        if name=='report.js':
            content=content.replace("esc(o.transcript)", "esc(o.transcript)+'<p class=\"caption\">'+esc(o.publication_note)+'</p>'")
        (out/'assets'/name).write_text(content)
    write_json(out/'data/report_data.json', data)
    write_json(out/'data/citation_source_inventory.json', dict(scope='Recovered selected-claim attachments, not source influence',rows=inventory(data)))
    for name in TABLES:
        target=out/'data/chart_tables'/name; target.parent.mkdir(exist_ok=True)
        target.write_text(clean((source/'data/chart_tables'/name).read_text()))
    for name in ('monitoring_baseline.json','monitoring_demo.json'):
        write_json(out/'data'/name, clean(json.loads((source/'data'/name).read_text())))
    (out/'configuration').mkdir()
    write_json(out/'configuration/study.json', data['study'])
    cfg=json.loads((source/'configuration/birkenstock.example.json').read_text())
    for key in ('inputs','output_root'): cfg.pop(key,None)
    write_json(out/'configuration/birkenstock.example.json',clean(cfg))
    for name in ('collection_plan.json','study.json'):
        value=json.loads((source/'demonstrations/birkenstock'/name).read_text())
        write_json(out/'demonstrations/birkenstock'/name,clean(value))
    write_json(out/'demonstrations/birkenstock/manifest.json', dict(status='preview_only',live_requests=0,source='Birkenstock category design; not collected findings'))
    (out/'evidence').mkdir()
    rows=[]
    for oid,obs in data['observations'].items():
        urls=''.join('<li><a href="'+esc(u)+'" rel="noreferrer">'+esc(u)+'</a></li>' for u in obs['observed_urls'] if urlsplit(u).scheme in ('http','https'))
        body='<h1>'+esc(engine_name(obs['engine'])+' · '+obs['question_id']+' · pass '+str(obs['repeat']))+'</h1>'
        body+='<p class="metadata">'+esc(oid+' · '+obs['timestamp']+' · '+obs['quality'])+'</p>'
        body+='<p>'+esc(obs['quality_reason'])+'</p><h2>Exact prompt</h2><p class="transcript">'+esc(obs['prompt'])+'</p>'
        body+='<p>'+esc('Model: '+obs['model']+' | Mode: '+obs['mode']+' | Sign-in: '+obs['sign_in'])+'</p>'
        body+='<p>'+esc('Recorded context flags: '+(', '.join(obs['flags']) or 'None; not proof of neutrality'))+'</p>'
        body+='<h2>Reviewed answer</h2><p class="caption">'+esc(obs['publication_note'])+' Product claims are not independently fact-verified.</p><div class="transcript">'+esc(obs['transcript'])+'</div>'
        body+='<h2>Recorded source destinations</h2><p>'+str(obs['mapped_claims'])+' / '+str(obs['selected_claims'])+' selected claims mapped; incomplete citation coverage.</p><ul>'+urls+'</ul>'
        (out/obs['evidence_path']).write_text(document(oid,body,True))
        if obs['quality']=='include':
            rows.append([esc(engine_name(obs['engine'])),esc(obs['question_id']),esc(obs['repeat']),'<a href="'+Path(obs['evidence_path']).name+'">Read answer</a>'])
    (out/'evidence/index.html').write_text(document('Included answer evidence','<h1>Included answer evidence</h1><p>'+str(data['counts']['included'])+' included answers. '+str(data['counts']['excluded'])+' excluded from complete-answer measures; originals are retained privately. Personal name/location references are withheld in this web edition.</p>'+table(['Engine','Question','Pass','Answer'],rows),True))
    (out/'reviewer-guide.html').write_text(document('Pipeline & reuse', implementation_guide(repo_url)))
    (out/'methodology').mkdir()
    method='<h1>Study method</h1>'+''.join('<p>'+esc(p)+'</p>' for p in data['narrative']['methods'])
    method+='<p>Trace each view through denominator IDs, membership and contribution tables, then to the reviewed answer ID. Numeric views and memberships are unchanged from the reviewed source release. Names/location phrases are withheld; originals are retained privately.</p><p><a href="../data/report_data.json">Report data</a> · <a href="../data/chart_tables/brand_metrics.csv">Brand metrics</a> · <a href="../data/chart_tables/denominators.csv">Denominators</a> · <a href="../data/chart_tables/membership.csv">Membership</a> · <a href="../data/chart_tables/contributions.csv">Contributions</a></p>'
    (out/'methodology/index.html').write_text(document('Study method',method,True))
    for name,title,original_name in [('assignment','Assignment coverage','ASSIGNMENT_REVIEW.md'),('monitoring','Quarterly comparison contract','MONITORING.md')]:
        body='<h1>'+title+'</h1><pre class="transcript">'+esc(clean((source/'methodology'/original_name).read_text()))+'</pre>'
        (out/'methodology'/f'{name}.html').write_text(document(title,body,True))
    (out/'methodology/verification.html').write_text(document('Verification status','<h1>Verification status</h1><p>The underlying benchmark passed offline tests and a GitHub-hosted brief build before this publication export. This web export checks exact metric parity, local links and selected private-data patterns. Browser, keyboard, responsive and print review of this web edition remain pending. Live API collection has not been piloted.</p>',True))
    for name,print_mode in [('index.html',False),('print.html',True)]:
        (out/name).write_text(render_public(data,repo_url,print_mode))
    (out/'.nojekyll').write_text('')
    (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    (out/'PUBLICATION.md').write_text('# Web edition contents\n\nPrepared for public website review; this command has not published it.\n\nIncludes the investment brief, '+str(data['counts']['included'])+' reviewed answers, exclusion audit placeholders, unchanged numeric views and chart tables, recovered source URLs and synthetic demonstrations. Name/location phrases are withheld. Original interface captures, screenshots and account context remain in a private archive. The public submission repository contains the code, sanitized reproducible inputs and both executable workflows.\n\nAnyone with access to a public website can inspect all HTML, JavaScript and embedded data. The robots directive discourages indexing; it is not access control.\n')
    (out/'README.md').write_text('# Investment brief | Website export\n\n[Interactive brief]('+site_url+') · [Print version]('+site_url+'print.html) · [Pipeline reference]('+site_url+'reviewer-guide.html)\n\nStatic publication export. Deploy separately; this command does not publish. Source code, reviewed inputs and workflows: [implementation repository]('+repo_url+').\n\nThe baseline contains '+str(data['counts']['included'])+' included answers and '+str(data['counts']['excluded'])+' excluded capture. Numeric views and memberships match the reviewed release. Original interface captures and personal references are withheld; see [publication record](PUBLICATION.md).\n')
    write_json(out/'release_manifest.json',dict(status='checking_not_published'))
    checks=check_site(out)
    write_json(out/'web_checks.json',checks)
    files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}
    write_json(out/'release_manifest.json',dict(status='prepared_not_published',source_fingerprint=data['source_fingerprint'],site_url=site_url,implementation_repository=repo_url,checks=checks,files=files))
    return dict(output=str(out),files=len(files)+1,**checks)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release',required=True);p.add_argument('--output',required=True)
    p.add_argument('--site-url',default='https://yliclaire.github.io/good-culture-brief/')
    p.add_argument('--repo-url',default='https://github.com/yliclaire/good-culture-brief')
    a=p.parse_args()
    print(json.dumps(build(a.release,a.output,a.site_url,a.repo_url),indent=2))
