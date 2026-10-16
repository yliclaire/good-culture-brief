"""Descriptive inventory of recovered citation attachments, not source influence."""
from urllib.parse import urlsplit
from .render import esc, table


def inventory(data):
    groups={}
    for oid,obs in data['observations'].items():
        if obs['quality']!='include':continue
        for url in obs['observed_urls']:
            parsed=urlsplit(url)
            if parsed.scheme not in ['http','https'] or not parsed.hostname:continue
            domain=parsed.hostname.lower().removeprefix('www.')
            key=(obs['layer'],domain)
            group=groups.setdefault(key,dict(layer=obs['layer'],domain=domain,observation_ids=set(),urls=set()))
            group['observation_ids'].add(oid);group['urls'].add(url)
    return [dict(layer=v['layer'],domain=v['domain'],observation_ids=sorted(v['observation_ids']),urls=sorted(v['urls'])) for _,v in sorted(groups.items())]


def render_inventory(data):
    rows=[]
    for item in inventory(data):
        records=[]
        for oid in item['observation_ids']:
            obs=data['observations'][oid]
            records.append('<a href="'+esc(obs['evidence_path'])+'">'+esc(obs['engine']+' / '+obs['question_id']+' / pass '+obs['repeat'])+'</a>')
        destinations='<details><summary>Recorded destination URLs</summary><ul>'+''.join('<li><a href="'+esc(url)+'" rel="noreferrer">'+esc(url)+'</a></li>' for url in item['urls'])+'</ul></details>'
        rows.append([esc(item['layer']),esc(item['domain']),str(len(item['observation_ids'])),', '.join(records)+destinations])
    return '<details class="source-inventory"><summary>Which sources were captured?</summary><p class="caption">Recovered attachments to selected claims only, grouped alphabetically within each collection layer. The answer count is the number of included answers with a recorded attachment to that domain in this mapped subset. An answer may cite several domains. These counts do not estimate overall source frequency, reliability or influence; links do not verify the underlying claims.</p>'+table(['Layer','Domain','Answers in mapped subset','Answer evidence and destination URLs'],rows)+'<p><a href="data/citation_source_inventory.json">Download the inventory and observation IDs</a></p></details>'
