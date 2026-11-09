"""CPU-only builder for a distinct Contract & Impact SWE architecture.

Uses byte-pinned external V2 only as a base-model/tools/budget source. Its
root architecture and prompt are replaced. Does not modify submission/.
"""
from __future__ import annotations
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "experiments/architecture-contract-impact-v0/skill"
PROMPT = """You are an autonomous software engineering agent. Solve the issue
in /workspace with the smallest correct, testable source change.

Task:
{problem_description}

You have access to native repository/file/edit/test tools and an optional
contract-impact Skill. You own the final source tree and submit_patch.

Follow an evidence-driven workflow rather than a fixed first-edit call count:
1. Extract exact observable requirements from the issue. Distinguish missing
   information from requirements the issue actually states. Never fabricate
   behavior that a title or inaccessible external link did not supply.
2. Localize likely implementation, caller, and test entry points with bounded
   reads. For a cross-file or semantic task, form an impact hypothesis and use
   contract-impact's deterministic analyzer to check what evidence and affected
   paths you have identified. The tool never supplies a hidden oracle.
3. Implement the most defensible fix. If source is unclear, run one cheap
   discriminating read/check rather than editing a random module. Keep changes
   reversible and inspect actual git diff after tool errors.
4. Choose focused verification tied to explicit requirements, not just import
   or syntax success. Account for linked entry points and preservation behavior.
   If checks fail, revise the underlying hypothesis, not merely repeat a call.
5. Review the actual diff and status, ensure a materialized intended change,
   and call submit_patch as the final action when evidence supports it. Do not
   mistake a partial green check for full issue correctness.

Budget: the shared task budget is limited. Avoid mandatory repeated planning,
long broad test suites, aimless searches and recurring use of the skill.
The contract-impact tool returns structural observations only. You must reason
about actual code behavior yourself. Never assume its verdict is a grader pass.
"""


def payload(source_zip: bytes):
    files = validate_source_zip(source_zip)
    if set(files) != {
        "agent.yaml", "prompts/system.md", "configs/sampling.yaml", "eval_config.yaml"
    }:
        raise ValueError("unexpected V2 file set")
    original = files["agent.yaml"]
    if original.count("\nskills:") or original.count("\ntools:\n") != 1:
        raise ValueError("unexpected original agent structure")
    for name in ("run_command", "read_file", "edit_file", "write_file", "get_status",
                 "submit_patch", "get_code_neighbors", "search_similar_code",
                 "get_code_subgraph"):
        if original.count("  - " + name + "\n") != 1:
            raise ValueError(f"required native tool missing/duplicated: {name}")
    files["agent.yaml"] = original.rstrip() + "\nskills:\n  - skills/contract-impact\n"
    files["prompts/system.md"] = PROMPT
    files["skills/contract-impact/SKILL.md"] = (SKILL_ROOT / "SKILL.md").read_text()
    files["skills/contract-impact/scripts/contract.py"] = (
        SKILL_ROOT / "scripts/contract.py").read_text()
    return files


def archive(files):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        for path, body in sorted(files.items()):
            item = zipfile.ZipInfo(path, date_time=(2026, 11, 9, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, body.encode("utf-8"))
    return data.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    content = archive(payload(options.source_zip.read_bytes()))
    if options.output.exists():
        raise FileExistsError("will not replace existing candidate")
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_bytes(content)
    print("CONTRACT_IMPACT_ZIP_SHA256=" + hashlib.sha256(content).hexdigest())
    print("CPU_PACKAGE_ONLY_NO_MODEL_NO_SUBMISSION")


if __name__ == "__main__":
    main()
