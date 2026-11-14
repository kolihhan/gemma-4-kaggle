"""Bounded remote Parquet random-access preflight for SWE-rebench-V2.

Never downloads or persists the entire 429-MB dataset. Does not read row contents,
task IDs, gold patches, test cases or repo names. Only schema/size metadata.

The exact public upstream file is dataset-nebius/SWE-rebench-V2@main.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = ("https://huggingface.co/datasets/nebius/SWE-rebench-V2/resolve/main/"
       "data/train-00000-of-00001.parquet")
COLS = ("instance_id", "repo", "license", "base_commit", "image_name",
        "FAIL_TO_PASS", "test_patch", "problem_statement")


def status_group(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return "http_" + str(exc.code)
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, URLError):
        return "network_url_error"
    return type(exc).__name__


def probe() -> dict:
    output = {"source": "nebius/SWE-rebench-V2/main/data/train-00000-of-00001.parquet",
              "raw_rows_or_columns_saved": False,
              "gold_patch_column_read": False,
              "full_file_downloaded": False}
    try:
        with urlopen(Request(URL, method="HEAD"), timeout=35) as response:
            output["head_status"] = int(response.status)
            length = response.headers.get("Content-Length")
            output["remote_content_bytes"] = int(length) if length and length.isdigit() else None
            output["accept_ranges"] = response.headers.get("Accept-Ranges", "unspecified")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        output["head_error_type"] = status_group(exc)
    try:
        request = Request(URL, headers={"Range": "bytes=0-3"})
        with urlopen(request, timeout=35) as response:
            output["range_status"] = int(response.status)
            output["range_content_length"] = response.headers.get("Content-Length")
            if response.status == 206:
                output["parquet_magic_valid"] = response.read(4) == b"PAR1"
            else:
                output["parquet_magic_valid"] = False
                output["range_supported"] = False
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        output["range_error_type"] = status_group(exc)
        return output
    if output.get("range_status") != 206 or not output.get("parquet_magic_valid"):
        return output
    try:
        import fsspec
        import pyarrow.parquet as pq
        with fsspec.open(URL, mode="rb", block_size=1 << 20,
                         cache_type="readahead", timeout=35) as handle:
            pf = pq.ParquetFile(handle)
            schema = set(pf.schema_arrow.names)
            meta = pf.metadata
            output["status"] = "REMOTE_PARQUET_METADATA_OPENED"
            output["row_groups"] = int(meta.num_row_groups)
            output["rows"] = int(meta.num_rows)
            output["expected_columns_present"] = {col: col in schema for col in COLS}
            compressed = {}
            for col in COLS:
                total = 0
                for ix in range(meta.num_row_groups):
                    group = meta.row_group(ix)
                    for col_ix in range(group.num_columns):
                        item = group.column(col_ix)
                        if item.path_in_schema == col:
                            total += int(item.total_compressed_size)
                compressed[col] = total
            output["selected_compressed_bytes"] = compressed
    except Exception as exc:  # diagnostic only; do not log remote signed URL
        output["metadata_error_type"] = status_group(exc)
    return output


if __name__ == "__main__":
    print("GEMMA_SWE_REBENCH_PARQUET_PREFLIGHT=" +
          json.dumps(probe(),sort_keys=True), flush=True)
    print("NO_FULL_DOWNLOAD_NO_RAW_ROWS_NO_GPU_NO_TRAINING=TRUE",flush=True)
