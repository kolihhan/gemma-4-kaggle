# Why did Reliability-v1 score 0.03? — adversarial root-cause review (2026-11-04)

Status: **post-score diagnosis, not a new model experiment.** Research branch: `exp/capacity-boundary-v0`. Preserve frozen Reliability-v1 control and the untouched comparison pool.

## Scoring observation

- Baseline submission `57879765`: COMPLETE, Public LB **0.03**.
- Reliability-v1 submission `57921371`: COMPLETE, Public LB **0.03**.
- Kaggle CLI probe: GitHub Actions run `41585360688`, job `126363546071`, 2026-11-04 03:13 UTC.
- Preregistered v1 prediction: **0.08 [0.05, 0.12]**. Miss = **-0.05** vs point and **-0.02** vs lower bound.
- Both displayed scores are equal; their hidden-scored task IDs, score rounding, and failures are **not** visible. Public discussion infers a 58-task public denominator and floor/truncation: 0.03 ≈ 2/58; this is a community inference, not ground truth available to this repo. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743506

**Scientific failure:** the intervention's observed throughput/patch-size changes did not transfer to the intended goal, *correct issue resolution*. One LB number does not identify causal mechanism.

## Strongest first-party evidence: 17-item inspected development diagnostic

Source: `deploy-reliability-v1.yml` run `41485671952`, job `125417231948`; GitHub Action safe artifact `13164353045`. Trace audit run `41590900152`, artifact `13209917848`.

- **1/17 resolved**; **13/17 non-empty patches**, 4 empty.
- Final verifier exit codes: 0 on 1, 1 on 14, 2 on 1, -1 on 1.
- **No task hit the five-minute agent ceiling** (max duration about **201 seconds**, from the existing diagnostic result JSON).
- **No task exhausted 32 tool calls** (max 30, mean 10.41).
- Thus a simple claim that more time / more tool-call budget will fix these 17 tasks is directly weakened.
- Same-classifier mechanics audit: **0/17** recognized task-relevant behavioral witness before first edit; **14/17** had no recognized targeted test; 3 targeted-test calls total vs 10 broad-test calls.
- Across 17 tasks: **75 read actions, 4 code-intelligence localization actions, 39 mutations**, and **14 explicit submissions** (conservative analyzer semantics).
- Two cases where the classifier saw failed targeted checks had **zero subsequent repair mutations**, yet submission occurred. These are clear soft-policy compliance concerns.
- Reliability-v1 vs predecessor: resolved **1 -> 1**, runtime **-12%**, mean non-empty patch size **-20%**, broad test calls **14 -> 10**, targeted test calls **3 -> 3**.

**Important methodological correction:** `12/12 non-empty unresolved patches have failing final verification` mainly restates the scoring outcome. It does **not** distinguish wrong root-cause reasoning from wrong edit, unrelated test environment failure, or mismatch to hidden assertions. Do not report it as an independently measured 12/12 root-cause error rate.

The 17 tasks were selected via `gold-pass AND no-op-fail` screening, so universal broken tests / already-passing empty patches are *less plausible on this denominator*; nevertheless, the local test ecosystem is known imperfect and the 17 are not the hidden private-repository tasks.

## Likely causal chain (hypothesis, not proven)

`underspecified issue or incomplete repo understanding`
→ `plausible localization`
→ `speculative edit before a discriminating reproduction/test`
→ `weak or irrelevant local verification`
→ `no convergent repair after failure`
→ `non-empty but incorrect final patch`.

This is consistent with the observed **0 pre-edit targeted witnesses**, **14/17 without recognized targeted tests**, and **0 repairs after recognized targeted failures**. It explains why editing/shortening prompts can improve efficiency and not correctness.

**Prompt-induced verification starvation is a specific alternative**: the new prompt discourages bare `pytest` and pushes narrow tests, but broad-test count fell **14 -> 10** without an increase in targeted-test count (**3 -> 3**). We may have **removed low-information testing without replacing it with high-information testing**. This is more concrete than saying simply `E4B too weak`. But the classifier undercounts compound-shell tests, and this is not a controlled prompt ablation.

## Competing explanations — evidence strength, falsifier

1. **Failure to establish relevant task semantics / diagnostic evidence before editing**: strongest direct *process* signal on inspected development traces. Falsify by giving truly relevant pre-edit behavioral evidence on untouched tasks and seeing no meaningful correctness benefit.
2. **Weak E4B reasoning / edit-generation capability**: plausible but **not proven**. More information may not help a model unable to synthesize the right fix. Compare identical policy on E4B and a stronger model, with both solved count and run cost; do not attribute a 31B-era public 0.17 score to model size alone.
3. **Tests available to the agent are unhelpful, incomplete, or interpreted badly**: likely contributor. One final recognized targeted pass still yielded unresolved outcome. Test usefulness, not merely command type, needs assessment.
4. **Budget/resource configuration**: a possible hidden-run bottleneck, but *not* primary on the existing 17 (0 call/time cap hits). Kaggle's global 12-hour budget includes sandbox setup and excludes verification; `max_time_minutes:5` only limits per-task agent time, not the end-to-end submission. Hidden task wall-clock and completion distribution are unavailable.
5. **Scorer/harness/runtime pathologies**: possible, unproven. In the scored run, packaging passed validation and a nonzero score proves some work was counted; however, it does not exclude partial task failures. Competition reports note vLLM Gemma4 array-tool parsing can stall later model requests (https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/753973), and model reasoning/compaction issues have changed across wheelhouse builds. Do not blame infrastructure without scored-run task logs.
6. **Distribution shift / task specification quality**: important unknown. Public 129 tasks cover Rich/FastAPI/Requests/HTTPX; the selected 17 cover only Rich/FastAPI. Hidden leaderboard tasks come from private repos. Some public issue statements are title + URL with offline sandbox and no hints (https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746944). No known hidden task-level scores are available to characterize transfer.

External comparator caveat: public v19 reached LB **0.17** with 31B-era model/policy and much larger local budgets (often 15 min and 100 tools; thinking off), so it is **not** a controlled E4B-vs-31B comparison. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696. Staff confirms hidden gold patches pass: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/744370.

## Mandatory bottleneck checkpoint

CURRENT BEST: E4B Reliability-v1 **0.03**, tied with previous E4B baseline.

REAL EVIDENCE OF STRENGTH: valid nonzero score, 1/17 clean-development solves; faster and smaller patches than predecessor without greater solved count.

MAIN FAILURE MODE: non-empty patches with no demonstrated task-relevant behavior improvement; verification and repair transitions not reliable.

CURRENT BOTTLENECK HYPOTHESIS: **task semantics/evidence→root cause→correct edit chain**, with unresolved base-model capacity and hidden-run runtime confounds.

IS THIS A LOCAL BUG OR MODEL-CLASS LIMITATION?: UNKNOWN; existing traces support a local policy/lifecycle failure but do not rule out model-class limitation.

WHAT METHOD CLASSES ARE CURRENTLY EXCLUDED?: no class permanently excluded; do not launch uncontrolled larger-model swap, new verifier-LoRA, broad SFT/RL, or another prompt sweep without discrimination.

WHY ARE THEY EXCLUDED?: no evidence which causes current failure; expensive/potentially confounded interventions do not solve causal uncertainty.

HAS THE ORIGINAL REASON FOR EXCLUSION CHANGED?: Yes. <0.05 preregistered pivot trigger fired. Capacity/model-policy comparison is now justified as a **diagnostic candidate**, not a default upgrade.

SMALLEST EXPERIMENT THAT DISCRIMINATES BETWEEN THE COMPETING EXPLANATIONS:
- **Stage 0 (no GPU):** reproduce exact current scorer/sandbox compatibility, ensure the 31B model source is available, and audit known dev trace-metric coverage / historical 12B failure. Freeze an untouched, provenance-clean paired denominator and explicit success/overhead criteria before seeing task text or traces.
- **Stage 1 (minimal new compute):** a preregistered feasibility/policy-control test (E4B frozen control vs 31B same prompt/tools/sampling and budget) on the same small untouched task set, recording startup, completion, patch production, exact final verification, elapsed time and calls. If 31B cannot finish within budget, record **throughput-limited** rather than “capacity weak”. Do not conclude superiority from one task.
- **Stage 2 only if Stage 1 viable:** sufficiently sized paired untouched comparison; inspect residual traces only after both arms finish. If both are similarly wrong, reopen evidence formation / test-aware retrieval / structured search. If 31B solves while E4B fails *with similar evidence*, capacity is supported. If 31B slower without unique solves, retire naive 31B swap and consider cheaper alternative/teacher-distillation separately.

WHAT RESULT WOULD CAUSE AN ARCHITECTURE-LEVEL PIVOT?: larger model without better resource-adjusted correctness → prioritize information-quality and repair-mechanism changes; stronger-model unique solves with acceptable budget → consider capacity and distillation; both strong model and evidence stages fail → revisit task representation/search/objective and hidden distribution assumptions.

## Decision

Keep the **0.03 result as a genuine failed prediction**, not merely bad luck. Fix the selection logic: *observed bad score is evidence against our predicted transfer, not proof that capacity is the cause*. Preserve the next small capacity probe as an experiment intended to distinguish hypotheses, with a cheap runtime gate and no 17-task resampling.

No new GPU run, adaptation, unseen task inspection, or submission is claimed by this note.
