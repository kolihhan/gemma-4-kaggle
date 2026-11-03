# Model-capacity probe v0 — fallback design

Status: **PREFROZEN FALLBACK / DO NOT EXECUTE while Reliability-v1 ref `57921371` is pending.**

## Trigger

Run this lane only if one of these occurs:

1. Reliability-v1 Public LB is **< 0.05**, below the preregistered interval; or
2. a correctly instantiated evidence-before-mutation candidate materially increases relevant pre-edit evidence on untouched tasks but does not improve correctness enough to justify its cost.

If neither trigger fires, this remains research-only.

## Question

Is the current E4B lineage limited primarily by agent policy/lifecycle, or is Gemma E4B itself a material capacity bottleneck under an otherwise matched policy?

This is a **model-class discrimination test**, not a new champion candidate and not permission to tune larger models.

## Current competition facts

As verified from current Kaggle competition material on 2026-11-03, submissions may use exactly one of:

- `gemma-4-31b-it-qat-w4a16-ct`
- `gemma-4-12b-it-qat-w4a16-ct`
- `gemma-4-e4b-it-qat-w4a16-ct`
- `gemma-4-e2b-it-qat-w4a16-ct`

All agents/subagents inside one submission must use the same base-model variant. E2B/E4B remain eligible for the small-model bonus; 12B/31B are main-track capacity alternatives.

## Scientific variable

Primary comparison:

- **A — E4B control:** exact frozen Reliability-v1 policy/topology/prompt/tool configuration.
- **B — 12B treatment:** identical configuration with only the declared base-model variant changed to 12B.

Do **not** start with 31B. 12B is the smallest capacity increase and therefore the cleaner first discrimination test.

Only if 12B shows a meaningful correctness gain that exceeds its resource penalty may a later 31B probe be justified.

## Why 12B first

A direct E4B -> 31B jump changes capacity and runtime too aggressively. If 31B wins, attribution is weak and the result may be unusable under the 12-hour global budget.

E4B -> 12B asks a narrower question:

> Does a moderate capacity increase, holding the agent policy fixed, recover repairs that the E4B policy cannot execute reliably?

This follows the research doctrine: reopen the model class with the smallest discriminating experiment, not a wholesale architecture switch.

## What must stay fixed

Unless technically impossible under the harness, freeze:

- agent topology;
- prompts/instructions;
- tool surface;
- sampling parameters and seed;
- per-task tool-call/turn limits;
- repair policy;
- submission ownership;
- scorer/evaluator;
- task denominator;
- no LoRA/adapters in either arm.

Record any unavoidable runtime-only difference explicitly rather than silently compensating for it.

## Untouched denominator

Do not use the inspected 17-task development denominator for promotion.

Use a newly frozen paired denominator selected before task-content or trace inspection, excluding all previously inspected/development/teacher/blind-preparation tasks.

Both E4B and 12B must run on exactly the same task IDs.

Do not inspect task-level traces between arms.

## Primary observables

Outcome:
- resolved count / resolution rate;
- unique solves by arm;
- empty-patch rate;
- non-empty unresolved patches with failing relevant verification.

Resource:
- elapsed time;
- model/agent invocations;
- tool calls;
- timeout rate;
- resolved-per-minute and resolved-per-budget proxy.

Mechanism diagnostics after both arms complete:
- localization quality;
- correctness of inferred root cause;
- edit synthesis quality;
- repair after relevant failure;
- whether 12B wins on tasks where E4B had adequate evidence but still chose/synthesized the wrong fix.

## Interpretation

### B ~= A

Capacity is not supported as the immediate bottleneck at this scale. Do not jump automatically to 31B. Return priority to lifecycle, retrieval, search/repair, or training hypotheses according to untouched traces.

### B > A but resource-adjusted value is poor

Capacity helps scientifically but may not be competition-optimal under the 12-hour global budget. Consider whether distillation/SFT into E4B or adaptive use of a stronger model class is possible within competition constraints; do not promote 12B solely on raw solves.

### B > A with acceptable resource cost

Model capacity is a real bottleneck candidate. A 31B probe becomes eligible, but must be separately preregistered and justified by the remaining gap.

### B improves tasks despite E4B having good localization/evidence

This is the strongest signal for a reasoning/edit-synthesis capacity ceiling and also raises the priority of trajectory distillation/SFT.

### B mostly wins because it spends more time/turns

Do not call this a pure capacity effect. Separate model quality from compute allocation before promotion.

## Falsifier

The capacity hypothesis is weakened if 12B, under a matched frozen policy and paired untouched denominator, fails to produce a meaningful correctness gain or loses enough resolved-per-budget to be competition-useless.

## Restrictions

RESTRICTION: Do not run this while Reliability-v1 is pending.
WHY IT EXISTS: The live E4B score is required to decide whether the model-class pivot trigger fired.
PIVOT TRIGGER: Reliability-v1 < 0.05, or untouched evidence-v0 demonstrates good evidence formation without correctness gain.
STATUS: ACTIVE.

RESTRICTION: Do not tune prompts/budgets separately for 12B before the matched comparison.
WHY IT EXISTS: That would confound model capacity with policy optimization.
PIVOT TRIGGER: Only after the matched capacity question is answered and a new experiment is preregistered.
STATUS: ACTIVE.

RESTRICTION: Do not jump directly to 31B.
WHY IT EXISTS: 12B is a smaller, cheaper, cleaner capacity intervention.
PIVOT TRIGGER: 12B materially improves correctness with acceptable resource cost, or independent evidence makes 12B technically non-diagnostic.
STATUS: ACTIVE.

## Current decision

This design is now prefrozen so a low Reliability-v1 score cannot cause a post-hoc, score-shaped experiment design.

No implementation, GPU run, or competition submission is authorized by this document alone.