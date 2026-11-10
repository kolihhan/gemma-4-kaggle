"""Idempotent, MANUAL, one-shot Kaggle V4-CGR exploratory code submission.

Requires official quota and a CPU-verified, byte-locked candidate. This is
NOT a claim of 31B improvement; its real 31B model work occurs only when
Kaggle scores the accepted submission. Never execute on a schedule.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from scripts.build_solver_v4_cgr_candidate import build, payload
from scripts.prepare_public_budgetfit_v2 import validate_source_zip
from scripts.probe_solver_v4_cgr_official_executor import probe
from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION, SOURCE, MODEL, authenticated_submissions, cmd,
)

KERNEL = "kolihhan/gemma4-solver-v4-cgr-one-shot-20261110"
MARKER = "solver-v4-cgr-one-shot-20261110"
EXPECTED_SHA = "5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be"
ROOT = Path("/tmp/gemma4-solver-v4-cgr-official")


def receipt(rows: list[dict]) -> dict | None:
    hits = [x for x in rows if x.get("description") == MARKER]
    if len(hits) > 1:
        raise RuntimeError("DUPLICATE_V4_OFFICIAL_MARKER_MANUAL_REVIEW")
    if hits:
        return {k: hits[0].get(k) for k in
                ("ref", "status", "date", "publicScore",
                 "privateScore", "description")}
    return None


def check_slot() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows = authenticated_submissions()
    previous = receipt(rows)
    if previous:
        print("V4_CGR_ALREADY_SUBMITTED="+json.dumps(previous,sort_keys=True),flush=True)
        return False
    api = KaggleApi()
    api.authenticate()
    limits = api.competition_get_submission_limits(COMPETITION)
    active = [x.get("ref") for x in rows
              if (x.get("status") or "").upper().split(".")[-1] in
              ("PENDING", "RUNNING", "QUEUED", "SCORING", "EVALUATING")]
    print("V4_CGR_OFFICIAL_SLOT="+json.dumps({
        "allowed_now":limits.num_allowed_now,
        "limited_by_total":limits.limited_by_total,
        "active":active},sort_keys=True),flush=True)
    if limits.num_allowed_now < 1 or limits.limited_by_total or active:
        raise RuntimeError("V4_OFFICIAL_QUOTA_OR_ACTIVE_SUBMISSION_BLOCK")
    return True


def preflight() -> None:
    from scripts.probe_solver_v4_cgr_official_executor import probe
    import asyncio
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("PREFLIGHT_OUTPUT_ALREADY_EXISTS")
    origin=ROOT/"source"
    origin.mkdir(parents=True)
    subprocess.run(["kaggle","kernels","output",SOURCE,
                    "-p",str(origin),"-o"],stdout=subprocess.DEVNULL,
                   check=True,timeout=180)
    source=(origin/"submission.zip").read_bytes()
    original=validate_source_zip(source)
    built=build(source)
    digest=hashlib.sha256(built).hexdigest()
    if digest!=EXPECTED_SHA:
        raise RuntimeError("FROZEN_V4_SHA_DRIFT:"+digest)
    files=payload(source)
    if set(files)!=set(original)|{"skills/repair-witness/SKILL.md",
          "skills/repair-witness/scripts/witness.py",
          "skills/repair-witness/scripts/counterexample.py"}:
        raise RuntimeError("UNEXPECTED_V4_PACKAGED_FILES")
    with zipfile.ZipFile(io.BytesIO(built)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(files):
            raise ValueError("V4_ZIP_CORRUPT")
        for key, value in files.items():
            if z.read(key).decode()!=value:
                raise ValueError("V4_MEMBER_CHANGED:"+key)
    # Execute the exact user-relevant mechanism on the official injected
    # swegemma CodeExecutor; the scripted test never runs Gemma itself.
    asyncio.run(probe(built))
    (ROOT/"submission.zip").write_bytes(built)
    (ROOT/"candidate.sha256").write_text(digest)
    print("V4_CGR_OFFICIAL_CPU_PREFLIGHT_PASS="+digest,flush=True)

    import nbformat
    b64=base64.b64encode(built).decode("ascii")
    cell=(
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"data=base64.b64decode({b64!r},validate=True)\n"
        f"expected={digest!r}\n"
        "assert hashlib.sha256(data).hexdigest()==expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(data)\n"
        "print('V4_CGR_PRIVATE_CPU_REMOTE_ZIP_SHA='+expected)\n"
    )
    notebook=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# Solver V4-CGR exploratory code submission builder\n\n"
            "Counterexample-guided repair research candidate, no fine-tuning. "
            "Built from attributed Apache-2.0 Budget-Fit V2 control. "
            "This CPU Notebook does not execute model inference or grading."
        ),
        nbformat.v4.new_code_cell(cell)
    ])
    notebook.metadata["kernelspec"]={
        "display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(notebook)
    kernel=ROOT/"kernel"
    kernel.mkdir()
    (kernel/"solver-v4-cgr.ipynb").write_text(nbformat.writes(notebook))
    (kernel/"kernel-metadata.json").write_text(json.dumps({
        "id":KERNEL,"title":KERNEL.split("/")[-1],
        "code_file":"solver-v4-cgr.ipynb",
        "language":"python","kernel_type":"notebook",
        "is_private":True,"enable_gpu":False,"enable_tpu":False,
        "enable_internet":False,"competition_sources":[COMPETITION],
        "dataset_sources":[],"kernel_sources":[],"model_sources":[]
    },sort_keys=True,indent=2)+"\n")
    print("V4_CGR_PRIVATE_CPU_BUILDER_READY="+KERNEL,flush=True)


def verified_kernel_version(response) -> int:
    """Pin the saved kernel version using the official Kaggle SDK response.

    Kaggle's response schema documents version_number, while CLI 2.2.5
    reads versionNumber from its SDK object. Fail closed on disagreement.
    """
    from urllib.parse import urlsplit

    if response is None or getattr(response, "error", None):
        raise RuntimeError("KAGGLE_PUSH_VERSION_UNCONFIRMED")
    versions = [
        value for value in (
            getattr(response, "version_number", None),
            getattr(response, "versionNumber", None),
        ) if value is not None
    ]
    if (not versions or any(type(x) is not int or x < 1 for x in versions)
            or any(x != versions[0] for x in versions)):
        raise RuntimeError("KAGGLE_PUSH_VERSION_UNCONFIRMED")
    reference = getattr(response, "ref", None)
    url = getattr(response, "url", None)
    if reference is not None and reference != KERNEL:
        raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    if url is not None:
        parsed = urlsplit(url)
        expected = "/code/" + KERNEL
        if (parsed.scheme != "https" or parsed.netloc not in
                ("www.kaggle.com", "kaggle.com") or
                parsed.path.rstrip("/") != expected):
            raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    if reference is None and url is None:
        raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    return versions[0]



def submit() -> None:
    local=(ROOT/"submission.zip").read_bytes()
    digest=(ROOT/"candidate.sha256").read_text().strip()
    if digest!=EXPECTED_SHA or hashlib.sha256(local).hexdigest()!=digest:
        raise RuntimeError("FROZEN_CANDIDATE_BYTES_MODIFIED")
    if not check_slot():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    pushed=api.kernels_push(str(ROOT/"kernel"), timeout="600")
    version=verified_kernel_version(pushed)
    pinned_kernel=f"{KERNEL}/{version}"
    print("V4_CGR_PRIVATE_CPU_PUSH_VERIFIED="+pinned_kernel,flush=True)
    for _ in range(60):
        status=cmd(["kaggle","kernels","status",pinned_kernel],timeout=60)
        if "KernelWorkerStatus.COMPLETE" in status:
            break
        if any(x in status for x in ("KernelWorkerStatus.ERROR",
           "KernelWorkerStatus.FAILED","KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("V4_CPU_BUILDER_TERMINAL_FAILURE")
        time.sleep(10)
    else:
        raise RuntimeError("V4_CPU_BUILDER_TIMEOUT")
    remote=ROOT/"remote"
    remote.mkdir()
    subprocess.run(["kaggle","kernels","output",pinned_kernel,
                    "-p",str(remote),"-o"],check=True,
                   stdout=subprocess.DEVNULL,timeout=180)
    if (remote/"submission.zip").read_bytes()!=local:
        raise RuntimeError("REMOTE_CPU_ARCHIVE_BYTES_CHANGED")
    print("V4_CGR_EXACT_REMOTE_ZIP_VERIFIED="+digest,flush=True)
    if not check_slot():
        return
    print("V4_CGR_OFFICIAL_SUBMIT_CALL_STARTED="+pinned_kernel,flush=True)
    try:
        response=api.competition_submit_code(
            file_name="submission.zip",message=MARKER,competition=COMPETITION,
            kernel=KERNEL,kernel_version=version,quiet=True)
        print("V4_CGR_SUBMIT_API_RESPONSE="+json.dumps(
            response.to_dict() if hasattr(response,"to_dict") else str(response),
            default=str,sort_keys=True),flush=True)
    except Exception as exc:
        print("V4_CGR_SUBMIT_CLIENT_EXCEPTION="+type(exc).__name__,flush=True)
    for _ in range(15):
        existing=receipt(authenticated_submissions())
        if existing:
            print("V4_CGR_AUTHENTICATED_OFFICIAL_RECEIPT="+json.dumps(
                existing,sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("V4_CGR_RECEIPT_UNCONFIRMED_DO_NOT_RETRY")


if __name__=="__main__":
    modes={"quota":check_slot,"preflight":preflight,"submit":submit}
    if len(sys.argv)!=2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_solver_v4_cgr_once quota|preflight|submit")
    modes[sys.argv[1]]()
