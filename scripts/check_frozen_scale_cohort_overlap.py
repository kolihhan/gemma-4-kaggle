"""Source-only check: strict task and repo duplicates across two frozen batches.

Does not download or reveal issue text, model/gold patch, task IDs or repo names.
Does not equate repo independence with benchmark-independence; only local audit.
"""
from __future__ import annotations
from collections import Counter
import json

from scripts.check_scale_swe_model_patch_apply import fetch_nvidia_fixed_eight
from scripts.freeze_next_scale_swe_cohort import collect_new_cohort


def audit()->dict:
    old=fetch_nvidia_fixed_eight()
    new=collect_new_cohort()
    if len(old)!=8 or len(new)!=8:
        raise ValueError("frozen source denominators changed")
    shared_ids=set(old)&set(new)
    old_repos={str(x["source"]["repo"]).lower() for x in old.values()}
    new_repos={str(x["source"]["repo"]).lower() for x in new.values()}
    joined_repos=[str(x["source"]["repo"]).lower() for x in list(old.values())+list(new.values())]
    return {
      "source":"NVIDIA Open-SWE-Traces v2.0 sweagent, rows 6..29",
      "frozen_source_success_rows":16,
      "distinct_task_ids":len(set(old)|set(new)),
      "cross_cohort_task_overlap_count":len(shared_ids),
      "distinct_repo_count":len(set(joined_repos)),
      "cross_cohort_repo_overlap_count":len(old_repos & new_repos),
      "repo_repeated_source_row_count":16-len(set(joined_repos)),
      "old_public_eval_repo_exclusion_gate_reused":True,
      "globally_disjoint_from_all_Kaggle_hidden_tasks_proven":False,
      "source_ids_or_repo_names_logged":False,
      "F2P_verified_training_examples_promoted_here":0,
      "training_performed":False
    }


if __name__=="__main__":
    try:
        print("GEMMA_TWO_COHORT_DISJOINTNESS="+json.dumps(audit(),sort_keys=True),flush=True)
    except Exception as exc:
        print("GEMMA_TWO_COHORT_DISJOINTNESS_BLOCKED="+json.dumps({
            "exception_class":type(exc).__name__,
            "sensitive_source_ids_logged":False}),flush=True)
        raise SystemExit(1) from None
