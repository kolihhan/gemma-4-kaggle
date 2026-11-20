"""Classify observable feedback in EXISTING 31B paired private traces.
No model GPU, no raw private trace exports, no grader text exposed to agent.
"""
import argparse,json,re
from pathlib import Path
from scripts.audit_pro_v3r_real31b_uptake_20261115 import validate,trace_path,ARMS
from scripts.audit_paired_31b_feedback_v2 import command_class,observation_exit

def classify(text):
    s=text if isinstance(text,str) else json.dumps(text) if isinstance(text,dict) else ""
    if re.search(r"\bFAILED\b.{0,100}(?:test_|\.py::)|\bAssertionError\b",s,re.I|re.S):
        return "assertion_or_test_failure_hint"
    if re.search(r"\b(?:ModuleNotFoundError|ImportError)\b",s):
        return "dependency_or_import_hint"
    if re.search(r"\b(?:SyntaxError|IndentationError)\b",s):
        return "syntax_hint"
    if re.search(r"\b(?:command not found|No such file or directory)\b",s,re.I):
        return "shell_path_hint"
    return "unclassified"

def summarize(trace):
    events=[]
    for step in trace.get("steps",[]):
        if not isinstance(step,dict) or not isinstance(step.get("tool_calls"),list):continue
        calls=step["tool_calls"]
        for call in calls:
            if not isinstance(call,dict):continue
            fn=call.get("function_name")
            if fn in ("edit_file","write_file"):events.append(("edit",False,"unknown",""))
            elif fn=="run_command":
                args=call.get("arguments",{})
                cmd=args.get("command","") if isinstance(args,dict) else ""
                cmd=cmd if isinstance(cmd,str) else ""
                obs=step.get("observation")
                body=obs.get("content","") if isinstance(obs,dict) else ""
                events.append((command_class(cmd),bool(re.search(
                    r"\b(?:pytest|unittest|tox|nox|assert)\b",cmd,re.I)),
                    observation_exit(obs,len(calls)>1),classify(body)))
            elif fn=="submit_patch":events.append(("submit",False,"unknown",""))
            else:events.append(("other_tool",False,"unknown",""))
    edits=[i for i,x in enumerate(events) if x[0]=="edit"]
    after=[(i,x) for i,x in enumerate(events) if edits and i>edits[0]]
    commands=[(i,x) for i,x in after if x[0] not in ("edit","submit","other_tool")]
    return {
        "has_edit":bool(edits),
        "post_edit_explicit_test":sum(x[0] in ("explicit_test","inline_assert") for i,x in commands),
        "post_edit_lexical_test_hint":sum(x[1] for i,x in commands),
        "post_edit_nonzero_exit":sum(x[2]=="nonzero" for i,x in commands),
        "post_edit_assert_or_pytest_fail_hint":sum(x[3]=="assertion_or_test_failure_hint" for i,x in commands),
        "post_edit_import_hint":sum(x[3]=="dependency_or_import_hint" for i,x in commands),
        "post_edit_syntax_hint":sum(x[3]=="syntax_hint" for i,x in commands),
        "post_edit_opaque":sum(x[0] in ("opaque_python","other","unavailable") for i,x in commands),
        "test_failure_hint_followed_by_reedit":sum(
            x[3]=="assertion_or_test_failure_hint" and any(j>i for j in edits)
            for i,x in commands),
    }

def run(root):
    d=json.loads((root/"paired_prompt_v2_31b_results.json").read_text())
    rows=validate(d);out={}
    for arm in ARMS:
        cohort=[r for r in rows if r["arm"]==arm]
        assert len(cohort)==3
        vals=[]
        for row in cohort:
            t=trace_path(root,arm,row["instance_id"])
            if t is None:raise RuntimeError("MISSING_REAL_FROZEN_TRACE")
            vals.append(summarize(json.loads(t.read_text())))
        out[arm]={
            "tasks":3,"grader_resolved":sum(r["resolved"] for r in cohort),
            "true_scorer_tool_calls":sum(int(r.get("tool_calls") or 0) for r in cohort),
            "task_presence":{k:sum(bool(v[k]) for v in vals) for k in vals[0]},
            "trace_event_totals":{k:sum(v[k] for v in vals) for k in vals[0] if k!="has_edit"}
        }
    return {"source":"EXISTING_FROZEN_REAL_31B_PUBLIC_DEV_PAIRED",
            "by_arm":out,"lexical_hints_are_not_verified_relevant_tests":True,
            "opaque_commands_are_unknown_not_no_test":True,
            "no_new_gpu_or_submission":True,"no_raw_private_content_exported":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path);p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert classify("AssertionError")=="assertion_or_test_failure_hint"
        assert classify("ModuleNotFoundError: foo")=="dependency_or_import_hint"
        print("GEMMA31B_REAL_TRACE_AUDITOR_UNIT=PASS")
    else:
        if not a.input:p.error("--input required")
        print("GEMMA31B_REAL_FEEDBACK_SIGNATURES="+json.dumps(run(a.input),sort_keys=True))
