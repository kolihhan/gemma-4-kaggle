"""CPU-only test cases for the Contract & Impact candidate and its tool."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_contract_impact_candidate as b

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "contract_tool", ROOT / "experiments/architecture-contract-impact-v0/skill/scripts/contract.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def req(paths, source="issue", status="not_run"):
    return {
        "id": "R1", "statement": "Keep both paths consistent",
        "source": source, "evidence": "issue: path operations and dependencies",
        "edit_targets": paths,
        "check": {"status": status, "evidence": "assert returned behavior" if status.startswith("reported") else ""},
    }


class ContractImpactTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        def git(*args):
            subprocess.run(["git", "-C", str(self.workspace), *args],
                           check=True, capture_output=True)
        git("init", "-q")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "Fixture")
        (self.workspace / "path.py").write_text("value = 0\n")
        (self.workspace / "deps.py").write_text("value = 0\n")
        git("add", ".")
        git("commit", "-qm", "baseline")

    def analyze(self, requirements, unknowns=()):
        return tool.analyze({"requirements": requirements, "unknowns": list(unknowns)}, self.workspace)

    def test_detects_missing_cross_file_impact_instead_of_green_local_patch(self):
        (self.workspace / "path.py").write_text("value = 1\n")
        result = self.analyze([req(["path.py", "deps.py"], status="reported_pass")])
        self.assertEqual(result["decision"], "investigate_missing_impact")
        self.assertEqual(result["requirements"][0]["missing_targets"], ["deps.py"])
        self.assertFalse(result["independent_correctness_verified"])

    def test_complete_reported_coverage_is_not_independent_correctness(self):
        (self.workspace / "path.py").write_text("value = 1\n")
        (self.workspace / "deps.py").write_text("value = 1\n")
        before = subprocess.check_output(["git", "-C", str(self.workspace), "status", "--porcelain"])
        result = self.analyze([req(["path.py", "deps.py"], status="reported_pass")])
        after = subprocess.check_output(["git", "-C", str(self.workspace), "status", "--porcelain"])
        self.assertEqual(before, after)
        self.assertEqual(result["decision"], "review_final_not_certified")
        self.assertFalse(result["independent_correctness_verified"])

    def test_missing_task_semantics_must_not_be_invented(self):
        result = self.analyze([], ["Issue title refers to inaccessible external URL"])
        self.assertEqual(result["decision"], "insufficient_specification")
        self.assertEqual(result["unknowns"], ["Issue title refers to inaccessible external URL"])

    def test_model_hypothesis_is_not_a_verified_requirement(self):
        (self.workspace / "path.py").write_text("value = 1\n")
        result = self.analyze([req(["path.py"], source="hypothesis", status="reported_pass")])
        self.assertEqual(result["decision"], "investigate_contract")
        self.assertIn("unverified_requirement", result["requirements"][0]["issues"])

    def test_missing_verification_is_reported(self):
        (self.workspace / "path.py").write_text("value = 1\n")
        result = self.analyze([req(["path.py"], status="blocked")])
        self.assertEqual(result["decision"], "verify_or_repair")

    def test_untracked_patch_is_visible_and_deleted_source_is_separate(self):
        (self.workspace / "path.py").unlink()
        (self.workspace / "new.py").write_text("value = 2\n")
        result = self.analyze([req(["new.py"], status="reported_pass")])
        self.assertIn("new.py", result["changed_files"])
        self.assertIn("path.py", result["deleted_files"])

    def test_rejects_unsafe_and_unverified_inputs(self):
        with self.assertRaisesRegex(ValueError, "unsafe repository path"):
            self.analyze([req(["../secrets"])])
        with self.assertRaisesRegex(ValueError, "reported check needs evidence"):
            bad = req(["path.py"], status="reported_pass")
            bad["check"]["evidence"] = ""
            self.analyze([bad])
        with self.assertRaisesRegex(ValueError, "invalid requirement schema"):
            bad = req(["path.py"])
            bad["surprise"] = True
            self.analyze([bad])


V2 = {
    "agent.yaml": """agent_class: LlmAgent
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - submit_patch
  - get_status
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
""",
    "prompts/system.md": "Original prompt forcing first edit by call 12.\n",
    "configs/sampling.yaml": "temperature: 0.2\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class ContractCandidateBuilderTests(unittest.TestCase):
    def test_full_root_prompt_replacement_and_budgets(self):
        with patch.object(b, "validate_source_zip", return_value=dict(V2)):
            files = b.payload(b"source")
            self.assertEqual(files["configs/sampling.yaml"], V2["configs/sampling.yaml"])
            self.assertEqual(files["eval_config.yaml"], V2["eval_config.yaml"])
            self.assertNotIn("forcing first edit", files["prompts/system.md"])
            self.assertIn("contract-impact", files["agent.yaml"])
            self.assertEqual(files["agent.yaml"].count("  - submit_patch"), 1)
            self.assertIn("skills/contract-impact/scripts/contract.py", files)
            import io
            import zipfile
            with zipfile.ZipFile(io.BytesIO(b.archive(files))) as z:
                self.assertEqual(set(z.namelist()), set(files))
                self.assertIsNone(z.testzip())

    def test_fail_closed_if_native_tools_drift(self):
        broken = dict(V2)
        broken["agent.yaml"] = broken["agent.yaml"].replace("  - edit_file\n", "")
        with patch.object(b, "validate_source_zip", return_value=broken):
            with self.assertRaisesRegex(ValueError, "required native tool"):
                b.payload(b"source")


if __name__ == "__main__":
    unittest.main()
