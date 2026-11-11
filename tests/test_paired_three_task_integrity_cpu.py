"""Synthetic metadata tests for a model-free Kaggle three-task control."""
import unittest
from kaggle.paired_three_task_integrity_cpu import TASKS, classify, features


class IntegrityScreenTests(unittest.TestCase):
    def test_exact_preselected_paired_tasks(self):
        self.assertEqual([x[0] for x in TASKS], [
            "fastapi_14487", "rich_3782", "requests_7427",
        ])
        self.assertEqual(len(set(TASKS)), 3)

    def test_short_external_pointer_not_sufficient_evidence(self):
        f = features("Syntax padding. Fixes https://github.com/x/y/issues/1", "")
        self.assertTrue(f["has_external_url"])
        self.assertTrue(f["short_link_pointer_risk"])
        self.assertTrue(f["not_a_spec_sufficiency_verdict"])
        self.assertNotIn("statement", f)
        self.assertNotIn("url", f)

    def test_long_explicit_context_not_marked_pointer_only(self):
        f = features("Expected behavior: " + ("tests should cover the boundary. " * 40),
                     "Specific failing case.")
        self.assertFalse(f["short_link_pointer_risk"])
        self.assertFalse(f["has_external_url"])
        self.assertGreater(f["statement_chars"], 300)

    def test_control_matrix(self):
        ok = {"status": "completed", "resolved": True}
        fail = {"status": "completed", "resolved": False}
        err = {"status": "error", "resolved": None}
        self.assertEqual(classify(fail, ok), "informative_gold_pass_noop_fail")
        self.assertEqual(classify(ok, ok), "unhelpful_noop_already_passes")
        self.assertEqual(classify(fail, fail), "confounded_gold_fails")
        self.assertEqual(classify(ok, fail), "confounded_other")
        self.assertEqual(classify(err, ok), "evaluation_error")


if __name__ == "__main__":
    unittest.main()
