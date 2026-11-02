# Post-v1 breakthrough hypotheses — 2026-11-03

## Question

After Reliability-v1 establishes a cleaner single-root baseline, what mechanism is most likely to improve hidden-distribution task resolution without overfitting the already-inspected Rich/FastAPI development traces?

This document is research only. It must not mutate the frozen Reliability-v1 candidate before its Kaggle feedback arrives.

## Evidence synthesis

### 1. The objective is budgeted resolution, not per-task maximal reasoning

The competition gives the agent 12 hours total to submit patches across all tasks, excluding patch validation. This makes compute allocation itself part of the algorithm: an action that marginally improves one hard task can lower overall score if it consumes enough time to prevent later tasks from finishing.

Primary source: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes

Competition experiments reinforce this. In the public v19/v20/v23 study, larger thinking budgets sometimes increased local solved counts but also sharply increased session timeouts and empty patches. A fixed high-compute policy is therefore not obviously Pareto-optimal.

Source: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696

**Inference:** the next major architectural variable should be *when to spend compute*, not simply *how much compute to allow everywhere*.

### 2. Localization is a real causal bottleneck, but graph should be conditional

LocAgent reports up to 92.7% file-level localization accuracy and downstream issue-resolution gains from graph-guided localization. The causal story is plausible: reducing the search space gives the repair model more useful context and fewer opportunities to wander.

Primary source: https://aclanthology.org/2025.acl-long.426/

Competition-specific evidence warns against a blanket graph policy. The same 314 graph queries returned results only 82 times on an early harness build but 270 times on later builds. Graph usefulness is therefore both task-dependent and harness-dependent. The current parser also has a reported array-argument failure mode that can freeze the inference server, which is especially relevant to array-shaped graph tools.

Sources:
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748323
- https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/753973

**Inference:** do not remove graph globally and do not call it reflexively. A better target is a low-cost routing rule that escalates from lexical → scalar semantic/neighborhood → graph only when ambiguity remains.

### 3. Reproduction-first can turn verification into causal evidence

ReProAgent decomposes bug reproduction into localization, root-cause analysis, test planning, and test generation, and reports 58.43%/70.30% reproduction success on SWT-bench-lite/verified with downstream repair improvement when integrated with repair systems.

Primary source: https://arxiv.org/abs/2607.09123

The competition constraint changes the engineering conclusion: an always-on multi-stage reproduction agent may be too expensive, but a tiny direct assertion or focused reproduction can still be high-value when the issue exposes a concrete behavioral contract.

**Inference:** reproduction should be an *adaptive verification action*, not a mandatory sub-agent pipeline.

### 4. Editing reliability is not cosmetic; it is part of reasoning quality

SWE-Edit identifies a context-coupling problem: inspection, modification planning, and format-sensitive edit generation compete in one context. Its Viewer/Editor separation improves SWE-bench resolved rate while reducing inference cost, and its learned editor adaptively selects editing formats rather than using one format for all edits.

Primary source: https://aclanthology.org/2026.findings-emnlp.485/

Competition traces independently show 105/524 edit/write calls rejected before execution in one public run, with repeated identical malformed calls accounting for much of the waste.

Source: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748323

**Inference:** Reliability-v1's edit-recovery guard is mechanistically justified. A later experiment could test a conditional editor or learned edit-format policy, but an always-on editor subagent would mix a new topology variable with the editing variable and should not be the first follow-up.

### 5. More autonomy is not automatically better

Agentless achieved strong SWE-bench Lite results with a simple localization → repair → validation pipeline rather than an open-ended autonomous loop. Its broader lesson is not that agents are useless, but that unnecessary action-selection freedom creates additional failure surfaces.

Primary source: https://arxiv.org/abs/2407.01489

**Inference:** our next design should add *selective* decision-making where it buys information, while keeping the default path simple.

### 6. Public-task description quality is a distribution-risk warning

A current competition discussion reports that many public task statements are extremely short and some are essentially title + GitHub URL while the sandbox has no network. Whether this is intentional for the hidden set is unresolved.

Source: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746944

**Inference:** optimizing rules around particular public issue-description pathologies is especially dangerous. The agent should detect uncertainty/underspecification generically rather than memorize Rich/FastAPI patterns.

## Ranked post-v1 hypotheses

### H1 — Adaptive compute / value-of-information routing — highest priority

**Mechanism:** choose the cheapest action that can discriminate between current hypotheses, and escalate compute only when uncertainty remains.

Candidate policy shape:

`lexical localization → direct read/assertion → semantic/neighborhood lookup → graph/deeper reasoning only if ambiguous`

**Why it may transfer:** it is task-agnostic and directly aligns with the 12-hour global objective.

**Falsifier:** on a new untouched set, it does not preserve resolution or does not reduce median/total calls and time relative to Reliability-v1.

### H2 — Reproduction-first for concrete behavioral issues

**Mechanism:** when the issue exposes a clear input/output or failure condition, generate/run the smallest reproduction before editing; use the same check after editing.

**Why it may transfer:** converts verification into causal evidence and reduces plausible-but-wrong patches.

**Falsifier:** reproduction overhead dominates, or generated assertions are too often invalid/misaligned to improve resolved rate.

### H3 — Test-aware retrieval

**Mechanism:** retrieve not only likely source symbols but also the smallest existing test or executable path that exercises them.

**Why it may transfer:** jointly solves localization and verification selection rather than treating them as separate late-stage steps.

**Falsifier:** retrieved tests are usually irrelevant/broad or do not improve repair decisions on untouched tasks.

### H4 — Conditional edit protocol / tool-schema reliability

**Mechanism:** keep normal edit_file for simple replacements, switch to an asserted script/editor path only after edit complexity or parser-risk signals.

**Why it may transfer:** targets a measured harness failure surface without paying a permanent subagent cost.

**Falsifier:** parser/edit failures are rare after Reliability-v1 or the fallback increases malformed/wide edits.

### H5 — Conditional bounded rescue

**Mechanism:** single-root remains the fast path; invoke one bounded rescue specialist only after a high-information trigger such as failed directly relevant verification with a plausible patch or unresolved cross-file ambiguity.

**Why it may transfer:** previous two-stage and single-root successes were disjoint, suggesting complementarity, but always-on handoff wasted context and time.

**Falsifier:** rescue consumes budget without adding unique solves on a new untouched set.

## Experiment discipline after Reliability-v1 feedback

1. First compare pre-registered prediction with actual public score and development aggregate.
2. Explain prediction error before changing the agent.
3. Select exactly one hypothesis above.
4. Freeze a new untouched evaluation denominator before inspecting its traces.
5. Change one major variable only.
6. Keep model/sampling/budget fixed unless the experiment is specifically about compute allocation.
7. Do not add task-ID, repository-name, or observed-instance-specific prompt rules.
8. A leaderboard gain without a supporting untouched/local mechanism result is evidence of outcome, not evidence that the hypothesized mechanism is correct.
