"""Third frozen training-source cohort, prespecified NVIDIA viewer rows 30..53.

Select first 12 strictly admissible successful Scale-SWE tasks IN SOURCE ORDER
without looking at their F2P test outcomes. No source text, patches, repo IDs,
model/tool traces or task IDs are persisted or logged. Distinct issue IDs are
required within the new batch; cross-wave checks happen separately.
"""
from __future__ import annotations
from collections import Counter
import json
import time
from urllib.error import HTTPError, URLError

from scripts.audit_open_swe_traces_metadata import DATASET,get_json,sample_grade
from scripts.probe_nvidia_swe_source_origin import recognized_origin

OFFSETS=(30,36,42,48)
ROWS_PER_SLICE=6
TAKE=12
ORIGIN="AweAI-Team/Scale-SWE"


def page(offset:int)->list[dict]:
    if offset not in OFFSETS:
        raise ValueError("offset outside fixed cohort")
    for attempt in range(3):
        try:
            payload=get_json("/rows",{
                "dataset":DATASET,"config":"v2.0","split":"sweagent",
                "offset":offset,"length":ROWS_PER_SLICE})
            rows=payload.get("rows")
            if not isinstance(rows,list) or len(rows)!=ROWS_PER_SLICE:
                raise ValueError("incomplete source page")
            return rows
        except HTTPError as exc:
            if exc.code not in {429,500,502,503,504} or attempt==2:
                raise
        except (URLError,TimeoutError):
            if attempt==2:
                raise
        time.sleep(2*(attempt+1))
    raise RuntimeError("source viewer unavailable")


def collect_wave3()->dict:
    selected=[]
    ids=set()
    outcomes=Counter()
    for offset in OFFSETS:
        for wrapped in page(offset):
            r=wrapped.get("row",{}) if isinstance(wrapped,dict) else {}
            gate=sample_grade(r)
            outcomes[gate]+=1
            if gate!="candidate_for_private_deep_audit":
                continue
            if recognized_origin(r.get("hf_dataset_name"))!=ORIGIN:
                outcomes["foreign_origin"]+=1
                continue
            taskid=r.get("instance_id")
            if not isinstance(taskid,str) or not 4<=len(taskid)<=150:
                raise ValueError("bad source ID")
            if taskid in ids:
                raise ValueError("duplicate ID in frozen source window")
            ids.add(taskid)
            meta=r.get("metadata")
            candidate=meta.get("model_patch") if isinstance(meta,dict) else None
            patch=candidate.get("patch") if isinstance(candidate,dict) else candidate
            if not isinstance(patch,str) or not patch.startswith("diff --git "):
                raise ValueError("missing model patch")
            selected.append({
                "instance_id":taskid,
                "source":{k:r.get(k) for k in ("instance_id","repo","license")},
                "model_patch":patch
            })
    if len(selected)<TAKE:
        raise ValueError("not enough admitted candidates in frozen 24-row window")
    # Select the exact predeclared first 12, not a success-aware cherry-pick.
    return {r["instance_id"]:r for r in selected[:TAKE]}


def summary()->dict:
    selected=collect_wave3()
    return {
        "source": "nvidia/Open-SWE-Traces v2.0/sweagent",
        "fixed_row_window":"30..53 inclusive",
        "selected_first_12_admissible":len(selected),
        "source_origin":"AweAI-Team/Scale-SWE",
        "F2P_results_inspected_when_selecting":False,
        "task_ids_or_patches_exported":False,
        "gold_training_targets":0,
        "approved_SFT_examples":0
    }


if __name__=="__main__":
    try:
        print("GEMMA_WAVE3_SOURCE_FREEZE="+json.dumps(summary(),sort_keys=True),flush=True)
    except Exception as exc:
        print("GEMMA_WAVE3_FREEZE_BLOCKED="+json.dumps({
            "exception_class":type(exc).__name__,
            "source_data_exposed":False}),flush=True)
        raise SystemExit(1) from None
