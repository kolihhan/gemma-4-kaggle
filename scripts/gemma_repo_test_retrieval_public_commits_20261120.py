"""One-shot REAL GitHub commit repository-test discovery mechanism A/B (CPU).

No Gemma inference, hidden/grader test access, Kaggle API, new scoring, GPU.
Use previous commit's repository-visible tests; label only test files
co-changed by the developer. This is a *retrieval proxy*, NOT actual patch PASS.
"""
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path
from collections import Counter

STOP={"test","tests","src","python","pkg","package","lib","app","fastapi","rich",
      "module","core","util","utils","internal","helpers","helper","code"}

def tokens(s: str) -> set[str]:
    out=set()
    for word in re.split(r"[^a-z0-9]+",s.lower()):
        if word and len(word)>=3 and word not in STOP:
            out.add(word)
    return out

def normstem(path: str) -> str:
    stem=Path(path).stem.lower()
    return stem[5:] if stem.startswith("test_") else (
        stem[:-5] if stem.endswith("_test") else stem)

def is_test(path: str) -> bool:
    p=Path(path)
    return p.suffix==".py" and ("tests" in p.parts or "test" in p.parts) and (
        p.stem.startswith("test_") or p.stem.endswith("_test"))

def is_src(path: str) -> bool:
    p=Path(path)
    return p.suffix==".py" and not is_test(path) and (
        not any(x in p.parts for x in ("examples","docs","tutorial","scripts","tests")))

def baseline(src: str, alltests: set[str]) -> list[str]:
    """Prior prototype: only an exact test_<module>.py name."""
    s=Path(src).stem
    return sorted(t for t in alltests
        if Path(t).name in ("test_"+s+".py",s+"_test.py"))[:1]

def char_match(a: str,b: str) -> bool:
    """Fixed prefix match, not tuned on labels, covers rout/routes, parse/parser."""
    return len(a)>=4 and len(b)>=4 and (a[:4]==b[:4] or a in b or b in a)

def rank(src: str, alltests: set[str], k: int=3) -> list[str]:
    """Proposed one-change test-path ranking: filename + path-package tokens."""
    sm=normstem(src)
    st=tokens(src)
    ranked=[]
    for p in alltests:
        tm=normstem(p)
        tt=tokens(p)
        overlap=len(st & tt)
        eq=int(sm==tm)
        broad=int(char_match(sm,tm))
        # Never guess a test when there is no lexical link.
        if not eq and not broad and overlap==0:continue
        score=100*eq+25*broad+8*overlap
        ranked.append((-score,p))
    return [p for _,p in sorted(ranked)[:k]]

def shell(cmd: list[str], cwd: Path|None=None, timeout:int=60) -> str:
    return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,check=True,timeout=timeout).stdout

def evaluate_repo(root: Path, label: str, history:int=100, cap:int=40) -> dict:
    revisions=shell(["git","log","--no-merges","--pretty=%H",f"-{history}"],root).splitlines()
    evaluated=[]
    for rev in revisions:
        if len(evaluated)>=cap:break
        try:
            parent=shell(["git","rev-parse",rev+"^"],root).strip()
            changed=shell(["git","diff","--name-only",parent,rev],root).splitlines()
            touched_sources=sorted(set(x for x in changed if is_src(x)))
            touched_tests=set(x for x in changed if is_test(x))
            if not touched_sources or not touched_tests:continue
            pre=set(shell(["git","ls-tree","-r","--name-only",parent],root).splitlines())
            pretests=set(x for x in pre if is_test(x))
            truth=touched_tests & pretests
            if not truth:continue
            for src in touched_sources[:4]:
                c0=baseline(src,pretests)
                c1=rank(src,pretests)
                evaluated.append({
                  "control_at1":int(bool(set(c0)&truth)),
                  "treatment_at1":int(bool(set(c1[:1])&truth)),
                  "treatment_at3":int(bool(set(c1)&truth)),
                  "has_candidate_control":int(bool(c0)),
                  "has_candidate_treatment":int(bool(c1)),
                  "truth_test_count":len(truth),
                })
                if len(evaluated)>=cap:break
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
            continue
    keys=evaluated[0].keys() if evaluated else ()
    totals={k:sum(int(row[k]) for row in evaluated) for k in keys}
    return {
        "repo":label,
        "exact_head_sha":shell(["git","rev-parse","HEAD"],root).strip(),
        "commit_history_examined":len(revisions),
        "frozen_valid_source_test_cases":len(evaluated),
        "counts":totals,
        "at1_rescues":sum(x["treatment_at1"]==1 and x["control_at1"]==0 for x in evaluated),
        "at1_regressions":sum(x["treatment_at1"]==0 and x["control_at1"]==1 for x in evaluated),
        "baseline_exact_name_vs_candidate_fixed_ranker":True,
        "test_path_labels_from_same_commit_only_never_used_in_candidate_selection":True,
        "pre_commit_repo_snapshot_only_for_available_tests":True,
    }

def smoke() -> None:
    src="fastapi/routing.py"
    paths={"tests/test_routes.py","tests/test_unrelated.py"}
    assert baseline(src,paths)==[]
    assert rank(src,paths)[0]=="tests/test_routes.py"
    src2="rich/console.py"
    paths2={"tests/test_console.py","tests/test_log.py"}
    assert baseline(src2,paths2)==["tests/test_console.py"]
    assert rank(src2,paths2)[0]=="tests/test_console.py"
    assert not is_src("tests/test_console.py")
    assert not rank("pkg/no_testable_link.py",paths2)
    print("GEMMA_REAL_REPO_TEST_DISCOVERY_UNIT=PASS",flush=True)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--fastapi",type=Path)
    a.add_argument("--rich",type=Path)
    a.add_argument("--self-test",action="store_true")
    args=a.parse_args()
    if args.self_test:
        smoke();return
    if not args.fastapi or not args.rich:
        a.error("--fastapi and --rich required")
    results=[
      evaluate_repo(args.fastapi,"fastapi/fastapi",history=120,cap=40),
      evaluate_repo(args.rich,"Textualize/rich",history=120,cap=40)
    ]
    b=sum(r["counts"].get("control_at1",0) for r in results)
    t=sum(r["counts"].get("treatment_at1",0) for r in results)
    tp3=sum(r["counts"].get("treatment_at3",0) for r in results)
    n=sum(r["frozen_valid_source_test_cases"] for r in results)
    rescue=sum(r["at1_rescues"] for r in results)
    regress=sum(r["at1_regressions"] for r in results)
    out={"version":"public_real_developer_commit_test_retrieval_proxy_v0",
         "repos":results,"cases":n,"baseline_hits_at1":b,
         "treatment_hits_at1":t,"treatment_hits_at3":tp3,
         "rescue":rescue,"regression":regress,
         "gate_pass":n>=20 and t>=b+5 and rescue>regress,
         "no_hidden_oracle_no_gold_patch_no_competition_data":True,
         "no_gpu_or_model_training_or_submission":True,
         "limitation":"Developer co-changed test is a noisy proxy, not task-relevant executable test evidence or scored patch resolution; temporal test-leak avoided using prior commit tree."}
    print("GEMMA_PUBLIC_REAL_REPO_TEST_RETRIEVAL="+json.dumps(out,sort_keys=True),flush=True)
    if n<20:raise SystemExit("INSUFFICIENT_PUBLIC_COMMIT_SAMPLE_STOP_NOT_A_MODEL_RESULT")

if __name__=="__main__":main()
