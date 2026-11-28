"""Read-only action recovery analysis. No raw trace output or command execution."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from scripts.audit_four_arm_evidence_20261127 import load, unwrap, norm
from scripts.render_fork_v1_20261127 import assess as assess_fork, RESULT as FORK
from scripts.render_multisurface_clean17_20261126 import assess as assess_multi, RESULT as MULTI


def status(observation):
    vals = unwrap(observation)
    if len(vals) != 1:
        return "unknown"
    v = vals[0]
    if v.get("status") == "error":
        return "error"
    if v.get("status") == "ok":
        return "ok"
    return "unknown"


def audit(trace):
    # Only a single native edit_file call per step allows response attribution.
    # Requests, not physical scorer calls; repeated trace entries may be duplicates.
    events = []
    for index, step in enumerate(trace.get("steps", [])):
        calls = step.get("tool_calls") or []
        if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
            continue
        call = calls[0]
        if call.get("function_name") != "edit_file":
            continue
        args = call.get("arguments")
        if not isinstance(args, dict):
            continue
        path = norm(args.get("filepath"))
        if not path:
            continue
        events.append((index, path, json.dumps(args, sort_keys=True), status(step.get("observation"))))
    c = Counter(episodes=1, native_edit_observed=int(bool(events)))
    errors = [e for e in events if e[3] == "error"]
    oks = [e for e in events if e[3] == "ok"]
    unknown = [e for e in events if e[3] == "unknown"]
    c["edit_ok_episode"] = int(bool(oks))
    c["edit_error_episode"] = int(bool(errors))
    c["edit_unknown_episode"] = int(bool(unknown))
    c["error_then_same_path_ok_episode"] = int(any(j>i and p==q for i,p,_,_ in errors for j,q,_,_ in oks))
    c["error_without_later_same_path_ok_episode"] = int(any(not any(j>i and p==q for j,q,_,_ in oks) for i,p,_,_ in errors))
    c["identical_args_error_repeated_episode"] = int(any(a==b for k,(_,_,a,_) in enumerate(errors) for _,_,b,_ in errors[k+1:]))
    c["error_and_no_observed_ok_episode"] = int(bool(errors) and not oks)
    return c


def run(fork, prior):
    groups = defaultdict(list)
    for root, file, assess, arms in [
        (fork,FORK,assess_fork,("champion_5min","fork_5min")),
        (prior,MULTI,assess_multi,("champion_5min","multisurface_5min"))
    ]:
        rows=load(root,file,assess)
        traces={}
        for p in root.rglob("trace_*.json"):
            key=(p.stem.removeprefix("trace_"),arms[int("public-prompt" in p.relative_to(root).parts)])
            if key not in rows:continue
            if key in traces:raise ValueError("ambiguous trace")
            traces[key]=p
        assert set(traces)==set(rows)
        for key,row in rows.items():
            counts=audit(json.loads(traces[key].read_text()))
            counts["nonempty_final_patch"]=int(bool(row["has_patch"]))
            counts["error_and_empty_patch"]=int(bool(counts["edit_error_episode"]) and not row["has_patch"])
            groups[key[0]].append((bool(row["resolved"]),counts))
    assert len(groups)==17 and all(len(v)==4 for v in groups.values())
    totals=defaultdict(Counter)
    for values in groups.values():
        n=sum(ok for ok,_ in values)
        label="always_pass" if n==4 else "always_fail" if n==0 else "mixed"
        totals[label]["tasks"]+=1
        for _,c in values:totals[label].update(c)
    return {"groups":totals,"episodes":68,"tasks":17,"raw_export":False,"model_inference":False,
            "same_path_later_ok_does_not_prove_correct_repair":True,
            "opaque_shell_and_multi_tool_steps_not_attributed":True,
            "repeated_args_may_be_duplicate_trace_entries":True}


def smoke():
    def edit(p, state, old="a"):
        return {"tool_calls":[{"function_name":"edit_file","arguments":{"filepath":p,"old_string":old}}],
                "observation":{"results":[{"content":json.dumps({"status":state})}]}}
    c=audit({"steps":[edit("x.py","error"),edit("x.py","error"),edit("x.py","ok","b"),edit("y.py","error")]})
    assert c["edit_error_episode"]==1 and c["edit_ok_episode"]==1
    assert c["error_then_same_path_ok_episode"]==1
    assert c["error_without_later_same_path_ok_episode"]==1
    assert c["identical_args_error_repeated_episode"]==1
    assert c["error_and_no_observed_ok_episode"]==0
    assert audit({"steps":[edit("x.py","error")]})["error_and_no_observed_ok_episode"]==1
    assert audit({"steps":[edit("x.py","weird")]})["edit_unknown_episode"]==1


if __name__=="__main__":
    import sys
    smoke()
    print("ACTION_RECOVERY="+json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2])),sort_keys=True),flush=True)
