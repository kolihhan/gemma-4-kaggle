# NOW — 2026-11-04

Updated: 2026-11-04 (capacity v0 Git-history/31B startup gate)

## Submission-first audit completed — 2026-11-04 (read-only + metadata archive)

**Latest deliverable:** [submission-first research decision](docs/research/submission-first-no-training-decision-2026-11-04.md), based on scored baseline `57879765` and Reliability-v1 `57921371` (both displayed Public **0.03**), inspected development-trace mechanics, prior 12B one-task negative, and publicly scored **no-training** 31B comparators. No new model/GPU/LoRA/leaderboard run occurred.

**Bottleneck priority, not causality:** (1) issue semantics/root-cause/patch correctness; (2) targeted evidence plus repair transitions; (3) E4B capacity/policy; (4) harness/scorer epoch; (5) budget alone. The inspected 17-task trace classifier is conservative and can miss compound-shell verification. A larger model is not guaranteed to improve performance, and the two public 31B systems have different prompts, topologies, budgets and host epochs.

**Recovered prior CPU artifact, no new compute:** [gold-screen Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800), artifact `13308702997`, ZIP SHA-256 `944b8acaac1e5f349f81bb0c941348dbc7c5694a57a48ce0ea843023a416711b`. Metadata-only [results](docs/evaluation/capacity-v0-replacement-gold-2026-11-04.json): **10/16 gold-pass**, Rich **4/4**, FastAPI **6/12**. These are **not** clean holdout replacements yet: independent no-op-fail screening is still missing. Do not confuse gold-check pass with model quality.

**Active instruction remains:** pause self-training, pause Colab/31B GPU execution and speculative submissions. The existing preregistered untrained same-policy E4B-vs-31B design is only a **conditional future experiment**, pending GPU feasibility and fully screened/provenance-clean paired tasks. No new candidate has been promoted; frozen `submission/` unchanged.

## Submission-first / no-new-training decision — 2026-11-04

**Current user directive:** Stop self-training/LoRA expansion and prioritize the existing scored Kaggle submissions. Put the optional Colab 31B feasibility notebook and Kaggle 31B GPU gate **on hold**, rather than treating them as required next steps. This is a priority change, not a deletion or a claim that all fine-tuning is intrinsically ineffective.

**Latest verified official per-user result**, from the read-only Kaggle CLI in [Actions 41585360688](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688), 2026-11-04 03:13 UTC:
- Baseline E4B submission `57879765`: `COMPLETE`, displayed Public LB **0.03**.
- Reliability-v1 E4B submission `57921371`: `COMPLETE`, displayed Public LB **0.03**; predicted **0.08 [0.05, 0.12]**; improvement **0.00 displayed**; private scores unavailable.
- This is **no demonstrated leaderboard improvement**, not proof that the submissions solve identical hidden tasks or that a specific mechanism failed.

**Process evidence, nonblind inspected development diagnostic (17 Rich/FastAPI tasks):** **1/17 resolved**, 13 nonempty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted test, two observed targeted-test failures with no subsequent repair mutation, zero time/tool-cap exhaustions. These observations support a *hypothesis* of weak issue understanding → testing/repair decisions; they do not prove root-cause causality or characterize the hidden benchmark. See `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**Priority decision:**
1. **No additional self-trained verifier LoRA, no Colab training, no adaptation of the 9-example adapter into the scored submission.** Prior successful LoRA optimization is engineering evidence only; the tiny training set and lack of independent improvement do not justify promotion.
2. **No speculative new Kaggle submission** or re-submit of the 0.03 bundle. Preserve the frozen Reliability-v1 artifact and current baseline for comparison.
3. Focus on **submission evidence and untrained pretrained-Gemma agent design**: compare publicly reproducible successful submissions, trace evidence before edits, targeted tests and repair-after-fail; favor mechanism-first changes that can be independently checked. A 31B pretrained-model baseline remains an option *only after* a separate feasibility/compute decision; no GPU run is authorized by this status entry.
4. Do not chase 0.03 by patching inspected 17 task IDs. For any eventual new proposal, freeze a clean denominator and prediction before evaluation; do not claim generalization from one Public LB sample.
5. The optional Colab notebook remains committed but **not an active execution task**. Kaggle 31B quota remains blocked; no change to official submission.

**Next research-only step:** rank the actual submission failure hypotheses by evidence, compare public untrained 31B and E4B policies without training, and identify one low-compute, untouched evaluation whose result would change a real decision.

## Colab 31B synthetic-only feasibility alternative — 2026-11-04

**User-requested alternative to Kaggle GPU-quota blockade:** Added `notebooks/capacity_31b_colab_smoke.ipynb` on `exp/capacity-boundary-v0`. **Notebook created and statically validated; NOT executed on any Colab GPU yet.**

- [Static CI 41805674499](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41805674499): PASS; source/cell syntax and no-competition-data contract verified.
- Model checkpoint: `google/gemma-4-31B-it-qat-w4a16-ct`; frozen original synthetic probe code pinned at commit `b13087b402ceef0aa0aa2ce55d1f7aa2c99108c3` and verified with Git blob hash; 32K max context, 0.90 GPU-memory utilization, no LoRA.
- Fail-closed resource gate before installs/downloads: exactly one GPU with >=32 GiB **free** GPU memory, compute capability >=8.0, >=30 GiB free disk. These are screening heuristics and do not guarantee model fit. A 16 GiB Colab T4 fails by design; Colab GPU types/quotas are not guaranteed.
- For qualifying Colab runtimes, install vLLM, attempt one 31B TP=1 startup, then reuse original **plain / scalar tool / array tool synthetic probes**. Save only structured scalar metrics locally; do not mirror raw data or auto-upload logs.
- **Scientific boundary:** Colab uses a separate GPU topology (TP=1) and installed vLLM, not the four-L4 Kaggle official scorer wheelhouse. A successful Colab probe is merely supplementary model/parser feasibility evidence. It does not unblock the Kaggle quota, validate official scorer equivalence, score tasks, or authorize any 4+12 model A/B or leaderboard submission.
- A Colab account owner must attach/select a capable GPU and execute the notebook. No integrated Colab execution was available from this GitHub-only workflow. Future results must be recorded with GPU identity, versions, error classification, and whether they were reproduced in the official Kaggle environment.

**Next action:** User runs the notebook in Colab on a compatible GPU and shares the metrics JSON. On failure, distinguish insufficient hardware / installation / model initialization / parser errors. Keep Kaggle 31B blocked until an official compatible kernel can actually start.

## Capacity v0 replacement checkpoint — 2026-11-04 (CPU-only)

**Verified original eligibility (no model):** original 16 metadata-preselected IDs yielded **10/16 gold-pass** and, for those exact ten gold-pass IDs, **10/10 no-op-fail**. The per-ID no-op record was downloaded and checked against the original private [run 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), artifact `13300818683`, then retained as metadata-only `docs/evaluation/capacity-v0-noop-screen-2026-11-04.json`. No raw patches, issue text, or hidden tests were committed.

**Frozen original gaps:** pilot Rich 0 / FastAPI 1; confirmation Rich 1 / FastAPI 4. Six replacements are needed in total (**Rich 1 + FastAPI 5**), all still subject to independent gold-pass AND no-op-fail screening.

**New deterministic metadata-only replacement gate:**
- `scripts/build_capacity_replacements_v0.py` preserves preregistered selector SHA `4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593`, excludes all original 16 and the original known-exposure corpus, and ranks additional candidates using the frozen source SHA namespace. No old holdout, training, or manually seen tasks are intentionally reassigned.
- [CPU Actions 41803046378](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803046378): **11/11 tests PASS**; queue **Rich 18 + FastAPI 28**; preselection tracked Git-source history scan **467 revisions**, **0 mentions** among first **16** queued prospective screening candidates. Historical Git source cleanliness **does not certify blind status** across previous private artifacts or unrecorded inspections.
- The first screening cohort was frozen as **4 Rich + 12 FastAPI** (the exact first 16 Git-source-audited replacement-queue IDs), before seeing replacement task outcomes.
- [Private Kaggle CPU gold-control Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800) was launched using a fail-closed Kaggle push guard and a metadata-only artifact policy. **Gold outcomes were not yet available at this checkpoint.** It has no GPU, model inference, or leaderboard submission.

**Next gate:** inspect the per-ID safe gold artifact on completion, run private CPU no-op verification **only on gold-pass replacement IDs**, then fill the missing Rich/FastAPI slots strictly in original ranked order. If the preregistered 16 replacement screens cannot fill six gaps, screen the next unexposed queue prefix without selecting on model results, or explicitly reduce/retire the planned comparison if clean source candidates run out. Do not pronounce blind certification from Git-source audit alone.

**31B GPU remains independently BLOCKED by Kaggle weekly quota**, not failed model inference. No new 31B run, no new LB score, and the frozen Reliability-v1 candidate remains unchanged. Verifier-LoRA's adapter artifact is a separate older research branch, not promoted.

## Latest PIC decision — 31B startup BLOCKED BY GPU QUOTA

**Verified external blocker:** GitHub Actions [41794811345](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794811345), job 126456289520, attempted to push a *private synthetic-only* 31B L4x4 startup kernel. Kaggle printed **"Kernel push error: Maximum weekly GPU quota of 30.00 hours reached."** CLI exit code was nevertheless 0. The subsequent HTTP 404 was for a kernel that was never created. Read-only status probe [41795018386](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795018386) confirmed no notebook/result. **NO model weights loaded, no GPU inference, no candidate issues tested and no new leaderboard submission.**

**Safeguards now implemented:** The 31B GPU workflow is **manual-only** (no auto-push on source commits); a new CLI push checker rejects zero-exit quota errors and requires an explicit successful push confirmation. CPU GitHub Action [41795366875](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795366875) reports **9/9 tests PASS**, including the push-failure guard. Historical preselection Git-source audit scans **467 revisions** and found **0 pre-existing document/source mentions among the 16 candidate IDs**; this is stronger than checking only the current tree, but does *not* certify full blind status across past private artifacts/unrecorded views.

**Decision:** Do not launch or re-run 31B GPU until account quota availability is verified. Startup/tool-call behavior remains UNKNOWN (not failed). Do not fill all 16 tasks merely to keep busy if model feasibility is still blocked; the 10 gold-pass/no-op-fail tasks remain frozen and unused by a model. An E4B-only evidence/repair lane is a potential separate pivot, not authorized as an automatic fallback by the quota error.

Canonical report: docs/research/capacity-v0-31b-gpu-quota-blocker-2026-11-04.md

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

**Gold eligibility:** 10/16 passed; **No-op eligibility:** 10/10 gold-passing candidates failed no-op verification, giving **10 doubly eligible tasks**. Private CPU actions: [gold 41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), [no-op 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489).

**Remaining gates before any expensive model run:** gold-pass + no-op-fail eligibility, prior-run/human exposure provenance limitations, and 31B runtime/startup resource feasibility on L4x4. Do not call the 16 candidates certified independent blind; the source-text audit cannot inspect private historical notebook artifacts or unrecorded human views. Do not alter frozen Reliability-v1 or publish competition data.

## Capacity eligibility update — 2026-11-04 14:28 MYT

**Gold reference screen completed successfully.** Private Kaggle CPU action [41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), metadata-only artifact `13299564669` (SHA256 `12a7ff7a377258eee08dd639ebd60726bdeb260649892c451c1d47d81e9e2f`):
- 16 preselected metadata IDs screened;
- **10/16 gold-pass**, 6 failed the official reference-patch verification;
- feasibility cohort 3/4 gold-pass; original confirmation reserve 7/12 gold-pass;
- Rich: 7 gold-pass out of 8, FastAPI: 3 gold-pass out of 8;
- source metadata preserved at `docs/evaluation/capacity-v0-gold-screen-2026-11-04.json`; contains no raw issue statements or patch bytes.

**No-op control now COMPLETE.** Private Kaggle CPU action [41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), job `126429235397`, completed successfully. The safe output reports `CAPACITY_NOOP_SCREENED=10` and `CAPACITY_NOOP_FAIL_COUNT=10`, artifact `13300818683`. All ten gold-passing tasks require a non-empty solution under the checked official no-op verifier. No model inference or GPU was used.

**Decision:** Continue gold-pass AND no-op-fail filtering, then replenish failed candidates using preregistered within-repo SHA-ranked metadata order before inspecting any A/B model results. Do not call the 16 raw candidates clean. Do not launch E4B/31B GPU while eligibility is incomplete. Do not change the frozen Reliability-v1 submission, sampler, prompts or budgets.

## PIC handoff — eligibility gate closed, replacements needed (2026-11-04)

**Verified:** CPU model/schema preflight GREEN (7/7); reference-patch gold pass 10/16; no-op fail 10/10 of gold pass; **10/16 total doubly eligible**. Gold and no-op remain separate controls. Private job `126429235397` and artifact `13300818683` establish the no-op gate; confirm exact per-task metadata from that artifact before finalizing a replacement manifest.

**Original frozen shape:** feasibility 4 = Rich 2 + FastAPI 2, currently gold/no-op eligible Rich 2 + FastAPI 1 (**missing FastAPI 1**). Confirmation 12 = Rich 6 + FastAPI 6, currently eligible Rich 5 + FastAPI 2 (**missing Rich 1 + FastAPI 4**). Overall **six replacement tasks needed: one Rich, five FastAPI**, from *new uninspected IDs* and fixed within-repo SHA ordering.

**PIC mandatory next steps:**
1. Verify the safe no-op artifact at the per-ID level and commit a vetted derived metadata-only eligibility record (no raw traces/test material).
2. Formally construct the next within-repo SHA-ranked replacement queue from the pre-existing 90-task source metadata; exclude the initial 16, previous training/holdout, known exposures and any ambiguous provenance. Freeze replacement order *before seeing model results*.
3. Run just enough private Kaggle CPU gold-pass AND no-op-fail screening to fill the **1 Rich + 5 FastAPI gaps**; stop early if provenance or eligible pool fails. Keep pilot and confirmation strata separate. If no clean replacements exist, **reduce/retire the preregistered comparison explicitly rather than silently changing the denominator**.
4. After a frozen eligible denominator, audit 31B vLLM startup on Kaggle L4×4 and command/tool/parser behavior, then run the *same-policy* four-task paired **E4B/31B feasibility** test only if justified by costs. That four-task pilot cannot promote 31B or establish a statistical win.
5. If feasible, use the untouched independent 12-task confirmation. Record resolved, unique solves, time, tool calls, empty patch rate, verifier exits and cost; follow the pre-registered threshold and pivot on genuine evidence.

**Not yet done:** clean replacement cohorts, GPU startup, paired model inference, any new competition LB score. **No submitted reliability-v1 artifacts changed.**

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

## Next action — revised after quota rejection

1. **Hard stop on GPU:** Do not push the 31B model again while Kaggle's weekly 30-hour quota is exhausted. The exact reset time is UNKNOWN. Future check must verify account quota and inspect active workloads before any manual dispatch.
2. **When quota is available, one explicit manual startup smoke:** use the now fail-closed workflow .github/workflows/capacity-31b-startup-smoke-v0.yml; record start, plain request, scalar tool, array-shaped tool, and total cost. This is zero-task feasibility only, not a model-capacity measurement.
3. **Before issue evaluation:** keep original selection immutable, verify historical exposure beyond Git where feasible, and replenish eligibility by preregistered within-repo SHA order (1 Rich, 5 FastAPI missing) if 31B startup actually works. The gold/no-op current result is 10/16 eligible; no task text/ref patches shared.
4. **If startup works and resources justify it:** execute the pre-registered four-task paired E4B/31B pilot; only then consider the 12-task independent confirmation. No changes to Reliability-v1, no per-task hyperparameter tuning, no leaderboard claims from pilot.
5. **If quota remains unavailable:** hold the capacity experiment; evaluate separately whether the 0.03 failure warrants a cheap, independent E4B evidence/test/repair mechanism hypothesis. Do not silently call a model-class limitation proven.

No new model inference or Public LB score has been produced by this checkpoint.
