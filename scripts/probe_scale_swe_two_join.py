"""Two fixed NVIDIA v2.0 Scale-SWE source joins via a DISTINCT dataset index.

No task IDs, raw prompt, patch, test code, source paths or URL can be printed.
The source dataset has 'parent_commit' and 'f2p_patch'/'f2p_script',
not SWE-rebench-V2's 'base_commit' and 'test_patch' schema.
"""
from __future__ import annotations
from collections import Counter
import json
import re
from urllib.error import HTTPError, URLError

from scripts.audit_open_swe_traces_metadata import get_json
from scripts.probe_external_source_join import collect_source

DATASET="AweAI-Team/Scale-SWE"


def verification(record: dict, source: dict) -> str:
    if record.get("instance_id")!=source.get("instance_id"):
        return "source_id_mismatch"
    owner=record.get("user"); repo=record.get("repo")
    if not isinstance(owner,str) or not isinstance(repo,str) or (
        f"{owner}/{repo}".casefold()!=str(source.get("repo","")).casefold()):
        return "source_repo_mismatch"
    parent=record.get("parent_commit")
    if not isinstance(parent,str) or not re.fullmatch("[a-f0-9]{40}",parent):
        return "missing_parent_commit"
    if not isinstance(record.get("problem_statement"),str) or not record["problem_statement"].strip():
        return "missing_original_issue"
    if not isinstance(record.get("image_url"),str) or not record["image_url"].strip():
        return "missing_image"
    f2p=record.get("f2p_patch")
    synth=record.get("f2p_script")
    if not any(isinstance(x,str) and x.strip() for x in (f2p,synth)):
        return "missing_reproduction_tests"
    checks=record.get("FAIL_TO_PASS")
    if not isinstance(checks,str) or not checks.strip():
        return "missing_test_names"
    try:
        parsed=json.loads(checks)
    except ValueError:
        return "test_names_not_json"
    if not isinstance(parsed,list) or not parsed:
        return "empty_test_names"
    return "source_commit_and_test_inputs_found_replay_pending"


def inspect_source(source:dict)->str:
    ident=source.get("instance_id")
    if not isinstance(ident,str) or not 4<=len(ident)<=150:
        return "invalid_id"
    query='"instance_id"=\''+ident.replace("'","''")+"\'"
    try:
        result=get_json("/filter",{"dataset":DATASET,"config":"default","split":"train",
                                  "where":query,"offset":0,"length":2})
    except HTTPError as exc:
        return "filter_http_"+str(exc.code) if exc.code in {400,401,403,404,422,429,500,502,503} else "filter_http_other"
    except (OSError,URLError,TimeoutError,ValueError):
        return "filter_service_error"
    if result.get("partial") is True:
        return "source_filter_partial_index"
    rows=result.get("rows")
    if not isinstance(rows,list):
        return "source_filter_no_rows_field"
    if not rows:
        return "not_found_or_incomplete_index"
    if len(rows)!=1 or not isinstance(rows[0],dict) or not isinstance(rows[0].get("row"),dict):
        return "source_filter_nonunique"
    return verification(rows[0]["row"],source)


def run()->dict:
    selected=collect_source()
    first_two=selected[:2]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(inspect_source,first_two))
    return {
        "source":"AweAI-Team/Scale-SWE",
        "cohort":"first two of eight NVIDIA v2.0/sweagent successful records, prespecified order",
        "queries":2,
        "match_categories":dict(Counter(results)),
        "candidate_source_replays":results.count("source_commit_and_test_inputs_found_replay_pending"),
        "reference_patch_used_as_training_target":False,
        "training_examples_exported":0,
        "patches_applied":0,
        "tests_run":0,
    }


if __name__=="__main__":
    print("GEMMA_SCALE_SWE_TWO_SOURCE_JOIN="+json.dumps(run(),sort_keys=True),flush=True)
