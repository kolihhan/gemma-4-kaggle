"""Private CPU-only prospective gold-control screening renderer tests."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.render_discriminating_evidence_gold import build_gold_manifest, render
from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory


class EvidenceGoldScreenTests(unittest.TestCase):
    def test_manifest_uses_only_precommitted_prospective_ids(self):
        select = build_exploratory(ROOT)
        manifest = build_gold_manifest(ROOT)
        self.assertEqual(
            [item["instance_id"] for item in manifest["holdout"]],
            select["pilot_ids"] + select["exploratory_ids"] + select["replacement_ids"]
        )
        self.assertEqual(len(manifest["holdout"]), 30)
        self.assertEqual(len(set(x["instance_id"] for x in manifest["holdout"])), 30)
        self.assertEqual(manifest["selector_sha256"], select["selection_digest_sha256"])
        self.assertTrue(all(set(x) == {"instance_id", "repo", "patch_bucket"}
                            for x in manifest["holdout"]))

    def test_private_cpu_kernel_never_embeds_task_body_or_trains(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = render(ROOT, Path(tmp) / "candidate",
                            "kolihhan/gemma4-evidence-gold-ci-test")
            meta = json.loads((output / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_gpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["model_sources"], [])
            self.assertEqual(meta["competition_sources"], ["gemma-4-developer-agent"])
            self.assertEqual({p.name for p in output.iterdir()},
                             {"kernel-metadata.json", "gold_control_sweep.py"})
            source = (output / "gold_control_sweep.py").read_text()
            compile(source, "gold_control_sweep.py", "exec")
            self.assertNotIn("__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__", source)

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out"
            render(ROOT, dest, "kolihhan/gemma4-evidence-gold-test")
            with self.assertRaises(ValueError):
                render(ROOT, dest, "kolihhan/gemma4-evidence-gold-test")


if __name__ == "__main__":
    unittest.main()
