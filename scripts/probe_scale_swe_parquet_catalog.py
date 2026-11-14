"""List Scale-SWE auto-Parquet shards only. Never fetch raw columns or source code."""
from __future__ import annotations
from collections import Counter
import json

from scripts.audit_open_swe_traces_metadata import get_json

SOURCE="AweAI-Team/Scale-SWE"


def probe()->dict:
    response=get_json("/parquet",{"dataset":SOURCE})
    files=response.get("parquet_files")
    if not isinstance(files,list):
        return {"status":"no_parquet_file_list","api_keys":sorted(response.keys())}
    info=[]
    for row in files:
        if not isinstance(row,dict):
            continue
        url=row.get("url")
        trusted=(isinstance(url,str) and url.startswith("https://") and
                 ("huggingface.co/" in url or "cdn-lfs.huggingface.co/" in url or
                  "datasets-server.huggingface.co/" in url))
        info.append({
          "config":row.get("config"),"split":row.get("split"),
          "size":row.get("size"),"num_rows":row.get("num_rows"),
          "trusted_href":trusted,"has_href":bool(url)
        })
    return {"source":SOURCE,"api_keys":sorted(response.keys()),
            "shards":len(info),
            "configuration_counts":dict(Counter(f"{x['config']}/{x['split']}" for x in info)),
            "size_bytes_total":sum(x["size"] for x in info if isinstance(x["size"],int)),
            "all_shards_trusted":all(x["trusted_href"] for x in info),
            "example_shards":info[:5],
            "raw_rows_exported":False,
            "downloaded_full_dataset":False}


if __name__=="__main__":
    print("GEMMA_SCALE_SWE_PARQUET_CATALOG="+json.dumps(probe(),sort_keys=True),flush=True)
