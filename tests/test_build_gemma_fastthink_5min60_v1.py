"""Frozen 0.18 champion vs 31B fast-thinking single-variable CPU tests."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_gemma_fastthink_5min60_v1 as fast
from scripts import build_v2_toolcap_submission as parent
from scripts import build_toolcap60_timeout_recovery as scored
from tests.test_build_toolcap60_timeout_recovery import V2


class FastThinkCandidateTests(unittest.TestCase):
    def setUp(self):
        m = patch.object(parent, "validate_source_zip", return_value=dict(V2))
        m.start()
        self.addCleanup(m.stop)

    def test_only_reasoning_budget_changes(self):
        a = scored.files_for_candidate(b"pinned")
        b = fast.files_for_candidate(b"pinned")
        self.assertEqual(set(a), set(b))
        self.assertEqual([k for k in a if a[k] != b[k]], ["configs/sampling.yaml"])
        self.assertEqual(b["configs/sampling.yaml"], a["configs/sampling.yaml"].replace(
            "thinking_budget: 4096", "thinking_budget: 2048"))
        for k in ("agent.yaml", "prompts/system.md", "eval_config.yaml"):
            self.assertEqual(a[k], b[k])

    def test_deterministic_zip_no_model_or_training(self):
        p = fast.build(b"pinned")
        self.assertEqual(p, fast.build(b"pinned"))
        self.assertEqual(hashlib.sha256(p).hexdigest(),fast.report(b"pinned")["candidate_sha256"])
        with zipfile.ZipFile(io.BytesIO(p)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()), set(V2))
            self.assertIn(b"thinking_budget: 2048",z.read("configs/sampling.yaml"))

    def test_drift_fails_closed(self):
        prior = dict(V2)
        prior["configs/sampling.yaml"] = "thinking_budget: 3072\n"
        with patch.object(parent,"validate_source_zip",return_value=prior):
            with self.assertRaisesRegex(ValueError, "control drift"):
                fast.files_for_candidate(b"pinned")

    def test_not_a_claim_of_score(self):
        d=fast.report(b"pinned")
        self.assertFalse(d["training"])
        self.assertFalse(d["official_submission"])
        self.assertIsNone(d["independent_model_quality_gain"])
        self.assertEqual(d["task_minutes"],5)
        self.assertEqual(d["tool_calls"],60)


if __name__ == "__main__":
    unittest.main()
