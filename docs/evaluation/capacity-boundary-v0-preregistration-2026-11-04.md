# Capacity-boundary v0 — frozen decision contract (2026-11-04)

Status: **PREFROZEN / CPU PREFLIGHT IN PROGRESS / NO GPU OR NEW LB SUBMISSION AUTHORIZED BY THIS FILE ALONE**.

Branch: exp/capacity-boundary-v0.
Canonical baseline: Reliability-v1 ref 57921371 / Public LB 0.03; exact frozen submission under submission/ validated by scripts/render_reliability_v1_kernel.py.
Supporting analyses:
- docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md
- docs/research/why-reliability-v1-only-003-2026-11-04.md
- docs/research/recovered-12b-capacity-evidence-2026-11-03.md
- docs/research/public-leaderboard-vs-open-methods-2026-11-04.md

## 1. Scientific question

Given **the exact same frozen Reliability-v1 policy and per-task budget**, can a stronger supported base model produce more correct repairs on previously uninspected public issue tasks, with acceptable execution cost?

This is a **model + runtime feasibility/repair test**. Although only the declared base-model string changes in the submitted config, the 31B model can require a different Kaggle GPU topology and throughput, so this is **not** a pure param-count causal estimate.

### Competing hypotheses

- H-capacity: E4B cannot reliably reason/edit a correct patch despite adequate observations, so 31B may produce genuinely more correct patches.
- H-evidence: Both models follow a weak evidence/repair policy; swapping the model alone may not cure test selection and repair state transitions.
- H-budget/runtime: 31B may be capable but too slow under unchanged 5-minute sessions, or unavailable in the local scorer environment.
- H-grader: Some local failures reflect task/harness or eligibility artifacts. A gold-pass/no-op-fail gate is therefore required before interpreting local success.

**Falsifiers:** No nonempty patch within available budget, no unique correct repair after sufficient paired runs, strong cost per solve disadvantage, or similar failure mechanics in both arms even after controlled observations.

## 2. Frozen intervention

Control A: exact frozen E4B Reliability-v1 configuration.

Treatment B: same five-file submission payload, with ONLY the root agent's single line changed:

    model: gemma-4-e4b-it-qat-w4a16-ct
    =>
    model: gemma-4-31b-it-qat-w4a16-ct

Everything else remains byte-identical: tools, prompts, no adapter, sampling (temperature 0.2, top_p 0.95, thinking budget 4096), maximum 5 minutes per issue, 32 tool calls, 64 turns, command timeout 300s.

**No 31B-specific prompt tuning, thinking-off tuning, special graph rules, budget increase, or task-specific exceptions.** If this fixed-policy comparison fails, it falsifies *simple same-policy substitution*, not all 31B architectures.

The official Kaggle announcement explicitly allows both model variants but not mixtures:
https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287

## 3. Denominator and leakage protection

The selector at scripts/capacity_preflight_v0.py is deterministic over EXISTING METADATA ONLY, not issue statements or gold patches.

Inputs:
- docs/evaluation/verifier-lora-split-v0.json
- docs/evaluation/verifier-lora-train-subset-v0.json
- docs/evaluation/verifier-lora-blind-reservation-v0.json
- docs/evaluation/verifier-lora-eval-contract-v1.json
- docs/evaluation/topology-ab-manifest-v1.json
- docs/evaluation/public-corpus-summary.md

It excludes known development, teacher/harvest, explicitly reserved blind, gold/noop confounded and prior public sample IDs. It builds a SHA256-ordered eligibility list within Rich and FastAPI, and earmarks the first **2 per repo** (four issues total) for a *feasibility-only paired check* and the next **6 per repo** (twelve) for an untouched confirmation reserve.

**Critical uncertainty:** These six artifact files do not conclusively prove no team member or historical job ever inspected a remaining ID. Before GPU execution, cross-check past Actions manifests, historical experiment documents and training/teacher exposures for exact candidate IDs and fail closed on any ambiguous collision. The selector label PREFROZEN_METADATA_ONLY_NOT_PROMOTION explicitly does NOT claim a certified clean blind split.

The source-side 129-task public corpus includes Requests/HTTPX, but no currently provably fresh Requests/HTTPX sample under these manifests. This gate's eventual results may only generalize to this Rich/FastAPI slice; it is NOT a hidden-score estimator.

Gold/no-op eligibility screening is to run exclusively via official scorer path on a private Kaggle runtime, without publishing raw competition data. Eligibility failures are replaced by the next source-repo SHA256-ranked *uninspected* candidate, before A/B results are reviewed, and replacements are recorded. Do not use gold patches to inform agent reasoning.

No viewing candidate task text, traces, reference patches or A/B outcomes before freezing paired denominators, replacement order and thresholds.

## 4. Cheap gate (before any GPU)

1. 5-file control hash check (frozen SHA in existing renderer).
2. Generate E4B and 31B from the same payload; assert byte-for-byte identity outside one model declaration.
3. Unit tests for unchanged payload, known-exposure exclusion, distinct cohorts, missing-manifest fail-closed and no task-data mirroring.
4. Query Kaggle model-instance metadata for both models using authenticated API, **without downloading weights**.
5. Validate each variant with the latest official Kaggle scorer wheelhouse (adk_submission.validate_directory and single-model declaration).
6. Check feasibility of the 31B base model on Kaggle's 4×L4 setup under the current scorer build. CPU metadata alone cannot verify vLLM startup, available L4 quota, context/cache, or throughput.

Only if 1–5 pass and (6) can be meaningfully tested is pilot GPU justified.

## 5. Paired feasibility-only pilot (NOT a promotion test)

- Same four IDs and same selected eligible replacements in A and B.
- Same budget and scorer version. Record model path/version, vLLM mode/tensor parallel, hardware shape, per-model startup time, per-issue wall time, model/agent tool calls, patch nonempty, verification exit, and resolved.
- No manual inspection after first arm before the second is fully complete.
- Pilot evaluates **working model load, run completion and nonempty patch production under budget**; any solved count is descriptive only.
- Pilot STOP if treatment cannot initialize under current official wheelhouse and Kaggle L4x4 within reasonable job time, if all four treatment attempts fail before any edit, if official scorer/schema rejects, or if gold/no-op screen cannot find eligible untouched pairs. Record infrastructure/time-cap separately from quality.
- Pilot GO to independent confirmation only if treatment starts, >=3/4 tasks complete, >=2/4 produce nonempty patches, and total wall-clock cost is recorded. This is a throughput feasibility condition, NOT a correctness victory.

No code competition LB submission from the pilot.

## 6. Untouched confirmation (if pilot passes)

Run the 12 additional frozen IDs with A/B using the identical candidate policies. No per-model parameter changes; no cherry-picking tasks or replacing failed model results. Compare paired:
- resolved count and unique solves (primary);
- exact final verifier exits (distinguish unhandled errors from issue failures);
- completion, empty patch, model startup, time to first edit, runtime per task;
- targeted-preedit-evidence and repair-after-failure mechanics after both arms finish;
- total model/server resource burden, resolution per agent minute and per kernel GPU-hour as proxies.

A useful directional result would require **>=2 more unique 31B solves across the 12 confirmations with no material loss of task coverage and a justified resource cost**; with n=12 this is weak evidence needing replication, not proof. Null/negative evidence (no new correct solves, cost blowup, incompletes) moves priority back to evidence/test-selection/repair policy and possibly policy training. Do not re-use these inspected 12 for subsequent promotion claims.

## 7. Scientific conclusions forbidden by design

- Do not call E4B capacity proven insufficient based on a Public LB 0.03.
- Do not call 31B inherently superior from unrelated published 0.17 or 0.18 LB agents.
- Do not call min-scaffold vs max-scaffold research a direct official Kaggle LB comparison.
- Do not claim a model wins on a four-task feasibility pilot.
- Do not claim difference is *caused purely by parameter count* when GPU topology/inference path can differ.
- Do not claim a Kaggle source/schema check proves that a large model loads and runs.
- Do not treat failed pre-edit testing or final verifier outcomes as automatically labeled root-cause mistakes.

## 8. Next executable decision

Run the CPU-only GitHub Actions gate. If RED, debug and repeat the CPU gate only, no GPU. If GREEN, audit the candidate ID exposure registry and scorer 31B runtime feasibility before building a one-off private Kaggle pilot.

The current Reliability-v1 submission remains frozen. New score: NONE.
