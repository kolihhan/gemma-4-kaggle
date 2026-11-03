# Model-capacity probe v0 — corrected fallback design

Status: **PREFROZEN FALLBACK / DO NOT EXECUTE while Reliability-v1 ref `57921371` is pending.**

This supersedes the earlier version of this document that proposed a fresh E4B -> 12B matched probe as the first capacity test.

## Why the earlier 12B-first design is retired

Repository history recovered after the original prefrozen design shows that a naive same-lineage 12B substitution has already been tested twice on the historical `rich_3278` diagnostic:

- E4B root-coder + verifier lineage produced a wrong non-empty patch within the five-minute budget;
- 12B default-thinking run timed out with 0 patch;
- 12B thinking-budget-1024 run also timed out with 0 patch despite more tool activity.

Canonical evidence: `docs/research/recovered-12b-capacity-evidence-2026-11-03.md`.

This is only one repeatedly inspected task, so it does **not** prove 12B is globally worse than E4B. It is sufficient to make a fresh repeat of the same 12B experiment non-informative and wasteful.

## Trigger

Open the capacity lane only if one of these occurs:

1. Reliability-v1 Public LB is **< 0.05**, below the preregistered interval; or
2. a correctly instantiated evidence-before-mutation candidate materially increases relevant pre-edit evidence on untouched tasks but still fails to improve correctness enough to justify its cost.

If neither trigger fires, keep this lane research-only.

## Question

Is the current E4B lineage materially capacity-limited after accounting for lifecycle/evidence quality and the competition's global runtime budget?

The capacity hypothesis is now:

> A materially stronger model / model-policy combination may improve hidden resolution, but naive E4B -> 12B substitution under the existing five-minute lineage has already failed to add useful evidence.

Do not equate `capacity` with `use 12B`.

## Eligible next discriminating experiments

If the trigger fires, choose exactly one of these after a fresh preregistration.

### Option A — 31B same-policy probe

Compare:

- **control:** exact frozen E4B Reliability-v1 policy/topology/prompt/tool configuration;
- **treatment:** same configuration with only the declared base-model variant changed to 31B, subject to runtime feasibility.

Purpose: test whether a much stronger base model can convert an otherwise matched policy into correct repairs.

Risk: 31B may win by consuming substantially more latency/compute, so outcome must be judged with resolved-per-budget metrics, not raw solves alone.

### Option B — faithful strong-public architecture reproduction

Reproduce a demonstrably stronger public 31B-era architecture under a frozen contract, while preserving provenance and avoiding post-hoc tuning.

Purpose: test a broader model-policy-class alternative rather than pretending model size alone explains the external gap.

This is preferable to Option A if the public architecture cannot be meaningfully separated from its model/policy interaction.

## What remains fixed

For any capacity experiment, freeze as much as technically possible:

- task denominator;
- scorer/evaluator;
- no task-specific rules;
- no tuning after task-level inspection;
- prompts/topology/tool surface for a same-policy comparison;
- sampling/seed where supported;
- no LoRA/adapters unless the experiment is explicitly a training hypothesis instead of a capacity hypothesis.

Record unavoidable runtime/model differences explicitly instead of silently compensating for them.

## Untouched denominator

Do not use the inspected 17-task development denominator or `rich_3278` for promotion.

Freeze a new paired denominator before task-content or trace inspection, excluding all previously inspected/development/teacher/blind-preparation tasks. Both arms must run on the same selected IDs, and task-level traces must not be inspected between arms.

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
- resolved-per-minute / resolved-per-budget proxy.

Mechanism diagnostics after both arms finish:
- localization/evidence quality;
- root-cause correctness;
- edit synthesis quality;
- repair after relevant failure;
- whether the stronger model wins specifically where E4B had adequate evidence but still reasoned/edited incorrectly.

## Interpretation

### Stronger model ~= E4B

Capacity is weakened as the immediate bottleneck. Return priority to lifecycle, retrieval, search/repair, or training hypotheses according to untouched traces.

### Stronger model > E4B but resource-adjusted value is poor

Capacity matters scientifically but is not automatically competition-optimal. Distillation/SFT into E4B or a cheaper policy may become more attractive than promoting the larger model directly.

### Stronger model > E4B with acceptable resource cost

Model capacity/model-policy class becomes a serious candidate. A separate promotion contract is still required; this probe alone does not authorize a competition submission.

## Restrictions

RESTRICTION: Do not run a capacity probe while Reliability-v1 is pending.
WHY IT EXISTS: The live E4B score determines whether the architecture-level pivot trigger fires.
PIVOT TRIGGER: Reliability-v1 < 0.05, or untouched evidence-v0 shows good evidence formation without enough correctness gain.
STATUS: ACTIVE.

RESTRICTION: Do not rerun the historical 12B `rich_3278` smokes or repeat the same naive 12B-first test.
WHY IT EXISTS: Existing historical evidence already answers that narrow question poorly enough to make repetition wasteful.
PIVOT TRIGGER: New independent evidence identifies a materially different 12B policy/budget question that cannot be answered from existing artifacts.
STATUS: ACTIVE.

RESTRICTION: Do not copy a strong public 31B system wholesale without a frozen comparison contract.
WHY IT EXISTS: model size, topology, prompts, budgets, and development history are confounded.
PIVOT TRIGGER: none; a reproduction is allowed only as an explicitly scoped model-policy-class experiment.
STATUS: ACTIVE.

## Current decision

Capacity remains **REOPENED globally but not selected for execution**.

While Reliability-v1 is pending:

- no new GPU/model run;
- no duplicate submission;
- do not repeat 12B historical diagnostics;
- retain evidence-before-mutation as the current provisional lifecycle candidate;
- if the capacity trigger fires later, use this corrected design plus `recovered-12b-capacity-evidence-2026-11-03.md` before choosing the next experiment.
