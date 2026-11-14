"""Zero-execution, synthetic contractual tests for SWE-agent action bridge."""
import unittest

from scripts.bridge_sweagent_adk import action_meta, trace_gate, summarize, path_category, source_editor_shape


def call(name, args):
    import json
    return {"type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def success_row(messages):
    return {
        "resolved": 1, "repo": "example/safe-project", "language": "python",
        "license": "MIT", "trajectory_id": "synthetic",
        "metadata": {"model_patch": {"patch": "diff --git a/pkg/a.py b/pkg/a.py\n+fixed"}},
        "messages": messages,
    }


class StrictBridgeTests(unittest.TestCase):
    def test_bash_and_submit_syntax_not_proof_of_semantic_transfer(self):
        src, mapped, gate = action_meta(call("bash", {"command": "pytest -q tests/test_a.py"}))
        self.assertEqual(src, "bash")
        self.assertEqual(mapped, {"name": "run_command",
                                  "args": {"command": "pytest -q tests/test_a.py"}})
        self.assertEqual(gate, "mapped_action_semantics_unverified")
        src, mapped, gate = action_meta(call("submit", {}))
        self.assertEqual(mapped, {"name": "submit_patch", "args": {}})
        self.assertEqual(gate, "mapped_submit_lifecycle_unverified")
        self.assertEqual(action_meta(call("submit", {"message": "done"}))[2],
                         "submit_extra_arguments")

    def test_only_minimal_str_replace_maps_and_path_is_sandbox_safe(self):
        args = {"command": "str_replace", "path": "/workspace/src/main.py",
                "old_str": "return 0", "new_str": "return 1"}
        src, mapped, reason = action_meta(call("str_replace_editor", args))
        self.assertEqual(src, "str_replace_editor")
        self.assertEqual(mapped["name"], "edit_file")
        self.assertEqual(mapped["args"], {"filepath": "src/main.py",
                                         "old_string": "return 0",
                                         "new_string": "return 1",
                                         "allow_multiple": False})
        self.assertEqual(reason, "mapped_editor_matching_and_root_unverified")
        # SWE-agent's documented sandbox root is /testbed.
        translated = action_meta(call("str_replace_editor", {
            **args, "path": "/testbed/src/main.py"
        }))
        self.assertEqual(translated[1]["args"]["filepath"], "src/main.py")
        self.assertEqual(translated[2], "mapped_editor_matching_and_root_unverified")
        for bad in ("../../passwd", "/etc/passwd", "/tmp/src/main.py",
                    "src/../secret.py", "src//dup.py", "/testbed/../etc/passwd"):
            self.assertEqual(action_meta(call("str_replace_editor", {**args, "path": bad}))[2],
                             "editor_unsafe_or_missing_path")
        self.assertEqual(action_meta(call("str_replace_editor", {
            **args, "view_range": [1, 10]}))[2], "editor_nonminimal_signature")

    def test_non_equivalent_editor_modes_rejected(self):
        for command, extra, reason in (
            ("view", {"view_range": [1, 200]}, "view_output_truncation_mismatch"),
            ("create", {"file_text": "print(1)"}, "editor_write_semantics_unverified"),
            ("insert", {"insert_line": 1, "new_str": "test"}, "editor_write_semantics_unverified"),
            ("undo_edit", {}, "editor_unknown_command"),
        ):
            name, mapped, why = action_meta(call("str_replace_editor", {
                "command": command, "path": "pkg/a.py", **extra}))
            self.assertIsNone(mapped)
            self.assertEqual(why, reason)

    def test_incomplete_feedback_never_approved_as_training(self):
        messages = [
            {"role": "user", "content": "synthetic"},
            {"role": "assistant", "tool_calls": [call("bash", {"command": "echo DO_NOT_LOG"})]},
            {"role": "tool", "content": "DO_NOT_LOG"},
            {"role": "assistant", "tool_calls": [call("submit", {})]},
            {"role": "tool", "content": '{"status":"ok"}'},
        ]
        x = trace_gate(success_row(messages))
        self.assertTrue(x["all_action_syntax_convertible"])
        self.assertEqual(x["mapped_action_count"], 2)
        self.assertFalse(x["feedback_semantically_equivalent_verified"])
        self.assertFalse(x["full_training_trace_approved"])
        summary = summarize([{"row": success_row(messages)}])
        self.assertEqual(summary["mapped_action_syntax_count"], 2)
        self.assertEqual(summary["trainable_trajectories_approved"], 0)
        self.assertNotIn("DO_NOT_LOG", str(summary))

    def test_path_metadata_never_contains_external_source_paths(self):
        self.assertEqual(path_category("/external_private_root/some_file.py"), "other_absolute")
        self.assertEqual(path_category("/workspace/pkg/a.py"), "workspace_absolute")
        self.assertEqual(path_category("/testbed/pkg/a.py"), "sweagent_testbed_absolute")
        self.assertEqual(path_category("pkg/a.py"), "relative")
        self.assertEqual(path_category("../escape.py"), "unsafe_or_traversal")
        mode, category = source_editor_shape(call("str_replace_editor", {
            "command": "str_replace", "path": "/external_private_root/a.py",
            "old_str": "x", "new_str": "y"}))
        self.assertEqual((mode, category), ("str_replace", "other_absolute"))
        x = trace_gate(success_row([
            {"role": "user"},
            {"role": "assistant", "tool_calls": [call("str_replace_editor", {
                "command": "str_replace", "path": "/external_private_root/a.py",
                "old_str": "x", "new_str": "y"})]},
            {"role": "tool", "content": "ok"}
        ]))
        self.assertEqual(x["editor_path_categories"], {"other_absolute": 1})
        self.assertNotIn("/external_private_root", str(x))

    def test_bad_or_unrecognized_calls_cannot_be_silent_positives(self):
        self.assertIsNone(action_meta(call("webfetch", {"url": "https://example.test"}))[1])
        self.assertIsNone(action_meta(None)[1])
        self.assertEqual(action_meta({"function": {"name": "bash",
                                                   "arguments": "{bad"}})[2],
                         "arguments_not_json")


if __name__ == "__main__":
    unittest.main()
