"""Audit pre-existing task exposure using only non-sensitive repository manifests.

This is a retrospective overlap check, not a leak diagnosis or a new model
evaluation. Does not open task statements, reference patches or private traces.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ("fastapi_13537", "fastapi_14479", "rich_3953", "rich_3471")
MANIFESTS = (
    ("old_train_trace_harvest",
     "docs/evaluation/verifier-lora-train-subset-v0.json", "tasks"),
    ("old_gold_clean_train_subset",
     "docs/evaluation/verifier-lora-training-gold-screen-v0.json", "clean_instance_ids"),
    ("old_training_targeted_checks",
     "docs/evaluation/verifier-lora-targeted-tests-v0.json", "targets"),
    ("old_blind_reservation",
     "docs/evaluation/verifier-lora-blind-reservation-v0.json", "tasks"),
)


def _ids(payload: dict, field: str) -> set[str]:
    rows = payload.get(field)
    if not isinstance(rows, list):
        raise ValueError("missing manifest list: " + field)
    ids = set()
    for row in rows:
        name = row if isinstance(row, str) else (
            row.get("instance_id") if isinstance(row, dict) else None
        )
        if not isinstance(name, str) or not name:
            raise ValueError("malformed task metadata entry")
        ids.add(name)
    return ids


def audit(root: Path, selected: tuple[str, ...] = PILOT) -> dict:
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("invalid or duplicate selected IDs")
    matched = {}
    for label, relative, field in MANIFESTS:
        path = root / relative
        obj = json.loads(path.read_text(encoding="utf-8"))
        seen = _ids(obj, field)
        overlap = sorted(set(selected) & seen)
        if overlap:
            matched[label] = overlap
    exposed = sorted(set().union(*(set(v) for v in matched.values())))
    return {
        "scope": "REPOSITORY_METADATA_ONLY_RETROSPECTIVE",
        "selected_count": len(selected),
        "historically_exposed_count": len(exposed),
        "historically_exposed_ids": exposed,
        "manifest_hits": matched,
        "clean_unseen_set_proven": False,
        "leakage_to_model_proven": False,
        "model_training_in_new_pilot": False,
        "note": "Prior research exposure invalidates an untouched-cohort claim, "
                "but is not proof gold was passed to the evaluated model.",
    }


def require_unexposed(root: Path, selected: tuple[str, ...]) -> None:
    """Fail closed before GPU if any proposed confirmation ID is already in old manifests.

    This is a minimal necessary gate, NOT sufficient proof of global
    independence: unindexed prior manual exposures remain possible.
    """
    result = audit(root, selected)
    if result["historically_exposed_count"]:
        raise ValueError("known historical task exposure: " +
                         ",".join(result["historically_exposed_ids"]))


if __name__ == "__main__":
    print(json.dumps(audit(ROOT),sort_keys=True))
