"""Single source-mutation channel paired experiment.

Control: exact FastPath 40/4 official submission 58808118.
Treatment: same prompt except the edit instructions, same 31B model and
sampling/time/call caps, but remove native edit_file and write_file. Use
the existing run_command tool with checked git apply. No new tool or grader
modification, training, or official submission. Private fresh issue pairs.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from scripts import render_edit_grammar_paired31b_20261124 as prior
from scripts.build_gemma_edit_grammar_20261124 import files_for_pair as prior_files
from scripts.submit_fastpath40_4min_once_20261124 import build as build_fastpath

CONTROL_SHA = "caf570136b365b9c55d499534e945f6216a37afadb7e3f8cdd6589b60ea7635c"
OLD_MODEL = prior.MODEL
VERSION = "single-edit-channel-31b-4min-paired-v1"
KERNEL = "kolihhan/gemma4-single-edit-channel-paired-20261124-v1"
RESULT = "paired_single_edit_channel31b_4min_results.json"
OLD_EDIT = """   complete source change. Do not wait for exhaustive certainty. Use edit_file
   with an exact unique old_string and a short replacement. If it fails, reread
   that region and use a smaller unique match. Keep the patch focused on the
   requested behavior."""
NEW_EDIT = """   complete source change. Do not wait for exhaustive certainty. Use run_command
   to write one small unified diff to /tmp/repair.diff (a quoted heredoc works).
   Include real source context, repository-relative a/ and b/ paths, and valid
   hunk headers. Run git apply --check --recount /tmp/repair.diff &&
   git apply --recount /tmp/repair.diff in the same command. If the check fails,
   reread the target region and correct the diff once; do not blindly apply it.
   Keep the patch focused on the requested behavior. The edit_file and
   write_file tools are intentionally unavailable. Do not modify hidden tests,
   evaluation infrastructure, or unrelated files."""


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def pack(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in sorted(files.items()):
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("unsafe archive path")
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, text.encode("utf-8"))
    return buf.getvalue()


def make_pair(source: bytes):
    blob = build_fastpath(source)
    if sha(blob) != CONTROL_SHA:
        raise ValueError("FastPath official archive does not match")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        control = {n: z.read(n).decode("utf-8") for n in z.namelist()}
    if set(control) != {"agent.yaml","eval_config.yaml","configs/sampling.yaml","prompts/system.md"}:
        raise ValueError("unexpected package")
    treatment = dict(control)
    for tool in ("edit_file", "write_file"):
        line = "  - " + tool + "\n"
        if treatment["agent.yaml"].count(line) != 1:
            raise ValueError("unexpected tool declaration")
        treatment["agent.yaml"] = treatment["agent.yaml"].replace(line, "", 1)
    if treatment["prompts/system.md"].count(OLD_EDIT) != 1:
        raise ValueError("FastPath edit clause changed")
    treatment["prompts/system.md"] = treatment["prompts/system.md"].replace(OLD_EDIT, NEW_EDIT, 1)
    assert {k for k in control if control[k] != treatment[k]} == {"agent.yaml","prompts/system.md"}
    assert all(x in control["eval_config.yaml"] for x in (
        "max_time_minutes: 4", "max_tool_calls: 40", "max_turns: 80", "timeout_seconds: 240"))
    return control, treatment, blob, pack(treatment)


def load_excluded(repo: Path, previous: list[Path]) -> set[str]:
    # Read only selected IDs from completed private dev results; never feed
    # previous task text, labels, patches, or model outputs into a solver.
    old_plan = json.loads((repo / prior.MANIFEST_PATH).read_text())
    excluded = set(old_plan["selection"]["exclude_instance_ids"])
    if len(previous) != 2:
        raise ValueError("both earlier completed pilots required")
    for file in previous:
        data = json.loads(file.read_text())
        ids = set(data["selected_public_dev_ids"])
        if data["status"] != "completed" or len(data["results"]) != 16 or len(ids) != 8:
            raise ValueError("previous pilot not complete")
        if excluded.intersection(ids):
            raise ValueError("prior pilot overlap or incorrect provenance")
        excluded.update(ids)
    return excluded


def render(repo: Path, source: bytes, out: Path, previous: list[Path]) -> dict:
    old_plan = json.loads((repo / prior.MANIFEST_PATH).read_text())
    old_c, old_t = prior_files(source)
    control, treatment, czip, tzip = make_pair(source)
    excluded = load_excluded(repo, previous)
    plan = {
        "version": VERSION,
        "model": OLD_MODEL,
        "selection": {
            "salt": "gemma-single-edit-channel-20261124-fresh-holdout-v1",
            "counts_by_repo": {"fastapi_":2,"rich_":2,"requests_":2},
            "exclude_instance_ids": sorted(excluded),
            "policy":"ID-only deterministic held-out selection; no labels; no replacement",
        },
        "shared_budget":{"max_time_minutes":4,"max_tool_calls":40,
                         "max_turns":80,"timeout_seconds":240},
        "control_sha256":sha(czip),"treatment_sha256":sha(tzip),
        "private_only":True,"official_submission":False,
    }

    # Reuse the previously successful real 31B runner, NOT its data.
    # All edits to the rendered runtime are explicit, fail closed, and keep
    # the same official Evaluator and independent arm directories.
    text = prior.render_runtime((repo / prior.TEMPLATE_PATH).read_text(), source, old_plan)
    def once(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError("render marker missing or duplicated")
        text = text.replace(old, new, 1)
    once(repr(prior.payload(old_c)), repr(prior.payload(control)))
    once(repr(prior.payload(old_t)), repr(prior.payload(treatment)))
    once(repr(json.dumps(old_plan,sort_keys=True)), repr(json.dumps(plan,sort_keys=True)))
    text = text.replace("edit-grammar-31b-5min-paired-v1", VERSION)
    text = text.replace("champion_5min", "fastpath_4min")
    text = text.replace("edit_grammar_5min", "single_edit_4min")
    text = text.replace("paired-champion-5min", "paired-fastpath-4min")
    text = text.replace("paired-edit-grammar-5min", "paired-single-edit-4min")
    text = text.replace("paired-edit-grammar-private-results","paired-single-edit-private-results")
    text = text.replace("paired_edit_grammar31b_5min_results.json", RESULT)
    once("if len(chosen) != 8 or len(set(chosen)) != 8:",
         "if len(chosen) != 6 or len(set(chosen)) != 6:")
    once("if len(records) != 16:", "if len(records) != 12:")
    once("if len(scored) != 8:", "if len(scored) != 6:")
    # Persist real final agent patches ONLY inside the private Kaggle output
    # to distinguish malformed diff, wrong edit and empty diff retrospectively.
    once('                    row = {\n                        "arm": arm,',
         '                    if patch:\n'
         '                        patch_dir = RESULTS_DIR / "private-final-patches" / arm\n'
         '                        patch_dir.mkdir(parents=True, exist_ok=True)\n'
         '                        (patch_dir / (task_id + ".patch")).write_text(patch, encoding="utf-8")\n'
         '                    row = {\n                        "arm": arm,')
    compile(text, "single_edit_channel_runtime.py", "exec")
    assert "competition_submit_code" not in text
    assert "treatment_evaluator = Evaluator(treatment_config)" in text
    out.mkdir(parents=True,exist_ok=False)
    (out / "single_edit_channel_runtime.py").write_text(text)
    metadata = {
        "id":KERNEL,"title":KERNEL.split("/")[1],
        "code_file":"single_edit_channel_runtime.py","language":"python",
        "kernel_type":"script","is_private":True,"enable_gpu":True,
        "enable_tpu":False,"enable_internet":False,"machine_shape":"NvidiaL4",
        "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources":["gemma-4-developer-agent"],
        "kernel_sources":[],"model_sources":[prior.MODEL_SOURCE],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(metadata,indent=2))
    return {"control_sha256":sha(czip),"candidate_sha256":sha(tzip),
            "matched_pairs":6,"evaluations":12,"prior_ids_excluded":len(excluded),
            "private_kernel":KERNEL,"model":OLD_MODEL,"official_submission":False,
            "changed":["mutation tool affordance and corresponding instruction"],
            "raw_private_content_exported":False}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--previous",type=Path,nargs=2,required=True)
    a=p.parse_args()
    report=render(Path("."),a.source.read_bytes(),a.out,a.previous)
    print("SINGLE_EDIT_CPU_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
