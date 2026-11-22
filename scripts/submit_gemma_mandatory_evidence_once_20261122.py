"""One Kaggle OFFICIAL code score of mandatory evidence-channel 31B candidate.

A distinct action-space/tool routing mechanism, NOT prompt-only; original
scored 0.18 31B base model & 5min/60 calls & sampling unchanged.
Strict prerequisites:
1. EXACT original scored source and byte-pinned candidate.
2. Native Kaggle CPU compiler confirmed with official wheelhouse.
3. One separate CPU-only builder yields byte-identical submission.zip.
4. Authenticated official code submission limits/absence of duplicates.

Predeclared hypothesis: Public >=0.20 vs own 0.18. Kill <=0.18, empty
score, bad native tool uptake, runtime errors. No adaptive retuning.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from scripts.build_gemma_mandatory_evidence_channel_20261122 import (
    build,files_for_candidate,MODEL,
)

COMP="gemma-4-developer-agent"
PUBLIC_SOURCE="lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
NATIVE_CPU="kolihhan/gemma-evidence-channel-native-cpu-20261122"
SCORE_KERNEL="kolihhan/gemma-evidence-channel-31b-once-20261122"
MARKER="gemma31-mandatory-evidence-tool-channel-once-20261122"
CHAMPION_REF="58183466"
CHAMPION_SCORE="0.18"
EXPECTED_CANDIDATE_SHA="652105308ee649322cc3f237618e4641c2e3c01ee15590758eb89dc3c59f08ea"
ROOT=Path("/tmp/gemma-evidence-channel-official-once")


def cli(args:list[str],*,timeout=150)->str:
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,
                     timeout=timeout)
    if p.returncode:
        # Refrain from reproducing full exceptions with credentials or URLs.
        raise RuntimeError("KAGGLE_"+args[0]+"_"+args[1]+"_ERROR_EXIT_"+str(p.returncode))
    return p.stdout


def ledger()->list[dict]:
    out=cli(["competitions","submissions",COMP,"-v"],timeout=90)
    return list(csv.DictReader(io.StringIO(out.lstrip("\ufeff"))))


def check_quota()->bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows=ledger()
    found=[r for r in rows if (r.get("description") or "")==MARKER]
    if len(found)>1:raise RuntimeError("DUPLICATE_OFFICIAL_MARKER")
    if found:
        print("GEMMA_EVIDENCE_EXISTING_SUBMISSION="+json.dumps({
          k:found[0].get(k) for k in ("ref","status","publicScore","date")
        },sort_keys=True),flush=True)
        return False
    best=[r for r in rows if r.get("ref")==CHAMPION_REF]
    if len(best)!=1 or best[0].get("publicScore")!=CHAMPION_SCORE or (
        "COMPLETE" not in (best[0].get("status") or "")):
        raise RuntimeError("EXACT_0P18_AUTHENTICATED_CHAMPION_MISSING")
    active=[r.get("ref") for r in rows if
            (r.get("status") or "").upper().split(".")[-1] in
            {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    api=KaggleApi();api.authenticate()
    limits=api.competition_get_submission_limits(COMP)
    receipt={
        "allowed_now":int(limits.num_allowed_now),
        "num_today":getattr(limits,"num_today",None),
        "limited_by_total":bool(limits.limited_by_total),
        "active":active,
    }
    print("GEMMA_EVIDENCE_OFFICIAL_SLOT="+json.dumps(receipt,sort_keys=True),flush=True)
    if limits.num_allowed_now<1 or limits.limited_by_total or active:
        print("GEMMA_EVIDENCE_NO_SAFE_OFFICIAL_SLOT=TRUE",flush=True)
        return False
    return True


def check_real_native_compiler()->dict:
    exact=cli(["kernels","status",NATIVE_CPU],timeout=90)
    if "KernelWorkerStatus.COMPLETE" not in exact:
        raise RuntimeError("OFFICIAL_NATIVE_CPU_COMPILER_NOT_COMPLETE")
    (ROOT/"native_cpu").mkdir(parents=True)
    cli(["kernels","output",NATIVE_CPU,"-p",str(ROOT/"native_cpu"),"-o"],timeout=120)
    result=ROOT/"native_cpu"/"gemma_evidence_channel_native_cpu.json"
    if not result.is_file():
        raise RuntimeError("OFFICIAL_NATIVE_CPU_COMPILER_JSON_MISSING")
    data=json.loads(result.read_text())
    if data.get("status")!="pass" or data.get("native_compiler") is not True:
        raise RuntimeError("OFFICIAL_NATIVE_CPU_COMPILER_DID_NOT_PASS")
    if data.get("root_class")!="LlmAgent" or data.get("model")!=MODEL:
        raise RuntimeError("OFFICIAL_NATIVE_CPU_COMPILER_WRONG_AGENT")
    names=list(map(str,data.get("registered_tools") or []))
    if any(x in names for x in ("run_command","write_file","search_similar_code")):
        raise RuntimeError("UNRESTRICTED_TOOL_NOT_REMOVED_BY_COMPILER")
    if not any("Skill" in name or "skill" in name for name in names):
        raise RuntimeError("OFFICIAL_NATIVE_COMPILER_SKILL_TOOL_NOT_IN_AGENT")
    print("GEMMA_EVIDENCE_NATIVE_TOOL_COMPILER_VERIFIED="+json.dumps({
        "root_class":data["root_class"],
        "model":MODEL,
        "visible_tool_names":names,
        "no_model_inference":True,
    },sort_keys=True),flush=True)
    return data


def prepare() -> str:
    if ROOT.exists():raise FileExistsError("fresh execution root required")
    ROOT.mkdir(parents=True)
    check_real_native_compiler()
    source=ROOT/"source"
    source.mkdir()
    cli(["kernels","output",PUBLIC_SOURCE,"-p",str(source),"-o"],timeout=120)
    file=source/"submission.zip"
    if not file.is_file():raise RuntimeError("PUBLIC_PINNED_SOURCE_ZIP_MISSING")
    raw=build(file.read_bytes())
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=EXPECTED_CANDIDATE_SHA:
        raise RuntimeError("CANDIDATE_ZIP_CHANGED_AFTER_NATIVE_CPU_GATE")
    parts=files_for_candidate(file.read_bytes())
    assert parts["agent.yaml"].count("model: "+MODEL)==1
    assert "run_command" not in parts["agent.yaml"]
    assert "skills/evidence-channel/SKILL.md" in parts
    (ROOT/"submission.zip").write_bytes(raw)
    code=(
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"raw=base64.b64decode({base64.b64encode(raw).decode('ascii')!r},validate=True)\n"
        f"expected={digest!r}\n"
        "assert hashlib.sha256(raw).hexdigest()==expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(raw)\n"
        "print('GEMMA_EVIDENCE_BUILDER_SHA='+expected)\n"
    )
    import nbformat
    notebook=nbformat.v4.new_notebook(cells=[
      nbformat.v4.new_markdown_cell(
        "# 31B mandatory evidence-channel one-shot competition experiment\n"
        "Source: verified 0.18 Budget-Fit V2 Apache-2.0. Model, time, "
        "sampling and tool count unchanged. Changed only the enforced "
        "native tool action-space architecture. No training."),
      nbformat.v4.new_code_cell(code)])
    notebook.metadata["kernelspec"]={"display_name":"Python 3",
                                   "language":"python","name":"python3"}
    kernel=ROOT/"notebook";kernel.mkdir()
    (kernel/"evidence_channel.ipynb").write_text(nbformat.writes(notebook))
    meta={"id":SCORE_KERNEL,"title":SCORE_KERNEL.split("/")[-1],
          "code_file":"evidence_channel.ipynb","language":"python",
          "kernel_type":"notebook","is_private":True,
          "enable_gpu":False,"enable_internet":False,"enable_tpu":False,
          "competition_sources":[COMP],
          "model_sources":[],"kernel_sources":[],"dataset_sources":[]}
    (kernel/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    print("GEMMA_EVIDENCE_OFFICIAL_CANDIDATE_SHA="+digest,flush=True)
    return digest


def submit_once()->None:
    if not os.environ.get("KAGGLE_API_TOKEN"):
        raise RuntimeError("MISSING_KAGGLE_TOKEN")
    # No GPU/model development; only the sanctioned official scorer runs 31B.
    if not check_quota():return
    expected=prepare()
    # Prevent overwrite of an already-existing differently named CPU builder.
    stat=subprocess.run(["kaggle","kernels","status",SCORE_KERNEL],
        capture_output=True,text=True,timeout=80)
    if stat.returncode==0:
        raise RuntimeError("PRIVATE_CPU_BUILDER_ALREADY_EXISTS")
    cli(["kernels","push","-p",str(ROOT/"notebook"),"-t","600"],timeout=240)
    print("GEMMA_EVIDENCE_CPU_BUILDER_PUSHED="+SCORE_KERNEL,flush=True)
    for i in range(42):
        p=subprocess.run(["kaggle","kernels","status",SCORE_KERNEL],
                         capture_output=True,text=True,timeout=80)
        state=re.findall(r"KernelWorkerStatus[.][A-Z_]+",p.stdout+p.stderr)
        if state:
            state=state[0].split(".")[-1]
            if state=="COMPLETE":break
            if state in {"ERROR","FAILED","CANCELLED"}:
                raise RuntimeError("PRIVATE_CPU_BUILDER_FAILED")
        time.sleep(10)
    else:raise RuntimeError("CPU_BUILDER_NOT_COMPLETE_NO_OFFICIAL_SUBMIT")
    (ROOT/"remote").mkdir()
    cli(["kernels","output",SCORE_KERNEL,"-p",str(ROOT/"remote"),"-o"],timeout=120)
    product=ROOT/"remote"/"submission.zip"
    if not product.is_file() or hashlib.sha256(product.read_bytes()).hexdigest()!=expected:
        raise RuntimeError("REMOTE_BUILDER_HASH_OR_OUTPUT_MISMATCH")
    print("GEMMA_EVIDENCE_REMOTE_CPU_BUILDER_VERIFIED="+expected,flush=True)
    if not check_quota():return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    api.competition_submit_code(
        file_name="submission.zip",message=MARKER,competition=COMP,
        kernel=SCORE_KERNEL,kernel_version=1,quiet=True)
    print("GEMMA_EVIDENCE_OFFICIAL_SUBMIT_API_ACCEPTED=TRUE",flush=True)
    for i in range(5):
        rows=ledger()
        found=[r for r in rows if (r.get("description") or "")==MARKER]
        if found:
            print("GEMMA_EVIDENCE_OFFICIAL_RECEIPT="+json.dumps({
                k:found[0].get(k) for k in
                ("ref","date","status","publicScore")
            },sort_keys=True),flush=True)
            return
        if i<4:time.sleep(12)
    print("GEMMA_EVIDENCE_NO_OFFICIAL_RECEIPT_DO_NOT_RETRY=TRUE",flush=True)


if __name__=="__main__":
    try:submit_once()
    finally:
        if ROOT.exists():shutil.rmtree(ROOT)
