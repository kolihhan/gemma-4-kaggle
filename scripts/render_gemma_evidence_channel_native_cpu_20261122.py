"""Render one CPU-only, no-model-inference native compiler check on Kaggle.

The private kernel uses the official competition wheelhouse / docker image
to validate & compile the scored 31B derived agent including mandatory
Skill. No reference patches, tasks, GPU or official submission are used.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from scripts.build_gemma_mandatory_evidence_channel_20261122 import build

REF="kolihhan/gemma-evidence-channel-native-cpu-20261122"
COMP="gemma-4-developer-agent"
WHEEL="metric/gemma-4-developer-agent-wheelhouse"
IMAGE="gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
MODEL="gemma-4-31b-it-qat-w4a16-ct"
NATIVE=("run_command","read_file","edit_file","write_file","get_status",
        "submit_patch","get_code_neighbors","search_similar_code",
        "get_code_subgraph")

BODY=String = r'''
import base64,hashlib,io,json,subprocess,shutil,sys,glob
from pathlib import Path
import tempfile
import zipfile
ROOT=Path("/kaggle/working")
WHEELHOUSE=Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
OUTPUT=ROOT/"gemma_evidence_channel_native_cpu.json"
MODEL="gemma-4-31b-it-qat-w4a16-ct"
NATIVE=("run_command","read_file","edit_file","write_file","get_status",
        "submit_patch","get_code_neighbors","search_similar_code",
        "get_code_subgraph")

def install_official():
    if not WHEELHOUSE.is_dir():
        raise RuntimeError("OFFICIAL_WHEELHOUSE_MISSING")
    for pattern in ("/usr/local/lib/python*/dist-packages/*cutlass*.pth",
                    "/usr/local/lib/python*/site-packages/*cutlass*.pth"):
        for item in glob.glob(pattern):
            try: Path(item).unlink()
            except OSError: pass
    scratch=Path("/tmp/gemma-native-wheelhouse")
    scratch.mkdir(parents=True,exist_ok=True)
    for wheel in WHEELHOUSE.glob("*.whl"):
        if "cutlass" in wheel.name.lower():continue
        name=wheel.name.replace("cu128","+cu128") if "cu128" in wheel.name and "+" not in wheel.name else wheel.name
        dst=scratch/name
        if not dst.exists():
            try:dst.symlink_to(wheel)
            except OSError:shutil.copyfile(wheel,dst)
    wheels=sorted(str(p) for p in scratch.glob("*.whl"))
    if not wheels:raise RuntimeError("EMPTY_OFFICIAL_WHEELHOUSE")
    subprocess.run([sys.executable,"-m","pip","install","-q",
                    "--no-deps","--force-reinstall",*wheels],
                   check=True,capture_output=True,timeout=240)

def compile_native(raw):
    from adk_submission import (
        validate_directory,compile_submission,ModelRegistry,ToolRegistry,
    )
    from google.adk.models.base_llm import BaseLlm
    from swegemma.config import build_submission_limits
    class NoInference(BaseLlm):
        async def generate_content_async(self,*a,**k):
            raise RuntimeError("FORBIDDEN_MODEL_INFERENCE")
            yield
    with tempfile.TemporaryDirectory(prefix="gemma-evidence-adk-") as d:
        root=Path(d)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip() is not None:raise ValueError("BAD_CANDIDATE_ZIP")
            z.extractall(root)
        limits,_=build_submission_limits()
        validate_directory(root,limits=limits)
        models=ModelRegistry()
        models.register(MODEL,NoInference(model=MODEL))
        tools=ToolRegistry()
        for toolname in NATIVE:
            def no_tool(*a,**k):raise RuntimeError("FORBIDDEN_TOOL_USE")
            tools.register(toolname,no_tool)
        agent=compile_submission(
            submission_dir=root,model_registry=models,tool_registry=tools)
        if type(agent).__name__!="LlmAgent":
            raise ValueError("WRONG_ROOT_CLASS")
        if getattr(agent.model,"model",None)!=MODEL:
            raise ValueError("WRONG_MODEL")
        names=[getattr(t,"name",getattr(t,"__name__",type(t).__name__)) for t in agent.tools]
        if "run_command" in names or "search_similar_code" in names or "write_file" in names:
            raise ValueError("UNRESTRICTED_TOOLS_LEAKED")
        if len(agent.tools)<4:
            raise ValueError("MISSING_REQUIRED_ADK_TOOLS")
        return {"native_compiler":True,"root_class":type(agent).__name__,
                "registered_tools":list(map(str,names)),
                "model":MODEL,
                "no_gpu":True,"no_model_inference":True,
                "official_submission":False,
                "no_grader":True}

def main():
    try:
        raw=base64.b64decode(ARCHIVE_B64,validate=True)
        if hashlib.sha256(raw).hexdigest()!=EXPECTED_ARCHIVE_SHA:
            raise ValueError("SOURCE_ZIP_SHA_MISMATCH")
        install_official()
        result=compile_native(raw)
        result["status"]="pass"
        OUTPUT.write_text(json.dumps(result,sort_keys=True))
        print("GEMMA_EVIDENCE_NATIVE_CPU_COMPILE=PASS",flush=True)
        print("GEMMA_EVIDENCE_NATIVE_CPU_TOOLS="+json.dumps(result["registered_tools"]),flush=True)
    except BaseException as exc:
        result={"status":"fail","failure_type":type(exc).__name__,
                "no_gpu":True,"no_model_inference":True,
                "official_submission":False}
        OUTPUT.write_text(json.dumps(result,sort_keys=True))
        print("GEMMA_EVIDENCE_NATIVE_CPU_COMPILE=FAIL_"+type(exc).__name__,flush=True)
        raise

if __name__=="__main__":main()
'''

def render(source_zip:bytes,target:Path)->dict:
    if target.exists():raise FileExistsError("refuse override")
    candidate=build(source_zip)
    digest=hashlib.sha256(candidate).hexdigest()
    encoded=base64.b64encode(candidate).decode("ascii")
    script="ARCHIVE_B64="+repr(encoded)+"\nEXPECTED_ARCHIVE_SHA="+repr(digest)+"\n"+BODY
    compile(script,"candidate_native_cpu.py","exec")
    target.mkdir(parents=True)
    (target/"candidate_native_cpu.py").write_text(script)
    meta={"id":REF,"title":REF.split("/")[-1],
          "code_file":"candidate_native_cpu.py","language":"python",
          "kernel_type":"script","is_private":True,
          "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
          "docker_image":IMAGE,
          "competition_sources":[COMP],
          "dataset_sources":[WHEEL],
          "model_sources":[],"kernel_sources":[]}
    (target/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    return {"candidate_sha256":digest,"exact_source_model":MODEL,
            "kernel_ref":REF,"gpu":False,"competition_submission":False}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    opts=ap.parse_args()
    info=render(opts.source_zip.read_bytes(),opts.out)
    print("GEMMA_EVIDENCE_NATIVE_CPU_PRIVATE_PLAN="+json.dumps(info,sort_keys=True))
