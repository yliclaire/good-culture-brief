"""Adapter for reviewed v2 tables and normalized saved browser observations."""
import csv
import json
import pathlib
import re
from .config import require, resolve, sha, planned


def readcsv(path):
    with pathlib.Path(path).open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def writecsv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else [])
    with pathlib.Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def array(row, key):
    value = json.loads(row.get(key) or '[]')
    require(isinstance(value, list) and all(isinstance(x, str) for x in value) and len(value) == len(set(value)), 'Invalid array: ' + key)
    return value


def load_evidence(cfg):
    spec = cfg.get('inputs', {})
    require(spec.get('adapter') == 'reviewed_v2', 'Configure inputs.adapter=reviewed_v2 after collection/review')
    paths = {k: resolve(cfg, spec[k]) for k in ['observations', 'coding', 'brands', 'claims']}
    for path in paths.values():
        require(path.is_file(), 'Missing input: ' + str(path))
    hashes = {str(p): sha(p) for p in paths.values()}
    warnings = []
    # A legacy run records raw evidence, review inputs and rule hashes. Check it
    # before importing its normalized observations, without modifying the run.
    if spec.get('upstream_manifest'):
        p = resolve(cfg, spec['upstream_manifest'])
        manifest = json.loads(p.read_text())
        hashes[str(p)] = sha(p)
        for name, digest in manifest['inputs'].items():
            source = pathlib.Path(name)
            require(source.is_file() and sha(source) == digest, 'Stale upstream provenance: ' + name)
            hashes[name] = digest
    for value in spec.get('provenance_files', []):
        p = resolve(cfg, value)
        require(p.is_file(), 'Missing provenance: ' + str(p))
        hashes[str(p)] = sha(p)
    observations = [json.loads(line) for line in paths['observations'].read_text().splitlines() if line.strip()]
    byid = {}
    cells = set()
    expected = {o['observation_id']: o for o in planned(cfg)}
    for row in observations:
        oid = row['observation_id']
        require(oid not in byid and oid in expected, 'Duplicate/unplanned observation: ' + oid)
        cell = (row['layer'], row['engine'], row['question_id'], str(row['repeat']))
        require(cell not in cells, 'Duplicate observation cell')
        cells.add(cell)
        require(oid == '/'.join(cell), 'Observation ID and cell disagree')
        require(row['exact_prompt'].replace('\r\n', '\n') == expected[oid]['exact_prompt'], 'Prompt differs from study: ' + oid)
        require(bool(row.get('raw_text')) and bool(row.get('captured_at_utc')), 'Missing raw answer or capture timestamp: ' + oid)
        publication = row.get('capture_format') == 'sanitized_browser_export'
        if publication:
            provenance = row.get('publication_provenance', {})
            require(provenance.get('kind') == 'sanitized_browser_export' and
                    re.fullmatch(r'[a-f0-9]{64}', provenance.get('original_capture_sha256', '')) and
                    bool(provenance.get('redaction_note')), 'Publication derivative lacks provenance: ' + oid)
            require(cfg.get('publication', {}).get('evidence_kind') == 'sanitized_browser_export',
                    'Sanitized browser evidence requires an explicit publication configuration')
        fields = ['evidence_file'] if row.get('capture_format') == 'direct_provider_api' or publication else ['evidence_file', 'screenshot']
        for field in fields:
            require(bool(row.get(field)), 'Missing evidence pointer: ' + oid)
            path = pathlib.Path(row[field])
            if not path.is_absolute():
                path = paths['observations'].parent / path
            require(path.is_file(), 'Evidence file unavailable: ' + str(path))
            hashes[str(path.resolve())] = sha(path)
        byid[oid] = row
    coded = readcsv(paths['coding'])
    require(len({c['observation_id'] for c in coded}) == len(coded), 'Duplicate coding IDs')
    require({c['observation_id'] for c in coded} <= set(byid), 'Coding without captured observation')
    cmap = {c['observation_id']: c for c in coded}
    for value in spec.get('overrides', []):
        p = resolve(cfg, value)
        hashes[str(p)] = sha(p)
        for override in readcsv(p):
            if override['observation_id'] not in cmap:
                continue
            require(override['field'] in cmap[override['observation_id']] and override['field'] != 'observation_id', 'Invalid override field')
            require(all(override.get(k) for k in ['reason', 'reviewer', 'reviewed_at_utc']), 'Override lacks provenance')
            v = json.loads(override['value_json'])
            cmap[override['observation_id']][override['field']] = json.dumps(v) if isinstance(v, list) else str(v)
    for oid, c in cmap.items():
        require(c['review_status'] in ['pending', 'needs_review', 'approved'], 'Unknown review status')
        if c['review_status'] != 'approved':
            continue
        require(c['quality_decision'] in ['include', 'exclude'], 'Missing quality decision')
        require(all(c.get(k) for k in ['reviewer', 'reviewed_at_utc', 'quality_reason']), 'Review lacks provenance: ' + oid)
        if c['quality_decision'] == 'exclude':
            continue
        mentioned = set(array(c, 'mentioned_brands_json'))
        recommended = set(array(c, 'recommended_brands_json'))
        leading = set(array(c, 'first_recommendations_json'))
        require(leading <= recommended <= mentioned, 'Invalid recommendation hierarchy: ' + oid)
        require(set(array(c, 'reason_tags_json')) <= set(cfg['attributes']), 'Attribute not in configured taxonomy: ' + oid)
        require(set(array(c, 'substitutes_json')) <= mentioned, 'Substitute absent from mentioned brands')
        array(c, 'context_flags_json')
        require(c.get('context_review_status') == 'reviewed', 'Context not reviewed: ' + oid)
        lead_status = c['overall_lead_status']
        require(lead_status in ['single', 'tied', 'conditional_only', 'no_recommendation', 'unclear'], 'Invalid overall lead status')
        require((lead_status == 'single' and len(leading) == 1) or (lead_status == 'tied' and len(leading) >= 2) or (lead_status in ['conditional_only', 'no_recommendation', 'unclear'] and not leading), 'Lead status disagrees with coded brands')
        require(lead_status != 'no_recommendation' or not recommended, 'No-recommendation answer has recommendations')
        require(lead_status != 'conditional_only' or bool(recommended), 'Conditional-only answer has no recommended brands')
        require((not mentioned and not c['first_brand_mentioned']) or c['first_brand_mentioned'] in mentioned, 'First mention invalid')
        require(bool(c.get('cleaned_answer')) and bool(c.get('supporting_excerpt')) and norm(c['supporting_excerpt']) in norm(byid[oid]['raw_text']), 'Answer/excerpt unavailable: ' + oid)
        flags = array(c, 'context_flags_json')
        excerpts = json.loads(c.get('context_evidence_json') or '[]')
        require(not flags or bool(excerpts), 'Context flag lacks excerpt')
        require(all(norm(x) in norm(byid[oid]['raw_text']) for x in excerpts), 'Context excerpt absent')
    brands, claims = readcsv(paths['brands']), readcsv(paths['claims'])
    pairs = set()
    for b in brands:
        pair = (b['observation_id'], b['brand'])
        require(pair not in pairs and pair[0] in byid, 'Duplicate/orphan brand row')
        pairs.add(pair)
        require(norm(b['mention_evidence']) and norm(b['mention_evidence']) in norm(byid[pair[0]]['raw_text']), 'Brand evidence absent')
    for oid, c in cmap.items():
        if c['review_status'] != 'approved' or c['quality_decision'] != 'include':
            continue
        bb = [b for b in brands if b['observation_id'] == oid]
        require({b['brand'] for b in bb} == set(array(c, 'mentioned_brands_json')), 'Brand/coding coverage differs')
        require(all(b['review_status'] == 'approved' for b in bb), 'Unreviewed brand rows')
        rec = {b['brand'] for b in bb if b['recommendation_type'] in ['leading', 'co_leading', 'conditional', 'alternative']}
        lead = {b['brand'] for b in bb if b['recommendation_type'] in ['leading', 'co_leading']}
        require(rec == set(array(c, 'recommended_brands_json')) and lead == set(array(c, 'first_recommendations_json')), 'Brand roles differ from coding')
    require(len({c['claim_id'] for c in claims}) == len(claims), 'Duplicate claim IDs')
    for claim in claims:
        oid = claim['observation_id']
        require((oid, claim['brand']) in pairs, 'Orphan claim')
        require(norm(claim['evidence_excerpt']) and norm(claim['evidence_excerpt']) in norm(byid[oid]['raw_text']), 'Claim excerpt absent')
        require(claim['citation_status'] in ['not_mapped', 'engine_citation_mapped', 'no_visible_citation', 'unavailable'], 'Unknown citation status')
        urls = array(claim, 'observed_source_urls_json')
        require(claim['citation_status'] != 'engine_citation_mapped' or bool(urls), 'Mapped citation has no URL')
        if oid in cmap and cmap[oid]['review_status'] == 'approved' and cmap[oid]['quality_decision'] == 'include':
            require(claim['review_status'] == 'approved', 'Unreviewed claim rows')
    if spec.get('citation_review'):
        p = resolve(cfg, spec['citation_review'])
        hashes[str(p)] = sha(p)
        reviews = json.loads(p.read_text())
        indexed_claims = {c['claim_id']: c for c in claims}
        for review in reviews:
            p = pathlib.Path(review['evidence_file'])
            if not p.is_absolute():
                p = paths['observations'].parent / p
            require(p.is_file() and sha(p) == review['evidence_sha256'], 'Citation attachment evidence changed')
            hashes[str(p)] = sha(p)
            claim = indexed_claims[review['claim_id']]
            require(claim['observation_id'] == review['observation_id'] and set(array(claim, 'observed_source_urls_json')) == set(review['urls']), 'Citation review mismatch')
    if not spec.get('upstream_manifest'):
        warnings.append('No upstream collection manifest: capture completeness/model/privacy setup rely on the supplied evidence pointers and explicit review.')
    return dict(observations=byid, coding=cmap, brands=brands, claims=claims, hashes=hashes, warnings=warnings)
