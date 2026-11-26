"""Frozen synthetic tests for the exact Champion-only prompt intervention."""
import unittest
from unittest.mock import patch

from scripts.build_multisurface_scope_20261126 import (
    SCOPE_GUIDANCE, files_for_pair, eligible_source_paths,
)

def fake_files():
    return {
      "agent.yaml": "root:\n  model: gemma-4-31b-it-qat-w4a16-ct\n  tools:\n  - run_command\n  - read_file\n  - edit_file\n  - submit_patch\n",
      "eval_config.yaml": "evaluation:\n  max_time_minutes: 5\n  max_tool_calls: 60\n  max_turns: 80\n  timeout_seconds: 300\n",
      "configs/sampling.yaml": "temperature: 0.2\ntop_p: 0.95\n",
      "prompts/system.md": "Solve code tasks. Use precise checks and submit_patch.\n",
    }

class ScopeBuilderTests(unittest.TestCase):
    def test_only_prompt_changes_on_verified_champion(self):
        original=fake_files()
        with patch("scripts.build_multisurface_scope_20261126._source_files", return_value=original):
            control,treatment=files_for_pair(b"irrelevant-for-mocked-dependency")
        self.assertEqual(set(control),set(treatment))
        self.assertEqual({p for p in original if control[p]!=treatment[p]},
                         {"prompts/system.md"})
        self.assertEqual(control,original)
        self.assertTrue(treatment["prompts/system.md"].startswith(original["prompts/system.md"].rstrip()))
        self.assertIn(SCOPE_GUIDANCE.strip(), treatment["prompts/system.md"])
        self.assertEqual(treatment["eval_config.yaml"], original["eval_config.yaml"])

    def test_missing_champion_tools_rejected(self):
        raw=fake_files()
        raw["agent.yaml"]="root:\n"
        with patch("scripts.build_multisurface_scope_20261126._source_files", return_value=raw):
            with self.assertRaises(ValueError):
                files_for_pair(b"x")

    def test_prompt_variant_avoids_unconditional_extra_verification(self):
        self.assertIn("Only when", SCOPE_GUIDANCE)
        self.assertIn("explicitly", SCOPE_GUIDANCE)
        self.assertIn("Do not", SCOPE_GUIDANCE)
        self.assertIn("one additional", SCOPE_GUIDANCE)
        self.assertIn("submit_patch", SCOPE_GUIDANCE)
        self.assertNotIn("hidden test", SCOPE_GUIDANCE.lower())

    def test_public_dev_selector_rejects_noncanonical_ids(self):
        with self.assertRaises(ValueError):
            eligible_source_paths(["fastapi_1", "rich_2", "../etc/shadow"])
        with self.assertRaises(ValueError):
            eligible_source_paths(["fastapi_1"] * 17)

    def test_public_dev_selector_canonical_count(self):
        ids=["fastapi_"+str(1000+i) for i in range(9)]+["rich_"+str(2000+i) for i in range(8)]
        self.assertEqual(eligible_source_paths(ids),sorted(ids))

if __name__=="__main__":
    unittest.main()
