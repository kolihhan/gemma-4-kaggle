"""Kaggle CLI may report a rejected push while returning exit code zero."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "capacity_push_gate", ROOT / "scripts" / "check_capacity_31b_push_v0.py"
)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


class KagglePushGateTests(unittest.TestCase):
    def test_success_needs_confirmed_version(self):
        self.assertEqual(gate.classify_push(
            "Kernel version 1 successfully pushed. Please check progress at https://...",
            0
        ), "CONFIRMED")

    def test_quota_error_with_zero_exit_is_hard_stop(self):
        self.assertEqual(gate.classify_push(
            "Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.",
            0
        ), "BLOCKED_GPU_QUOTA")

    def test_other_push_error_with_zero_exit_is_hard_stop(self):
        self.assertEqual(gate.classify_push(
            "Kernel push error: Access to a resource was denied.", 0
        ), "REJECTED")

    def test_no_confirmation_or_nonzero_exit_fails_closed(self):
        self.assertEqual(gate.classify_push("", 0), "UNCONFIRMED")
        self.assertEqual(gate.classify_push(
            "Kernel version 1 successfully pushed.", 1
        ), "CLIENT_EXIT_NONZERO")

    def test_generic_404_is_not_evidence_of_model_runtime_failure(self):
        self.assertEqual(gate.classify_push(
            "404 Client Error: Not Found for url: GetKernelSessionStatus",
            0
        ), "UNCONFIRMED")


if __name__ == "__main__":
    unittest.main()
