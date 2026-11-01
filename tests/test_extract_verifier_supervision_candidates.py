import unittest

from scripts.extract_verifier_supervision_candidates import (
    extract_candidate,
    extract_problem_description,
)


class TestProblemDescription(unittest.TestCase):
    def test_extracts_problem_statement_before_budget(self):
        prompt = """You are evaluating a software engineering task for repository Textualize/rich.

Problem Statement:
Fix traceback recursion

Fixes issue 123

## Task Budget (Session terminates when any budget is exhausted)
- Time allowance: 5 minutes
"""
        self.assertEqual(
            extract_problem_description(prompt),
            "Fix traceback recursion\n\nFixes issue 123",
        )


class TestCandidateExtraction(unittest.TestCase):
    def trace(self):
        return {
            "schema_version": "1",
            "steps": [
                {
                    "source": "user",
                    "message": """You are evaluating a software engineering task for repository Textualize/rich.

Problem Statement:
Fix traceback recursion

## Task Budget (Session terminates when any budget is exhausted)
- Time allowance: 5 minutes
""",
                    "extra": {"author": "harness", "event_type": "task_prompt"},
                },
                {
                    "source": "agent",
                    "message": "coder work",
                    "tool_calls": [
                        {
                            "function_name": "run_command",
                            "arguments": {"command": "pytest"},
                        }
                    ],
                    "observation": {
                        "content": '{"status":"error","details":{"exit_code":1}}'
                    },
                    "extra": {"author": "swe_e4b_coder"},
                },
                {
                    "source": "agent",
                    "message": "inspect first",
                    "tool_calls": [
                        {
                            "function_name": "run_command",
                            "arguments": {"command": "git diff"},
                        }
                    ],
                    "observation": {
                        "content": '{"status":"ok","stdout":"diff","stderr":"","exit_code":0}'
                    },
                    "extra": {"author": "swe_e4b_verifier"},
                },
                {
                    "source": "agent",
                    "message": "run broad suite",
                    "tool_calls": [
                        {
                            "function_name": "run_command",
                            "arguments": {"command": "pytest -q"},
                        }
                    ],
                    "observation": {
                        "content": '{"status":"error","error_type":"CommandError","details":{"exit_code":2,"stdout":"collection failed","stderr":""}}'
                    },
                    "extra": {"author": "swe_e4b_verifier"},
                },
                {
                    "source": "agent",
                    "message": "submit anyway",
                    "tool_calls": [
                        {"function_name": "submit_patch", "arguments": {}}
                    ],
                    "observation": {"content": '{"status":"ok"}'},
                    "extra": {"author": "swe_e4b_verifier"},
                },
            ],
        }

    def test_extracts_only_verifier_steps_with_exact_arguments_and_results(self):
        candidate = extract_candidate("rich_3772", self.trace())
        self.assertEqual(candidate["instance_id"], "rich_3772")
        self.assertFalse(candidate["approved"])
        self.assertEqual(candidate["source"], "base_trace_curated_candidate")
        self.assertEqual(candidate["problem_description"], "Fix traceback recursion")
        self.assertEqual(len(candidate["steps"]), 3)
        self.assertEqual(candidate["steps"][0]["arguments"], {"command": "git diff"})
        self.assertEqual(candidate["steps"][0]["result"]["exit_code"], 0)
        self.assertEqual(candidate["steps"][1]["result"]["exit_code"], 2)
        self.assertEqual(candidate["steps"][2]["tool"], "submit_patch")

    def test_marks_behavioral_violations_without_auto_approving(self):
        candidate = extract_candidate("rich_3772", self.trace())
        self.assertIn("broad_pytest", candidate["audit_flags"])
        self.assertIn("submit_after_failed_test", candidate["audit_flags"])
        self.assertNotIn("reference_patch", repr(candidate))

    def test_normalizes_successful_targeted_test(self):
        trace = self.trace()
        trace["steps"][3]["tool_calls"][0]["arguments"]["command"] = (
            "pytest tests/test_syntax.py::test_case -q"
        )
        trace["steps"][3]["observation"] = {
            "content": '{"status":"ok","stdout":"1 passed","stderr":"","exit_code":0}'
        }
        candidate = extract_candidate("rich_3772", trace)
        self.assertNotIn("broad_pytest", candidate["audit_flags"])
        self.assertNotIn("submit_after_failed_test", candidate["audit_flags"])
        self.assertIn("missing_final_diff_check", candidate["audit_flags"])
        self.assertEqual(candidate["suggested_label"], "verified_submit")
        self.assertFalse(candidate["approved"])

    def test_counts_multiple_successful_repairs(self):
        trace = self.trace()
        edit = {
            "source": "agent",
            "message": "repair",
            "tool_calls": [
                {
                    "function_name": "edit_file",
                    "arguments": {
                        "filepath": "rich/a.py",
                        "old_string": "a",
                        "new_string": "b",
                    },
                }
            ],
            "observation": {"content": '{"status":"ok"}'},
            "extra": {"author": "swe_e4b_verifier"},
        }
        trace["steps"].insert(-1, edit)
        trace["steps"].insert(-1, edit.copy())
        candidate = extract_candidate("rich_3772", trace)
        self.assertIn("multiple_repairs", candidate["audit_flags"])

    def test_rejects_trace_without_task_prompt(self):
        trace = self.trace()
        trace["steps"] = [step for step in trace["steps"] if step.get("source") != "user"]
        with self.assertRaisesRegex(ValueError, "problem statement"):
            extract_candidate("rich_3772", trace)


if __name__ == "__main__":
    unittest.main()
