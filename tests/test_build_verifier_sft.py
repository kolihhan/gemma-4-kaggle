import unittest

from scripts.build_verifier_sft import (
    SupervisionError,
    build_examples,
    classify_test_command,
)


VERIFIER_TEMPLATE = "Verifier policy for task:\n{problem_description}"
TRAIN_IDS = {"train_1", "train_2"}
BLIND_IDS = {"blind_1"}


def step(tool, arguments=None, *, exit_code=None, output=""):
    item = {
        "tool": tool,
        "arguments": arguments or {},
        "assistant_text": "",
    }
    if exit_code is not None or output:
        item["result"] = {"exit_code": exit_code, "output": output}
    return item


def record(instance_id="train_1", *, label="verified_submit", approved=True, steps=None):
    return {
        "instance_id": instance_id,
        "approved": approved,
        "label": label,
        "source": "base_trace_curated",
        "problem_description": "Fix the requested behavior without unrelated changes.",
        "steps": steps or [],
    }


class TestCommandClassification(unittest.TestCase):
    def test_targeted_pytest_file_or_node_is_targeted(self):
        self.assertEqual(classify_test_command("pytest tests/test_api.py -q"), "targeted")
        self.assertEqual(
            classify_test_command("python -m pytest tests/test_api.py::test_case -q"),
            "targeted",
        )

    def test_repo_wide_pytest_is_broad(self):
        self.assertEqual(classify_test_command("pytest"), "broad")
        self.assertEqual(classify_test_command("pytest -q"), "broad")
        self.assertEqual(classify_test_command("python -m pytest"), "broad")
        self.assertEqual(classify_test_command("pytest tests -q"), "broad")


class TestBuildExamples(unittest.TestCase):
    def good_submit_steps(self):
        return [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest tests/test_api.py::test_case -q"}, exit_code=0),
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("submit_patch", {}),
        ]

    def test_builds_chat_template_compatible_example(self):
        examples = build_examples(
            [record(steps=self.good_submit_steps())],
            allowed_training_ids=TRAIN_IDS,
            forbidden_ids=BLIND_IDS,
            verifier_template=VERIFIER_TEMPLATE,
        )
        self.assertEqual(len(examples), 1)
        example = examples[0]
        self.assertEqual(example["instance_id"], "train_1")
        self.assertEqual(example["label"], "verified_submit")
        self.assertEqual(example["messages"][0]["role"], "system")
        self.assertIn("Fix the requested behavior", example["messages"][0]["content"])
        tool_names = {
            tool["function"]["name"]
            for tool in example["tools"]
        }
        self.assertIn("run_command", tool_names)
        self.assertIn("submit_patch", tool_names)
        self.assertTrue(any("tool_calls" in message for message in example["messages"]))

    def test_rejects_unapproved_raw_trace(self):
        with self.assertRaisesRegex(SupervisionError, "approved"):
            build_examples(
                [record(approved=False, steps=self.good_submit_steps())],
                allowed_training_ids=TRAIN_IDS,
                forbidden_ids=BLIND_IDS,
                verifier_template=VERIFIER_TEMPLATE,
            )

    def test_rejects_blind_or_non_training_id(self):
        for instance_id in ("blind_1", "unknown_1"):
            with self.subTest(instance_id=instance_id):
                with self.assertRaises(SupervisionError):
                    build_examples(
                        [record(instance_id=instance_id, steps=self.good_submit_steps())],
                        allowed_training_ids=TRAIN_IDS,
                        forbidden_ids=BLIND_IDS,
                        verifier_template=VERIFIER_TEMPLATE,
                    )

    def test_rejects_reference_solution_fields_recursively(self):
        bad = record(steps=self.good_submit_steps())
        bad["metadata"] = {"reference_patch": "secret gold patch"}
        with self.assertRaisesRegex(SupervisionError, "reference_patch"):
            build_examples(
                [bad],
                allowed_training_ids=TRAIN_IDS,
                forbidden_ids=BLIND_IDS,
                verifier_template=VERIFIER_TEMPLATE,
            )

    def test_rejects_broad_pytest_as_positive_verification(self):
        bad_steps = [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest -q"}, exit_code=0),
            step("submit_patch", {}),
        ]
        with self.assertRaisesRegex(SupervisionError, "targeted"):
            build_examples(
                [record(steps=bad_steps)],
                allowed_training_ids=TRAIN_IDS,
                forbidden_ids=BLIND_IDS,
                verifier_template=VERIFIER_TEMPLATE,
            )

    def test_rejects_submit_after_known_targeted_failure(self):
        bad_steps = [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=1),
            step("submit_patch", {}),
        ]
        with self.assertRaisesRegex(SupervisionError, "failing targeted"):
            build_examples(
                [record(steps=bad_steps)],
                allowed_training_ids=TRAIN_IDS,
                forbidden_ids=BLIND_IDS,
                verifier_template=VERIFIER_TEMPLATE,
            )

    def test_allows_one_narrow_repair_then_passing_retest(self):
        repair_steps = [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=1),
            step(
                "edit_file",
                {"path": "pkg/api.py", "old_text": "old", "new_text": "new"},
            ),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=0),
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("submit_patch", {}),
        ]
        examples = build_examples(
            [record(steps=repair_steps)],
            allowed_training_ids=TRAIN_IDS,
            forbidden_ids=BLIND_IDS,
            verifier_template=VERIFIER_TEMPLATE,
        )
        self.assertEqual(len(examples), 1)

    def test_rejects_multiple_repairs(self):
        bad_steps = [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=1),
            step("edit_file", {"path": "a.py", "old_text": "a", "new_text": "b"}),
            step("edit_file", {"path": "a.py", "old_text": "b", "new_text": "c"}),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=0),
            step("submit_patch", {}),
        ]
        with self.assertRaisesRegex(SupervisionError, "more than one repair"):
            build_examples(
                [record(steps=bad_steps)],
                allowed_training_ids=TRAIN_IDS,
                forbidden_ids=BLIND_IDS,
                verifier_template=VERIFIER_TEMPLATE,
            )

    def test_safe_stop_requires_failed_targeted_test_and_no_submit(self):
        safe_stop = [
            step("run_command", {"command": "git diff --check && git diff"}, exit_code=0),
            step("run_command", {"command": "pytest tests/test_api.py -q"}, exit_code=1),
        ]
        examples = build_examples(
            [record(label="safe_stop", steps=safe_stop)],
            allowed_training_ids=TRAIN_IDS,
            forbidden_ids=BLIND_IDS,
            verifier_template=VERIFIER_TEMPLATE,
        )
        self.assertEqual(examples[0]["label"], "safe_stop")


if __name__ == "__main__":
    unittest.main()
