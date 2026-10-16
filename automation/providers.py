"""Direct REST adapters. Keys are read only from environment at call time."""
import json
import os
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.parse import quote

KEYS = {'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY',
        'gemini': 'GEMINI_API_KEY', 'perplexity': 'PERPLEXITY_API_KEY'}


def specification(provider, model, prompt, limit=4096):
    message = [{'role': 'user', 'content': prompt}]
    if provider == 'openai':
        return 'https://api.openai.com/v1/responses', dict(model=model, input=prompt,
            store=False, max_output_tokens=limit, tools=[{'type': 'web_search'}],
            include=['web_search_call.action.sources'])
    if provider == 'anthropic':
        return 'https://api.anthropic.com/v1/messages', dict(model=model, messages=message,
            max_tokens=limit, tools=[dict(type='web_search_20250305', name='web_search', max_uses=5)])
    if provider == 'gemini':
        return 'https://generativelanguage.googleapis.com/v1beta/models/' + quote(model, safe='') + ':generateContent', dict(
            contents=[{'role': 'user', 'parts': [{'text': prompt}]}],
            tools=[{'google_search': {}}], generationConfig={'maxOutputTokens': limit})
    if provider == 'perplexity':
        return 'https://api.perplexity.ai/v1/sonar', dict(model=model, messages=message, max_tokens=limit)
    raise ValueError('Unsupported provider')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Provider redirect blocked; check adapter endpoint before retrying')


def post(provider, url, body):
    key = os.environ[KEYS[provider]]
    headers = {'Content-Type': 'application/json'}
    if provider == 'gemini':
        headers['x-goog-api-key'] = key
    elif provider == 'anthropic':
        headers.update({'x-api-key': key, 'anthropic-version': '2023-06-01'})
    else:
        headers['Authorization'] = 'Bearer ' + key
    request = Request(url, data=json.dumps(body).encode(), headers=headers, method='POST')
    with build_opener(NoRedirect).open(request, timeout=180) as response:
        return json.load(response)


def normalize(provider, raw):
    texts, citations, sources, searches, issues = [], [], [], [], []
    returned = raw.get('model', raw.get('modelVersion', 'undisclosed'))
    usage = raw.get('usage', raw.get('usageMetadata', {}))
    if provider == 'openai':
        for item in raw.get('output', []):
            if item.get('type') == 'web_search_call':
                searches.append(item)
                sources.extend(item.get('action', {}).get('sources', []))
                if item.get('status') != 'completed':
                    issues.append('search_not_completed')
            if item.get('type') == 'message':
                for part in item.get('content', []):
                    if part.get('type') == 'output_text':
                        citations.extend(dict(block_index=len(texts), **c) for c in part.get('annotations', []))
                        texts.append(part.get('text', ''))
        if raw.get('status') != 'completed':
            issues.append('response_not_completed')
    elif provider == 'anthropic':
        for part in raw.get('content', []):
            if part.get('type') == 'text':
                citations.extend(dict(block_index=len(texts), **c) for c in part.get('citations', []))
                texts.append(part.get('text', ''))
            if part.get('type') == 'server_tool_use':
                searches.append(part)
            if part.get('type') == 'web_search_tool_result':
                content = part.get('content', [])
                if isinstance(content, list):
                    sources.extend(content)
                else:
                    issues.append('search_error')
        if raw.get('stop_reason') != 'end_turn':
            issues.append('response_not_completed')
    elif provider == 'gemini':
        candidates = raw.get('candidates', [])
        if len(candidates) != 1:
            issues.append('unexpected_candidate_count')
        for candidate in candidates:
            for part in candidate.get('content', {}).get('parts', []):
                if 'text' in part and not part.get('thought'):
                    texts.append(part['text'])
            grounding = candidate.get('groundingMetadata', {})
            citations.extend(grounding.get('groundingSupports', []))
            sources.extend(grounding.get('groundingChunks', []))
            searches.extend(grounding.get('webSearchQueries', []))
            if candidate.get('finishReason') != 'STOP':
                issues.append('response_not_completed')
        if raw.get('promptFeedback', {}).get('blockReason'):
            issues.append('prompt_blocked')
    else:
        choices = raw.get('choices', [])
        if len(choices) != 1:
            issues.append('unexpected_choice_count')
        for item in choices:
            texts.append(item.get('message', {}).get('content', '') or '')
            if item.get('finish_reason') != 'stop':
                issues.append('response_not_completed')
        citations = [{'url': url, 'citation_index': i + 1} for i, url in enumerate(raw.get('citations', []))]
        sources = raw.get('search_results', [])
        # Sources imply retrieval evidence, not a known search invocation count.
    answer = '\n\n'.join(texts)
    if not answer.strip():
        issues.append('empty_answer')
    return dict(answer=answer, citations=citations, search_sources=sources,
        observed_search_metadata=searches, search_evidence_present=bool(searches or sources),
        usage=usage, returned_model=returned, issues=issues,
        status='needs_review' if issues else 'captured_pending_coding')
