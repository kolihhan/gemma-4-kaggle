#!/usr/bin/env python3
"""Render verifier-LoRA v0 on the frozen nine-task development set.

Infrastructure-only launcher: preserve the canonical two-stage submission and
all evaluation settings, inject the already-frozen adapter into the verifier
only, and replace only the evaluation task manifest with the frozen development
IDs from verifier-lora-eval-contract-v1.json.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"
ADAPTER_DATASET_SLUG = "gemma4-verifier-lora-v0-fullseq-41429301498"
EXPECTED_DEV_IDS = [
    "rich_3061",
    "rich_3067",
    "rich_3934",
    "rich_3942",
    "fastapi_13920",
    "fastapi_14077",
    "fastapi_14463",
    "fastapi_14851",
    "fastapi_14986",
]


def render(*, repo: Path, kernel_dir: Path, kernel_ref: str) -> None:
    submission = repo / "submission"
    template_path = repo / "kaggle" / "verifier_baseline_runtime.py"
    contract_path = repo / "docs" / "evaluation" / "verifier-lora-eval-contract-v1.json"

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    ids = contract["development_validation"]["instance_ids"]
    if ids != EXPECTED_DEV_IDS:
        raise SystemExit(f"development IDs drifted: {ids!r}")
    if len(ids) != 9 or len(set(ids)) != 9:
        raise SystemExit("development set must contain exactly nine unique tasks")

    payload: dict[str, str] = {}
    for path in sorted(submission.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(submission).as_posix()
        if relative.startswith("adapters/"):
            continue
        payload[relative] = path.read_text(encoding="utf-8")

    if "agent.yaml" not in payload or "sub_agents/verifier.yaml" not in payload:
        raise SystemExit("canonical two-stage submission is incomplete")
    verifier = payload["sub_agents/verifier.yaml"]
    needle = f"model: {MODEL_NAME}\n"
    if verifier.count(needle) != 1 or "adapter:" in verifier:
        raise SystemExit("unexpected verifier YAML before adapter injection")
    payload["sub_agents/verifier.yaml"] = verifier.replace(
        needle, needle + "adapter: verifier_lora\n", 1
    )

    manifest = {
        "version": "verifier-lora-v0",
        "holdout": [{"instance_id": task_id} for task_id in ids],
    }
    encoded = base64.b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")

    text = template_path.read_text(encoding="utf-8")
    submission_marker = "__SUBMISSION_PAYLOAD_B64__"
    manifest_marker = 'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"'
    if text.count(submission_marker) != 1:
        raise SystemExit("unexpected submission marker count")
    if text.count(manifest_marker) != 1:
        raise SystemExit("unexpected manifest marker count")
    text = text.replace(submission_marker, encoded, 1)
    text = text.replace(
        manifest_marker,
        f"HOLDOUT_MANIFEST_JSON = {json.dumps(manifest, sort_keys=True)!r}",
        1,
    )

    insert_before = "\ndef load_holdout_ids() -> list[str]:\n"
    adapter_function = f'''
def materialize_frozen_adapter() -> None:
    slug = {ADAPTER_DATASET_SLUG!r}
    candidates = [
        Path(f"/kaggle/input/datasets/kolihhan/{{slug}}/adapter"),
        Path(f"/kaggle/input/{{slug}}/adapter"),
    ]
    for config_path in Path("/kaggle/input").glob(f"**/{{slug}}/**/adapter_config.json"):
        candidates.append(config_path.parent)
    source = next(
        (
            candidate
            for candidate in candidates
            if (candidate / "adapter_config.json").is_file()
            and (candidate / "adapter_model.safetensors").is_file()
        ),
        None,
    )
    if source is None:
        raise FileNotFoundError(f"frozen adapter dataset not mounted for slug={{slug}}")
    target = AGENT_DIR / "adapters" / "verifier_lora"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("adapter_config.json", "adapter_model.safetensors"):
        shutil.copyfile(source / name, target / name)
'''
    if text.count(insert_before) != 1:
        raise SystemExit("adapter function insertion point missing")
    text = text.replace(insert_before, "\n" + adapter_function + insert_before, 1)

    call_site = "    materialize_submission()\n    holdout_ids = load_holdout_ids()\n"
    replacement = (
        "    materialize_submission()\n"
        "    materialize_frozen_adapter()\n"
        "    holdout_ids = load_holdout_ids()\n"
    )
    if text.count(call_site) != 1:
        raise SystemExit("adapter materialization call site missing")
    text = text.replace(call_site, replacement, 1)

    old_guard = (
        '    adapter_map = getattr(adapters, "adapters", None) or {}\n'
        "    if adapter_map:\n"
        '        raise RuntimeError(f"baseline v0 must not contain adapters: {sorted(adapter_map)}")\n'
    )
    new_guard = (
        '    adapter_map = getattr(adapters, "adapters", None) or {}\n'
        '    if set(adapter_map) != {"verifier_lora"}:\n'
        '        raise RuntimeError(f"LoRA v0 expected only verifier_lora adapter, got: {sorted(adapter_map)}")\n'
    )
    if text.count(old_guard) != 1:
        raise SystemExit("baseline adapter guard missing")
    text = text.replace(old_guard, new_guard, 1)
    if text.count("enable_lora=False") != 1:
        raise SystemExit("unexpected enable_lora occurrence count")
    text = text.replace("enable_lora=False", "enable_lora=True", 1)

    compile(text, "dev_lora_runtime.py", "exec")
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "dev_lora_runtime.py").write_text(text, encoding="utf-8")

    slug = kernel_ref.split("/", 1)[1]
    metadata = {
        "id": kernel_ref,
        "title": slug,
        "code_file": "dev_lora_runtime.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaL4",
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources": [
            "metric/gemma-4-developer-agent-wheelhouse",
            f"kolihhan/{ADAPTER_DATASET_SLUG}",
        ],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": ["google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2"],
    }
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print("kernel_ref=", kernel_ref)
    print("development_ids=", ids)
    print(
        "verifier_adapter_injected=",
        "adapter: verifier_lora" in payload["sub_agents/verifier.yaml"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--kernel-dir", required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    render(
        repo=Path(args.repo).resolve(),
        kernel_dir=Path(args.kernel_dir).resolve(),
        kernel_ref=args.kernel_ref,
    )


if __name__ == "__main__":
    main()
