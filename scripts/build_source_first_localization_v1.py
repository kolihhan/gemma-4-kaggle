"""Source-first localization policy, derived only from pinned 0.18 scored 31B control.

One decision-variable difference versus scored Toolcap60/5min control: choose
production-file-first lexical navigation before graph. Model, tools, sampling,
task budgets, base prompt and packaging stay byte-identical. No GPU or model
inference, no Kaggle submission in this module.
"""
from __future__ import annotations

import hashlib
import io
import zipfile

from scripts.build_toolcap60_timeout_recovery import (
    STAMP,
    files_for_candidate as scored_control_files,
)

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
POLICY = """

## Source-first, no test-file distraction (file localization policy)

The FIRST objective is to identify the production source file to edit, not to
collect many tool results. For the initial file search:
1. From the issue, extract at most two concrete symbols/API names, error terms
   or distinctive phrases. Run one narrow lexical search through production
   source files with `run_command` (such as ripgrep/rg, or git grep if rg
   is unavailable); exclude tests, docs, generated examples, and __pycache__
   from the FIRST ranked candidate paths. For example:
   `rg -n -i --glob '*.py' --glob '!**/tests/**' --glob '!**/test_*.py' --glob '!docs/**' 'symbol_or_error' . | head -80`.
   Use a repository-specific non-Python file extension only if necessary.
   If the issue explicitly targets test infrastructure, do not exclude it.
2. If the first query returns nothing, try at most ONE broader semantic or
   related-symbol text search. Rank likely PRODUCTION FILES, then read the
   best file and its immediate caller or existing test. Never assume a test
   file is the implementation merely because it matches the issue.
3. The graph tools have limited coverage, especially of async functions.
   Do NOT call a graph tool just to explore the repo. Only use
   `search_similar_code`, `get_code_neighbors`, or `get_code_subgraph`
   when the target symbol is already grounded in a real source file and
   one targeted relation would resolve a remaining ambiguity.
   An empty or irrelevant graph answer is NOT evidence that an async
   implementation is absent. Return to source text; do not repeat graph.
4. After locating a plausible implementation, inspect the actual function
   and directly relevant test/behavior. Edit only the production cause;
   keep a small patch, run the narrowest available test, inspect git diff
   and always call `submit_patch`. Once a cause is identified, STOP
   searching. Preserve the original safety, budget and no-empty-patch rules.

This is a fallback strategy for localization, not a new code-analysis tool.
Do not add general web search, unnecessary full-repository scans or long
tool explorations.
"""


def files_for_candidate(source_zip: bytes) -> dict[str, str]:
    reference = scored_control_files(source_zip)
    expected = {
        "agent.yaml", "prompts/system.md", "configs/sampling.yaml",
        "eval_config.yaml"
    }
    if set(reference) != expected:
        raise ValueError("Scored control member list changed")
    if reference["agent.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("Scored 31B model drift")
    if reference["eval_config.yaml"].count("max_time_minutes: 5") != 1:
        raise ValueError("Scored 5 minute task budget drift")
    if reference["eval_config.yaml"].count("max_tool_calls: 60") != 1:
        raise ValueError("Scored 60 tool cap drift")
    if reference["eval_config.yaml"].count("max_turns: 80") != 1:
        raise ValueError("Scored 80 turn cap drift")
    if "run_command" not in reference["agent.yaml"] or "submit_patch" not in reference["agent.yaml"]:
        raise ValueError("Native text-shell or submit_patch tool missing")
    if "Source-first, no test-file distraction" in reference["prompts/system.md"]:
        raise ValueError("Candidate policy already applied to base")
    candidate = dict(reference)
    candidate["prompts/system.md"] = reference["prompts/system.md"].rstrip() + "\n" + POLICY
    changed = {key for key in reference if candidate[key] != reference[key]}
    if changed != {"prompts/system.md"}:
        raise AssertionError("One variable not isolated")
    return candidate


def build(source_zip: bytes) -> bytes:
    files = files_for_candidate(source_zip)
    with io.BytesIO() as sink:
        with zipfile.ZipFile(sink, "w") as archive:
            for path, value in sorted(files.items()):
                item = zipfile.ZipInfo(path, date_time=STAMP)
                item.compress_type = zipfile.ZIP_DEFLATED
                item.external_attr = 0o100644 << 16
                archive.writestr(item, value.encode("utf-8"))
        data = sink.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise RuntimeError("Bad source-first candidate ZIP")
    return data


def summary(source_zip: bytes) -> dict:
    data = build(source_zip)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "change": "production-source-first lexical localization, avoid test-first and blind graph",
        "model": MODEL,
        "eval_config": "5 minutes / 60 tool calls / 80 turns unchanged",
        "new_tools": False,
        "no_dev_gpu": True,
        "no_training": True,
        "official_submit": False,
        "official_score_delta": None,
    }
