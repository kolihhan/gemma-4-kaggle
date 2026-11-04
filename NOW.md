# NOW — 2026-11-04

Updated: 2026-11-04 11:13 MYT

## North star

Build a competitive Gemma 4 software-engineering agent by learning which mechanisms transfer to Kaggle hidden evaluation, not by patching inspected tasks or chasing Public LB noise.

Research must remain anti-overfit, resource-aware, mechanism-first, and willing to reopen model/training/topology classes when evidence changes. Read `RESEARCH_DOCTRINE.md` before preserving or rejecting a major method class.

## Terminal scoring / active decision

**Reliability-v1 is terminal; its preregistered Public-LB prediction failed.**

Fresh read-only probe on **2026-11-04 03:13 UTC / 11:13 MYT**:
- baseline ref `57879765`: **COMPLETE**, Public LB **0.03**;
- Reliability-v1 ref `57921371`: **COMPLETE**, Public LB **0.03**, private score not available;
- frozen prediction: **0.08 [0.05, 0.12]**; observed result **0.03**, **-0.05** vs point, **0.02** below lower bound;
- observed displayed Public-LB gain over baseline: **0.00**.

Source: GitHub Actions run `41585360688`, latest job `126363546071`. Canonical calibration: `docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md`.

**Activated predeclared branch: Public LB < 0.05.** Do **not** automatically implement evidence-before-mutation-v0. Open an architecture/model-policy capacity discriminating lane, while explicitly preserving uncertainty about *which* mechanism failed.

Frozen Reliability-v1 submission remains untouched. No duplicate submission, no rerun of inspected 17-task denominator, and no task-specific prompt tuning.

## Root-cause investigation after the 0.03 miss

Research audit: `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**First-party evidence:** 1/17 resolved, 13/17 non-empty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted tests, 0 repairs after the two recognized failed targeted checks. Existing development result JSON shows **0/17 five-minute time-cap hits** (max ~201 sec) and **0/17 tool-cap exhaustions** (max 30 of 32).

**Main diagnostic hypothesis:** issue semantics/evidence → root cause → correct edit/repair is unreliable. Reliability-v1 reduced broad tests (14→10) without increasing recognized targeted tests (3→3), suggesting a possible verification-starvation trade-off rather than a knowledge gain.

**Not established:** hidden scorer task-level failure classes, same solved IDs across baseline/v1, model-capacity ceiling, partial hidden runtime/harness failures. The 17 development tasks are Rich/FastAPI-only and were inspected. Gold-pass/no-op-fail selection weakens blanket broken-harness explanations for that 17, not for hidden private-repo tasks.

**Decision correction:** the <0.05 pivot opens capacity as a *testable alternative*, not as the proven root cause. Before an expensive comparison, run a cheap scorer/model-source feasibility gate and freeze a genuinely untouched paired denominator. Do not assume that 5 minutes/32 calls caused the local 1/17 (neither limit was reached).

## Public leaderboard and open-method recon (2026-11-04)

Canonical evidence: `docs/research/public-leaderboard-vs-open-methods-2026-11-04.md`.

- Latest third-party CLIST Public LB snapshot: leader **0.29**, several teams **0.24**; **leader's method not publicly established**. Do not assign an unknown top agent a model or architecture.
- Disclosed scored stronger systems: **31B no-LoRA two-role v19 0.17**, with tracing/localization and thinking off; **31B single-root Budget-Fit 0.18**, using eight-minute cap, 28 tools and 4096 thinking budget. Neither proves multi-agent or thinking mode is universally superior.
- Factorial self-hosted study (3 model sizes × 2 scaffolds × 5 seeds × 104 public tasks): richer E4B scaffold improved local resolved rate **10.0% → 15.4%** while 12B min **25.2%** exceeded E4B max. The study used GGUF/llama.cpp and a repaired local verifier: **not official hidden LB**, not a directly controlled comparison with our E4B QAT.
- Caveat: identical public bundles have been observed scoring differently by up to 0.05 in hosted experiments; do not read a causal mechanism from single LB points.
- Our E4B 0.03 is lower than these 31B open systems, but the difference bundles model class, policy, budgets, harness epoch and hidden task draws. Stronger evidence for model capacity as a **candidate**, not a proven root cause.
- Official competition provides a **$10,000 E2B/E4B small-model prize**, but current filtered small-model standings have not been independently verified.

**Decision:** Preserve the planned capacity probe as a controlled falsification test; explicitly keep test-aware evidence/scaffold design as a competing hypothesis. Do not copy public leader configs without determining what mechanism is actually responsible.

## Capacity-v0 execution checkpoint — 2026-11-04

**Model-only CPU preflight: VERIFIED GREEN.** Run [41782383957](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782383957), job 126416680873:
- 7/7 integrity/selection/exposure-scanning tests passed;
- old frozen E4B submission hash contract passed;
- E4B vs 31B exact file-set check passed; only one agent model declaration differs;
- Kaggle official model instance metadata found both E4B and 31B;
- 41 current official scorer wheels fetched;
- both model declarations passed the same scorer's submission schema checks;
- 149 repo research/source files scanned for the 16 candidates, zero unexpected mentions;
- candidate feasibility n=4 (2 Rich, 2 FastAPI); confirmation reserve n=12 (6 per repo);
- frozen selector SHA256: 4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593.

Source code/contract:
- scripts/capacity_preflight_v0.py; tests/test_capacity_preflight_v0.py;
- .github/workflows/capacity-preflight-v0.yml;
- docs/evaluation/capacity-boundary-v0-preregistration-2026-11-04.md.

**Model-free gold eligibility is running in private Kaggle CPU:** Action [41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381). It uses the official gold-reference verification path against 16 metadata-only candidates; no LLM model or GPU, and only sanitized result metadata may become a GitHub artifact. Status/outcomes are **UNKNOWN until completed**.

**Remaining gates before any expensive model run:** gold-pass + no-op-fail eligibility, prior-run/human exposure provenance limitations, and 31B runtime/startup resource feasibility on L4x4. Do not call the 16 candidates certified independent blind; the source-text audit cannot inspect private historical notebook artifacts or unrecorded human views. Do not alter frozen Reliability-v1 or publish competition data.

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

Status: **OPEN, but no longer the automatic first candidate after the <0.05 pivot trigger.**

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

Status: **SELECTED for next discriminating research lane; not proven as the dominant bottleneck.**

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

## Predeclared score fork — terminal branch now activated

### Public LB < 0.05 — TRIGGERED (observed 0.03)

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

**Open one capacity/model-policy diagnostic on `exp/capacity-boundary-v0`, with the root-cause audit as gate zero.** Do not mistake the failed E4B policy prediction for proof that increasing model size works.

1. Start from the corrected fallback `docs/design/model-capacity-probe-v0-2026-11-03.md` and the recovered 12B negative evidence.
2. Verify availability/compatibility of the official 31B scorer model and adapter-free same-policy runtime **without GPU first**.
3. Freeze an untouched task selector and all historical task exclusions before running any model on selected tasks.
4. Preregister the smallest 31B-vs-E4B feasibility gate and paired outcome/resource comparison. The gate must distinguish timeout/infeasible throughput from weak reasoning quality.
5. Execute Kaggle inference only after static/schema/model-source prerequisites are met; retire if the larger-model cost cannot be justified.
6. Reconsider lifecycle, search, and trajectory-SFT after independent evidence—not as task-specific patches.

No 31B/E4B paired GPU model run or new competition score has been produced. Private CPU gold eligibility is underway.
