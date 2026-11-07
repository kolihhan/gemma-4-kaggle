"""CPU check of the official compiler and skill execution path, without inference."""

import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from adk_eval_core.sandbox.base import AdkSandboxCodeExecutor, ExecutionResult
from adk_submission import ModelRegistry, ToolRegistry, compile_submission
from google.adk.models.base_llm import BaseLlm
from google.adk.tools.skill_toolset import LoadSkillTool, RunSkillScriptTool, SkillToolset

from scripts.build_paired_check_candidate import payload


MODEL = "gemma-4-31b-it-qat-w4a16-ct"
SOURCE_ZIP = Path(__file__).resolve().parents[2] / "kaggle-reads/budgetfit-v2-exact.zip"


class NoInferenceModel(BaseLlm):
    async def generate_content_async(self, *args, **kwargs):
        raise AssertionError("The CPU check must never call a model")
        yield


class LocalSandbox:
    def __init__(self, workspace):
        self.work_dir = str(workspace)

    def write_file(self, path, content):
        (Path(self.work_dir) / path).write_text(content)

    def run_command(self, command, timeout=None):
        process = subprocess.run(
            command, shell=True, executable="/bin/bash", cwd=self.work_dir,
            capture_output=True, text=True, timeout=timeout,
        )
        return ExecutionResult(
            status="ok" if process.returncode == 0 else "error",
            stdout=process.stdout, stderr=process.stderr, exit_code=process.returncode,
        )


class OfficialSkillExecutionTests(unittest.TestCase):
    def test_both_arms_compile_and_execute_through_the_official_adapter(self):
        original = SOURCE_ZIP.read_bytes()
        paired, repeated = payload(original, "paired"), payload(original, "repeat")
        differences = [name for name in paired if paired[name] != repeated[name]]
        self.assertEqual(differences, ["skills/repository-check/scripts/compare.py"])
        self.assertEqual(
            paired[differences[0]].replace('COMPARISON_MODE = "paired"', 'COMPARISON_MODE = "repeat"'),
            repeated[differences[0]],
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            def git(*args):
                subprocess.run(["git", "-C", str(workspace), *args], check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.name", "CPU fixture")
            git("config", "user.email", "cpu@example.invalid")
            (workspace / "samplepkg.py").write_text("value = 'before'\n")
            git("add", ".")
            git("commit", "-qm", "fixture")
            git("tag", "_swegemma_baseline")
            (workspace / ".git/info/exclude").write_text(".adk_exec_*\n")
            (workspace / "samplepkg.py").write_text("value = 'after'\n")
            for arm, files in (("paired", paired), ("repeat", repeated)):
                directory = root / arm
                for name, body in files.items():
                    target = directory / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(body)
                tools = ToolRegistry()
                for name in ("run_command", "read_file", "edit_file", "write_file", "get_status",
                             "submit_patch", "get_code_neighbors", "search_similar_code", "get_code_subgraph"):
                    def unused_native_tool():
                        raise AssertionError("Native tool was not expected")
                    tools.register(name, unused_native_tool)
                models = ModelRegistry()
                models.register(MODEL, NoInferenceModel(model=MODEL))
                executor = AdkSandboxCodeExecutor(sandbox=LocalSandbox(workspace), timeout_seconds=30)
                agent = compile_submission(
                    submission_dir=directory, tool_registry=tools,
                    model_registry=models, code_executor=executor,
                )
                self.assertEqual(agent.model.model, MODEL)
                skillset = next(tool for tool in agent.tools if isinstance(tool, SkillToolset))
                context = SimpleNamespace(
                    invocation_id="cpu-check", agent_name=agent.name, state={},
                    _invocation_context=SimpleNamespace(),
                )
                loaded = asyncio.run(LoadSkillTool(skillset).run_async(
                    args={"skill_name": "repository-check"}, tool_context=context,
                ))
                self.assertIn("run_skill_script", loaded["instructions"])
                self.assertIn("repository-check", context.state[f"_adk_activated_skill_{agent.name}"])
                tool = RunSkillScriptTool(skillset)
                result = asyncio.run(tool.run_async(args={
                    "skill_name": "repository-check", "file_path": "scripts/compare.py",
                    "args": {"workspace": str(workspace), "code": "import samplepkg; print(samplepkg.value)"},
                }, tool_context=context))
                observation = json.loads(result["stdout"])
                self.assertEqual(observation["status"], "compared", result)
                expected = ["before", "after"] if arm == "paired" else ["after", "after"]
                self.assertEqual([r["stdout"].strip() for r in observation["runs"]], expected)
                self.assertEqual((workspace / "samplepkg.py").read_text(), "value = 'after'\n")


if __name__ == "__main__":
    unittest.main()
