"""V1 caller-hop: prompt-only conditional function/implementation expansion.

The control is the byte-pinned scored Toolcap60 31B / 5min / 60-calls
archive. The sole change is the production system instruction. This is
NOT evidence of a PASS gain until an official paired or scored run.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import zipfile

from scripts.build_toolcap60_timeout_recovery import (
    STAMP,
    files_for_candidate as scored_control_files,
)

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
NEW_INSTRUCTION = """

## Conditional one-hop implementation localization

Treat a named function, error, or API in the issue as a search *anchor*,
not automatically as the implementation file to edit. First use narrow
text search and read the match. If two or more different definitions have
the same name, or the matched definition is only a thin delegate/wrapper,
make ONE targeted `get_code_neighbors` or `get_code_subgraph` lookup
for that anchor (choose one; do not enumerate the whole repo). Follow
the immediate caller/callee that actually implements the requested behavior.
Read the implementation and its closest caller or test to confirm the
behavior BEFORE editing. The graph is only a candidate locator, not
evidence that its suggested file is right.

If an ordinary narrow search already identifies the implementation,
SKIP graph expansion. If the first graph lookup is absent, errors,
irrelevant, or too expensive, return to a narrow text search; do not
retry or widen graph exploration. Do not edit a same-name wrapper merely
because its name matches the issue. Preserve the original targeted test,
diff check, source-edit policy and final `submit_patch` requirement.
Do not spend the remaining task budget on extra lookup after the cause
is identified.
"""


def files_for_candidate(source_zip: bytes) -> dict[str, str]:
    original = scored_control_files(source_zip)
    if set(original) != {
        "agent.yaml", "eval_config.yaml", "configs/sampling.yaml", "prompts/system.md"
    }:
        raise ValueError("Unexpected control contents")
    if original["agent.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("31B control model drift")
    if original["eval_config.yaml"].count("max_time_minutes: 5") != 1:
        raise ValueError("Control time budget drift")
    if original["eval_config.yaml"].count("max_tool_calls: 60") != 1:
        raise ValueError("Control tool budget drift")
    if "get_code_neighbors" not in original["agent.yaml"] or "get_code_subgraph" not in original["agent.yaml"]:
        raise ValueError("Missing existing native graph tools")
    if "Conditional one-hop implementation localization" in original["prompts/system.md"]:
        raise ValueError("Caller-hop intervention already applied")
    output = dict(original)
    output["prompts/system.md"] = original["prompts/system.md"].rstrip() + "\n" + NEW_INSTRUCTION
    for path in original:
        if path != "prompts/system.md" and output[path] != original[path]:
            raise AssertionError("Unexpected non-prompt change")
    return output


def build(source_zip: bytes) -> bytes:
    files = files_for_candidate(source_zip)
    with io.BytesIO() as stream:
        with zipfile.ZipFile(stream, "w") as archive:
            for path, text in sorted(files.items()):
                info = zipfile.ZipInfo(path, date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, text.encode("utf-8"))
        data = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise ValueError("Candidate ZIP integrity failed")
    return data


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError("Will not overwrite a candidate")
    data = build(args.source_zip.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print("GEMMA_CALLER_HOP_ZIP_SHA256=" + hashlib.sha256(data).hexdigest())
    print("MODEL=" + MODEL)
    print("BUDGET=5min:60calls:80turns")
    print("OFFICIAL_SUBMISSION=FALSE")
    print("CORRECTNESS_GAIN=UNTESTED")


if __name__ == "__main__":
    main()
