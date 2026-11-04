import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capacity_noop", ROOT / "scripts" / "render_capacity_noop_v0.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class CapacityNoopTests(unittest.TestCase):
    def test_render_private_cpu_noop_only(self):
        with tempfile.TemporaryDirectory() as td:
            folder = module.render(
                ROOT, Path(td) / "out", "kolihhan/capacity-noop-contract-test"
            )
            meta = json.loads((folder / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_gpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["competition_sources"], ["gemma-4-developer-agent"])
            self.assertEqual(meta["model_sources"], [])
            self.assertEqual(
                {p.name for p in folder.iterdir()},
                {"kernel-metadata.json", "capacity_noop_screen.py"},
            )
            source = (folder / "capacity_noop_screen.py").read_text()
            compile(source, "capacity_noop_screen.py", "exec")
            self.assertNotIn("('rich_3061',", source)
            self.assertIn("capacity-v0-noop-screen-v1", source)
            self.assertIn("if len(ids) != 10 or len(set(ids)) != 10:", source)
            self.assertIn("'requested': 10", source)

    def test_all_and_only_gold_pass_candidates(self):
        data = module.get_gold_pass_items(ROOT)
        self.assertEqual(len(data), 10)
        self.assertEqual(len({v["instance_id"] for v in data}), 10)
        self.assertEqual(
            {v["repo"] for v in data},
            {"Textualize/rich", "fastapi/fastapi"},
        )
        self.assertEqual(
            [v["instance_id"] for v in data],
            [v["instance_id"] for v in module.load_gold_metadata(ROOT)["results"]
             if v["gold_pass"]],
        )

    def test_missing_or_inconsistent_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "gold.json"
            data = module.load_gold_metadata(ROOT)
            data["gold_pass_count"] = 11
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "gold"):
                module.load_gold_metadata(ROOT, path)


if __name__ == "__main__":
    unittest.main()
