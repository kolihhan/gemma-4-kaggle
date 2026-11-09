"""One-shot official Kaggle code submission of validated V2 tool-cap 60 candidate.

Called only after private 31B paired comparison has reached a measurable
terminal state and the independent workflow gate has accepted its risk.
This program never trains and cannot submit more than once with MARKER.
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

from scripts.build_v2_toolcap_submission import build
from scripts.prepare_public_budgetfit_v2 import validate_source_zip

COMPETITION = "gemma-4-developer-agent"
SOURCE = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
KERNEL = "kolihhan/gemma4-v2-toolcap60-v1-20261109"
MARKER = "v2-toolcap60-v1-20261109"
ROOT = Path("/tmp/gemma4-v2-toolcap60-submit")
NATIVE = (
    "run_command", "read_file", "edit_file", "write_file", "get_status",
    "submit_patch", "get_code_neighbors", "search_similar_code",
    "get_code_subgraph",
)
MODEL = "gemma-4-31b-it-qat-w4a16-ct"


def cmd(args: list[str], timeout=180) -> str:
    proc = subprocess.run(args, text=True, capture_output=True,
                          timeout=timeout, check=True)
    return proc.stdout


def authenticated_submissions() -> list[dict[str, str]]:
    stream = cmd(["kaggle", "competitions", "submissions", COMPETITION, "-v"],
                 timeout=120)
    return list(csv.DictReader(io.StringIO(stream.lstrip("\ufeff"))))


def existing_receipt(rows) -> dict | None:
    exact = [row for row in rows if row.get("description") == MARKER]
    if len(exact) > 1:
        raise RuntimeError("DUPLICATE_OFFICIAL_MARKER_REQUIRES_MANUAL_REVIEW")
    if not exact:
        return None
    row = exact[0]
    return {name: row.get(name) for name in (
        "ref", "status", "date", "publicScore", "privateScore", "description")}


def check_slot() -> bool:
    from kaggle.api.kaggle_api_extended import KaggleApi

    rows = authenticated_submissions()
    receipt = existing_receipt(rows)
    if receipt is not None:
        print("TOOLCAP60_EXISTING_OFFICIAL_RECEIPT=" +
              json.dumps(receipt, sort_keys=True), flush=True)
        return False
    api = KaggleApi()
    api.authenticate()
    quota = api.competition_get_submission_limits(COMPETITION)
    active = [row.get("ref") for row in rows if
              (row.get("status") or "").upper().split(".")[-1] in
              {"PENDING", "RUNNING", "QUEUED", "SCORING", "EVALUATING"}]
    print("TOOLCAP60_OFFICIAL_SLOT=" + json.dumps({
        "allowed_now": quota.num_allowed_now,
        "num_today": quota.num_today,
        "limited_by_total": quota.limited_by_total,
        "active": active,
    }), flush=True)
    if quota.num_allowed_now < 1 or quota.limited_by_total or active:
        raise RuntimeError("OFFICIAL_SLOT_UNAVAILABLE")
    return True


def compile_without_inference(archive: bytes) -> None:
    from adk_submission import (
        validate_directory, compile_submission, ModelRegistry, ToolRegistry,
    )
    from google.adk.models.base_llm import BaseLlm
    from swegemma.config import build_submission_limits
    from tempfile import TemporaryDirectory

    class NoInferenceModel(BaseLlm):
        async def generate_content_async(self, *args, **kwargs):
            raise AssertionError("MODEL_CALL_DURING_CPU_PREFLIGHT_FORBIDDEN")
            yield

    with TemporaryDirectory(prefix="toolcap60-official-") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            if z.testzip() is not None:
                raise ValueError("invalid output ZIP")
            z.extractall(target)
        limits, _ = build_submission_limits()
        validate_directory(target, limits=limits)
        models = ModelRegistry()
        models.register(MODEL, NoInferenceModel(model=MODEL))
        registry = ToolRegistry()
        for name in NATIVE:
            def unused_tool(*args, **kwargs):
                raise AssertionError("NO_NATIVE_TOOL_DURING_COMPILE")
            registry.register(name, unused_tool)
        agent = compile_submission(
            submission_dir=target, model_registry=models, tool_registry=registry,
        )
        if agent.model.model != MODEL:
            raise ValueError("root model unexpectedly changed")
        if len(agent.tools) != len(NATIVE):
            raise ValueError("root native tool list unexpectedly changed")
        print("TOOLCAP60_OFFICIAL_ADK_COMPILE=PASS", flush=True)
        print("TOOLCAP60_OFFICIAL_LIMIT_VALIDATION=PASS", flush=True)


def preflight() -> None:
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("PREFLIGHT_DIR_ALREADY_POPULATED")
    origin = ROOT / "source"
    origin.mkdir(parents=True)
    subprocess.run(
        ["kaggle", "kernels", "output", SOURCE, "-p", str(origin), "-o"],
        check=True, stdout=subprocess.DEVNULL, timeout=180,
    )
    source = (origin / "submission.zip").read_bytes()
    original = validate_source_zip(source)
    candidate = build(source)
    digest = hashlib.sha256(candidate).hexdigest()
    with zipfile.ZipFile(io.BytesIO(candidate)) as zipped:
        if zipped.testzip() is not None:
            raise RuntimeError("candidate zip CRC invalid")
        if sorted(zipped.namelist()) != sorted(original):
            raise RuntimeError("candidate members changed")
        for filename in original:
            observed = zipped.read(filename).decode("utf-8")
            expected = (original[filename].replace(
                "max_tool_calls: 28", "max_tool_calls: 60", 1)
                if filename == "eval_config.yaml" else original[filename])
            if observed != expected:
                raise RuntimeError("UNEXPECTED_CANDIDATE_DIFF:" + filename)

    compile_without_inference(candidate)
    (ROOT / "submission.zip").write_bytes(candidate)
    (ROOT / "candidate.sha256").write_text(digest)
    print("TOOLCAP60_ARCHIVE_SHA256=" + digest, flush=True)

    import nbformat

    data64 = base64.b64encode(candidate).decode("ascii")
    cell = (
        "import base64, hashlib\n"
        "from pathlib import Path\n"
        f"payload = base64.b64decode({data64!r}, validate=True)\n"
        f"expected = {digest!r}\n"
        "assert hashlib.sha256(payload).hexdigest() == expected\n"
        "Path('/kaggle/working/submission.zip').write_bytes(payload)\n"
        "print('TOOLCAP60_REMOTE_ARCHIVE_SHA256=' + expected)\n"
    )
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# V2 tool-cap 60 — scored development experiment\n\n"
            "Apache-2.0 source attribution: lynnsakurai public Budget-Fit V2. "
            "This notebook only reproduces an independently CPU-compiled agent ZIP. "
            "It performs no model inference or training."
        ),
        nbformat.v4.new_code_cell(cell),
    ])
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3",
    }
    nbformat.validate(notebook)
    dest = ROOT / "kernel"
    dest.mkdir()
    (dest / "v2-toolcap60.ipynb").write_text(nbformat.writes(notebook))
    metadata = {
        "id": KERNEL, "title": KERNEL.split("/", 1)[1],
        "code_file": "v2-toolcap60.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": False, "enable_tpu": False, "enable_internet": False,
        "competition_sources": [COMPETITION],
        "dataset_sources": [], "kernel_sources": [], "model_sources": [],
    }
    (dest / "kernel-metadata.json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n"
    )
    print("TOOLCAP60_PRIVATE_NOTEBOOK_PREPARED=" + KERNEL, flush=True)


def submit() -> None:
    digest = (ROOT / "candidate.sha256").read_text().strip()
    local = (ROOT / "submission.zip").read_bytes()
    if hashlib.sha256(local).hexdigest() != digest:
        raise RuntimeError("LOCAL_ARCHIVE_SHA_MISMATCH")
    # The preflight is deterministic. A prior matching submission must be reused.
    if not check_slot():
        return
    response = cmd(
        ["kaggle", "kernels", "push", "-p", str(ROOT / "kernel"), "-t", "600"],
        timeout=240,
    )
    # The CLI exits non-zero when the push fails. Do not inspect localized or
    # version-dependent success text; the authenticated status/output round-trip
    # below is the authoritative proof of the accepted kernel version.
    print("TOOLCAP60_PRIVATE_KERNEL_PUSH_RETURNED_OK", flush=True)
    for _ in range(60):
        status = cmd(["kaggle", "kernels", "status", KERNEL], timeout=60)
        if "KernelWorkerStatus.COMPLETE" in status:
            break
        if any(x in status for x in (
                "KernelWorkerStatus.ERROR", "KernelWorkerStatus.FAILED",
                "KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("CPU_NOTEBOOK_ERROR")
        time.sleep(10)
    else:
        raise RuntimeError("CPU_NOTEBOOK_NOT_TERMINAL")
    output = ROOT / "remote"
    output.mkdir()
    subprocess.run(
        ["kaggle", "kernels", "output", KERNEL + "/1", "-p", str(output), "-o"],
        check=True, stdout=subprocess.DEVNULL, timeout=180,
    )
    remote = (output / "submission.zip").read_bytes()
    if remote != local:
        raise RuntimeError("REMOTE_BUILDER_OUTPUT_BYTES_CHANGED")
    print("TOOLCAP60_REMOTE_ARCHIVE_VERIFIED=" + digest, flush=True)
    if not check_slot():
        return
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    print("TOOLCAP60_OFFICIAL_SUBMIT_STARTED", flush=True)
    try:
        result = api.competition_submit_code(
            file_name="submission.zip", message=MARKER, competition=COMPETITION,
            kernel=KERNEL, kernel_version=1, quiet=True,
        )
        print("TOOLCAP60_SUBMIT_RESPONSE=" + json.dumps(
            result.to_dict() if hasattr(result, "to_dict") else str(result),
            default=str, sort_keys=True,
        ), flush=True)
    except Exception as exc:
        # The server may accept even if the client loses the response.
        print("TOOLCAP60_SUBMIT_CLIENT_ERROR=" + type(exc).__name__, flush=True)
    for _ in range(15):
        found = existing_receipt(authenticated_submissions())
        if found:
            print("TOOLCAP60_AUTHENTICATED_RECEIPT=" + json.dumps(
                found, sort_keys=True), flush=True)
            return
        time.sleep(10)
    raise RuntimeError("OFFICIAL_RECEIPT_UNCONFIRMED_DO_NOT_RETRY")


if __name__ == "__main__":
    modes = {"quota": check_slot, "preflight": preflight, "submit": submit}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_v2_toolcap60_official_once [quota|preflight|submit]")
    modes[sys.argv[1]]()
