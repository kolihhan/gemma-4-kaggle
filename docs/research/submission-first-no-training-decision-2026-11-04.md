# Submission-first, no-new-training decision — 2026-11-04

Status: **research/evidence decision**, not a new Kaggle submission, model evaluation, training run, or promotion. Branch: `exp/capacity-boundary-v0`.

## Question and decision

Given the actual scored submissions, what is the most defensible route to improving the Gemma 4 coding agent **without training adapters**, under the existing Kaggle GPU quota blockade?

**Decision:** Stop the verifier-LoRA and Colab training lanes. The first plausible next *model* experiment, when inference resources become available, is the **already-preregistered, untrained, same-policy E4B-versus-31B comparison**; do not invent a new denominator or submit a larger model blindly. Meanwhile preserve and reconcile existing evidence, rather than shipping another prompt rewrite. A task-evidence/test-discovery skill can be reopened only as a separate, falsifiable intervention, not inserted speculatively into the frozen candidate.

This is a **priority restriction**, not a permanent claim that training or E4B improvements are intrinsically impossible. Pivot trigger: independently verified correctness improvement or a new, large, provenance-clean training corpus with a clear counterfactual. Neither is currently established.

## 1. Direct evidence from OUR submissions

| Quantity | Verified | Source |
|---|---|---|
| E4B baseline Public LB | **0.03**, COMPLETE, Kaggle ref `57879765` | [Kaggle read-only Actions 41585360688](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688), log 2026-11-04 03:13 UTC |
| E4B Reliability-v1 Public LB | **0.03**, COMPLETE, ref `57921371` | Same CLI read; submission uploaded 2026-11-02 |
| Preregistered Reliability-v1 prediction | **0.08 [0.05, 0.12]** | `docs/evaluation/reliability-v1-preregistered-prediction.json` (locked pre-feedback) |
| Public score delta | **0.00 displayed**; point-prediction miss **-0.05** | `docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md` |
| Inspected Rich/FastAPI development diagnostic | **1/17 resolved**; **13/17 nonempty patches**; no observed task time/tool-cap exhaustion | `docs/research/why-reliability-v1-only-003-2026-11-04.md` |
| Trace classifier (not full command semantics) | **0/17 recognized pre-edit targeted witnesses**, **14/17 without recognized targeted test**; after two recognized failed targeted checks, no repair edits | [Trace audit Actions 41590900152](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41590900152) and `scripts/analyze_root_trace_mechanics.py` |
| Earlier matched 12B case | Two 12B settings both failed to edit/solve **one** `rich_3278` task, despite increased calls when thinking dropped | `docs/evaluation/12b-rich3278-model-size-ab-2026-10-31.md` |

**What this does NOT show:** identical scored task IDs on the two 0.03 submissions; task-specific hidden score; unbiased generalization from the 17 inspected development tasks; causal proof that the model or tests alone are responsible. Compound-shell tests can be misclassified by the current trace parser. Do not silently upgrade a *classifier-recognized* zero to an exact zero.

**What the intervention did:** v1 made the already-inspected dev runs about **12% faster** and their nonempty patches about **20% smaller**, with **no resolved-count increase** and **no displayed Kaggle gain**. Efficiency proxies failed to predict correctness transfer.

## 2. Independent public comparators: NO training required for the observed v19 result

- [Public v19 author write-up](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696): official **0.17** Public score with the frozen **31B base / no LoRA**, analyzer + coder and prescribed localization/tracing. **7.5 min** applies to the actual scored submission; 8/15-min and 100-tool settings are separate local experiments.
- [Budget-Fit Kaggle source](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue): public notebook displays **Best Score 0.18 V2**, uses a **single-root 31B** approach. [Detailed hosted variation report](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/) explains 8-minute / 28-tool E0052 reference, variable host epochs, and repeat runs of byte-identical candidates.
- [Official competition rules / model announcement](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287): one model family/variant per submitted agent tree; 31B, 12B, E4B and E2B are permitted. The allowed submission format is declarative ADK configuration and supported skills/tools, **not arbitrary Python hooks around the scorer's ToolRegistry**.
- [Official competition timeline](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview): optional paper due **November 12**, main final submission due **December 2, 2026 at 23:59 UTC**; 12h total scoring budget. The paper-track date must **not** be confused with the main submission deadline.

**Counter-evidence:** The public 31B systems change **base model + topology/policy + budgets + host epoch** simultaneously versus our E4B. One is dual-agent and one single-agent; hence neither dual-agent topology nor 31B-only capacity can be singled out as the cause. The Budget-Fit report documents changes in scoring environment and meaningful variation on identical ZIPs. A single better Public score does not establish a repeatable effect.

## 3. Ranked bottleneck hypotheses (ordinal, not probabilities)

| Rank | Hypothesis | Support | Counterweight / discriminating observation |
|---|---|---|---|
| **1** | Issue understanding → correct code location/edit is weak | 13 nonempty patches but 1 resolved; earlier verifier-LORA training-side audit found inherently wrong coder patches, not just false acceptance | Hidden tasks unknown; relevant tests may also be inadequate; verify whether stronger model uniquely solves same, independently screened cases |
| **2** | Task-relevant verification and repair transition fails | 14/17 without classifier-recognized targeted test; two failed-targeted traces had no repair; v1's fewer broad tests did not produce more targeted tests | Trace classifier undercounts compound commands; a targeted local pass may still miss hidden tests; inspect post-hoc only after paired runs |
| **3** | E4B reasoning/tool-policy ceiling | Public untrained 31B scored agents materially stronger; small-model scaffold study suggests capability/architecture interactions | Completely confounded across submitted policies; old 12B one-task negative warns against assuming size always helps |
| **4** | Harness epoch, parser, scorer/test mismatch | Official host tool/reasoning fixes and community array-tool parser bug reports; identical-score comparison crossed dates | Both submitted bundles received nonzero scores; no scored hidden task-level logs establish runtime failure for our entries |
| **5** | Simply more minutes, turns, or tools | Plausible on unknown private tasks only | **0/17** recorded local task caps reached; blindly raising limits also risks the 12-hour whole-run cap |
| **Not selected** | Verifier-only self-trained LoRA | Premature submissions were real in prior verifier traces | Tiny frozen supervision, no independent resolution improvement, verifier cannot repair fundamentally wrong upstream edits; additional training is not warranted |

Rankings above are **research priorities**, not measured causal effect sizes.

## 4. First discriminating experiment — existing frozen no-training capacity-v0, conditional

Do **not** run until inference hardware/official Kaggle quota is available and baseline/provenance eligibility is complete.

- **Control:** exact frozen E4B policy, prompts, tools, sampling, task/time limits.
- **Treatment:** the **same policy** with only base model changed to pretrained official 31B; **no adapter, no additional training**.
- **Tasks:** preserve `docs/evaluation/capacity-boundary-v0-preregistration-2026-11-04.md`. Do not choose or reject tasks based on agent outcomes, task text, or a scored submission. Gold-pass and **no-op-fail** must both be shown independently. Initial four-task pilot is *feasibility only*; the 12-task confirmation population must remain separate, with provenance.
- **Measure:** both arms' boot/tool parsing, completion, unique resolves, patches, targeted checks, repairs, per-task time/calls/token burden, task-level disagreement and estimated full-run 12h budget risk. A model that cannot finish is **throughput-limited**, not “bad at coding.”
- **Falsifier:** if pretrained 31B cannot boot/fit or has no unique successes at tolerable cost, retire the naive larger-model swap. If both models solve equally few, pursue a separate evidence/test-discovery mechanism rather than more prompt policy or LoRA. If 31B uniquely solves eligible cases with acceptable throughput, only then evaluate a faithful publicly sourced single-root or analyzer-coder alternative.
- **No Public-LB-driven tuning:** do not treat 4 tasks as promotion evidence, reuse inspected 17 cases to select hyperparameters, or send a speculative new `submission.zip`.

**Current blocker:** the Kaggle L4x4 GPU attempt was rejected at push for 30h weekly quota (Actions `41794811345`), **before** model startup. The optional Colab synthetic smoke is documented but user-paused. No model-score evidence exists for 31B in this repository.

## 5. Existing CPU-only eligibility evidence recovered; STOP before unrequested compute

[Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800) had completed when this audit began. Retrieved artifact `13308702997` ZIP SHA-256 `944b8acaac1e5f349f81bb0c941348dbc7c5694a57a48ce0ea843023a416711b`, inspected `replacement-gold-metadata.json`, and archived metadata only to `docs/evaluation/capacity-v0-replacement-gold-2026-11-04.json`.

- **16/16** planned replacement candidates had a terminal CPU gold check.
- **10/16 gold-pass**: Rich **4/4**, FastAPI **6/12**.
- **Gold-pass is NOT eligible holdout membership**: the required independent **no-op-fail** check has not been done on these ten replacements.
- No model ran, no competition patch/text/hidden tests were added to the repo, and **no additional CPU or GPU screen** was initiated during this research-only pass.

This preserves provenance if the user later resumes the capacity comparison. It does not count as a new coding-agent accuracy evaluation.

## 6. Action gate (current)

1. Preserve scored baseline `57879765` and Reliability-v1 `57921371`; no re-submission, no training, no speculative prompt edits.
2. Treat **recovery of a GPU-capable inference path plus a genuinely clean paired denominator** as prerequisites, not a reason to keep writing new model configurations.
3. If quota does not recover, defer paired model evaluation; research an untrained **test-discovery/diagnostic evidence skill** only with a small synthetic, file-isolated CPU proof and an untouched performance check defined *before* exposure. The official skill interface is supported; an arbitrary deterministic `submit_patch` interception hook is not.
4. Re-evaluate priorities after actual new evidence. Never label syntax tests, positive teacher loss, or gold-patch CPU controls as leaderboard improvement.

**Net:** No new GPU, no LoRA, no Kaggle submit. One old CPU artifact recovered and classified, two scored submissions reconciled, external no-training comparators distinguished from a true controlled comparison.
