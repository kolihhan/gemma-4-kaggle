"""CPU-only retrospective: all four arms, no raw export, no semantic oracle."""
import argparse,json,re,shlex
from pathlib import Path
from collections import Counter,defaultdict
from scripts.audit_gemma31b_semantic_gap_private_20261120 import diff_evidence,source
from scripts.audit_requirements_coverage_private_20261126 import read_selected_tasks,spec_evidence
from scripts.audit_paired_31b_feedback_v2 import _classify_tokens
from scripts.render_fork_v1_20261127 import assess as assess_fork,RESULT as FORK
from scripts.render_multisurface_clean17_20261126 import assess as assess_multi,RESULT as MULTI

def commands(cmd,depth=0):
    if not isinstance(cmd,str) or depth>4:return []
    try:
        lex=shlex.shlex(cmd,posix=True,punctuation_chars=";&|")
        lex.whitespace_split=True;lex.commenters=""
        ts=list(lex)
    except ValueError:return []
    seg=[];out=[]
    for t in ts:
        if t in (";","&&","||","|","&"):
            if seg:out.append(seg)
            seg=[]
        else:seg.append(t)
    if seg:out.append(seg)
    expanded=[]
    for seg in out:
        while seg and re.fullmatch(r"[A-Za-z_]\w*=.*",seg[0]):seg=seg[1:]
        if seg and seg[0].split("/")[-1]=="env":seg=seg[1:]
        while seg and re.fullmatch(r"[A-Za-z_]\w*=.*",seg[0]):seg=seg[1:]
        if seg and seg[0].split("/")[-1]=="timeout":
            seg=seg[1:]
            while seg and seg[0].startswith("-"):
                opt=seg.pop(0)
                if opt in ("-k","--kill-after","-s","--signal") and seg:seg.pop(0)
            if seg and re.fullmatch(r"\d+(?:\.\d+)?[smhd]?",seg[0]):seg=seg[1:]
            else:continue
        if len(seg)>=3 and seg[0].split("/")[-1] in ("sh","bash") and seg[1] in ("-c","-lc"):
            expanded.extend(commands(seg[2],depth+1))
        elif seg:expanded.append(seg)
    return expanded

def categories(cmd):
    return {_classify_tokens(s) for s in commands(cmd)}

def unwrap(o,depth=0):
    if depth>8:return []
    if isinstance(o,str):
        try:return unwrap(json.loads(o),depth+1)
        except (ValueError,TypeError):return []
    if isinstance(o,list):
        return [v for item in o for v in unwrap(item,depth+1)]
    if not isinstance(o,dict):return []
    if "status" in o or "exit_code" in o:return [o]
    return [v for k in ("results","content","text","result","response") if k in o for v in unwrap(o[k],depth+1)]

def response(o):
    vals=unwrap(o)
    if len(vals)!=1:return "unknown",None
    v=vals[0];d=v.get("details")
    if not isinstance(d,dict):d={}
    e=v.get("exit_code",d.get("exit_code"))
    if type(e) is int:return ("zero" if e==0 else "nonzero"),e
    typ=v.get("error_type")
    if typ=="TimeoutExceeded":return "timeout",None
    if v.get("status")=="error":return "tool_error",None
    return "unknown",None

def norm(x):
    if not isinstance(x,str):return ""
    x=x.removeprefix("/workspace/").removeprefix("./")
    return x if not x.startswith("/") and ".." not in Path(x).parts else ""

def trace_stats(trace,gold):
    c=Counter();read=set();edit=set();mentioned=set()
    tests=[];edit_idx=[];seen_requests=set();observations=[]
    for i,step in enumerate(trace.get("steps",[])):
        calls=step.get("tool_calls") or []
        if not isinstance(calls,list):continue
        for call in calls:
            if not isinstance(call,dict):continue
            n=call.get("function_name");a=call.get("arguments")
            if not isinstance(a,dict):continue
            if n=="read_file":
                p=norm(a.get("filepath"));read.add(p)
            if n in ("edit_file","write_file"):
                p=norm(a.get("filepath"));edit.add(p);edit_idx.append(i)
            if n!="run_command":continue
            cmd=a.get("command")
            if not isinstance(cmd,str):continue
            for p in gold:
                if re.search(r"(?<![\w./-])(?:/workspace/|\./)?"+re.escape(p)+r"(?![\w./-])",cmd):mentioned.add(p)
            k=categories(cmd)
            if "source_mutation" in k:edit_idx.append(i)
            if not k.intersection({"explicit_test","inline_assert"}):continue
            # Dedup requested commands at episode level; keep feedback observations separate.
            seen_requests.add(cmd)
            state,exit_code=response(step.get("observation")) if len(calls)==1 else ("unknown",None)
            tests.append((i,state,exit_code))
    c["explicit_read_gold_any"]=int(bool(read&gold))
    c["explicit_read_gold_all"]=int(bool(gold) and gold<=read)
    c["read_or_shell_mentions_gold_any"]=int(bool((read|mentioned)&gold))
    c["read_or_shell_mentions_gold_all"]=int(bool(gold) and gold<=read|mentioned)
    c["explicit_edit_gold_any"]=int(bool(edit&gold))
    c["test_requested"]=int(bool(tests))
    c["distinct_test_commands"]=len(seen_requests)
    c["test_after_edit_request"]=int(any(j<i for i,_,_ in tests for j in edit_idx))
    for key in ("zero","nonzero","timeout","tool_error","unknown"):
        c["test_feedback_"+key]=int(any(s==key for _,s,_ in tests))
    c["test_nonzero_then_edit_request"]=int(any(s=="nonzero" and any(j>i for j in edit_idx) for i,s,_ in tests))
    c["pytest_assertion_exit1_observed"]=int(any(e==1 for _,_,e in tests))
    # exit 1 is generic for inline assertion / other runner; not proof of issue-specific failure.
    return c

def load(root,filename,assess):
    d=json.loads((root/filename).read_text());s=assess(d)
    if any(s["error_evaluations"].values()):raise ValueError("incomplete grader")
    return {(r["instance_id"],r["arm"]):r for r in d["results"]}

def run(root,tasks_path,prior):
    a=load(root,FORK,assess_fork);b=load(prior,MULTI,assess_multi)
    ids={t for t,_ in a}
    assert ids=={t for t,_ in b} and len(ids)==17
    tasks=read_selected_tasks(tasks_path,ids)
    groups={}
    for t in ids:
        n=sum(int(r["resolved"]) for (i,_),r in list(a.items())+list(b.items()) if i==t)
        groups[t]="always_pass" if n==4 else "always_fail" if n==0 else "mixed"
    issue_counts=defaultdict(Counter);metrics=defaultdict(Counter)
    for t,row in tasks.items():
        c=issue_counts[groups[t]];c["tasks"]+=1
        for k,v in spec_evidence(row.get("problem_statement","")).items():
            if isinstance(v,bool):c[k]+=int(v)
        c["reference_multifile"]+=int(len(source(diff_evidence(row["patch"])))>1)
    for directory,rows,arms,folder,runname in (
        (root,a,("champion_5min","fork_5min"),"paired-fork-private-results","fork_trial"),
        (prior,b,("champion_5min","multisurface_5min"),"paired-multisurface-private-results","multi_trial")):
        traces={}
        for p in directory.rglob("trace_*.json"):
            t=p.stem.removeprefix("trace_");arm=arms[int("public-prompt" in p.relative_to(directory).parts)]
            if (t,arm) not in rows:continue
            if (t,arm) in traces:raise ValueError("ambiguous trace")
            traces[t,arm]=p
        for (t,arm),r in rows.items():
            m=metrics[groups[t]];m["evaluations"]+=1;m["resolved"]+=int(r["resolved"]);m["nonempty"]+=int(r["has_patch"])
            gold=source(diff_evidence(tasks[t]["patch"]))
            patch=directory/folder/"private-final-patches"/arm/(t+".patch")
            raw=patch.read_text() if patch.is_file() else ""
            if bool(raw.strip())!=r["has_patch"] or len(raw)!=r["patch_chars"]:raise ValueError("patch mismatch")
            g=source(diff_evidence(raw))
            m["final_gold_overlap_any"]+=int(bool(g&gold));m["final_gold_overlap_all"]+=int(bool(gold) and gold<=g)
            p=traces.get((t,arm))
            if p:
                m["traces"]+=1;m.update(trace_stats(json.loads(p.read_text()),gold))
    return {"issue_proxy_by_stability":issue_counts,"trace_proxy_by_stability":metrics,"unique_tasks":len(ids),"evaluations":len(a)+len(b),"issue_semantic_judgment":"NOT_ESTABLISHED","test_replay":"NOT_RUN","new_model_inference":False,"private_content_exported":False}

def smoke():
    assert "explicit_test" in categories("timeout 15s python -m pytest tests/test_x.py::test_y -q")
    assert "explicit_test" in categories("cd /workspace && timeout -k 2s 15s pytest -q")
    assert "inline_assert" in categories("bash -lc 'timeout 10s python -c \"assert 1\"'")
    assert response({"results":[{"content":"{\"status\":\"ok\",\"exit_code\":0}"}]})==("zero",0)
    assert response({"results":[{"content":"{\"status\":\"error\",\"exit_code\":1}"}]})==("nonzero",1)
    assert response({"results":[{"content":"garbage"}]})==("unknown",None)
if __name__=="__main__":
    smoke()
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True);p.add_argument("--tasks",type=Path,required=True);p.add_argument("--prior-root",type=Path,required=True)
    a=p.parse_args()
    print("FOUR_ARM_EVIDENCE="+json.dumps(run(a.root,a.tasks,a.prior_root),sort_keys=True),flush=True)
