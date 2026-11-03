# Evidence-before-mutation v0 — causal identifiability review

Date: 2026-11-03

Status: **research guard only; no implementation or execution authorized while Reliability-v1 ref `57921371` is pending.**

## Finding

The provisional `evidence-before-mutation-v0` design is a valid **practical architecture test**, but the primary frozen-control comparison is not by itself a clean causal test of the evidence mechanism.

The planned comparison is:

- A: frozen Reliability-v1 single-root agent;
- C: pre-edit evidence stage -> editing coder.

If C beats A, several things changed at once:

1. an extra independent model invocation exists before editing;
2. context is partitioned/compressed across stages;
3. role specialization is introduced;
4. the coder receives a structured handoff instead of doing all discovery in one trajectory;
5. LLM-turn and latency cost increase even if the same per-task tool-call budget remains in force.

Therefore `C > A` would show that the **two-stage candidate is useful**, but would not by itself prove that pre-edit behavioral evidence caused the gain.

This does not invalidate the current design. It changes what evidence is required before making a strong mechanism claim.

## Harness facts supporting a matched-topology control

The bundled harness documentation supports:

- `SequentialAgent` for strict sequential execution;
- `output_key` for saving one agent's final text into session state;
- `include_contents: none` for preventing conversation history from automatically entering the next agent;
- a shared per-task evaluation budget (`max_tool_calls`, `max_turns`, wall-clock limits);
- declarative multi-agent configurations under the same single base model.

This allows a topology-matched null-handoff control without custom Python execution.

The harness also documents that `AgentTool(skip_summarization: true)` can isolate context usage, which is another reason not to attribute any two-stage gain to evidence content without a matched control.

## Pre-register a conditional three-arm interpretation

Keep the current frozen practical control A and treatment C.

Before any untouched A/C execution, freeze a third configuration B:

### A — practical incumbent

Exact frozen Reliability-v1 single-root candidate.

Purpose: answer whether the new architecture is competition-useful relative to the incumbent.

### B — topology-matched null handoff

Use the **same evidence stage as C** with the same model, sampling, tools, stage order, and zero-diff invariant.

The evidence stage still runs and may form its normal evidence package, but the coder must not receive that package:

- store the stage result in session state if needed for artifact parity;
- set the coder to `include_contents: none`;
- do not interpolate the evidence-stage `output_key` into the coder instruction;
- give the coder only the original task state it would otherwise need.

Purpose: preserve the extra model stage, stage-local context use, and most compute/topology effects while removing the information handoff to the coder.

### C — evidence handoff treatment

Same evidence stage and coder topology as B, but the coder receives the pre-edit evidence package through the frozen `output_key` handoff.

Purpose: test whether transferring the behavioral witness/localization package to the coder adds value beyond the existence of a second stage.

## Resource-aware execution rule

Do **not** automatically pay for all three arms.

1. Freeze A, B, C definitions and the untouched denominator before task-level inspection.
2. Run A and C first.
3. Do not inspect task-level traces between A and C.
4. If C does not beat A by the predeclared practical promotion criterion, stop. The candidate is not useful enough; B is unnecessary.
5. If C does beat A, run the already-frozen B on the same denominator **before inspecting task-level traces**.
6. Only then inspect residual traces and explain the result.

This keeps the expensive matched-topology ablation conditional on the candidate first showing practical value.

## Interpretation table

| Result | Strongest defensible interpretation |
|---|---|
| `C <= A` | Two-stage evidence candidate is not practically justified; retire or redesign without paying for B. |
| `C > A`, `C > B` | Evidence handoff contributes beyond stage/context/topology effects, subject to mechanism-metric confirmation. |
| `C > A`, `C ~= B` | Improvement is more consistent with extra stage/context partition/independent reasoning than with evidence transfer itself. |
| `B > C` | The evidence handoff is likely misaligned or harmful even if two-stage topology helps. |
| `A >= B` and `A >= C` | No evidence that the added stage is worth its cost. |

Do not use tiny unresolved-count differences alone to claim `C > B`; pair outcome evidence with resource-adjusted metrics and the preregistered mechanism observables.

## Mechanism claim gate

A strong claim that **evidence-before-mutation** caused improvement requires all of:

1. C is practically better than A under the predeclared promotion criterion;
2. C is better than the already-frozen topology-matched B by a meaningful amount;
3. C materially increases relevant pre-edit witness formation/transfer;
4. pre-coder mutation remains zero by contract/audit;
5. the coder actually uses/reuses the witness where feasible;
6. the gain is not bought by competition-prohibitive latency/model cost.

If C beats A but not B, keep any useful two-stage architecture result but retire the specific evidence-handoff causal explanation.

## Zero-diff safety remains necessary

Removing `edit_file` and `submit_patch` from the evidence stage does not make it cryptographically read-only because `run_command` can mutate `/workspace`.

All B/C implementations must therefore keep the existing zero-diff handoff invariant and trace-level pre-coder mutation detection.

## Decision

- Keep `docs/design/evidence-before-mutation-v0-2026-11-03.md` frozen while the live Reliability-v1 submission is pending.
- Do not implement A/B/C now.
- When `57921371` becomes terminal, first reconcile the preregistered leaderboard prediction.
- If the bottleneck diagnosis survives, freeze the untouched denominator and all three configurations before any task-level inspection.
- Run the resource-aware conditional sequence above.

This guard prevents a future positive result from being over-interpreted as causal evidence merely because a more complex topology beat the current single-root baseline.
