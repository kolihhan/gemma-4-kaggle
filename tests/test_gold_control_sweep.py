import hashlib
import json
import unittest
from pathlib import Path

from kaggle.gold_control_sweep import (
    EMBEDDED_MANIFEST_MARKER,
    HOLDOUT_MANIFEST_PATH,
    build_result_record,
    load_holdout_items,
    render_kernel_source,
    summarize_results,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "gold_control_sweep.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-gold-sweep.yml"
EXPECTED_HOLDOUT_IDS = {
    "rich_3067",
    "rich_3064",
    "rich_3942",
    "rich_4070",
    "fastapi_13920",
    "fastapi_14297",
    "fastapi_14077",
    "fastapi_14583",
    "fastapi_14371",
    "fastapi_15030",
    "requests_6629",
    "requests_7505",
}


class GoldControlSweepTests(unittest.TestCase):
    def test_loads_only_frozen_holdout_items(self):
        items = load_holdout_items(HOLDOUT_MANIFEST_PATH)
        ids = {item["instance_id"] for item in items}

        self.assertEqual(ids, EXPECTED_HOLDOUT_IDS)
        self.assertEqual(len(items), 12)
        self.assertEqual(len(ids), len(items))
        self.assertTrue(all(set(item) >= {"instance_id", "repo", "patch_bucket"} for item in items))

    def test_rendered_kernel_embeds_manifest_for_single_script_kaggle_runtime(self):
        source = RUNTIME.read_text(encoding="utf-8")
        manifest_text = HOLDOUT_MANIFEST_PATH.read_text(encoding="utf-8")

        rendered = render_kernel_source(source, manifest_text)

        self.assertNotIn(EMBEDDED_MANIFEST_MARKER, rendered)
        self.assertIn("rich_3067", rendered)
        self.assertIn("requests_7505", rendered)
        compile(rendered, "gold_control_sweep.py", "exec")

    def test_workflow_loads_renderer_by_path_not_kaggle_package_import(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("runpy.run_path", text)
        self.assertNotIn("from kaggle.gold_control_sweep import", text)

    def test_result_record_hashes_reference_patch_without_exposing_it(self):
        reference_patch = "diff --git a/a.py b/a.py\n+safe\n"
        record = build_result_record(
            instance_id="rich_3067",
            repo="Textualize/rich",
            reference_patch=reference_patch,
            resolved=True,
            test_exit_code=0,
            error=None,
            duration_seconds=1.25,
            test_output="12 passed",
        )

        self.assertEqual(record["reference_patch_chars"], len(reference_patch))
        self.assertEqual(
            record["reference_patch_sha256"],
            hashlib.sha256(reference_patch.encode("utf-8")).hexdigest(),
        )
        self.assertNotIn("reference_patch", record)
        self.assertNotIn(reference_patch, json.dumps(record, sort_keys=True))
        self.assertEqual(record["test_output_tail"], "12 passed")

    def test_sweep_uses_verifier_only_and_never_runs_submission_agent(self):
        text = RUNTIME.read_text(encoding="utf-8")

        self.assertIn("verify_task", text)
        self.assertIn("_hydrate_task_from_secret", text)
        self.assertIn("resolve_task_snapshot_paths", text)
        self.assertIn("ModelRegistry()", text)
        self.assertNotIn("evaluate_task(", text)
        self.assertNotIn("VllmServer", text)
        self.assertNotIn("VllmConfig", text)
        self.assertNotIn("compile_submission", text)

    def test_summary_separates_clean_from_confounded(self):
        summary = summarize_results(
            [
                {"instance_id": "a", "status": "completed", "resolved": True, "test_exit_code": 0},
                {"instance_id": "b", "status": "completed", "resolved": False, "test_exit_code": 1},
                {"instance_id": "c", "status": "error", "resolved": False, "test_exit_code": None},
            ],
            expected_count=3,
        )

        self.assertEqual(summary["requested"], 3)
        self.assertEqual(summary["completed"], 2)
        self.assertEqual(summary["clean"], 1)
        self.assertEqual(summary["confounded"], 2)
        self.assertEqual(summary["clean_instance_ids"], ["a"])
        self.assertEqual(summary["confounded_instance_ids"], ["b", "c"])


if __name__ == "__main__":
    unittest.main()
