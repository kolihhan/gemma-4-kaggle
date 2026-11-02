import json
import unittest

from kaggle.verifier_gold_teacher_supervision import (
    build_teacher_safe_stop_record,
    build_teacher_supervision_record,
    load_targeted_test_plan,
)


INLINE_ASSERT = (
    "python -c \"import requests, requests.adapters; "
    "a=requests.adapters.HTTPAdapter(); "
    "p=requests.Request(method='GET', url='http://127.0.0.1:10000//v:h').prepare(); "
    "assert a.request_url(p, {}) == '/v:h'\""
)


class TargetedTestPlanTests(unittest.TestCase):
    def test_loads_frozen_targeted_tests_for_clean_training_ids_only(self):
        plan = {
            "version": "verifier-lora-v0-targeted-tests",
            "status": "frozen",
            "targets": [
                {
                    "instance_id": "rich_1",
                    "command": "pytest tests/test_panel.py -q",
                },
                {
                    "instance_id": "requests_2",
                    "command": INLINE_ASSERT,
                },
            ],
        }
        self.assertEqual(
            load_targeted_test_plan(
                json.dumps(plan),
                {"rich_1", "requests_2", "rich_3"},
            ),
            {
                "rich_1": "pytest tests/test_panel.py -q",
                "requests_2": INLINE_ASSERT,
            },
        )

    def test_rejects_pending_broad_duplicate_non_clean_or_unsafe_targets(self):
        cases = [
            {
                "version": "verifier-lora-v0-targeted-tests",
                "status": "pending",
                "targets": [{"instance_id": "rich_1", "command": "pytest tests/test_panel.py -q"}],
            },
            {
                "version": "verifier-lora-v0-targeted-tests",
                "status": "frozen",
                "targets": [{"instance_id": "rich_1", "command": "pytest -q"}],
            },
            {
                "version": "verifier-lora-v0-targeted-tests",
                "status": "frozen",
                "targets": [
                    {"instance_id": "rich_1", "command": "pytest tests/test_panel.py -q"},
                    {"instance_id": "rich_1", "command": "pytest tests/test_panel.py -q"},
                ],
            },
            {
                "version": "verifier-lora-v0-targeted-tests",
                "status": "frozen",
                "targets": [{"instance_id": "blind_1", "command": "pytest tests/test_api.py -q"}],
            },
            {
                "version": "verifier-lora-v0-targeted-tests",
                "status": "frozen",
                "targets": [
                    {
                        "instance_id": "rich_1",
                        "command": "python -c \"print('no assertion')\"",
                    }
                ],
            },
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    load_targeted_test_plan(json.dumps(payload), {"rich_1"})


class TeacherSupervisionRecordTests(unittest.TestCase):
    def test_builds_approved_verified_submit_from_deterministic_passing_evidence(self):
        diff = "diff --git a/rich/panel.py b/rich/panel.py\n"
        record = build_teacher_supervision_record(
            instance_id="rich_1",
            problem_description="Fix the panel rendering regression.",
            targeted_command=INLINE_ASSERT,
            pre_diff={"exit_code": 0, "output": diff},
            targeted_test={"exit_code": 0, "output": ""},
            final_diff={"exit_code": 0, "output": diff},
        )
        self.assertTrue(record["approved"])
        self.assertEqual(record["example_id"], "rich_1:gold-pass")
        self.assertEqual(record["label"], "verified_submit")
        self.assertEqual(record["source"], "gold_patch_targeted_test")
        self.assertEqual(
            [step["tool"] for step in record["steps"]],
            ["run_command", "run_command", "run_command", "submit_patch"],
        )
        self.assertEqual(record["steps"][1]["arguments"]["command"], INLINE_ASSERT)
        self.assertNotIn("reference_patch", record)
        self.assertNotIn("gold_patch", record)

    def test_builds_approved_safe_stop_from_clean_base_failure(self):
        record = build_teacher_safe_stop_record(
            instance_id="requests_2",
            problem_description="Trim excess leading path separators.",
            targeted_command=INLINE_ASSERT,
            pre_diff={"exit_code": 0, "output": ""},
            targeted_test={"exit_code": 1, "output": "AssertionError\n"},
            final_diff={"exit_code": 0, "output": ""},
        )
        self.assertTrue(record["approved"])
        self.assertEqual(record["example_id"], "requests_2:base-fail")
        self.assertEqual(record["label"], "safe_stop")
        self.assertEqual(record["source"], "base_targeted_failure")
        self.assertNotIn("submit_patch", [step["tool"] for step in record["steps"]])

    def test_safe_stop_rejects_passing_or_mutating_base_state(self):
        cases = [
            (
                {"exit_code": 0, "output": ""},
                {"exit_code": 0, "output": "passed"},
                {"exit_code": 0, "output": ""},
                "targeted_test_unexpectedly_passed",
            ),
            (
                {"exit_code": 0, "output": ""},
                {"exit_code": 1, "output": "failed"},
                {"exit_code": 0, "output": "diff --git a/a.py b/a.py\n"},
                "base_diff_changed_during_test",
            ),
        ]
        for pre_diff, targeted_test, final_diff, expected_flag in cases:
            with self.subTest(expected_flag=expected_flag):
                record = build_teacher_safe_stop_record(
                    instance_id="rich_1",
                    problem_description="Fix it.",
                    targeted_command=INLINE_ASSERT,
                    pre_diff=pre_diff,
                    targeted_test=targeted_test,
                    final_diff=final_diff,
                )
                self.assertFalse(record["approved"])
                self.assertIsNone(record["label"])
                self.assertIn(expected_flag, record["audit_flags"])

    def test_failing_deterministic_evidence_stays_unapproved(self):
        for field in ("pre_diff", "targeted_test", "final_diff"):
            evidence = {
                "pre_diff": {"exit_code": 0, "output": "diff"},
                "targeted_test": {"exit_code": 0, "output": "passed"},
                "final_diff": {"exit_code": 0, "output": "diff"},
            }
            evidence[field] = {"exit_code": 1, "output": "failed"}
            with self.subTest(field=field):
                record = build_teacher_supervision_record(
                    instance_id="rich_1",
                    problem_description="Fix it.",
                    targeted_command="pytest tests/test_panel.py -q",
                    **evidence,
                )
                self.assertFalse(record["approved"])
                self.assertIsNone(record["label"])
                self.assertNotIn("submit_patch", [step["tool"] for step in record["steps"]])

    def test_empty_or_changed_diff_never_becomes_positive_supervision(self):
        cases = [
            (
                {"exit_code": 0, "output": ""},
                {"exit_code": 0, "output": ""},
                "empty_diff",
            ),
            (
                {"exit_code": 0, "output": "diff --git a/a.py b/a.py\n-old\n+new\n"},
                {"exit_code": 0, "output": "diff --git a/a.py b/a.py\n-old\n+different\n"},
                "diff_changed_during_test",
            ),
        ]
        for pre_diff, final_diff, expected_flag in cases:
            with self.subTest(expected_flag=expected_flag):
                record = build_teacher_supervision_record(
                    instance_id="rich_1",
                    problem_description="Fix it.",
                    targeted_command="pytest tests/test_panel.py -q",
                    pre_diff=pre_diff,
                    targeted_test={"exit_code": 0, "output": "2 passed\n"},
                    final_diff=final_diff,
                )
                self.assertFalse(record["approved"])
                self.assertIsNone(record["label"])
                self.assertIn(expected_flag, record["audit_flags"])
                self.assertNotIn("submit_patch", [step["tool"] for step in record["steps"]])


if __name__ == "__main__":
    unittest.main()
