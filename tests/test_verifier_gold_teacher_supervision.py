import json
import unittest

from kaggle.verifier_gold_teacher_runtime import (
    build_teacher_supervision_record,
    load_targeted_test_plan,
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
                    "instance_id": "fastapi_2",
                    "command": "python -m pytest tests/test_api.py::test_case -q",
                },
            ],
        }
        self.assertEqual(
            load_targeted_test_plan(
                json.dumps(plan),
                {"rich_1", "fastapi_2", "rich_3"},
            ),
            {
                "rich_1": "pytest tests/test_panel.py -q",
                "fastapi_2": "python -m pytest tests/test_api.py::test_case -q",
            },
        )

    def test_rejects_pending_broad_duplicate_or_non_clean_targets(self):
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
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    load_targeted_test_plan(json.dumps(payload), {"rich_1"})


class TeacherSupervisionRecordTests(unittest.TestCase):
    def test_builds_approved_verified_submit_from_deterministic_passing_evidence(self):
        record = build_teacher_supervision_record(
            instance_id="rich_1",
            problem_description="Fix the panel rendering regression.",
            targeted_command="pytest tests/test_panel.py -q",
            pre_diff={"exit_code": 0, "output": "diff --git a/rich/panel.py b/rich/panel.py\n"},
            targeted_test={"exit_code": 0, "output": "2 passed\n"},
            final_diff={"exit_code": 0, "output": "diff --git a/rich/panel.py b/rich/panel.py\n"},
        )
        self.assertTrue(record["approved"])
        self.assertEqual(record["label"], "verified_submit")
        self.assertEqual(record["source"], "gold_patch_targeted_test")
        self.assertEqual(
            [step["tool"] for step in record["steps"]],
            ["run_command", "run_command", "run_command", "submit_patch"],
        )
        self.assertEqual(record["steps"][1]["arguments"]["command"], "pytest tests/test_panel.py -q")
        self.assertNotIn("reference_patch", record)
        self.assertNotIn("gold_patch", record)

    def test_failing_or_missing_deterministic_evidence_stays_unapproved(self):
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


if __name__ == "__main__":
    unittest.main()
