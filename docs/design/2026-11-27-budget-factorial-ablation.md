# Budget factorial ablation — 2026-11-27

Owner explicitly requests D in addition to A/B/C. This is a CPU-first design and retrospective feasibility check, not an authorized new model run or official submission. Keep architecture/prompt fixed to the exact scored Champion (not the unimplemented Semantic Repair hypothesis), then evaluate a supported architecture separately.

| Arm | max_tool_calls | thinking_budget |
|---|---:|---:|
| Champion | 60 | 4096 |
| A | 28 | 4096 |
| B | 60 | 2048 |
| C | 60 | 1024 |
| D | 28 | 2048 |

A/B/D/control constitute a 2x2 factorial. C is an additional lower-thinking condition. Model gemma-4-31b-it-qat-w4a16-ct; 5 minutes, 80 turns, same sampling except thinking_budget, same tools/prompt/harness. The four-file source must reconstruct exact scored Champion SHA ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b. No LoRA or training. No claim of novelty or causal effect from CPU fixtures.

## Actual CPU retrospective

Source: existing public calibration evidence, same three Git blobs recorded in the global ledger. 1350 episodes, 150 tasks; phase1 = 900 episodes (150 tasks x 3 configurations x 2 seeds), all with 28-call ceiling. Phase1 has 279 WT passes, 621 failures, 137 tool-budget endings (45 passes/92 failures, 53 empty patches), 540 virtual-time endings. Estimated max per-turn reasoning-token exposure:

| Threshold | Episodes with > threshold | Pass among exposed | Failed time endings with fatal thought > threshold | Of these empty |
|---|---:|---:|---:|---:|
| 1024 | 423 | 62 | 176 | 167 |
| 1536 | 275 | 29 | 131 | 129 |
| 2048 | 186 | 6 | 104 | 104 |
| 3072 | 77 | 1 | 51 | 51 |

Phase1 joint exposure at 2048: neither cap binding nor long thought 577 episodes / 228 pass; long thought only 186 / 6 pass / 155 empty; tool-budget ending only 137 / 45 pass / 53 empty; both 0. These are end-of-run classifications, not randomized groups; a long thought can exhaust time before the tool limit is reached, producing a mechanical association. They do not estimate D's effect. Shortening thinking may increase tool calls and make the lower call cap bind, an interaction worth measuring.

Paired phase3 1024 vs tr20 seed1 4096 at the SAME external 28-call cap: 48/150 vs 48/150 (+9/-9). Among 27 baseline episodes whose estimated max reasoning exceeds 2048, baseline 0/27, capped 1/27; among other 123, baseline 48/123, capped 47/123 (+8/-9). Retrospective subgroup, not a causal 2048 test. All external trajectories are already 28-capped, so cannot infer Champion 60->28 truncation. Our own FORK and Champion each had 6/17 reaching >=28, no >=55, but aggregate does not identify counterfactual final patches at call 28. Do not claim 60 is unnecessary or that 2048 rescues 104 tasks. Estimated fatal-turn clipping is not a correct-patch simulation.

## Prospective protocol
Only after explicit compute authorization and availability of genuinely independent gold/noop-valid tasks (the repeatedly inspected 17 are NOT fresh), run all five arms on identical preregistered task identities, rotate arm order and keep sampling/seed policy fixed. Primary metric paired actual resolved issues, not time, calls or submit rate. Report all arms including failures, paired rescue/regression counts, time/tool end reasons and actual duration. Estimate the interaction on task-level paired outcomes: (D-A)-(B-Champion). No assumption of additive budget effects. C vs control is separate; external C-like result is at 28, not 60. Report uncertainty clustered by task, and selection/multiple-comparison risk. Define the promotion rule before inference (at least two net rescues, <=1 regression, no scorer errors, <=115% total task time and calls vs control as exploratory minimum, independent confirmation needed); never use the winner of a five-arm sweep as proof by itself. Five arms x N x 300s is the maximum configured agent time (excludes setup/scoring), so account for total GPU quota before launch; do not duplicate already-running kernels. If no new eligible cohort or compute authorization, hold. No automatic promotion or submission.

Interpretation: prioritize B and D as plausible compute allocation interventions; A is necessary for factorial identification and C retained as requested. This priority is not an outcome ranking. No experiment here proves reduced thinking or tool limits improve score. Track all twelve variables in global ledger.
