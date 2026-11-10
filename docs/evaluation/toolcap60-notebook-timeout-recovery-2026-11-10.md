# Toolcap60 notebook timeout: incident and bounded recovery

**Date:** 2026-11-10 MYT. **Classification:** official notebook/runtime failure, not a measured semantic-solver failure. **No score gain claimed.**

## Verified observations

- User reported Kaggle error **"Notebook Timeout — Your submission notebook exceeded the allowed runtime"** for the new Toolcap60 submission workflow.
- [Official accepted code submission Action 42617788829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617788829), ref **58164176**, generated ZIP SHA-256 `e05753aed22f360bfdc74942c0b1b432bc1aca8eeb0741804eb023f9714018f6`.
- [Authenticated score read Action 42648039124, November 10 rerun](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42648039124) confirmed `SubmissionStatus.COMPLETE` with blank `publicScore` and `privateScore`, consistent with the user's visible timeout message. Kaggle CLI's COMPLETE listing by itself does not distinguish code success from notebook failure; combine with the user-supplied error.
- **Scored controls:** unchanged attributed V2 (8 minutes, 28 tool calls) **0.17** Public, ref `58019162`; historical 5-minute / 28-call V2 **0.15**, ref `58045795`. Those scores establish that the original V2 and a shorter task-time variant have completed scoring before, but do not predict this future run.
- Failed candidate changed V2 **28 → 60 tool calls** while retaining **8 minutes per task**, 80 turns and 31B thinking.
- Official competition time limit: **12 hours total** across all issue runs including sandbox startup, **excluding patch validation**. The public information says the hidden set has **about 120 issues**; hidden count, total setup cost, per-task wall clock and service stalls are unknown. Kaggle's generic "Notebook Timeout" category does not reveal the failing stage.

## Root-cause analysis: credible, not proven

- **Plausible:** extra tool-call capacity makes it more likely to spend the full 8-minute window on difficult issues, causing aggregate compute to exceed 12 hours. A conservative upper-envelope calculation assuming 120 tasks at 8 minutes gives 960 task-minutes *before setup*, >720-minute limit. This is a worst-case bound, not an observed runtime.
- **Other possible causes:** server-side vLLM request stalls, startup overhead, a changed hidden task mix, slow sandbox tools, and general Kaggle service variability. No private task-level timing logs for ref 58164176 have been verified. Do **not** claim "60 calls caused the timeout" as a proved fact.
- **Control evidence:** 28-call/8-minute original 31B already received a scored public result, so a blanket claim that 8-minute configuration *always* times out is contradicted.

## Recovery, distinct from research novelty

- Build a **one-variable recovery candidate** by deriving the *failed* Toolcap60 archive and changing only `evaluation.max_time_minutes: 8 → 5`. Keep model, prompt, native tools, sampling, `max_tool_calls: 60`, command timeout and 80 turns identical to the failed archive.
- Under the **approximation** of 120 hidden tasks, 5 × 120 = 600 task-minutes, leaving ~120 minutes for startup/other agent-billed costs. This is **not an unconditional guarantee** of finishing the full notebook; tasks, setup, Kaggle platform and patch validation can vary.
- Reproducible builder `scripts/build_toolcap60_timeout_recovery.py` and focused tests `tests/test_build_toolcap60_timeout_recovery.py`; official CPU preflight/one-shot Kaggle submit program `scripts/submit_toolcap60_timeout_recovery_once.py`, Actions `.github/workflows/toolcap60-safetime5-official-once.yml`.
- Run one CPU source/official-ADK compile test, private CPU kernel round-trip exact ZIP verification, authentic quota/duplicate check, and **at most one new official score submission** under distinct description marker `toolcap60-safetime5-v1-20261110`. No training and no duplicate private GPU test.
- **Selection/success metric:** first clear the Notebook Timeout failure and receive any valid score; then compare to 0.15 (5-minute reference) and 0.17 (best scored). A new official result is not proof of a scientific improvement due to host variation.

## Research status unaffected

The user’s goal remains a genuinely stronger semantic-repair coding agent, not indefinite time/tool-call tuning. Timeout recovery is an **operational repair**, not Solver V3, not an independent semantic-repair advance. After one recovery outcome, halt this timeout configuration lane and resume the goal-aligned plan in `docs/design/goal-aligned-replan-2026-11-10.md`. If it also times out, inspect infrastructure and platform-specific failure conditions rather than blindly reducing caps again.

**Run status at writing:** [GitHub Action 42744871831](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42744871831) was running, and no new Kaggle submission receipt existed at that moment. Check the authoritative run and authenticated receipt for later results.
