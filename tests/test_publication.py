"""Publication derivatives retain provenance without relaxing browser capture rules."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmark_tool.config import StudyError, load
from benchmark_tool.evidence import load_evidence

ROOT=Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def test_public_baseline_has_explicit_derivative_lineage(self):
        cfg=load(ROOT/'studies/good_culture.json')
        evidence=load_evidence(cfg)
        self.assertEqual(len(evidence['observations']),156)
        for row in evidence['observations'].values():
            self.assertEqual(row['capture_format'],'sanitized_browser_export')
            self.assertFalse(row.get('screenshot'))
            self.assertEqual(len(row['publication_provenance']['original_capture_sha256']),64)
            record=json.loads((ROOT/'data/browser_baseline'/row['evidence_file']).read_text())
            self.assertIn('reviewed_answer',record)
            self.assertIn('audit_excerpts',record)
        self.assertFalse(list((ROOT/'data/browser_baseline').rglob('*.png')))
        self.assertFalse(list((ROOT/'data/browser_baseline').rglob('*.jpg')))

    def test_screenshot_exception_requires_provenance_and_publication_config(self):
        cfg=load(ROOT/'studies/good_culture.json')
        original=Path(ROOT/'data/browser_baseline/observations.jsonl').read_text()
        broken=copy.deepcopy(cfg);broken.pop('publication')
        with self.assertRaisesRegex(StudyError,'explicit publication configuration'):
            load_evidence(broken)
        rows=[json.loads(x) for x in original.splitlines()]
        rows[0].pop('publication_provenance')
        text=''.join(json.dumps(r)+'\n' for r in rows)
        original_read=Path.read_text
        def substituted(path,*args,**kwargs):
            return text if path.name=='observations.jsonl' else original_read(path,*args,**kwargs)
        with patch.object(Path,'read_text',substituted):
            with self.assertRaisesRegex(StudyError,'lacks provenance'):
                load_evidence(cfg)


if __name__=='__main__':unittest.main()
