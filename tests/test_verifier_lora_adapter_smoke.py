"""Contract tests for the private, verifier-only frozen-adapter smoke."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kaggle import verifier_lora_adapter_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]


class FrozenAdapterSmokeTests(unittest.TestCase):
    def _workspace(self, root: Path):
        source = root / "input" / "frozen-adapter"
        source.mkdir(parents=True)
        blobs = {
            "adapter_config.json": b'{"r": 8, "peft_type": "LORA"}',
            "adapter_model.safetensors": b"synthetic-weights-not-an-adapter",
        }
        for name, body in blobs.items():
            (source / name).write_bytes(body)

        candidate = root / "submission"
        (candidate / "sub_agents").mkdir(parents=True)
        (candidate / "agent.yaml").write_text(
            "name: swe_e4b_coder\nmodel: gemma-4-e4b-it-qat-w4a16-ct\n", encoding="utf-8"
        )
        (candidate / "sub_agents" / "verifier.yaml").write_text(
            "name: swe_e4b_verifier\nmodel: gemma-4-e4b-it-qat-w4a16-ct\ntools:\n  - submit_patch\n",
            encoding="utf-8",
        )
        hashes = {name: hashlib.sha256(body).hexdigest() for name, body in blobs.items()}
        return source, candidate, blobs, hashes

    def test_loads_exact_private_adapter_into_verifier_only(self):
        with tempfile.TemporaryDirectory() as temp:
            source, candidate, blobs, hashes = self._workspace(Path(temp))
            root_before = (candidate / "agent.yaml").read_bytes()
            with (
                patch.object(runtime, "FROZEN_ADAPTER_SOURCE", source),
                patch.object(runtime, "EXPECTED_ADAPTER_SHA256", hashes),
                patch.object(runtime, "AGENT_DIR", candidate),
            ):
                runtime.install_frozen_verifier_adapter()

            self.assertEqual((candidate / "agent.yaml").read_bytes(), root_before)
            verifier = (candidate / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8")
            self.assertEqual(verifier.count("adapter: verifier_lora_v0"), 1)
            self.assertEqual(verifier.count("model: gemma-4-e4b-it-qat-w4a16-ct"), 1)
            for name, data in blobs.items():
                self.assertEqual(
                    (candidate / "adapters" / "verifier_lora_v0" / name).read_bytes(), data
                )

    def test_bad_hash_fails_before_writing_or_editing(self):
        with tempfile.TemporaryDirectory() as temp:
            source, candidate, _, hashes = self._workspace(Path(temp))
            (source / "adapter_model.safetensors").write_bytes(b"tampered")
            before = (candidate / "sub_agents" / "verifier.yaml").read_bytes()
            with (
                patch.object(runtime, "FROZEN_ADAPTER_SOURCE", source),
                patch.object(runtime, "EXPECTED_ADAPTER_SHA256", hashes),
                patch.object(runtime, "AGENT_DIR", candidate),
            ):
                with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                    runtime.install_frozen_verifier_adapter()
            self.assertFalse((candidate / "adapters").exists())
            self.assertEqual((candidate / "sub_agents" / "verifier.yaml").read_bytes(), before)

    def test_submission_candidate_stays_adapter_free_and_runtime_enables_lora(self):
        self.assertNotIn(
            "adapter:",
            (ROOT / "submission" / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8"),
        )
        self.assertNotIn(
            "adapter:",
            (ROOT / "submission" / "agent.yaml").read_text(encoding="utf-8"),
        )
        source = (ROOT / "kaggle" / "verifier_lora_adapter_runtime.py").read_text(encoding="utf-8")
        self.assertIn("enable_lora=True", source)
        self.assertIn("install_frozen_verifier_adapter()", source)
        self.assertIn("EXPECTED_ADAPTER_SHA256", source)
        self.assertNotIn("enable_lora=False", source)
        self.assertNotIn("kaggle competitions submit", source)


if __name__ == "__main__":
    unittest.main()
