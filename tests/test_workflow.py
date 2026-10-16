import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from automation.run import parser, study, execute, verify_baseline
from automation.providers import normalize, specification
from benchmark_tool.config import StudyError, planned
from benchmark_tool.evidence import readcsv


class WorkflowTests(unittest.TestCase):
    def args(self, operation='preview', *extra):
        return parser().parse_args([operation, '--output', 'unused', *extra])

    def test_defaults_preserve_exact_main_prompts(self):
        cfg = study(self.args())
        saved = json.loads((ROOT/'studies/good_culture.json').read_text())
        self.assertEqual(cfg['questions'], saved['questions'])
        self.assertEqual(len(list(planned(cfg))), 144)
        self.assertEqual(cfg['layers'][0]['id'], 'api')
        self.assertNotIn('inputs', cfg)

    def test_other_brand_profile_does_not_retain_dairy(self):
        cfg = study(self.args('preview', '--study', 'birkenstock', '--brand', 'Test Sandals', '--competitors', 'Other Sandals,Third Sandals'))
        text = ' '.join(q['text'] for q in cfg['questions'])
        self.assertNotIn('Birkenstock', text)
        self.assertNotIn('Teva', text)
        self.assertNotIn('cottage cheese', text)
        self.assertIn('Test Sandals', text)

    def test_custom_questions_remove_original_contrasts(self):
        qs = json.dumps([dict(id='new', kind='discovery', text='Which brand offers good value?')])
        cfg = study(self.args('preview', '--questions', qs))
        self.assertEqual(cfg['contrasts'], [])
        self.assertEqual(len(list(planned(cfg))), 12)

    def test_browser_cannot_swap_brand(self):
        with self.assertRaises(StudyError):
            study(self.args('build-browser', '--brand', 'Other'))

    def test_unsupported_surface_not_silently_substituted(self):
        with self.assertRaises(StudyError):
            study(self.args('preview', '--providers', 'copilot_search'))

    def test_preview_requires_no_keys_or_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch('automation.run.post') as send:
            args = self.args()
            args.output = str(Path(tmp)/'preview')
            result = execute(args)
            self.assertEqual(result['attempted'], 0)
            send.assert_not_called()

    def test_request_cap_fails_before_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch('automation.run.post') as send:
            args = self.args('collect', '--max-calls', '1', '--confirm-paid')
            args.output = str(Path(tmp)/'run')
            with self.assertRaises(StudyError):
                execute(args)
            send.assert_not_called()
            self.assertFalse(Path(args.output).exists())

    def test_missing_keys_fail_before_any_provider_call(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch('automation.run.post') as send:
            args = self.args('collect', '--confirm-paid')
            args.output = str(Path(tmp)/'run')
            with self.assertRaisesRegex(StudyError, 'Configure selected providers'):
                execute(args)
            send.assert_not_called()

    def test_paid_confirmation_required(self):
        with tempfile.TemporaryDirectory() as tmp, patch('automation.run.post') as send:
            args = self.args('collect')
            args.confirm_paid = False
            args.output = str(Path(tmp)/'run')
            with self.assertRaisesRegex(StudyError, 'confirmation'):
                execute(args)
            send.assert_not_called()

    def test_partial_response_preserved_and_not_retried(self):
        raw = dict(status='incomplete', model='fixture', output=[dict(type='message', content=[dict(type='output_text', text='partial answer')])])
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'OPENAI_API_KEY': 'TEST_ONLY_NOT_A_KEY', 'OPENAI_MODEL': 'fixture'}), patch('automation.run.post', return_value=raw) as send:
            args = self.args('collect', '--confirm-paid', '--providers', 'openai', '--repeats', '1')
            args.output = str(Path(tmp)/'run')
            with self.assertRaisesRegex(StudyError, 'stopped for review'):
                execute(args)
            send.assert_called_once()
            manifest = json.loads((Path(args.output)/'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'stopped_for_review')
            from benchmark_tool.config import sha
            self.assertEqual(manifest['input_sha256'], sha(Path(args.output)/manifest['input_file']))
            self.assertEqual(manifest['review_study_sha256'], sha(Path(args.output)/'study.json'))
            self.assertTrue((Path(args.output)/'attempts/0001.raw.json').exists())
            for p in Path(args.output).rglob('*'):
                if p.is_file():
                    self.assertNotIn('TEST_ONLY_NOT_A_KEY', p.read_text())

    def test_baseline_provenance_and_counts(self):
        verify_baseline()
        with tempfile.TemporaryDirectory() as tmp, patch('automation.run.post') as send:
            args = self.args('build-browser')
            args.output = str(Path(tmp)/'baseline')
            result = execute(args)
            self.assertEqual((result['collected'], result['included'], result['excluded'], result['pending']), (156, 155, 1, 0))
            send.assert_not_called()
            expected = readcsv(ROOT/'data/expected_brand_metrics.csv')
            actual = readcsv(Path(args.output)/'brand_metrics.csv')
            self.assertEqual(actual, expected)

    def test_complete_capture_is_importable_but_remains_draft(self):
        from benchmark_tool.config import load
        from benchmark_tool.evidence import load_evidence
        raw = dict(status='completed', model='fixture-returned', usage={'output_tokens': 4}, output=[dict(type='message', content=[dict(type='output_text', text='A complete fixture answer.')])])
        questions = json.dumps([dict(id='single', kind='discovery', text='Which brand?')])
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'OPENAI_API_KEY': 'TEST_ONLY_NOT_A_KEY', 'OPENAI_MODEL': 'fixture-requested'}), patch('automation.run.post', return_value=raw):
            args = self.args('collect', '--confirm-paid', '--providers', 'openai', '--repeats', '1', '--questions', questions)
            args.output = str(Path(tmp)/'run')
            result = execute(args)
            self.assertEqual(result['status'], 'collected_pending_coding')
            cfg = load(Path(args.output)/'study.json')
            self.assertEqual(cfg['study_status'], 'draft')
            data = load_evidence(cfg)
            self.assertEqual(len(data['observations']), 1)
            self.assertEqual(data['coding'], {})
            row = next(iter(data['observations'].values()))
            self.assertEqual(row['model'], 'fixture-returned')
            self.assertEqual(row['screenshot'], '')


class AdapterTests(unittest.TestCase):
    def test_openai_sources_and_annotations_remain_distinct(self):
        raw = dict(status='completed', output=[dict(type='web_search_call', status='completed', action={'sources': [{'url': 'https://source.example'}]}), dict(type='message', content=[dict(type='output_text', text='answer', annotations=[{'url':'https://citation.example'}])])])
        row = normalize('openai', raw)
        self.assertEqual(row['status'], 'captured_pending_coding')
        self.assertNotEqual(row['citations'][0]['url'], row['search_sources'][0]['url'])

    def test_claude_tool_error_is_not_success(self):
        row = normalize('anthropic', dict(stop_reason='end_turn', content=[dict(type='text', text='Answer'), dict(type='web_search_tool_result', content={'type':'web_search_tool_result_error'})]))
        self.assertEqual(row['status'], 'needs_review')

    def test_gemini_keeps_grounding_segments_and_indices(self):
        support = dict(segment={'text':'answer'}, groundingChunkIndices=[0])
        row = normalize('gemini', dict(candidates=[dict(finishReason='STOP', content={'parts':[{'text':'answer'}]}, groundingMetadata={'groundingSupports':[support], 'groundingChunks':[{'web': {'uri':'https://example.com'}}]})]))
        self.assertEqual(row['citations'], [support])
        self.assertEqual(row['status'], 'captured_pending_coding')

    def test_perplexity_truncation_not_accepted(self):
        row = normalize('perplexity', dict(choices=[dict(message={'content':'partial'}, finish_reason='length')]))
        self.assertEqual(row['status'], 'needs_review')

    def test_no_credentials_in_request_specifications(self):
        for provider in ['openai','anthropic','gemini','perplexity']:
            url, body = specification(provider, 'configured-model', 'exact prompt')
            self.assertTrue(url.startswith('https://'))
            self.assertIn('exact prompt', json.dumps(body))
            self.assertNotIn('API_KEY', json.dumps(body))


if __name__ == '__main__':
    unittest.main()
