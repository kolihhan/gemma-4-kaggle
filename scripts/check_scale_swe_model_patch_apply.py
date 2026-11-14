"""Patch apply preflight for two fixed NVIDIA successful Scale-SWE cases.

Uses exact source parent_commit from matched Scale-SWE Parquet, not a ref patch.
Downloads only a shallow filtered public repository checkout, then runs
`git apply --check` with NVIDIA *model* patch. Never executes repository code,
tests, or source-provided commands. Ephemeral runner only; logs aggregates.
"""
from __future__ import annotations
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from urllib.error import HTTPError

from scripts.audit_open_swe_traces_metadata import get_json, DATASET, sample_grade
from scripts.join_scale_swe_parquet_eight import (
    DATASET as SCALE, COLUMNS, replay_fields, may_contain, validate_catalog
)

MAX_REPO_BYTES=900_000_000


def fetch_nvidia_fixed_eight() -> dict:
    # Read each fixed six-row NVIDIA viewer page only ONCE.
    eligible = []
    for offset in (6, 12):
        page = get_json("/rows", {"dataset": DATASET, "config": "v2.0",
                                  "split": "sweagent", "offset": offset, "length": 6})
        wrapped = page.get("rows")
        if not isinstance(wrapped, list) or len(wrapped) != 6:
            raise ValueError("frozen NVIDIA cohort incomplete")
        for item in wrapped:
            rec = item.get("row", {}) if isinstance(item, dict) else {}
            if sample_grade(rec) != "candidate_for_private_deep_audit":
                continue
            meta = rec.get("metadata")
            patch_obj = meta.get("model_patch") if isinstance(meta,dict) else None
            patch = patch_obj.get("patch") if isinstance(patch_obj,dict) else patch_obj
            if not isinstance(patch,str) or not patch.startswith("diff --git "):
                raise ValueError("frozen model diff missing")
            eligible.append({
                "instance_id": rec.get("instance_id"),
                "source": {k: rec.get(k) for k in ("instance_id","repo","license")},
                "model_patch": patch
            })
    if len(eligible) != 8 or len({r["instance_id"] for r in eligible}) != 8:
        raise ValueError("frozen eight-task denominator drift")
    return {r["instance_id"]: r for r in eligible}


def fetch_nvidia_fixed_two() -> dict:
    """Frozen first two, maintaining the previously tested sample contract."""
    whole=fetch_nvidia_fixed_eight()
    return dict(list(whole.items())[:2])

def get_scale_match(rows:dict)->dict:
    import fsspec
    import pyarrow.parquet as pq
    wanted=set(rows)
    found={key:[] for key in wanted}
    # source gold `patch` remains intentionally not in column list
    for uri in validate_catalog():
        with fsspec.open(uri,mode="rb",block_size=1<<16,
                         cache_type="none",timeout=40) as handle:
            pf=pq.ParquetFile(handle)
            for j in range(pf.metadata.num_row_groups):
                rg=pf.metadata.row_group(j)
                idx=next((k for k in range(rg.num_columns) if
                          rg.column(k).path_in_schema=="instance_id"),None)
                if idx is not None and not may_contain(rg.column(idx).statistics,wanted):
                    continue
                ids=pf.read_row_group(j,columns=["instance_id"])["instance_id"].to_pylist()
                hits=[(ix,id_) for ix,id_ in enumerate(ids) if id_ in wanted]
                if not hits:
                    continue
                # Two rows: only fetch non-gold provenance columns in matching
                # row groups, then validate provenance before any git work.
                data=pf.read_row_group(j,columns=list(COLUMNS))
                for ix,id_ in hits:
                    record={key:data[key][ix].as_py() for key in COLUMNS}
                    found[id_].append(record)
    for key in wanted:
        if len(found[key])!=1:
            raise ValueError("missing or duplicate Scale-SWE parent commit")
        if replay_fields(found[key][0],rows[key]["source"])!=(
            "source_parent_sha_and_test_inputs_joined_NOT_REPLAYED"):
            raise ValueError("Scale-SWE replay metadata drift")
    return {key:found[key][0] for key in wanted}


def safe_public_repo_url(owner:str, repo:str)->str:
    for value in (owner,repo):
        if not isinstance(value,str) or re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,95}",value) is None:
            raise ValueError("unsafe repository name")
        if value in {".",".."}:
            raise ValueError("unsafe repository name")
    return f"https://github.com/{owner}/{repo}.git"


def git_cmd(root: Path, *args: str, timeout:int=135, stdin: str|None=None)->bool:
    env={**os.environ,"GIT_TERMINAL_PROMPT":"0","GIT_LFS_SKIP_SMUDGE":"1",
         "GIT_CONFIG_NOSYSTEM":"1"}
    try:
        res=subprocess.run(["git", "-C",str(root), *args],input=stdin,
                           capture_output=True,text=True,check=False,
                           timeout=timeout, env=env)
    except (OSError,TimeoutError,subprocess.TimeoutExpired):
        return False
    return res.returncode==0


def check_one(meta:dict, model_patch:str)->str:
    owner=meta["user"]; repo=meta["repo"]
    url=safe_public_repo_url(owner,repo)
    with TemporaryDirectory(prefix="gemma_source_apply_") as base:
        root=Path(base)/"checkout";root.mkdir()
        if not git_cmd(root,"init","-q",timeout=20):
            return "local_git_unavailable"
        if not git_cmd(root,"remote","add","origin",url,timeout=20):
            return "remote_invalid"
        if not git_cmd(root,"-c","protocol.version=2","fetch",
                       "--depth=1","--filter=blob:none","origin",meta["parent_commit"],
                       timeout=160):
            return "parent_commit_fetch_failed"
        if not git_cmd(root,"-c","core.hooksPath=/dev/null","checkout",
                       "--force","--detach","FETCH_HEAD",timeout=180):
            return "parent_commit_checkout_failed"
        if not git_cmd(root,"apply","--check","-",stdin=model_patch,timeout=40):
            return "model_patch_does_not_apply"
        if not git_cmd(root,"apply","-",stdin=model_patch,timeout=40):
            return "model_patch_apply_failed"
        if not git_cmd(root,"diff","--check",timeout=25):
            return "model_patch_whitespace_invalid"
        return "model_patch_applies_cleanly_NO_TESTS_RUN"


def run()->dict:
    try:
        sources=fetch_nvidia_fixed_two()
    except HTTPError as exc:
        raise RuntimeError("nvidia_source_http_" + str(exc.code)) from None
    try:
        meta=get_scale_match(sources)
    except HTTPError as exc:
        raise RuntimeError("scale_source_http_" + str(exc.code)) from None
    statuses=[]
    # Deterministic source order from original eight selected labels.
    for ident in sources:
        statuses.append(check_one(meta[ident],sources[ident]["model_patch"]))
    return {"cohort":"first two frozen source-eligible NVIDIA v2.0/sweagent rows 6..17",
            "source":"AweAI-Team/Scale-SWE",
            "attempted_source_checkouts":len(statuses),
            "patch_application_categories":dict(Counter(statuses)),
            "gold_source_patch_read":False,
            "raw_patch_or_repo_id_logged":False,
            "source_commands_or_tests_executed":False,
            "approved_training_examples":0,
            "model_training":False,
            "official_submission":False}


if __name__=="__main__":
    try:
        print("GEMMA_SCALE_SWE_TWO_MODEL_PATCH_APPLY="+json.dumps(run(),sort_keys=True),flush=True)
    except Exception as e:
        print("GEMMA_SCALE_SWE_TWO_MODEL_PATCH_BLOCKED="+json.dumps({
            "exception_class":type(e).__name__,
            "source_phase_status":str(e) if isinstance(e,RuntimeError) and
                str(e).startswith(("nvidia_source_http_","scale_source_http_")) else "unknown",
            "source_values_printed":False}),flush=True)
        raise SystemExit(1) from None
