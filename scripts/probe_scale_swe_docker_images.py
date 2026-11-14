"""Non-pulling Docker image availability/size preflight for two frozen Scale-SWE tasks.

Only inspect public registry manifests, never run container or source tests.
No raw image refs (which embed task IDs), repository IDs or URLs in logs.
"""
from __future__ import annotations

from collections import Counter
import json
import re
import shutil
import subprocess

from scripts.check_scale_swe_model_patch_apply import (
    fetch_nvidia_fixed_two, get_scale_match
)

MAX_PULL_BYTES=5_000_000_000


def manifest_status(image:object)->dict:
    if not isinstance(image,str) or not re.fullmatch(
        r"aweaiteam/scaleswe:[A-Za-z0-9_.-]{5,180}",image):
        return {"state":"image_reference_untrusted"}
    try:
        p=subprocess.run(["docker","manifest","inspect",image],check=False,
                         capture_output=True,text=True,timeout=80)
    except (OSError,subprocess.TimeoutExpired):
        return {"state":"registry_probe_unavailable"}
    if p.returncode != 0:
        return {"state":"manifest_unavailable"}
    try:
        obj=json.loads(p.stdout)
    except ValueError:
        return {"state":"manifest_schema_unknown"}
    layers=obj.get("layers")
    if isinstance(layers,list) and layers:
        sizes=[x.get("size") for x in layers if isinstance(x,dict)]
        if len(sizes)==len(layers) and all(isinstance(x,int) and x>0 for x in sizes):
            size=sum(sizes)
            return {"state":"manifest_layers_available",
                    "size_band":"under_5GB" if size<MAX_PULL_BYTES else "over_5GB",
                    "compressed_bytes":size,
                    "layer_count":len(layers)}
    return {"state":"manifest_no_direct_layers"}


def run()->dict:
    selected=fetch_nvidia_fixed_two()
    source=get_scale_match(selected)
    ordered=list(selected)
    results=[manifest_status(source[key].get("image_url")) for key in ordered]
    return {"source":"AweAI-Team/Scale-SWE",
            "same_two_predeclared_task_ids":len(results)==2,
            "image_statuses":dict(Counter(x["state"] for x in results)),
            "images_with_sizes":[{k:v for k,v in x.items() if k!="state"} for x in results],
            "runner_free_disk_gb":round(shutil.disk_usage("/tmp").free/1e9,1),
            "images_downloaded":0,
            "containers_started":0,
            "source_tests_run":0,
            "training_started":False}


if __name__=="__main__":
    try:
        print("GEMMA_SCALE_SOURCE_DOCKER_MANIFESTS="+json.dumps(run(),sort_keys=True),flush=True)
    except Exception as e:
        print("GEMMA_SCALE_SOURCE_DOCKER_PROBE_BLOCKED="+json.dumps({
            "error_class":type(e).__name__,"raw_image_or_task_id_logged":False}),flush=True)
        raise SystemExit(1) from None
