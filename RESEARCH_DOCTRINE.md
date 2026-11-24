# Research Doctrine — Avoid Methodological Lock-In

This file is a durable research rule for the Gemma 4 competition. It supplements `AGENTS.md`, experiment contracts, `NOW.md`, and the evaluation policy. Current experiment contracts still control any already-frozen run.

## Core lesson

Do **not** copy a previous winner's method mechanically. In particular, this doctrine does not say "use RL" or "use fine-tuning".

The durable lesson is:

> Do not let an initially sensible research restriction become permanent after the evidence supporting it has changed.

A disciplined experiment loop can still converge to the wrong local optimum if the search space itself is artificially restricted.

## 1. Separate engineering correctness from competitive strength

Engineering correctness includes reproducibility, valid packaging, no leakage, passing tests, valid tool/runtime behavior, and compliance with competition constraints.

Competitive strength requires independent evidence that the system improves the actual task: untouched validation, meaningful slices, strong alternatives, and transfer toward the hidden distribution.

Never use engineering correctness as evidence of model quality.

## 2. Every major restriction needs a pivot trigger

Whenever a research plan says things such as:

- do not fine-tune;
- do not use RL;
- do not ensemble;
- keep the current model family;
- only improve the verifier;
- keep the current representation;
- do not redesign the topology;

record the restriction explicitly:

```text
RESTRICTION:
WHY IT EXISTS:
CURRENT EVIDENCE SUPPORTING IT:
PIVOT TRIGGER:
STATUS: ACTIVE / REOPENED / RETIRED
```

A restriction without a pivot condition is not an acceptable long-term research rule.

## 3. Detect model/policy-class ceilings

Treat these as signals that the current method class may be at a ceiling:

- repeated local patches with diminishing returns;
- gains concentrated on already-inspected failures;
- DEV improvement without external/hidden transfer;
- repeated symptoms from the same underlying error class;
- growing rule complexity needed to preserve old behavior;
- a simpler competing architecture systematically wins;
- local metrics stop correlating with Kaggle/hidden performance.

When several of these appear, stop asking only "what patch next?" and explicitly ask whether the representation, model family, training objective, search procedure, or topology is incapable of capturing the missing behavior.

Previously rejected method classes may then be reopened, including supervised fine-tuning, preference/ranking training, distillation, retrieval, ensembling, self-training, synthetic data, RL, search, verifier-guided generation, alternative losses, and different representations.

Reopening a method class is not authorization to use it. It means the old ban must be re-justified against current evidence.

## 4. Maintain local and global hypotheses simultaneously

Every active research lane must maintain two levels:

**Local:** what is the smallest next experiment?

**Global:** what is the current dominant bottleneck hypothesis?

Possible global bottlenecks include representation, data, distribution shift, optimization, model capacity, reasoning/generation, tool planning, state representation, verifier behavior, retrieval, calibration, search/inference, evaluation mismatch, or architectural ceiling.

After a few meaningful experiments, revisit the global diagnosis. Do not allow a long chain of local experiments to proceed merely because the next patch is easy to specify.

## 5. Build a learning loop, not only a patch loop

Handcrafted rules are appropriate for invariants, safety, formatting, deterministic constraints, and experiment hygiene.

They must not quietly become the primary mechanism for learning the task.

Preferred loop:

```text
error
-> identify failure class
-> gather or construct representative evidence
-> change representation / training / objective / search when necessary
-> evaluate on disjoint evidence
-> analyze residual failures
-> update the bottleneck hypothesis
```

## 6. Diagnose why an experiment works

For every promoted experiment, answer:

1. What changed?
2. Which slices improved?
3. Which slices regressed?
4. What mechanism plausibly caused the change?
5. What alternative explanation could produce the same result?
6. Does it survive disjoint validation?
7. Is it complementary information or merely a correlated variant?
8. What new prediction follows from the explanation?

Prefer experiments that teach something even when they fail.

## 7. Preserve anti-overfitting discipline

Architecture-level flexibility does **not** justify weaker evaluation.

Continue to enforce untouched validation where feasible, no leakage, no tuning after final/blind inspection, explicit DEV vs confirmation vs final evidence, paired comparisons when appropriate, reproducible contracts, exact provenance, FACT / INFERENCE / UNKNOWN, and retained negative results.

The goal is to be more willing to change the model class, not more willing to overfit.

## 8. Gemma 4-specific application

Current research hypotheses must never become permanent architecture mandates.

Examples:

- `evidence-before-mutation` may be the strongest current mechanism hypothesis, but it is not a permanent ban on different training, search, or topology.
- Verifier-only LoRA must not become the default final architecture merely because it has a clean scoped contract. If future untouched evidence isolates downstream verifier compliance as dominant, it may be reopened. If failures primarily originate upstream in generation/reasoning, tool planning, state representation, trajectory construction, training signal, or verifier-generator mismatch, stop disguising the problem as another verifier tweak.
- A read-only evidence stage, test-aware retrieval, search, supervised training, preference training, RL, or a different agent topology may be considered when evidence supports the corresponding mechanism. None is preferred merely because it is more sophisticated.

For any already-frozen experiment, do not mutate the contract mid-run in the name of this doctrine. Finish or stop it according to its preregistered rules, then reconsider the architecture at the next decision boundary.

## 9. Mandatory checkpoint before a major new direction

Before opening a substantial research lane, record:

```text
CURRENT BEST:
REAL EVIDENCE OF STRENGTH:
MAIN FAILURE MODE:
CURRENT BOTTLENECK HYPOTHESIS:
IS THIS A LOCAL BUG OR MODEL-CLASS LIMITATION?:
WHAT METHOD CLASSES ARE CURRENTLY EXCLUDED?:
WHY ARE THEY EXCLUDED?:
HAS THE ORIGINAL REASON FOR EXCLUSION CHANGED?:
SMALLEST EXPERIMENT THAT DISCRIMINATES BETWEEN THE COMPETING EXPLANATIONS:
WHAT RESULT WOULD CAUSE AN ARCHITECTURE-LEVEL PIVOT?:
```

Do not reflexively continue the existing lineage. Do not reflexively redesign it either. Follow the strongest independent evidence available.


## 10. Competition failure-triage: low score is evidence, not a stop command (2026-11-24)

**Owner direction:** Never discard a research idea solely because an initial Public Score, private pilot, or local score is low. A failed recipe does not disprove the underlying mechanism. Equally, successful packaging, fewer calls, or a nonempty patch is not proof of competitive strength. Do not reflexively patch or change architectures before identifying the bottleneck.

Adapt the owner's [Name That LLM research doctrine](https://github.com/kolihhan/name-kaggle/blob/main/RESEARCH_DOCTRINE.md) to software repair. Methodological references: [Kaggle Learner](https://github.com/Galaxy-Dawn/claude-scholar), [NVIDIA Kaggle Skill](https://github.com/NVIDIA/nvidia-kaggle), [Hypothesis Testing](https://github.com/rohitg00/skillkit), and [Scientific Critical Thinking](https://github.com/K-Dense-AI/scientific-agent-skills). Use their research principles; do not automatically install or execute external scripts.

### Required diagnosis before retiring a mechanism

1. **Verify measurement:** actual terminal Kaggle status, score/denominator, model, candidate ZIP hash, task IDs, grader and environment, matched budgets, errors and time. Distinguish PENDING, blank score, confirmed timeout and completed low score. Do not conflate CPU validation with model correctness.
2. **Separate weak implementation from weak idea:** investigate issue understanding, localization, model reasoning, tool-call serialization, missing tools/dependencies, failed mutations, wrong semantic fixes, verification bias, lost edits, termination behavior, task distribution and runtime. A single prompt, adapter or topology does not exhaust a method class.
3. **Analyze paired errors, not aggregate score alone:** rescues, regressions, both solved, neither solved, patch presence, time to first successful edit, tool errors, patch survival, test result and walltime. Distinguish callback events from physical calls; missing events are not proof that actions never occurred. Where available and lawful, compare actual failed patches with public-development reference patches after evaluation, isolated from all solving agents. Mark missing evidence UNKNOWN.
4. **Test competing hypotheses:** state at least two plausible causes with evidence for/against, predictions if true and false, and a minimal fixed-control experiment that distinguishes them. Prefer existing traces or a cheap CPU fixture when sufficient; run fresh matched model evaluations when necessary. Update the global bottleneck hypothesis after the result instead of simply creating another prompt or architecture.
5. **Preserve partial gains:** lower calls or latency, improved localization, valid mutation or patch emission may remain useful even when resolved count falls. Determine whether the improvement is independent and addresses a bottleneck; isolate it on fresh tasks. Never equate a proxy gain to correctness.
6. **Respect frozen evaluations and constraints:** do not mutate ongoing candidates, tune on spent holdouts, use hidden labels or suppress failures. Record small-sample limitations and gold/no-op certification status. Preserve the Champion, legal submission limits, 12-hour full-batch runtime cap and owner-authorized resource limits. A per-task cap does not guarantee complete Notebook runtime. Do not introduce schedulers or new training merely because a skill recommends them.
7. **Decision labels:** DIAGNOSE (unresolved root cause), REPAIR_BUG (verified defect), NEW_HYPOTHESIS (evidence-based mechanism change), PARK (resource/evidence limit, state reopening condition), PROMOTE (independent correctness and cost evidence), RETIRE_SPECIFIC_RECIPE (supported negative). REJECT_IDEA_BECAUSE_SCORE_LOW is inadmissible. Retiring a recipe for submission does not retire its research family.

### Apply to current Gemma research

| Observation | Competing explanations | Next discriminating evidence | Decision |
| --- | --- | --- | --- |
| Behavioral Verification: 4/8 to 2/8, zero rescues, two regressions ([paired run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45211599647), [trace audit](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45228018995)) | Probe consumes edit time; malformed arguments or trace serialization; incorrect behavioral hypothesis | Inspect attributable tool results, probe uptake, actual patches and edit chronology. Nineteen malformed recorded edit events concentrate in both regressions; uncertain responses/duplicate callbacks prevent causal claims. | DIAGNOSE; do not promote exact recipe, keep verification family open |
| Edit Grammar: 2/8 vs 2/8, calls 224 to 208, five nonempty patches each ([paired run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45256288841), [audit](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45286629098)) | Efficiency improves without better localization/semantic repair; earlier unsuccessful termination; small noisy pilot | Compare per-issue success, edit chronology and timing. Empty-patch tasks have no recorded edits. Identify whether saved calls enable actual repair. | DIAGNOSE; efficiency hypothesis remains open |
| Evidence-Channel #58729456 COMPLETE, blank score | Timeout, scoring/runtime failure, unavailable result | Obtain actual diagnostics if accessible. Blank is neither confirmed timeout nor zero. | DIAGNOSE |
| FastPath 40/4 #58808118 last verified PENDING ([receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45317046341), [status](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45393544885)) | Not a completed measurement | Retrieve terminal status before interpreting. | No performance conclusion |

The already-running [Single Edit Channel experiment](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45396076963) stays frozen. Its six paired issues test mutation-interface reliability, not an established gain. Analyze successful and failed patches and actual tool behavior, rather than automatically dropping this idea or opening a replacement architecture.

### Minimum low-score report

- Observed score/status, source and denominator; paired rescues/regressions and partial gains.
- FACT / INFERENCE / UNKNOWN.
- H1 and H2, supporting/contradictory evidence and predictions if true/false.
- Missing evidence and cheapest controlled discriminating test.
- Runtime, GPU and submission cost.
- Decision and reopening/falsification condition.

The objective remains independently verified repair correctness and official Public Score >= 0.25, not PR or audit count. After identifying an actionable mechanism, implement and evaluate it under the owner's constraints; do not substitute indefinite analysis for competitive progress.
