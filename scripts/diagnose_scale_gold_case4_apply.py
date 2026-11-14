"""One fixed case-4 gold application diagnostic, NO test or model execution.

Separates upstream PR reference patch applicability at clean source parent
from applicability after source F2P fixture installation. Never prints
source diff, raw file paths, repository/issue IDs or container output.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from scripts.check_scale_swe_model_patch_apply import fetch_nvidia_fixed_eight, get_scale_match
from scripts.replay_scale_swe_one_in_docker import (
    fetch_gold_for_control_only, image_size_gate, invoke, workdir_sane
)

CASE_INDEX=4


def _diff_paths(patch: str)->set[str]:
    pairs=re.findall(r"^diff --git a/(.*?) b/(.*?)$",patch,flags=re.M)
    return {b for _,b in pairs}


def diagnose()->dict:
    sources=fetch_nvidia_fixed_eight()
    if len(sources)!=8:
        raise ValueError("frozen source count drift")
    selected_key=list(sources)[CASE_INDEX]
    record=get_scale_match(sources)[selected_key]
    gold=fetch_gold_for_control_only(selected_key)
    model=sources[selected_key]["model_patch"]
    image=record.get("image_url")
    workdir=record.get("workdir")
    if not isinstance(image,str) or not re.fullmatch(r"aweaiteam/scaleswe:[A-Za-z0-9_.-]{5,180}",image):
        raise ValueError("untrusted task image")
    if not workdir_sane(workdir) or image_size_gate(image)!="image_under_1p5GB_cap":
        raise ValueError("image/workspace resource gate")
    if invoke(["docker","pull","--quiet",image],timeout=420)[0]!=0:
        raise ValueError("image pull unsuccessful")
    container="gemma_scale_gold_applicability_4"
    args=["docker","create","--name",container,"--network","none","--memory","5g",
          "--cpus","2","--pids-limit","256","--cap-drop","ALL",
          "--security-opt","no-new-privileges",
          "--tmpfs","/tmp:rw,size=512m",image,"sleep","480"]
    if invoke(args,timeout=40)[0]!=0:
        raise ValueError("isolated container create failed")
    try:
        if invoke(["docker","start",container],timeout=30)[0]!=0:
            raise ValueError("isolated container start failed")
        def cmd(*params: str, text: str|None=None)->bool:
            args=["docker","exec","-i","-w",workdir,container,*params]
            return invoke(args,stdin=text,timeout=55)[0]==0
        if not cmd("git","reset","--hard",record["parent_commit"]):
            raise ValueError("source checkout reset failed")
        gold_clean=cmd("git","apply","--check","-",text=gold)
        model_clean=cmd("git","apply","--check","-",text=model)
        fixture=record.get("f2p_script")
        f2p=record.get("f2p_patch")
        fixture_type="synthetic_script" if isinstance(fixture,str) and fixture.strip() else "git_test_patch"
        if fixture_type=="synthetic_script":
            with TemporaryDirectory(prefix="gemma_fixture_") as temp:
                f=Path(temp)/"test_fail_to_pass.py"
                f.write_text(fixture,encoding="utf-8")
                success=invoke(["docker","cp",str(f),
                                container+":"+workdir+"/test_fail_to_pass.py"],timeout=35)[0]==0
        elif isinstance(f2p,str) and f2p.strip():
            success=cmd("git","apply","-",text=f2p)
        else:
            raise ValueError("F2P fixture is empty")
        if not success:
            raise ValueError("F2P fixture install failed")
        gold_after=cmd("git","apply","--check","-",text=gold)
        model_after=cmd("git","apply","--check","-",text=model)
        overlap_fixture=(fixture_type=="synthetic_script" and
                         "test_fail_to_pass.py" in _diff_paths(gold))
        gold_paths=_diff_paths(gold)
        model_paths=_diff_paths(model)
        return {
          "scope":"frozen source success case index 4 only",
          "gold_apply_check_on_clean_source":gold_clean,
          "gold_apply_check_after_f2p_fixture":gold_after,
          "nvidia_model_apply_check_on_clean_source":model_clean,
          "nvidia_model_apply_check_after_f2p_fixture":model_after,
          "fixture_kind":fixture_type,
          "gold_diff_file_count":len(gold_paths),
          "model_diff_file_count":len(model_paths),
          "gold_and_model_diff_file_overlap_count":len(gold_paths & model_paths),
          "gold_modifies_synthetic_test_filename":overlap_fixture,
          "patch_or_test_code_executed":False,
          "gold_given_to_model_or_training":False,
          "raw_source_or_patch_logged":False,
          "independent_f2p_tests_run":0,
          "new_training":False,
          "official_submission":False,
        }
    finally:
        invoke(["docker","rm","-f",container],timeout=30)


if __name__=="__main__":
    try:
        print("GEMMA_CASE4_GOLD_APPLY_CAUSE="+json.dumps(diagnose(),sort_keys=True),flush=True)
    except Exception as e:
        print("GEMMA_CASE4_GOLD_APPLY_DIAG_ERROR="+json.dumps(
            {"type":type(e).__name__, "sensitive_contents_logged":False}),flush=True)
        raise SystemExit(1) from None
