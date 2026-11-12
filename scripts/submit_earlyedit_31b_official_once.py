"""Submit one exact tested 31B Early-Edit candidate through a private Kaggle CPU builder.

No training, no new model GPU, no raw issue data, no optimistic score claims.
The predeclared 5-minute policy is identical to the completed real 3/4 pilot.
"""
from __future__ import annotations
import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from scripts.build_public_prompt_only_control_20261111 import make_zip
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256
from scripts.render_earlyedit_v2_paired_31b import (
    ROOT, PLAN_FILE, POLICY, candidate_files, validate_plan,
)

COMPETITION = "gemma-4-developer-agent"
SOURCE_REF = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
DESCRIPTION = "31B EarlyEdit feedback 5min 28calls frozen 3of4 private pilot 20261112"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check_source_and_candidate(original: bytes, repo: Path = ROOT) -> tuple[bytes, dict]:
    plan = json.loads((repo / PLAN_FILE).read_text(encoding="utf-8"))
    validate_plan(plan)
    if sha(original) != EXPECTED_ZIP_SHA256:
        raise ValueError("exact public V2 source ZIP hash mismatch")
    control, treatment = candidate_files(original)
    changed = [k for k in control if control[k] != treatment[k]]
    if changed != ["prompts/system.md"]:
        raise ValueError("untested modification beyond system prompt")
    if treatment["prompts/system.md"].count(POLICY) != 1:
        raise ValueError("candidate does not contain exactly one policy")
    if "max_time_minutes: 5" not in treatment["eval_config.yaml"]:
        raise ValueError("candidate clock mismatch")
    if "max_tool_calls: 28" not in treatment["eval_config.yaml"]:
        raise ValueError("candidate tool cap mismatch")
    if "max_turns: 80" not in treatment["eval_config.yaml"]:
        raise ValueError("candidate turn cap mismatch")
    if f"model: {MODEL}" not in treatment["agent.yaml"]:
        raise ValueError("candidate must use same 31B model")
    data = make_zip(treatment)
    import zipfile
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() or set(z.namelist()) != set(treatment):
            raise ValueError("candidate archive corrupted")
    report = {
        "source_sha256":sha(original),
        "candidate_sha256":sha(data),
        "model":MODEL,
        "policy_sha256":sha(POLICY.encode()),
        "frozen_pilot_run":43178431152,
        "pilot_resolved":3,
        "pilot_denominator":4,
        "pilot_baseline_resolved":3,
        "new_training":False,
        "new_gpu":False,
        "candidate_diff_is_prompt_only":True,
    }
    return data,report


def render_builder(output: Path, kernel_ref: str, data: bytes) -> None:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{20,100}",kernel_ref):
        raise ValueError("kernel reference invalid")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("builder directory already exists")
    output.mkdir(parents=True, exist_ok=True)
    blob = base64.b64encode(data).decode()
    source = (
      "import base64, hashlib\n"
      "from pathlib import Path\n"
      f"BLOB={blob!r}\n"
      f"SHA={sha(data)!r}\n"
      "raw=base64.b64decode(BLOB)\n"
      "assert hashlib.sha256(raw).hexdigest()==SHA\n"
      "Path('/kaggle/working/submission.zip').write_bytes(raw)\n"
      "print('GEMMA_EARLYEDIT_REMOTE_ZIP_SHA='+SHA)\n"
    )
    compile(source,"builder.py","exec")
    (output / "builder.py").write_text(source)
    metadata={
        "id":kernel_ref,
        "title":kernel_ref.split("/",1)[1],
        "code_file":"builder.py",
        "language":"python","kernel_type":"script",
        "is_private":True,
        "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
        "competition_sources":[COMPETITION],
        "dataset_sources":[],"kernel_sources":[],"model_sources":[],
    }
    (output / "kernel-metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")


def kaggle(cmd: list[str], *, timeout: int=120) -> subprocess.CompletedProcess:
    return subprocess.run(["kaggle",*cmd],check=True,text=True,capture_output=True,timeout=timeout)


def official_quota_and_duplicate() -> None:
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    quota=api.competition_get_submission_limits(COMPETITION)
    if not isinstance(quota.num_allowed_now,int) or quota.num_allowed_now < 1:
        raise RuntimeError("NO_OFFICIAL_GEMMA_SUBMISSION_SLOT")
    rows=list(csv.DictReader(io.StringIO(kaggle(
        ["competitions","submissions",COMPETITION,"-v","-q"]).stdout)))
    matches=[x for x in rows if DESCRIPTION in (x.get("description") or "")]
    if matches:
        raise RuntimeError("EXACT_GEMMA_EARLYEDIT_ALREADY_SUBMITTED_NO_RETRY")
    active=[x for x in rows if (x.get("status") or "").upper().split(".")[-1] in
            ("PENDING","QUEUED","RUNNING","SCORING","EVALUATING")]
    if active:
        raise RuntimeError("ANOTHER_GEMMA_SCORING_ACTIVE")
    print("GEMMA_EARLYEDIT_OFFICIAL_QUOTA="+json.dumps({
        "allowed_now":quota.num_allowed_now,"active":len(active),
        "candidate_already_exists":len(matches)>0},sort_keys=True),flush=True)


def check_kernel_absent(kernel_ref: str) -> None:
    result=subprocess.run(["kaggle","kernels","status",kernel_ref],
        capture_output=True,text=True,timeout=80)
    if result.returncode == 0:
        raise RuntimeError("REMOTE_KERNEL_ALREADY_EXISTS_REFUSE_DUPLICATION")


def poll_complete(kernel_ref: str) -> None:
    for attempt in range(150):
        p=subprocess.run(["kaggle","kernels","status",kernel_ref],
                         capture_output=True,text=True,timeout=90)
        line=(p.stdout+" "+p.stderr).upper()
        if "COMPLETE" in line:
            return
        if any(x in line for x in ("ERROR","FAIL","CANCEL")):
            raise RuntimeError("PRIVATE_CPU_BUILDER_TERMINAL_ERROR")
        if attempt%12==0:
            print("GEMMA_PRIVATE_CPU_BUILDER_POLL="+str(attempt+1),flush=True)
        time.sleep(8)
    raise TimeoutError("PRIVATE_CPU_BUILDER_NOT_COMPLETE_NO_RETRY")


def execute(source: Path, out: Path, kernel_ref: str) -> None:
    official_quota_and_duplicate()
    check_kernel_absent(kernel_ref)
    data,report=check_source_and_candidate(source.read_bytes())
    print("GEMMA_EARLYEDIT_FROZEN_CANDIDATE="+json.dumps(report,sort_keys=True),flush=True)
    render_builder(out/"builder",kernel_ref,data)
    p=subprocess.run(["kaggle","kernels","push","-p",str(out/"builder"),"-t","3600"],
                     capture_output=True,text=True,timeout=140)
    if p.returncode:
        raise RuntimeError("KAGGLE_PRIVATE_CPU_BUILDER_PUSH_FAILED")
    print("GEMMA_PRIVATE_CPU_BUILDER_PUSH_ACCEPTED=TRUE",flush=True)
    poll_complete(kernel_ref)
    downloaded=out/"remote"
    downloaded.mkdir(parents=True,exist_ok=True)
    kaggle(["kernels","output",kernel_ref,"-p",str(downloaded),"-o"],timeout=130)
    remote=(downloaded/"submission.zip").read_bytes()
    if remote != data or sha(remote) != report["candidate_sha256"]:
        raise RuntimeError("PRIVATE_REMOTE_CANDIDATE_DIFFERS_FROM_TESTED_SOURCE")
    print("GEMMA_PRIVATE_REMOTE_ZIP_BYTES_MATCH=TRUE",flush=True)
    official_quota_and_duplicate()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    result=api.competition_submit_code(
      file_name="submission.zip",message=DESCRIPTION,
      competition=COMPETITION,kernel=kernel_ref,kernel_version=1,quiet=False,
    )
    reply=result.to_dict() if hasattr(result,"to_dict") else repr(result)
    print("GEMMA_OFFICIAL_CODE_SUBMISSION_RESPONSE="+json.dumps(reply,sort_keys=True,default=str),flush=True)
    entry_ref=str(reply.get("ref") if isinstance(reply,dict) else "")
    if not entry_ref.isdigit():
        raise RuntimeError("SUBMISSION_SENT_BUT_NO_NUMERIC_RECEIPT_DO_NOT_AUTO_RETRY")
    receipt={"ref":entry_ref,"message":DESCRIPTION,
        "kernel":kernel_ref,"candidate_sha256":report["candidate_sha256"],
        "utc":datetime.now(timezone.utc).isoformat(),
        "status":"accepted_for_scoring","not_yet_a_score":True}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GEMMA_ACTUAL_OFFICIAL_RECEIPT="+json.dumps(receipt,sort_keys=True),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["preflight","submit"])
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kernel-ref",type=str,required=True)
    a=p.parse_args()
    if a.mode=="preflight":
        data,report=check_source_and_candidate(a.source_zip.read_bytes())
        render_builder(a.out/"builder",a.kernel_ref,data)
        print("GEMMA_EARLYEDIT_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)
    else:
        execute(a.source_zip,a.out,a.kernel_ref)


if __name__=="__main__":
    main()
