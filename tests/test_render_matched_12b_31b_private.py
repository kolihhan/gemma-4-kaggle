"""Synthetic CPU preflight; never reads any real task text or model weights."""
from __future__ import annotations
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import render_matched_12b_31b_private as renderer


class TwoModelCapacityRendererTests(unittest.TestCase):
    def test_manifest_exact_four_clean_prequalified_ids(self):
        self.assertEqual([a for a,_ in renderer.FROZEN],
                         ["fastapi_14458","fastapi_15589","rich_3894","rich_3905"])
        self.assertEqual(len(set(renderer.FROZEN)),4)
        self.assertEqual(renderer.manifest()["version"],"verifier-lora-v0")

    def test_compile_two_separate_model_kernels(self):
        repo=Path(__file__).resolve().parents[1]
        sample={
            "agent.yaml":"model: gemma-4-31b-it-qat-w4a16-ct\n",
            "eval_config.yaml":"max_time_minutes: 5\nmax_tool_calls: 28\nmax_turns: 80\n",
            "configs/sampling.yaml":"temperature: 0.1\n",
            "prompts/system.md":"synthetic unit-test only\n",
        }
        arms={key:dict(sample) for key in renderer.ARMS}
        arms["v2_12b"]["agent.yaml"]="model: gemma-4-12b-it-qat-w4a16-ct\n"
        hashes={key:renderer.hashlib.sha256(renderer.archive(files)).hexdigest()
                for key,files in arms.items()}
        with tempfile.TemporaryDirectory() as d:
            for arm in renderer.ARMS:
                with patch.object(renderer,"validate_source_zip",return_value=sample),\
                     patch.object(renderer,"candidate_files",return_value=arms),\
                     patch.object(renderer,"EXPECTED",hashes):
                    out=Path(d)/arm
                    result=renderer.render(repo,b"fake",arm,out,
                        "kolihhan/gemma4-capacity-check-"+arm.replace("_","-"))
                    meta=json.loads((out/"kernel-metadata.json").read_text())
                    text=(out/renderer.FILENAME).read_text()
                    self.assertTrue(meta["is_private"])
                    self.assertTrue(meta["enable_gpu"])
                    self.assertFalse(meta["enable_internet"])
                    self.assertEqual(len(meta["model_sources"]),1)
                    self.assertIn(renderer.ARMS[arm],meta["model_sources"][0])
                    self.assertNotIn("__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__",text)
                    self.assertNotIn("__SUBMISSION_PAYLOAD_B64__",text)
                    self.assertIn("Evaluator(eval_config)",text)
                    # Only the 12B needs the documented text-only HF architecture override.
                    if arm == "v2_12b":
                        self.assertIn("--hf-overrides",text)
                        self.assertIn("Gemma4ForCausalLM",text)
                        self.assertIn("model_type",text)
                    else:
                        self.assertNotIn("--hf-overrides",text)
                        self.assertIn("extra_args=(),",text)
                    self.assertFalse(result["new_official_submission"])
                    self.assertEqual(result["issue_count"],4)
                    compile(text,"frozen_model_capacity_runtime.py","exec")

    def test_bad_ref_or_arm_is_rejected(self):
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"private kernel"):
                renderer.render(repo,b"fake","v2_31b",Path(d),"someone/wrong")
            with self.assertRaises(ValueError):
                renderer.render_runtime("",b"fake","unapproved")


if __name__=="__main__":
    unittest.main()
