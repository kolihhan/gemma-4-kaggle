"""Fail-closed tests for the metadata-only CPU replacement no-op renderer."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts import render_capacity_replacement_noop_v0 as renderer
from scripts import render_capacity_replacement_gold_v0 as gold_renderer

ROOT = Path(__file__).resolve().parents[1]


class CapacityReplacementNoopRendererTests(unittest.TestCase):
    def test_frozen_gold_pass_only_with_original_order(self):
        frozen = gold_renderer.create_manifest(ROOT)["holdout"]
        selected = renderer.get_gold_pass_items(ROOT)
        data = json.loads((ROOT / renderer.GOLD_FILE).read_text(encoding="utf-8"))
        self.assertEqual(len(frozen), 16)
        self.assertEqual(len(selected), 10)
        self.assertEqual(len({x["instance_id"] for x in selected}), 10)
        self.assertEqual(selected, [
            {"instance_id": x["instance_id"], "repo": x["repo"]}
            for x in data["results"] if x["gold_pass"]
        ])
        self.assertEqual(sum(x["repo"]=="Textualize/rich" for x in selected), 4)
        self.assertEqual(sum(x["repo"]=="fastapi/fastapi" for x in selected), 6)

    def test_render_is_private_no_gpu_no_model_and_fails_on_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "private"
            renderer.render(ROOT, out, "kolihhan/replacement-noop-smoke")
            metadata = json.loads((out / "kernel-metadata.json").read_text())
            self.assertEqual(metadata["id"], "kolihhan/replacement-noop-smoke")
            self.assertTrue(metadata["is_private"])
            self.assertFalse(metadata["enable_gpu"])
            self.assertFalse(metadata["enable_tpu"])
            self.assertFalse(metadata["enable_internet"])
            self.assertEqual(metadata["model_sources"], [])
            self.assertEqual(metadata["competition_sources"], ["gemma-4-developer-agent"])
            self.assertEqual(
                {p.name for p in out.iterdir()},
                {"kernel-metadata.json", renderer.SOURCE_FILENAME},
            )
            source = (out / renderer.SOURCE_FILENAME).read_text()
            compile(source, renderer.SOURCE_FILENAME, "exec")
            self.assertIn(renderer.VERSION, source)
            self.assertIn(renderer.RESULT_FILENAME, source)
            self.assertIn("if len(ids) != 10 or len(set(ids)) != 10:", source)
            self.assertIn("'requested': 10", source)
            self.assertNotIn("('rich_3061',", source)
            for item in renderer.get_gold_pass_items(ROOT):
                self.assertIn(repr((item["instance_id"], item["repo"])), source)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                renderer.render(ROOT, out, "kolihhan/replacement-noop-smoke")

    def test_frozen_gold_metadata_integrity_gates(self):
        original = json.loads((ROOT / renderer.GOLD_FILE).read_text(encoding="utf-8"))
        cases = [
            ("wrong gold source", lambda d: d.update(source_run_id=1)),
            ("wrong artifact", lambda d: d.update(artifact_id=42)),
            ("wrong content hash", lambda d: d.update(artifact_zip_sha256="unknown")),
            ("wrong selector", lambda d: d.update(source_selector_sha256="unknown")),
            ("wrong count", lambda d: d.update(gold_pass_count=9)),
            ("reordered tasks", lambda d: d["results"].reverse()),
            ("unexpected result", lambda d: d["results"][0].update(test_exit_code=1)),
            ("no raw task guarantees", lambda d: d.update(contains_raw_patch_or_task_text=True)),
        ]
        with tempfile.TemporaryDirectory() as td:
            for name, corrupt in cases:
                with self.subTest(name=name):
                    data = json.loads(json.dumps(original))
                    corrupt(data)
                    path = Path(td) / "override.json"
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        renderer.get_gold_pass_items(ROOT, path)


if __name__ == "__main__":
    unittest.main()
