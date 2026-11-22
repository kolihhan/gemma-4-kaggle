"""One-shot official test of a real causal-localization SequentialAgent.

This changes topology (not a tool prompt). No GPU development: only a
CPU-packaged candidate; the official Kaggle scorer performs real 31B inference
if separately authorized by the immutable GO marker.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from scripts.build_gemma_causal_sequence_20261122 import make_zip
from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION, SOURCE, MODEL, NATIVE, cmd, authenticated_submissions
)

MARKER = "causal-localization-sequence-v1-20261122"
KERNEL = "kolihhan/gemma-causal-location-sequence-20261122-v1"
ROOT = Path("/tmp/gemma-causal-location-sequence-20261122")
GO = Path("experiments/causal-sequence-v1/GO_OFFICIAL_20261122")


def compiled(archive: bytes) -> None:
    from adk_submission import (validate_directory, compile_submission,
                                ModelRegistry, ToolRegistry)
    from google.adk.models.base_llm import BaseLlm
    from swegemma.config import build_submission_limits

    class NoInference(BaseLlm):
        async def generate_content_async(self,*args,**kwargs):
            raise RuntimeError("NO_INFERENCE_IN_COMPILER")
            yield

    with tempfile.TemporaryDirectory(prefix="causal-seq-") as d:
        path = Path(d)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            z.extractall(path)
        limits, _ = build_submission_limits()
        validate_directory(path, limits=limits)
        models = ModelRegistry()
        models.register(MODEL, NoInference(model=MODEL))
        registry = ToolRegistry()
        for name in NATIVE:
            def unused_tool(*args,**kwargs):
                raise RuntimeError("NO_TOOL_EXECUTION_IN_COMPILER")
            registry.register(name, unused_tool)
        root = compile_submission(
            submission_dir=path,model_registry=models,tool_registry=registry)
        sub = getattr(root, "sub_agents", [])
        if type(root).__name__ != "SequentialAgent" or len(sub) != 2:
            raise ValueError(f"wrong compiled topology: {type(root).__name__}, {len(sub)}")
        if [x.name for x in sub] != ["location_scout", "swe_coder"]:
            raise ValueError("wrong child agent order or name")
        if not all(getattr(x.model, "model", None) == MODEL for x in sub):
            raise ValueError("base model mismatch")
        if any(t.name == "submit_patch" for t in sub[0].tools):
            raise ValueError("scout must not submit a patch")
        if not any(t.name == "submit_patch" for t in sub[1].tools):
            raise ValueError("coder must own final submission")
        print("GEMMA_CAUSAL_OFFICIAL_NATIVE_COMPILER=PASS",flush=True)


def check_slot() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows = authenticated_submissions()
    matched = [r for r in rows if r.get("description") == MARKER]
    if len(matched) > 1: raise RuntimeError("DUPLICATE_OFFICIAL_MARKER")
    if matched:
        print("GEMMA_CAUSAL_EXISTING_RECEIPT="+json.dumps({
            k:matched[0].get(k) for k in ("ref","status","publicScore","date")
        },sort_keys=True),flush=True)
        return False
    api=KaggleApi();api.authenticate()
    q=api.competition_get_submission_limits(COMPETITION)
    active = [r.get("ref") for r in rows if
              (r.get("status") or "").upper().split(".")[-1] in
              {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    print("GEMMA_CAUSAL_SLOT="+json.dumps({
        "allowed_now":q.num_allowed_now,"num_today":q.num_today,
        "limited_by_total":q.limited_by_total,"active":active
    },sort_keys=True),flush=True)
    if q.num_allowed_now < 1 or q.limited_by_total or active:
        raise RuntimeError("NO_SAFE_SCORING_SLOT")
    return True


def prepare() -> None:
    if ROOT.exists():
        raise FileExistsError("refuse to reuse CPU staging directory")
    source_dir=ROOT/"source"
    source_dir.mkdir(parents=True)
    subprocess.run(["kaggle","kernels","output",SOURCE,
                    "-p",str(source_dir),"-o"],
                   check=True,stdout=subprocess.DEVNULL,timeout=240)
    source=source_dir/"submission.zip"
    if not source.is_file():
        raise FileNotFoundError("pinned public scored-source ZIP unavailable")
    raw,meta=make_zip(source.read_bytes())
    compiled(raw)
    archive=ROOT/"submission.zip"
    archive.write_bytes(raw)
    print("GEMMA_CAUSAL_ARCHIVE="+json.dumps(meta,sort_keys=True),flush=True)
    import nbformat
    hexdata=base64.b64encode(raw).decode("ascii")
    sha=hashlib.sha256(raw).hexdigest()
    code = (
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"raw=base64.b64decode({hexdata!r},validate=True)\n"
        f"expected={sha!r}\n"
        "assert hashlib.sha256(raw).hexdigest()==expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(raw)\n"
        "print('GEMMA_CAUSAL_KAGGLE_KERNEL_SHA256='+expected)\n"
    )
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# Causal localization sequence — original architecture experiment\n"
            "Scored 0.18 control source is Apache-2.0 BudgetFit V2. "
            "Modified topology: mandatory bounded scout then original coder; "
            "same 31B variant, native tools, five-minute, sixty-call budget."),
        nbformat.v4.new_code_cell(code)
    ])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python","name":"python3"}
    dest=ROOT/"notebook"
    dest.mkdir()
    (dest/"causal-sequence.ipynb").write_text(nbformat.writes(nb))
    (dest/"kernel-metadata.json").write_text(json.dumps({
        "id":KERNEL,"title":"causal-localization-sequence-20261122-v1",
        "code_file":"causal-sequence.ipynb","language":"python",
        "kernel_type":"notebook","is_private":True,
        "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
        "competition_sources":[COMPETITION],"dataset_sources":[],
        "kernel_sources":[],"model_sources":[]
    },sort_keys=True,indent=2)+"\n")
    shutil.rmtree(source_dir)
    print("GEMMA_CAUSAL_PRIVATE_BUILDER_READY=TRUE",flush=True)


def official_once() -> None:
    if Path('experiments/causal-sequence-v1/NO_GO.md').is_file():
        raise RuntimeError('STOP_KNOWN_ROOT_SEQUENTIAL_COMPACTION_FAILURE_NO_OFFICIAL_SUBMISSION')
    if not GO.is_file() or GO.read_text().strip() != "GO_CAUSAL_SEQUENCE_20261122_V1":
        raise RuntimeError("EXPLICIT_GO_MARKER_MISSING")
    if not check_slot():
        return
    prepare()
    local=(ROOT/"submission.zip").read_bytes()
    expected=hashlib.sha256(local).hexdigest()
    cmd(["kaggle","kernels","push","-p",str(ROOT/"notebook"),"-t","600"],
        timeout=240)
    for i in range(72):
        status=cmd(["kaggle","kernels","status",KERNEL],timeout=60)
        if "KernelWorkerStatus.COMPLETE" in status: break
        if any(x in status for x in ("KernelWorkerStatus.ERROR",
                                    "KernelWorkerStatus.FAILED",
                                    "KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("CPU_BUILDER_ERRORED")
        time.sleep(10)
    else:
        raise RuntimeError("CPU_BUILDER_NOT_COMPLETE_NO_SUBMISSION")
    resultdir=ROOT/"remote";resultdir.mkdir()
    subprocess.run(["kaggle","kernels","output",KERNEL+"/1",
                    "-p",str(resultdir),"-o"],
                   check=True,stdout=subprocess.DEVNULL,timeout=240)
    remote=(resultdir/"submission.zip").read_bytes()
    if remote!=local or hashlib.sha256(remote).hexdigest()!=expected:
        raise RuntimeError("REMOTE_BYTE_MISMATCH")
    print("GEMMA_CAUSAL_PRIVATE_BUILDER_VERIFIED="+expected,flush=True)
    if not check_slot():return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    api.competition_submit_code(
        file_name="submission.zip",message=MARKER,
        competition=COMPETITION,kernel=KERNEL,kernel_version=1,quiet=True)
    for _ in range(14):
        r=[v for v in authenticated_submissions() if v.get("description")==MARKER]
        if r:
            print("GEMMA_CAUSAL_OFFICIAL_RECEIPT="+json.dumps({
                x:r[0].get(x) for x in ("ref","status","date","publicScore")
            },sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("SUBMISSION_RECEIPT_UNCONFIRMED_NO_AUTORETRY")


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ("preflight","submit"):
        raise SystemExit("preflight|submit")
    if sys.argv[1]=="preflight":prepare()
    else:official_once()


if __name__=="__main__":main()
