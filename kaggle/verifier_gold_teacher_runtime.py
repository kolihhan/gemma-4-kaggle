"""Training-only gold-patch verifier teacher primitives for LoRA v0.

This module deliberately keeps its top-level imports stdlib-only so repo unit
checks do not require the Kaggle scorer wheelhouse. The eventual private GPU
runtime may use these helpers only after the training gold screen is frozen.

Security / leakage boundary:
- accepts only IDs from the frozen training subset;
- requires a frozen training gold-control screen;
- rewrites an experiment copy of submission/ to a verifier-only root;
- applies the gold patch only *after* the official clean baseline commit;
- never serializes raw reference or agent patches into summary records.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"
TRAINING_GOLD_SCREEN_VERSION = "verifier-lora-v0-training-gold-screen"
TRAINING_MANIFEST_VERSION = "verifier-lora-v0-train-harvest"


def load_clean_training_ids(
    manifest_json: str,
    allowed_training_ids: set[str],
) -> list[str]:
    """Return frozen gold-clean IDs, refusing any non-training contamination."""

    try:
        payload = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid training gold-screen JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("training gold-screen manifest must be an object")
    if payload.get("version") != TRAINING_GOLD_SCREEN_VERSION:
        raise ValueError(
            f"unexpected training gold-screen version: {payload.get('version')!r}"
        )
    if payload.get("status") != "frozen":
        raise ValueError("training gold-screen must be frozen before teacher use")
    if payload.get("source_training_manifest") != TRAINING_MANIFEST_VERSION:
        raise ValueError(
            "training gold-screen source manifest does not match the frozen training subset"
        )

    raw_ids = payload.get("clean_instance_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("training gold-screen has no clean_instance_ids")
    ids: list[str] = []
    for raw in raw_ids:
        if not isinstance(raw, str) or not raw:
            raise ValueError("training gold-screen contains an invalid task ID")
        ids.append(raw)
    if len(ids) != len(set(ids)):
        raise ValueError("training gold-screen contains duplicate task IDs")

    contamination = sorted(set(ids) - set(allowed_training_ids))
    if contamination:
        raise ValueError(
            f"training gold-screen contains non-training IDs: {contamination}"
        )
    return ids


def build_verifier_only_submission(files: dict[str, str]) -> dict[str, str]:
    """Build an experiment-only root agent that is exactly the current verifier.

    The canonical repository submission is not modified. The returned mapping is
    intended to be materialized into a private experiment runtime directory.
    """

    if not isinstance(files, dict) or not files:
        raise ValueError("submission payload must be a non-empty file mapping")
    required = ("prompts/verifier.md", "configs/sampling.yaml")
    missing = [path for path in required if not isinstance(files.get(path), str)]
    if missing:
        raise ValueError(f"submission payload is missing verifier assets: {missing}")

    built = dict(files)
    built["agent.yaml"] = (
        "agent_class: LlmAgent\n"
        "name: swe_e4b_verifier\n"
        f"model: {MODEL_NAME}\n"
        "description: Independently verifies the existing patch, performs at most one narrow repair, and owns final submission.\n"
        "instruction: !include prompts/verifier.md\n"
        "tools:\n"
        "  - run_command\n"
        "  - read_file\n"
        "  - edit_file\n"
        "  - get_status\n"
        "  - submit_patch\n"
        "generate_content_config: !include configs/sampling.yaml\n"
    )
    return built


def install_gold_patch_after_baseline_hook():
    """Patch the official runner so a gold patch appears after baseline creation.

    Returns ``(state, original_setup_baseline_commit)``. Set
    ``state['patch_path']`` to the host-side temporary reference-patch file before
    evaluating each task, then restore the original runner function in a final
    cleanup block after the experiment.

    This function imports scorer modules lazily because they exist only inside
    the official Kaggle wheelhouse.
    """

    import swegemma.harness.agent_runner as agent_runner
    from swegemma.harness.container_setup import apply_patch_in_container

    original_setup_baseline_commit = agent_runner.setup_baseline_commit
    state: dict[str, Path | None] = {"patch_path": None}

    def setup_baseline_then_gold_patch(docker, container_id, commit_msg="baseline"):
        # The clean snapshot *must* be committed first, otherwise the reference
        # change becomes part of the baseline and the verifier sees an empty diff.
        original_setup_baseline_commit(docker, container_id, commit_msg)

        patch_path = state.get("patch_path")
        if patch_path is None:
            raise RuntimeError("gold teacher has no active reference patch")
        patch_path = Path(patch_path)
        if not patch_path.is_file() or patch_path.stat().st_size == 0:
            raise RuntimeError(f"gold teacher reference patch is missing/empty: {patch_path}")

        container_patch = "/tmp/verifier_gold_reference.patch"
        docker.copy_to(container_id, patch_path, container_patch)
        exit_code, stdout, stderr = apply_patch_in_container(
            docker,
            container_id,
            container_patch,
        )
        try:
            if exit_code != 0:
                raise RuntimeError(
                    "failed to apply gold teacher patch: "
                    f"exit={exit_code} stdout={stdout[-1000:]!r} stderr={stderr[-1000:]!r}"
                )

            diff_check = docker.exec(container_id, "cd /workspace && git diff --check")
            if diff_check.exit_code != 0:
                raise RuntimeError(
                    "gold teacher patch failed git diff --check: "
                    f"{(diff_check.stderr or diff_check.stdout)[-1000:]}"
                )

            # `git diff --quiet HEAD` returns 1 for the desired non-empty diff,
            # 0 when no change is visible, and >1 on an execution error.
            diff_nonempty = docker.exec(
                container_id,
                "cd /workspace && git diff --quiet HEAD",
            )
            if diff_nonempty.exit_code != 1:
                raise RuntimeError(
                    "gold teacher patch is not a clean non-empty diff: "
                    f"git diff --quiet HEAD exit={diff_nonempty.exit_code}"
                )
        finally:
            docker.exec(container_id, f"rm -f {container_patch}")

    agent_runner.setup_baseline_commit = setup_baseline_then_gold_patch
    return state, original_setup_baseline_commit


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_result_record(
    *,
    instance_id: str,
    repo: str,
    reference_patch: str,
    resolved: bool,
    test_exit_code: int | None,
    agent_patch: str,
    tool_calls: int | None,
    duration_seconds: float | None,
    error: str | None,
) -> dict[str, Any]:
    """Build a metadata-only teacher result without leaking either patch body."""

    if not isinstance(reference_patch, str) or not reference_patch:
        raise ValueError("reference_patch must be non-empty text")
    if not isinstance(agent_patch, str):
        raise ValueError("agent_patch must be text")
    return {
        "instance_id": instance_id,
        "repo": repo,
        "status": "completed" if error is None else "error",
        "resolved": bool(resolved),
        "test_exit_code": test_exit_code,
        "reference_patch_chars": len(reference_patch),
        "reference_patch_sha256": _sha256_text(reference_patch),
        "agent_patch_chars": len(agent_patch),
        "agent_patch_sha256": _sha256_text(agent_patch),
        "has_agent_patch": bool(agent_patch.strip()),
        "tool_calls": tool_calls,
        "duration_seconds": duration_seconds,
        "error": error,
    }
