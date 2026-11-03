# External architecture recon — 2026-11-03

Status: **research-only update while Reliability-v1 ref `57921371` remains pending. No new submission, GPU run, or frozen-candidate mutation is authorized by this note.**

## Question

Does current external evidence still support treating lifecycle/evidence quality as the next bottleneck, or has enough changed to reopen model-class, training, or broader topology hypotheses before implementing `evidence-before-mutation-v0`?

This review applies the repository doctrine: a previously sensible restriction must have a pivot trigger, and a strong alternative architecture is evidence that the current search space may be too narrow.

## Current external evidence

### 1. A public no-LoRA 31B-era agent is materially stronger than our completed E4B baseline

A current Kaggle discussion documents a public v19 coding-agent submission with verified Public LB **0.17**. The same write-up reports 44/129 and 49/129 solved on its 129-task public runs under its local setup, with v19 using an analyzer/root workflow plus prescribed localization/tracing rather than a learned adapter.

Source:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696

The v19 Public LB check in that write-up is dated **2026-10-09**. Kaggle's later staff announcement added the 12B/E4B/E2B competition variants after that earlier 31B-only period.

Source:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287

Our only completed competition score remains:

- `baseline-e4b-v0`: **0.03**
- `Reliability-v1`: still pending

**Inference:** the large gap is not a controlled model-size comparison, but it is strong enough that we must keep **model capacity / model-class ceiling** as an active global hypothesis. We cannot assume agent-policy changes alone will close the competitive gap.

Do not interpret this as permission to copy v19 or switch to 31B immediately. v19 differs in model size, topology, prompts, budgets, and development history.

### 2. More thinking/compute is not a monotonic solution

The same public experiment series reports that adding larger thinking budgets often increased session timeouts and empty patches. Public v19 variants with extra thinking did not establish a clean monotonic gain, and the competition has a fixed total runtime objective.

Source:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696

**Inference:** keep adaptive/value-of-information compute as a hypothesis. Do not respond to a low E4B score by simply raising thinking everywhere.

### 3. Tool behavior is version-dependent, so prompt dogma ages quickly

A public CPU replay of 314 graph-tool calls across wheelhouse builds found result-producing calls moving from 82 to 11 to 270 to 270 as harness builds changed. The same report measured many rejected edit/write tool calls in historical runs.

Source:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748323

A newer competition bug report also documents an array-argument parser failure mode that can freeze the inference server.

Source:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/753973

**Inference:** our policy should remain conditional and tool-state-aware. Do not encode permanent rules such as "never use graph" or "always use graph" from one harness build. Array-shaped graph/tool calls deserve extra caution because failure can be catastrophic under the global runtime budget.

### 4. Broader trajectory training is operationally more feasible than our old verifier-LoRA lane suggested

The public `gemma4-swe-kit` project now includes competition-oriented trajectory conversion/curation, distillation tooling, LoRA training paths including a free Kaggle TPU route, adapter-shape checks, and a vLLM logit canary.

Source:
- https://github.com/damsolanke/gemma4-swe-kit

This is **feasibility evidence**, not competitive proof. It weakens a blanket argument that trajectory-level LoRA/SFT is too operationally awkward to consider, but it does not show that training will solve our present bottleneck.

**Inference:** distinguish two training hypotheses:

1. old `verifier-LoRA-v0` — downstream verifier compliance; still NOT TESTED and not currently prioritized;
2. broader policy/trajectory distillation or SFT — potentially relevant if untouched evidence shows the base E4B agent understands the task poorly even after the evidence lifecycle is correctly instantiated.

Do not collapse these into one "LoRA" bucket.

## Global diagnosis update

### H-lifecycle — evidence / information quality before mutation

Status: **ACTIVE, provisional first candidate**.

Supporting evidence:
- 0/17 classifier-recognized targeted behavioral evidence before first mutation in both inspected single-root variants;
- Reliability-v1 became smaller/faster without improving the 17-task resolved count;
- soft lifecycle rules were not reliably enforced.

Counterweight:
- known denominator is development-only;
- the external 31B-era v19 anchor is much stronger than our completed E4B baseline, so model capacity remains unresolved.

### H-capacity — E4B model-class ceiling

Status: **REOPENED as a global hypothesis; not yet selected as the next experiment**.

Supporting evidence:
- public no-LoRA 31B-era v19 reached 0.17 while our completed E4B baseline is 0.03;
- Kaggle explicitly positions smaller variants partly as a speed/test-time-compute trade-off, not as quality-equivalent replacements.

Weakness:
- no controlled same-policy E4B vs 12B/31B comparison exists in this repo;
- topology/budget/history differ across the public v19 evidence.

### H-training — policy/trajectory distillation

Status: **REOPENED for feasibility; causal priority remains conditional**.

Supporting evidence:
- public competition-specific tooling makes teacher-trajectory curation and adapter training substantially more practical than before.

Weakness:
- no clean evidence yet that our dominant errors persist after the evidence state transition is fixed;
- old verifier-LoRA was never run, and its narrow target is not equivalent to broader policy training.

## Pre-registered decision rule when Reliability-v1 becomes terminal

Use the existing preregistered interval **0.05–0.12** as a calibration boundary, not as a target to optimize toward.

### If Public LB < 0.05

Interpretation:
- Reliability-v1 underperformed the preregistered interval and failed to establish that the current lifecycle-policy lineage transfers.

Decision:
- **do not automatically implement evidence-before-mutation-v0 first**;
- reopen the architecture-level checkpoint immediately;
- prioritize a smallest controlled test that can separate E4B policy limitation from model-capacity limitation, potentially including a same-policy larger-model capacity probe or a faithful strong-public-architecture reproduction under a frozen contract;
- keep training/search/model-family hypotheses open.

### If Public LB is 0.05–0.12

Interpretation:
- Reliability-v1 is consistent with our preregistered calibration but still far below the public 31B-era 0.17 anchor.

Decision:
- retain `evidence-before-mutation-v0` as the first causal mechanism test because the trace evidence directly supports it;
- keep H-capacity explicitly second, not banned;
- if evidence-v0 instantiates the mechanism but does not improve correctness, pivot to capacity/training/edit/search rather than stacking more evidence prompts.

### If Public LB > 0.12

Interpretation:
- Reliability-v1 transferred better than expected and materially closed the external gap.

Decision:
- lifecycle/policy improvements become more credible as a productive search direction;
- still do not call the mechanism proven from one LB point;
- proceed with the untouched evidence-v0 causal test, including the topology-matched null-handoff guard, before making a stronger causal claim.

## Restrictions and pivot triggers

RESTRICTION: Do not switch the competition candidate to 12B/31B now.
WHY IT EXISTS: Reliability-v1 E4B feedback is already pending; switching model class now would destroy calibration and mix policy with capacity.
CURRENT EVIDENCE SUPPORTING IT: No controlled same-policy model-size comparison exists; current E4B submission is unresolved.
PIVOT TRIGGER: Reliability-v1 scores below the preregistered interval, or a correctly instantiated evidence-v0 fails to improve correctness on untouched tasks despite high-quality evidence formation.
STATUS: ACTIVE, with H-capacity REOPENED globally.

RESTRICTION: Do not launch broader SFT/trajectory LoRA now.
WHY IT EXISTS: Training changes representation/policy broadly and is not yet required by the strongest current causal diagnosis.
CURRENT EVIDENCE SUPPORTING IT: Current trace evidence points to missing pre-edit evidence; no untouched demonstration yet shows persistent reasoning failure after that transition is fixed.
PIVOT TRIGGER: Untouched traces show relevant pre-edit evidence is present and used, yet repair decisions remain systematically wrong; or a model-capacity probe indicates the base E4B policy class is the limiting factor.
STATUS: ACTIVE, but training feasibility is REOPENED.

RESTRICTION: Do not copy public v19 wholesale.
WHY IT EXISTS: v19 is a multi-variable historical system from a different model-size/harness period; copying it would destroy attribution.
CURRENT EVIDENCE SUPPORTING IT: Its 0.17 Public LB is real external strength evidence but not a controlled ablation against this repo.
PIVOT TRIGGER: Use v19 only as a frozen external reference/reproduction candidate if the current E4B lineage materially underperforms its preregistered expectation or reaches an architecture ceiling.
STATUS: ACTIVE.

## Current PIC decision

While `57921371` is pending:

- no new expensive experiment;
- no duplicate submission;
- no implementation of evidence-v0;
- keep the newly added causal-identifiability guard and deterministic sequential-stage implementation plan;
- preserve H-capacity and H-training as explicitly reopened global hypotheses;
- when the live score arrives, apply the preregistered decision rule above before choosing the next experiment.
