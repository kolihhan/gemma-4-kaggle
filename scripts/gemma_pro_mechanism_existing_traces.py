"""Decision-relevant paired agent failure mechanism study from *existing* private traces.

No raw issue text, commands, patches, prompt or grader details are published.
This audit distinguishes stage opportunity signals; it does NOT assign causal F1-F9
failure labels or estimate hidden Kaggle score.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from scripts.audit_paired_31b_feedback_v2 import audit

ARMS=("v2_5min","public_prompt_5min")

def summarize(report:dict)->dict:
    rows=report.get("tasks")
    if not isinstance(rows,list) or len(rows)!=6:
        raise ValueError("full_6_eval_denominator_required")
    ids={x.get("instance_id") for x in rows}
    if len(ids)!=3 or not all(isinstance(x,str) and x for x in ids):
        raise ValueError("three_real_matched_ids_required")
    for id_ in ids:
        if {x.get("arm") for x in rows if x.get("instance_id")==id_}!=set(ARMS):
            raise ValueError("missing_matched_arm")
    result={}
    for arm in ARMS:
        xs=[x for x in rows if x["arm"]==arm]
        observed=[x for x in xs if x.get("trace_found") is True]
        counts=Counter()
        for x in observed:
            edit=x.get("total_edit_actions",0)
            tests=x.get("explicit_or_inline_tests",0)
            cnt=x.get("recorded_action_count")
            first=x.get("first_edit_action")
            if type(edit)!=int or type(tests)!=int or type(cnt)!=int:
                raise ValueError("invalid_audit_counts")
            counts["observed_traces"]+=1
            counts["ever_edited"]+=int(edit>0)
            counts["no_edit"]+=int(edit==0)
            counts["any_recognized_test"]+=int(tests>0)
            counts["edited_but_no_recognized_test"]+=int(edit>0 and tests==0)
            counts["test_after_edit"]+=int(x.get("tests_after_first_edit",0)>0)
            counts["late_first_edit_over_half_actions"]+=int(
                isinstance(first,int) and cnt>0 and (first-1)*2>=cnt)
            counts["observed_failed_test"]+=int(
                x.get("tests_with_structured_exit",{}).get("nonzero",0)>0)
            counts["failed_test_without_observed_reedit"]+=int(
                x.get("tests_with_structured_exit",{}).get("nonzero",0)>0
                and x.get("nonzero_test_then_edit",0)==0)
            counts["failed_command_after_last_edit"]+=int(
                x.get("nonzero_commands_after_last_edit",0)>0)
            counts["opaque_command"]+=int(x.get("unclassified_opaque_commands",0)>0)
        counts["resolved"]=sum(x.get("resolved") is True for x in xs)
        counts["incomplete_or_missing_traces"]=3-len(observed)
        result[arm]=dict(sorted(counts.items()))
    # Never conclude correct root cause from missing command structure.
    return {
        "source":"previously_used_3_matched_public_dev_issues",
        "model_task_evaluations":6,
        "independent_holdout":False,
        "paired_resolved_difference":result["public_prompt_5min"]["resolved"]-result["v2_5min"]["resolved"],
        "by_arm":result,
        "competing_explanations":{
          "H1_locate_budget":"Agent fails to reach a code edit early enough; predicts many no/late edits",
          "H2_understand_or_edit":"Edits occur but independent grader still rejects; predicts patches with no resolution",
          "H3_test_feedback":"After editing, there are few usable tests or no repair after observed failures",
        },
        "interpretation_limit":"Early edit alone or a recognized test call does not establish relevance, correctness, actual test execution or root cause. Missing trace is not zero actions.",
        "new_gpu":False,"new_training":False,"new_competition_submission":False,
    }

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    x=summarize(audit(a.root))
    print("GEMMA_PRO_MECHANISM_EXISTING_TRACES="+json.dumps(x,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
