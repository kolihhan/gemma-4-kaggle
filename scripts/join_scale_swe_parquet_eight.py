"""Exact eight-task NVIDIA→Scale-SWE source provenance join using HTTP-Range Parquet.

Pin source cohort NVIDIA v2.0/sweagent rows 6..17 (eight successes).
Read only identity column in each Parquet row group and selected provenance
fields for matches. NEVER read the upstream gold `patch` column. No logging
task IDs, commit hashes, source repo names, issue/test strings, signed URLs.
"""
from __future__ import annotations

from collections import Counter
import json
import re
from urllib.parse import urlparse

from scripts.audit_open_swe_traces_metadata import get_json
from scripts.probe_external_source_join import collect_source
from scripts.join_swe_traces_parquet_source import may_contain

DATASET="AweAI-Team/Scale-SWE"
COLUMNS=("instance_id","user","repo","parent_commit","pr_commit",
         "image_url","workdir","problem_statement","f2p_patch","f2p_script","FAIL_TO_PASS")
MAX_PROJECTED_BYTES=110_000_000
ALLOWED_HOSTS={"huggingface.co","cdn-lfs.huggingface.co","datasets-server.huggingface.co"}


def replay_fields(row:dict,source:dict)->str:
    if row.get("instance_id")!=source.get("instance_id"):
        return "instance_id_mismatch"
    owner=row.get("user")
    repo=row.get("repo")
    if not (isinstance(owner,str) and isinstance(repo,str)
            and f"{owner}/{repo}".casefold()==str(source.get("repo","")).casefold()):
        return "source_repository_mismatch"
    if not isinstance(row.get("parent_commit"),str) or not re.fullmatch("[0-9a-fA-F]{40}",row["parent_commit"]):
        return "parent_commit_invalid"
    if not isinstance(row.get("pr_commit"),str) or not re.fullmatch("[0-9a-fA-F]{40}",row["pr_commit"]):
        return "fixing_commit_invalid"
    if not isinstance(row.get("problem_statement"),str) or not row["problem_statement"].strip():
        return "issue_missing"
    if not isinstance(row.get("image_url"),str) or not row["image_url"].strip():
        return "replay_image_missing"
    if not any(isinstance(row.get(key),str) and row[key].strip() for key in ("f2p_patch","f2p_script")):
        return "reproduction_script_missing"
    field=row.get("FAIL_TO_PASS")
    if isinstance(field,str):
        try:
            field=json.loads(field)
        except ValueError:
            return "fail_to_pass_invalid_json"
    if not isinstance(field,list) or not field:
        return "fail_to_pass_unavailable"
    return "source_parent_sha_and_test_inputs_joined_NOT_REPLAYED"


def validate_catalog()->list[str]:
    p=get_json("/parquet",{"dataset":DATASET})
    files=p.get("parquet_files",[])
    if not isinstance(files,list) or not 1<=len(files)<=8:
        raise ValueError("unexpected public source shard count")
    urls=[]
    for entry in files:
        if not isinstance(entry,dict) or entry.get("config")!="default" or entry.get("split")!="train":
            raise ValueError("unexpected public source split")
        url=entry.get("url")
        if not isinstance(url,str) or urlparse(url).scheme!="https" or urlparse(url).hostname not in ALLOWED_HOSTS:
            raise ValueError("untrusted shard URL")
        urls.append(url)
    if len(set(urls))!=len(urls):
        raise ValueError("duplicate source shard URL")
    return urls


def join()->dict:
    chosen=collect_source()
    if len(chosen)!=8 or len({v["instance_id"] for v in chosen})!=8:
        raise ValueError("frozen NVIDIA cohort drift")
    wanted={x["instance_id"] for x in chosen}
    found:dict[str,list[dict]]={x:[] for x in wanted}
    shard_urls=validate_catalog()
    import fsspec
    import pyarrow.parquet as pq
    groups_total=groups_skipped=groups_read=0
    matched_rows=0
    compressed_budget=0
    for url in shard_urls:
        with fsspec.open(url,mode="rb",block_size=1<<16,
                         cache_type="none",timeout=40) as handle:
            pf=pq.ParquetFile(handle)
            schema=set(pf.schema_arrow.names)
            if not set(COLUMNS).issubset(schema):
                raise ValueError("Scale-SWE provenance schema changed")
            if pf.metadata.num_rows > 25000:
                raise ValueError("source sample expansion unsupported")
            for rg in range(pf.metadata.num_row_groups):
                groups_total+=1
                meta=pf.metadata.row_group(rg)
                ix=next((j for j in range(meta.num_columns) if
                         meta.column(j).path_in_schema=="instance_id"),None)
                stats=meta.column(ix).statistics if ix is not None else None
                if not may_contain(stats,wanted):
                    groups_skipped+=1
                    continue
                groups_read+=1
                ids=pf.read_row_group(rg,columns=["instance_id"])["instance_id"].to_pylist()
                indices=[(rownum,val) for rownum,val in enumerate(ids) if val in wanted]
                if not indices:
                    continue
                # Only fetch test/issue data for row groups with exact ID hits;
                # never request or log source gold `patch`.
                group_bytes=sum(int(meta.column(j).total_compressed_size)
                                for j in range(meta.num_columns)
                                if any(meta.column(j).path_in_schema==col or
                                       meta.column(j).path_in_schema.startswith(col+".")
                                       for col in COLUMNS))
                compressed_budget+=group_bytes
                if compressed_budget>MAX_PROJECTED_BYTES:
                    raise ValueError("source metadata byte cap exceeded")
                data=pf.read_row_group(rg,columns=list(COLUMNS))
                for rownum,ident in indices:
                    found[ident].append({col:data[col][rownum].as_py() for col in COLUMNS})
                    matched_rows+=1
    counts=Counter()
    for source in chosen:
        matches=found[source["instance_id"]]
        if len(matches)==0:
            counts["missing_source_id"]+=1
        elif len(matches)>1:
            counts["duplicate_source_id"]+=1
        else:
            counts[replay_fields(matches[0],source)]+=1
    return {
        "status":"SCALE_SWE_SOURCE_PARQUET_JOIN_FINISHED",
        "origin":"NVIDIA v2.0/sweagent 8 eligible successes",
        "source_dataset":DATASET,
        "source_shards":len(shard_urls),
        "rowgroups_total":groups_total,
        "rowgroups_skipped_by_stats":groups_skipped,
        "rowgroups_read_for_ids":groups_read,
        "matching_rows_seen":matched_rows,
        "provenance_categories":dict(counts),
        "projected_compressed_bytes_matched_groups":compressed_budget,
        "upstream_gold_patch_column_read":False,
        "task_ids_or_commit_values_logged":False,
        "executed_tests":0,
        "actual_source_replays":0,
        "approved_sft_training_rows":0,
        "new_model_training":False,
        "official_kaggle_submission":False
    }


if __name__=="__main__":
    try:
        print("GEMMA_SCALE_SWE_EIGHT_PARQUET_JOIN="+json.dumps(join(),sort_keys=True),flush=True)
    except Exception as e:
        print("GEMMA_SCALE_SWE_EIGHT_JOIN_BLOCKED="+json.dumps({
            "exception_kind":type(e).__name__,
            "source_url_or_task_content_printed":False}),flush=True)
        raise SystemExit(1) from None
