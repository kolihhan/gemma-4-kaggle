#!/usr/bin/env python3
"""CPU-only preflight for a paired E4B/31B capacity hypothesis.

Does NOT run Kaggle, read issue text/patches, start a model, or submit.
The frozen Reliability-v1 control is treated as an immutable byte contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

CONTROL = "gemma-4-e4b-it-qat-w4a16-ct"
TREATMENT = "gemma-4-31b-it-qat-w4a16-ct"
EXPOSURE_FILES = (
    "docs/evaluation/verifier-lora-split-v0.json",
    "docs/evaluation/verifier-lora-train-subset-v0.json",
    "docs/evaluation/verifier-lora-blind-reservation-v0.json",
    "docs/evaluation/verifier-lora-eval-contract-v1.json",
    "docs/evaluation/topology-ab-manifest-v1.json",
    "docs/evaluation/public-corpus-summary.md",
)
REPOS = ("Textualize/rich", "fastapi/fastapi")
SELECTION_NAMESPACE = "gemma4-capacity-v0-2026-11-04"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def load_frozen_payload(repo: Path) -> dict[str, str]:
    renderer = repo / "scripts" / "render_reliability_v1_kernel.py"
    spec = importlib.util.spec_from_file_location("frozen_reliability_renderer", renderer)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(renderer)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_frozen_submission(repo / "submission")


def prepare_model_pair(repo: Path, output: Path) -> dict[str, dict[str, object]]:
    """Preserve all control bytes; change exactly one model-declaration value."""
    original = load_frozen_payload(repo)
    anchor = f"model: {CONTROL}"
    agent = original["agent.yaml"]
    if agent.count(anchor) != 1 or len(re.findall(r"(?m)^model:", agent)) != 1:
        raise ValueError("frozen root must contain one exact base-model declaration")
    if output.exists() and any(output.iterdir()):
        raise ValueError("preflight output must be empty; refuse accidental overwrite")
    output.mkdir(parents=True, exist_ok=True)

    result = {}
    for label, model in (("e4b", CONTROL), ("31b", TREATMENT)):
        candidate = dict(original)
        if model != CONTROL:
            candidate["agent.yaml"] = agent.replace(anchor, f"model: {model}", 1)
        directory = output / label
        directory.mkdir()
        for rel, body in candidate.items():
            dst = directory / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(body.encode("utf-8"))
        if set(candidate) != set(original):
            raise ValueError("candidate file set differs from frozen control")
        if any(candidate[k] != original[k] for k in original if k != "agent.yaml"):
            raise ValueError("non-model policy drift")
        if candidate["agent.yaml"].count(f"model: {model}") != 1:
            raise ValueError("model declaration drift")
        result[label] = {
            "model": model,
            "agent_sha256": sha256(candidate["agent.yaml"].encode("utf-8")),
            "file_count": len(candidate),
        }
    return result


def build_feasibility_manifest(repo: Path) -> dict[str, object]:
    """Metadata-only candidate list; not an assertion of full historical cleanliness.

    Original reserved blind tasks are *excluded*, never reassigned to this experiment.
    The first four new IDs are for a paired feasibility diagnostic only.
    The 12 remaining IDs are held untouched for a later powered comparison.
    """
    source_bytes = {p: (repo / p).read_bytes() for p in EXPOSURE_FILES}
    split = read_json(repo, EXPOSURE_FILES[0])
    train_subset = read_json(repo, EXPOSURE_FILES[1])
    blind = read_json(repo, EXPOSURE_FILES[2])
    contract = read_json(repo, EXPOSURE_FILES[3])
    topology = read_json(repo, EXPOSURE_FILES[4])
    if split["counts"]["total_input"] != 129 or split["counts"]["train"] != 90:
        raise ValueError("unexpected corpus split; audit before choosing tasks")
    train = split["train"]
    ids = [str(e["instance_id"]) for e in train]
    if len(ids) != 90 or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicated metadata-only training candidates")

    exposed = set()
    for role in ("excluded", "holdout"):
        exposed.update(str(e["instance_id"]) for e in split[role])
    for source in (train_subset, blind):
        exposed.update(str(e["instance_id"]) for e in source["tasks"])
    exposed.update(str(e["instance_id"]) for e in topology["holdout"])
    exposed.update(str(e) for e in topology["noop_screen"]["excluded_noop_pass"])
    exposed.update(str(e) for e in contract["development_validation"]["instance_ids"])
    exposed.update(str(e) for e in contract["blind_evaluation"]["instance_ids"])

    # The historical public corpus diagnostic sample also shaped earlier experiments.
    public_summary = source_bytes[EXPOSURE_FILES[5]].decode("utf-8")
    exposed.update(re.findall(r"(?m)^-\s+\`([a-z]+_\d+)\`", public_summary))
    if len(exposed) < 35:
        raise ValueError("exposure provenance implausibly incomplete")

    ranked_by_repo = {}
    for name in REPOS:
        pool = [
            str(e["instance_id"])
            for e in train
            if e["repo"] == name and str(e["instance_id"]) not in exposed
        ]
        pool.sort(key=lambda x: (sha256(f"{SELECTION_NAMESPACE}:{x}".encode()), x))
        if len(pool) < 8:
            raise ValueError(f"insufficient metadata candidates for {name}")
        ranked_by_repo[name] = pool
    feasibility = []
    reserve = []
    for name in REPOS:
        feasibility += ranked_by_repo[name][:2]
        reserve += ranked_by_repo[name][2:8]
    if len(set(feasibility + reserve)) != 16:
        raise ValueError("overlap in provisional paired denominator")

    selection = {
        "version": "capacity-boundary-v0",
        "status": "PREFROZEN_METADATA_ONLY_NOT_PROMOTION",
        "contains_task_text": False,
        "source_split_version": split["version"],
        "selection_namespace": SELECTION_NAMESPACE,
        "exposure_source_sha256": {
            k: sha256(v) for k, v in sorted(source_bytes.items())
        },
        "excluded_known_id_count": len(exposed),
        "feasibility_by_repo": {name: 2 for name in REPOS},
        "feasibility_ids": feasibility,
        "confirmation_reserve_ids": reserve,
        "gate": (
            "Fail closed until a historical exposure audit and official gold/no-op "
            "eligibility checks; 4-item feasibility cannot promote a model."
        ),
    }
    digest_input = json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    selection["selection_digest_sha256"] = sha256(digest_input)
    return selection



def audit_candidate_text_mentions(repo: Path, manifest: dict) -> dict[str, object]:
    """Fail closed when a selected ID appears in research/source text outside metadata.

    This detects **repository-stored** prior exposure only. It cannot certify
    unrecorded human browsing, private Kaggle artifacts, or previous chats.
    """
    candidate_ids = set(manifest["feasibility_ids"] + manifest["confirmation_reserve_ids"])
    # After the first screening, this vetted derived artifact must quote the
    # *preselected* candidate IDs. It is not evidence of historical exposure.
    # Keep the exception exact and documented; other files still fail closed.
    input_paths = set(EXPOSURE_FILES) | {
        "docs/evaluation/capacity-v0-gold-screen-2026-11-04.json",
        "docs/evaluation/capacity-v0-noop-screen-2026-11-04.json",
    }
    # Frozen after the original preselection cutoff. This is a structured
    # metadata-only denominator, not evidence that somebody inspected task text.
    # Validate schema before exempting it: arbitrary notes/raw content in that
    # file must NOT silently bypass the exposure scan.
    cohort_path = "docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json"
    if (repo / cohort_path).is_file():
        frozen = read_json(repo, cohort_path)
        expected_keys = {
            "version", "status", "source_selector_sha256",
            "replacement_noop_run_id", "feasibility", "confirmation",
            "totals", "contains_raw_patch_or_task_text",
            "model_evaluation_executed", "certifies_blind",
        }
        if set(frozen) != expected_keys:
            raise ValueError("unexpected frozen cohort metadata fields")
        if frozen["version"] != "capacity-v0-paired-denominator-v1":
            raise ValueError("unexpected frozen cohort version")
        if frozen["contains_raw_patch_or_task_text"] is not False:
            raise ValueError("frozen cohort must contain metadata only")
        if frozen["certifies_blind"] is not False or frozen["model_evaluation_executed"] is not False:
            raise ValueError("frozen cohort status drift")
        items = frozen.get("feasibility", []) + frozen.get("confirmation", [])
        if not isinstance(frozen.get("feasibility"), list) or not isinstance(frozen.get("confirmation"), list):
            raise ValueError("frozen cohort group is not a list")
        if len(frozen["feasibility"]) != 4 or len(frozen["confirmation"]) != 12:
            raise ValueError("frozen cohort population drift")
        if any(
            not isinstance(item, dict)
            or set(item) != {"instance_id", "repo", "source"}
            or item["source"] not in {"original", "replacement"}
            or item["repo"] not in REPOS
            or not re.fullmatch(r"(rich|fastapi)_\d+", str(item["instance_id"]))
            for item in items
        ):
            raise ValueError("frozen cohort item is not metadata-only")
        if len({item["instance_id"] for item in items}) != 16:
            raise ValueError("frozen cohort duplicated issue IDs")
        if frozen["totals"] != {"feasibility": 4, "confirmation": 12, "replacements_used": 6}:
            raise ValueError("frozen cohort totals drift")
        input_paths.add(cohort_path)

    findings: list[dict[str, str]] = []
    scanned = 0
    for dirname in ("docs", "scripts", "tests", "kaggle", ".github/workflows"):
        base = repo / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".yml", ".yaml"}:
                continue
            relative = path.relative_to(repo).as_posix()
            if relative in input_paths:
                continue
            if path.stat().st_size > 2_000_000:
                raise ValueError(f"unreviewed oversized source file in exposure audit: {relative}")
            text = path.read_text(encoding="utf-8", errors="replace")
            scanned += 1
            for issue_id in sorted(candidate_ids):
                if re.search(r"(?<![A-Za-z0-9_])" + re.escape(issue_id) + r"(?![A-Za-z0-9_])", text):
                    findings.append({"instance_id": issue_id, "path": relative})
    if findings:
        raise ValueError(
            "historical source mention of selected candidate(s): "
            + json.dumps(findings, sort_keys=True)
        )
    if scanned == 0:
        raise ValueError("source exposure audit inspected no files")
    return {
        "scanned_files": scanned,
        "unexpected_mentions": findings,
        "scope": "repository-present text only; not full historical/Kaggle guarantee",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo, output = args.repo.resolve(), args.out.resolve()
    if repo == output or repo in output.parents and output == repo / "submission":
        raise ValueError("refuse to write into canonical submission tree")
    pairs = prepare_model_pair(repo, output / "model_pairs")
    denominator = build_feasibility_manifest(repo)
    audit = audit_candidate_text_mentions(repo, denominator)
    manifest_path = output / "feasibility-metadata.json"
    manifest_path.write_text(
        json.dumps(denominator, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CAPACITY_PREFLIGHT_MODEL_ONLY_DELTA=PASS")
    print("CONTROL_MODEL=", pairs["e4b"]["model"])
    print("TREATMENT_MODEL=", pairs["31b"]["model"])
    print("CAPACITY_FEASIBILITY_N=", len(denominator["feasibility_ids"]))
    print("CAPACITY_UNTOUCHED_RESERVE_N=", len(denominator["confirmation_reserve_ids"]))
    print("CAPACITY_SELECTOR_SHA256=", denominator["selection_digest_sha256"])
    print("CAPACITY_EXPOSURE_TEXT_SCAN_FILES=", audit["scanned_files"])
    print("CAPACITY_EXPOSURE_TEXT_MENTIONS=", len(audit["unexpected_mentions"]))
    print("CAPACITY_FEASIBILITY_IDS=", ",".join(denominator["feasibility_ids"]))
    print("CAPACITY_RESERVE_IDS=", ",".join(denominator["confirmation_reserve_ids"]))
    print("CAPACITY_PREFLIGHT_GPU_EXECUTION=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
