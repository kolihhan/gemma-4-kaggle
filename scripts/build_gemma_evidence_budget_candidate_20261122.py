"""Build a real Gemma-4 31B Skill-based evidence-budget candidate.

Score-facing (declarative) package, but NO model evaluation or submission.
The tool is optional; the declarative harness does NOT allow competitor-supplied
Python before_tool_callback, so the policy cannot silently override 31B calls.
A true end-to-end uptake and grader test remains necessary.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import zipfile

from scripts.build_requirements_skill_candidate_20261121 import (
    CHAMPION_SHA256, MODEL, EXPECTED, STAMP,
)
from scripts.gemma_evidence_budget_policy_20261122 import self_test

SKILL = "skills/evidence-budget"
SOURCE = Path(__file__).with_name("gemma_evidence_budget_policy_20261122.py")
SKILL_DOC = """---
name: evidence-budget
description: Suggest the next exploration/edit/verification action from observed source evidence and remaining tool/time budget. No code mutation or grading.
---
# Evidence-budget action controller

Call once when search/read calls have repeated without new evidence, or after
the first materialized edit, through run_skill_script with
skill_name="evidence-budget", file_path="scripts/decide.py".

Pass args events_json (JSON-serialized list) containing observed actions:
{"action":"search","paths":["path/actually/seen.py"],"source_evidence":true},
{"action":"edit","patch_changed":true},
{"action":"test","test_outcome":"pass"}.
Also provide calls_left and seconds_left from the latest get_status.
The CLI flags are --events-json, --calls-left, and --seconds-left.

Only give paths you really saw in tool output. Report source_evidence=true
ONLY when a concrete issue-grounded source location was observed, and mark a
test passed ONLY after an actual issue-relevant behavioral check passed.
The controller returns one of FIND_TARGET / READ_TARGET /
CHANGE_SEARCH_CHANNEL / EDIT / VERIFY / REVISE / SUBMIT /
STOP_FAILED_CHECK. It is a policy suggestion, not a hidden oracle.
Do not use the skill repeatedly without newly observed evidence.
Never submit on the strength of the controller's words alone.
"""
PROMPT_DELTA = """
## Evidence-budget pivot
Tool calls are scarce. Do NOT automatically ask the evidence-budget Skill
at the start of every task. After a repeated no-new-path search (3 stale
steps) or the first materialized edit, use the evidence-budget Skill ONCE,
passing truthful observed search/read/edit/test events and exact remaining
tool/time budgets from get_status. Act on its recommendation only when it
agrees with observed source and behavior. If the controller recommends EDIT,
you still must have a concrete issue-grounded target; if it says SUBMIT,
you still must have a changed patch and a passing directly relevant check.
Always preserve time for the final native submit_patch call.
"""


def files_for_candidate(control: dict[str, str]) -> dict[str, str]:
    if set(control) != EXPECTED:
        raise ValueError("unexpected scored champion file set")
    yaml = control["agent.yaml"]
    if yaml.count("model: " + MODEL) != 1:
        raise ValueError("unexpected model")
    if yaml.count("\ntools:\n") != 1 or "skills:" in yaml:
        raise ValueError("requires unmodified no-skills champion")
    required = ("run_command", "read_file", "edit_file", "get_status",
                "submit_patch")
    if any("  - " + name + "\n" not in yaml for name in required):
        raise ValueError("missing required native tool")
    ev = control["eval_config.yaml"]
    for required_budget in ("max_time_minutes: 5", "max_tool_calls: 60",
                            "max_turns: 80"):
        if ev.count(required_budget) != 1:
            raise ValueError("expected frozen champion budget")
    files = dict(control)
    files["agent.yaml"] = yaml.replace(
        "\ntools:\n", "\nskills:\n  - " + SKILL + "\ntools:\n", 1)
    files["prompts/system.md"] = control["prompts/system.md"].rstrip() + (
        "\n" + PROMPT_DELTA)
    files[SKILL + "/SKILL.md"] = SKILL_DOC
    files[SKILL + "/scripts/decide.py"] = SOURCE.read_text()
    if files["eval_config.yaml"] != ev:
        raise AssertionError("budget unexpectedly changed")
    return files


def build_candidate(source_zip: bytes) -> tuple[bytes, dict]:
    from scripts.build_toolcap60_timeout_recovery import (
        build as build_control,
        files_for_candidate as champion_files,
    )
    self_test()
    champion = build_control(source_zip)
    if sha256(champion).hexdigest() != CHAMPION_SHA256:
        raise ValueError("the scored 0.18 Champion source is not exact")
    files = files_for_candidate(champion_files(source_zip))
    with BytesIO() as sink:
        with zipfile.ZipFile(sink, "w") as archive:
            for path, value in sorted(files.items()):
                if path.startswith("/") or ".." in Path(path).parts:
                    raise ValueError("unsafe package path")
                info = zipfile.ZipInfo(path, date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, value.encode("utf-8"))
        package = sink.getvalue()
    with zipfile.ZipFile(BytesIO(package)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(files):
            raise RuntimeError("archive validation failed")
    return package, {
        "champion_sha": CHAMPION_SHA256,
        "candidate_sha": sha256(package).hexdigest(),
        "method": "evidence-budget skill action recommender",
        "model": MODEL,
        "task_timeout_minutes": 5,
        "max_tool_calls": 60,
        "official_score": None,
        "official_submission": False,
    }


if __name__ == "__main__":
    raise SystemExit("Use build_candidate(pinned_source_zip) in private CPU builder")
