# VALIDATION — Gemma 4 Developer Agent (2026-11-16)
Primary quality measure: matched real independent issue grader-resolved fraction; official Public score is a separate distribution. Existing selected public-dev issues are **spent**, not fresh 30-task benchmarks.

| Comparison | Matched n | Real PASS baseline → candidate | Paired rescues/regressions | Difference / 95% paired bootstrap percentile CI | Evidence |
| --- | ---: | --- | --- | --- | --- |
| 31B V2 → 12B size-only | **3** | 1/3 → 0/3 | 0 / 1 | **-33.3 pp [-100, 0]** | [Action 43781086310](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43781086310) |
| 31B V2 → V3-R optional Skill | **3** | 1/3 → 1/3 | 0 / 0 | **0 pp [0, 0]** sample-only; **not a precision claim** | [Action 43689217134](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689217134) |
| 31B V2 → Early-Edit | **4** | 3/4 → 3/4 | 1 / 1 | **0 pp [-75, +75]** | [Action 43178431152](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43178431152) |

Bootstrap CI calculations above: exact enumeration of all n^n matched task resamples, equal probability, paired differences of task PASS indicators; for n=3/4 intervals are illustrative and underpowered. Especially [0,0] on all concordant outcomes cannot certify equivalence or rule out unobserved treatment effects.

## Official Kaggle ledger (NOT local CV)
- Scored champion **0.18** #58183466 [authenticated read-only ref in NOW](NOW.md).
- Historical 0.15 #58222227; #58350278 COMPLETE but **blank numeric score**. No numeric improvement claimed.
- Local 3/4-task metrics do **not** translate to the 12-hour hidden evaluator; no valid local-CV/Public correlation estimate exists.

## Prospective contract — NO NEW RUN AUTHORIZED
H0: a new mechanism produces no higher hidden-independent grader success than pinned V2. Compare on identical newly selected issues **without prior manual failure review**, stratified by repository and issue difficulty where grounded. Verify reference gold PASS/no-op FAIL in the same scorer epoch before inclusion; freeze inclusion independent of treatment outcome. Preserve no-op/gold confounds separately instead of replacing a failed treated item post hoc.

**Sample-size proposal requiring user confirmation:** minimum **30 independently selected matched tasks**; target more if the pilot disagreement rate and detectable gain demand it. Paired issue bootstrap CI and exact McNemar conditional on discordances; count rescues, regressions, tool calls from scorer, wall time and budget. A 30-task floor is not automatically enough to detect a few-percentage-point gain.

**Candidate advancement condition (proposed):** predeclared feasibility/uptake passes, legal harness, no invalid task handling; lower bound of paired 95% CI >0 for demonstrated improvement on independent tasks and within cost limits. Otherwise *INSUFFICIENT EVIDENCE*, never claim general elimination from n=3/4. Never choose based on leaderboard Public gain alone.

Official submission decision includes (paired DEV metric n+CI, official scored Public result, code SHA, elapsed and quota) in this ledger; retain two predeclared alternatives based on independent validation and robust diversity, no Public-LB tuning. Existing pretrained candidate CV `N/A` where not reproducible, never invented.
