"""CPU contract tests; no model, GPU, raw competition tasks or third-party code exec."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import render_public_prompt_vs_v2_paired_31b as m
from scripts.build_public_prompt_only_control_20261111 import make_zip

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/m.MANIFEST_PATH).read_text())
TEMPLATE=(ROOT/m.TEMPLATE_PATH).read_text()
SOURCE=b"mock baseline bytes"
BASE={
    "agent.yaml":"name: direct\nmodel: "+m.MODEL+"\ntools:\n  - read_file\n  - edit_file\n",
    "configs/sampling.yaml":"thinking_budget: 4096\n",
    "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
    "prompts/system.md":"V2 public baseline",
}
TREAT=copy.deepcopy(BASE)
TREAT["eval_config.yaml"]=BASE["eval_config.yaml"].replace("max_time_minutes: 8","max_time_minutes: 5")
TREAT["prompts/system.md"]="public competitor prompt only"


def fake_render():
    manifest=copy.deepcopy(PLAN)
    manifest["baseline_zip_sha256"]=hashlib.sha256(SOURCE).hexdigest()
    manifest["prompt_only_5min_zip_sha256"]=hashlib.sha256(make_zip(TREAT)).hexdigest()
    with (patch.object(m,"EXPECTED_ZIP_SHA256",manifest["baseline_zip_sha256"]),
          patch.object(m,"PROMPT_ZIP_SHA",manifest["prompt_only_5min_zip_sha256"]),
          patch.object(m,"validate_source_zip",return_value=BASE),
          patch.object(m,"candidate_files",return_value=TREAT)):
        return m.render_runtime(TEMPLATE,SOURCE,TREAT,manifest)


class PairedPromptContractTests(unittest.TestCase):
    def test_valid_pinned_task_and_two_arm_manifest(self):
        m.validate_manifest(PLAN)
        self.assertEqual(PLAN["experiment"]["model_task_evaluations"],6)
        self.assertEqual(PLAN["experiment"]["tasks"],3)
        self.assertEqual(PLAN["shared_budget"]["max_time_minutes"],5)
        self.assertIn("requests_7328",PLAN["selection"]["exclude_instance_ids"])

    def test_private_runtime_has_two_disjoint_evaluators_and_only_prompt_differs(self):
        source=fake_render()
        self.assertIn("TREATMENT_PAYLOAD_B64",source)
        self.assertIn('treatment_evaluator = Evaluator(treatment_config)',source)
        self.assertIn('evaluators = {"v2_5min": evaluator, "public_prompt_5min": treatment_evaluator}',source)
        self.assertIn('PAIRED_PROMPT_FROZEN_SELECTED_PUBLIC_DEV_IDS',source)
        self.assertIn('PRIVATE_PAIRED_31B_SAFE_METRIC=',source)
        self.assertNotIn('"__SUBMISSION_PAYLOAD_B64__"',source)
        self.assertNotIn("competition_submit_code",source)
        compile(source,"paired_kernel.py","exec")

    def test_no_task_reselection_from_hidden_labels_and_selection_deterministic(self):
        ns={"__name__":"not_main"}
        exec(compile(fake_render(),"paired_kernel.py","exec"),ns)
        tasks=[SimpleNamespace(instance_id=f"{prefix}{i}") for prefix in
               ("requests_","rich_","fastapi_") for i in range(100,115)]
        tasks.append(SimpleNamespace(instance_id="requests_7328"))
        a=ns["load_holdout_ids"](tasks)
        b=ns["load_holdout_ids"](list(reversed(tasks)))
        self.assertEqual(a,b)
        self.assertEqual(len(a),3)
        self.assertTrue(a[0].startswith("fastapi_"))
        self.assertTrue(a[1].startswith("rich_"))
        self.assertTrue(a[2].startswith("requests_"))
        self.assertNotIn("requests_7328",a)

    def test_invalid_variants_stop_before_gpu(self):
        for field,new_value in [
            ("model","wrong_model"),
            ("source_prompt_sha256","zero"),
        ]:
            v=dict(PLAN)
            v[field]=new_value
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.validate_manifest(v)
        v=copy.deepcopy(PLAN)
        v["shared_budget"]["max_time_minutes"]=8
        with self.assertRaises(ValueError):
            m.validate_manifest(v)

    def test_exact_pairing_and_refuse_unrelated_file_drift(self):
        altered=dict(TREAT)
        altered["agent.yaml"]="bad"
        manifest=copy.deepcopy(PLAN)
        manifest["baseline_zip_sha256"]=hashlib.sha256(SOURCE).hexdigest()
        manifest["prompt_only_5min_zip_sha256"]=hashlib.sha256(make_zip(altered)).hexdigest()
        with (patch.object(m,"EXPECTED_ZIP_SHA256",manifest["baseline_zip_sha256"]),
              patch.object(m,"PROMPT_ZIP_SHA",manifest["prompt_only_5min_zip_sha256"]),
              patch.object(m,"validate_source_zip",return_value=BASE),
              patch.object(m,"candidate_files",return_value=altered)):
            with self.assertRaisesRegex(ValueError,"uncontrolled change"):
                m.render_runtime(TEMPLATE,SOURCE,altered,manifest)

if __name__=="__main__":
    unittest.main()
