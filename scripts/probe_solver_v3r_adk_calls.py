"""Official ADK CPU-only end-to-end tool advertisement probe for Solver V3-R.

Uses the *actual compiled YAML and SkillToolset* with a scripted, no-inference
BaseLlm. Captures tool declarations supplied to the model through Runner, not
merely static names attached to compiled agent.tools. No Kaggle tasks are run.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
from pathlib import Path
import tempfile
import zipfile


async def check(candidate: bytes) -> dict:
    from adk_submission import compile_submission, validate_directory, ModelRegistry, ToolRegistry
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits

    observed = []
    tool_responses = []
    turn = [0]
    class ScriptedProbe(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            functions = []
            config = getattr(llm_request, "config", None)
            for tool in (getattr(config, "tools", None) or []):
                for declaration in (getattr(tool, "function_declarations", None) or []):
                    functions.append(declaration.name)
            observed.append(functions)
            response_parts = [
                p.function_response for msg in (getattr(llm_request,"contents",None) or [])
                for p in (getattr(msg,"parts",None) or [])
                if getattr(p,"function_response",None) is not None
            ]
            if response_parts:
                tool_responses.extend({"name":x.name,"response":x.response}
                                      for x in response_parts)
            if turn[0] == 0:
                call = types.FunctionCall(
                    name="load_skill",args={"skill_name":"repair-witness"})
                print("V3R_SYNTHETIC_ADK_MODEL_CALL=load_skill",flush=True)
                response = types.Content(role="model",parts=[types.Part(function_call=call)])
            elif turn[0] == 1:
                schema = [
                    d for t in (getattr(config,"tools",None) or [])
                    for d in (getattr(t,"function_declarations",None) or [])
                    if d.name=="run_skill_script"
                ]
                if len(schema)!=1:
                    raise AssertionError("run_skill_script not declared on second model call")
                declaration=schema[0].model_dump(exclude_none=True)
                params = getattr(schema[0],"parameters",None)
                props=set((getattr(params,"properties",None) or {}).keys())
                json_parameters=declaration.get("parameters_json_schema") or {}
                props.update((json_parameters.get("properties") or {}).keys())
                print("V3R_SCRIPT_TOOL_SCHEMA="+json.dumps(
                    declaration,sort_keys=True,default=str)[:3200],flush=True)
                print("V3R_SCRIPT_TOOL_PARAMETER_KEYS="+json.dumps(sorted(props)),flush=True)
                arguments={"skill_name":"repair-witness","file_path":"scripts/witness.py"}
                if "script_args" in props:
                    arguments["script_args"]={"phase":"after","target":"test_synthetic.py"}
                elif "args" in props:
                    arguments["args"]={"phase":"after","target":"test_synthetic.py"}
                else:
                    # The installed ADK 1.36.1 can serialize JSON-schema only
                    # inside a different declaration field. Test the documented
                    # script_args call rather than asserting an empty .parameters.
                    arguments["script_args"]={"phase":"after","target":"test_synthetic.py"}
                    print("V3R_SCRIPT_ARGS_FALLBACK_TO_DOCUMENTED_SIGNATURE=TRUE",flush=True)
                call=types.FunctionCall(name="run_skill_script",args=arguments)
                print("V3R_SYNTHETIC_ADK_MODEL_CALL=run_skill_script",flush=True)
                response=types.Content(role="model",parts=[types.Part(function_call=call)])
            else:
                response=types.Content(role="model",parts=[
                    types.Part(text="CPU probe complete")])
            turn[0]+=1
            yield LlmResponse(content=response)

    with tempfile.TemporaryDirectory(prefix="gemma-v3r-adk-events-") as tmp:
        root = Path(tmp) / "submission"
        root.mkdir()
        with zipfile.ZipFile(io.BytesIO(candidate)) as archive:
            if archive.testzip() is not None:
                raise ValueError("candidate archive CRC invalid")
            archive.extractall(root)

        limits, _ = build_submission_limits()
        validate_directory(root, limits=limits)
        models = ModelRegistry()
        models.register("gemma-4-31b-it-qat-w4a16-ct", ScriptedProbe(model="gemma-4-31b-it-qat-w4a16-ct"))
        tools = ToolRegistry()
        for name in (
            "run_command", "read_file", "edit_file", "write_file", "get_status",
            "submit_patch", "get_code_neighbors", "search_similar_code",
            "get_code_subgraph",
        ):
            def unused(*args, **kwargs):
                raise AssertionError("native tool must not be called in synthetic probe")
            tools.register(name, unused)
        agent = compile_submission(
            submission_dir=root, model_registry=models, tool_registry=tools,
        )
        skill_tools = [t for t in agent.tools if type(t).__name__ == "SkillToolset"]
        if len(skill_tools) != 1:
            raise AssertionError("expected exactly one compiled SkillToolset")
        skill = skill_tools[0]
        snapshot = {
            "root_code_executor": type(getattr(agent, "code_executor", None)).__name__,
            "skill_code_executor": type(getattr(skill, "_code_executor", None)).__name__,
            "skill_environment": type(getattr(skill, "_env", None)).__name__,
        }
        print("V3R_ADK_EXECUTION_BINDINGS="+json.dumps(snapshot,sort_keys=True),flush=True)

        service = InMemorySessionService()
        session = await service.create_session(app_name="v3r_cpu_probe",user_id="tester")
        runner = Runner(agent=agent,app_name="v3r_cpu_probe",session_service=service)
        events=[]
        async for event in runner.run_async(
            user_id="tester",session_id=session.id,
            new_message=types.Content(role="user",parts=[types.Part(text="Check installed tool declaration availability only")]),
        ):
            events.append({
                "author":getattr(event,"author",None),
                "tool_calls":[p.function_call.name for p in
                    (getattr(getattr(event,"content",None),"parts",None) or [])
                    if getattr(p,"function_call",None)],
                "tool_results":[p.function_response.name for p in
                    (getattr(getattr(event,"content",None),"parts",None) or [])
                    if getattr(p,"function_response",None)],
            })
        print("V3R_ADK_FAKE_MODEL_EVENTS="+json.dumps(events,sort_keys=True),flush=True)
        print("V3R_SYNTHETIC_TOOL_FUNCTION_RESPONSES="+json.dumps(
            tool_responses,default=str,sort_keys=True)[:4200],flush=True)
        if len(observed)!=3:
            raise AssertionError(f"expected 3 no-inference model turns, got {len(observed)}")
        if not any(x["name"]=="load_skill" for x in tool_responses):
            raise AssertionError("ADK did not return a load_skill function response")
        scripts=[x for x in tool_responses if x["name"]=="run_skill_script"]
        if len(scripts)!=1:
            raise AssertionError("ADK did not return run_skill_script function response")
        offered=observed[0]
        scripts=[x for x in tool_responses if x["name"]=="run_skill_script"]
        script_result=scripts[0]["response"] or {}
        report={"script_return_kind": "error" if script_result.get("error") else "normal",
                "script_error_code":script_result.get("error_code"),
                "actual_function_response_for_script":True,
                "offers_load_skill":"load_skill" in offered,
                "offers_run_skill_script":"run_skill_script" in offered,
                "offered_skill_tools":[x for x in offered if "skill" in x],
                **snapshot}
        print("V3R_ADK_ACTUAL_LLM_REQUEST_TOOLS="+json.dumps(report,sort_keys=True),flush=True)
        # Tool advertised is mandatory to proceed to any 31B evaluation.
        if not report["offers_run_skill_script"]:
            raise RuntimeError("V3R_SCRIPT_UNREACHABLE_IN_REAL_ADK_LLM_REQUEST")
        if report["script_error_code"] == "NO_CODE_EXECUTOR":
            print("V3R_STANDALONE_RUNNER_NEEDS_EVALUATOR_EXECUTOR=TRUE",flush=True)
        elif report["script_error_code"] is not None:
            print("V3R_STANDALONE_RUNNER_SCRIPT_ERROR="+str(report["script_error_code"]),flush=True)
        else:
            print("V3R_ADK_SCRIPT_FUNCTION_RESPONSE_DELIVERED_NO_ERROR=TRUE",flush=True)
        return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(check(args.zip.read_bytes()))


if __name__=="__main__":
    main()
