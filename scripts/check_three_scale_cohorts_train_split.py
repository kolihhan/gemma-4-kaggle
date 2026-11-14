"""Pre-training repo-group disjointness for three frozen Scale-SWE cohorts.

Input F2P pass indices are anchored to authenticated GitHub Actions' completed
Docker logs (not raw provider 'resolved' flags). This tool does not train or
materialize source prompts, model patches or gold references.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import hashlib
import json

from scripts.check_frozen_scale_cohort_overlap import source_read_with_bounded_retry
from scripts.check_scale_swe_model_patch_apply import fetch_nvidia_fixed_eight
from scripts.freeze_next_scale_swe_cohort import collect_new_cohort
from scripts.freeze_scale_swe_wave3 import collect_wave3

F2P_PROVEN_POSITIVE_INDICES={
    "original":(0,2,3,5,6,7),
    "next18":(0,2,3,6,7),
    "wave3_30":(1,3,4,5,6,7,9,10),
}
SOURCE_RUNS={
    "original":(43599380451,43600254972,43600411080),
    "next18":(43602635913,),
    "wave3_30":(43604539933,),
}
SALT="gemma-31b-private-source-repair-repo-disjoint-v0"


def group_split(groups:set[str],holdout_repos:int=3)->tuple[set[str],set[str]]:
    if len(groups)<=holdout_repos:
        raise ValueError("not enough repositories for grouped split")
    order=sorted(groups,key=lambda repo:(hashlib.sha256(
        (SALT+"|"+repo).encode()).hexdigest(),repo))
    holdout=set(order[:holdout_repos])
    train=set(order[holdout_repos:])
    if holdout & train or train|holdout!=groups:
        raise ValueError("group partition invalid")
    return train,holdout


def check()->dict:
    collections={
        "original":source_read_with_bounded_retry(fetch_nvidia_fixed_eight),
        "next18":source_read_with_bounded_retry(collect_new_cohort),
        "wave3_30":source_read_with_bounded_retry(collect_wave3)
    }
    expected={"original":8,"next18":8,"wave3_30":12}
    if any(len(collections[k])!=expected[k] for k in expected):
        raise ValueError("frozen cohort size drift")
    issues=[]
    repo_by_issue={}
    train_eligible=[]
    for name,entries in collections.items():
        records=list(entries.values())
        positives=F2P_PROVEN_POSITIVE_INDICES[name]
        if len(positives)!=len(set(positives)):
            raise ValueError("duplicate proven index")
        for i,record in enumerate(records):
            id_=record["instance_id"]
            repo=record["source"]["repo"]
            if not isinstance(repo,str) or "/" not in repo:
                raise ValueError("missing source repo")
            issues.append(id_)
            repo_by_issue[id_]=repo.casefold()
            if i in positives:
                train_eligible.append(id_)
    if len(set(issues))!=28:
        raise ValueError("cross-wave duplicate issue IDs; cannot claim 28")
    if len(train_eligible)!=19 or len(set(train_eligible))!=19:
        raise ValueError("proven-positive cohort drift")
    groups={repo_by_issue[id_] for id_ in train_eligible}
    train_repos,val_repos=group_split(groups)
    return {
        "frozen_source_task_count":len(issues),
        "distinct_source_task_ids":len(set(issues)),
        "all_source_repo_count":len(set(repo_by_issue.values())),
        "F2P_proven_positive_task_count":len(train_eligible),
        "F2P_positive_distinct_repo_count":len(groups),
        "source_train_repos":len(train_repos),
        "source_validation_repos":len(val_repos),
        "source_train_positive_tasks":sum(repo_by_issue[i] in train_repos for i in train_eligible),
        "source_validation_positive_tasks":sum(repo_by_issue[i] in val_repos for i in train_eligible),
        "cross_split_source_repo_overlap":len(train_repos & val_repos),
        "model_train_examples_serialized":0,
        "hidden_Kaggle_independence_proven":False,
        "raw_ids_repos_patches_prompts_exported":False,
        "competition_submission_created":False,
    }


if __name__=="__main__":
    try:
        print("GEMMA_THREE_FROZEN_REPO_SPLIT="+json.dumps(check(),sort_keys=True),flush=True)
    except Exception as exc:
        print("GEMMA_THREE_FROZEN_REPO_SPLIT_BLOCKED="+json.dumps({
            "exception_class":type(exc).__name__,
            "source_contents_logged":False}),flush=True)
        raise SystemExit(1) from None
