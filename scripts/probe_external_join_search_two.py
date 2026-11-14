"""Two-task alternate public search-path diagnostic for SWE-rebench source joining.

No source prompts, task IDs, reference patches, tests or URLs enter logs.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import json
import re
from urllib.error import HTTPError, URLError

from scripts.audit_open_swe_traces_metadata import get_json
from scripts.probe_external_source_join import SOURCE, collect_source


def search_one(source: dict) -> str:
    ident=source.get("instance_id")
    if not isinstance(ident,str) or not ident or len(ident)>150:
        return "bad_task_id"
    try:
        payload=get_json("/search", {
            "dataset":SOURCE, "config":"default", "split":"train",
            "query": ident, "offset":0, "length":10})
    except HTTPError as exc:
        return "search_http_"+str(exc.code) if exc.code in {400,404,422,500,501,502,503} else "search_http_other"
    except (TimeoutError, OSError, URLError, ValueError):
        return "search_unavailable"
    if payload.get("partial") is True:
        return "search_partial_index"
    items=payload.get("rows")
    if not isinstance(items,list):
        return "invalid_search_response"
    match=[x["row"] for x in items if isinstance(x,dict) and
           isinstance(x.get("row"),dict) and x["row"].get("instance_id")==ident]
    if not match:
        return "no_exact_search_match"
    if len(match)!=1:
        return "multiple_search_matches"
    row=match[0]
    if str(row.get("repo","")).lower()!=str(source.get("repo","")).lower():
        return "repo_mismatch"
    if str(row.get("license","")).lower()!=str(source.get("license","")).lower():
        return "license_mismatch"
    if not isinstance(row.get("base_commit"),str) or not re.fullmatch(r"[0-9a-f]{40}",row["base_commit"]):
        return "base_commit_absent"
    if not isinstance(row.get("FAIL_TO_PASS"),list) or not row["FAIL_TO_PASS"]:
        return "tests_absent"
    if not isinstance(row.get("test_patch"),str) or not row["test_patch"]:
        return "test_patch_absent"
    return "exact_source_commit_and_tests_found_no_replay"


def run()->dict:
    # Two fixed first candidate IDs only, selected before any API feedback.
    sources=collect_source()[:2]
    if len(sources)!=2:
        raise RuntimeError("missing two prescribed candidates")
    with ThreadPoolExecutor(max_workers=2) as exe:
        statuses=list(exe.map(search_one,sources))
    return {"requested":2,"source":"nebius/SWE-rebench-V2",
            "diagnostic":"public /search alternative to failed /filter HTTP 500",
            "result_counts":dict(Counter(statuses)),
            "matched":statuses.count("exact_source_commit_and_tests_found_no_replay"),
            "models_trained":0,"task_data_exported":False,"patches_replayed":0}


if __name__=="__main__":
    print("GEMMA_SOURCE_JOIN_SEARCH_TWO_ONLY="+json.dumps(run(),sort_keys=True),flush=True)
