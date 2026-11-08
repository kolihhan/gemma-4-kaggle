"""Stage and submit one role-recovery Gemma 4 candidate (private Kaggle).

Run by the opt-in workflow on research/dual-agent-recovery-v0-20261108.
Never runs model inference on GitHub; official Kaggle scoring does so after submission.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from scripts.build_recovery_decision_candidate import build, ARMS
from scripts.prepare_public_budgetfit_v2 import validate_source_zip

COMPETITION = "gemma-4-developer-agent"
SOURCE = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
KERNEL = "kolihhan/gemma4-recovery-reviewer-v0-fixed-20261108"
ARM = "recovery_reviewer"
EXPECTED = "430e64d2c9a60a737f197a5372afa33c4813526239828b71c5971eda283a743e"
MARKER = "recovery-reviewer-v0:430e64d2c9a6"
ROOT = Path("/tmp/gemma4-recovery-submit")
NATIVE = (
    "run_command", "read_file", "edit_file", "write_file", "get_status",
    "submit_patch", "get_code_neighbors", "search_similar_code",
    "get_code_subgraph",
)


def run(args: list[str], *, timeout: int = 180) -> str:
    p = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout)
    return p.stdout


def submissions() -> list[dict[str, str]]:
    text = run(["kaggle", "competitions", "submissions", COMPETITION, "-v"], timeout=120)
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def matching_receipt(rows: list[dict[str, str]]) -> dict | None:
    found = [r for r in rows if r.get("description") == MARKER]
    if len(found) > 1:
        raise RuntimeError("DUPLICATE_RECOVERY_RECEIPT")
    return {k: found[0].get(k) for k in (
        "ref", "status", "date", "publicScore", "privateScore", "description"
    )} if found else None


def print_receipt(receipt: dict) -> None:
    print("RECOVERY_OFFICIAL_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)


def check_slot() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi
    rows = submissions()
    existing = matching_receipt(rows)
    if existing:
        print_receipt(existing)
        print("RECOVERY_ALREADY_SUBMITTED=TRUE", flush=True)
        return False
    api = KaggleApi()
    api.authenticate()
    quota = api.competition_get_submission_limits(COMPETITION)
    active = [r.get("ref") for r in rows if
              (r.get("status") or "").upper().split(".")[-1] in
              {"PENDING", "RUNNING", "QUEUED", "SCORING", "EVALUATING"}]
    print("RECOVERY_KAGGLE_SLOT=" + json.dumps({
        "allowed_now": quota.num_allowed_now,
        "num_today": quota.num_today,
        "limited_by_total": quota.limited_by_total,
        "active": active,
    }), flush=True)
    if quota.num_allowed_now < 1 or quota.limited_by_total or active:
        raise RuntimeError("KAGGLE_SLOT_UNAVAILABLE_NO_SUBMISSION")
    return True


def compile_without_inference(paths: dict[str, Path]) -> None:
    from adk_submission import validate_directory, compile_submission
    from adk_submission import ModelRegistry, ToolRegistry
    from google.adk.models.base_llm import BaseLlm

    class NoInference(BaseLlm):
        async def generate_content_async(self, *args, **kwargs):
            raise AssertionError("MODEL_CALL_FORBIDDEN_DURING_PREFLIGHT")
            yield

    for arm, directory in paths.items():
        validate_directory(directory)
        models = ModelRegistry()
        models.register("gemma-4-31b-it-qat-w4a16-ct",
                        NoInference(model="gemma-4-31b-it-qat-w4a16-ct"))
        registry = ToolRegistry()
        for name in NATIVE:
            def unusable_native(*args, **kwargs):
                raise AssertionError("NATIVE_TOOL_CALL_FORBIDDEN_DURING_PREFLIGHT")
            registry.register(name, unusable_native)
        agent = compile_submission(submission_dir=directory, tool_registry=registry,
                                   model_registry=models)
        if agent.model.model != "gemma-4-31b-it-qat-w4a16-ct":
            raise AssertionError("MODEL_CHANGED")
        if len(agent.tools) != len(NATIVE) + 1:
            raise AssertionError("TOOLS_CHANGED")
        adviser = [tool for tool in agent.tools
                   if getattr(tool, "name", None) == "recovery_adviser"]
        if len(adviser) != 1 or adviser[0].agent.model.model != agent.model.model:
            raise AssertionError("ADVISER_MISSING")
        if adviser[0].agent.tools:
            raise AssertionError("ADVISER_HAS_TOOLS")
        print("RECOVERY_ADK_OFFICIAL_COMPILE=PASS:" + arm, flush=True)


def preflight() -> None:
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("PREFLIGHT_DIRECTORY_NOT_EMPTY")
    (ROOT / "source").mkdir(parents=True)
    subprocess.run(["kaggle", "kernels", "output", SOURCE,
                    "-p", str(ROOT / "source"), "-o"],
                   check=True, stdout=subprocess.DEVNULL, timeout=180)
    raw = (ROOT / "source/submission.zip").read_bytes()
    original = validate_source_zip(raw)
    archives = build(raw)
    by_arm = {}
    paths = {}
    for arm in ARMS:
        data = archives[arm]
        if arm == ARM and hashlib.sha256(data).hexdigest() != EXPECTED:
            raise AssertionError("RECOVERY_SHA_MISMATCH")
        directory = ROOT / "inspect" / arm
        directory.mkdir(parents=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if z.testzip() is not None:
                raise AssertionError("BAD_ARCHIVE")
            z.extractall(directory)
            assert z.read("configs/sampling.yaml").decode() == original["configs/sampling.yaml"]
            assert z.read("eval_config.yaml").decode() == original["eval_config.yaml"]
        by_arm[arm] = data
        paths[arm] = directory
    compile_without_inference(paths)
    (ROOT / "archive.zip").write_bytes(by_arm[ARM])
    print("RECOVERY_PRECHECK_SHA=" + EXPECTED, flush=True)

    import nbformat
    payload = base64.b64encode(by_arm[ARM]).decode("ascii")
    cell = (
        "import base64,hashlib\nfrom pathlib import Path\n"
        f"data=base64.b64decode({payload!r},validate=True)\n"
        f"expected={EXPECTED!r}\n"
        "assert hashlib.sha256(data).hexdigest()==expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(data)\n"
        "print('RECOVERY_CPU_OUTPUT_VERIFIED='+expected)\n"
    )
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# Recovery Reviewer v0 — CPU archive builder\n\n"
            "Derived from lynnsakurai's Apache-2.0 Budget-Fit V2. "
            "No model execution in this notebook."
        ),
        nbformat.v4.new_code_cell(cell),
    ])
    notebook.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbformat.validate(notebook)
    directory = ROOT / "kernel"
    directory.mkdir()
    (directory / "recovery-reviewer-v0.ipynb").write_text(
        nbformat.writes(notebook), encoding="utf-8"
    )
    metadata = {
        "id": KERNEL, "title": KERNEL.split("/", 1)[1],
        "code_file": "recovery-reviewer-v0.ipynb",
        "language": "python", "kernel_type": "notebook",
        "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": False, "competition_sources": [COMPETITION],
        "dataset_sources": [], "kernel_sources": [], "model_sources": [],
    }
    (directory / "kernel-metadata.json").write_text(
        json.dumps(metadata) + "\n", encoding="utf-8"
    )
    print("RECOVERY_PRIVATE_NOTEBOOK_PREPARED=" + KERNEL, flush=True)


def submit() -> None:
    if not (ROOT / "archive.zip").exists():
        raise RuntimeError("NO_VERIFIED_ARCHIVE")
    data = (ROOT / "archive.zip").read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise RuntimeError("LOCAL_ARCHIVE_HASH_CHANGED")
    subprocess.run(["kaggle", "kernels", "push", "-p", str(ROOT / "kernel"),
                    "-t", "600"], check=True, timeout=240)
    for _ in range(60):
        status = run(["kaggle", "kernels", "status", KERNEL], timeout=60)
        if "KernelWorkerStatus.COMPLETE" in status or "KernelWorkerStatus.COMPLETED" in status:
            break
        if any(s in status for s in ("KernelWorkerStatus.ERROR", "KernelWorkerStatus.FAILED",
                                    "KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("PRIVATE_CPU_NOTEBOOK_FAILED:" + status[-500:])
        time.sleep(10)
    else:
        raise RuntimeError("PRIVATE_CPU_NOTEBOOK_NOT_TERMINAL")
    (ROOT / "remote").mkdir()
    subprocess.run(["kaggle", "kernels", "output", KERNEL + "/1",
                    "-p", str(ROOT / "remote"), "-o"],
                   check=True, stdout=subprocess.DEVNULL, timeout=150)
    remote = (ROOT / "remote/submission.zip").read_bytes()
    if remote != data:
        raise RuntimeError("PRIVATE_CPU_ARCHIVE_MISMATCH")
    print("RECOVERY_PRIVATE_CPU_ARCHIVE_VERIFIED=" + EXPECTED, flush=True)

    # Authenticated quota rechecked immediately before submission, after staging.
    if not check_slot():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    print("RECOVERY_OFFICIAL_SUBMIT_STARTED", flush=True)
    try:
        result = api.competition_submit_code(
            file_name="submission.zip", message=MARKER,
            competition=COMPETITION, kernel=KERNEL,
            kernel_version=1, quiet=True,
        )
        print("RECOVERY_SUBMIT_API_RESULT=" + json.dumps(
            result.to_dict() if hasattr(result, "to_dict") else str(result),
            default=str,
        ), flush=True)
    except Exception as exc:
        # A failed client response may still mean the server accepted a request.
        print("RECOVERY_SUBMIT_EXCEPTION=" + type(exc).__name__, flush=True)
    for _ in range(12):
        found = matching_receipt(submissions())
        if found:
            print_receipt(found)
            return
        time.sleep(10)
    raise RuntimeError("RECOVERY_RECEIPT_UNCONFIRMED_DO_NOT_RESUBMIT")


if __name__ == "__main__":
    modes = {"quota": lambda: check_slot(), "preflight": preflight, "submit": submit}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_recovery_official_once [quota|preflight|submit]")
    modes[sys.argv[1]]()
