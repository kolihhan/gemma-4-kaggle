# NOW — 2026-11-03

## North star

Build a competitive E4B software-engineering agent by learning which local signals actually transfer to Kaggle, not by chasing individual development tasks or public-LB noise.

## Current decision

**Deploy frozen Reliability-v1 once and use the result as a calibration experiment.**

Reliability-v1 is a single-root E4B agent. Relative to the previous topology experiment, model, sampling, runtime budget, and code-intelligence tool surface remain frozen. The only intended behavioral changes are generic localization discipline, edit/tool-recovery discipline, and targeted verification/submission policy.

## Anti-overfit boundary

The existing 17-task topology denominator is now development-only: task IDs, outcomes, and traces have been inspected. It may diagnose regressions and failure modes but cannot be called blind and cannot gate this submission.

The candidate is frozen before leaderboard feedback. Do not add FastAPI/Rich-specific rules or tune prompts against individual failures. Any next candidate must name one major variable; promotion evidence requires a new untouched set.

Pre-registered public-LB prediction lives in `docs/evaluation/reliability-v1-preregistered-prediction.json`:

- point: **0.08**
- interval: **0.05–0.12**

The purpose is calibration of our prediction process, not target-chasing.

## Deployment architecture

GitHub stores only code, prompts, experiment contracts, and compact summaries. Raw Competition Data is runtime-only.

`deploy-reliability-v1.yml` performs:

1. frozen-candidate unit/compile checks;
2. fresh official scorer-wheelhouse validation;
3. a 17-task development diagnostic in a private Kaggle kernel;
4. in parallel, a private Kaggle builder kernel that emits exactly `submission.zip`;
5. Kaggle CLI code-competition submission;
6. capture of submission ref, early status/public-score feedback when available, and compact diagnostic summaries.

The diagnostic result does not select whether the competition submission happens.

## Next research after feedback

Do not immediately add prompt rules. First compare prediction vs observed result and decompose the gap. Candidate next hypotheses are:

1. adaptive compute / value-of-information routing;
2. reproduction-first debugging;
3. test-aware retrieval;
4. isolated tool-schema/parser reliability ablation;
5. conditional bounded rescue rather than always-on verifier.

Only one major hypothesis moves into the next experiment.
