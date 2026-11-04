"""Static, GPU-free contract for the optional Colab 31B deployment smoke."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "capacity_31b_colab_smoke.ipynb"


class CapacityColabSmokeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = cls.data["cells"]
        cls.sources = [
            "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
            for cell in cls.cells
        ]

    def test_valid_notebook_and_compile_every_code_cell(self):
        self.assertEqual(self.data["nbformat"], 4)
        self.assertGreaterEqual(len(self.cells), 5)
        self.assertEqual(self.cells[0]["cell_type"], "markdown")
        for index, (cell, source) in enumerate(zip(self.cells, self.sources)):
            if cell["cell_type"] != "code":
                continue
            self.assertEqual(cell["outputs"], [])
            self.assertIsNone(cell["execution_count"])
            compile(source, f"<colab-cell-{index}>", "exec")

    def test_model_and_original_probe_are_frozen(self):
        text = "\n".join(self.sources)
        for required in (
            'MODEL_ID = "google/gemma-4-31B-it-qat-w4a16-ct"',
            "MAX_MODEL_LEN = 32768",
            "GPU_MEMORY_UTILIZATION = 0.90",
            'SOURCE_COMMIT = "b13087b402ceef0aa0aa2ce55d1f7aa2c99108c3"',
            'SOURCE_BLOB_SHA1 = "c458c21c04e0b456cb3b0e01f6f145129445524c"',
            '"probe_plain"',
            '"probe_scalar_tool"',
            '"probe_array_tool"',
            '"--tool-call-parser", "gemma4"',
            '"--reasoning-parser", "gemma4"',
            '"--tensor-parallel-size", "1"',
            '"competition_tasks_used": 0',
            '"official_kaggle_scorer": False',
        ):
            self.assertIn(required, text)

    def test_resource_gate_precedes_download_install_and_startup(self):
        self.assertIn("MIN_FREE_GPU_GIB = 32.0", self.sources[1])
        self.assertIn("MIN_FREE_DISK_GIB = 30.0", self.sources[1])
        self.assertIn("raise RuntimeError", self.sources[1])
        self.assertIn("if not eligible:", self.sources[1])
        self.assertNotIn("pip", self.sources[1])
        self.assertNotIn("subprocess.Popen", self.sources[1])
        self.assertIn("pip", self.sources[2])
        self.assertIn("urlopen", self.sources[3])
        self.assertIn("Popen", self.sources[4])
        self.assertIn("os.killpg", self.sources[4])

    def test_no_competition_data_distribution_or_hidden_evaluation(self):
        text = "\n".join(self.sources)
        for forbidden in (
            "kaggle kernels push",
            "kaggle competitions submit",
            "tasks.jsonl",
            "competition_sources",
            "reference_patch",
            "hidden_test",
            "solution_patch",
            "submit_patch",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("not the official Kaggle scorer", text)
        self.assertIn("no benchmark tasks", text.lower())


if __name__ == "__main__":
    unittest.main()
