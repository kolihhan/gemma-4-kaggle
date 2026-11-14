"""Freeze next source-only NVIDIA cohort without looking at repair outcomes.

Public Open-SWE-Traces v2.0/sweagent rows 18..29, in source order,
12 total. From these, accept exactly the first 8 source success rows with
same existing sample_grade gate AND verified Scale-SWE hf_dataset_name.
Never output issue IDs, patches, source repos, tests or model tool messages.
"""
from __future__ import annotations

from collections import Counter
import json

from scripts.audit_open_swe_traces_metadata import DATASET, get_json, sample_grade
from scripts.probe_nvidia_swe_source_origin import recognized_origin

OFFSETS=(18,24)
EXPECTED_SOURCE_SUCCESS=8
SOURCE="AweAI-Team/Scale-SWE"


def collect_new_cohort()->dict:
    count=Counter()
    qualified=[]
    selected_ids=set()
    for offset in OFFSETS:
        payload=get_json("/rows",{"dataset":DATASET,"config":"v2.0",
                                  "split":"sweagent","offset":offset,"length":6})
        records=payload.get("rows")
        if not isinstance(records,list) or len(records)!=6:
            raise ValueError("fixed six-row source viewer slice incomplete")
        for wrapper in records:
            row=wrapper.get("row",{}) if isinstance(wrapper,dict) else {}
            category=sample_grade(row)
            count[category]+=1
            if category!="candidate_for_private_deep_audit":
                continue
            origin=recognized_origin(row.get("hf_dataset_name"))
            count["source_origin_"+origin]+=1
            if origin!=SOURCE:
                continue
            ident=row.get("instance_id")
            if not isinstance(ident,str) or not 4<=len(ident)<=150:
                raise ValueError("missing source task identity")
            if ident in selected_ids:
                raise ValueError("duplicate source identity")
            selected_ids.add(ident)
            meta=row.get("metadata")
            patch_obj=meta.get("model_patch") if isinstance(meta,dict) else None
            patch=patch_obj.get("patch") if isinstance(patch_obj,dict) else patch_obj
            if not isinstance(patch,str) or not patch.startswith("diff --git "):
                raise ValueError("source success patch missing")
            qualified.append({
                "instance_id":ident,
                "source":{k:row.get(k) for k in ("instance_id","repo","license")},
                "model_patch":patch,
            })
    if len(qualified)!=EXPECTED_SOURCE_SUCCESS:
        raise ValueError("next cohort fixed denominator must be exactly eight")
    return {x["instance_id"]:x for x in qualified}


def counts_only()->dict:
    entries=collect_new_cohort()
    return {
        "cohort":"NVIDIA v2.0 sweagent source offsets 18..29",
        "fixed_count":12,"eligible_source_success_count":len(entries),
        "unique_source_ids":len(set(entries)),
        "source_origin":"Scale-SWE only",
        "training_examples_approved":0,
        "f2p_tests_executed":0,
        "raw_data_exported":False,
        "model_training_started":False
    }


if __name__=="__main__":
    try:
        print("GEMMA_NEW_SOURCE_COHORT_GATE="+json.dumps(counts_only(),sort_keys=True),flush=True)
    except Exception as exc:
        print("GEMMA_NEW_SOURCE_COHORT_BLOCKED="+json.dumps({
            "exception_class":type(exc).__name__,
            "raw_source_data_exposed":False}),flush=True)
        raise SystemExit(1) from None
