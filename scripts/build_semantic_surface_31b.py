"""One-root Gemma 31B semantic-surface candidate from exact scored 0.180 source.

The production difference is a real read-only git+AST inspection skill, not
a second model or a Python callback registered outside the official compiler.
Agent decides whether to invoke it. No training or official submit.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from scripts.build_public_prompt_only_control_20261111 import make_zip
from scripts.build_toolcap60_timeout_recovery import build, files_for_candidate
from scripts.render_patch_checkpoint_31b import CHAMPION_SHA

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "experiments/semantic-surface-v0/skill"
RULE = (
    "- For an edited Python method or public API whose behavior may affect a router, "
    "wrapper, caller or another entry point, inspect the full code impact rather "
    "than assuming one edited function is complete. After your first concrete "
    "source edit, call load_skill(\"semantic-surface\") and invoke "
    "run_skill_script(skill_name=\"semantic-surface\", "
    "file_path=\"scripts/surface.py\", args={}) ONCE. Read its actual "
    "other-file symbol references, inspect only relevant paths, and correct "
    "a genuinely missing issue requirement if supported. These references "
    "are lexical clues, NOT correctness evidence. Skip for a trivial "
    "one-location fix or when no Python source changes. Do not lose time "
    "to repeated skill calls; finish with the smallest correct patch.\n"
)


def candidate_files(source_zip: bytes) -> dict[str, str]:
    original = files_for_candidate(source_zip)
    if hashlib.sha256(build(source_zip)).hexdigest() != CHAMPION_SHA:
        raise ValueError("official scored 0.180 source not reproduced")
    if set(original) != {"agent.yaml", "prompts/system.md",
                         "configs/sampling.yaml", "eval_config.yaml"}:
        raise ValueError("unexpected champion file set")
    root = original["agent.yaml"]
    if "skills:" in root or root.count("model: gemma-4-31b-it-qat-w4a16-ct") != 1:
        raise ValueError("base agent declaration drift")
    if "  - run_command" not in root or "  - submit_patch" not in root:
        raise ValueError("native tools not present")
    heading = "### 2. Edit by call 10, absolutely by call 12\n\n"
    src = original["prompts/system.md"]
    if src.count(heading) != 1 or "semantic-surface" in src:
        raise ValueError("prompt anchor drift")
    output = dict(original)
    output["agent.yaml"] = root.rstrip() + "\nskills:\n  - skills/semantic-surface\n"
    output["prompts/system.md"] = src.replace(heading, heading + RULE, 1)
    for member, filename in (
        ("skills/semantic-surface/SKILL.md", "SKILL.md"),
        ("skills/semantic-surface/scripts/surface.py", "scripts/surface.py"),
    ):
        file = SKILL_ROOT / filename
        output[member] = file.read_text(encoding="utf-8")
    compile(output["skills/semantic-surface/scripts/surface.py"], "surface.py", "exec")
    if output["eval_config.yaml"] != original["eval_config.yaml"]:
        raise AssertionError("task budget changed")
    if output["configs/sampling.yaml"] != original["configs/sampling.yaml"]:
        raise AssertionError("sampler changed")
    return output


def build_candidate(source_zip: bytes) -> bytes:
    files = candidate_files(source_zip)
    if len(files) != 6:
        raise ValueError("unexpected package contents")
    return make_zip(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse to overwrite candidate")
    blob = build_candidate(args.source_zip.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(blob)
    print("GEMMA_SEMANTIC_SURFACE_CANDIDATE_SHA256=" + hashlib.sha256(blob).hexdigest())
    print("GEMMA_SEMANTIC_SURFACE_NO_TRAINING_NO_SUBMISSION=TRUE")


if __name__ == "__main__":
    main()
