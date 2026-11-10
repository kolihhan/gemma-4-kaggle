# Gemma 4 — Public leaderboard repeatability audit (2026-11-11)

**Decision:** Do not promote a +0.01 Public score as an independently verified solver improvement. A score can move when the *exact same packaged config* is reevaluated; the public set is small and competition scoring is a single stochastic run.

## Provenance and executable evidence

- Independent community dataset: [Dariush Afshar, `gemma-4-agent-public-config-draws`](https://www.kaggle.com/dariushafshar/gemma-4-agent-public-config-draws), CC BY 4.0. The dataset records public notebook version scores and, only when source could be traced safely to the bundle contents, `files_sha256` of its serialized bundle dictionary.
- Reproducible, **CPU-only** GitHub Action: [run 42868703115](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42868703115) and [workflow](../.github/workflows/v4-public-score-repeatability-one-shot.yml). It downloaded only the public aggregate CSV, printed summary statistics, **did not publish source rows, run Gemma, fetch competition tasks, create Kaggle submissions, or consume GPU**.
- Audit executed 2026-11-10 17:48 UTC (2026-11-11 01:48 MYT). Only records with an actual score, `hash_kind=files`, and a 64-digit `files_sha256` were counted as exact-file-set matches. Different notebook versions with ambiguous/untraceable bundles were excluded from the repeatability comparison.

## Observed results

| Measure | Value |
|---|---:|
| Rows inspected | 145 |
| Scored rows | 145 |
| Unique traced exact-file-set hashes | 21 |
| Exact-file-set hashes with at least two scored observations | 6 |
| Scored observations belonging to those six repeat groups | 29 |
| Within-hash pairwise comparisons | 84 |
| Repeat groups with non-zero observed score spread | **6 / 6** |
| Median absolute score difference across the 84 within-hash pairs | **0.02** |
| Maximum observed same-bundle score range among the six groups | **0.10** |

**Interpretation:** A single 0.17→0.18 change is smaller than the sample's median same-bundle pair difference. The hidden scorer's full tasks, task-level paired outcomes and seeds are not public to this audit, and these six groups are not a randomized sample. The 84 pair comparisons are correlated (the same 29 observations recur), so do **not** mislabel them as 84 independent trials or use these statistics as a formal confidence interval for the user’s agent. A distinct score can still represent a real improvement; this dataset simply invalidates the inference that a *single* +0.01 is sufficient proof.

The public LB is widely inferred to contain 58 issues: [Kaggle competition discussion 743506](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743506), based on the observed truncated score lattice. As an approximate resolution, one task contributes roughly 1/58 = 0.01724 to the untruncated score; the displayed decimal movement must not be confused with a precise percentage point of consistent improvement.

## What counts as evidence for the next V4 decision

1. **Execution validity:** exact frozen candidate `5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be` (31B, 5 minutes/28 calls) is accepted by the authenticated Kaggle competition; record ID and receipt. Frozen CPU integration PASS is already established but is not real-model proof.
2. **Behavioral uptake:** on real Gemma 31B trajectories, measure whether `load_skill` and `run_skill_script` were called, whether a generated contract was meaningful, the fraction returning blocked, the fraction with non-empty source diffs, and actual hidden issue resolution if the platform reveals it. Do not claim any of these without logs.
3. **Competitive interpretation:** score against verified 0.18 control, preserving model/budget and avoiding repeated micro-tuning to public cases. Record the numeric outcome even if it is worse. A single V4 run may justify continuing investigation, but a one-task increment is *not* a generalizable architecture breakthrough.
4. **Resource discipline:** official quota is one per day currently; run one legally authorized code submission at most when quota is available. Do not spin up new duplicate GPU test notebooks or retrospectively alter controls.

## Misleading notebook titles

A notebook titled [`Gemma 4 Baseline | LB 0.24`](https://www.kaggle.com/code/honghanhhh/gemma-4-baseline-lb-0-24) displayed **Best Score 0.18 V3** when publicly checked on 2026-11-11. Its title is not an authenticated 0.24 proof. Similarly, [`Gemma and the Shape of Doubt`](https://www.kaggle.com/code/prvsiyan/gemma-and-the-shape-of-doubt) shows **Best 0.20 V32**, while its latest visible Public Score is 0.15. Distinguish *historical best*, *latest score*, *title text* and *the user's authenticated score*.

## Current user-owned competition status

- Authenticated best scored Public: **0.18**, ID **58183466**. This is an achieved score, not evidence of a reproducible gain from V4.
- Current V4 score: **none yet**. Last authenticated Kaggle quota at 2026-11-10 17:37 UTC was allowed_now=0, active=[].
- Current valid manual submission workflow: `main/.github/workflows/submit-v4-cgr-manual.yml`, pinned to source `b9ab80af9da55e0808971011a91ae925b3f5d05c`, without scheduling or automatic submission.
