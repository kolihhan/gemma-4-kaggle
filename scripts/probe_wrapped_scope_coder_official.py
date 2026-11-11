"""Official ADK CPU-only probe of compaction-safe LlmAgent-root AgentTool.

Synthetic model and workspace only. Verifies root model compaction, nested
read-only scope before native edits, and typed native tool behavior. This does
not prove actual 31B invokes AgentTool or improves independent correctness.
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

async def probe(source: bytes):
    from adk_submission import compile_submission,validate_directory,ModelRegistry,ToolRegistry
    from google.adk.apps.app import App,EventsCompactionConfig
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits

    with tempfile.TemporaryDirectory(prefix="wrapped-staged-adk-") as tmp:
        root=Path(tmp)
        pkg=root/"package"
        pkg.mkdir()
        with zipfile.ZipFile(io.BytesIO(source)) as z:
            if z.testzip() is not None:raise ValueError("invalid candidate ZIP")
            z.extractall(pkg)
        limits,_=build_submission_limits()
        validate_directory(pkg,limits=limits)
        repo=root/"repo"
        repo.mkdir()
        (repo/"sample.py").write_text("def result():\n    return 2\n")
        native=[]
        state={"turn":0,"packet":False,"submitted":False}

        def read_file(filepath: str):
            assert filepath=="sample.py"
            native.append("read_file")
            return {"content":(repo/filepath).read_text()}

        def edit_file(filepath: str,old_string: str,new_string: str):
            assert filepath=="sample.py" and old_string=="return 2" and new_string=="return 3"
            before=(repo/filepath).read_text()
            assert before.count(old_string)==1
            (repo/filepath).write_text(before.replace(old_string,new_string))
            native.append("edit_file")
            return {"modified":True}

        def submit_patch():
            assert "return 3" in (repo/"sample.py").read_text()
            native.append("submit_patch")
            state["submitted"]=True
            return {"submitted":True}

        def unused(*args,**kwargs):
            raise AssertionError("unexpected native tool")

        registry=ToolRegistry()
        registry.register("read_file",read_file)
        registry.register("edit_file",edit_file)
        registry.register("submit_patch",submit_patch)
        for name in ("run_command","write_file","get_status","get_code_neighbors",
                     "search_similar_code","get_code_subgraph"):
            def stub(*args,**kwargs):
                return unused(*args,**kwargs)
            stub.__name__=name
            registry.register(name,stub)

        packet=("EXPLICIT_BEHAVIOR: result() returns 3\n"
                "REPOSITORY_FACTS: sample.py has return 2\n"
                "CANDIDATE_AFFECTED_SURFACES: sample.py\n"
                "UNRESOLVED_AMBIGUITIES: none observed\n"
                "FIRST_DISCRIMINATING_ACTION: edit and verify\n")

        class Scripted(BaseLlm):
            async def generate_content_async(self,llm_request,stream=False):
                turn=state["turn"]
                data=getattr(llm_request,"contents",None) or []
                tool_responses=[
                    part.function_response for event in data
                    for part in (getattr(event,"parts",None) or [])
                    if getattr(part,"function_response",None)
                ]
                last=tool_responses[-1] if tool_responses else None
                if turn==0:
                    call=types.FunctionCall(name="mandatory_scope_then_patch",
                                             args={"request":"Fix sample.py result to return 3"})
                elif turn==1:
                    call=types.FunctionCall(name="read_file",args={"filepath":"sample.py"})
                elif turn==2:
                    assert last and last.name=="read_file",last
                    state["turn"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                        parts=[types.Part(text=packet)]))
                    return
                elif turn==3:
                    config=getattr(llm_request,"config",None)
                    if "REPOSITORY_FACTS: sample.py has return 2" not in str(getattr(config,"system_instruction","")):
                        raise AssertionError("nested scope packet not delivered")
                    state["packet"]=True
                    call=types.FunctionCall(name="edit_file",args={"filepath":"sample.py",
                        "old_string":"return 2","new_string":"return 3"})
                elif turn==4:
                    assert last and last.name=="edit_file",last
                    call=types.FunctionCall(name="submit_patch",args={})
                elif turn in (5,6):
                    if turn==5:
                        assert last and last.name=="submit_patch",last
                    state["turn"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                        parts=[types.Part(text="Synthetic patch complete")]))
                    return
                else:
                    # Four further user invocations exercise the default
                    # root-model compaction summarizer. Its answer can be
                    # ordinary short text because this is a CPU lifecycle gate.
                    state["turn"]+=1
                    yield LlmResponse(content=types.Content(role="model",
                        parts=[types.Part(text="No further action required.")]))
                    return
                state["turn"]+=1
                yield LlmResponse(content=types.Content(role="model",
                    parts=[types.Part(function_call=call)]))

        models=ModelRegistry()
        models.register(MODEL,Scripted(model=MODEL))
        agent=compile_submission(submission_dir=pkg,model_registry=models,
                                 tool_registry=registry,limits=limits)
        if type(agent).__name__!="LlmAgent":
            raise AssertionError("root must be LlmAgent for default compactor")
        root_tools=list(agent.tools)
        if len(root_tools)!=1 or "AgentTool" not in type(root_tools[0]).__name__:
            raise AssertionError("root must expose only one AgentTool")
        root_tool_names={getattr(t,"name",None) for t in root_tools}
        if root_tool_names!={"mandatory_scope_then_patch"}:
            raise AssertionError("root exposes a forbidden or wrong tool: "+str(root_tool_names))
        app=App(name="wrappedcpu",root_agent=agent,
                events_compaction_config=EventsCompactionConfig(
                    compaction_interval=3,overlap_size=1))
        # Execute the official ADK default summarizer resolution. This is
        # exactly where the SequentialAgent-root failed; it requires root
        # LlmAgent.canonical_model. A short session may not compact due to
        # event-savings heuristics, which is NOT a model-resolution failure.
        from google.adk.apps.compaction import _ensure_compaction_summarizer
        _ensure_compaction_summarizer(
            config=app.events_compaction_config,agent=app.root_agent)
        if app.events_compaction_config.summarizer is None:
            raise AssertionError("ROOT_LLM_DEFAULT_SUMMARIZER_NOT_RESOLVED")
        sessions=InMemorySessionService()
        session=await sessions.create_session(app_name="wrappedcpu",user_id="cpu")
        runner=Runner(app=app,session_service=sessions)
        observed=[]
        compacted=0
        for invocation in range(5):
            request=("Fix sample.py result to return 3" if invocation==0
                     else "Confirm the synthetic task was already completed.")
            async for event in runner.run_async(
                user_id="cpu",session_id=session.id,new_message=types.Content(
                    role="user",parts=[types.Part(text=request)]),
            ):
                if getattr(getattr(event,"actions",None),"compaction",None):
                    compacted+=1
                for part in (getattr(getattr(event,"content",None),"parts",None) or []):
                    if part.function_call:observed.append("call:"+part.function_call.name)
                    if part.function_response:observed.append("result:"+part.function_response.name)
        if native!=["read_file","edit_file","submit_patch"]:
            raise AssertionError({"native":native})
        if not state["packet"] or not state["submitted"]:
            raise AssertionError("nested mandatory tool path was not exercised")
        # The scorer's ADK 1.36.1 Runner invokes this exact official
        # sliding-window routine. Trigger it explicitly on the REAL recorded
        # session; short synthetic responses may not produce it automatically.
        from google.adk.apps.compaction import _run_compaction_for_sliding_window
        latest=await sessions.get_session(
            app_name="wrappedcpu",user_id="cpu",session_id=session.id)
        invocations={e.invocation_id for e in latest.events
                     if getattr(e,"invocation_id",None) and
                     not getattr(getattr(e,"actions",None),"compaction",None)}
        if len(invocations)<3:
            raise AssertionError("TOO_FEW_RECORDED_ADK_INVOCATIONS")
        # ADK 1.36.1 implements this as a coroutine and appends its event
        # to session_service itself; it does NOT yield events.
        def count_compactions(events):
            return sum(bool(getattr(getattr(e,"actions",None),"compaction",None))
                       for e in events)
        before=count_compactions(latest.events)
        await _run_compaction_for_sliding_window(app,latest,sessions)
        after_session=await sessions.get_session(
            app_name="wrappedcpu",user_id="cpu",session_id=session.id)
        after=count_compactions(after_session.events)
        manual_official_compaction=after-before
        if not compacted and manual_official_compaction<1:
            raise AssertionError("ROOT_LLM_REAL_ADK_COMPACTION_EVENT_NOT_CREATED")
        if "return 3" not in (repo/"sample.py").read_text():
            raise AssertionError("synthetic patch not materialized")
        print("WRAPPED_SCOPE_CODER_OFFICIAL_CPU_GATE="+json.dumps({
            "root_type":type(agent).__name__,
            "root_only_agent_tool":True,
            "native_tool_order":native,
            "runner_stream_compaction_events":compacted,
            "direct_official_compaction_events":manual_official_compaction,
            "recorded_user_invocations":len(invocations),
            "default_compactor_model_resolved":True,
            "compaction_fully_exercised":bool(compacted or manual_official_compaction),
            "typed_events":observed,
            "scope_packet_used":state["packet"],
            "synthetic_submission":True,
            "real_gemma_31b":False,"independent_issue_resolution":False
        },sort_keys=True),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    args=p.parse_args()
    asyncio.run(probe(args.zip.read_bytes()))

if __name__=="__main__":
    main()
