"""CPU-only official ADK end-to-end generated counterexample → source repair.

The scripted model consumes a real failing custom test generated from a
synthetic problem, then edits source and checks the EXACT SAME locked test.
This verifies native tool semantics, not autonomous 31B model quality.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from scripts.probe_solver_v3r_official_executor import SyntheticSandbox


EXAMPLE_TEST = (
    "from example import answer\n\n"
    "def test_issue_contract():\n"
    "    assert answer() == 3\n"
)


async def probe(archive: bytes) -> dict:
    from adk_submission import compile_submission, validate_directory, ModelRegistry, ToolRegistry
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits
    from swegemma.harness.agent_runner import AdkSandboxCodeExecutor

    state={"turn":0,"case_id":None,"steps":[],"before":None,"after":None}
    with tempfile.TemporaryDirectory(prefix="v4-cgr-official-") as temporary:
        root=Path(temporary)
        pkg=root/"package"
        pkg.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            if z.testzip() is not None:
                raise ValueError("invalid V4 ZIP")
            z.extractall(pkg)
        limits,_=build_submission_limits()
        validate_directory(pkg,limits=limits)
        workspace=root/"repo"
        workspace.mkdir()
        subprocess.run(["git","init","-q",str(workspace)],check=True)
        (workspace/"example.py").write_text(
            "def answer():\n    return 2\n",encoding="utf-8")

        def edit_file(filepath: str,old_string: str,new_string: str):
            assert filepath=="example.py"
            assert old_string=="return 2" and new_string=="return 3"
            file=workspace/filepath
            old=file.read_text()
            assert old.count(old_string)==1
            file.write_text(old.replace(old_string,new_string))
            return {"modified":True}

        def submit_patch():
            assert "return 3" in (workspace/"example.py").read_text()
            return {"submitted":True}

        def unused(*args,**kwargs):
            raise AssertionError("unexpected extra native tool")
        registry=ToolRegistry()
        registry.register("edit_file",edit_file)
        registry.register("submit_patch",submit_patch)
        for name in ("run_command","read_file","write_file","get_status",
                     "get_code_neighbors","search_similar_code","get_code_subgraph"):
            func=lambda *a,**kw: unused(*a,**kw)
            func.__name__=name
            registry.register(name,func)

        class ScriptedDecision(BaseLlm):
            async def generate_content_async(self,llm_request,stream=False):
                messages=getattr(llm_request,"contents",None) or []
                results=[part.function_response
                         for msg in messages
                         for part in (getattr(msg,"parts",None) or [])
                         if getattr(part,"function_response",None)]
                recent=results[-1] if results else None
                turn=state["turn"]
                if turn==0:
                    call=types.FunctionCall(name="load_skill",
                        args={"skill_name":"repair-witness"})
                elif turn==1:
                    assert recent and recent.name=="load_skill"
                    call=types.FunctionCall(name="run_skill_script",
                        args={"skill_name":"repair-witness",
                              "file_path":"scripts/counterexample.py",
                              "args":{"phase":"before","source":EXAMPLE_TEST}})
                elif turn==2:
                    assert recent and recent.name=="run_skill_script",recent
                    envelope=recent.response or {}
                    assert envelope.get("status")=="success",envelope
                    witness=json.loads(envelope["stdout"])
                    assert witness.get("status")=="fail",witness
                    assert witness.get("baseline_discriminating") is True,witness
                    assert witness.get("test_relevance_verified") is False,witness
                    state["before"]=witness
                    state["case_id"]=witness["case_id"]
                    state["steps"].append("observed-before-fail")
                    call=types.FunctionCall(name="edit_file",
                        args={"filepath":"example.py","old_string":"return 2",
                              "new_string":"return 3"})
                elif turn==3:
                    assert recent and recent.name=="edit_file",recent
                    call=types.FunctionCall(name="run_skill_script",
                        args={"skill_name":"repair-witness",
                              "file_path":"scripts/counterexample.py",
                              "args":{"phase":"after","case-id":state["case_id"]}})
                elif turn==4:
                    assert recent and recent.name=="run_skill_script",recent
                    envelope=recent.response or {}
                    assert envelope.get("status")=="success",envelope
                    witness=json.loads(envelope["stdout"])
                    assert witness.get("status")=="pass",witness
                    assert witness.get("comparison")=="counterexample_repaired",witness
                    assert witness["case_id"]==state["case_id"],witness
                    assert witness["test_relevance_verified"] is False,witness
                    state["after"]=witness
                    state["steps"].append("observed-after-pass")
                    call=types.FunctionCall(name="submit_patch",args={})
                elif turn==5:
                    assert recent and recent.name=="submit_patch",recent
                    state["turn"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                         parts=[types.Part(text="synthetic repair complete")]))
                    return
                else:
                    raise AssertionError(f"extra turn {turn}")
                state["turn"]+=1
                yield LlmResponse(content=types.Content(role="model",
                     parts=[types.Part(function_call=call)]))

        models=ModelRegistry()
        models.register("gemma-4-31b-it-qat-w4a16-ct",
                        ScriptedDecision(model="gemma-4-31b-it-qat-w4a16-ct"))
        executor=AdkSandboxCodeExecutor(
            sandbox=SyntheticSandbox(workspace),timeout_seconds=40)
        agent=compile_submission(
            submission_dir=pkg,model_registry=models,tool_registry=registry,
            code_executor=executor,script_timeout=40,limits=limits)
        skillsets=[tool for tool in agent.tools
                   if type(tool).__name__=="SkillToolset"]
        assert len(skillsets)==1,"one legal SkillToolset expected"

        service=InMemorySessionService()
        session=await service.create_session(app_name="v4cgr",user_id="cpu")
        runner=Runner(agent=agent,app_name="v4cgr",session_service=service)
        events=[]
        async for event in runner.run_async(
            user_id="cpu",session_id=session.id,
            new_message=types.Content(role="user",parts=[
                types.Part(text="Fix synthetic answer() to equal 3")]),
        ):
            for part in (getattr(getattr(event,"content",None),"parts",None) or []):
                if part.function_call:events.append("call:"+part.function_call.name)
                if part.function_response:events.append("result:"+part.function_response.name)

        expected=[
            "call:load_skill","result:load_skill",
            "call:run_skill_script","result:run_skill_script",
            "call:edit_file","result:edit_file",
            "call:run_skill_script","result:run_skill_script",
            "call:submit_patch","result:submit_patch",
        ]
        assert events==expected,(events,expected)
        assert state["steps"]==["observed-before-fail","observed-after-pass"]
        assert "return 3" in (workspace/"example.py").read_text()
        assert not (workspace/"test_issue_contract.py").exists()
        result={"event_sequence":events,"before_status":state["before"]["status"],
                "after_status":state["after"]["status"],
                "comparison":state["after"]["comparison"],
                "scripted_model":True,"real_gemma_31b":False,
                "independent_issue_resolution":False}
        print("V4_CGR_OFFICIAL_SYNTHETIC_RESULT="+json.dumps(result,sort_keys=True),flush=True)
        return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(probe(args.zip.read_bytes()))


if __name__=="__main__":
    main()
