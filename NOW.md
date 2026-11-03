# NOW — 2026-11-03

## North star

Build a competitive E4B software-engineering agent by learning which local signals actually transfer to Kaggle, not by chasing individual development tasks or public-LB noise.

Research must be resource-aware and mechanism-first: reuse existing evidence, avoid tuning to inspected tasks, explain why an intervention should work, and deploy only the smallest candidate that survives a discriminating test.

## Current decision

**Keep frozen Reliability-v1 unchanged while its real Kaggle submission is pending. Do not rerun the 17-task development diagnostic.**

Reliability-v1 is a single-root E4B agent. Relative to the previous topology experiment, model, sampling, runtime budget, and code-intelligence tool surface remain frozen. The intended behavioral changes are generic localization discipline, edit/tool-recovery discipline, targeted verification, and direct root-agent submission ownership.

The next scientific candidate is **not selected yet**. Current development evidence updates the hypothesis ranking, but it cannot promote a new candidate.

## Anti-overfit boundary

The existing 17-task topology denominator is development-only: task IDs, outcomes, and traces have been inspected. It may diagnose regressions and failure modes but cannot be called blind and cannot gate a new submission.

The Reliability-v1 candidate was frozen before leaderboard feedback. Do not add FastAPI/Rich-specific rules or tune prompts against individual failures. Any next candidate must name one major variable, one causal mechanism, and one falsifier; promotion evidence requires a new untouched denominator.

Pre-registered public-LB prediction lives in `docs/evaluation/reliability-v1-preregistered-prediction.json`:

- point: **0.08**
- interval: **0.05–0.12**

The purpose is calibration of our prediction process, not target-chasing.

## Verified deployment state

### Static / builder

- Frozen-candidate unit tests and compile checks: **PASS**.
- Fresh current official scorer-wheelhouse validation: **PASS**.
- Reliability-v1 builder kernel produced an exact five-file `submission.zip`: **PASS**.
- Kaggle `CreateCodeSubmission` request shape: **PASS**.

### Real Kaggle submissions

- Baseline submission ref **57879765**, description `baseline-e4b-v0`, submitted 2026-11-01 17:59:25 UTC: **COMPLETE**, public score **0.03**.
- Frozen Reliability-v1 submission ref **57921371**, description `reliability-v1:slot-clear:pred=0.08:[0.05,0.12]`, submitted 2026-11-02 20:59:37 UTC: **PENDING** as of the read-only probe run **41585360688** on 2026-11-03 05:41 UTC.
- Do not submit a duplicate Reliability-v1 candidate while ref 57921371 is pending.

### Development diagnostic — complete, do not rerun

Canonical run: `deploy-reliability-v1.yml` run **41485671952**, diagnostic job **125417231948**.

- requested/completed: **17 / 17**
- resolved: **1 / 17** (`fastapi_9425`)
- non-empty patches: **13 / 17**
- empty patches: **4 / 17**
- mean tool calls: **10.41**
- median tool calls: **10**
- mean duration: **89.21 s**
- median duration: **85.61 s**
- call-cap exhaustions: **0**
- non-empty unresolved patches with non-zero verification exit: **12 / 12**

The development result is at the lower bound of the pre-registered 1–3 resolved expectation. It is diagnostic evidence only.

## Current mechanism interpretation

Canonical note: `docs/research/reliability-v1-diagnostic-interpretation-2026-11-03.md`.

The current aggregate weakens a **pure compute-efficiency** explanation as the immediate repair-quality bottleneck: the agent is not generally exhausting its call budget, yet almost every produced patch still fails relevant verification.

The stronger unresolved surface is **information quality / root-cause correctness / repair convergence**:

- F2 UNDERSTAND may be wrong before editing;
- F3 EDIT may produce incomplete or semantically wrong patches;
- F5 REPAIR may fail to use the verification signal to converge.

The aggregate cannot yet distinguish F2 vs F3 vs F5, so do not claim a single cause from these 17 tasks.

## Provisional breakthrough ranking

This ranking may guide research while Reliability-v1 is pending; it does **not** authorize implementation on the frozen candidate.

1. **Evidence-first repair for concrete behavioral contracts** — conditionally reproduce/identify the smallest behavioral witness before editing, then reuse it after editing. Goal: improve the information available to F2/F3/F5 rather than add generic compute.
2. **Test-aware retrieval** — connect likely source locations to the smallest relevant existing test/executable path before mutation.
3. **Adaptive compute / value-of-information routing** — retain as an efficiency mechanism, but do not equate it with simply reducing calls. Escalate only when the next action can discriminate between hypotheses.
4. Conditional edit/tool-schema reliability path.
5. Conditional bounded rescue instead of an always-on verifier.

Do not bundle these into a v1.1 mixture.

## Resource policy

- Existing run/artifact answers the question -> **reuse it**.
- Cheap GitHub Actions for static checks, read-only probes, reproducibility, artifacts, and deployment orchestration -> **use freely** in this public repo.
- Kaggle GPU/full diagnostic -> **only when it can falsify a named hypothesis or change a decision**.
- Do not duplicate an active submission or diagnostic.
- Do not spend compute merely to get another sample from an already-inspected denominator.

Competition Data remains runtime-only for new runs. Public repository status is not a scientific blocker under `PUBLIC_VISIBILITY.md`; legacy exposure cleanup remains deferred and must not alter the experiment.

## Next decision after Kaggle feedback

When ref **57921371** reaches a terminal state:

1. compare its actual public score with the pre-registered **0.08 [0.05, 0.12]** prediction and with the baseline **0.03** outcome, without treating one leaderboard point as causal proof;
2. explain the prediction error and reconcile it with the 1/17 development diagnostic;
3. choose exactly one next mechanism;
4. freeze a **new untouched evaluation denominator before inspecting its traces**;
5. pre-register the targeted failure surface, expected observable effect, resource cost, and falsifier;
6. only then implement and deploy the smallest candidate that expresses that mechanism.

Until then: **no new expensive experiment and no prompt tuning against the 17 known tasks.**
