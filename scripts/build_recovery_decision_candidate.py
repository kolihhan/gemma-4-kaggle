"""Build matched CPU-only Gemma 4 31B recovery-role candidate archives.

Requires the byte-pinned, externally attributed Budget-Fit V2 submission ZIP.
This script never invokes a model, launches Kaggle, or alters submission/.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip

ARMS = ("fresh_coder", "recovery_reviewer")
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
ROLE = "recovery_adviser"

# Identical in both arms; the intervention is only the child-role instruction.
CALL_POLICY = """
### Optional one-shot recovery advice
Continue with the original Budget-Fit workflow and all existing native tools.
Only if a concrete issue-relevant observation contradicts the current repair
hypothesis and you cannot identify a different useful next action, consider one
call to recovery_adviser. Do not call automatically after a test fails. Before
calling, inspect the actual workspace with native tools and provide the adviser
with a concise evidence packet: issue requirement, relevant code facts, actual
current diff, attempted edits, exact test command/output, and remaining time.
Do not provide an imagined patch as an observed change or any hidden reference.
Ask for at most one falsifiable next action; a response of INSUFFICIENT is valid.
Preserve useful changes; apply an advised edit only after checking it yourself.
Keep time for the final diff and submit_patch. Do not call the adviser twice.
"""

COMMON_ADVISER = """You have no tools and cannot edit files or submit.
You receive ONLY the caller's current issue-and-evidence packet.
Do not claim access to the full repository, the task grader, or hidden tests.
Distinguish stated facts from hypotheses. Do not invent an observed test.
Suggest at most one concrete, falsifiable next action with a reason.
If the evidence is insufficient to distinguish a useful action, say so.
A failing test alone never proves that reverting is best.

Answer briefly using exactly these labels:
OBSERVED:
HYPOTHESIS:
NEXT_ACTION:
FALSIFIER:
UNCERTAINTY:
"""

ROLE_DELTA = {
    "fresh_coder": """Act as a fresh ordinary coding assistant asked to continue a repair.
Reason from the issue and actual evidence, without trusting the previous
coder's proposed explanation. Choose the most useful next coding action.
""",
    "recovery_reviewer": """Act as an independent recovery critic for a stalled repair.
Look first for a counterexample to the current hypothesis, an edit that did
not reach the tree, a missing requirement, or a regression introduced by the
current candidate. Recommend one discriminating check or narrow repair.
""",
}

ADVISER_YAML = f"""agent_class: LlmAgent
name: {ROLE}
model: {MODEL}
description: Provide one evidence-grounded recovery action if the repair has stalled.
instruction: !include ../prompts/recovery-adviser.md
include_contents: none
tools: []
generate_content_config:
  temperature: 0.2
  top_p: 0.95
  max_output_tokens: 768
  thinking_config:
    include_thoughts: true
    thinking_budget: 256
"""

TOOL_STANZA = """  - agent_tool:
      config_path: sub_agents/recovery-adviser.yaml
      skip_summarization: true
"""


def candidate_files(source_zip: bytes, arm: str) -> dict[str, str]:
    """Keep V2 sampling, eval budget and all native tools byte-identical."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    original = validate_source_zip(source_zip)
    if set(original) != {
        "agent.yaml", "prompts/system.md", "configs/sampling.yaml",
        "eval_config.yaml",
    }:
        raise ValueError("unexpected pinned V2 members")
    root = original["agent.yaml"]
    if (root.count("\ntools:\n") != 1
            or root.count("\ngenerate_content_config:") != 1
            or "agent_tool:" in root or "sub_agents:" in root):
        raise ValueError("unexpected agent structure")
    native_tools = re.findall(r"(?m)^  - ([a-z_]+)$", root.split("\ngenerate_content_config:", 1)[0])
    required = {"run_command", "read_file", "edit_file", "submit_patch", "get_status"}
    if not required.issubset(native_tools) or len(native_tools) != len(set(native_tools)):
        raise ValueError("V2 native tool contract changed")
    new_root = root.replace(
        "\ngenerate_content_config:",
        "\n" + TOOL_STANZA + "generate_content_config:",
        1,
    )
    if not all(f"  - {tool}\n" in new_root for tool in native_tools):
        raise AssertionError("native tool lost")
    if new_root.count("agent_tool:") != 1:
        raise AssertionError("unexpected tool count")
    result = dict(original)
    result["agent.yaml"] = new_root
    result["prompts/system.md"] = original["prompts/system.md"].rstrip() + "\n\n" + CALL_POLICY
    result["sub_agents/recovery-adviser.yaml"] = ADVISER_YAML
    result["prompts/recovery-adviser.md"] = COMMON_ADVISER + "\n" + ROLE_DELTA[arm]
    return result


def deterministic_zip(files: dict[str, str]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for path, value in sorted(files.items()):
            entry = zipfile.ZipInfo(path, (2026, 11, 8, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, value.encode("utf-8"))
    return out.getvalue()


def build(source_zip: bytes) -> dict[str, bytes]:
    """Two arms: all files except child instruction have identical bytes."""
    files = {arm: candidate_files(source_zip, arm) for arm in ARMS}
    changed = {key for key in files[ARMS[0]] if files[ARMS[0]][key] != files[ARMS[1]][key]}
    if changed != {"prompts/recovery-adviser.md"}:
        raise AssertionError(f"comparison not role-only: {sorted(changed)}")
    return {arm: deterministic_zip(files[arm]) for arm in ARMS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    archives = build(args.source_zip.read_bytes())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for arm, content in archives.items():
        path = args.out_dir / f"{arm}.zip"
        if path.exists():
            raise FileExistsError(f"will not overwrite: {path}")
        path.write_bytes(content)
        manifest[arm] = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
