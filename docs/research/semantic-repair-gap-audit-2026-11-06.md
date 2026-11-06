# Semantic repair gap — independent research audit (2026-11-06)

**Status:** source-level research only; **no original performance result**, no new model run, no new Kaggle submission, no training/LoRA, no changes to `submission/`. Do not present a hypothesis here as a validated method or paper-level novelty.

## Research question

When a coding agent finds and edits a plausible file, **what prevents the edit from satisfying the required behavior**? Can repository evidence distinguish competing interpretations of an underspecified issue before patching, without making each task much slower?

**Avoid the wrong question:** “Which budget / prompt / tool configuration maximizes one Public leaderboard value?” The user has explicitly rejected the copy → submit → score loop as research.

## Source audit: three populations, not one causal experiment

| Evidence | Direct observation | Valid conclusion | Invalid jump |
|---|---|---|---|
| Own E4B development, Reliability-v1 | Previously inspected 17 tasks: **1/17 resolved; 13/17 non-empty patches; 16/17 with any mutation**, mean duration ~89 s; no task hit 5-minute or 32-tool limit. Fourteen of 17 lacked classifier-recognized targeted tests; no recognized pre-edit targeted witness | Cheap edits and shorter sessions did **not** deliver correctness on those E4B tasks | “Verification is THE cause of 31B hidden failures”; “more time solves E4B” |
| Own official, different bundles | 31B same old Reliability policy `57983156` **0.08** vs attributed external Budget-Fit 31B V2 `58019162` **0.17** | A *whole* public V2 reference package got a higher displayed score when reproduced on our account | Attributing +0.09 to V2 prompt, 8 minutes, graph tool, or any single mechanism; calling the reference our innovation |
| Independent Budget-Fit author's deeper logs | On exposed diagnostic cases, **52 of 69 verification-failed attempts edited a file also edited by the reference fix**; in eight *selected* cases, six lacked some grader-required details in the issue statement; a pinned pre-edit check completed only **1 of 8** opportunities. Identical package once scored **0.10 vs 0.15 in the same observed host epoch** | A file-overlap failure can persist even when broad localization succeeds; task specification and the execution/evaluator are serious confounders | “52/69 knew the exact faulty symbol”; extrapolating eight selected cases to all tasks; treating 0.17 alone as strong causal evidence |

**Own provenance:** `docs/research/why-reliability-v1-only-003-2026-11-04.md`, `docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md`, `docs/evaluation/trace-test-evidence-v0-2026-11-05.json`; official Kaggle receipt recorded in `NOW.md`.

**Independent external source:** Pilkwang Kim, [*Measuring an Agent While Its Evaluator Moved*](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/) (Oct 23–24, 2026), especially sections 7, 9–10. Its 69 failed attempts, 8 selected cases and our 17 E4B tasks are different, non-exchangeable samples.

### What the source actually shows about V2 vs our 31B

| Dimension | Own frozen old-policy 31B | External exact V2 |
|---|---|---|
| Base | Same 31B | Same 31B |
| Agent topology | One LlmAgent | One LlmAgent |
| Prompt | Advice to localize, maintain root-cause hypothesis, narrow edit, verify, and refuse known failure | More explicit issue API/edge-case contract; localize within ~6 calls; force first edit by calls 10–12; bounded check/repair and submit |
| Tools | Eight; no `write_file` | Nine, adds `write_file` |
| Max output | 16,384 | 8,192 |
| Time / calls / turns | 5 min / 32 / 64 | 8 min / 28 / 80 |
| Test command timeout | 300 sec | 240 sec |

Source: repository `submission/{agent.yaml,prompts/coder.md,configs/sampling.yaml,eval_config.yaml}`; V2 exact SHA-pinned ZIP verified in [Actions 42161771179](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42161771179), upstream [lynnsakurai v2](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue). Note: V2 lists `get_code_subgraph` but *instructs not to use it*; having a tool in YAML is not evidence it was executed.

**Interpretation:** V2 makes the agent *act* earlier and caps unproductive exploration, but it also risks making a speculative edit before recovering missing requirements. This is a tradeoff hypothesis, **not a diagnosis of its hidden task results**. Our E4B single-run traces do not establish V2's task-level behavior.

## Literature-based rejection of false originality

| Tempting idea | Existing work | Verdict |
|---|---|---|
| More agents / generic stage decomposition | [Agentless](https://arxiv.org/abs/2407.01489), [SWE-agent](https://proceedings.nips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html) | Not justified by this competition evidence; more topology is not itself innovation |
| “Use code graphs for localization” | [LocAgent (ACL 2025)](https://aclanthology.org/2025.acl-long.426/) | Prior art; graph tool benefit here remains unmeasured |
| “Generate a failing check before editing” | [Otter (ICML 2025)](https://proceedings.mlr.press/v267/ahmed25b.html), [ReProAgent (2026)](https://arxiv.org/abs/2607.09123) | Prior art; third-party V2 follow-the-prompt rate 1/8 also warns against another long instruction |
| “Find related tests using the dependency graph” | [TestPrune](https://arxiv.org/abs/2510.18270), [TDAD (2026)](https://arxiv.org/abs/2603.17973) | Already studied. TDAD explicitly found plain TDD prompting worse on its setup; cannot claim graph-guided test selection is new |
| Keep tuning minute caps / tool caps against hosted Public score | Exact V2 hosted variance and own non-transfering E4B efficiency improvements | Weak research; reject the score-chasing lane |

No exhaustive systematic novelty search was performed; these works **disprove novelty claims for the broad methods**, not every conceivable narrower method.

## The research lead: *recoverability of missing behavioral constraints*

**Three distinct cases, not one “verification failure” bucket:**

- **A. Explicit:** issue contains the expected API/input/output/edge case; the agent overlooks it. Remedy may be better extraction/execution.
- **B. Repository-recoverable:** issue is underspecified, but callers, sibling implementations, existing tests, signatures, or defaults reveal a missing invariant. Here a *discriminating observation* could distinguish two plausible fixes.
- **C. Unrecoverable:** neither the issue nor available repository state defines the hidden requirement; extra tools cannot logically infer an arbitrary oracle. Do not label this a reasoning failure or promise a fix.

**Provisional original hypothesis, NOT a demonstrated innovation:**

> For subset B **after the relevant code is localized**, a *contrastive contract check*—explicitly state two competing interpretations of the behavior, retrieve ONE independent caller/test/sibling observation that favors one, and only then choose the edit—may reduce semantically wrong patches more efficiently than blanket test-first or graph-always rules.

This targets **interpretation discrimination**, not file localization or merely the number of tests. The intervention should be conditional: trigger only when the issue admits materially different behaviors and an accessible repository witness can resolve the ambiguity; otherwise follow the simpler single-root baseline. An unsupported “witness” must never be treated as a true hidden specification.

**Mechanism, if supported:** independent repository behavior contradicts one proposed semantics, so an incorrect edit is rejected *before* costly patch/test cycles. It would also predict fewer wrong edits *among tasks that already touched correct source files*, rather than a universal boost from more tooling.

**Strong counterarguments:**

1. This may be a recombination of known requirement inference, test generation, and decision-theoretic debugging—not a publishably new method; originality is **UNKNOWN**.
2. Callers and tests may encode legacy behavior that the issue explicitly seeks to change; treating them as authoritative can block legitimate features.
3. Multi-interpretation reasoning adds latency and may reduce completion under the global 12-hour limit.
4. In group C, no repository witness exists; forced checks become hallucinated tests.
5. Hidden 31B traces are unavailable. The most concrete observations come from *other* E4B dev or the external author's exposed issue populations.

### Evidence that would change this research decision

**First, audit only already-inspected development examples (no new model inference):** distinguish A/B/C and label (i) whether the first edited file overlaps the reference file, (ii) the two plausible interpretations if any, (iii) exactly what *pre-edit, model-accessible* code/test evidence discriminated them, (iv) whether it was actually available before the edit, and (v) whether prior tool output already contained it. Reference patches, if used, are **audit labels only**; do not give them to an agent. Where an invariant is not observable, mark UNKNOWN rather than invent it. This is a **research audit** of existing evidence, not a new benchmark or selection of new tasks.

**Go/pivot:** Only if several independently reviewed examples belong to B *with real discriminating evidence* should there be a candidate intervention; otherwise reject this line and re-evaluate patch synthesis capability, test oracle limits and model adaptation on disjoint evidence. In future, compare **correctness on code-localized tasks, requirement-coverage violations, extra wall-time, and global completion**, not “number of tests” or raw patch size. Even a positive result would be development-only until an untouched independent check.

**Execution boundary:** no Kaggle Submit, no GPU/TPU, no model inference, no tuning to ref `58045795`, no replacing `submission/`, no private raw test/patch leakage, no new orchestrator, and no assumption that the paper track is justified. This is a defensible *question* to investigate, not a validated solution.
