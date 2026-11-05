"""Tests for a conservative uncertainty bound on overlooked test invocations."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_uncertain_test_evidence_v0 as candidate


def step(tool, cmd=None, *, exit_code=0):
    return {
        "extra": {"author": "swe_e4b_coder"},
        "tool_calls": [{
            "function_name": tool,
            "arguments": {"command": cmd} if cmd else {}
        }],
        "observation": {"content": json.dumps({"exit_code": exit_code})},
    }


class TestInvocationSensitivityTests(unittest.TestCase):
    def test_clear_invocations_and_nested_wrappers(self):
        positives = (
            "pytest tests/test_foo.py -q | tail -n 4",
            "python -m unittest discover -s tests",
            "cd pkg && python -m unittest tests.test_foo",
            "make test",
            "uv run pytest tests/test_foo.py && echo ok",
            "bash -lc 'cd pkg && python -m unittest tests.test_foo'",
            "env PYTHONPATH=src python3 -m unittest tests.test_foo",
            "coverage run -m pytest tests/test_foo.py",
        )
        for cmd in positives:
            with self.subTest(cmd=cmd):
                self.assertTrue(candidate.plausible_test_invocation(cmd))

    def test_mentions_do_not_count_as_invocations(self):
        negatives = (
            "grep pytest pyproject.toml",
            "echo pytest tests/test_foo.py",
            "cat tests/test_foo.py",
            "python -c 'print(\"pytest\")'",
            "git status --short",
            "sed -n '/pytest/p' README.md",
            "bash -lc 'grep pytest pyproject.toml'",
        )
        for cmd in negatives:
            with self.subTest(cmd=cmd):
                self.assertFalse(candidate.plausible_test_invocation(cmd))

    def test_recognized_test_not_double_counted_as_uncertain(self):
        recognized = candidate.reduce_one({
            "steps": [step("run_command", "cd pkg && pytest tests/test_foo.py -q")]
        }, "swe_e4b_coder")
        self.assertEqual(recognized["recognized_test_calls"], 1)
        self.assertEqual(recognized["unclassified_possible_test_calls"], 0)

    def test_sensitivity_does_not_output_raw_commands_or_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            traces = folder / "traces"
            traces.mkdir()
            results = []
            for i in range(17):
                ident = f"private_test_id_{i}"
                actions = [step("read_file")]
                if i == 0:
                    actions += [
                        step("edit_file"),
                        step("run_command", "pytest tests/secret_test.py | tail -n 4"),
                    ]
                elif i == 1:
                    actions += [step("run_command", "cd project && pytest tests/secret_test.py -q")]
                elif i == 2:
                    actions += [step("run_command", "echo pytest tests/secret_test.py")]
                (traces / f"trace_{ident}.json").write_text(json.dumps({"steps": actions}))
                results.append({"instance_id": ident, "resolved": i == 1})
            result_file = folder / "results.json"
            result_file.write_text(json.dumps({"results": results}))
            summary = candidate.audit(traces, result_file)
            counts = summary["totals"]
            self.assertEqual(counts["tasks"], 17)
            self.assertEqual(counts["resolved"], 1)
            self.assertEqual(counts["recognized_test_calls"], 1)
            self.assertEqual(counts["legacy_unsafe_recognized_calls"], 1)
            self.assertEqual(counts["unclassified_possible_test_calls"], 1)
            self.assertEqual(counts["tasks_without_any_recognized_or_candidate_test"], 15)
            self.assertEqual(counts["tasks_with_recognized_pre_edit_test"], 0)
            self.assertEqual(json.dumps(summary).find("private_test_id"), -1)
            self.assertNotIn("secret_test", json.dumps(summary))

    def test_failed_test_submit_without_repair_is_distinct_from_repaired_retest(self):
        fail = {"steps": [
            step("edit_file"),
            step("run_command", "pytest tests/test_x.py -q", exit_code=1),
            step("submit_patch"),
        ]}
        result = candidate.reduce_one(fail, "swe_e4b_coder")
        self.assertEqual(result["recognized_nonzero_exit_calls"], 1)
        self.assertTrue(result["last_recognized_test_nonzero_exit"])
        self.assertFalse(result["has_repair_after_nonzero_test_exit"])
        self.assertTrue(result["has_submit_after_nonzero_test_exit_without_repair"])

        repaired = {"steps": [
            step("edit_file"),
            step("run_command", "pytest tests/test_x.py -q", exit_code=1),
            step("edit_file"),
            step("run_command", "pytest tests/test_x.py -q", exit_code=0),
            step("submit_patch"),
        ]}
        second = candidate.reduce_one(repaired, "swe_e4b_coder")
        self.assertEqual(second["recognized_nonzero_exit_calls"], 1)
        self.assertEqual(second["recognized_zero_exit_calls"], 1)
        self.assertTrue(second["has_repair_after_nonzero_test_exit"])
        self.assertTrue(second["last_recognized_test_zero_exit"])
        self.assertFalse(second["has_submit_after_nonzero_test_exit_without_repair"])

    def test_known_exit_codes_are_not_inferred_from_missing_observations(self):
        observed = {"steps": [
            {"extra": {"author": "swe_e4b_coder"},
             "tool_calls": [{"function_name": "run_command", "arguments": {"command": "pytest tests/test_x.py -q"}}]}
        ]}
        result = candidate.reduce_one(observed, "swe_e4b_coder")
        self.assertEqual(result["recognized_unknown_exit_calls"], 1)
        self.assertEqual(result["recognized_zero_exit_calls"], 0)
        self.assertFalse(result["last_recognized_test_zero_exit"])

    def test_missing_trace_is_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "traces").mkdir()
            (tmp / "results.json").write_text(json.dumps({
                "results": [{"instance_id": "id", "resolved": False}]
            }))
            with self.assertRaisesRegex(ValueError, "differ"):
                candidate.audit(tmp / "traces", tmp / "results.json")


if __name__ == "__main__":
    unittest.main()
