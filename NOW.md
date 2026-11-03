# NOW — 2026-11-03

## North star

Build a competitive E4B software-engineering agent by learning which local signals actually transfer to Kaggle, not by chasing individual development tasks or public-LB noise.

Research must be resource-aware and mechanism-first: reuse existing evidence, avoid tuning to inspected tasks, explain why an intervention should work, and deploy only the smallest candidate that survives a discriminating test.

## Current decision

**Keep frozen Reliability-v1 unchanged while its real Kaggle submission is pending. Do not rerun the 17-task development diagnostic and do not add more prompt rules to it.**

Reliability-v1 is a single-root E4B agent. Relative to the previous topology experiment, model, sampling, runtime budget, and code-intelligence tool surface remain frozen. The intended behavioral changes are generic localization discipline, edit/tool-recovery discipline, targeted verification, and direct root-agent submission ownership.

The next scientific candidate is **not selected yet**. Current development evidence now identifies a stronger next mechanism — **evidence-before-mutation** — but does not yet select its implementation or authorize deployment.

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
- Frozen Reliability-v1 submission ref **57921371**, description `reliability-v1:slot-clear:pred=0.08:[0.05,0.12]`, submitted 2026-11-02 20:59:37 UTC: **PENDING** at the latest read-only probe in this research pass.
- Do not submit a duplicate Reliability-v1 candidate while ref 57921371 is pending.

### Development diagnostic — complete, do not rerun

Canonical run: `deploy-reliability-v1.yml` run **41485671952**, diagnostic job **125417231948**.

- requested/completed: **17 / 17**
- resolved: **1 / 17**
- non-empty patches: **13 / 17**
- empty patches: **4 / 17**
- mean tool calls: **10.41**
- median tool calls: **10**
- mean duration: **89.21 s**
- median duration: **85.61 s**
- call-cap exhaustions: **0**
- non-empty unresolved patches with non-zero evaluator verification exit: **12 / 12**

Against the earlier single-root topology run on the same denominator, Reliability-v1 kept resolution at **1 -> 1** while total evaluator runtime fell by about **12%** and mean non-empty patch size fell by about **20%**. The development result is diagnostic evidence only.

## Post-hoc trace mechanics audit — complete

Canonical audit: GitHub Actions run **41590900152**, job **125767140355**, compact artifact **13209917848**.

Execution cost/profile:

- reused two already-completed Kaggle kernel outputs;
- **no new Kaggle kernel, GPU inference, task execution, or competition submission**;
- analyzer synthetic tests: **8/8 PASS**;
- `py_compile`: **PASS**;
- safe-output gate: **PASS**;
- artifact contains compact derived JSON only.

Same-classifier A/B, earlier single-root -> Reliability-v1:

- resolved: **1 -> 1**
- tasks with targeted evidence before first mutation: **0 -> 0**
- targeted-test calls: **3 -> 3**
- tasks with no targeted test: **15 -> 14**
- broad-test calls: **14 -> 10**
- localization-tool calls: **0 -> 4**
- total mutations: **40 -> 39**
- failed targeted check followed by a repair mutation: **0 -> 0**
- submit after latest classifier-recognized targeted failure: **1 -> 2**

The analyzer is conservative, so absolute targeted-test counts may be underestimates. Use these numbers for same-classifier A/B mechanism comparison, not as exhaustive trace labels.

## Current mechanism interpretation

Canonical note: `docs/research/reliability-v1-diagnostic-interpretation-2026-11-03.md`.

### What Reliability-v1 actually improved

It became **more restrained**, not demonstrably more capable:

- less broad testing;
- fewer reads;
- some use of code-intelligence localization;
- smaller patches and lower runtime;
- edit recovery shifted some mutations from direct `edit_file` to asserted script paths.

These changes did not improve the 17-task resolved count.

### Strongest missing capability

Both single-root versions show **0/17 targeted behavioral evidence before the first mutation** under the conservative audit.

The strongest next mechanism is therefore:

> **evidence-before-mutation** — obtain the cheapest discriminating behavioral witness before editing when a concrete contract exists, then reuse that witness after editing.

This targets information quality and root-cause correctness rather than simply adding or removing compute.

### Soft-policy control gap

Reliability-v1's prompt contains repair/verification/submission discipline, yet classifier-recognized post-edit targeted failures were not followed by repair mutations and were still followed by submission.

This does not prove every affected patch was wrong or every classifier label is semantically perfect. It does show that **critical lifecycle transitions are not reliably enforced by prose instructions alone**.

Therefore:

- do **not** respond by stacking more prompt rules;
- do **not** equate “ran a targeted-looking command” with high-quality evidence;
- separate the mechanism from the implementation.

The competition format is declarative and uses a closed host tool registry; there is no arbitrary custom deterministic submit wrapper. The harness may also extract a non-empty diff even if `submit_patch` is never called. If stronger lifecycle enforcement is later tested, a supported structural option is a **minimal read-only evidence stage before the editing stage**, but that extra topology/model-call cost must earn itself on untouched evidence.

## Provisional breakthrough ranking

This ranking guides research only while Reliability-v1 feedback is pending.

1. **Evidence-before-mutation** — strongest mechanism; conditional behavioral witness before source mutation.
2. **Test-aware retrieval** — likely low-cost implementation lever for #1: retrieve source candidate + smallest exercising test together.
3. **Adaptive compute / value-of-information routing** — secondary efficiency mechanism; choose actions by expected discrimination, not simply fewer calls.
4. Conditional edit/tool-schema reliability — retained only if new evidence shows grammar failures remain material.
5. Conditional bounded rescue / structural stage separation — only if a specific missing control capability justifies the added topology cost.

Do not bundle these into a v1.1 mixture.

## Resource policy

- Existing run/artifact answers the question -> **reuse it**.
- Cheap GitHub Actions for static checks, read-only probes, reproducibility, compact artifacts, and deployment orchestration -> **use freely** in this public repo.
- Kaggle GPU/full diagnostic -> **only when it can falsify a named hypothesis or change a decision**.
- Do not duplicate an active submission or diagnostic.
- Do not spend compute merely to get another sample from an already-inspected denominator.

Competition Data remains runtime-only for new runs. Public repository status is not a scientific blocker under `PUBLIC_VISIBILITY.md`; legacy exposure cleanup remains deferred and must not alter the experiment.

## Next decision after Kaggle feedback

When ref **57921371** reaches a terminal state:

1. compare its actual public score with the pre-registered **0.08 [0.05, 0.12]** prediction and with the baseline **0.03**, without treating one leaderboard point as causal proof;
2. explain the prediction error and reconcile it with the 1/17 development diagnostic and the trace-mechanics audit;
3. choose exactly one implementation of the **evidence-before-mutation** mechanism unless the score materially falsifies that diagnosis;
4. freeze a **new untouched evaluation denominator before inspecting its traces**;
5. pre-register the targeted failure surface, expected observable effect, resource cost, and falsifier;
6. only then implement and deploy the smallest candidate expressing that mechanism.

Until then: **no new expensive experiment, no duplicate submission, and no prompt tuning against the 17 known tasks.**
