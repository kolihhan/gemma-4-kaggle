# NOW — 2026-11-03

Updated: 2026-11-03 23:43 MYT

## North star

Build a competitive Gemma 4 software-engineering agent by learning which mechanisms transfer to Kaggle hidden evaluation, not by patching inspected tasks or chasing Public LB noise.

Research must remain anti-overfit, resource-aware, mechanism-first, and willing to reopen model/training/topology classes when evidence changes. Read `RESEARCH_DOCTRINE.md` before preserving or rejecting a major method class.

## Current live state

**Frozen Reliability-v1 remains unchanged while its real Kaggle submission is pending.**

- baseline ref `57879765`: COMPLETE, Public LB **0.03**;
- Reliability-v1 ref `57921371`: **PENDING** at fresh read-only probe **2026-11-03 15:43 UTC / 23:43 MYT**;
- preregistered Reliability-v1 prediction: point **0.08**, interval **0.05–0.12**;
- do not submit a duplicate Reliability-v1 candidate;
- do not rerun the inspected 17-task development denominator;
- do not tune prompts against known Rich/FastAPI failures;
- no new expensive model/GPU experiment while the live score is unresolved.

Latest status probe:
- workflow run `41585360688`;
- latest job `126023940185`;
- result: `SubmissionStatus.PENDING`.

## Frozen control / development evidence

Reliability-v1 is the current frozen E4B single-root control.

Canonical development diagnostic:
- run `41485671952`;
- job `125417231948`;
- 17 / 17 completed;
- **1 / 17 resolved**;
- 13 non-empty patches, 4 empty;
- mean tool calls `10.41`;
- mean duration `89.21 s`;
- call-cap exhaustions `0`;
- 12 / 12 non-empty unresolved patches had non-zero evaluator verification exit.

Relative to the earlier single-root run on the same inspected denominator:
- resolved stayed **1 -> 1**;
- total evaluator runtime fell about **12%**;
- mean non-empty patch size fell about **20%**.

Interpretation: Reliability-v1 became more restrained/efficient, not demonstrably more capable on the inspected development set.

## Trace-mechanics audit

Canonical audit:
- run `41590900152`;
- job `125767140355`;
- artifact `13209917848`;
- no new model inference or Kaggle task execution;
- analyzer tests **8/8 PASS**;
- safe-output gate PASS.

Same-classifier earlier single-root -> Reliability-v1:
- resolved: `1 -> 1`;
- targeted behavioral evidence before first mutation: `0 -> 0` tasks;
- targeted-test calls: `3 -> 3`;
- tasks with no targeted test: `15 -> 14`;
- broad-test calls: `14 -> 10`;
- localization-tool calls: `0 -> 4`;
- mutations: `40 -> 39`;
- failed targeted check followed by repair mutation: `0 -> 0`;
- submit after latest classifier-recognized targeted failure: `1 -> 2`.

The analyzer is conservative; use these values for same-classifier mechanism comparison, not as exhaustive semantic labels.

## Current global hypotheses

### H-lifecycle — evidence before mutation

Status: **ACTIVE / provisional first candidate if live score does not trigger a broader pivot.**

Current mechanism:

> Obtain the cheapest discriminating behavioral witness before mutation when a concrete contract exists, then reuse that witness after editing where feasible.

Why it remains plausible:
- both inspected single-root variants show 0/17 classifier-recognized targeted pre-edit behavioral evidence;
- soft repair/submission lifecycle instructions were not reliably followed;
- simply reducing calls/runtime did not improve solved count.

Canonical design:
- `docs/design/evidence-before-mutation-v0-2026-11-03.md`

Implementation plan:
- `docs/superpowers/plans/2026-11-03-evidence-before-mutation-v0.md`

### H-capacity — E4B/model-policy ceiling

Status: **REOPENED globally, not selected for execution.**

External evidence includes a materially stronger public 31B-era no-LoRA system, but that comparison is confounded by model size, topology, prompts, budgets, and development history.

Important recovered repository evidence:
- old E4B/12B same-lineage `rich_3278` smokes already exist;
- E4B produced a wrong patch inside five minutes;
- 12B default-thinking timed out with 0 patch;
- 12B thinking-budget-1024 also timed out with 0 patch despite more tool activity.

Canonical note:
- `docs/research/recovered-12b-capacity-evidence-2026-11-03.md`

Therefore:
- do **not** repeat the old naive 12B-first experiment;
- capacity does **not** mean `swap E4B -> 12B`;
- if the capacity trigger fires, the next experiment must add new information, e.g. a preregistered 31B same-policy probe or a frozen strong-public model-policy reproduction.

Corrected fallback design:
- `docs/design/model-capacity-probe-v0-2026-11-03.md`

### H-training — trajectory/policy distillation or SFT

Status: **REOPENED for feasibility, not causally prioritized yet.**

Do not confuse this with historical verifier-LoRA v0. Verifier-LoRA remains **NOT TESTED**, not falsified. Broader policy/trajectory training becomes higher priority only if untouched evidence shows the lifecycle is correctly instantiated but E4B still systematically reasons/edits incorrectly, or a capacity probe shows a clear model-policy ceiling.

## Evidence-before-mutation causal guard

A simple comparison of:
- A: frozen Reliability-v1 single-root;
- C: two-role evidence -> coder;

is not enough to prove evidence transfer caused any gain because topology, independent model invocation, context partition, and latency also change.

Pre-register a conditional third arm:
- **A** — frozen Reliability-v1 incumbent;
- **B** — topology-matched null handoff: evidence root still runs, but coder is prevented from receiving its evidence/history;
- **C** — same topology, coder receives evidence/history.

Resource-aware rule:
1. freeze A/B/C plus untouched denominator before trace inspection;
2. run A and C first;
3. if C does not beat A by the practical promotion rule, stop and do not pay for B;
4. only if C > A, run already-frozen B before inspecting task-level traces;
5. strong evidence-mechanism claim requires C to beat B meaningfully as well as A.

Canonical review:
- `docs/research/evidence-before-mutation-v0-causal-identifiability-review-2026-11-03.md`.

## Current ADK / scorer runtime blocker

A cheap source probe against the current official scorer wheelhouse verified:
- `google_adk-1.36.1`;
- `adk_submission-0.2.13`;
- `swegemma-0.2.11`.

The historical compaction path still raises when the root agent is not an `LlmAgent` and no explicit summarizer model exists.

Therefore **do not use a root `SequentialAgent`** for evidence-v0 under the current wheelhouse.

Current safe provisional topology:

`root evidence LlmAgent -> coder LlmAgent`

Properties:
- root has no `edit_file`, `write_file`, or `submit_patch`;
- coder is the only mutation/submission role;
- zero-diff-before-coder remains mandatory because `run_command` can mutate;
- transfer is model-controlled, so successful transfer/compliance must be measured rather than assumed.

Canonical probe:
- `docs/research/current-compaction-probe-2026-11-03.md`;
- workflow run `41624178623`;
- job `125877217844`.

## Decision rule when Reliability-v1 becomes terminal

### Public LB < 0.05

The live candidate underperformed the preregistered interval.

Do **not** automatically implement evidence-v0 first. Reopen the architecture checkpoint and choose the smallest new experiment that separates lifecycle/policy limitations from model-policy capacity. Use the recovered 12B evidence; do not repeat it.

### Public LB 0.05–0.12

The live result is consistent with preregistration.

Evidence-before-mutation remains the first causal mechanism test. H-capacity stays explicitly open and second-line. If evidence-v0 forms high-quality pre-edit evidence but correctness does not improve, pivot rather than stacking more evidence prompts.

### Public LB > 0.12

Lifecycle/policy changes transferred better than expected.

Proceed with the untouched evidence-v0 causal test, but do not treat one LB score as proof of mechanism. Keep the A/B/C causal guard.

## Resource policy

- Existing artifact answers a question -> reuse it.
- Cheap GitHub Actions / source probes / static validation -> use freely in this public repo.
- Kaggle GPU/full task evaluations -> only when they can falsify a named hypothesis or change a decision.
- No duplicate active submissions/diagnostics.
- No compute to obtain another sample from an already-inspected denominator.
- No verifier-LoRA catch-up run merely for bookkeeping.
- No repeated 12B `rich_3278` smoke.

## Next action

**Wait only on the external dependency: terminal status for ref `57921371`.**

While it remains pending, productive work is limited to cheap non-contaminating research, static/runtime verification, and source-of-truth cleanup. Do not implement or execute the next scientific candidate prematurely.

Once the score is terminal, apply the preregistered decision rule above immediately and start exactly one discriminating experiment lane.
