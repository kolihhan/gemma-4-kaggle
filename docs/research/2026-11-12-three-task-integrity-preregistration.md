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

## Completed experimental result — official public-dev wheelhouse CPU runtime

[Authenticated one-shot private CPU Action 43070401519](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43070401519) finished **SUCCESS** at 2026-11-11 17:44 UTC. The exact preregistered three issues were tested; 6 total `verify_task` calls: noop + gold per issue. No GPU, inference, or official Kaggle submission. Static gate and synthetic unit tests passed.

| ID | Model-visible statement length | External URL / hints | No-op | Gold | Preregistered category |
| --- | --- | --- | --- | --- | --- |
| `fastapi_14487` | 204 characters | no URL, 0 hint chars | unresolved, exit 1 | **resolved, exit 0** | **informative_gold_pass_noop_fail** |
| `rich_3782` | 68 characters | URL present, 0 hint chars | unresolved, exit 1 | **resolved, exit 0** | **informative_gold_pass_noop_fail**, short pointer-risk |
| `requests_7427` | 394 characters | URL present, 0 hint chars | unresolved, exit 1 | **unresolved, exit 1** | **confounded_gold_fails** |

### Adversarial implications

1. **Requests_7427 is an invalid correctness datapoint for this scorer epoch.** The bundled official gold fix failed, so we cannot blame the two models' failures on their edits. This does **not** identify why gold failed (wheel shadow, missing dependencies, tests, or other); do not assert the specific community-described empty-patch behavior occurred in our current runtime. Our no-op also failed, unlike one documented community epoch.
2. **Rich_3782 is verifier-informative but spec-short.** The model received only 68 characters including a URL, with no hints. Upstream PR refers to rich Issue #3727 for the real padding/wrapping reproduction. Because Kaggle's sandbox is offline, the model may not receive the issue body; this is a strong **information-sufficiency risk**, not formal proof no local evidence exists.
3. **FastAPI_14487 is locally informative** (gold pass, no-op fail) and has a 204-character statement with no external URL. It is the cleanest *of these three* for post-hoc patch-synthesis diagnosis, not a sufficient denominator for generalization.
4. The earlier 31B paired prompt comparison has **0/3 vs 0/3 observed** but its actionable clean-and-specified effective denominator is at most **1** without a detailed issue-text audit. No causal model-quality conclusion or optimizer promotion follows.
5. Older [discriminating-evidence gold screen](https://github.com/kolihhan/gemma-4-kaggle/blob/research/dual-agent-recovery-v0-20261108/docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json) had `fastapi_14487` gold-pass as well; this checks consistency on that case, not broad scorer stability.

### Decision after completing the gate

**Stop deriving prompt superiority, model capability, or PPO training reward from this three-task panel.** Retain the scored account best 0.18 V2, freeze the no-gain prompt-only challenger and the failed V5 nested topology. Prefer deeper root-cause analysis on a separate preselected sample that passes both gold and noop gates; do not rerun training or move to PPO until reliable reward and issue-information availability are established. Preserve the existing independent V10 schedule and do not call its public 0.22 observation a new user-account score.
