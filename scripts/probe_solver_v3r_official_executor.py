"""Real official swegemma CodeExecutor + ADK tool-event integration without a model.

The exact V3-R ZIP is compiled with the *same AdkSandboxCodeExecutor injection*
used in swegemma's official agent_runner. A scripted BaseLlm performs the
native ADK sequence load_skill -> run_skill_script(before) -> edit_file ->
run_skill_script(after) -> submit_patch; the actual bundled script runs pytest
inside an isolated synthetic git repository and its real result controls the
next synthetic action. This proves official tool mechanics, NOT 31B quality.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import zipfile


class SyntheticSandbox:
    def __init__(self, workspace: Path):
        self.work_dir = str(workspace)
        self.workspace = workspace

    def write_file(self, relative_path: str, content: str) -> None:
        destination = (self.workspace / relative_path).resolve()
        if not destination.is_relative_to(self.workspace.resolve()):
            raise ValueError("unsafe synthetic executor path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def run_command(self, command: str, timeout: int | None = None):
        # Private, offline fixture source only. No user data/competition tasks.
        env = dict(os.environ)
        env["PWD"] = str(self.workspace)
        env["SWE_WORKSPACE"] = str(self.workspace)
        try:
            p = subprocess.run(
                ["/bin/bash", "-c", command], cwd=self.workspace,
                capture_output=True, text=True, timeout=timeout or 30,
                env=env, check=False,
            )
            return SimpleNamespace(
                stdout=p.stdout, stderr=p.stderr, exit_code=p.returncode,
                status="ok" if p.returncode == 0 else "error",
            )
        except subprocess.TimeoutExpired:
            return SimpleNamespace(
                stdout="", stderr="synthetic command timed out",
                exit_code=124, status="timeout",
            )


async def run(candidate: bytes) -> dict:
    from adk_submission import (
        compile_submission, validate_directory, ModelRegistry, ToolRegistry,
    )
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits
    from swegemma.harness.agent_runner import AdkSandboxCodeExecutor

    phase = [0]
    inspected = []
    snapshots = []
    with tempfile.TemporaryDirectory(prefix="gemma-v3r-injected-official-") as tmp:
        root = Path(tmp)
        workspace = root / "repo"
        workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(workspace)], check=True)
        (workspace / "fixme.py").write_text(
            "def answer():\n    return 2\n", encoding="utf-8")
        (workspace / "test_fixme.py").write_text(
            "from fixme import answer\n\ndef test_answer():\n    assert answer() == 3\n",
            encoding="utf-8",
        )
        package = root / "package"
        package.mkdir()
        with zipfile.ZipFile(io.BytesIO(candidate)) as z:
            if z.testzip() is not None:
                raise ValueError("invalid candidate ZIP")
            z.extractall(package)
        limits, _ = build_submission_limits()
        validate_directory(package, limits=limits)

        def tool_edit_file(filepath: str, old_string: str, new_string: str):
            if filepath != "fixme.py" or old_string != "return 2" or new_string != "return 3":
                raise AssertionError("unexpected scripted edit")
            target = workspace / filepath
            old = target.read_text(encoding="utf-8")
            if old.count(old_string) != 1:
                raise AssertionError("edit string not unique")
            target.write_text(old.replace(old_string, new_string),
                              encoding="utf-8")
            return {"status": "ok", "changed": True}

        def tool_submit_patch():
            diff = (workspace / "fixme.py").read_text(encoding="utf-8")
            return {"status": "submitted", "patch_nonempty": "return 3" in diff}

        class ScriptedRepairModel(BaseLlm):
            async def generate_content_async(self, llm_request, stream=False):
                responses = [
                    p.function_response for msg in (getattr(llm_request,"contents",None) or [])
                    for p in (getattr(msg,"parts",None) or [])
                    if getattr(p,"function_response",None) is not None
                ]
                last = responses[-1] if responses else None
                if last:
                    snapshots.append({"name":last.name,"response":last.response})
                s = phase[0]
                if s == 0:
                    call = types.FunctionCall(name="load_skill",
                                              args={"skill_name":"repair-witness"})
                elif s == 1:
                    if last is None or last.name != "load_skill":
                        raise AssertionError("expected real load_skill response")
                    call = types.FunctionCall(
                        name="run_skill_script",
                        args={"skill_name":"repair-witness",
                              "file_path":"scripts/witness.py",
                              "args":{"phase":"before",
                                      "target":"test_fixme.py::test_answer"}},
                    )
                elif s == 2:
                    if last is None or last.name != "run_skill_script":
                        raise AssertionError("no before script function response")
                    envelope=last.response or {}
                    if envelope.get("status")!="success":
                        raise AssertionError("official script executor failed: "+json.dumps(envelope,default=str)[-1200:])
                    parsed=json.loads(envelope.get("stdout",""))
                    if parsed.get("status")!="fail" or parsed.get("comparison")!="baseline_recorded":
                        raise AssertionError("real before-test did not fail: "+json.dumps(parsed)[-1200:])
                    inspected.append("before-failed-evidence-used")
                    call = types.FunctionCall(
                        name="edit_file",
                        args={"filepath":"fixme.py","old_string":"return 2",
                              "new_string":"return 3"},
                    )
                elif s == 3:
                    if last is None or last.name != "edit_file":
                        raise AssertionError("no native edit response")
                    call = types.FunctionCall(
                        name="run_skill_script",
                        args={"skill_name":"repair-witness",
                              "file_path":"scripts/witness.py",
                              "args":{"phase":"after",
                                      "target":"test_fixme.py::test_answer"}},
                    )
                elif s == 4:
                    if last is None or last.name != "run_skill_script":
                        raise AssertionError("no after script response")
                    envelope=last.response or {}
                    if envelope.get("status")!="success":
                        raise AssertionError("official after-script failed: "+json.dumps(envelope,default=str)[-1200:])
                    parsed=json.loads(envelope.get("stdout",""))
                    if parsed.get("status")!="pass" or parsed.get("comparison")!="repair_demonstrated":
                        raise AssertionError("real after-test did not verify repair: "+json.dumps(parsed)[-1200:])
                    inspected.append("repair-evidence-used")
                    call = types.FunctionCall(name="submit_patch",args={})
                elif s == 5:
                    if last is None or last.name != "submit_patch":
                        raise AssertionError("no native submit result")
                    phase[0] += 1
                    yield LlmResponse(content=types.Content(
                        role="model", parts=[types.Part(text="completed scripted repair")]))
                    return
                else:
                    raise AssertionError("unexpected extra turn")
                phase[0] += 1
                yield LlmResponse(content=types.Content(
                    role="model",parts=[types.Part(function_call=call)]))

        sandbox = SyntheticSandbox(workspace)
        code_executor = AdkSandboxCodeExecutor(sandbox=sandbox,timeout_seconds=45)
        models = ModelRegistry()
        models.register("gemma-4-31b-it-qat-w4a16-ct",
                        ScriptedRepairModel(model="gemma-4-31b-it-qat-w4a16-ct"))
        tools = ToolRegistry()
        tools.register("edit_file",tool_edit_file)
        tools.register("submit_patch",tool_submit_patch)
        for name in (
            "run_command","read_file","write_file","get_status",
            "get_code_neighbors","search_similar_code","get_code_subgraph",
        ):
            def unused(*args, **kwargs):
                raise AssertionError("no extra native tool in scripted probe")
            tools.register(name,unused)

        agent = compile_submission(
            submission_dir=package, model_registry=models,
            tool_registry=tools, code_executor=code_executor,
            script_timeout=45, limits=limits,
        )
        skillsets=[t for t in agent.tools if type(t).__name__=="SkillToolset"]
        if len(skillsets)!=1:
            raise AssertionError("missing official SkillToolset")
        print("V3R_OFFICIAL_SKILL_EXECUTOR_BOUND="+type(
            getattr(skillsets[0],"_code_executor",None)).__name__,flush=True)

        sessions=InMemorySessionService()
        session=await sessions.create_session(
            app_name="official_synthetic_v3r",user_id="tester")
        runner=Runner(agent=agent,app_name="official_synthetic_v3r",
                      session_service=sessions)
        events=[]
        async for event in runner.run_async(
            user_id="tester",session_id=session.id,
            new_message=types.Content(role="user",parts=[
                types.Part(text="Fix synthetic answer from 2 to 3")]),
        ):
            parts=(getattr(getattr(event,"content",None),"parts",None) or [])
            events.extend(
                ("call",p.function_call.name) if p.function_call else
                ("result",p.function_response.name)
                for p in parts if p.function_call or p.function_response
            )
        names=[kind+":"+name for kind,name in events]
        expected=[
            "call:load_skill","result:load_skill",
            "call:run_skill_script","result:run_skill_script",
            "call:edit_file","result:edit_file",
            "call:run_skill_script","result:run_skill_script",
            "call:submit_patch","result:submit_patch",
        ]
        if names != expected:
            raise AssertionError(f"official ADK event order mismatch: {names}")
        if inspected!=["before-failed-evidence-used","repair-evidence-used"]:
            raise AssertionError(f"script responses not used: {inspected}")
        if "return 3" not in (workspace / "fixme.py").read_text():
            raise AssertionError("native edit did not materialize")
        print("V3R_OFFICIAL_ADK_EVENT_SEQUENCE="+json.dumps(names),flush=True)
        print("V3R_OFFICIAL_ADK_SCRIPTED_EVIDENCE_CONSUMED="+json.dumps(inspected),flush=True)
        print("V3R_REAL_PYTEST_FAIL_TO_PASS=TRUE",flush=True)
        print("V3R_REAL_31B_MODEL_TESTED=FALSE",flush=True)
        return {"events":names,"evidence_consumed":inspected,
                "score_claim":"NONE"}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,required=True)
    a=parser.parse_args()
    asyncio.run(run(a.zip.read_bytes()))


if __name__=="__main__":
    main()
