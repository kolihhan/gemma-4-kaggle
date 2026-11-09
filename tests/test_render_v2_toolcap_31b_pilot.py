"""Tests for disjoint same-time 31B tool-call cap experiment (no model)."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import render_v2_toolcap_31b_pilot as p

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / p.MANIFEST_PATH).read_text())
TEMPLATE = (ROOT / p.TEMPLATE_PATH).read_text()

V2 = {
    "agent.yaml": "agent_class: LlmAgent\nname: coder\nmodel: gemma-4-31b-it-qat-w4a16-ct\n",
    "prompts/system.md": "exact original prompt",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_config:\n  thinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class ToolCapExperimentTests(unittest.TestCase):
    def build(self):
        with patch.object(p, "validate_source_zip", return_value=dict(V2)):
            return p.render_runtime(TEMPLATE, b"fake pinned ZIP", MANIFEST)

    def test_one_parameter_changes_and_runtime_override_applies(self):
        runtime = self.build()
        self.assertIn('MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"', runtime)
        self.assertIn('alternative_kwargs["max_tool_calls"] = 60', runtime)
        self.assertIn('base_kwargs = dict(eval_kwargs)', runtime)
        self.assertIn('Evaluator(EvalConfig(**alternative_kwargs))', runtime)
        self.assertIn('Evaluator(EvalConfig(**base_kwargs))', runtime)
        self.assertIn('"baseline_v2_28"', runtime)
        self.assertIn('"v2_60_calls"', runtime)
        self.assertNotIn('contract-impact', runtime)
        self.assertNotIn('kaggle competitions submit', runtime)
        compile(runtime, p.KERNEL_FILE, "exec")

    def test_payload_diff_exactly_one_max_tool_calls(self):
        import ast
        import base64
        runtime=self.build()
        assignments=ast.parse(runtime).body
        value=next(n.value for n in assignments if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=="SUBMISSION_PAYLOAD_B64"
                           for t in n.targets))
        arms=json.loads(base64.b64decode(ast.literal_eval(value)))
        self.assertEqual(set(arms),{"baseline_v2_28","v2_60_calls"})
        old=arms["baseline_v2_28"]
        new=arms["v2_60_calls"]
        self.assertEqual(set(old),set(new))
        for name in old:
            if name=="eval_config.yaml":
                self.assertEqual(new[name],
                                 old[name].replace("max_tool_calls: 28",
                                                   "max_tool_calls: 60"))
            else:
                self.assertEqual(old[name],new[name])

    def test_deterministic_fresh_sample_excludes_previous_pilot(self):
        scope={"__name__":"dont_run_runtime_main"}
        exec(self.build(),scope)
        ids=[f"fastapi_{n}" for n in range(10000,10030)]
        ids += [f"rich_{n}" for n in range(10000,10030)]
        ids += MANIFEST["exclusions"]
        tasks=[SimpleNamespace(instance_id=ident) for ident in ids]
        a=scope["load_holdout_ids"](tasks)
        b=scope["load_holdout_ids"](list(reversed(tasks)))
        self.assertEqual(a,b)
        self.assertEqual(len(a),4)
        self.assertFalse(set(a)&set(MANIFEST["exclusions"]))
        self.assertEqual(sum(i.startswith("fastapi_") for i in a),2)
        self.assertEqual(sum(i.startswith("rich_") for i in a),2)

    def test_rejects_manifest_or_baseline_drift(self):
        with self.assertRaisesRegex(ValueError,"manifest version"):
            p.validate_manifest({**MANIFEST,"version":"mutated"})
        drift=dict(V2)
        drift["eval_config.yaml"] = drift["eval_config.yaml"].replace("max_tool_calls: 28", "max_tool_calls: 60")
        with patch.object(p,"validate_source_zip",return_value=drift):
            with self.assertRaisesRegex(ValueError,"pinned 28-call"):
                p.render_runtime(TEMPLATE,b"fake",MANIFEST)

    def test_kernel_is_private_and_not_automatically_submitted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            file=root/p.MANIFEST_PATH
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(json.dumps(MANIFEST))
            template=root/p.TEMPLATE_PATH
            template.parent.mkdir(parents=True,exist_ok=True)
            template.write_text(TEMPLATE)
            with patch.object(p,"validate_source_zip",return_value=dict(V2)):
                summary=p.render(root,b"fake",root/"out","kolihhan/private-v2-toolcap-test")
            meta=json.loads((root/"out/kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertTrue(meta["enable_gpu"])
            self.assertEqual(meta["model_sources"],[p.MODEL_SOURCE])
            self.assertFalse(summary["official_submission_created"])
            self.assertFalse(summary["model_inference_executed_by_renderer"])


if __name__=="__main__":
    unittest.main()
