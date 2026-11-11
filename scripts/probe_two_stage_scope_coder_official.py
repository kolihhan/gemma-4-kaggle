"""Official ADK CPU-only lifecycle gate for mandatory scope -> coder.

Uses a scripted No-Gemma model and synthetic one-file workspace. This verifies
the actual compiled workflow order, tool access and typed tool events, NOT
hidden SWE issue resolution or autonomous 31B stage compliance.
"""
from __future__ import annotations
import argparse
import asyncio
import io
import json
from pathlib import Path
import tempfile
import zipfile

MODEL="gemma-4-31b-it-qat-w4a16-ct"

async def probe(archive: bytes):
    from adk_submission import compile_submission, validate_directory, ModelRegistry, ToolRegistry
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits

    with tempfile.TemporaryDirectory(prefix="staged-swe-adk-") as tmp:
        root=Path(tmp)
        package=root/"package"
        package.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            if z.testzip() is not None:raise ValueError("archive CRC invalid")
            z.extractall(package)
        limits,_=build_submission_limits()
        validate_directory(package,limits=limits)
        workspace=root/"workspace"
        workspace.mkdir()
        (workspace/"sample.py").write_text("def result():\n    return 2\n")
        calls=[]
        state={"step":0,"submitted":False,"scope_seen_by_coder":False}

        def read_file(filepath: str):
            if filepath!="sample.py":raise AssertionError("wrong file")
            calls.append("read")
            return {"content":(workspace/filepath).read_text()}

        def edit_file(filepath: str,old_string: str,new_string: str):
            if filepath!="sample.py" or old_string!="return 2" or new_string!="return 3":
                raise AssertionError("unexpected edit")
            before=(workspace/filepath).read_text()
            if before.count(old_string)!=1:raise AssertionError("ambiguous edit")
            (workspace/filepath).write_text(before.replace(old_string,new_string))
            calls.append("edit")
            return {"modified":True}

        def submit_patch():
            if "return 3" not in (workspace/"sample.py").read_text():
                raise AssertionError("invalid synthetic submission")
            calls.append("submit")
            state["submitted"]=True
            return {"submitted":True}

        def forbidden(*args,**kwargs):
            raise AssertionError("unexpected tool call")

        registry=ToolRegistry()
        registry.register("read_file",read_file)
        registry.register("edit_file",edit_file)
        registry.register("submit_patch",submit_patch)
        for name in ("run_command","write_file","get_status","get_code_neighbors",
                     "search_similar_code","get_code_subgraph"):
            # Tool access is controlled by declared role; these are stubs.
            def stub(*args,**kwargs):
                return forbidden(*args,**kwargs)
            stub.__name__=name
            registry.register(name,stub)

        scope_packet=(
            "EXPLICIT_BEHAVIOR: result() should return 3\n"
            "REPOSITORY_FACTS: sample.py currently returns 2\n"
            "CANDIDATE_AFFECTED_SURFACES: sample.py\n"
            "UNRESOLVED_AMBIGUITIES: none observed\n"
            "FIRST_DISCRIMINATING_ACTION: change return and verify\n"
        )

        class ScriptedModel(BaseLlm):
            async def generate_content_async(self,llm_request,stream=False):
                step=state["step"]
                history=getattr(llm_request,"contents",None) or []
                results=[part.function_response for msg in history
                         for part in (getattr(msg,"parts",None) or [])
                         if getattr(part,"function_response",None)]
                latest=results[-1] if results else None
                if step==0:
                    # Root sequential MUST start with an investigator.
                    call=types.FunctionCall(name="read_file",args={"filepath":"sample.py"})
                elif step==1:
                    assert latest and latest.name=="read_file",latest
                    state["step"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                        parts=[types.Part(text=scope_packet)]))
                    return
                elif step==2:
                    # The coder receives the analyst output through state.
                    config=getattr(llm_request,"config",None)
                    system=str(getattr(config,"system_instruction",""))
                    if "REPOSITORY_FACTS: sample.py currently returns 2" not in system:
                        raise AssertionError("scope_packet was not injected into coder")
                    state["scope_seen_by_coder"]=True
                    call=types.FunctionCall(name="edit_file",args={
                        "filepath":"sample.py","old_string":"return 2","new_string":"return 3"})
                elif step==3:
                    assert latest and latest.name=="edit_file",latest
                    call=types.FunctionCall(name="submit_patch",args={})
                elif step==4:
                    assert latest and latest.name=="submit_patch",latest
                    state["step"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                         parts=[types.Part(text="synthetic task submitted")]))
                    return
                else:
                    raise AssertionError("unexpected model step "+str(step))
                state["step"]+=1
                yield LlmResponse(content=types.Content(role="model",
                     parts=[types.Part(function_call=call)]))

        models=ModelRegistry()
        models.register(MODEL,ScriptedModel(model=MODEL))
        agent=compile_submission(submission_dir=package,model_registry=models,
                                 tool_registry=registry,limits=limits)
        if type(agent).__name__!="SequentialAgent":
            raise AssertionError("root must be SequentialAgent")
        children=list(agent.sub_agents)
        if len(children)!=2 or children[0].name!="read_only_scope" or children[1].name!="sole_patch_writer":
            raise AssertionError("stage ordering does not match declarative YAML")
        readonly_tools={t.name if hasattr(t,"name") else str(t) for t in children[0].tools}
        if {"edit_file","write_file","run_command","submit_patch"} & readonly_tools:
            raise AssertionError("investigator has mutation tools")

        session_service=InMemorySessionService()
        session=await session_service.create_session(app_name="stagedcpu",user_id="cpu")
        runner=Runner(agent=agent,app_name="stagedcpu",session_service=session_service)
        events=[]
        async for event in runner.run_async(
            user_id="cpu",session_id=session.id,new_message=types.Content(
                role="user",parts=[types.Part(text="Make sample.py result() return 3")]),
        ):
            for p in (getattr(getattr(event,"content",None),"parts",None) or []):
                if p.function_call:events.append("call:"+p.function_call.name)
                if p.function_response:events.append("result:"+p.function_response.name)
        expected=["call:read_file","result:read_file","call:edit_file",
                  "result:edit_file","call:submit_patch","result:submit_patch"]
        if events!=expected:raise AssertionError({"observed":events,"expected":expected})
        if calls!=["read","edit","submit"] or not state["submitted"]:
            raise AssertionError("unexpected native tool execution order")
        if not state["scope_seen_by_coder"]:
            raise AssertionError("stage output packet never reached writer")
        if state["step"]!=5:raise AssertionError("unexpected scripted turns")
        print("STAGED_SCOPE_CODER_OFFICIAL_CPU_GATE="+json.dumps({
            "root":"SequentialAgent","stage_order":[c.name for c in children],
            "events":events,"readonly_scope":True,
            "packet_reached_writer":True,
            "scripted_model":True,"real_gemma_31b":False,
            "independent_issue_resolution":False
        },sort_keys=True),flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--zip",type=Path,required=True)
    opts=ap.parse_args()
    asyncio.run(probe(opts.zip.read_bytes()))


if __name__=="__main__":
    main()
