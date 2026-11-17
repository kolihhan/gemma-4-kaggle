"""One hypothesis, one official Gemma scorer run: existing-test evidence before edit.

CPU-only GitHub preflight and Kaggle CPU builder. Only the official Kaggle
competition scoring rerun may invoke a model/GPU. The scored 0.18 control is
SHA-verified; a distinct new kernel slug protects the champion.
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

from scripts.build_gemma31_existing_tests import build
from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION, SOURCE, authenticated_submissions, compile_without_inference,
)
from scripts.prepare_public_budgetfit_v2 import validate_source_zip

KERNEL = "kolihhan/gemma4-existing-tests-score-nov17"
MARKER = "existing-tests-31b-one-variable-20261117"
ROOT = Path("/tmp/gemma4-existing-tests-official-once")
EXPECTED_CONTROL_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
HYPOTHESIS = {
    "mechanism": "retrieve matching local assertions once, before code edit",
    "expected_public_BA_delta": 0.02,
    "baseline": 0.18,
    "kill": "official Public score <=0.18, blank score, runtime error or broken patch completion",
    "validation": "CPU sanity only; old invalid 31-case GPU grader does not count",
}


def run(argv, timeout=150):
    return subprocess.run(argv, text=True, capture_output=True, check=True, timeout=timeout).stdout


def receipt():
    rows = authenticated_submissions()
    found = [r for r in rows if str(r.get("description") or "") == MARKER]
    if len(found) > 1:
        raise RuntimeError("DUPLICATE_MARKER_STOP")
    return found[0] if found else None


def quota():
    from kaggle.api.kaggle_api_extended import KaggleApi
    old = receipt()
    if old:
        print("GEMMA_ALREADY_SUBMITTED=" + json.dumps({x: old.get(x) for x in ("ref", "status", "publicScore")}, sort_keys=True),flush=True)
        return False
    rows = authenticated_submissions()
    api = KaggleApi()
    api.authenticate()
    limits = api.competition_get_submission_limits(COMPETITION)
    active = [r.get("ref") for r in rows if str(r.get("status") or "").upper().split(".")[-1] in
              {"PENDING", "RUNNING", "QUEUED", "SCORING", "EVALUATING"}]
    print("GEMMA_AUTHENTICATED_QUOTA=" + json.dumps({
        "allowed_now": limits.num_allowed_now, "num_today": limits.num_today,
        "limited_by_total": limits.limited_by_total, "active": active
    }, sort_keys=True), flush=True)
    if int(limits.num_allowed_now) < 1:
        raise RuntimeError("GEMMA_DAILY_QUOTA_BLOCKED")
    if limits.limited_by_total or active:
        raise RuntimeError("GEMMA_ACTIVE_OR_TOTAL_QUOTA_BLOCKED")
    return True


def prepare():
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("REFUSE_NONEMPTY_DIR")
    rawdir = ROOT / "source"
    rawdir.mkdir(parents=True)
    subprocess.run(["kaggle", "kernels", "output", SOURCE, "-p", str(rawdir), "-o"],
                   check=True, timeout=200, stdout=subprocess.DEVNULL)
    source = (rawdir / "submission.zip").read_bytes()
    validate_source_zip(source)
    control, candidate = build(source)
    if hashlib.sha256(control).hexdigest() != EXPECTED_CONTROL_SHA:
        raise RuntimeError("SCORED_CONTROL_SHA_DRIFT")
    with zipfile.ZipFile(io.BytesIO(candidate)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("BAD_ARCHIVE_CRC")
        files = {name: archive.read(name) for name in archive.namelist()}
    with zipfile.ZipFile(io.BytesIO(control)) as archive:
        original = {name: archive.read(name) for name in archive.namelist()}
    changed = {k for k in original if files.get(k) != original[k]}
    if changed != {"agent.yaml", "prompts/system.md"}:
        raise RuntimeError("UNEXPECTED_ORIGINAL_DIFF:" + str(changed))
    if any(name not in original and not name.startswith("skills/existing-test-retrieval/") for name in files):
        raise RuntimeError("UNEXPECTED_EXTRA_ARCHIVE_MEMBERS")
    if not any(name.endswith("scripts/retrieve.py") for name in files):
        raise RuntimeError("SKILL_SCRIPT_MISSING")
    if MODEL.encode() not in files["agent.yaml"]:
        raise RuntimeError("MODEL_CHANGED")
    if files["eval_config.yaml"] != original["eval_config.yaml"]:
        raise RuntimeError("BUDGET_CHANGED")
    compile_without_inference(candidate)
    digest = hashlib.sha256(candidate).hexdigest()
    (ROOT / "candidate.zip").write_bytes(candidate)
    (ROOT / "candidate.sha256").write_text(digest)
    (ROOT / "hypothesis.json").write_text(json.dumps(HYPOTHESIS, indent=2))
    import nbformat
    payload = base64.b64encode(candidate).decode("ascii")
    cell = (
        "import base64,hashlib\nfrom pathlib import Path\n" +
        f"payload=base64.b64decode({payload!r},validate=True)\n" +
        f"expected={digest!r}\n" +
        "assert hashlib.sha256(payload).hexdigest()==expected\n" +
        "Path('/kaggle/working/submission.zip').write_bytes(payload)\n" +
        "print('GEMMA_EXISTING_TESTS_CPU_BUILDER_PASS='+expected)\n"
    )
    nb = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell("Existing-test retrieval single hypothesis; attributed Budget-Fit V2 lineage; no model execution in this CPU builder."),
        nbformat.v4.new_code_cell(cell),
    ])
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbformat.validate(nb)
    p = ROOT / "kernel"
    p.mkdir()
    (p / "builder.ipynb").write_text(nbformat.writes(nb))
    metadata = {
        "id": KERNEL, "title": KERNEL.split("/")[-1], "code_file": "builder.ipynb",
        "language": "python", "kernel_type": "notebook",
        "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": False, "competition_sources": [COMPETITION],
        "dataset_sources": [], "model_sources": [], "kernel_sources": []
    }
    (p / "kernel-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2))
    print("GEMMA_EXISTING_TESTS_CPU_SANITY=PASS candidate_sha=" + digest, flush=True)


def submit():
    data = (ROOT / "candidate.zip").read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == (ROOT / "candidate.sha256").read_text()
    if not quota():
        return
    # Must not overwrite an already-created private candidate or retry blindly.
    probe = subprocess.run(["kaggle", "kernels", "status", KERNEL], capture_output=True,text=True,timeout=75)
    if "KernelWorkerStatus." in (probe.stdout + probe.stderr):
        raise RuntimeError("KERNEL_ALREADY_EXISTS_NO_OVERWRITE")
    subprocess.run(["kaggle","kernels","push","-p",str(ROOT/"kernel"),"-t","600"],
                   check=True,timeout=240,stdout=subprocess.DEVNULL)
    for _ in range(60):
        status = run(["kaggle", "kernels", "status", KERNEL], timeout=70)
        if "KernelWorkerStatus.COMPLETE" in status:
            break
        if any(x in status for x in ["KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED","KernelWorkerStatus.CANCELLED"]):
            raise RuntimeError("KAGGLE_CPU_BUILDER_ERROR")
        time.sleep(10)
    else:
        raise RuntimeError("KAGGLE_CPU_BUILDER_UNVERIFIED")
    dest = ROOT / "remote"
    dest.mkdir()
    subprocess.run(["kaggle","kernels","output",KERNEL+"/1","-p",str(dest),"-o"],
                   check=True,timeout=150,stdout=subprocess.DEVNULL)
    if (dest / "submission.zip").read_bytes() != data:
        raise RuntimeError("KAGGLE_REMOTE_ZIP_DIFFERS")
    print("GEMMA_EXISTING_TESTS_REMOTE_CPU_BYTES=PASS",flush=True)
    if not quota():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    print("GEMMA_EXISTING_TESTS_OFFICIAL_SUBMIT_STARTED",flush=True)
    try:
        response=api.competition_submit_code(
            file_name="submission.zip",message=MARKER,competition=COMPETITION,
            kernel=KERNEL,kernel_version=1,quiet=True)
        print("GEMMA_EXISTING_TESTS_API_RESPONSE="+json.dumps(
            response.to_dict() if hasattr(response,"to_dict") else str(response),default=str),flush=True)
    except Exception as exc:
        print("GEMMA_EXISTING_TESTS_API_RESPONSE_ERROR="+type(exc).__name__,flush=True)
    for _ in range(18):
        old=receipt()
        if old:
            print("GEMMA_EXISTING_TESTS_OFFICIAL_RECEIPT="+json.dumps(
                {x:old.get(x) for x in ("ref","status","publicScore","description")},
                sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("SUBMISSION_RECEIPT_MISSING_DO_NOT_RETRY")


def watch():
    old=receipt()
    print("GEMMA_EXISTING_TESTS_CURRENT_RECEIPT="+json.dumps(
        {x:old.get(x) for x in ("ref","status","publicScore")} if old else None,
        sort_keys=True),flush=True)


if __name__=="__main__":
    modes={"quota":quota,"prepare":prepare,"submit":submit,"watch":watch}
    if len(sys.argv)!=2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_existing_test_retrieval_official_once_20261117 quota|prepare|submit|watch")
    modes[sys.argv[1]]()
