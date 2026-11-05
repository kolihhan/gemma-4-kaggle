"""Validate no-op CPU renderer against a synthetic metadata-only gold screen."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory
from scripts.render_discriminating_evidence_noop import (
    load_gold_pass_items, render,
)

EXPECTED_RUN = 42066105011


def mock_gold(path: Path, keep_count: int) -> list[str]:
    chosen = build_exploratory(ROOT)
    ids = (chosen["pilot_ids"] + chosen["exploratory_ids"]
           + chosen["replacement_ids"])
    rows = [{
        "instance_id": i,
        "repo": "Textualize/rich" if i.startswith("rich_") else "fastapi/fastapi",
        "status": "completed",
        "gold_pass": n < keep_count,
        "test_exit_code": 0 if n < keep_count else 1,
        "error_type": None,
    } for n, i in enumerate(ids)]
    data = {
        "version": "discriminating-evidence-v0-exploratory-gold-screen",
        "source_run_id": EXPECTED_RUN,
        "source_selector_sha256": chosen["selection_digest_sha256"],
        "screened": 30,
        "gold_pass_count": keep_count,
        "results": rows,
        "contains_raw_patch_or_task_text": False,
        "certifies_blind": False,
        "model_evaluation_executed": False,
    }
    path.write_text(json.dumps(data))
    return ids


class EvidenceNoopTests(unittest.TestCase):
    def test_gold_pass_items_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "gold.json"
            original = mock_gold(p, 17)
            selected = load_gold_pass_items(ROOT, p)
            self.assertEqual([x["instance_id"] for x in selected], original[:17])

    def test_renders_private_cpu_kernel_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "gold.json"
            mock_gold(p, 21)
            out = render(ROOT, root / "out", "kolihhan/gemma4-evidence-noop-test", p)
            meta = json.loads((out / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_gpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["model_sources"], [])
            self.assertEqual({f.name for f in out.iterdir()},
                             {"kernel-metadata.json", "evidence_noop_screen.py"})
            source = (out / "evidence_noop_screen.py").read_text()
            compile(source, "evidence_noop_screen.py", "exec")
            self.assertIn("len(ids) != 21", source)
            self.assertNotIn("len(ids) != 19", source)
            self.assertIn("evidence_noop_screen.json", source)

    def test_rejects_wrong_source_run_and_mismatched_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "gold.json"
            mock_gold(p, 17)
            data = json.loads(p.read_text())
            data["source_run_id"] = 7
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_gold_pass_items(ROOT, p)


if __name__ == "__main__":
    unittest.main()
