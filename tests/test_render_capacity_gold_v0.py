"""CPU-only tests for private capacity gold-eligibility kernel renderer."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "capacity_gold_renderer", ROOT / "scripts" / "render_capacity_gold_v0.py"
)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)


class CapacityGoldRendererTests(unittest.TestCase):
    def test_private_no_gpu_no_model_no_data_mirror(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            out = renderer.render(ROOT, p / "out", "kolihhan/capacity-gold-test")
            metadata = json.loads((out / "kernel-metadata.json").read_text())
            self.assertTrue(metadata["is_private"])
            self.assertFalse(metadata["enable_gpu"])
            self.assertFalse(metadata["enable_internet"])
            self.assertEqual(metadata["model_sources"], [])
            self.assertEqual(metadata["competition_sources"], ["gemma-4-developer-agent"])
            files = {x.name for x in out.iterdir()}
            self.assertEqual(files, {"kernel-metadata.json", "gold_control_sweep.py"})
            source = (out / "gold_control_sweep.py").read_text()
            self.assertNotIn('EMBEDDED_HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"', source)
            self.assertNotIn("tasks.jsonl\": \"", source)
            compile(source, "gold_control_sweep.py", "exec")

    def test_gold_eligibility_is_metadata_only_and_has_all_16_candidate_ids(self):
        manifest = renderer.create_gold_manifest(ROOT)
        self.assertEqual(manifest["version"], "verifier-lora-v0")
        self.assertEqual(len(manifest["holdout"]), 16)
        ids = [x["instance_id"] for x in manifest["holdout"]]
        self.assertEqual(len(set(ids)), 16)
        self.assertTrue(all(x["repo"] in {"Textualize/rich", "fastapi/fastapi"}
                            for x in manifest["holdout"]))
        self.assertFalse(any("patch" in str(v).lower() for x in manifest["holdout"]
                             for k, v in x.items() if k != "patch_bucket"))


if __name__ == "__main__":
    unittest.main()
