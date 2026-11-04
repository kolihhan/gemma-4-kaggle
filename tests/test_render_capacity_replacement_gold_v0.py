"""Tests for metadata-only private capacity replacement gold-screen renderer."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import render_capacity_replacement_gold_v0 as renderer


ROOT = Path(__file__).resolve().parents[1]


class CapacityReplacementGoldRendererTests(unittest.TestCase):
    def test_frozen_replacement_screen_uses_new_metadata_only_ids(self):
        manifest=renderer.create_manifest(ROOT)
        rows=manifest["holdout"]
        self.assertEqual(manifest["version"],"verifier-lora-v0")
        self.assertEqual(len(rows),16)
        self.assertEqual(len({r["instance_id"] for r in rows}),16)
        self.assertEqual(sum(r["repo"]=="Textualize/rich" for r in rows),4)
        self.assertEqual(sum(r["repo"]=="fastapi/fastapi" for r in rows),12)
        plan=renderer.replacements.build_plan(ROOT)
        self.assertEqual([r["instance_id"] for r in rows[:4]],plan["queues"]["Textualize/rich"][:4])
        self.assertEqual([r["instance_id"] for r in rows[4:]],plan["queues"]["fastapi/fastapi"][:12])
        self.assertFalse({r["instance_id"] for r in rows}&set(plan["original_ids"]))
        self.assertTrue(all(r["patch_bucket"]=="metadata-only" for r in rows))
        self.assertTrue(all(set(r)=={"instance_id","repo","patch_bucket"} for r in rows))

    def test_renderer_is_private_cpu_only_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"render"
            renderer.render(ROOT,out,"kolihhan/test-replacements-cpu")
            meta=json.loads((out/"kernel-metadata.json").read_text())
            self.assertFalse(meta["enable_gpu"])
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["model_sources"],[])
            self.assertEqual(meta["competition_sources"],["gemma-4-developer-agent"])
            source=(out/"gold_control_sweep.py").read_text()
            self.assertNotIn('__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__', source)
            compile(source,"gold_control_sweep.py","exec")
            with self.assertRaises(ValueError):
                renderer.render(ROOT,out,"kolihhan/test-replacements-cpu")


if __name__=="__main__":
    unittest.main()
