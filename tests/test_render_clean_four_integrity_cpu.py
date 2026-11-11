"""No model inference: synthetic tests for frozen clean four-task kernel."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from scripts.render_clean_four_integrity_cpu import render, VERSION


class FourTaskKernelTests(unittest.TestCase):
    def test_exact_prequalified_tasks_and_no_gpu(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"kernel"
            report=render(root,out,"kolihhan/gemma4-cleanfour-cpu-12345678")
            meta=json.loads((out/"kernel-metadata.json").read_text())
            code=(out/"clean_four_integrity_cpu.py").read_text()
            self.assertEqual(report["tasks"],[
                "fastapi_14458","fastapi_15589","rich_3894","rich_3905"
            ])
            self.assertEqual(code.count("gemma4-clean-four-integrity-v1"),1)
            self.assertEqual(code.count("def evaluate_controls()"),1)
            self.assertEqual(meta["enable_gpu"],False)
            self.assertEqual(meta["enable_internet"],False)
            self.assertEqual(meta["model_sources"],[])
            self.assertTrue(meta["is_private"])
            compile(code, "clean_four_integrity_cpu.py", "exec")

    def test_duplicate_refuse(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"kernel"
            render(root,out,"kolihhan/gemma4-cleanfour-cpu-12345678")
            with self.assertRaises(FileExistsError):
                render(root,out,"kolihhan/gemma4-cleanfour-cpu-12345678")

    def test_no_unverified_historical_ids(self):
        self.assertEqual(VERSION,"gemma4-clean-four-integrity-v1")


if __name__=="__main__":
    unittest.main()
