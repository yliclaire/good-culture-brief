import copy
import json
from pathlib import Path
import unittest
from report.reuse import render_preview

ROOT = Path(__file__).resolve().parents[1]


class ReusePreviewTests(unittest.TestCase):
    def setUp(self):
        root = ROOT/'demonstrations/birkenstock'
        self.study = json.loads((root/'study.json').read_text())
        self.plan = json.loads((root/'collection_plan.json').read_text())

    def test_readable_preview_preserves_each_exact_prompt_and_calls(self):
        from html import escape
        page = render_preview(self.study,self.plan)
        self.assertIn('96 planned requests · 0 collected answers',page)
        self.assertEqual(len(self.study['questions']),8)
        for prompt in {j['exact_prompt'] for j in self.plan['jobs']}:
            self.assertIn(escape(prompt,quote=True),page)
        self.assertIn('Download request plan (JSON)',page)
        self.assertIn('require category review',page)

    def test_duplicate_provider_pass_cannot_present_complete_coverage(self):
        plan = copy.deepcopy(self.plan)
        job = plan['jobs'][0]
        other = next(j for j in plan['jobs'][1:] if j['question_id']==job['question_id'])
        job['engine'],job['repeat'] = other['engine'],other['repeat']
        with self.assertRaisesRegex(ValueError,'provider/pass cell'):
            render_preview(self.study,plan)
