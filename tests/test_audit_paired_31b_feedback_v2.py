"""Synthetic-only verification: no private task material in unit tests."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_paired_31b_feedback_v2 import (
    command_class, observation_exit, reduce_feedback, audit,
)


class FeedbackTests(unittest.TestCase):
    def test_runner_and_wrappers(self):
        self.assertEqual(command_class("bash -lc 'cd project && python -m pytest tests/test_a.py'"), "explicit_test")
        self.assertEqual(command_class("uv run pytest -q"), "explicit_test")
        self.assertEqual(command_class("python -m unittest"), "explicit_test")
        self.assertEqual(command_class("make test"), "explicit_test")
        self.assertEqual(command_class("python -c 'assert 1 == 1'"), "inline_assert")
        self.assertEqual(command_class("python -m compileall ."), "compile_lint")

    def test_not_a_runner(self):
        for cmd in ("echo pytest", "rg pytest", "cat tests/test_a.py",
                    "python -c 'print(\"pytest\")'", "git diff --check"):
            self.assertNotIn(command_class(cmd), ("explicit_test", "inline_assert"))

    def test_structured_exit_and_parallel_ambiguity(self):
        self.assertEqual(observation_exit({"content": '{"details":{"exit_code":1}}'}), "nonzero")
        self.assertEqual(observation_exit({"content": {"exit_code":0}}), "zero")
        self.assertEqual(observation_exit({"content": '{"exit_code":1}'}, True), "unknown")
        self.assertEqual(observation_exit({"content": "command failed; output here"}), "unknown")

    def test_feedback_repair_chronology(self):
        def call(name, command=None):
            args = {"command": command} if command is not None else {}
            return {"tool_calls":[{"function_name":name, "arguments": args}],
                    "observation":{"content": '{"exit_code":1}' if name == "run_command"
                                   else '{"exit_code":0}'}}
        trace={"steps":[
            call("read_file"),call("edit_file"),
            call("run_command","python -m pytest tests/test_a.py"),
            call("edit_file"),call("submit_patch"),
        ]}
        result=reduce_feedback(trace)
        self.assertEqual(result["explicit_or_inline_tests"],1)
        self.assertEqual(result["tests_after_first_edit"],1)
        self.assertEqual(result["nonzero_test_then_edit"],1)
        self.assertEqual(result["tests_with_structured_exit"],{"nonzero":1})
        self.assertEqual(result["total_edit_actions"],2)

    def test_full_paired_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rows=[]
            for task in ("fastapi_14487","rich_3782","requests_7427"):
                for arm in ("v2_5min","public_prompt_5min"):
                    rows.append({"arm":arm,"instance_id":task,
                                 "resolved":False,"has_patch":True,
                                 "test_exit_code":1})
                    directory=root/"paired-prompt-private-results"
                    if arm=="public_prompt_5min": directory=directory/"public-prompt"
                    directory.mkdir(parents=True,exist_ok=True)
                    (directory/f"trace_{task}.json").write_text(json.dumps({"steps":[]}))
            (root/"paired_prompt_v2_31b_results.json").write_text(json.dumps({
                "version":"public-prompt-v2-paired-clean-v1", "results":rows
            }))
            result=audit(root)
            self.assertEqual(result["by_arm"]["v2_5min"]["tasks"],3)
            self.assertEqual(result["by_arm"]["public_prompt_5min"]["traces_found"],3)
            self.assertFalse(result["raw_competition_content_exported"])


if __name__ == "__main__":
    unittest.main()
