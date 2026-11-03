import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_root_trace_mechanics.py"


def step(tool, *, arguments=None, exit_code=None, author="swe_e4b_coder"):
    payload = {
        "step_id": "x",
        "source": "agent",
        "message": "",
        "extra": {"author": author, "event_type": "thinking"},
        "tool_calls": [{"function_name": tool, "arguments": arguments or {}}],
    }
    if exit_code is not None:
        payload["observation"] = {"content": json.dumps({"exit_code": exit_code})}
    return payload


def trace(*steps):
    return {"schema_version": 1, "agent": "test", "steps": list(steps), "final_metrics": {}}


class TraceMechanicsCliTests(unittest.TestCase):
    def run_analyzer(self, traces, results):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            trace_dir = tmp / "traces"
            trace_dir.mkdir()
            for instance_id, payload in traces.items():
                (trace_dir / f"trace_{instance_id}.json").write_text(json.dumps(payload), encoding="utf-8")
            results_path = tmp / "results.json"
            results_path.write_text(json.dumps({"results": results}), encoding="utf-8")
            output = tmp / "out.json"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), str(trace_dir), "--results", str(results_path), "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            return json.loads(output.read_text(encoding="utf-8"))

    def test_counts_pre_edit_targeted_evidence(self):
        data = self.run_analyzer(
            {"a": trace(
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=0),
                step("submit_patch", exit_code=0),
            )},
            [{"instance_id": "a", "resolved": True}],
        )
        task = data["tasks"][0]
        self.assertTrue(task["pre_edit_targeted_evidence"])
        self.assertEqual(task["final_targeted_exit"], 0)
        self.assertFalse(task["submit_after_failed_targeted"])

    def test_detects_failed_verification_without_repair(self):
        data = self.run_analyzer(
            {"a": trace(
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        task = data["tasks"][0]
        self.assertTrue(task["failed_targeted_after_edit"])
        self.assertFalse(task["repair_after_failed_targeted"])
        self.assertTrue(task["failed_targeted_no_repair"])

    def test_detects_repair_and_retest_after_failure(self):
        data = self.run_analyzer(
            {"a": trace(
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=0),
                step("submit_patch", exit_code=0),
            )},
            [{"instance_id": "a", "resolved": True}],
        )
        task = data["tasks"][0]
        self.assertTrue(task["repair_after_failed_targeted"])
        self.assertTrue(task["targeted_retest_after_repair"])
        self.assertEqual(task["final_targeted_exit"], 0)

    def test_flags_submit_after_failed_targeted(self):
        data = self.run_analyzer(
            {"a": trace(
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
                step("submit_patch", exit_code=0),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        self.assertTrue(data["tasks"][0]["submit_after_failed_targeted"])

    def test_broad_pytest_is_not_pre_edit_targeted_evidence(self):
        data = self.run_analyzer(
            {"a": trace(
                step("run_command", arguments={"command": "pytest"}, exit_code=1),
                step("edit_file", arguments={"filepath": "pkg/x.py"}, exit_code=0),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        task = data["tasks"][0]
        self.assertEqual(task["broad_test_count"], 1)
        self.assertEqual(task["targeted_test_count"], 0)
        self.assertFalse(task["pre_edit_targeted_evidence"])

    def test_non_test_command_uses_safe_other_command_category(self):
        data = self.run_analyzer(
            {"a": trace(
                step("run_command", arguments={"command": "git log -1 --oneline"}, exit_code=0),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        self.assertEqual(data["tasks"][0]["action_counts"].get("other_command"), 1)

        def assert_no_raw_command_key(value):
            if isinstance(value, dict):
                self.assertNotIn("command", value)
                for child in value.values():
                    assert_no_raw_command_key(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_raw_command_key(child)

        assert_no_raw_command_key(data)

    def test_generated_json_write_is_not_source_mutation(self):
        command = "python3 -c \"import json; open('openapi.json','w').write('{}')\""
        data = self.run_analyzer(
            {"a": trace(
                step("run_command", arguments={"command": command}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        self.assertEqual(data["tasks"][0]["mutation_count"], 0)

    def test_python_source_file_write_is_script_mutation(self):
        command = "python3 -c \"p='pkg/x.py'; open(p,'w').write('x=1')\""
        data = self.run_analyzer(
            {"a": trace(
                step("run_command", arguments={"command": command}, exit_code=0),
                step("run_command", arguments={"command": "pytest tests/test_x.py -q"}, exit_code=1),
            )},
            [{"instance_id": "a", "resolved": False}],
        )
        self.assertEqual(data["tasks"][0]["mutation_count"], 1)
        self.assertEqual(data["tasks"][0]["script_mutation_count"], 1)


if __name__ == "__main__":
    unittest.main()
