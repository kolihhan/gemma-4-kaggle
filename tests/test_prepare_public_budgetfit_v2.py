"""Deterministic no-training tests for the attributed public V2 reference builder."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import prepare_public_budgetfit_v2 as candidate

ROOT = Path(__file__).resolve().parents[1]
FAKE_FILES = {
    "agent.yaml": (
        "name: swe_agent\nmodel: gemma-4-31b-it-qat-w4a16-ct\n"
        "instruction: !include prompts/system.md\n"
        "tools:\n  - run_command\n  - submit_patch\n"
    ),
    "configs/sampling.yaml": "thinking_config:\n  thinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  max_tool_calls: 28\n  max_time_minutes: 8\n",
    "prompts/system.md": "test-only synthetic fixture; not a competition prompt\n",
}


def fake_archive(files=FAKE_FILES):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content.encode("utf-8"))
    return buf.getvalue()


class PublicBudgetFitV2Contract(unittest.TestCase):
    def fake_reference(self):
        data = fake_archive()
        return data, {
            "EXPECTED_ZIP_SHA256": candidate.digest(data),
            "EXPECTED_MEMBERS": {
                name: candidate.digest(body.encode("utf-8"))
                for name, body in FAKE_FILES.items()
            },
        }

    def test_real_public_version_pins_are_nonempty_and_distinct(self):
        self.assertEqual(candidate.SOURCE_VERSION, 2)
        self.assertEqual(candidate.SOURCE_LICENSE, "Apache-2.0")
        self.assertEqual(candidate.SOURCE_REPORTED_PUBLIC_SCORE, "0.18")
        self.assertEqual(len(candidate.EXPECTED_ZIP_SHA256), 64)
        self.assertEqual(len(set(candidate.EXPECTED_MEMBERS.values())), 4)
        self.assertNotIn("adapters/", candidate.EXPECTED_MEMBERS)

    def test_tampered_or_invalid_archive_rejected(self):
        data, overrides = self.fake_reference()
        with patch.multiple(candidate, **overrides):
            self.assertEqual(len(candidate.validate_source_zip(data)), 4)
            with self.assertRaisesRegex(ValueError, "not the pinned"):
                candidate.validate_source_zip(data + b"tamper")

    def test_extra_member_and_wrong_model_rejected_even_with_hash_override(self):
        extras = dict(FAKE_FILES)
        extras["extra.py"] = "print('no')"
        data = fake_archive(extras)
        with patch.multiple(candidate, EXPECTED_ZIP_SHA256=candidate.digest(data)):
            with self.assertRaisesRegex(ValueError, "unexpected ZIP members"):
                candidate.validate_source_zip(data)
        bad = dict(FAKE_FILES)
        bad["agent.yaml"] = bad["agent.yaml"].replace("gemma-4-31b", "gemma-4-e4b")
        data = fake_archive(bad)
        overrides = {
            "EXPECTED_ZIP_SHA256": candidate.digest(data),
            "EXPECTED_MEMBERS": {k: candidate.digest(v.encode()) for k, v in bad.items()},
        }
        with patch.multiple(candidate, **overrides):
            with self.assertRaisesRegex(ValueError, "31B model"):
                candidate.validate_source_zip(data)

    def test_private_cpu_builder_reproduces_exact_bytes(self):
        data, overrides = self.fake_reference()
        with tempfile.TemporaryDirectory() as td, patch.multiple(candidate, **overrides):
            folder = Path(td) / "builder"
            candidate.render(data, folder, "kolihhan/public-v2-test")
            meta = json.loads((folder / "kernel-metadata.json").read_text())
            self.assertTrue(meta["is_private"])
            self.assertFalse(meta["enable_gpu"])
            self.assertFalse(meta["enable_internet"])
            self.assertEqual(meta["model_sources"], [])
            self.assertEqual(meta["competition_sources"], [candidate.COMPETITION])
            output = Path(td) / "output"
            env = {**os.environ, "OUTPUT_DIR": str(output)}
            process = subprocess.run(
                [sys.executable, str(folder / candidate.BUILD_SCRIPT)],
                env=env, capture_output=True, text=True
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual((output / "submission.zip").read_bytes(), data)
            self.assertIn("EXACT_ZIP=PASS", process.stdout)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                candidate.render(data, folder, "kolihhan/public-v2-test")
            with self.assertRaisesRegex(ValueError, "invalid owner"):
                candidate.render(data, Path(td) / "else", "attacker/not-valid")


if __name__ == "__main__":
    unittest.main()
