"""Exercise the observer in the official ADK Runner using scripted CPU responses."""

import asyncio
from pathlib import Path
import subprocess
import tempfile
import unittest

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import PrivateAttr

from scripts.candidate_history import History, adk_plugin, grade_history
from tests.test_candidate_history import BAD, GOOD, PARTIAL, CHECK
from tests.test_paired_check_adk import LocalSandbox


class ScriptedCPUModel(BaseLlm):
    _index: int = PrivateAttr(default=0)
    _observations: list = PrivateAttr(default_factory=list)

    async def generate_content_async(self, llm_request, stream=False):
        for content in llm_request.contents:
            for part in content.parts or []:
                if part.function_response:
                    self._observations.append(part.function_response.response)
        programs = (GOOD, PARTIAL)
        if self._index < len(programs):
            part = types.Part(function_call=types.FunctionCall(
                name="edit_file", args={"content": programs[self._index]},
            ))
        else:
            part = types.Part(text="Done")
        self._index += 1
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


class CandidateHistoryAdkTests(unittest.TestCase):
    def test_official_runner_observes_a_lost_candidate_without_changing_tool_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            def git(*args):
                return subprocess.check_output(["git", "-C", str(workspace), *args])
            git("init", "-q")
            git("config", "user.name", "CPU fixture")
            git("config", "user.email", "cpu@example.invalid")
            (workspace / "samplepkg.py").write_text(BAD)
            git("add", ".")
            git("commit", "-qm", "base")
            git("tag", "_swegemma_baseline")
            (workspace / "samplepkg.py").write_text(GOOD)
            gold = git("diff", "--binary", "_swegemma_baseline")
            (workspace / "samplepkg.py").write_text(BAD)
            history = History.for_sandbox(LocalSandbox(workspace), root / "history", str(workspace))
            history.start()
            model = ScriptedCPUModel(model="scripted-cpu-fixture")
            def edit_file(content: str) -> dict:
                """Replace the fixture source."""
                (workspace / "samplepkg.py").write_text(content)
                return {"status": "ok"}
            agent = LlmAgent(name="fixture", model=model, instruction="CPU fixture", tools=[edit_file])
            async def run():
                service = InMemorySessionService()
                session = await service.create_session(app_name="cpu", user_id="fixture")
                runner = Runner(app=App(name="cpu", root_agent=agent, plugins=[adk_plugin(history)]),
                                session_service=service)
                async for _ in runner.run_async(user_id="fixture", session_id=session.id,
                                               new_message=types.Content(role="user", parts=[types.Part(text="Run fixture")])):
                    pass
            try:
                asyncio.run(run())
            finally:
                history.finish()
            self.assertTrue(model._observations)
            self.assertTrue(all(observation == {"status": "ok"} for observation in model._observations))
            self.assertEqual((workspace / "samplepkg.py").read_text(), PARTIAL)
            report = grade_history(workspace, root / "history", CHECK, gold)
            self.assertEqual(report["diagnosis"], "discarded_passing_candidate")
            self.assertEqual(report["nonempty_candidates"], 2)


if __name__ == "__main__":
    unittest.main()
