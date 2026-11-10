"""V4-CGR: issue-specific locked executable counterexample, from pinned V3-R.

Production difference: the agent can CREATE a diagnostic behavior witness
when existing repository tests do not reproduce the issue, then compare
exactly the same test before and after its source repair. No oracle or training.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import zipfile

from scripts import build_solver_v3r_candidate as v3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/solver-v4/skill/scripts/counterexample.py"
MEMBER = "skills/repair-witness/scripts/counterexample.py"
STAMP = (2026, 11, 10, 0, 0, 0)

NEW_INSTRUCTION = """

## V4-CGR: issue-specific causal counterexample before source edits

A source edit and a successful pre-existing unit test do not establish that
the reported issue is actually fixed. Seek a concrete *behavioral discrepancy*
between the problem statement and the current repository. When the issue
provides an observable input/output contract that existing tests do not cover,
construct ONE minimal issue-specific pytest test_* function with a real
assertion. Use observed public APIs/source; do not make up nonexistent APIs.

Call load_skill("repair-witness") first. Then use run_skill_script(
skill_name="repair-witness",file_path="scripts/counterexample.py",
args={"phase":"before","source":"def test_issue_contract():\\n    ..."})
with actual Python test source. No imports from hidden grader or reference
patch. Never modify, create, or delete repository test files for this purpose.

Use the returned case_id and only when the BEFORE run actually reports an
assertion fail, make a concrete source repair. Afterwards call the identical
locked test by run_skill_script(...,file_path="scripts/counterexample.py",
args={"phase":"after","case-id":"<exact case_id>"}) and interpret the output.
An after pass with before fail is useful *self-generated* evidence, not proof
of hidden issue correctness. Never rewrite the test after seeing the patch
and pretend it is the same before/after witness.

If no reliable issue-specific witness can be synthesized quickly, the before
run passes, or it is blocked, do not get stuck generating speculative tests.
Use existing targeted tests through scripts/witness.py and actual source/
caller contracts. Check relevant pre-existing tests and git diff before
submit_patch, and preserve remaining time. No loops of generated tests.
"""


def payload(source_zip: bytes) -> dict[str, str]:
    files = v3.payload(source_zip)
    if MEMBER in files:
        raise ValueError("counterexample script already packaged")
    script = SOURCE.read_text(encoding="utf-8")
    if "def run(" not in script or "counterexample_repaired" not in script:
        raise ValueError("missing implemented locked witness")
    compile(script, str(SOURCE), "exec")
    files[MEMBER] = script
    manifest = files["skills/repair-witness/SKILL.md"]
    if "counterexample.py" in manifest:
        raise ValueError("unexpected preexisting V4 capability")
    files["skills/repair-witness/SKILL.md"] = manifest + """

## Issue-specific counterexample (CGR)

If existing tests do not exercise a concrete issue requirement, generate
one small pytest test function from the observed API and issue statement.
Call run_skill_script:
- BEFORE: file_path="scripts/counterexample.py",
  args={"phase":"before","source":"def test_issue_contract():\\n    assert ..."}
- AFTER: file_path="scripts/counterexample.py",
  args={"phase":"after","case-id":"<case_id returned by BEFORE>"}

The BEFORE run must fail with an actual pytest AssertionError to show
an issue-specific discrepancy. The script stores the exact test outside
the repository and refuses to replace its source in AFTER. A pass on the
unchanged test is evidence of a local behavioral improvement only; it does
not certify hidden evaluation requirements or test relevance. Baseline pass
or blocked is NOT a counterexample. Use one short witness at most, and
prefer existing tests when a suitable one already exists.
"""
    files["prompts/system.md"] += NEW_INSTRUCTION
    if files["eval_config.yaml"].count("max_time_minutes: 5") != 1:
        raise ValueError("V3-R budget drift")
    if files["eval_config.yaml"].count("max_tool_calls: 28") != 1:
        raise ValueError("V3-R tool call cap drift")
    if files["agent.yaml"].count("model: gemma-4-31b-it-qat-w4a16-ct") != 1:
        raise ValueError("unexpected model")
    return files


def build(source_zip: bytes) -> bytes:
    files = payload(source_zip)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, source in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.encode("utf-8"))
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise ValueError("corrupt V4 candidate ZIP")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():
        raise FileExistsError("refuse overwrite candidate")
    data=build(a.source_zip.read_bytes())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(data)
    print("V4_CGR_CANDIDATE_SHA256="+hashlib.sha256(data).hexdigest())
    print("V4_CGR_MODEL=gemma-4-31b-it-qat-w4a16-ct")
    print("V4_CGR_BUDGET=5min:28calls:80turns")
    print("V4_CGR_OFFICIAL_SUBMISSION=FALSE")


if __name__=="__main__":
    main()
