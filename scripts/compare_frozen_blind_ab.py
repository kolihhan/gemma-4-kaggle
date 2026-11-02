#!/usr/bin/env python3
"""Compare frozen blind base and verifier-LoRA result summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def metrics(result: dict) -> dict:
    rows = result.get("results") or []
    tool_calls = [row.get("tool_calls") for row in rows if isinstance(row.get("tool_calls"), (int, float))]
    durations = [row.get("duration_seconds") for row in rows if isinstance(row.get("duration_seconds"), (int, float))]
    return {
        "completed": result.get("completed"),
        "resolved": result.get("resolved"),
        "errors": sum(row.get("status") != "completed" for row in rows),
        "patches": sum(bool(row.get("has_patch")) for row in rows),
        "mean_tool_calls": sum(tool_calls) / len(tool_calls) if tool_calls else None,
        "mean_duration_seconds": sum(durations) / len(durations) if durations else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--lora", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    lora = json.loads(Path(args.lora).read_text(encoding="utf-8"))
    if base.get("requested") != 10 or lora.get("requested") != 10:
        raise SystemExit("both frozen blind runs must request exactly 10 tasks")
    base_ids = [row["instance_id"] for row in base.get("results") or []]
    lora_ids = [row["instance_id"] for row in lora.get("results") or []]
    if len(base_ids) != 10 or base_ids != lora_ids:
        raise SystemExit("base and LoRA task order must match the same 10 blind IDs")

    base_resolved = set(base.get("resolved_instance_ids") or [])
    lora_resolved = set(lora.get("resolved_instance_ids") or [])
    comparison = {
        "version": "verifier-lora-v0-frozen-blind-ab",
        "base": metrics(base),
        "lora": metrics(lora),
        "delta_resolved": len(lora_resolved) - len(base_resolved),
        "base_only": sorted(base_resolved - lora_resolved),
        "lora_only": sorted(lora_resolved - base_resolved),
        "both": sorted(base_resolved & lora_resolved),
        "neither": sorted(set(base_ids) - base_resolved - lora_resolved),
    }
    Path(args.output).write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FROZEN_BLIND_AB", json.dumps(comparison, sort_keys=True))


if __name__ == "__main__":
    main()
