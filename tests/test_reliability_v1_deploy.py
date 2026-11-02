import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('renderer', ROOT/'scripts'/'render_reliability_v1_kernel.py')
renderer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(renderer)

class ReliabilityV1DeployTests(unittest.TestCase):
    def test_frozen_submission_contract(self):
        payload = renderer.load_frozen_submission(ROOT/'submission')
        self.assertEqual(sorted(payload), sorted(renderer.EXPECTED_SHA256))
        self.assertNotIn('agent_tool:', payload['agent.yaml'])
        self.assertEqual(payload['agent.yaml'].count('- submit_patch'), 1)
        self.assertIn('Never run bare `pytest`', payload['prompts/coder.md'])
        self.assertIn('Before a fourth exploratory `read_file`', payload['prompts/coder.md'])
        self.assertIn('old text was not found', payload['prompts/coder.md'])

    def test_submit_kernel_writes_only_frozen_submission_zip(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            renderer.render_submit(ROOT, out, 'kolihhan/reliability-v1-test')
            meta = json.loads((out/'kernel-metadata.json').read_text())
            self.assertEqual(meta['competition_sources'], ['gemma-4-developer-agent'])
            self.assertFalse(meta['enable_internet'])
            self.assertFalse(meta['enable_gpu'])
            code = (out/'reliability_v1_submit_builder.py').read_text()
            self.assertIn('/kaggle/working/submission.zip', code)
            self.assertNotIn('kaggle-data-2026-10-31', code)

    def test_diagnostic_renderer_preserves_frozen_manifest_contract(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            repo = td/'repo'; repo.mkdir()
            import shutil
            shutil.copytree(ROOT/'submission', repo/'submission')
            (repo/'kaggle').mkdir()
            (repo/'kaggle'/'verifier_baseline_runtime.py').write_text(
                'SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"\n'
                'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"\n', encoding='utf-8')
            manifest = {'version':'verifier-lora-v0','selection_rule':'gold-pass AND no-op-fail','sampling_frozen':True,'budget_frozen':True,'holdout':[{'instance_id':'x'}]}
            mp=repo/'manifest.json'; mp.write_text(json.dumps(manifest))
            out=td/'out'
            renderer.render_diagnostic(repo,out,'kolihhan/reliability-v1-diag-test',mp)
            text=(out/'reliability_v1_diagnostic.py').read_text()
            self.assertNotIn('__SUBMISSION_PAYLOAD_B64__', text)
            self.assertNotIn('__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__', text)
            meta=json.loads((out/'kernel-metadata.json').read_text())
            self.assertTrue(meta['enable_gpu'])
            self.assertEqual(meta['competition_sources'], ['gemma-4-developer-agent'])

if __name__ == '__main__':
    unittest.main()
