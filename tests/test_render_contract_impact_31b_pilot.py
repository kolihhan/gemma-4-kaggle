"""CPU tests for real private paired-31B renderer: no GPU, no submissions."""
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from scripts import render_contract_impact_31b_pilot as p

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / p.MANIFEST_PATH).read_text())
TEMPLATE = (ROOT / p.TEMPLATE_PATH).read_text()

V2 = {
    "agent.yaml": "agent_class: LlmAgent\nname: coder\nmodel: gemma-4-31b-it-qat-w4a16-ct\n",
    "prompts/system.md": "control",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
    "configs/sampling.yaml": "temperature: 0.2\n",
}


def render():
    treatment = dict(V2)
    treatment["prompts/system.md"] = "contract"
    treatment["skills/contract-impact/scripts/contract.py"] = "print('ok')\n"
    with patch.object(p, "validate_source_zip", return_value=dict(V2)), \
         patch.object(p, "payload", return_value=treatment):
        return p.render_runtime(TEMPLATE, b"fixture", MANIFEST)


class PilotRendererTests(unittest.TestCase):
    def test_private_pair_has_two_evaluators_and_shared_model(self):
        runtime = render()
        self.assertIn('MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"', runtime)
        self.assertIn('Evaluator(EvalConfig(**base_kwargs))', runtime)
        self.assertIn('Evaluator(EvalConfig(**alternative_kwargs))', runtime)
        self.assertIn("result = run_maybe_async(", runtime)
        self.assertNotIn("alternate_kwargs", runtime)
        self.assertIn('"status": "partial"', runtime)
        self.assertIn("private-results", runtime)
        self.assertNotIn("competitions submit", runtime)
        self.assertNotIn("kaggle kernels push", runtime)
        compile(runtime, "runtime.py", "exec")

    def test_deterministic_exposure_exclusion_and_preregistered_denominator(self):
        runtime = render()
        scope = {"__name__": "cpu_only_no_main"}
        exec(compile(runtime, "runtime.py", "exec"), scope)
        ids = [f"fastapi_{n}" for n in range(10000, 10020)]
        ids += [f"rich_{n}" for n in range(10000, 10020)]
        ids += MANIFEST["exclude_instance_ids"]
        tasks = [SimpleNamespace(instance_id=ident) for ident in ids]
        first = scope["load_holdout_ids"](tasks)
        second = scope["load_holdout_ids"](list(reversed(tasks)))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)
        self.assertEqual(len(set(first)), 4)
        self.assertTrue(all(x not in MANIFEST["exclude_instance_ids"] for x in first))
        self.assertEqual(sum(x.startswith("rich_") for x in first), 2)

    def test_fails_closed_on_budget_imbalance(self):
        changed = dict(V2)
        changed["eval_config.yaml"] = "evaluation:\n  max_time_minutes: 30\n"
        changed["skills/contract-impact/scripts/contract.py"] = "print('ok')\n"
        with patch.object(p, "validate_source_zip", return_value=dict(V2)), \
             patch.object(p, "payload", return_value=changed):
            with self.assertRaisesRegex(ValueError, "budget confounded"):
                p.render_runtime(TEMPLATE, b"fixture", MANIFEST)

    def test_sample_mutation_is_rejected(self):
        bad = dict(MANIFEST)
        bad["per_repo"] = 8
        with self.assertRaisesRegex(ValueError, "sample size"):
            p.validate_manifest(bad)

    def test_uses_private_gpu_metadata_with_model_and_competition_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / p.MANIFEST_PATH).parent.mkdir(parents=True)
            (root / p.MANIFEST_PATH).write_text(json.dumps(MANIFEST))
            (root / p.TEMPLATE_PATH).parent.mkdir(parents=True)
            (root / p.TEMPLATE_PATH).write_text(TEMPLATE)
            treatment = dict(V2)
            treatment["skills/contract-impact/scripts/contract.py"] = "print('ok')\n"
            with patch.object(p, "validate_source_zip", return_value=dict(V2)), \
                 patch.object(p, "payload", return_value=treatment):
                p.render(root, b"fixture", root / "build", "kolihhan/private-pilot-test")
            meta = json.loads((root / "build/kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertTrue(meta["enable_gpu"])
            self.assertEqual(meta["competition_sources"], ["gemma-4-developer-agent"])
            self.assertEqual(meta["model_sources"], [p.MODEL_SOURCE])
            with self.assertRaises(FileExistsError):
                p.render(root, b"fixture", root / "build", "kolihhan/private-pilot-test")


if __name__ == "__main__":
    unittest.main()
