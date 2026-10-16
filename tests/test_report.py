import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmark_tool.config import StudyError,load,sha
from benchmark_tool.evidence import load_evidence,readcsv
from benchmark_tool.cli import build
from report.build import registered,build_brief
from report.export import fingerprint,export,view_key
from report.render import render,tokens
from report.competition import competitive_rows


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.cfg,cls.narrative,cls.review,cls.entry=registered('good_culture_browser_2026_q4')
        cls.source=load_evidence(cls.cfg)
        cls.metricdir=Path(cls.tmp.name)/'metrics'
        build(dict(cls.cfg,output_root=cls.tmp.name,run_id='metrics'))
        cls.data=export(cls.cfg,cls.source,cls.metricdir,cls.narrative)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_baseline_exact_metric_parity(self):
        self.assertEqual(readcsv(self.metricdir/'brand_metrics.csv'),readcsv(ROOT/'data/expected_brand_metrics.csv'))

    def test_primary_claims_are_bound_to_metrics(self):
        n=self.data['numbers']
        self.assertEqual([n[k] for k in ['protein_leads','culture_leads','ingredient_leads','ingredient_primary','budget_rec','budget_great_value','premium_conditional','stockout_subs','stockout_leads','switch_primary']], [12,11,2,8,0,9,12,12,11,6])

    def test_counts_and_source_mapping_units(self):
        self.assertEqual(self.data['counts'],dict(planned=156,collected=156,included=155,excluded=1,pending=0))
        self.assertEqual((self.data['numbers']['mapped_claims'],self.data['numbers']['selected_claims']),(32,698))

    def test_every_question_partition_conserves_answers(self):
        for v in self.data['views'].values():
            self.assertEqual(v['n'],len(v['observation_ids']))
            if v['status']=='ready' and v['scope']=='question':
                self.assertAlmostEqual(sum(r['first_choice_credit_sum'] for r in v['rows'])+v['no_lead_n'],v['n'])

    def test_competitors_are_question_specific(self):
        expected={'Q6':'Private label: Great Value','Q7':'Friendship Dairies','Q8':'Lactaid','Q9':'Hood'}
        for q,brand in expected.items():
            v=self.data['views'][view_key('main','baseline','question',q,'all')]
            self.assertIn(brand,[r['brand'] for r in competitive_rows(self.data,v)])
        v=self.data['views'][view_key('main','baseline','question','Q5','all')]
        rows=competitive_rows(self.data,v,'recommended_sum')
        self.assertEqual(next(r['recommended_sum'] for r in rows if r['brand']=="Nancy's"),10)

    def test_matrix_keeps_named_competitors_and_frozen_core_roster(self):
        roster=self.data['competitor_matrix']
        self.assertEqual(len(roster['questions']),9)
        for brand in ['Good Culture','Daisy',"Breakstone's",'Knudsen','Lactaid','Hood','Friendship Dairies','Anderson Erickson','Private label: Great Value',"Nancy's"]:
            self.assertIn(brand,roster['core_brands'])
        self.assertTrue(set(roster['core_brands'])<=set(roster['brands']))

    def test_editorial_reading_hierarchy_preserves_explorer_and_print(self):
        page=render(self.data)
        for name in ['panel-brief','panel-explore','panel-methodology','chapter-navigation','story-positioning','story-competition','story-durability','story-diligence']:
            self.assertIn('id="'+name+'"',page)
        self.assertEqual(page.count('data-chapter="'),5)
        self.assertIn('assets/navigation.js',page)
        # Compact preview and the full competitor matrix both survive generation.
        self.assertIn('compact-comparison',page)
        self.assertIn('id="matrix-table"',page)

    def test_workflow_guide_preserves_evidence_and_review_boundary(self):
        page=render(self.data)
        guide=page.split('<section id="reuse"',1)[1].split('</section>',1)[0]
        for value in ['build-brief','preview','collect','reviewed-study registry','Save and register the approved package','code/README.md']:
            self.assertIn(value,guide)
        self.assertNotIn('Additional evidence for the investment decision',guide)
        self.assertIn('<details id="study-details" class="methodology-details"><summary>Study definitions, limitations and evidence</summary><section id="methods">',page)
        self.assertIn('id="browse-results"',page)

    def test_editorial_atlas_uses_reviewed_discovery_counts_and_ties(self):
        page=render(self.data)
        self.assertNotIn('data-design="investment-memo"',page)
        self.assertIn('Exhibit 1 ·',page)
        self.assertIn('Exhibit 2 ·',page)
        self.assertIn('Exhibit 3 ·',page)
        self.assertIn('class="proof-grid"',page)
        self.assertIn('Great Value leads 9 / 12 answers',page)
        self.assertIn('methodology/ASSIGNMENT_REVIEW.md',page)
        atlas=page.split('<section id="category-map"',1)[1].split('</section>',1)[0]
        self.assertEqual(atlas.count('class="atlas-need'),9)
        self.assertIn('Hood',atlas)
        self.assertIn('Friendship Dairies',atlas)
        self.assertIn('No overall lead: 6 / 12',atlas)
        self.assertNotIn('data-preset-question="Q10"',atlas)
        for q in self.data['competitor_matrix']['questions']:
            self.assertIn('data-preset-question="'+q+'"',atlas)

    def test_decision_support_separates_observation_scenario_and_diligence(self):
        page=render(self.data)
        self.assertIn('Preliminary investment view',page)
        self.assertIn('Scenario, not an observed launch',page)
        self.assertIn('Strengthens the case',page)
        self.assertIn('Weakens the case',page)
        self.assertEqual(page.count('<details class="evidence-challenge">'),4)
        for eid in ['E05','E09','E12','E14']:
            excerpt=next(e['excerpt'] for e in self.data['selections'] if e['evidence_id']==eid)
            from report.render import esc
            self.assertIn(esc(excerpt),page)
        self.assertIn('Synthetic demonstration',page)

    def test_monitoring_demo_is_separate_from_observed_metrics(self):
        from report.monitoring import demo
        result=demo(self.data)
        self.assertEqual(result['baseline']['first_choice_credit'],12)
        self.assertFalse(result['baseline']['synthetic'])
        self.assertEqual(result['cases']['decline']['result']['delta_pp'],-25)
        self.assertEqual(result['cases']['decline']['result']['status'],'review')
        self.assertEqual(result['cases']['unchanged']['result']['status'],'no_alert')
        self.assertIsNone(result['cases']['model_change']['result']['delta_pp'])
        for case in result['cases'].values():
            self.assertTrue(case['future']['synthetic'])
            self.assertEqual(case['future']['observation_ids'],[])
        self.assertEqual(len(self.data['observations']),156)

    def test_monitoring_checks_actual_metadata_and_roundtrips(self):
        from report.monitoring import demo,compare
        baseline=demo(self.data)['baseline']
        other=json.loads(json.dumps(baseline))
        self.assertEqual(compare(baseline,other)['status'],'no_alert')
        for key in ['market','question','codebook','metadata']:
            changed=copy.deepcopy(other)
            changed['protocol'][key]='changed but hash deliberately left stale'
            self.assertEqual(compare(baseline,changed)['status'],'hold')
        changed=copy.deepcopy(other);changed['n']=13
        self.assertEqual(compare(baseline,changed)['status'],'hold')
        changed['n']=0
        with self.assertRaises(ValueError):compare(baseline,changed)

    def test_source_inventory_retains_layer_and_answer_provenance(self):
        from report.sources import inventory
        rows=inventory(self.data)
        self.assertTrue(rows)
        for item in rows:
            self.assertEqual(item['observation_ids'],sorted(set(item['observation_ids'])))
            for oid in item['observation_ids']:
                self.assertEqual(self.data['observations'][oid]['layer'],item['layer'])
                self.assertEqual(self.data['observations'][oid]['quality'],'include')
        self.assertIn('goodculture.com',[r['domain'] for r in rows])
        self.assertIn('Which sources were captured?',render(self.data))
        self.assertIn('do not estimate overall source frequency',render(self.data))

    def test_unavailable_matched_q1_never_becomes_zero(self):
        for engine in ['all']+self.cfg['layers'][0]['engines']:
            v=self.data['views'][view_key('main','matched_context','question','Q1',engine)]
            self.assertNotEqual(v['status'],'ready');self.assertEqual(v['rows'],[])

    def test_engine_filter_keeps_global_matching(self):
        for engine in self.cfg['layers'][0]['engines']:
            v=self.data['views'][view_key('main','matched_context','question','Q6',engine)]
            self.assertEqual(v['pass_labels'],['3'])
            self.assertEqual(v['n'],1)

    def test_original_and_exploratory_contrasts_remain_distinct(self):
        rows=[c for c in self.data['contrasts'] if c['population']=='matched_context']
        for c in rows:
            if c['analysis_status']=='prespecified':self.assertIsNone(c['first_choice_rate_difference_pp'])
            if c['contrast_id']=='exploratory_budget_q2':self.assertEqual(c['retained_repeats_n'],'1')

    def test_stale_narrative_rejected(self):
        n=copy.deepcopy(self.narrative);n['source_fingerprint']='changed'
        with self.assertRaisesRegex(StudyError,'stale'):export(self.cfg,self.source,self.metricdir,n)

    def test_brand_or_quarter_cannot_inherit_narrative(self):
        for field,value in [('focal_brand','Synthetic Fixture Brand'),('wave','2099-Q1')]:
            cfg=dict(self.cfg,**{field:value})
            self.assertNotEqual(fingerprint(cfg,self.source),self.narrative['source_fingerprint'])
            with self.assertRaisesRegex(StudyError,'stale'):export(cfg,self.source,self.metricdir,self.narrative)

    def test_unregistered_study_cannot_be_arbitrary_path(self):
        with self.assertRaisesRegex(StudyError,'not registered'):registered('../../other')
        from report.build import within
        for path in ['../README.md',str(ROOT/'README.md')]:
            with self.assertRaisesRegex(StudyError,'relative'):within(path)

    def test_literal_source_excerpt_required(self):
        n=copy.deepcopy(self.narrative);n['evidence_selections'][0]['excerpt']='THIS IS AN ABSENT SYNTHETIC EXCERPT'
        with self.assertRaisesRegex(StudyError,'excerpt absent'):export(self.cfg,self.source,self.metricdir,n)

    def test_missing_numeric_reference_fails(self):
        with self.assertRaisesRegex(ValueError,'Unbound'):tokens('A value {{not_defined}}',self.data)

    def test_shared_template_does_not_hardcode_focal_or_primary(self):
        # A label-only synthetic fixture, never exported as a collected study.
        fixture=json.loads(json.dumps(self.data).replace('Good Culture','Synthetic Focal').replace('Daisy','Synthetic Peer'))
        visible=render(fixture).split('<script type="application/json"')[0]
        self.assertFalse('Good Culture' in visible or 'Daisy' in visible)
        self.assertIn('Synthetic Focal',visible)

    def test_print_contains_all_principal_findings_and_safe_data(self):
        page=render(self.data,True)
        self.assertIn('print-document',page)
        self.assertIn('Minimum cost per serving',page)
        self.assertIn('Good Culture unavailable',page)
        self.assertFalse('{{' in page.split('<script type="application/json"')[0], 'Visible narrative contains an unresolved metric token')
        d=copy.deepcopy(self.data);d['observations'][next(iter(d['observations']))]['transcript']='</script><script>alert(1)</script>'
        self.assertNotIn('</script><script>alert(1)</script>',render(d))

    def test_release_links_hashes_and_dom_interactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'brief'
            result=build_brief('good_culture_browser_2026_q4',out)
            self.assertEqual(result['checks']['all_observation_pages'],156)
            manifest=json.loads((out/'release_manifest.json').read_text())
            for name,digest in manifest['outputs'].items():self.assertEqual(sha(out/name),digest)
            node=shutil.which('node') or ''
            if not node or not Path(node).exists():self.skipTest('Node unavailable for DOM-model checks')
            p=subprocess.run([node,str(ROOT/'tests/report_ui.cjs'),str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            result=json.loads(p.stdout)
            self.assertEqual(result['questionStates'],240)
            self.assertEqual(result['matrixStates'],40)
            self.assertEqual(result['evidenceDialogs'],156)
            p=subprocess.run([node,str(ROOT/'tests/navigation_ui.cjs'),str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertEqual(json.loads(p.stdout)['readingViews'],3)
            p=subprocess.run([node,str(ROOT/'tests/monitoring_ui.cjs'),str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertEqual(json.loads(p.stdout)['syntheticCases'],3)
            preview=json.loads((out/'demonstrations/birkenstock/manifest.json').read_text())
            self.assertEqual(preview['attempted'],0)
            self.assertEqual(preview['captured'],0)
            self.assertEqual(preview['planned_requests'],96)


if __name__=='__main__':unittest.main()
