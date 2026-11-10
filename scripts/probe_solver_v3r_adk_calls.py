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
    class ScriptedProbe(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            functions = []
            config = getattr(llm_request, "config", None)
            for tool in (getattr(config, "tools", None) or []):
                for declaration in (getattr(tool, "function_declarations", None) or []):
                    functions.append(declaration.name)
            observed.append(functions)
            yield LlmResponse(content=types.Content(
                role="model", parts=[types.Part(text="CPU probe complete")]
            ))

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
        if len(observed)!=1:
            raise AssertionError(f"expected one no-inference model call, got {len(observed)}")
        offered=observed[0]
        report={"offers_load_skill":"load_skill" in offered,
                "offers_run_skill_script":"run_skill_script" in offered,
                "offered_skill_tools":[x for x in offered if "skill" in x],
                **snapshot}
        print("V3R_ADK_ACTUAL_LLM_REQUEST_TOOLS="+json.dumps(report,sort_keys=True),flush=True)
        # Tool advertised is mandatory to proceed to any 31B evaluation.
        if not report["offers_run_skill_script"]:
            raise RuntimeError("V3R_SCRIPT_UNREACHABLE_IN_REAL_ADK_LLM_REQUEST")
        return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(check(args.zip.read_bytes()))


if __name__=="__main__":
    main()
