"""V3-R: a single-writer 31B coder with an executable real-test witness Skill.

This is a research candidate, NOT a scored winner. Preserve the exact
Apache-2.0 V2 model/native-tools/sampling as control and use a 5-minute
per-task envelope to avoid the timed-out unrestricted 8-minute Toolcap60.
Only the root policy, Skill files and task-time are changed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import re
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / "experiments/solver-v3/skill/scripts/witness.py"
MANIFEST = ROOT / "experiments/solver-v3/skill/SKILL.md"
STAMP = (2026, 11, 10, 0, 0, 0)
MODEL = "gemma-4-31b-it-qat-w4a16-ct"

PROMPT_SUFFIX = """

## Solver V3-R: source-grounded diagnosis and test feedback

Use observed repository code, caller contracts and the issue text to decide
what behavior needs repairing. Do not invent requirements or fake test results.
A nonempty diff does not mean a correct repair.

The repair-witness Skill is a REAL executable targeted pytest witness, NOT a
second LLM or hidden oracle. When an applicable existing test is known,
FIRST call load_skill with skill_name="repair-witness" and read its protocol.
Then call run_skill_script with skill_name="repair-witness",
file_path="scripts/witness.py",
args={"phase":"before","target":"relative/test_file.py::test_name"} before
the edit IF it fits the time budget, then rerun with phase="after" and the
same target after editing. Never call a skill script before loading its Skill.
If an existing narrow test is only found after editing, run phase="after"
only and recognize baseline_unavailable. Never invent a test path.

Read the tool's actual status/comparison/evidence values. If regression is
introduced or the relevant check still fails, inspect the concrete traceback,
fix the observed cause rather than repeating the same edit or broader search,
and rerun at most one bounded repair cycle. If the check is blocked, do not
claim it passed. The Skill may be skipped when no relevant test exists or
when too little task time remains; do not waste scarce calls on ritual steps.

Use a narrow source change, verify the actual git diff/status, and own the
final submit_patch. Time is shared across the complete Kaggle evaluation.
"""

def payload(source_zip: bytes) -> dict[str, str]:
    base = validate_source_zip(source_zip)
    if set(base) != {
        "agent.yaml", "prompts/system.md", "configs/sampling.yaml",
        "eval_config.yaml"
    }:
        raise ValueError("unexpected pinned V2 archive members")
    if base["agent.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("wrong root 31B model")
    if re.search(r"(?m)^skills\s*:", base["agent.yaml"]):
        raise ValueError("unexpected skill already declared")
    baseline_budget = base["eval_config.yaml"]
    if (baseline_budget.count("max_time_minutes: 8") != 1 or
            baseline_budget.count("max_tool_calls: 28") != 1 or
            baseline_budget.count("max_turns: 80") != 1):
        raise ValueError("pinned V2 eval budget drift")
    if not MANIFEST.is_file() or not WITNESS.is_file():
        raise FileNotFoundError("V3-R real Skill script/manifest missing")
    manifest = MANIFEST.read_text(encoding="utf-8")
    witness = WITNESS.read_text(encoding="utf-8")
    if not manifest.startswith("---\nname: repair-witness\n"):
        raise ValueError("invalid repair-witness SKILL.md frontmatter")
    if "def run_witness(" not in witness or "run_skill_script" not in manifest:
        # Script must be runnable Python, not an empty placeholder.
        # The manifest documents direct execution parameters and return codes.
        raise ValueError("invalid repair-witness declaration")
    compile(witness, str(WITNESS), "exec")
    out = dict(base)
    out["agent.yaml"] = base["agent.yaml"].rstrip() + (
        "\nskills:\n  - skills/repair-witness\n"
    )
    out["prompts/system.md"] = base["prompts/system.md"].rstrip() + (
        "\n" + PROMPT_SUFFIX
    )
    out["eval_config.yaml"] = baseline_budget.replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1
    )
    out["skills/repair-witness/SKILL.md"] = manifest
    out["skills/repair-witness/scripts/witness.py"] = witness
    assert out["configs/sampling.yaml"] == base["configs/sampling.yaml"]
    assert out["eval_config.yaml"].replace(
        "max_time_minutes: 5", "max_time_minutes: 8", 1
    ) == baseline_budget
    return out


def build(source_zip: bytes) -> bytes:
    files = payload(source_zip)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, text in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, text.encode("utf-8"))
    content = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(files):
            raise ValueError("V3-R ZIP integrity/member check failed")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse to overwrite candidate ZIP")
    result = build(args.source_zip.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(result)
    print("SOLVER_V3R_ZIP_SHA256="+hashlib.sha256(result).hexdigest())
    print("SOLVER_V3R_BASE_MODEL="+MODEL)
    print("SOLVER_V3R_BUDGET=5min:28calls:80turns")
    print("SOLVER_V3R_OFFICIAL_SUBMISSION=FALSE")


if __name__ == "__main__":
    main()
