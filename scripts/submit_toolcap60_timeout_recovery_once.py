"""Submit exactly one 5-minute Toolcap60 rescue via verified private CPU ZIP builder.

Source: pinned Apache-2.0 external V2 archive. No inference or training is
performed until the competition scoring service runs the accepted submission.
Do not claim this fixes Kaggle 12-hour limits or improves patch correctness.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from scripts.build_toolcap60_timeout_recovery import build, files_for_candidate
from scripts.build_v2_toolcap_submission import files_for_candidate as from_v2
from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION, SOURCE, MODEL, cmd, authenticated_submissions,
    compile_without_inference,
)

KERNEL = "kolihhan/gemma4-toolcap60-safetime5-v1-20261110"
MARKER = "toolcap60-safetime5-v1-20261110"
ROOT = Path("/tmp/gemma4-toolcap60-safetime5-submit")
EXPECTED_PREVIOUS_SUBMISSION = "58164176"


def matching_receipt(rows: list[dict]) -> dict | None:
    matches = [r for r in rows if r.get("description") == MARKER]
    if len(matches) > 1:
        raise RuntimeError("DUPLICATE_SAFETIME5_MARKER")
    if not matches:
        return None
    return {k:matches[0].get(k) for k in (
        "ref", "status", "date", "publicScore", "privateScore", "description")}


def check_slot() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    records = authenticated_submissions()
    existing = matching_receipt(records)
    if existing is not None:
        print("SAFETIME5_EXISTING_AUTHENTICATED_RECEIPT="+
              json.dumps(existing, sort_keys=True), flush=True)
        return False
    source_record = [r for r in records if r.get("ref") ==
                     EXPECTED_PREVIOUS_SUBMISSION]
    if len(source_record) != 1:
        raise RuntimeError("PREVIOUS_TOOLCAP60_SUBMISSION_MISSING")
    source = source_record[0]
    print("SAFETIME5_PREVIOUS_SUBMISSION="+json.dumps({
        "ref":source.get("ref"),"status":source.get("status"),
        "publicScore":source.get("publicScore"),
        "description":source.get("description")
    },sort_keys=True),flush=True)
    api=KaggleApi()
    api.authenticate()
    quota=api.competition_get_submission_limits(COMPETITION)
    active=[r.get("ref") for r in records
            if (r.get("status") or "").upper().split(".")[-1]
               in {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    print("SAFETIME5_SLOT="+json.dumps({
        "allowed_now":quota.num_allowed_now,
        "limited_by_total":quota.limited_by_total,
        "active":active
    },sort_keys=True),flush=True)
    if quota.num_allowed_now<1 or quota.limited_by_total or active:
        raise RuntimeError("NO_SAFE_OFFICIAL_SUBMISSION_SLOT")
    return True


def preflight() -> None:
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("PREFLIGHT_DESTINATION_ALREADY_EXISTS")
    input_dir=ROOT/"source"
    input_dir.mkdir(parents=True)
    subprocess.run(["kaggle","kernels","output",SOURCE,"-p",str(input_dir),"-o"],
                   stdout=subprocess.DEVNULL,check=True,timeout=180)
    source=(input_dir/"submission.zip").read_bytes()
    baseline60=from_v2(source)
    corrected=files_for_candidate(source)
    if set(baseline60)!=set(corrected):
        raise RuntimeError("SOURCE_MEMBER_DRIFT")
    for filename in baseline60:
        expected=(baseline60[filename].replace("max_time_minutes: 8",
                   "max_time_minutes: 5",1)
                  if filename=="eval_config.yaml" else baseline60[filename])
        if corrected[filename]!=expected:
            raise RuntimeError("UNEXPECTED_SOURCE_DIFF:"+filename)
    raw=build(source)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError("BAD_SAFETIME5_ZIP_CRC")
        if set(z.namelist())!=set(corrected):
            raise ValueError("BAD_SAFETIME5_MEMBERS")
        for filename in corrected:
            if z.read(filename).decode()!=corrected[filename]:
                raise ValueError("BAD_SAFETIME5_MEMBER_BYTES")
    # Official compiler validates allowed tool registry, model and budget.
    compile_without_inference(raw)
    sha=hashlib.sha256(raw).hexdigest()
    (ROOT/"submission.zip").write_bytes(raw)
    (ROOT/"candidate.sha256").write_text(sha)
    print("SAFETIME5_OFFICIAL_CPU_ARCHIVE_SHA256="+sha,flush=True)

    import nbformat
    content64=base64.b64encode(raw).decode("ascii")
    source_code=(
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"raw=base64.b64decode({content64!r},validate=True)\n"
        f"digest={sha!r}\n"
        "assert hashlib.sha256(raw).hexdigest()==digest\n"
        "Path('/kaggle/working/submission.zip').write_bytes(raw)\n"
        "print('SAFETIME5_REMOTE_BUILDER_SHA256='+digest)\n"
    )
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# 31B Toolcap60 5-minute timeout recovery — CPU-only builder\n\n"
            "Original V2 source: lynnsakurai, Apache-2.0. "
            "Per-task maximum time 8→5 min, all other Toolcap60 "
            "archive members byte-identical."
        ),
        nbformat.v4.new_code_cell(source_code),
    ])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python",
                               "name":"python3"}
    nbformat.validate(nb)
    kernel_dir=ROOT/"kernel"
    kernel_dir.mkdir()
    (kernel_dir/"safetime5.ipynb").write_text(nbformat.writes(nb))
    (kernel_dir/"kernel-metadata.json").write_text(
        json.dumps({
            "id":KERNEL,"title":"gemma4-toolcap60-safetime5-v1-20261110",
            "code_file":"safetime5.ipynb","language":"python",
            "kernel_type":"notebook","is_private":True,
            "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
            "competition_sources":[COMPETITION],"dataset_sources":[],
            "kernel_sources":[],"model_sources":[],
        },sort_keys=True,indent=2)+"\n"
    )
    print("SAFETIME5_CPU_BUILDER_READY="+KERNEL,flush=True)


def submit() -> None:
    sha=(ROOT/"candidate.sha256").read_text().strip()
    local=(ROOT/"submission.zip").read_bytes()
    if hashlib.sha256(local).hexdigest()!=sha:
        raise RuntimeError("SOURCE_ARCHIVE_MODIFIED")
    if not check_slot():
        return
    cmd(["kaggle","kernels","push","-p",str(ROOT/"kernel"),"-t","600"],
        timeout=240)
    for _ in range(60):
        raw=cmd(["kaggle","kernels","status",KERNEL],timeout=60)
        if "KernelWorkerStatus.COMPLETE" in raw:
            break
        if any(item in raw for item in
               ("KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED",
                "KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("PRIVATE_CPU_BUILDER_FAILED")
        time.sleep(10)
    else:
        raise RuntimeError("PRIVATE_CPU_BUILDER_NOT_COMPLETED")
    remote_dir=ROOT/"remote"
    remote_dir.mkdir()
    subprocess.run(["kaggle","kernels","output",KERNEL+"/1",
                    "-p",str(remote_dir),"-o"],stdout=subprocess.DEVNULL,
                   check=True,timeout=180)
    remote=(remote_dir/"submission.zip").read_bytes()
    if remote!=local:
        raise RuntimeError("KAGGLE_CPU_ARCHIVE_NOT_BYTE_IDENTICAL")
    print("SAFETIME5_REMOTE_ARCHIVE_VERIFIED="+sha,flush=True)
    if not check_slot():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    print("SAFETIME5_OFFICIAL_SUBMIT_STARTED",flush=True)
    try:
        result=api.competition_submit_code(
            file_name="submission.zip",message=MARKER,
            competition=COMPETITION,kernel=KERNEL,kernel_version=1,quiet=True
        )
        print("SAFETIME5_SUBMIT_API_RESPONSE="+json.dumps(
            result.to_dict() if hasattr(result,"to_dict") else str(result),
            default=str,sort_keys=True),flush=True)
    except Exception as err:
        print("SAFETIME5_SUBMIT_CLIENT_EXCEPTION="+type(err).__name__,
              flush=True)
    for _ in range(15):
        r=matching_receipt(authenticated_submissions())
        if r:
            print("SAFETIME5_AUTHENTICATED_RECEIPT="+json.dumps(r,sort_keys=True),
                  flush=True)
            return
        time.sleep(10)
    raise RuntimeError("OFFICIAL_RECEIPT_UNCONFIRMED_DONT_RETRY")


if __name__=="__main__":
    modes={"quota":check_slot,"preflight":preflight,"submit":submit}
    if len(sys.argv)!=2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_toolcap60_timeout_recovery_once quota|preflight|submit")
    modes[sys.argv[1]]()
