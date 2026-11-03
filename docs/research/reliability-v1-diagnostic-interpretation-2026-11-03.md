# Reliability-v1 diagnostic interpretation — 2026-11-03

## Decision supported

Use already-completed development evidence to explain what Reliability-v1 changed and what it did **not** change, without rerunning the inspected 17-task denominator or mutating the frozen submission candidate.

This is mechanism analysis, not promotion evidence. The 17 tasks are development-only and their traces have already shaped the project.

## Verified aggregate evidence

Reliability-v1 source run: `deploy-reliability-v1.yml` run `41485671952`, diagnostic job `125417231948`.

- requested/completed: **17 / 17**
- resolved: **1 / 17**
- non-empty patches: **13 / 17**
- empty patches: **4 / 17**
- mean tool calls: **10.41**
- median tool calls: **10**
- mean duration: **89.21 s**
- median duration: **85.61 s**
- call-cap exhaustions: **0**
- non-empty unresolved patches with non-zero evaluator verification exit: **12 / 12**

Against the earlier single-root topology run on the same 17-task denominator, Reliability-v1 kept resolution at **1 -> 1**, while total evaluator runtime fell from about **1726 s -> 1517 s** and mean non-empty patch size fell from about **1147 -> 920 characters**. Evaluator-reported total tool calls were effectively flat (**176 -> 177**).

**Interpretation:** Reliability-v1 became more restrained and somewhat faster, but the savings did not convert into more correct repairs.

The real Reliability-v1 Kaggle submission ref `57921371` is still pending at the latest read-only probe. No leaderboard score is used to select a candidate here.

## Verified post-hoc trace mechanics audit

Canonical audit: GitHub Actions run `41590900152`, job `125767140355`, compact artifact `13209917848`.

The Action used CPU only. It downloaded two already-completed Kaggle kernel outputs, reduced traces to tool-sequence mechanics, enforced a fail-closed output boundary, and uploaded only three compact JSON summaries. It did **not** push a Kaggle kernel, consume GPU inference, rerun any task, or upload raw traces.

Analyzer verification in the Action: **8/8 synthetic tests PASS** plus `py_compile` PASS.

### Same-classifier A/B

The analyzer is intentionally conservative. Compound shell commands are not guessed to be targeted tests, so absolute targeted-test counts may be underestimates. The useful comparison is the A/B under the same classifier.

| Mechanic | Earlier single-root | Reliability-v1 |
|---|---:|---:|
| Resolved | 1 | 1 |
| Tasks with targeted evidence before first mutation | **0** | **0** |
| Targeted-test calls | 3 | 3 |
| Tasks with no targeted test | 15 | 14 |
| Broad-test calls | 14 | 10 |
| Localization-tool calls | 0 | 4 |
| Mutations | 40 | 39 |
| Failed targeted check after mutation | 1 | 2 |
| Repair after failed targeted check | **0** | **0** |
| Submit after latest targeted failure | 1 | 2 |
| Tasks whose final targeted check passed | 0 | 1 |

Normalized analyzer tool-call totals are **190 -> 195** and use different counting semantics from evaluator totals; do not mix the two metrics.

## Mechanism conclusion

### 1. Pure compute-efficiency is not the immediate repair-quality bottleneck

Reliability-v1 did not generally exhaust its call budget, reduced runtime and broad testing, and produced smaller patches, yet resolution stayed flat.

**Inference:** budget-aware routing still matters to the competition-wide 12-hour objective, but simply making the agent shorter/cheaper is unlikely to solve the current correctness bottleneck.

### 2. The missing capability is earlier high-quality behavioral evidence

Under the conservative audit, **0/17 tasks in both runs obtained a targeted behavioral witness before the first source mutation**.

This is stronger than saying “the agent should test more.” The key missing state transition is:

`hypothesis -> discriminating evidence -> edit`

rather than the observed common pattern:

`plausible hypothesis -> edit -> discover failure later`

**Inference:** evidence-before-mutation is the strongest next mechanism because it changes the information available to root-cause reasoning before code is touched. It can potentially reduce F2 UNDERSTAND and F3 EDIT together, and gives F5 REPAIR a better-defined post-edit comparison.

### 3. Reliability-v1 soft policy did not reliably control critical lifecycle transitions

The frozen coder policy says that directly relevant verification failure permits at most one narrow repair/test cycle and that a known-failing patch must not be submitted. The post-hoc audit nevertheless observed conservative targeted failures followed by **no mutation/repair**, and submission still occurred afterward.

This is not proof that every such submission was semantically wrong; the targeted-test classifier is conservative and a tool-shaped test may itself be misaligned. It is, however, direct evidence that critical lifecycle invariants are **not reliably enforced by prose instructions alone**.

**Implication:** adding more prompt sentences is now a lower-priority intervention. Reliability-v1 already added generic verification/recovery language and changed surface behavior, but did not reliably instantiate the intended state machine.

### 4. A passing command-shaped check is not enough

Reliability-v1 produced one task whose final classifier-recognized targeted check passed while the task was still unresolved.

**Inference:** the next mechanism must optimize **evidence relevance**, not merely test execution frequency. A cheap but behaviorally misaligned test can create false confidence.

## Updated breakthrough ranking

### H1 — Evidence-before-mutation — strongest next mechanism

**Mechanism:** before a source mutation, obtain the cheapest high-information behavioral witness available when the task exposes a concrete contract. Prefer an existing directly relevant test; otherwise use a minimal executable assertion/reproduction. Reuse the same witness after the edit when possible.

**Important:** this is a mechanism, not yet an implementation choice.

Possible implementations to compare later:

- single-root policy with stronger evidence selection;
- test-aware retrieval that pairs a source candidate with its smallest exercising test;
- a minimal read-only evidence/localization stage whose tool surface mechanically excludes editing before handing evidence to the coder.

The last option is structurally stronger than prose but costs an additional agent stage. It must not be assumed superior merely because it is “harder.”

**Falsifier:** on a new untouched denominator, evidence-before-mutation does not reduce wrong-patch / failing-relevant-verification outcomes or its overhead reduces resolved-per-budget enough to erase the benefit.

### H2 — Test-aware retrieval — likely implementation lever for H1

**Mechanism:** jointly retrieve likely source locations and the smallest existing executable path that exercises the same behavior.

This may be cheaper and less hallucination-prone than generating a reproduction when a good test already exists.

**Falsifier:** retrieved tests are usually broad/misaligned, or evidence selection improves without changing repair correctness.

### H3 — Adaptive compute / value-of-information routing

Keep as an efficiency mechanism, but define it as **choose the next action by expected discrimination between hypotheses**, not “use fewer calls.”

It becomes complementary to H1 rather than the first repair-quality intervention.

### H4 — Conditional edit/tool-schema reliability

Reliability-v1 changed edit format behavior: direct edits decreased while script-side edits increased, without changing total mutation volume or resolution. Keep this conditional; current evidence does not show edit grammar as the dominant bottleneck.

### H5 — Conditional bounded rescue / topology

Do not add an always-on verifier or rescue agent merely to enforce policy. The competition submission format is declarative and uses a closed host tool registry, so a custom deterministic submit wrapper is not available; the harness can also extract a non-empty working-tree diff even when `submit_patch` is never called.

If structural enforcement is tested later, the more causally aligned experiment is a **read-only evidence stage before mutation**, not another post-edit verifier. That is a distinct hypothesis and must pay for its extra topology/model-call cost on a new untouched denominator.

## Historical route closure — verifier-LoRA v0

**Verdict: NOT TESTED, not falsified.**

The frozen verifier-LoRA training workflow exists and is well specified, but it accepts execution only through `workflow_dispatch` or `workflow_call`. A repository-wide Actions query on 2026-11-03 found exactly one `workflow_dispatch` run, the baseline submission workflow, and **zero `workflow_call` runs**. The public one-shot training wrapper on `exp/public-train-once` had a push-triggered run, but that run was skipped rather than producing a successful training execution.

Therefore there is no verified successful verifier-LoRA training run, no verified frozen adapter artifact, and no clean adapter-vs-base development/blind A/B to interpret.

This route must not be described as a failed scientific hypothesis. It is an **unexecuted historical experiment**. It is also **not the current priority**: the newer Reliability-v1 evidence points upstream to evidence quality before mutation, whereas verifier-only LoRA targeted downstream verification/compliance behavior.

Resource decision: do **not** launch verifier-LoRA now merely to close the historical experiment. Reopen it only if future untouched evidence again isolates downstream verifier compliance as the dominant bottleneck and the expected information gain justifies a GPU run.

## Anti-overfit boundary

Do not tune new prompt rules to the 17 known task IDs, repository names, individual reference patches, or manually inspected failure details.

The development evidence may update the **hypothesis ranking**, but it may not promote a candidate. Before implementing the next major variable:

1. consume the already-submitted frozen Reliability-v1 Kaggle feedback when it becomes terminal;
2. explain prediction error rather than target the score;
3. freeze a **new untouched evaluation denominator before inspecting its traces**;
4. pre-register one mechanism, targeted failure surface, expected observable effect, resource cost, and falsifier;
5. keep model/sampling/tool surface fixed unless one of them is explicitly the variable under test.

## Resource decision

No additional Kaggle GPU run is justified now. Reuse the completed trace-mechanics artifact for mechanism work; do not rerun the 17-task denominator and do not launch verifier-LoRA only for historical completeness.
