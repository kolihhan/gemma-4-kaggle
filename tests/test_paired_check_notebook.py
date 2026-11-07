"""Execute the standalone CPU notebook and protect the exact V2 settings."""

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from scripts.build_paired_check_candidate import archive, notebook, payload
from scripts.prepare_public_budgetfit_v2 import validate_source_zip


SOURCE = Path(__file__).resolve().parents[2] / "kaggle-reads/budgetfit-v2-exact.zip"


class NotebookPackagingTests(unittest.TestCase):
    def test_clean_cpu_process_builds_reproducible_matched_archives(self):
        source = SOURCE.read_bytes()
        original = validate_source_zip(source)
        document = notebook(source)
        self.assertEqual(document["nbformat"], 4)
        code = document["cells"][1]["source"]
        observed = {}
        with tempfile.TemporaryDirectory() as directory:
            for index, mode in enumerate(("paired", "paired", "repeat")):
                output = Path(directory) / str(index)
                process = subprocess.run(
                    [sys.executable, "-c", code.replace('ARM = "paired"', f'ARM = "{mode}"', 1)],
                    env={**os.environ, "OUTPUT_DIR": str(output)},
                    cwd=directory, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                data = (output / "submission.zip").read_bytes()
                self.assertEqual(data, archive(payload(source, mode)))
                if mode in observed:
                    self.assertEqual(data, observed[mode])
                observed[mode] = data
                with zipfile.ZipFile(io.BytesIO(data)) as zipped:
                    self.assertIsNone(zipped.testzip())
                    for name in ("prompts/system.md", "configs/sampling.yaml", "eval_config.yaml"):
                        self.assertEqual(zipped.read(name), original[name].encode())
                    self.assertEqual(
                        zipped.read("agent.yaml").decode(),
                        original["agent.yaml"] + "skills:\n  - skills/repository-check\n",
                    )
        self.assertNotEqual(hashlib.sha256(observed["paired"]).digest(),
                            hashlib.sha256(observed["repeat"]).digest())
        self.assertEqual(json.loads(json.dumps(document)), document)


if __name__ == "__main__":
    unittest.main()
