"""Study definitions: no category, engine, question or hypothesis constants."""
import hashlib
import itertools
import json
import pathlib
import re


class StudyError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise StudyError(message)


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load(path):
    path = pathlib.Path(path).resolve()
    cfg = json.loads(path.read_text())
    require(cfg.get('schema_version') == '1.0', 'Unsupported schema_version')
    for key in ['study_id', 'run_id', 'wave', 'focal_brand', 'category', 'market', 'context', 'codebook_version', 'questions', 'layers', 'groups', 'contrasts', 'attributes', 'output_root']:
        require(key in cfg, 'Missing configuration field: ' + key)
    for key in ['study_id', 'run_id']:
        require(re.fullmatch(r'[A-Za-z0-9_.-]+', cfg[key]) is not None, 'Unsafe ' + key)
    questions = cfg['questions']
    qids = [q['id'] for q in questions]
    require(bool(qids) and len(qids) == len(set(qids)), 'Questions must have unique IDs')
    for q in questions:
        require(q.get('kind') in ['discovery', 'branded'] and bool(q.get('text')), 'Question needs kind and exact text')
    for section in ['layers', 'groups', 'contrasts']:
        ids = [x['id'] for x in cfg[section]]
        require(len(ids) == len(set(ids)), 'Duplicate ' + section + ' IDs')
    require(bool(cfg['layers']), 'At least one layer required')
    for layer in cfg['layers']:
        for key in ['engines', 'question_ids', 'repeat_labels']:
            values = layer.get(key, [])
            require(bool(values) and len(values) == len(set(map(str, values))), 'Layer needs distinct ' + key)
        require(set(layer['question_ids']) <= set(qids), 'Layer refers to unknown question')
    for group in cfg['groups']:
        require(group.get('coverage') in ['planned_within_layer', 'fixed'], 'Group coverage must be explicit')
        require(bool(group['question_ids']) and len(group['question_ids']) == len(set(group['question_ids'])) and set(group['question_ids']) <= set(qids), 'Invalid group questions')
        kinds = {q['kind'] for q in questions if q['id'] in group['question_ids']}
        require(len(kinds) == 1, 'Separate discovery and branded groups')
    layer_ids = {l['id'] for l in cfg['layers']}
    for contrast in cfg['contrasts']:
        require(contrast.get('analysis_status') in ['prespecified', 'post_collection_exploratory'], 'Contrast needs analysis_status')
        a, b = contrast['baseline_questions'], contrast['comparison_questions']
        require(bool(a) and bool(b) and not set(a) & set(b), 'Contrast arms must be nonempty and disjoint')
        require(len(a) == len(set(a)) and len(b) == len(set(b)) and set(a + b) <= set(qids), 'Invalid contrast questions')
        require(set(contrast['layers']) <= layer_ids, 'Contrast refers to unknown layer')
    for id_ in qids + [l['id'] for l in cfg['layers']] + [e for l in cfg['layers'] for e in l['engines']] + [g['id'] for g in cfg['groups']] + [c['id'] for c in cfg['contrasts']]:
        require(isinstance(id_, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', id_) is not None, 'IDs must contain letters, numbers, _, . or -')
    require(len(cfg['attributes']) == len(set(cfg['attributes'])), 'Duplicate attributes')
    cfg['_path'] = path
    return cfg


def resolve(cfg, value):
    return (cfg['_path'].parent / value).resolve()


def planned(cfg):
    questions = {q['id']: q for q in cfg['questions']}
    for layer in cfg['layers']:
        for engine, qid, repeat in itertools.product(layer['engines'], layer['question_ids'], layer['repeat_labels']):
            q = questions[qid]
            yield dict(observation_id='/'.join([layer['id'], engine, qid, str(repeat)]),
                       layer=layer['id'], engine=engine, question_id=qid, repeat=str(repeat),
                       prompt_type=q['kind'], exact_prompt=cfg['context'] + '\n\n' + q['text'])


def semantic_fingerprint(cfg):
    """Study measurement identity; excludes dates, run IDs, filenames and comments."""
    keys = ['schema_version', 'category', 'market', 'focal_brand', 'context', 'codebook_version', 'attributes', 'groups', 'contrasts']
    value = {k: cfg[k] for k in keys}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
