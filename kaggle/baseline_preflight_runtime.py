"""CPU Kaggle runtime that validates the exact baseline submission archive."""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import traceback
import zipfile
from pathlib import Path, PurePosixPath


SUBMISSION_ARCHIVE_B64 = "__SUBMISSION_ARCHIVE_B64__"
EXPECTED_SHA256 = "__EXPECTED_SHA256__"
EXPECTED_MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
RESULT_PATH = WORKING_DIR / "baseline_submission_validation.json"


def install_official_wheelhouse() -> None:
    if not WHEELHOUSE_DIR.is_dir():
        raise FileNotFoundError(f"missing official wheelhouse: {WHEELHOUSE_DIR}")

    fixed = Path("/tmp/gemma4-baseline-wheelhouse")
    fixed.mkdir(parents=True, exist_ok=True)
    for wheel in WHEELHOUSE_DIR.glob("*.whl"):
        if "cutlass" in wheel.name.lower():
            continue
        name = (
            wheel.name.replace("cu128", "+cu128")
            if "cu128" in wheel.name and "+" not in wheel.name
            else wheel.name
        )
        target = fixed / name
        if target.exists():
            continue
        try:
            target.symlink_to(wheel)
        except OSError:
            shutil.copyfile(wheel, target)

    wheels = sorted(str(path) for path in fixed.glob("*.whl"))
    if not wheels:
        raise RuntimeError("official scorer wheelhouse contained no usable wheels")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--no-deps",
            "--force-reinstall",
            *wheels,
        ],
        check=True,
    )
    importlib.invalidate_caches()


def extract_archive(raw: bytes, destination: Path) -> list[str]:
    archive_path = WORKING_DIR / "submission.zip"
    archive_path.write_bytes(raw)
    with zipfile.ZipFile(archive_path) as zf:
        names = zf.namelist()
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise RuntimeError(f"unsafe archive member: {name}")
        if "agent.yaml" not in names:
            raise RuntimeError("archive is missing root agent.yaml")
        if any(name.startswith("submission/") for name in names):
            raise RuntimeError("archive contains unexpected submission/ wrapper directory")
        zf.extractall(destination)
    return names


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    if SUBMISSION_ARCHIVE_B64.startswith("__") or EXPECTED_SHA256.startswith("__"):
        raise RuntimeError("preflight runtime placeholders were not rendered")

    raw = base64.b64decode(SUBMISSION_ARCHIVE_B64.encode("ascii"))
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise RuntimeError(
            f"archive SHA mismatch before validation: {actual_sha} != {EXPECTED_SHA256}"
        )

    install_official_wheelhouse()

    submission_dir = WORKING_DIR / "validated-submission"
    if submission_dir.exists():
        shutil.rmtree(submission_dir)
    submission_dir.mkdir(parents=True)
    names = extract_archive(raw, submission_dir)

    from adk_submission import validate_directory
    from adk_submission.discovery import discover_declared_models
    from swegemma.config import build_submission_limits

    limits, _generation_constraints = build_submission_limits()
    validate_directory(submission_dir, limits=limits)
    models = discover_declared_models(submission_dir)
    if models != {EXPECTED_MODEL}:
        raise RuntimeError(f"unexpected declared models: {sorted(models)}")

    result = {
        "status": "valid",
        "archive_sha256": actual_sha,
        "declared_models": sorted(models),
        "file_count": len(names),
        "files": names,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("BASELINE_SUBMISSION_VALIDATION", json.dumps(result, sort_keys=True))


def write_failure(exc: BaseException) -> None:
    RESULT_PATH.write_text(
        json.dumps(
            {
                "status": "error",
                "archive_sha256": EXPECTED_SHA256,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
