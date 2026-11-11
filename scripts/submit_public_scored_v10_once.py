"""Verified public 0.22 Gemma 4 V10: one authorized Kaggle entry, no training.

This is an ATTRIBUTED public, exact-byte scored source control, NOT original
work, not guaranteed 0.22 on re-scoring, not an improvement from our V2.
The only user-owned competition submission action happens in submit() after
an authenticated available slot, official compiler preflight, exact remote
private kernel output verification, and duplicate marker protection.

Public source: flexonafft/gemma-4-budget-aware-coding-agent-v2/10
Verified original Public: 0.22, with observed exact-config rerun 0.12–0.22.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile
from urllib.parse import urlsplit

from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION, authenticated_submissions, cmd,
)

KERNEL = "kolihhan/gemma4-attributed-scored-v10-one-shot-20261112"
MARKER = "attributed-scored-v10-exact-one-shot-20261112"
PUBLIC_SOURCE = "flexonafft/gemma-4-budget-aware-coding-agent-v2/10"
PUBLIC_URL = "https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2?scriptVersionId=357955943"
EXPECTED_SHA = "6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887"
EXPECTED_FILES_SHA = "56010e9e9d4c7f33856ce49d12ec3edae5c912261986e999a4aa989b3cd463cb"
EXPECTED_MEMBERS = {
    "agent.yaml": "680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4",
    "configs/sampling.yaml": "571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926",
    "eval_config.yaml": "916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531",
    "prompts/system.md": "7f8dde62578a247ffbfc1a519b712ae65849fcfae1ee70c49e0628cab74cbef6",
}
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
ROOT = Path("/tmp/gemma4-attributed-scored-v10-official")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def verify_source(blob: bytes) -> dict[str, str]:
    if digest(blob) != EXPECTED_SHA:
        raise RuntimeError("SCORED_PUBLIC_V10_SOURCE_ZIP_HASH_DRIFT")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if z.testzip() is not None or len(names)!=len(set(names)) or set(names)!=set(EXPECTED_MEMBERS):
            raise RuntimeError("SCORED_PUBLIC_V10_ARCHIVE_MEMBERS_CHANGED")
        files={}
        for name in sorted(EXPECTED_MEMBERS):
            raw=z.read(name)
            if digest(raw)!=EXPECTED_MEMBERS[name]:
                raise RuntimeError("SCORED_PUBLIC_V10_MEMBER_SHA_DRIFT:"+name)
            files[name]=raw.decode("utf-8")
    if digest(json.dumps(files,sort_keys=True).encode())!=EXPECTED_FILES_SHA:
        raise RuntimeError("SCORED_PUBLIC_V10_SCORED_VERSION_BUNDLE_HASH_CHANGED")
    if files["agent.yaml"].count("model: "+MODEL)!=1:
        raise RuntimeError("UNSUPPORTED_MODEL_OR_MULTIPLE_MODELS")
    cfg=files["eval_config.yaml"]
    if any(cfg.count(s)!=1 for s in
           ("max_time_minutes: 8","max_tool_calls: 28","max_turns: 80")):
        raise RuntimeError("PUBLIC_V10_BUDGET_CONFIG_DRIFT")
    if "thinking_budget: 4096" not in files["configs/sampling.yaml"]:
        raise RuntimeError("PUBLIC_V10_SAMPLING_DRIFT")
    if not files["prompts/system.md"].strip():
        raise RuntimeError("PUBLIC_V10_EMPTY_PROMPT")
    return files


def matching_receipt(rows: list[dict]) -> dict | None:
    hits=[x for x in rows if x.get("description")==MARKER]
    if len(hits)>1:
        raise RuntimeError("DUPLICATE_PUBLIC_V10_OFFICIAL_RECEIPT")
    if not hits:return None
    return {k:hits[0].get(k) for k in
            ("ref","status","date","publicScore","privateScore","description")}


def check_quota() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows=authenticated_submissions()
    receipt=matching_receipt(rows)
    if receipt:
        print("SCORED_V10_ALREADY_SUBMITTED="+json.dumps(receipt,sort_keys=True),flush=True)
        return False
    api=KaggleApi();api.authenticate()
    limits=api.competition_get_submission_limits(COMPETITION)
    running=[{"ref":r.get("ref"),"status":r.get("status")} for r in rows
             if (r.get("status") or "").upper().split(".")[-1] in
             {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    status={"allowed_now":limits.num_allowed_now,
            "limited_by_total":limits.limited_by_total,
            "active":running}
    print("PUBLIC_V10_OFFICIAL_SUBMIT_SLOT="+json.dumps(status,sort_keys=True),flush=True)
    if limits.num_allowed_now<1 or limits.limited_by_total or running:
        raise RuntimeError("OFFICIAL_SUBMIT_QUOTA_OR_ACTIVE_SUBMISSION_BLOCK")
    return True


def compile_official(source_path: Path) -> None:
    from adk_submission import validate_directory
    from adk_submission.discovery import discover_declared_models
    from swegemma.config import build_submission_limits
    limits,_=build_submission_limits()
    validate_directory(source_path,limits=limits)
    models=discover_declared_models(source_path)
    if models!={MODEL}:
        raise RuntimeError("OFFICIAL_COMPILER_DECLARED_MODEL_MISMATCH")
    print("SCORED_V10_OFFICIAL_WHEELHOUSE_COMPILER_GATE=PASS",flush=True)


def preflight() -> None:
    import nbformat
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("REFUSE_OVERWRITE_SCORED_V10_BUILDER")
    src=ROOT/"source"
    src.mkdir(parents=True)
    subprocess.run(["kaggle","kernels","output",PUBLIC_SOURCE,
                    "-p",str(src),"-o"],
                   stdout=subprocess.DEVNULL,check=True,timeout=240)
    blob=(src/"submission.zip").read_bytes()
    files=verify_source(blob)
    pkg=ROOT/"package"
    pkg.mkdir()
    for name,body in files.items():
        loc=pkg/name
        loc.parent.mkdir(parents=True,exist_ok=True)
        loc.write_text(body,encoding="utf-8")
    compile_official(pkg)
    (ROOT/"submission.zip").write_bytes(blob)
    (ROOT/"candidate.sha256").write_text(EXPECTED_SHA)
    print("PUBLIC_V10_SCORED_ARCHIVE_EXACT_SHA256="+digest(blob),flush=True)
    print("PUBLIC_V10_SCORED_FILEHASH_MATCH="+EXPECTED_FILES_SHA,flush=True)

    b64=base64.b64encode(blob).decode("ascii")
    source_code=(
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"blob=base64.b64decode({b64!r},validate=True)\n"
        f"expected={EXPECTED_SHA!r}\n"
        "assert hashlib.sha256(blob).hexdigest()==expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(blob)\n"
        "print('ATTRIBUTED_PUBLIC_V10_REMOTE_ZIP_SHA='+expected)\n"
    )
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# Exact scored public Gemma 4 V10 repro (attributed)\n\n"
            "Original author: flexonafft. Source: "+PUBLIC_URL+
            "\nPrevious observed Public 0.22; multiple identical-configuration "
            "scorings ranged 0.12–0.22, so no guaranteed score. "
            "This CPU notebook only writes byte-verified submission.zip."),
        nbformat.v4.new_code_cell(source_code)
    ])
    nb.metadata["kernelspec"]={"display_name":"Python 3",
                                "language":"python","name":"python3"}
    nbformat.validate(nb)
    kd=ROOT/"kernel"
    kd.mkdir()
    (kd/"scored-v10.ipynb").write_text(nbformat.writes(nb))
    (kd/"kernel-metadata.json").write_text(json.dumps({
        "id":KERNEL,"title":KERNEL.split("/")[-1],
        "code_file":"scored-v10.ipynb",
        "language":"python","kernel_type":"notebook",
        "is_private":True,"enable_gpu":False,"enable_tpu":False,
        "enable_internet":False,"competition_sources":[COMPETITION],
        "dataset_sources":[],"kernel_sources":[],"model_sources":[]
    },sort_keys=True,indent=2)+"\n")
    print("PUBLIC_V10_ATTRIBUTED_PRIVATE_CPU_BUILDER_READY="+KERNEL,flush=True)


def verified_version(response) -> int:
    if response is None or getattr(response,"error",None):
        raise RuntimeError("KAGGLE_PUSH_VERSION_UNCONFIRMED")
    versions=[v for v in (
        getattr(response,"version_number",None),
        getattr(response,"versionNumber",None)
    ) if v is not None]
    if not versions or any(type(v) is not int or v<1 for v in versions):
        raise RuntimeError("KAGGLE_PUSH_VERSION_UNCONFIRMED")
    if len(set(versions))!=1:
        raise RuntimeError("KAGGLE_PUSH_VERSION_MISMATCH")
    ref=getattr(response,"ref",None)
    uri=getattr(response,"url",None)
    if ref is not None and ref not in {KERNEL,"/code/"+KERNEL}:
        raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    if uri is not None:
        parsed=urlsplit(uri)
        if parsed.scheme!="https" or parsed.netloc not in {"www.kaggle.com","kaggle.com"} or parsed.path.rstrip("/")!="/code/"+KERNEL:
            raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    if ref is None and uri is None:
        raise RuntimeError("KAGGLE_PUSH_IDENTITY_UNCONFIRMED")
    return versions[0]


def submit_once() -> None:
    local=(ROOT/"submission.zip").read_bytes()
    expected=(ROOT/"candidate.sha256").read_text().strip()
    if expected!=EXPECTED_SHA:
        raise RuntimeError("CPU_PREFLIGHT_SHA_DRIFT")
    verify_source(local)
    if not check_quota():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    pushed=api.kernels_push(str(ROOT/"kernel"),timeout="600")
    version=verified_version(pushed)
    pinned=f"{KERNEL}/{version}"
    print("SCORED_V10_KAGGLE_PRIVATE_BUILDER_VERSION="+pinned,flush=True)
    for _ in range(60):
        result=cmd(["kaggle","kernels","status",pinned],timeout=60)
        if "KernelWorkerStatus.COMPLETE" in result:break
        if any(x in result for x in (
                "KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED",
                "KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("PUBLIC_V10_PRIVATE_CPU_BUILDER_FAILED")
        time.sleep(10)
    else:
        raise RuntimeError("PUBLIC_V10_PRIVATE_CPU_BUILDER_TIMEOUT")
    remote=ROOT/"remote"
    remote.mkdir()
    subprocess.run(["kaggle","kernels","output",pinned,"-p",str(remote),"-o"],
                   stdout=subprocess.DEVNULL,check=True,timeout=180)
    got=(remote/"submission.zip").read_bytes()
    if got!=local:
        raise RuntimeError("PUBLIC_V10_REMOTE_ARCHIVE_NOT_BYTE_IDENTICAL")
    print("PUBLIC_V10_REMOTE_ARCHIVE_EXACT_SHA256="+digest(got),flush=True)
    if not check_quota():
        return
    print("PUBLIC_V10_OFFICIAL_ONE_SUBMIT_STARTED="+pinned,flush=True)
    try:
        answer=api.competition_submit_code(
            file_name="submission.zip",message=MARKER,competition=COMPETITION,
            kernel=KERNEL,kernel_version=version,quiet=True)
        print("PUBLIC_V10_OFFICIAL_API_RESPONSE_TYPE="+type(answer).__name__,flush=True)
    except Exception as exc:
        print("PUBLIC_V10_OFFICIAL_API_EXCEPTION_TYPE="+type(exc).__name__,flush=True)
    for _ in range(18):
        receipt=matching_receipt(authenticated_submissions())
        if receipt:
            print("PUBLIC_V10_AUTHENTICATED_COMPETITION_RECEIPT="+json.dumps(receipt,sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("PUBLIC_V10_RECEIPT_UNCONFIRMED_STOP_NO_RETRY")


def main() -> None:
    choices={"quota":check_quota,"preflight":preflight,"submit":submit_once}
    if len(sys.argv)!=2 or sys.argv[1] not in choices:
        raise SystemExit("usage: python -m scripts.submit_public_scored_v10_once quota|preflight|submit")
    choices[sys.argv[1]]()


if __name__=="__main__":
    main()
