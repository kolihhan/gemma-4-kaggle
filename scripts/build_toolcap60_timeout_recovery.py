"""One-variable timeout recovery of official Toolcap60.

Preserve model, prompt, tools, sampling, 60 tool calls and 80 turns.
Change only per-task walltime from 8 to 5 minutes to bound total run risk.
The earlier 60-call 8-min submission 58164176 timed out; this candidate is
an operational recovery, not evidence of stronger semantic repair.
"""
from __future__ import annotations

import hashlib
import io
import zipfile

from scripts.build_v2_toolcap_submission import (
    files_for_candidate as toolcap60_files,
)

FROM_TIME = "max_time_minutes: 8"
TO_TIME = "max_time_minutes: 5"
STAMP = (2026, 11, 10, 0, 0, 0)


def files_for_candidate(source_zip: bytes) -> dict[str, str]:
    files = toolcap60_files(source_zip)
    eval_config = files["eval_config.yaml"]
    if eval_config.count(FROM_TIME) != 1:
        raise ValueError("unexpected Toolcap60 task-time configuration")
    if eval_config.count("max_tool_calls: 60") != 1:
        raise ValueError("unexpected Toolcap60 tool-call configuration")
    if eval_config.count("max_turns: 80") != 1:
        raise ValueError("unexpected Toolcap60 turn configuration")
    out = dict(files)
    out["eval_config.yaml"] = eval_config.replace(FROM_TIME, TO_TIME, 1)
    if out["eval_config.yaml"].replace(TO_TIME, FROM_TIME, 1) != eval_config:
        raise AssertionError("other Toolcap60 config drift")
    for path in files:
        if path != "eval_config.yaml" and out[path] != files[path]:
            raise AssertionError("source prompt/model/tools/sampling drift")
    return out


def build(source_zip: bytes) -> bytes:
    files = files_for_candidate(source_zip)
    with io.BytesIO() as sink:
        with zipfile.ZipFile(sink, mode="w") as z:
            for path, body in sorted(files.items()):
                info = zipfile.ZipInfo(path, date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, body.encode())
        archive = sink.getvalue()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(files):
            raise ValueError("bad timeout-recovery archive")
    return archive


def summary(source_zip: bytes) -> dict:
    archive = build(source_zip)
    return {
        "sha256": hashlib.sha256(archive).hexdigest(),
        "task_time_minutes": 5,
        "tool_calls_cap": 60,
        "model": "gemma-4-31b-it-qat-w4a16-ct",
        "official_submission": False,
        "claimed_correctness_gain": False,
    }
