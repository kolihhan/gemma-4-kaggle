# Public Corpus Summary — 2026-10-31

Generated from repository `tasks.jsonl` by `scripts/analyze_tasks.py` and verified in GitHub Actions.

## Corpus

- Total tasks: **129**
- `fastapi/fastapi`: **67**
- `Textualize/rich`: **48**
- `psf/requests`: **13**
- `encode/httpx`: **1**
- Tasks with non-empty `hints_text`: **0**
- Median problem-statement length: **418 characters**
- Maximum problem-statement length: **10,095 characters**
- `created_at` range: **2023-07-29T07:06:41Z → 2026-06-20T00:20:49Z**

## Reference solution changed-line distribution

Reference patches are labels for analysis only. They must not be exposed to the candidate agent during blind evaluation.

- `1–10`: **60** tasks
- `11–30`: **29** tasks
- `31–80`: **20** tasks
- `81+`: **20** tasks

This is a useful reminder that almost one third of the public tasks have reference fixes above 30 changed lines; a baseline cannot assume every issue is a one-line patch.

## Deterministic diagnostic sample

`python scripts/analyze_tasks.py tasks.jsonl --per-repo 3`

The sample selects low/medium/high reference-patch-size tasks within each repository, up to three per repo. HTTPX only has one public task, so the sample has **10 tasks**:

- `rich_3278`
- `rich_2725`
- `rich_3930`
- `httpx_3672`
- `fastapi_14361`
- `fastapi_14266`
- `fastapi_14609`
- `requests_6592`
- `requests_7502`
- `requests_6757`

## What the sample is for

This is a **diagnostic** sample, not a leaderboard proxy. Use it to answer:

- Can the submission compile/run end-to-end?
- Where does the agent fail: locate, understand, edit, test, repair, context, tool, budget, or submit?
- Does a proposed intervention improve the same fixed sample without merely increasing cost?

Do not tune directly against the provided reference patches. Score through the harness/test path.
