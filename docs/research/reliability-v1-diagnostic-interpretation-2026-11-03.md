# Reliability-v1 diagnostic interpretation — 2026-11-03

## Decision supported

Use the already-completed Reliability-v1 development diagnostic to update the post-v1 research priority without rerunning the inspected 17-task denominator or changing the frozen submission candidate.

This is mechanism analysis, not promotion evidence. The 17 tasks are development-only and their traces have already shaped the project.

## Verified aggregate evidence

Source run: `deploy-reliability-v1.yml` run `41485671952`, diagnostic job `125417231948`.

- requested/completed: **17 / 17**
- resolved: **1 / 17** (`fastapi_9425`)
- non-empty patches: **13 / 17**
- empty patches: **4 / 17**
- mean tool calls: **10.41**
- median tool calls: **10**
- mean duration: **89.21 s**
- median duration: **85.61 s**
- call-cap exhaustions: **0**
- non-empty unresolved patches with non-zero verification exit: **12 / 12**
- verification exits across all tasks: `0: 1`, `1: 14`, `2: 1`, `-1: 1`

The pre-registered development prediction expected 1–3 resolved tasks, so the observed result is at the lower bound. The real Reliability-v1 Kaggle submission remains pending at the time of this note and is not used here to select a candidate.

## What this evidence weakens

### Pure compute-efficiency as the first bottleneck

The run did not hit the 32-call cap, median tool use was 10 calls, and median runtime was under 90 seconds. One task reached 30 calls, but the aggregate is not dominated by budget exhaustion.

**Inference:** reducing calls further may still help the global 12-hour objective, but the current diagnostic does not support treating call reduction itself as the highest-priority repair-quality intervention.

This weakens the previous ranking of H1 Adaptive Compute when H1 is interpreted mainly as `use fewer calls`.

## What this evidence strengthens

### Evidence quality before and after editing

The strongest aggregate pattern is that the agent frequently produced a patch but still failed directly relevant verification: 12 non-empty unresolved patches, all with non-zero verification exits.

This is consistent with several mechanisms that the compact aggregate cannot distinguish by itself:

1. **F2 UNDERSTAND:** the agent reaches plausible code but its root-cause hypothesis is wrong.
2. **F3 EDIT:** the hypothesis is substantially right but the patch is incomplete or semantically wrong.
3. **F5 REPAIR:** verification exposes a useful failure, but the bounded second attempt does not converge.

The aggregate does **not** prove which of F2/F3/F5 dominates. It does show that an intervention aimed only at F8 BUDGET is poorly matched to the observed surface.

## Updated breakthrough ranking

### Provisional H1 — evidence-first repair for concrete behavioral contracts

This is the narrow version of the earlier reproduction-first idea.

**Mechanism:** before editing, when the issue exposes a concrete input/output, exception, state transition, or regression condition, construct or identify the smallest executable assertion that reproduces the required behavior. Use the same evidence after editing.

This changes the information available to root-cause reasoning rather than merely adding more reasoning tokens.

**Why it could break the bottleneck:** the current agent often discovers that its patch is wrong only after editing. A pre-edit behavioral witness can constrain both localization and semantics before code mutation, potentially reducing F2/F3 and giving F5 a higher-information repair signal.

**Resource guard:** conditional only. Do not generate a reproduction when the task does not expose a cheap concrete behavioral contract. The intervention must replace wandering, not become another mandatory sub-agent stage.

**Falsifier:** on a new untouched denominator, the policy does not reduce the rate of non-empty patches ending with failing directly relevant verification, or the added reproduction cost lowers resolved-per-budget without compensating accuracy.

### Provisional H2 — test-aware retrieval

**Mechanism:** when localizing a likely source symbol, retrieve the smallest existing test/executable path that exercises the same behavior, so localization and verification are connected before editing.

**Why it could help:** it may deliver similar evidence benefits to reproduction-first at lower generation risk when a relevant test already exists.

**Falsifier:** retrieved tests are usually irrelevant/broad, or source localization improves without changing patch correctness.

### H3 — adaptive compute / value-of-information routing

Retain this as an efficiency mechanism, but demote it as the immediate repair-quality hypothesis unless future evidence shows budget pressure on the hidden distribution.

A stronger formulation is not `always use fewer calls`; it is `spend the next call on the action with the highest expected discrimination between current hypotheses`.

### H4 — conditional edit/tool-schema reliability

Keep conditional. The current aggregate does not establish parser/edit-tool failure as the dominant source of the 12 failing patched tasks.

### H5 — conditional bounded rescue

Keep deferred. Adding a rescue stage before proving a specific missing capability would mix topology cost with uncertain repair benefit.

## Anti-overfit boundary

Do not tune new prompt rules to the 17 known task IDs, repository names, individual traces, or reference patches.

The development diagnostic may update the **hypothesis ranking**, but it may not promote a candidate. Before implementing the next major variable:

1. wait for the already-submitted frozen Reliability-v1 Kaggle feedback;
2. explain prediction error rather than target the score;
3. freeze a new untouched denominator;
4. pre-register one mechanism, one targeted failure surface, and one falsifier;
5. keep model/sampling/tool surface fixed unless they are the variable under test.

## Cheapest next action

No additional Kaggle GPU run is justified yet. The Reliability-v1 submission ref `57921371` is already pending. Use a cheap read-only submission-status probe only when current feedback is needed. Do not rerun the 17-task diagnostic.
