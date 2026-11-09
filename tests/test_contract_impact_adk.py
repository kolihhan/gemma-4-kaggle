"""Official ADK CPU smoke test of isolated contract-impact candidate (no model)."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from adk_submission import ModelRegistry, ToolRegistry, compile_submission
from google.adk.models.base_llm import BaseLlm
from google.adk.tools.skill_toolset import LoadSkillTool, RunSkillScriptTool, SkillToolset
from tests.test_paired_check_adk import LocalSandbox
from adk_eval_core.sandbox.base import AdkSandboxCodeExecutor


MODEL = "gemma-4-31b-it-qat-w4a16-ct"


class NoInferenceModel(BaseLlm):
    async def generate_content_async(self, *args, **kwargs):
        raise AssertionError("No inference allowed in the CPU contract test")
        yield


class ContractImpactAdkTests(unittest.TestCase):
    def test_compiles_and_runs_structured_contract_skill(self):
        root = os.environ.get("CONTRACT_IMPACT_CANDIDATE_DIR")
        if not root:
            self.skipTest("Requires CPU-built pinned candidate directory")
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            def git(*args):
                subprocess.run(["git", "-C", str(workspace), *args], check=True,
                               capture_output=True)
            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "Fixture")
            (workspace / "api.py").write_text("value = 0\n")
            (workspace / "dependency.py").write_text("value = 0\n")
            git("add", ".")
            git("commit", "-qm", "base")
            (workspace / "api.py").write_text("value = 1\n")
            tools = ToolRegistry()
            for name in ("run_command", "read_file", "edit_file", "write_file",
                         "get_status", "submit_patch", "get_code_neighbors",
                         "search_similar_code", "get_code_subgraph"):
                def unused_native_tool():
                    raise AssertionError("No native calls in fixture")
                tools.register(name, unused_native_tool)
            models = ModelRegistry()
            models.register(MODEL, NoInferenceModel(model=MODEL))
            compiled = compile_submission(
                submission_dir=Path(root), tool_registry=tools, model_registry=models,
                code_executor=AdkSandboxCodeExecutor(
                    sandbox=LocalSandbox(workspace), timeout_seconds=30),
            )
            skillset = next(t for t in compiled.tools if isinstance(t, SkillToolset))
            context = SimpleNamespace(
                invocation_id="contract-test", agent_name=compiled.name, state={},
                _invocation_context=SimpleNamespace(),
            )
            loaded = asyncio.run(LoadSkillTool(skillset).run_async(
                args={"skill_name": "contract-impact"}, tool_context=context))
            self.assertIn("run_skill_script", loaded["instructions"])
            request = {
                "requirements": [{
                    "id": "R1", "statement": "Both surfaces", "source": "issue",
                    "evidence": "issue body",
                    "edit_targets": ["api.py", "dependency.py"],
                    "check": {"status": "reported_pass", "evidence": "assert endpoint output"},
                }],
                "unknowns": [],
            }
            result = asyncio.run(RunSkillScriptTool(skillset).run_async(
                args={"skill_name": "contract-impact", "file_path": "scripts/contract.py",
                      "args": {"workspace": str(workspace),
                               "request": json.dumps(request, sort_keys=True)}},
                tool_context=context))
            report = json.loads(result["stdout"])
            self.assertEqual(report["decision"], "investigate_missing_impact")
            self.assertEqual(report["requirements"][0]["missing_targets"], ["dependency.py"])
            self.assertFalse(report["independent_correctness_verified"])
            self.assertEqual((workspace / "api.py").read_text(), "value = 1\n")
            self.assertEqual((workspace / "dependency.py").read_text(), "value = 0\n")


if __name__ == "__main__":
    unittest.main()
