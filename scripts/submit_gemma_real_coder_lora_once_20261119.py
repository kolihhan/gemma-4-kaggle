"""One-shot official Kaggle submission of the real 31B coder LoRA candidate.

Source: publicly shared competition notebook ayush04barai/lora-step-2.
Contest rules allow public Competition Code sharing as OSI-licensed.
The underlying weights carry no independently established separate model license:
record this provenance rather than inventing one.

Hard guards: authenticated exact one remaining slot, no active grader, no
duplicate marker, source still public and tied to this competition, pinned
private builder version 1 COMPLETE, full ZIP hash and member structure.
One official submit only. No local model inference or development GPU.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import tempfile
import time
from pathlib import Path
import zipfile

COMPETITION="gemma-4-developer-agent"
SOURCE="ayush04barai/lora-step-2"
KERNEL="kolihhan/gemma31-018-coder-lora-cpu-nov19"
MARKER="gemma31-real-coder-lora-one-variable-20261119"
EXPECTED="deccb0f8cecc69bc4b1eb81db73b208fb84d45571730fa43b033f21c27885b5e"
SCORED_BASE_SHA="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
MODEL="gemma-4-31b-it-qat-w4a16-ct"
EXPECTED_FILES={
 "agent.yaml","prompts/system.md","configs/sampling.yaml",
 "eval_config.yaml","adapters/main_lora/adapter_config.json",
 "adapters/main_lora/adapter_model.safetensors",
}

def command(args,*,timeout=120):
    return subprocess.run(args,text=True,capture_output=True,check=True,timeout=timeout).stdout

def ledger():
    raw=command(["kaggle","competitions","submissions",COMPETITION,"-v","-q"]).lstrip("\ufeff")
    rows=list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        raise RuntimeError("NO_AUTHENTICATED_SUBMISSION_LEDGER")
    return rows

def existing(rows):
    found=[r for r in rows if str(r.get("description") or "")==MARKER]
    if len(found)>1:
        raise RuntimeError("DUPLICATE_MARKER_ALREADY_PRESENT")
    return found[0] if found else None

def gate():
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows=ledger()
    prev=existing(rows)
    if prev:
        print("GEMMA_LORA_OFFICIAL_EXISTING_RECEIPT="+json.dumps(
            {k:prev.get(k) for k in ("ref","status","publicScore","description")},sort_keys=True),flush=True)
        return False
    api=KaggleApi()
    api.authenticate()
    limits=api.competition_get_submission_limits(COMPETITION)
    active=[r.get("ref") for r in rows if str(r.get("status") or "").upper().split(".")[-1]
            in ("PENDING","RUNNING","QUEUED","SCORING","EVALUATING")]
    print("GEMMA_LORA_ONE_SHOT_SLOT="+json.dumps({
        "allowed_now":int(limits.num_allowed_now),
        "num_today":int(limits.num_today),
        "limited_by_total":bool(limits.limited_by_total),
        "active":active,
    },sort_keys=True),flush=True)
    if int(limits.num_allowed_now)<1 or limits.limited_by_total or active:
        raise RuntimeError("NO_VERIFIED_EXCLUSIVE_KAGGLE_SUBMISSION_SLOT")
    return True

def verify_provenance_and_candidate():
    with tempfile.TemporaryDirectory(prefix="gemma31-lora-once-") as root:
        source=Path(root)/"source"; source.mkdir()
        command(["kaggle","kernels","pull",SOURCE,"-p",str(source),"-m"],timeout=100)
        mfile=source/"kernel-metadata.json"
        if not mfile.is_file():
            raise RuntimeError("NO_ORIGINAL_PUBLIC_NOTEBOOK_METADATA")
        meta=json.loads(mfile.read_text())
        if meta.get("is_private") is not False or COMPETITION not in meta.get("competition_sources",[]):
            raise RuntimeError("ORIGINAL_LORA_NOT_PUBLIC_IN_THIS_COMPETITION")
        print("GEMMA_LORA_ORIGIN_PUBLIC_CONTEST_NOTEBOOK=TRUE",flush=True)
        print("GEMMA_LORA_ADAPTER_WEIGHT_LICENSE_SEPARATELY_DOCUMENTED=FALSE",flush=True)
        print("GEMMA_LORA_PUBLIC_CODE_LICENSE_BASIS=KAGGLE_COMPETITION_PUBLIC_SHARING_RULE",flush=True)
        status=command(["kaggle","kernels","status",KERNEL],timeout=75)
        if "KernelWorkerStatus.COMPLETE" not in status:
            raise RuntimeError("PRIVATE_CPU_BUILDER_NOT_COMPLETE")
        dest=Path(root)/"output";dest.mkdir()
        command(["kaggle","kernels","output",KERNEL+"/1","-p",str(dest),"-o"],timeout=170)
        file=dest/"submission.zip"
        if not file.is_file():
            raise RuntimeError("PRIVATE_CPU_VERSION_1_ZIP_MISSING")
        blob=file.read_bytes()
        digest=hashlib.sha256(blob).hexdigest()
        if digest!=EXPECTED:
            raise RuntimeError("PRIVATE_CPU_ZIP_HASH_DRIFT:"+digest)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            if z.testzip() or set(z.namelist())!=EXPECTED_FILES:
                raise RuntimeError("CANDIDATE_ZIP_MEMBER_CONTRACT_FAILURE")
            agent=z.read("agent.yaml").decode("utf-8")
            if (agent.count("model: "+MODEL)!=1 or
                agent.count("adapter: main_lora")!=1):
                raise RuntimeError("CANDIDATE_AGENT_MODEL_OR_LORA_ROUTE_DRIFT")
            eval_cfg=z.read("eval_config.yaml").decode()
            for line in ("max_time_minutes: 5","max_tool_calls: 60","max_turns: 80"):
                if line not in eval_cfg:raise RuntimeError("CANDIDATE_BUDGET_DRIFT:"+line)
            if "thinking_budget: 4096" not in z.read("configs/sampling.yaml").decode():
                raise RuntimeError("CANDIDATE_SAMPLING_DRIFT")
        print("GEMMA_LORA_CANDIDATE_EXACT_SHA256="+digest,flush=True)
        print("GEMMA_LORA_PINNED_CONTROL_SHA256="+SCORED_BASE_SHA,flush=True)
        print("GEMMA_LORA_PRIVATE_BUILDER_VERSION=1",flush=True)
        print("GEMMA_LORA_NO_MODEL_INFERENCE_DURING_PREFLIGHT=TRUE",flush=True)
    return True

def submit():
    if not gate():return
    verify_provenance_and_candidate()
    if not gate():return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    print("GEMMA_LORA_ONE_AUTHENTICATED_OFFICIAL_SUBMISSION_STARTED=TRUE",flush=True)
    try:
        res=api.competition_submit_code(
            file_name="submission.zip",message=MARKER,
            competition=COMPETITION,kernel=KERNEL,kernel_version=1,quiet=True)
        print("GEMMA_LORA_SUBMIT_API_RESPONSE="+json.dumps(
            res.to_dict() if hasattr(res,"to_dict") else str(res),default=str),flush=True)
    except Exception as e:
        print("GEMMA_LORA_SUBMIT_API_ERROR_TYPE="+type(e).__name__,flush=True)
    for _ in range(16):
        rec=existing(ledger())
        if rec:
            print("GEMMA_LORA_OFFICIAL_LEDGER_RECEIPT="+json.dumps({
                k:rec.get(k) for k in ("ref","status","publicScore","description","date")},
                sort_keys=True),flush=True)
            print("GEMMA_LORA_NEW_PUBLIC_SCORE_NOT_CLAIMED_UNTIL_COMPLETE=TRUE",flush=True)
            return
        time.sleep(7)
    raise RuntimeError("OFFICIAL_LEDGER_NO_RECEIPT_DO_NOT_RESUBMIT")

if __name__=="__main__":
    submit()
