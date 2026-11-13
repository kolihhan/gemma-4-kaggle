"""One authorized exploratory Gemma 4 31B fast-thinking CODE submission.

Source is hash-pinned Apache-2.0 Budget-Fit V2 public ZIP. Candidate is
distinct from already-scored 0.18 5min/60calls by exactly one sampling
parameter (thinking_budget 4096 -> 2048). No training or private GPU
in this submission builder. No promise of better hidden transfer.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time

from scripts.build_gemma_fastthink_5min60_v1 import build, files_for_candidate, report
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256
from scripts.submit_earlyedit_31b_official_once import render_builder
from scripts.submit_v2_toolcap60_official_once import compile_without_inference
from kaggle.api.kaggle_api_extended import KaggleApi

CONTEST="gemma-4-developer-agent"
SOURCE="lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
MARKER="31B-fastthink2048-5min60-inference-throughput-v1-20261113"
MODEL="gemma-4-31b-it-qat-w4a16-ct"


def cli(*args: str, timeout: int = 120) -> str:
    return subprocess.run(["kaggle",*args],capture_output=True,text=True,
                          timeout=timeout,check=True).stdout


def ledger() -> list[dict]:
    return list(csv.DictReader(io.StringIO(cli(
        "competitions","submissions",CONTEST,"-v","-q").lstrip("\ufeff"))))


def protect_slot(api: KaggleApi) -> None:
    rows=ledger()
    prior=[r for r in rows if r.get("description")==MARKER]
    if prior:
        print("GEMMA_FASTTHINK_PRIOR_REF="+json.dumps(
            {k:prior[0].get(k) for k in ("ref","status","publicScore")},sort_keys=True),flush=True)
        raise SystemExit("STOP_ALREADY_SUBMITTED_NO_DUPLICATE")
    pending=[r.get("ref") for r in rows if
             (r.get("status") or "").upper().split(".")[-1]
             in ("PENDING","RUNNING","QUEUED","SCORING","EVALUATING")]
    if pending:raise SystemExit("STOP_OTHER_OFFICIAL_ENTRY_STILL_PENDING")
    quota=api.competition_get_submission_limits(CONTEST)
    if int(quota.num_allowed_now or 0)<1:raise SystemExit("STOP_NO_OFFICIAL_SLOT")
    print("GEMMA_FASTTHINK_AUTHENTICATED_ALLOWED_NOW="+str(quota.num_allowed_now),flush=True)


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--kernel",required=True)
    args=ap.parse_args()
    if not re.fullmatch(r"kolihhan/gemma4-fastthink5m60-[a-z0-9-]{10,80}",args.kernel):
        raise ValueError("bad unique private kernel ID")
    out=args.out
    if out.exists() and any(out.iterdir()):raise FileExistsError("nonempty work dir")
    out.mkdir(parents=True,exist_ok=True)
    api=KaggleApi();api.authenticate()
    protect_slot(api)

    origin=out/"origin"
    origin.mkdir()
    cli("kernels","output",SOURCE,"-p",str(origin),"-o",timeout=180)
    base=(origin/"submission.zip").read_bytes()
    if hashlib.sha256(base).hexdigest()!=EXPECTED_ZIP_SHA256:
        raise RuntimeError("STOP_PUBLISHED_SOURCE_SHA_DRIFT")
    candidate=build(base)
    metadata=report(base)
    print("GEMMA_FASTTHINK_CANDIDATE="+json.dumps(metadata,sort_keys=True),flush=True)
    if metadata["changed_files"]!=["configs/sampling.yaml"]:
        raise RuntimeError("not single-variable intervention")
    compile_without_inference(candidate)
    print("GEMMA_FASTTHINK_OFFICIAL_CPU_COMPILE=PASS",flush=True)

    d=out/"builder"
    render_builder(d,args.kernel,candidate)
    src=cli("kernels","status",args.kernel,timeout=65) if False else ""
    p=subprocess.run(["kaggle","kernels","status",args.kernel],capture_output=True,text=True,timeout=90)
    if p.returncode==0 or "KernelWorkerStatus." in p.stdout+p.stderr:
        raise SystemExit("STOP_KERNEL_ID_ALREADY_USED")
    cli("kernels","push","-p",str(d),"-t","600",timeout=180)
    print("GEMMA_FASTTHINK_PRIVATE_CPU_BUILDER_PUSHED=TRUE",flush=True)
    for i in range(90):
        s=cli("kernels","status",args.kernel,timeout=70)
        if "KernelWorkerStatus.COMPLETE" in s:break
        if any(x in s for x in ("KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED",
                                "KernelWorkerStatus.CANCELLED")):
            raise SystemExit("STOP_REMOTE_CPU_BUILDER_FAILED")
        time.sleep(8)
    else:raise SystemExit("STOP_BUILDER_NOT_COMPLETE_NO_RETRY")
    output=out/"remote";output.mkdir()
    cli("kernels","output",args.kernel,"-p",str(output),"-o",timeout=180)
    remote=(output/"submission.zip").read_bytes()
    if remote!=candidate or hashlib.sha256(remote).hexdigest()!=metadata["candidate_sha256"]:
        raise SystemExit("STOP_REMOTE_CANDIDATE_BYTES_DIFFER")
    print("GEMMA_FASTTHINK_REMOTE_ARCHIVE_SHA_MATCH=TRUE",flush=True)
    protect_slot(api)
    r=api.competition_submit_code(
        file_name="submission.zip",message=MARKER,
        competition=CONTEST,kernel=args.kernel,kernel_version=1,quiet=False)
    reply=r.to_dict() if hasattr(r,"to_dict") else {}
    ref=str(reply.get("ref") or "")
    if not ref.isdigit():
        print("GEMMA_FASTTHINK_SUBMISSION_REPLY_WITHOUT_VERIFIED_REF_DO_NOT_RETRY",flush=True)
        raise SystemExit("STOP_AMBIGUOUS_OFFICIAL_RECEIPT")
    print("GEMMA_FASTTHINK_OFFICIAL_SUBMISSION_REF="+ref,flush=True)
    for i in range(20):
        found=[row for row in ledger() if row.get("ref")==ref and row.get("description")==MARKER]
        if len(found)==1:
            print("GEMMA_FASTTHINK_AUTHENTICATED_LEDGER_RECEIPT="+json.dumps(
                {k:found[0].get(k) for k in
                 ("ref","description","status","publicScore","privateScore","date")},
                sort_keys=True),flush=True)
            return
        time.sleep(8)
    raise SystemExit("STOP_RECEIPT_DELAY_NO_RESUBMIT")


if __name__=="__main__":
    main()
