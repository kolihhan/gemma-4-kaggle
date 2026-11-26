"""Pre-register UNUSED current-public-development scorer controls, CPU only.

This builds a private Kaggle notebook for untouched cases that independently
passed gold/no-op checks and do not carry a short-link issue description.
It never uses a hidden score or a model response to select cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.render_six_gold_noop_cpu_20261126 import SAFE_RUNTIME, TEMPLATE

KERNEL="kolihhan/gemma31-fresh17-gold-noop-20261126-v1"
EXPECTED_TOTAL=17
PREVIOUS=(
    ("behavior", "paired_behavioral_probe31b_4min_results.json", 8),
    ("grammar", "paired_edit_grammar31b_5min_results.json", 8),
    ("single", "paired_single_edit_channel31b_4min_results.json", 6),
)
PINNED_EXTERNAL_AUDIT_COMMIT="f3b6d3ac4c532a2bf3745872fe171747d0bf3e31"


def build(repo:Path, previous:Path, gold:Path, noop:Path, out:Path) -> dict:
    old=json.loads((repo/"experiments/edit-grammar-paired-20261124/manifest.json").read_text())
    used=set(old["selection"]["exclude_instance_ids"])
    assert len(used)==43
    for name,filename,n in PREVIOUS:
        x=json.loads((previous/name/filename).read_text())
        ids=set(x["selected_public_dev_ids"])
        if x["status"]!="completed" or len(ids)!=n or len(x["results"])!=2*n:
            raise ValueError("old experiment missing")
        if used & ids: raise ValueError("prior used task collision")
        used.update(ids)
    if len(used)!=65: raise ValueError("exclusion drift")
    def load(path):
        rows=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        return {r["instance_id"]:r for r in rows}
    gold_rows,noop_rows=load(gold),load(noop)
    if len(gold_rows)!=129 or set(gold_rows)!=set(noop_rows):
        raise ValueError("pinned third party gold/noop records incomplete")
    candidates={id for id,row in gold_rows.items()
                if row["resolved"] is True
                and noop_rows[id]["resolved"] is False and id not in used}
    if len(candidates)!=28: raise ValueError("unused independent gold-valid proxy count changed")
    selected=[]
    with (repo/"tasks.jsonl").open(encoding="utf-8") as f:
        for line in f:
            t=json.loads(line);id=t["instance_id"]
            if id not in candidates: continue
            statement=t.get("problem_statement","")
            if not isinstance(statement,str):
                raise ValueError("issue statement not text")
            if len(statement.strip())<160 and re.search(r"https?://",statement):
                continue
            selected.append(id)
    ids=sorted(selected)
    if len(ids)!=EXPECTED_TOTAL or len(set(ids))!=EXPECTED_TOTAL:
        raise ValueError("strict fixed independent pool expected 17")
    orig=(repo/TEMPLATE).read_text()
    marker='if __name__ == "__main__":'
    if orig.count(marker)!=1 or "async def run_sweep" not in orig:
        raise ValueError("original gold control template drift")
    safe=SAFE_RUNTIME
    assert safe.count("__SELECTED_IDS__")==1
    safe=safe.replace("__SELECTED_IDS__",repr(ids))
    safe=safe.replace("gemma31_six_gold_noop_safe.json",
                      "gemma31_fresh17_gold_noop_safe.json")
    safe=safe.replace("gemma31-six-private-current-wheelhouse-gold-noop-v1",
                      "gemma31-fresh17-private-current-wheelhouse-gold-noop-v1")
    runtime=orig.split(marker,1)[0]+"\n"+safe
    assert runtime.count('if __name__ == "__main__":')==1
    assert "competition_submit_code" not in runtime
    compile(runtime,"main.py","exec")
    if out.exists():raise FileExistsError("refuse to overwrite private preregistration")
    out.mkdir(parents=True)
    (out/"main.py").write_text(runtime)
    meta={"id":KERNEL,"title":KERNEL.split("/")[1],
          "code_file":"main.py","language":"python",
          "kernel_type":"script","is_private":True,
          "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
          "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
          "competition_sources":["gemma-4-developer-agent"],
          "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
          "model_sources":[],"kernel_sources":[]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    return {"selected_count":len(ids),"id_membership_sha256":hashlib.sha256(
                "|".join(ids).encode()).hexdigest(),
            "independent_public_gold_noop_valid_untouched_pool":28,
            "excluded_previous":len(used),
            "no_short_external_reference":True,
            "third_party_audit_commit":PINNED_EXTERNAL_AUDIT_COMMIT,
            "control_verifications_planned":2*len(ids),
            "current_environment_score":"UNRUN",
            "no_model_calls":True,"gpu":False,"official_submit":False,
            "raw_ids_exported":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--previous",type=Path,required=True)
    p.add_argument("--gold",type=Path,required=True)
    p.add_argument("--noop",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=build(Path("."),args.previous,args.gold,args.noop,args.out)
    print("FRESH17_PRIVATE_CPU_PREREGISTRATION="+json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
