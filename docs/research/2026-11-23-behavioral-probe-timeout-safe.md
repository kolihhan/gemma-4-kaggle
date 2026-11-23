# Gemma 31B behavioral probe — timeout-safe paired plan (2026-11-23)

## Goal and nonclaims

Increase **independently resolved issues**, not patch rate or code search hits. The new candidate is a **single prompt-policy trial**: an opportunistic, executable, bounded counterexample check after editing. It adds no tools, agents, models or training. The previous Champion already encouraged targeted verification; an incremental improvement is **unproven**. No public score or hidden-set timeout safety is established by a CPU bundle check.

## Exact packages

- Immutable source: Kaggle public notebook lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2, SHA256 a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3.
- Historical scored owner Champion: exact derived archive SHA256 ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b, official ref 58183466, Public 0.18.
- **CONTROL:** Champion files unchanged except evaluation.max_time_minutes 5 -> 4.
- **CANDIDATE:** CONTROL, changing only prompts/system.md to add a conditional issue-relevant, <=20s behavioral probe, at most one evidence-backed correction, and earlier submit if <=70s remain.
- Both: Gemma 4 31B, same sampling and all native tools, 4 minutes, 60 tool calls, 80 turns, unchanged command timeout. Deterministic bundles with SHA digests.
- The arms compare at equal 4-minute budgets; do NOT attribute differences from historical 5-minute 0.18 to verification.

## Timeout is the primary gate

Official competition: 12 hours for all patch generation, including sandbox setup, excluding patch validation. Kaggle Notebook may independently fail at its own time limit. The per-task max_time_minutes begins after environment setup. Therefore **4 minutes per task does not guarantee a global 12-hour pass**. Hidden set size and setup cost are unknown.

Assumption sensitivity with 30 minutes one-time startup and 45 seconds average setup per task:
- 120 tasks × (240s agent + 45s setup) + 1800s startup = 10h. Reserve one additional hour; pass the forecast.
- 140 tasks × (240s agent + 45s setup) + 1800s startup = 11h35m. Less than the reserved hour remains; fail the forecast.

Before official scoring estimate real task count, startup overhead and setup distribution. Keep >=1h planning margin. If unknown or unsafe, lower cap in BOTH matched arms before evaluating; do not claim timeout protection.

The model prompt recommends targeted shell command timeout 20 seconds, **but this is not a deterministic cap on every command**. The official per-task session timer is the enforceable hard stop. Confirm observed command wall time and patch submission behavior on real traces.

## Real-model next step (not run by this PR)

After native ADK compile and private quota checks, preregister eight fresh, disjoint issues with gold PASS / no-op FAIL in the same scorer epoch; do not expose reference patch or hidden tests to the model. Run the control and candidate on each frozen issue, alternating arm order. Measure actual model uptake of behavioral probe, resolved cases, rescues, regressions, wall time, tool calls, patches and test timeouts. Count each issue only once.

Primary outcome: net independent resolved issues. Stop if no net improvement, regressions or test latency causes missed submissions. This is a **prompt-level mechanism**, and uptake is NOT assured: CPU tests never substitute for model traces.

## Hard boundaries

Do not change or submit the scored Champion, run GPU, make Kaggle competition submissions, or publish private competition data from this CPU workflow. Green CI confirms reproducibility and budget contract only, not agent accuracy.
