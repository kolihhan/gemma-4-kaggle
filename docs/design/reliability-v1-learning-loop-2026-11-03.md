# Reliability v1 learning loop

## Intent

Deploy the already-frozen single-root Reliability-v1 candidate once, collect both development diagnostics and real Kaggle submission feedback, and use the discrepancy between predicted and observed behavior to choose the next single-variable experiment.

## Frozen candidate

No task-specific changes after inspecting the existing 17-task traces. Model, sampling, runtime budget, and code-intelligence tool surface stay fixed. Reliability-v1 changes only generic localization, edit-recovery, and targeted-verification policy.

## Anti-overfit boundary

The 17-task set is development-only. It can explain failure modes and regression behavior, but it cannot be called blind and cannot gate this submission. The public leaderboard is also not a hyperparameter oracle: one score updates calibration; it does not justify adding issue/repository-specific rules.

Pre-registered public-LB prediction: point 0.08, interval 0.05-0.12. The important learning signal is prediction error plus runtime/failure-class evidence, not whether one rounded score moved upward.

## Data handling

Competition Data is runtime-only. GitHub stores code, prompts, experiment contracts, and compact result summaries. The diagnostic Kaggle kernel mounts the competition source and official wheelhouse at runtime. Raw Competition Data is never committed or uploaded as a GitHub Actions artifact.

## Deployment loop

1. Static contract checks verify the exact frozen candidate hashes and current official scorer package compatibility.
2. A development diagnostic kernel evaluates the same frozen 17-task denominator. Its result is diagnostic only.
3. In parallel, a tiny private Kaggle builder notebook emits exactly `submission.zip` for the frozen candidate.
4. GitHub Actions submits that notebook output to the code competition through the Kaggle CLI.
5. The Action records submission ref/status and any public score available during the polling window.
6. Next analysis compares predicted vs observed score, runtime, tool-use, and failure modes before choosing the next hypothesis.

## Next hypotheses, deliberately not mixed into v1

1. Adaptive compute / value-of-information routing.
2. Reproduction-first debugging.
3. Test-aware retrieval.
4. Tool-schema reliability ablation only if traces show parser risk is material.
5. Conditional bounded rescue rather than an always-on verifier.

Each becomes its own experiment. No combined v1.1 bundle.
