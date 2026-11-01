import inspect
import json
import unittest

from kaggle.verifier_gold_teacher_runtime import (
    MODEL_NAME,
    build_result_record,
    build_verifier_only_submission,
    load_clean_training_ids,
    install_gold_patch_after_baseline_hook,
)


class GoldTeacherManifestTests(unittest.TestCase):
    def test_loads_only_frozen_clean_training_ids(self):
        manifest = {
            "version": "verifier-lora-v0-training-gold-screen",
            "status": "frozen",
            "source_training_manifest": "verifier-lora-v0-train-harvest",
            "clean_instance_ids": ["rich_1", "fastapi_2"],
        }
        self.assertEqual(
            load_clean_training_ids(json.dumps(manifest), {"rich_1", "fastapi_2", "rich_3"}),
            ["rich_1", "fastapi_2"],
        )

    def test_rejects_pending_or_non_training_ids(self):
        pending = {
            "version": "verifier-lora-v0-training-gold-screen",
            "status": "pending",
            "source_training_manifest": "verifier-lora-v0-train-harvest",
            "clean_instance_ids": ["rich_1"],
        }
        with self.assertRaises(ValueError):
            load_clean_training_ids(json.dumps(pending), {"rich_1"})

        contaminated = dict(pending, status="frozen", clean_instance_ids=["blind_1"])
        with self.assertRaises(ValueError):
            load_clean_training_ids(json.dumps(contaminated), {"rich_1"})


class VerifierOnlySubmissionTests(unittest.TestCase):
    def test_rewrites_root_to_current_verifier_without_coder_or_agent_tool(self):
        files = {
            "agent.yaml": "name: coder\n",
            "prompts/verifier.md": "verify {problem_description}\n",
            "configs/sampling.yaml": "temperature: 0.2\n",
            "sub_agents/verifier.yaml": "name: old verifier\n",
        }
        built = build_verifier_only_submission(files)
        root = built["agent.yaml"]
        self.assertIn("agent_class: LlmAgent", root)
        self.assertIn("name: swe_e4b_verifier", root)
        self.assertIn(f"model: {MODEL_NAME}", root)
        self.assertIn("instruction: !include prompts/verifier.md", root)
        self.assertIn("generate_content_config: !include configs/sampling.yaml", root)
        self.assertIn("- submit_patch", root)
        self.assertNotIn("agent_tool", root)
        self.assertNotIn("coder", root.lower())
        self.assertEqual(built["prompts/verifier.md"], files["prompts/verifier.md"])

    def test_requires_verifier_prompt_and_sampling_config(self):
        with self.assertRaises(ValueError):
            build_verifier_only_submission({"agent.yaml": "name: coder\n"})


class GoldPatchHookTests(unittest.TestCase):
    def test_hook_is_explicitly_after_baseline_and_uses_official_patch_helper(self):
        source = inspect.getsource(install_gold_patch_after_baseline_hook)
        self.assertIn("original_setup_baseline_commit", source)
        self.assertIn("apply_patch_in_container", source)
        self.assertIn("docker.copy_to", source)
        self.assertIn("git diff --check", source)
        self.assertIn("git diff --quiet HEAD", source)
        self.assertLess(
            source.index("original_setup_baseline_commit("),
            source.index("apply_patch_in_container("),
        )


class GoldTeacherResultTests(unittest.TestCase):
    def test_summary_hashes_reference_patch_without_serializing_it(self):
        record = build_result_record(
            instance_id="rich_1",
            repo="Textualize/rich",
            reference_patch="diff --git a/a.py b/a.py\n",
            resolved=True,
            test_exit_code=0,
            agent_patch="diff --git a/a.py b/a.py\n",
            tool_calls=4,
            duration_seconds=12.5,
            error=None,
        )
        self.assertTrue(record["resolved"])
        self.assertEqual(record["reference_patch_chars"], 27)
        self.assertIn("reference_patch_sha256", record)
        self.assertNotIn("reference_patch", record)
        self.assertIn("agent_patch_sha256", record)
        self.assertNotIn("agent_patch", record)


if __name__ == "__main__":
    unittest.main()
