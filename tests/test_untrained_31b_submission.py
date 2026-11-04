"""Static and deterministic safety checks for official untrained 31B submission."""
import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import render_untrained_31b_submission as sub

ROOT = Path(__file__).resolve().parents[1]


class Untrained31BSubmissionTests(unittest.TestCase):
    def test_exactly_one_model_line_changed_and_no_adapter(self):
        control, candidate = sub.payload(ROOT)
        self.assertEqual(sorted(control), sorted(candidate))
        self.assertEqual(len(control), 5)
        self.assertIn(f"model: {sub.BASE_MODEL}", control["agent.yaml"])
        self.assertIn(f"model: {sub.NEW_MODEL}", candidate["agent.yaml"])
        self.assertEqual(
            candidate["agent.yaml"].replace(sub.NEW_MODEL, sub.BASE_MODEL, 1),
            control["agent.yaml"],
        )
        for name in control:
            if name != "agent.yaml":
                self.assertEqual(candidate[name], control[name])
        self.assertTrue(all("adapter:" not in content for content in candidate.values()))
        self.assertTrue(all(".safetensors" not in content for content in candidate.values()))

    def test_zip_exact_deterministic_contents(self):
        _, candidate = sub.payload(ROOT)
        first = sub.create_zip_bytes(candidate)
        second = sub.create_zip_bytes(candidate)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as z:
            self.assertEqual(sorted(z.namelist()), sorted(candidate))
            self.assertEqual(
                z.read("agent.yaml").decode("utf-8"), candidate["agent.yaml"]
            )
            self.assertFalse(any(name.startswith("adapters/") for name in z.namelist()))

    def test_kernel_cpu_private_and_compiles_with_embedded_zip(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "private"
            sub.render(ROOT, out, "kolihhan/gemma4-31b-untrained-contract")
            meta = json.loads((out / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_gpu"])
            self.assertFalse(meta["enable_tpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["model_sources"], [])
            self.assertEqual(meta["competition_sources"], [sub.COMPETITION])
            self.assertEqual(set(meta), {
                "id", "title", "code_file", "language", "kernel_type",
                "is_private", "enable_gpu", "enable_tpu", "enable_internet",
                "competition_sources", "dataset_sources", "kernel_sources",
                "model_sources"
            })
            code = (out / sub.KERNEL_FILE).read_text(encoding="utf-8")
            compile(code, sub.KERNEL_FILE, "exec")
            self.assertIn("/kaggle/working/submission.zip", code)
            self.assertIn("NO_TRAINING=TRUE", code)
            self.assertNotIn("tasks.jsonl", code)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                sub.render(ROOT, out, "kolihhan/gemma4-31b-untrained-contract")

    def test_invalid_slug_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "invalid"):
                sub.render(ROOT, Path(td)/"out", "notkolihhan/unsafe")

    def test_frozen_hashes_still_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            from shutil import copytree
            folder = Path(td) / "submission"
            copytree(ROOT / "submission", folder)
            agent = folder / "agent.yaml"
            agent.write_text(agent.read_text()+"\n# unreviewed mutation\n")
            with self.assertRaisesRegex(ValueError, "hash drift"):
                sub.payload(Path(td))


if __name__ == "__main__":
    unittest.main()
