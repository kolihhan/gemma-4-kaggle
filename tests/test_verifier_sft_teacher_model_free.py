import json
from pathlib import Path
import unittest

from kaggle.verifier_gold_teacher_supervision import build_teacher_safe_stop_record


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_sft_teacher_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-sft-teacher.yml"
PLAN = ROOT / "docs" / "evaluation" / "verifier-lora-targeted-tests-v0.json"

INLINE_ASSERT = (
    "python -c \"import requests, requests.adapters; "
    "a=requests.adapters.HTTPAdapter(); "
    "p=requests.Request(method='GET', url='http://127.0.0.1:10000//v:h').prepare(); "
    "assert a.request_url(p, {}) == '/v:h'\""
)


class VerifierSftTeacherModelFreeContractTests(unittest.TestCase):
    def test_safe_stop_rejects_infrastructure_failure(self):
        record = build_teacher_safe_stop_record(
            instance_id="requests_2",
            problem_description="Trim excess leading path separators.",
            targeted_command=INLINE_ASSERT,
            pre_diff={"exit_code": 0, "output": ""},
            targeted_test={
                "exit_code": 1,
                "output": "Traceback (most recent call last):\nModuleNotFoundError: No module named 'requests'\n",
            },
            final_diff={"exit_code": 0, "output": ""},
        )
        self.assertFalse(record["approved"])
        self.assertIsNone(record["label"])
        self.assertIn("non_behavioral_targeted_failure", record["audit_flags"])

    def test_fastapi_gate_checks_new_error_message_behavior(self):
        payload = json.loads(PLAN.read_text(encoding="utf-8"))
        commands = {item["instance_id"]: item["command"] for item in payload["targets"]}
        command = commands["fastapi_14479"]
        self.assertIn("python -c", command)
        self.assertIn("assert", command)
        self.assertIn("Query parameter", command)
        self.assertNotIn("pytest tests/test_invalid_sequence_param.py", command)

    def test_teacher_runtime_bootstraps_workspace_without_model_inference(self):
        source = RUNTIME.read_text(encoding="utf-8")
        for required in (
            "resolve_task_snapshot_paths",
            "sandbox_start",
            "sandbox_stop",
            "setup_container_wheels",
            "extract_snapshot",
            "setup_git_exclude",
            "install_editable_package",
            "install_test_dependencies",
            "setup_workspace_test_config",
            "setup_baseline_commit",
            "apply_patch_in_container",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "VllmServer",
            "VllmConfig",
            "discover_adapters",
            "discover_declared_models",
            "torch.cuda",
            "server.start",
        ):
            self.assertNotIn(forbidden, source)

    def test_teacher_workflow_is_cpu_only_and_has_no_model_mount(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('"enable_gpu": False', source)
        self.assertIn('"model_sources": []', source)
        self.assertNotIn('"machine_shape": "NvidiaL4"', source)
        self.assertNotIn("--accelerator NvidiaL4", source)


if __name__ == "__main__":
    unittest.main()
