"""CPU-only renderer tests for a model-only 31B startup/tool-parser smoke."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "capacity31_render", ROOT / "scripts" / "render_capacity_31b_startup_v0.py"
)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)


class Capacity31BStartupTests(unittest.TestCase):
    def test_render_has_one_private_l4x4_model_and_no_task_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = renderer.render(
                ROOT, Path(tmp) / "out", "kolihhan/capacity31b-standalone-test"
            )
            files = {p.name for p in path.iterdir()}
            self.assertEqual(files, {"kernel-metadata.json", "capacity_31b_startup_v0.py"})
            meta = json.loads((path / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertTrue(meta["enable_gpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["machine_shape"], "NvidiaL4")
            self.assertEqual(meta["competition_sources"], ["gemma-4-developer-agent"])
            self.assertEqual(meta["model_sources"], [
                "google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2"
            ])
            code = (path / "capacity_31b_startup_v0.py").read_text()
            compile(code, "capacity_31b_startup_v0.py", "exec")
            self.assertNotIn("tasks.jsonl", code)
            self.assertNotIn("reference_patch", code)
            self.assertNotIn("evaluate_task", code)
            self.assertIn("VllmServer", code)
            self.assertIn("get_code_subgraph", code)
            self.assertIn("probe_scalar_tool", code)
            self.assertIn("probe_array_tool", code)

    def test_render_does_not_overwrite_or_accept_wrong_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "render"
            with self.assertRaises(ValueError):
                renderer.render(ROOT, dst, "someoneelse/kernel")
            renderer.render(ROOT, dst, "kolihhan/capacity31b-test")
            with self.assertRaises(ValueError):
                renderer.render(ROOT, dst, "kolihhan/capacity31b-test")

    def test_no_scorer_or_submission_side_effects(self):
        code = (ROOT / "kaggle" / "capacity_31b_startup_v0.py").read_text()
        forbidden = (
            "kaggle competitions submit", "kaggle kernels push",
            "submit_patch", "reference_patch", "agent_patch", "tasks.jsonl",
        )
        for term in forbidden:
            self.assertNotIn(term, code)


if __name__ == "__main__":
    unittest.main()
