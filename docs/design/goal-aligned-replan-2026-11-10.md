# Gemma 4 Developer Agent — Goal-aligned Research & Delivery Reset

Date: 2026-11-10. Authority: the user's explicit objective, current repo instructions, measured Kaggle results, and the official competition contract. This document **replans** the project; it does not itself prove, implement, or submit a new solver.

## North star

> Build a genuinely stronger, reproducible **offline Gemma 4 software-engineering agent** that fixes more previously unseen repository issues **within the competition's total inference/sandbox budget**; explain the causal mechanism with defensible research evidence, implement it in an official-compatible agent, and verify through real Kaggle submissions.

The user values **both** a competitive official Kaggle outcome and transferable Applied AI / SWE Agent / LLM Systems engineering experience. Kaggle is the externally scored **validation target**, not the algorithm for choosing what to build. An optional paper track is not a present deliverable; produce one only if real research earns it. Do not spend the November 12 paper deadline on an unsupported writeup. Main submission deadline is December 2, 2026 (official Kaggle schedule, subject to updates).

### Exact deliverables, in order of importance

1. A **correctness-improving agent**: materialized nonempty patches are not enough; a larger proportion of independent issues must pass their validation suites at bounded total compute.
2. A reproducible, legal **`submission.zip`** with `agent.yaml` at its root, exact model/config/tool/adapter provenance, official ADK compilation and authentic Kaggle submission receipt.
3. A small scientific explanation: what failure mode changed, how the change works, matched baseline, independent confirming evidence, regressions, and when it should **not** work.
4. A credible reusable research/engineering artifact; **not** 100 more CI workflows, a wall of audits, or an unproven "paper."

### Non-goals / operating constraints

- No Copy → Submit → Score → Copy loop; don't retune to Public LB or previously inspected issues.
- No repeated prompt patches, optional skills, new reviewers, graphs or RL because they *sound* stronger. These are competing mechanisms, not cumulative requirements.
- No spending user-managed GPU on speculative training; SFT/LoRA/RL is **open as a hypothesis**, not authorized execution.
- No CPU pass, container build, patch byte count, tool-call count or "submitted" action as a substitute for issue-resolution evidence.
- No publication of raw Kaggle Competition Data, hidden tests, gold/reference patches or private traces to this public repo. Hydrate model/task data at runtime as required by `PUBLIC_VISIBILITY.md`.
- Use GitHub Actions for reliable **orchestration**, not as a proxy for model research; no duplicated long-running GPU pilots while a private kernel is QUEUED.
- Do not mutate old scored ZIPs, reference controls, task exclusions, or historically frozen experiments.

## Understand the actual two-layer system

```
Agent quality path (what matters):
Competition issue + source code + permitted graph/embedding evidence
    -> Gemma 4 policy + official ADK tools
    -> source understanding / behavior hypothesis
    -> actual workspace edit -> targeted evidence / repair
    -> FINAL workspace diff -> submit_patch
    -> hidden test PASS or FAIL [primary metric]

Experiment/operations path (a means, not the goal):
GitHub source + pinned artifact + preregistered cohort
    -> CPU ADK compiler & safety / budget checks
    -> private Kaggle matched issue evaluation [when capacity exists]
    -> independent correctness decision
    -> one official Kaggle code submission [if justified]
    -> authenticated score and failure report -> next hypothesis
```

Official scoring: issue-level binary validation. There is a **12-hour total** run allowance including setup and tool execution, not 12 hours per task. Current Kaggle Staff supports 31B/12B/E4B/E2B QAT; different Gemma 4 model variants may **not** be mixed inside one submission. The original overview text may lag behind Staff announcements. Official tools are closed to the harness's predefined native tools or declared `agent_tool`; Skill scripts must be actually invoked in the sandbox. Never implement a fictional custom ToolRegistry API.

## What's actually built (verified versus unknown)

| Asset / evidence | Verified outcome | What it does not show |
| --- | --- | --- |
| `submission/` E4B baseline / Reliability | 0.03 Public for two scored variants; useful trace instruments | Not the actual strongest scored 31B candidate |
| Original 31B policy | 0.08 Public | Not an established 31B capacity ceiling |
| External Apache-2.0 Budget-Fit V2 exact reproduction | **0.17** Public on our account; currently strongest **scored** reference | Not our invention or causal proof of its tool/prompt policy |
| Recovery Reviewer v0 | 0.13 Public | No benefit of that *specific* optional reviewer; not a rejection of all multi-agent designs |
| Contract & Impact matched private pilot | Same four 31B tasks: V2 **0/4**, treatment **0/4**; candidate made 3 nonempty patches versus 4 | Not proof that structured understanding can never help; Skill calls weren't authenticated as typed events |
| Official Toolcap60 | Authenticated submission **58164176** accepted, PENDING and blank Public score at last recorded check | Does not demonstrate stronger repair; 28→60 is a budget change |
| Private 28-vs-60 pilot | Kernel QUEUED at last check; GitHub orchestration timed out | No valid task-quality inference |
| Candidate-history observer | CPU tests detect lost revisions in synthetic conditions | No observed current 31B case with a *passing* candidate later discarded |

The original public Budget-Fit author's matched small-sample 28→36 call-cap change **did not** improve resolution; their same ZIP also varied across hosted executions. These weaken a "just increase budget" global thesis. The project has approximately 100 Actions workflows, 48 scripts, 64 tests at its recent tree checkpoint; this reflects substantial measurement/plumbing work, not 100 interventions that improve the solver.

**Documentation drift:** `README.md` calls the repository private, but the actual repository is PUBLIC. It calls `submission/` the sole canonical candidate, but recent scored 31B artifacts were built from pinned external source through scripts. This distinction must be made explicit; historical mirrors are not approved as a new workflow.

## Failure-mechanism decision: **do not blindly implement checkpoint-first V3**

The observable goal gap is **patch semantic correctness**. Our E4B 17-task diagnostic shows only 1/17 resolved, many nonempty patches, few recognized targeted tests, and 0 observed pre-edit targeted checks. An existing four-task 31B pilot produced nonempty V2 patches but 0 independent solves. The evidence does **not** yet prove semantic reasoning is the largest 31B failure *rate*; it does directly undermine the belief that "more edits/more calls/more reviewers" is sufficient.

Four competing method classes remain open:

| Candidate class | When to prioritize | Explicit falsifier |
| --- | --- | --- |
| **A. Evidence-grounded semantic repair** — leading *hypothesis*, NOT predetermined winner | Edited correct area but omitted issue constraints, other entry points, invariants, or recovery after meaningful test output | Relevant evidence is present and used yet candidate correctness does not improve, or extra analysis costs more useful tasks |
| **B. Checkpoint + branch/select** | Independently passing intermediate patches are repeatedly overwritten or final selection loses them | Actual private history contains no passing discarded candidate; selectors cannot differentiate candidates at matched compute |
| **C. Coder adaptation (clean SFT/LoRA/distillation; RL only if justified)** | Correct candidate generation stays poor even after evidence/feedback is available to the model | Clean held-out transfer absent or training/adapter costs prohibit deployment |
| **D. Specialist multi-agent** | Specialized agent contributes *distinct extra evidence* that single-root Coder cannot obtain equally cheaply | No typed invocation, redundant reasoning, or fewer resolved issues per global runtime |

**Recommendation:** first evaluate **A vs C's underlying diagnosis**, preserving B and D as conditional alternatives. Current checkpoint-first `experiments/solver-v3/README.md` is **a proposal and must not be treated as the mandated implementation plan**. A checkpoint is a safety/measurement tool until *real* passing-candidate loss supports branch search.

## Next execution plan — one research loop, not an audit factory

### Phase 1: Freeze control and decide the bottleneck (single bounded diagnostic)

Inputs: byte-pinned externally attributed V2 31B ZIP, already captured 31B task result metrics and any safely accessible existing private trajectories, the established E4B 17-task traces, and historical failure taxonomy. Do not start a new GPU evaluation to re-observe the same tasks. For the 31B pilot, inspect only available task/source evidence; when trace semantics are unavailable, label mechanism **unknown**.

**Deliverable:** one concise `F1–F9` mechanism table across already-exposed tasks showing count/evidence for: wrong localization, wrong interpretation, incomplete edits, failed test/repair, tool/submit failure, and **observed** passing-patch loss (if any). Two competing explanations, with confidence and one disjoint falsifier each. No six-stage reviewer pipeline or retrospective prompt selection.

**Stop rule:** one diagnostic pass. If generation/semantic failure cannot be distinguished from selection using existing evidence, proceed with an architecture that provides an observable discriminating comparison rather than running another audit of the same material.

### Phase 2: Build ONE meaningful candidate, not five fixes

**Provisional build:** `Solver V3-A — Semantic Repair with Grounded Feedback` on 31B, one writer. The method must **change actual tool-use behavior or state**, not merely append an instruction to V2:

- Evidence: when ambiguity materially affects the edit, gather a *specific* caller, test, sibling implementation, or API invariant before deciding between competing implementations. If the task specification does not establish a requirement, record UNKNOWN instead of inventing the hidden oracle.
- Synthesis: make a materialized patch that covers the stated behavior across relevant entry points; do not force a large up-front planning stage on easy tasks.
- Feedback: execute one discriminating targeted check and use its *actual failure* to decide a bounded repair. Reserve final diff/submit budget. Avoid generic "test-first" ritual and broad suites without payoff.
- Mechanism: any proposed deterministic helper must use **actually supported ADK tools/skills**, with a recorded real tool-call/result event in a synthetic sandbox. A prompt that says "always invoke" does NOT enforce execution.
- Keep snapshot/restore as a minimal optional invariant, not the main algorithm unless actual passing candidate loss was measured.

**Deliverable:** a reproducible candidate builder in an isolated `experiments/solver-v3/` lane, official ADK-compatible `submission.zip`, a targeted CPU tool-contract test proving the *mechanism executes* in synthetic cases, and a small source-diff review. Do not replace `submission/` or claim performance based on CPU tests.

**Pivot:** if the necessary controlled action interface cannot run under the official tool registry, drop this form rather than producing another decorative Skill. Test a genuinely different Coder policy/adapter feasibility path next, without automatically training it.

### Phase 3: Disjoint, matched-budget correctness evaluation

- Use original V2 as comparator, identical model/visible task input, and a **matched total compute ceiling**. For a substantial redesign, compare the whole new architecture first; ablate only components that explain a measured win/loss. Don't insist on dozens of budget micro-tweaks.
- Select a previously uninspected, source-/repository-aware development pilot and a separately reserved confirmation set *before* opening candidate outcomes. Do not recycle the exposed 17 E4B or Contract & Impact four tasks as a blind claim.
- Primary measure: **`resolved / issues attempted`** under the 12-hour global-budget projection including failures, empty patches, timeouts and setup. Report paired rescues/regressions, and per-repository slices. Secondary: corrected semantic requirements, tested repairs, tool calls, wall-time and actual submit state. Do not equate small-sample directional gains with statistical certainty.
- Prefer authenticated Kaggle private scorer when runnable; if private 31B is queued, **do not** restart duplicate runs. Use CPU fixture validation, static checks and source-level implementation meanwhile. The official Kaggle scoreboard is an external final confirmation, not a free hyperparameter sweep.

**Gate:** promote only on authentic correctly resolved issues with a defensible direction across disjoint cases and acceptable total runtime. CPU validation is an *eligibility check* only.

### Phase 4: One official submission and a real decision

- Run official compilation, one privately built/verifiable ZIP, SHA pin, quota/status check and one idempotent submission.
- Compare authenticated score with exact prior 0.17 scored control; disclose that a single Public value can vary with host/seed. Record failure honestly, not "closer to success."
- If A fails, **do not** keep rephrasing prompts. Use the observed failure to choose B if there was real candidate loss, C if correct generation is absent, D if complementary information transfer is demonstrated; otherwise a new evidence-backed direction.
- No paper-track diversion, no more Toolcap60 retries, and no repeating a rejected intervention on the same tasks.

## Repo operating model after reset

- `README.md`: one truthful entry point explaining the *goal* and current scored/artifact distinction.
- `AGENTS.md` + `RESEARCH_DOCTRINE.md`: stable scientific and execution constraints.
- `NOW.md`: brief **current** status and next executable deliverable at top. Preserve older history until a safe non-destructive archive cleanup; do not endlessly prepend duplicate progress prose.
- `docs/evaluation/`: evidence, frozen cohorts, measured outcomes and negative results.
- `experiments/solver-v3/`: **the sole active candidate lane**, while old experiments remain historical, not competing default workflows.
- `submission/`: canonical source package **only after** explicit promotion; clarify that current E4B tree is a historical diagnostic baseline and past 31B submissions were generated externally.
- `.github/workflows/`: CI/execution infrastructure, **not** research success. Do not launch more analysis-only Actions or private GPU jobs without a named decision they can change.
- Merge research branch to default only after verification; do not destroy or force-push old branches or historical artifacts.

## Research checkpoint (required by RESEARCH_DOCTRINE.md)

- **CURRENT BEST:** authenticated Public 0.17, attributed external V2; Toolcap60 58164176 PENDING at last check.
- **REAL EVIDENCE OF STRENGTH:** official 0.17 result and independently scored 31B control trace; original improvements not established.
- **MAIN FAILURE MODE:** unresolved semantic patch quality, with distinct possible generation, test-feedback, or selection causes; exact 31B distribution UNKNOWN.
- **CURRENT BOTTLENECK HYPOTHESIS:** correct localization/edit materialization does not reliably lead to correct behavioral repair; mere budget or extra roles unlikely to suffice.
- **LOCAL BUG OR MODEL-CLASS LIMIT?:** UNKNOWN; require actual disjoint behavior evidence.
- **EXCLUDED CLASSES:** none globally. Training/LoRA requires separate authorization, not an ideological ban.
- **SMALLEST DISCRIMINATING EXPERIMENT:** matched 31B control vs one concrete *executed* semantic-feedback mechanism on a frozen disjoint cohort; report independently resolved tasks and overhead.
- **ARCHITECTURE PIVOT:** no correct candidates despite adequate evidence -> C; observed passing candidates lost -> B; useful independent specialist evidence -> D; no transfer/too much overhead -> reject that candidate.

**Implementation not yet executed:** this plan changes research priority and repo documentation only. It does not assert a working Solver V3 or a new Kaggle result.
