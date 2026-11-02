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

`deploy-reliability-v1.yml` performs frozen-candidate checks, fresh official scorer validation, a 17-task development diagnostic, and an independent real competition submission path. The diagnostic result does not select whether the competition submission happens.

### Verified deployment state

- Frozen-candidate unit tests and compile checks: **PASS**.
- Fresh current official scorer-wheelhouse validation: **PASS**.
- Reliability-v1 builder kernel produced an exact five-file `submission.zip`: **PASS**.
- Kaggle `CreateCodeSubmission` request shape is valid. A direct API probe exposed the actual server rejection reason rather than the CLI's generic HTTP 400.
- Reliability-v1 has **not** consumed a competition submission slot yet.
- Existing old submission ref **57879765**, description `baseline-e4b-v0`, submitted 2026-11-01 17:59:25 UTC, is still `PENDING` with no public/private score. Kaggle rejects another code submission while this team submission is pending.
- `wait-slot-submit-reliability-v1.yml` run **41487538624** is active. It checks ref 57879765 read-only, deduplicates against any existing Reliability-v1 submission, and submits the already-frozen builder kernel/version exactly once after the slot becomes available.
- The original Reliability-v1 17-task diagnostic remains a single run, `deploy-reliability-v1.yml` run **41485671952**, diagnostic job **125417231948**. Do not launch a duplicate diagnostic while it is running.

Do not interpret the pending-slot transport condition as a scientific failure of Reliability-v1.

## Research state

`docs/research/post-v1-breakthrough-hypotheses-2026-11-03.md` ranks transfer-oriented follow-ups without modifying v1.

Current research priority after v1 feedback:

1. **Adaptive compute / value-of-information routing** — cheapest discriminating action first, escalate only under ambiguity.
2. Reproduction-first for concrete behavioral contracts.
3. Test-aware retrieval linking likely source locations to the smallest useful verification target.
4. Conditional edit/tool-schema reliability path.
5. Conditional bounded rescue instead of an always-on verifier.

These are hypotheses, not queued implementation. Do not move one into the candidate until Reliability-v1 feedback is analyzed and one major variable is selected.

## Next decision after feedback

Do not immediately add prompt rules. First compare the pre-registered 0.08 [0.05, 0.12] prediction with actual Kaggle score and the development aggregate, then explain the prediction error. Select exactly one next hypothesis and freeze a new untouched evaluation denominator before inspecting its traces.
