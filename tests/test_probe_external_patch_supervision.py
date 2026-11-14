"""Synthetic schema-only patch-supervision gates."""
import unittest
from scripts.probe_external_patch_supervision import check_row, summarize


def example(content="Fix thing", patch="diff --git a/pkg/a.py b/pkg/a.py\n@@ -1 +1 @@\n-old\n+new"):
    return {"resolved": 1, "repo": "example/safe-code", "language": "python",
            "license": "MIT", "trajectory_id": "dummy",
            "metadata": {"model_patch": {"patch": patch}, "category": "bug-fix"},
            "messages": [
                {"role": "user", "content": content},
                {"role": "assistant", "tool_calls": [{"type": "function"}]},
                {"role": "tool", "content": "DO_NOT_PRINT"}]}


class PatchSchemaTests(unittest.TestCase):
    def test_issue_and_model_patch_presence_without_leaking_values(self):
        one = check_row(example())
        self.assertTrue(one["prompt_and_model_patch_present"])
        self.assertFalse(one["final_model_patch_training_approval"])
        self.assertFalse(one["patch_replayed_against_source_snapshot"])
        self.assertNotIn("Fix thing", str(one))
        self.assertNotIn("DO_NOT_PRINT", str(one))
        a=summarize([{"row":example()}])
        self.assertEqual(a["prompt_and_patch_present"], 1)
        self.assertEqual(a["ADK_policy_training_approved"], 0)

    def test_reject_broken_diff_headers_and_missing_prompt(self):
        bad = check_row(example(patch="diff --git a/pkg/a.py b/pkg/b.py\n+wrong"))
        self.assertFalse(bad["prompt_and_model_patch_present"])
        noissue = check_row(example(content=[]))
        self.assertFalse(noissue["prompt_and_model_patch_present"])


if __name__ == "__main__":
    unittest.main()
