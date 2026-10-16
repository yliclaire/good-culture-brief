import copy
import json
from pathlib import Path
import tempfile
import unittest

from report.web_export import public_data, check_site


class WebExportTests(unittest.TestCase):
    def test_publication_preserves_counts_but_removes_private_context(self):
        source=dict(study=dict(output_root='/Users/private/output'),views={'one':dict(n=1,observation_ids=['one'])},
                    numbers={'lead':1},counts={'included':1,'excluded':1},observations={
                        'one':dict(quality='include',context_excerpts=['For ExampleName in ExampleTown'],transcript='For ExampleName in ExampleTown, choose Brand A.'),
                        'two':dict(quality='exclude',context_excerpts=[],transcript='raw partial private text')})
        before=copy.deepcopy(source)
        result=public_data(source)
        self.assertEqual(source,before)
        for key in ('views','numbers','counts'):self.assertEqual(result[key],source[key])
        self.assertNotIn('output_root',result['study'])
        self.assertNotIn('ExampleName',json.dumps(result))
        self.assertNotIn('raw partial private text',json.dumps(result))
        self.assertEqual(result['observations']['one']['context_excerpts'],[])
        self.assertIn('[name and location withheld]',result['observations']['one']['transcript'])

    def test_export_check_rejects_missing_assets_and_private_markers(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'index.html').write_text('<a href="missing.html">Evidence</a>')
            with self.assertRaisesRegex(ValueError,'Broken link'):check_site(root)
            (root/'index.html').write_text('<p>/Users/private/file</p>')
            with self.assertRaisesRegex(ValueError,'Private marker'):check_site(root)
            (root/'index.html').write_text('<p id="brief">Brief</p><a href="#brief">Start</a>')
            self.assertEqual(check_site(root)['html_files'],1)


if __name__=='__main__':unittest.main()
