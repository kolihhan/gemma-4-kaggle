"""Synthetic tests for the independent, no-GPU current scorer controls."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import tempfile
import unittest

from scripts import render_earlyedit_current_controls_cpu as m
from scripts import render_earlyedit_v2_paired_31b as study

ROOT=Path(__file__).resolve().parents[1]


class CurrentEpochControlTests(unittest.TestCase):
    def test_frozen_ids_only_and_real_official_verifier(self):
        src=m.build(ROOT)
        self.assertIn("agent_patch=patch",src)
        self.assertIn("gemma4-earlyedit-four-current-scorer-controls-v1",src)
        self.assertNotIn("requests_7427",src)
        self.assertNotIn("gemma-4-31b-it-qat-w4a16-ct",src)
        p=json.loads((ROOT/study.PLAN_FILE).read_text())
        for t in p["tasks"]:
            self.assertIn(t["instance_id"],src)
        compile(src,m.FILENAME,"exec")

    def test_cpu_kernel_never_enables_gpu_or_models(self):
        with tempfile.TemporaryDirectory() as td:
            result=m.render(ROOT,Path(td)/"out",
                            "kolihhan/earlyedit-cpu-four-preflight-only")
            self.assertTrue(result["no_gpu_inference_training_or_submission"])
            meta=json.loads((Path(td)/"out/kernel-metadata.json").read_text())
            self.assertFalse(meta["enable_gpu"])
            self.assertEqual(meta["model_sources"],[])
            self.assertTrue(meta["is_private"])


if __name__=="__main__":
    unittest.main()
