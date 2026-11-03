# Evidence-before-mutation v0 — provisional design

Status: **DESIGN FROZEN / EXECUTION NOT AUTHORIZED while Reliability-v1 ref `57921371` is pending**.

This document chooses the smallest architecture that can test the current mechanism hypothesis without turning the known 17-task development set into another tuning loop.

## Mandatory checkpoint

CURRENT BEST:
- Frozen Reliability-v1 single-root E4B candidate; real Kaggle ref `57921371` pending.

REAL EVIDENCE OF STRENGTH:
- Compared with the earlier single-root topology run on the same 17 development tasks, Reliability-v1 reduced runtime by about 12% and mean non-empty patch size by about 20%, but resolution remained 1/17.
- Post-hoc same-classifier trace audit found 0/17 tasks with targeted behavioral evidence before first mutation in both runs.

MAIN FAILURE MODE:
- The agent commonly mutates from a plausible hypothesis before obtaining discriminating behavioral evidence. Post-edit targeted failures also did not reliably trigger repair before submission.

CURRENT BOTTLENECK HYPOTHESIS:
- Information quality before mutation is a stronger immediate bottleneck than raw call-budget efficiency.

IS THIS A LOCAL BUG OR MODEL-CLASS LIMITATION?:
- UNKNOWN. Current evidence is consistent with a lifecycle/policy limitation of the single-root agent, but does not prove the underlying Gemma model cannot perform the behavior.

WHAT METHOD CLASSES ARE CURRENTLY EXCLUDED?:
- Large-scale SFT/RL, always-on post-edit verifier, extra rescue agents, larger model, and broad topology redesign are not current first-line experiments.

WHY ARE THEY EXCLUDED?:
- None is yet required by the current causal diagnosis; each adds cost or confounding variables. These restrictions are provisional, not permanent.

HAS THE ORIGINAL REASON FOR EXCLUSION CHANGED?:
- Verifier-only LoRA remains NOT TESTED, not falsified. It should be reopened only if new untouched evidence again isolates downstream verifier compliance as the dominant bottleneck.

SMALLEST EXPERIMENT THAT CAN DISCRIMINATE BETWEEN THE COMPETING EXPLANATIONS:
- A pre-edit evidence stage that must form a concrete behavioral witness and localization package before handing the task to the editing coder, compared against the frozen Reliability-v1 control on a new untouched denominator.

WHAT RESULT WOULD CAUSE AN ARCHITECTURE-LEVEL PIVOT?:
- If the stage reliably creates relevant pre-edit evidence but repair correctness does not improve, the bottleneck moves downstream toward reasoning/model capacity, edit synthesis, or repair convergence; reopen training/search/model-family hypotheses rather than adding more evidence-stage rules.

## Restriction registry

RESTRICTION: Do not launch verifier-LoRA now.
WHY IT EXISTS: Current evidence points upstream to pre-edit information quality rather than downstream verifier compliance.
CURRENT EVIDENCE SUPPORTING IT: 0/17 pre-edit targeted evidence; Reliability-v1 soft repair/submission policy gap; no clean verifier-LoRA A/B exists.
PIVOT TRIGGER: New untouched traces show correct pre-edit evidence and mostly-correct candidate patches but repeated downstream verification/submit decisions remain dominant failures.
STATUS: ACTIVE.

RESTRICTION: Do not add a larger/more complex topology than one pre-edit stage plus one coder.
WHY IT EXISTS: Extra model stages cost latency/compute and obscure attribution.
CURRENT EVIDENCE SUPPORTING IT: Reliability-v1 already reduced runtime without improving resolution; prior post-edit specialization did not establish a general benefit.
PIVOT TRIGGER: The two-stage pre-edit experiment isolates a distinct downstream bottleneck that cannot be tested within the same two roles.
STATUS: ACTIVE.

RESTRICTION: Do not use the known 17-task development set to promote this candidate.
WHY IT EXISTS: Its task IDs/outcomes/traces have already shaped the hypothesis.
CURRENT EVIDENCE SUPPORTING IT: The set has been repeatedly inspected and is explicitly development-only.
PIVOT TRIGGER: Never for promotion. It may remain diagnostic-only.
STATUS: ACTIVE.

## Approaches considered

### A. Add one stronger pre-edit prompt rule to the current single-root agent

Pros:
- cheapest runtime change;
- smallest code diff.

Rejected as the main discriminating experiment:
- if it fails, we cannot tell whether evidence-before-mutation is wrong or whether the model simply ignored another prose lifecycle rule;
- Reliability-v1 already demonstrated that critical verification/repair/submission transitions are not reliably controlled by prose alone.

This remains a possible later ablation, not the primary candidate.

### B. Test-aware retrieval only inside the current single-root agent

Pros:
- low overhead;
- likely improves source/test pairing.

Not chosen as the first causal test:
- it improves evidence selection but does not separate evidence formation from mutation;
- failure remains ambiguous between bad retrieval and lifecycle non-compliance.

Keep this as a likely implementation component/ablation if the structural stage proves useful.

### C. Pre-edit evidence stage -> coder — chosen provisionally

Use one root evidence agent followed by one editing coder agent.

The evidence stage owns no `edit_file` and no `submit_patch`. Its job is bounded:
1. localize the likely implementation surface;
2. identify the smallest existing test/executable behavior relevant to the issue;
3. obtain a pre-edit witness when possible;
4. hand the coder a compact evidence package: hypothesis, source location, witness command/result, and what observation would falsify the hypothesis.

The coder then owns mutation, post-edit verification, bounded repair, and final submission.

Why this is preferred:
- it changes the information state before mutation, matching the current causal hypothesis;
- it makes the experiment more interpretable than another prompt-only patch;
- it is structurally different from the old post-edit verifier: the extra compute is spent before the first edit, where current evidence says information is missing.

## Important harness limitation

`run_command` can in principle mutate the working tree even when `edit_file` is absent. Therefore the evidence stage is not cryptographically read-only.

The candidate must treat zero pre-coder diff as an explicit invariant:
- evidence-stage prompt forbids write/edit commands;
- evidence stage checks `git diff --quiet` before handoff;
- coder checks that the incoming working tree is clean before its first mutation;
- trace audit records any pre-coder mutation as a contract failure.

Do not claim hard read-only isolation beyond what the host tool surface actually enforces.

## Frozen scientific variable

Only the lifecycle placement of evidence changes:

`issue -> bounded pre-edit evidence stage -> coder/edit/verify/submit`

Keep fixed unless explicitly required by the experiment:
- E4B model;
- sampling config;
- code-intelligence tool family;
- post-edit repair budget;
- submission packaging;
- evaluator/scorer;
- task time/tool budget where the harness permits.

No LoRA, RL, larger model, third agent, task-specific rules, or known-task hints.

## Untouched denominator contract

Do not evaluate on the known 17-task development denominator for promotion.

Before any candidate trace is inspected, freeze a new paired denominator by deterministic ID selection from the fixed competition task pool:
- exclude every task previously used for targeted development, topology smoke tests, LoRA teacher/dev/blind preparation, or manually inspected traces;
- choose by a committed seed/hash rule, not by repository/failure content;
- record only the selection rule, exclusions provenance, count, and denominator fingerprint before execution;
- run the frozen Reliability-v1 control and treatment on the same selected tasks;
- inspect task-level traces only after both arms are complete.

Initial execution should be staged:
1. static/schema validation only;
2. smallest untouched compliance smoke sufficient to verify that evidence precedes mutation and quantify overhead;
3. paired untouched A/B only if the lifecycle mechanism is actually instantiated.

No Kaggle Public LB is used to tune the candidate.

## Primary observables

Mechanism metrics:
- fraction of tasks with a relevant pre-edit behavioral witness;
- fraction with any working-tree mutation before evidence handoff (target: 0);
- witness relevance: same behavior/test reused after edit where feasible;
- change in non-empty-patch + failing-relevant-verification rate;
- repair-after-failed-targeted-check rate.

Outcome/resource metrics:
- resolved count on paired untouched tasks;
- elapsed time;
- model/agent invocations;
- tool calls;
- patch size;
- empty-patch rate.

Do not promote on mechanism compliance alone; correctness must improve enough to pay for added compute.

## Falsifiers

Evidence-before-mutation v0 is falsified as the next architecture if one of these occurs on untouched evidence:

1. the stage cannot reliably produce relevant pre-edit evidence without excessive overhead;
2. pre-edit evidence rises materially but wrong-patch/failing-verification outcomes do not improve;
3. resolved-per-budget degrades enough that any correctness gain is not competition-useful;
4. evidence is frequently misaligned, creating false confidence and worse edits.

If #2 holds, do not add more evidence-stage prompt rules. Reopen downstream hypotheses: reasoning/model capacity, edit synthesis, repair/search, training objective, or model-family ceiling.

## Promotion rule

No implementation or expensive run is authorized by this design alone.

After Reliability-v1 ref `57921371` becomes terminal:
1. calibrate the preregistered `0.08 [0.05, 0.12]` prediction against the actual score;
2. decide whether that feedback materially changes the bottleneck diagnosis;
3. if the diagnosis survives, freeze the untouched denominator before inspecting it;
4. implement only this single major variable;
5. pass static/compliance smoke;
6. run paired untouched A/B;
7. promote only if both correctness and resource-adjusted evidence justify it.
