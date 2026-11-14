"""Materialize ONLY independently F2P-confirmed external repair demonstrations.

Training-only, external-source, issue -> NVIDIA model patch supervised pairs.
Never include reference (gold) patch, source tests, tool traces/feedback, or
Kaggle competition data. Repo grouping is deterministic and mutually disjoint.
No bytes written to public GitHub; outputs stay in ephemeral runner before a
PRIVATE Kaggle dataset upload subject to the caller's independent approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unicodedata

from scripts.check_frozen_scale_cohort_overlap import source_read_with_bounded_retry
from scripts.check_scale_swe_model_patch_apply import fetch_nvidia_fixed_eight,get_scale_match
from scripts.freeze_next_scale_swe_cohort import collect_new_cohort
from scripts.freeze_scale_swe_wave3 import collect_wave3
from scripts.check_three_scale_cohorts_train_split import (
    F2P_PROVEN_POSITIVE_INDICES,group_split,
)

MAX_ISSUE_CHARS=45_000
MAX_DIFF_CHARS=80_000
SALT="gemma31b-source-sft-prompt-contract-v0"
EXPECTED={"original":8,"next18":8,"wave3_30":12}
HOLDOUT_COUNT=3
POSITIVE_COUNT=19
TRAIN_COUNT=16
VALIDATION_COUNT=3

# Requirements-first code repair prompt (completion-only loss); never
# claim this demonstrates ADK native tool-use trajectories.
SYSTEM=("You are a software engineer repairing a Python repository. "
        "Given the issue description, produce a valid unified Git diff "
        "implementing the change. Output only the diff, with no commentary. "
        "Do not invent tests or claims of execution.\n")
FORMAT="Issue description:\n{issue}\n\nPatch:\n"


def forbidden_content(issue:str,diff:str)->str|None:
    if "\x00" in issue or "\x00" in diff:
        return "NUL"
    if any(unicodedata.category(c)=="Cs" for c in issue[:1000]+diff[:1000]):
        return "surrogate_codepoint"
    if not issue.strip() or not diff.strip():
        return "empty_pair"
    if len(issue)>MAX_ISSUE_CHARS:
        return "issue_over_bound"
    if len(diff)>MAX_DIFF_CHARS:
        return "diff_over_bound"
    if not diff.lstrip().startswith("diff --git a/"):
        return "not_unified_git_diff"
    if not re.search(r"^--- a/|^--- /dev/null",diff,flags=re.M) or not re.search(
        r"^\+\+\+ b/|^\+\+\+ /dev/null",diff,flags=re.M):
        return "diff_header_missing"
    if not re.search(r"^@@ .* @@",diff,flags=re.M):
        return "diff_hunk_missing"
    return None


def selected_sources()->list[dict]:
    cohorts={
      "original":source_read_with_bounded_retry(fetch_nvidia_fixed_eight),
      "next18":source_read_with_bounded_retry(collect_new_cohort),
      "wave3_30":source_read_with_bounded_retry(collect_wave3)
    }
    if any(len(rows)!=EXPECTED[name] for name,rows in cohorts.items()):
        raise ValueError("source count drift")
    all_ids=[]
    records=[]
    for name,collection in cohorts.items():
        all_ids += list(collection)
        for index,record in enumerate(collection.values()):
            if index not in F2P_PROVEN_POSITIVE_INDICES[name]:
                continue
            records.append({"cohort":name,"index":index,**record})
    if len(all_ids)!=28 or len(set(all_ids))!=28 or len(records)!=POSITIVE_COUNT:
        raise ValueError("source IDs or F2P proven labels drift")
    return records


def assemble()->tuple[list[dict],list[dict],dict]:
    chosen=selected_sources()
    by_id={row["instance_id"]:row for row in chosen}
    scale=get_scale_match(by_id)  # verified upstream parent SHA/issue/F2P, never gold.
    repos={r["source"]["repo"].casefold() for r in chosen}
    train_repos,valid_repos=group_split(repos,holdout_repos=HOLDOUT_COUNT)
    if train_repos & valid_repos:
        raise ValueError("repository groups overlap")
    train=[]
    valid=[]
    lens=[]
    for example in chosen:
        src=scale[example["instance_id"]]
        repo=example["source"]["repo"].casefold()
        if f'{src["user"]}/{src["repo"]}'.casefold()!=repo:
            raise ValueError("source repository mismatch")
        issue=src["problem_statement"]
        diff=example["model_patch"]
        if not isinstance(issue,str) or not isinstance(diff,str):
            raise ValueError("missing text")
        rejection=forbidden_content(issue,diff)
        if rejection:
            raise ValueError("bad training example:"+rejection)
        if not re.fullmatch(r"(?:[a-z0-9_.-]+)/(?:[a-z0-9_.-]+)",repo):
            raise ValueError("unsafe repo metadata")
        prompt=SYSTEM+FORMAT.format(issue=issue.strip())
        # Hashing source issue IDs here permits private repeatability without
        # showing exact task names in any public logs or reports.
        issue_tag=hashlib.sha256((SALT+"|"+example["instance_id"]).encode()).hexdigest()
        rec={
           "id_hash":issue_tag,
           "repo_hash":hashlib.sha256((SALT+"|"+repo).encode()).hexdigest(),
           "source_cohort":example["cohort"],
           "source_case_index":example["index"],
           "prompt":prompt,
           "completion":diff.rstrip()+"\n",
           "supervision_kind":"verified_external_model_patch_only",
           "source_F2P_proven_pass":True,
           "gold_patch_present":False,
           "tool_trace_present":False,
        }
        (train if repo in train_repos else valid).append(rec)
        lens.append((len(issue),len(diff)))
    if len(train)!=TRAIN_COUNT or len(valid)!=VALIDATION_COUNT:
        raise ValueError("repo-group assignment changed; abort")
    if ({r["repo_hash"] for r in train} & {r["repo_hash"] for r in valid}):
        raise ValueError("cross-split repository overlap")
    if len({r["id_hash"] for r in train+valid})!=POSITIVE_COUNT:
        raise ValueError("duplicate source task hash")
    meta={
       "schema_version":"gemma31b-source-patch-completion-v0",
       "data_source":"NVIDIA Open-SWE-Traces v2.0/sweagent + Scale-SWE",
       "original_fixed_rows":"6..17,18..29,30..53",
       "original_F2P_task_count":28,
       "eligible_verified_positive_count":POSITIVE_COUNT,
       "train_rows":len(train),"holdout_rows":len(valid),
       "train_repo_count":len(train_repos),"holdout_repo_count":len(valid_repos),
       "max_issue_chars":max(x[0] for x in lens),
       "max_patch_chars":max(x[1] for x in lens),
       "total_issue_chars":sum(x[0] for x in lens),
       "total_patch_chars":sum(x[1] for x in lens),
       "excluded_gold_patch":True,"excluded_external_tool_feedback":True,
       "proven_kaggle_hidden_disjoint":False,
       "adapter_trained":False,"competition_submitted":False,
    }
    return train,valid,meta


def write_private(out:Path)->dict:
    train,holdout,report=assemble()
    out.mkdir(parents=True,exist_ok=True)
    for name,records in (("train.jsonl",train),("holdout.jsonl",holdout)):
        filepath=out/name
        if filepath.exists():
            raise FileExistsError("refuse overwrite of private source split")
        with filepath.open("x",encoding="utf-8") as handle:
            for item in records:
                handle.write(json.dumps(item,ensure_ascii=False,sort_keys=True)+"\n")
        if len(filepath.read_text(encoding="utf-8").splitlines())!=len(records):
            raise ValueError("private source row count verification failed")
    if (out/"source_contract.json").exists():
        raise FileExistsError("private contract already exists")
    (out/"source_contract.json").write_text(json.dumps(report,sort_keys=True,indent=2),encoding="utf-8")
    return report


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-dir",type=Path,required=True)
    args=parser.parse_args()
    try:
        report=write_private(args.private_dir)
        print("GEMMA_PRIVATE_F2P_SFT_SHAPE="+json.dumps(report,sort_keys=True),flush=True)
        print("GEMMA_EXTERNAL_DATA_PRIVATE_RUNNER_ONLY=TRUE",flush=True)
    except Exception as exc:
        print("GEMMA_PRIVATE_F2P_SFT_BLOCKED="+json.dumps({
          "exception_class":type(exc).__name__,
          "restricted_error_class":"ValueError" if isinstance(exc,ValueError) else "other",
          "raw_data_logged":False}),flush=True)
        raise SystemExit(1) from None
