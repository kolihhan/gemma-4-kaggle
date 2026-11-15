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


## 10. Competition-Grandmaster research operating loop (2026-11-15)

**Purpose:** learn the transferable *experiment-decision process* of strong multi-domain Kaggle competitors, including Yuanzhe Zhou. This is our own synthesis, **not** a claim that this exact protocol is his published checklist. Objective: increase **official coding-agent resolved-task score**, not tool calls, prompt length, CI passes, or successful LoRA initialization. Best authenticated scored Public remains **0.18** until verified otherwise.

**Research beats ritual:** a correct Docker/Kaggle package, model load, dependency fix, timing check, green gate, or an agent that emits a patch is *engineering readiness*, not a resolved bug. Repeating old prompt-only tweaks after controlled 0/3-vs-0/3 evidence is not exploration.

**For each scientific decision:**
1. **Understand the score and task-generation process.** Describe how actual issue resolution is judged, what the official tools can observe, and the failure chronology on *the same issues*. Separate task localization, root-cause inference, edit correctness, executable validation, and timeout/invalid-patch errors. Inspect leading external solutions **for causal mechanisms**, not code to copy.
2. **Rank at least two conflicting bottleneck hypotheses** (e.g. wasted pre-edit exploration **versus** insufficient root-cause evidence or bad post-edit tests **versus** model/representation ceiling). State a concrete observation that would falsify each explanation; count *correct issues resolved*, not just changed lines.
3. **Design the cheapest useful paired test** with frozen model, harness and task selection before examining outcome; report paired rescues/regressions, first actual mutation time, test/repair chronology, calls and end-to-end cost. Never expose reference patches, grader labels or private issue texts to the agent.
4. **Spend compute for information gain.** Reuse authentic traces first, then a small source-disjoint, fixed-budget blinded cohort only if it can differentiate the hypotheses. A 3-task all-fail comparison is weak for a generalization claim but strong evidence **against promoting that exact prompt**; a synthetic 31B adapter smoke proves neither training benefit nor repair skill.
5. **Pivot at the research level.** If efficient tools, extra steps and prompt-only changes repeatedly fail to increase *resolved* tasks, investigate better evidence acquisition, representation, policy/training signal, verification feedback or search rather than appending another instruction. RL/QLoRA is neither mandatory nor banned: its scope needs a diagnosed deficiency, training-signal provenance, and held-out task-resolved test.
6. **Decide and record.** Separate engineering validity, mechanistic evidence, true resolution lift and official score; include regressions, costs, possible confounds, uncertainty and a kill criterion. Do not tune against repeated public leaderboard submissions.

**Minimum executable experiment contract:**

| Field | Required entry |
| --- | --- |
| Target | Official resolved-task score, own scored 0.18 reference |
| Observation | Same-issue error type and chronology, denominator/source |
| Hypotheses A vs B | At least two distinct mechanisms with falsifying observations |
| Treatment/control | Exactly one main change and identical budget/task selection |
| Evidence validity | Disjointness, rights, no reference-patch/oracle exposure |
| Primary/secondary | Paired resolved count first; edits/tests/time/calls second |
| Cost/stop | GPU quota, runtime, failures and cutoff preregistered |
| Outcome | Promote / revise / retire; alternatives and uncertainty |

**Immediate lane:** frozen public-prompt replacement had **0/3 vs 0/3**, more calls (71 vs 66); retire it as a score-improvement candidate. Compare actual traces for *early localization vs patch/test feedback* to choose a different mechanism, then run a small **new** issue-level paired test only when its eligibility and effect falsifier are frozen. Separately, the 31B QLoRA private smoke ended at 4-bit load \`ImportError\`; CPU image lacks bitsandbytes, but the GPU root cause is unconfirmed. That is an infrastructure issue, **not** the main research hypothesis.

When updating \`NOW.md\`, lead with the **scientific decision** and avoid repeated status-only cycles.

