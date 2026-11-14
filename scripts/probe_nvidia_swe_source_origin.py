"""Origin-only diagnostic on eight source-labelled NVIDIA successful v2.0 tasks.

Expose only recognized dataset origin category, never freeform hf_dataset_name,
row ID, repo, prompt, patch or raw test material.
"""
from __future__ import annotations
from collections import Counter
import json
from scripts.audit_open_swe_traces_metadata import DATASET, get_json, sample_grade


def recognized_origin(value: object) -> str:
    if not isinstance(value, str):
        return "missing"
    val=value.casefold().replace("_","-")
    if "scale-swe" in val:
        return "AweAI-Team/Scale-SWE"
    if "swe-rebench-v2" in val or "swe-rebench" in val:
        return "nebius/SWE-rebench-V2"
    return "unknown_or_other"


def probe()->dict:
    seen=Counter()
    with_origin=Counter()
    for offset in (6,12):
        response=get_json("/rows",{"dataset":DATASET,"config":"v2.0",
                                   "split":"sweagent","offset":offset,"length":6})
        rows=response.get("rows",[])
        if not isinstance(rows,list) or len(rows)!=6:
            raise RuntimeError("fixed cohort unavailable")
        for wrapped in rows:
            row=wrapped.get("row",{}) if isinstance(wrapped,dict) else {}
            if sample_grade(row)!="candidate_for_private_deep_audit":
                continue
            seen[recognized_origin(row.get("hf_dataset_name"))]+=1
            with_origin["field_present"]+=int("hf_dataset_name" in row)
    if sum(seen.values())!=8:
        raise ValueError("original eligible count drift")
    return {"cohort":"NVIDIA v2.0/sweagent rows 6..17",
            "eligible_success_rows":8,
            "origin_counts":dict(seen),
            "source_name_field_count":with_origin["field_present"],
            "task_ids_exported":False,
            "raw_hf_dataset_field_exported":False,
            "model_or_training_started":False}


if __name__=="__main__":
    print("GEMMA_NVIDIA_SWE_SOURCE_ORIGIN="+json.dumps(probe(),sort_keys=True),flush=True)
