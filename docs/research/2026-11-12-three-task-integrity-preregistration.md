# Three-task integrity gate before further 31B optimisation — 2026-11-12

## Motivation and strongest known evidence

The completed preselected 31B paired pilot ([Action 43057377220](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43057377220)) yielded **0/3 resolved** for each of pinned V2 and a public prompt-only treatment, all six producing materialised patches, every final grader exit **1**. The subsequent private trace audit ([Action 43069386668](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43069386668)) found **13 nonzero structured command exits**; 10 occurred before later edits, 3 after the final recorded edit, but these are not verified issue-relevant failed tests. Rewriting prompts or launching PPO based on these counters alone would be an unjustified escalation.

New independent issue-level context (post-hoc public upstream, **not fed to an agent**):

- [FastAPI #14487](https://github.com/fastapi/fastapi/pull/14487) is a safe exception-handling documentation/tutorial update across documentation, example and tests. Its official gold patch previously passed in project metadata from 2026-11-06, though wheelhouse/runtime may drift.
- [Rich #3782](https://github.com/Textualize/rich/pull/3782) only refers to the linked [Issue #3727](https://github.com/Textualize/rich/issues/3727) for the full syntax/padding reproduction. The exact visible benchmark text **may** omit essential requirements. Never infer exact benchmark input from upstream alone.
- [Requests #7427](https://github.com/psf/requests/pull/7427) concerns no_proxy domain-boundary semantics. [Kaggle community discussion #747248](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747248) documents a possible local scorer confound: a bundled Requests wheel can shadow patched source, causing an empty patch to pass in some environments. This is community evidence, **not proof it happened in our 31B evaluation**.
- [Community discussion #746944](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746944) reports some public-development tasks have only title and URL, with no hints and an offline sandbox. These are not official prevalence estimates of private scored tasks.

## Frozen integrity question

> Under the official currently mounted scorer wheelhouse on the exact same **three already-evaluated** public-development tasks, does untouched source fail and a reference patch pass? How much issue text does the model actually receive?

Use one **PRIVATE CPU-only Kaggle** kernel with the official `swegemma` verifier, current task snapshots and original wheelhouse, no model weights or GPU. No Kaggle competition submission. Two independent `verify_task` calls per task: no-op (empty candidate patch), and gold (provided public-development reference patch, private runtime only). Record only pass/fail, exit codes, duration and anonymous task-input metadata (statement character count, hints character count, URL present, short title/link pointer-risk heuristic). **Do not export reference patch/source diff/task text/test result bodies.** This study is fully retrospective and cannot estimate out-of-sample solver accuracy.

### Predeclared decision gate

| Gold | No-op | Interpretation | Research decision |
|---|---|---|---|
| Pass | Fail | Locally informative | Candidate for semantic/verification audit; still check issue text sufficiency |
| Pass | Pass | Non-discriminative verification | Do NOT use as training reward/effectiveness evidence |
| Fail | Fail | Inconclusive scorer/dependency failure | Do NOT attribute candidate failure to policy; investigate environment |
| Fail | Pass | Unexpected/invalid reward | Exclude from accuracy conclusions and investigate scorer |
| Error | Any | Environment/infrastructure issue | Stop; no data-driven training or leaderboard extrapolation |

Even if gold passes and no-op fails, this does **not** rule out installed-wheel shadowing in every possible test path or prove the issue statement contains enough information. As a separate diagnostic, `short_link_pointer_risk` marks only a short URL-containing task statement; it is **not** a human sufficiency verdict.

## Frozen files and execution

- Runtime: `kaggle/paired_three_task_integrity_cpu.py` (no GPU, no model, official wheelhouse).
- Renderer: `scripts/render_paired_three_task_integrity_cpu.py`.
- Synthetic tests: `tests/test_paired_three_task_integrity_cpu.py`.
- Single-run action: `.github/workflows/paired-three-task-integrity-cpu-once-20261112.yml`.
- Task IDs frozen **before** this run: `fastapi_14487`, `rich_3782`, `requests_7427`. These are historical exposed tasks, **not** new holdout.
- Public repo receives only code, run status, safe task identifiers, categorical metadata. The reference gold patch remains inside the Kaggle runtime.
- No changes to `submission/`, no training, no new official Kaggle entry; the separate date-gated attributed v10 one-shot remains unchanged.

## Research priorities after integrity

1. Exclude noninformative or infrastructure-confounded tasks **from estimating policy effects**, while retaining them as a diagnostic count.
2. For sufficient and informative tasks, inspect full failure semantics privately. Attribute a model-limited repair problem only if actionable requirements/verification exist.
3. Prefer a small paired controlled experiment that changes a real mechanism (e.g. a structured, tool-observed repair loop) over generic prompt rewrites or nested agents.
4. Reopen PPO/GRPO **only** after independently checkable rewards and a clean train/eval split are demonstrated. No claim that RL is inherently inferior to prompt-only methods.
