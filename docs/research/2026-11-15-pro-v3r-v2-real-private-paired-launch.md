# 2026-11-15 — PRO continuation: launch paired 31B V3R vs V2

## Why this is not another prompt-only test

The prior six actual 31B task traces have edits but zero grader-resolved issues. An isolated host Python post-edit hook is not yet demonstrated to be accepted by the competition's restricted `adk_submission` YAML runtime, so **do not claim this hook is a deployable competition intervention**.

The repo already has a distinct, legal **V3-R `repair-witness` Skill** that was tested via official `swegemma` ADK CodeExecutor with a scripted model. It had never shown real 31B autonomous uptake or paired resolution. Rather than build a second synthetic verifier, **test V3R with genuine 31B on fresh tasks now.**

## Actual execution and immutable contract

- **Preregistered** [3-issue paired manifest](../../experiments/solver-v3/pro-v3r-vs-v2-fresh-paired-20261115.json) before private execution. 1 randomly ID-hash-selected public-dev issue from FastAPI, Rich and Requests, excluding 34 previously exposed IDs; no issue text/reference solution consulted for selection.
- Actual model: **Gemma 4 31B**. Pinned source V2 ZIP SHA256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3` vs legal V3R ZIP SHA256 `ae8201c0ce30daf581102ef5d22886f8a4dcebfae47236dffb02ffa6426f9b0c`.
- Equal per-task budget **5 minutes / 28 calls / 80 turns**, identical model+sampling, 3 matched issues and 6 actual independent grader task evaluations, alternating order. Only difference is the real Skill and instructions to use it, not a larger model or extra time.
- **CPU authentic-source preflight PASS**, [Action #43689003780](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689003780). It rendered a full private kernel with exact known candidate SHA, no GPU, no competition submission.
- **Private real 31B run launched**, [Action #43689217134](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689217134). GitHub steps through one private Kaggle kernel push completed successfully and its poll step was still in progress at last check. Exact private ref: `kolihhan/gemma4-v3r-v2-pro-nov15-v1`. No new official competition submission, training, or score claimed.
- Primary decision: grader-resolved **rescues minus regressions** on the SAME issues. Secondary: model *actually* calls and consumes the Skill test result, patch materialization, time/call budget. A synthetic scripted Skill event is **not** counted as uptake. Zero real rescues, or more regressions, retires V3R; one rescue on three tasks is preliminary until validated on a separate source.
- Current authenticated best public Gemma remains **0.18**. Independent official submission #58350278 is still **PENDING**, verified [Action #43688525240](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43688525240).
