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


---

## Completed case-level falsification audit — existing trajectories only (2026-11-06)

**Research decision: DOWNRANK “Contrastive Contract Checking” as a next implementation.** A prerequisite of the proposed mechanism was multiple concrete, **repository-recoverable (B)** examples with a pre-edit witness that would discriminate alternative requirements. This audit did **not** substantiate that prerequisite. It found clear counterexamples of *explicit-but-incorrectly-implemented* (A) and *underspecified or externally-linked-only* (C-risk) tasks. This is a **negative/insufficient-evidence audit, not an experiment showing the method fails**.

### Exact provenance and method

- Downloaded and inspected the **already existing** GitHub Actions artifact **`13150931817`** from [topology single-root run `41458804862`](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41458804862): 17 E4B development task traces, including `steps[].source=user`, ordered tools, and edits. This is the **topology** arm, **not** the Reliability-v1 trace arm and **not** a scored 31B private task run.
- Cross-referenced the PR/issue IDs (these task IDs map to original public GitHub PRs) and **original reference PR source diffs** for the inspected cases. Reference patches were viewed **only by the auditor after the agent run**, not passed to an agent or used to regenerate scored patches.
- Reviewed the original 17 problem statements for whether task semantics were directly given or deferred to external links. Used the stored tool interactions to challenge, not simply repeat, the agent's stated root-cause explanation. Did **not** run model inference, sandbox tests, Github Actions workflows, official submissions, or touch held-out tasks.
- **Evidence limitation:** Original PR differences illustrate one accepted implementation, not necessarily a unique correct solution; a source-file overlap or gold-patch difference alone is neither a correctness oracle nor an independent proof of a missing requirement.

### Concrete cases (direct task text + trace + accepted source changes)

| Already-inspected task | Task info actually supplied to E4B | Observed trajectory | Reference PR and differentiated failure | Classification |
|---|---|---|---|---|
| `fastapi_14448` | Explicitly says wrapped/partial callables need correct async handling for **path operations AND dependencies**, including mixed wrappers | Agent edited **`fastapi/routing.py` only**, then broad test command errored on imports; unresolved | [FastAPI PR #14448](https://github.com/fastapi/fastapi/pull/14448) changes `fastapi/dependencies/models.py` and `dependencies/utils.py` for callable classifications and generator handling | **A: scope/localization / multi-entry-point completeness**, not recoverable missing semantics |
| `fastapi_14463` | Explicit problem of accumulating duplicate OpenAPI `anyOf` refs; includes MRE | Agent edited **`fastapi/openapi/utils.py`**, substituted `jsonable_encoder(...)` for shallow `.copy()`; attempted verification via wrong `get_openapi` import; unresolved | [FastAPI PR #14463](https://github.com/fastapi/fastapi/pull/14463) uses **`copy.deepcopy`** instead, preserving the nested object structure | **A: candidate-edit semantics / test selection**; precise reason its different patch failed is NOT isolated |
| `rich_3061` | Explicit desired behavior: expanded tabs should preserve/extend text styling spans | Agent found `rich/text.py` and replaced appended-space style with a search over spans; whole-suite test failure, submitted unresolved patch | [Rich PR #3061](https://github.com/Textualize/rich/pull/3061) extends **span boundaries**, tracks display-cell positions and updates related text behavior, not merely style label on appended text | **A: implementation-invariant complexity**; no missing task behavior established |
| `fastapi_14873` | Explicit reproducible startup/shutdown callback problem and constructor overwrite explanation | Repeated large reads and **three failed `edit_file` attempts**; `submit_patch` returned 0 bytes / 0 files; unresolved | [FastAPI PR #14873](https://github.com/fastapi/fastapi/pull/14873) addresses APIRouter initialization semantics | **A: navigation/edit-tool execution**, not evidence for competing requirement interpretation |
| `rich_3934` | Only **“empty live”** plus an external issue URL; no description of newline behavior supplied | Agent repeatedly changed **`rich/live.py::get_renderable()`**, observed repeated failing tests and submitted unresolved | [Rich issue #3796](https://github.com/Textualize/rich/issues/3796) says **spurious newline** when exiting empty `Live`; [PR #3934](https://github.com/Textualize/rich/pull/3934) changes `Live.stop` and `LiveRender` rendered-height tracking | **C-risk: missing external requirement**. Not proof no repository clue could exist |
| `rich_4079` | Only **“Inline table code”** plus external issue URL | Agent investigated `rich/table.py`, added `Table.__str__`; recorded `SyntaxError` in tests; unresolved | [Issue #4038](https://github.com/Textualize/rich/issues/4038) actually concerns Markdown table **inline code syntax-highlight spans**; [PR #4079](https://github.com/Textualize/rich/pull/4079) changes **`rich/markdown.py::TableDataElement.on_text`** | **C-risk: crucial issue facts absent from task text**; source guess went to wrong subsystem |
| `rich_3105` | Only **“Fix #3104”**, generic PR checklist and URL; no symptom or reproduction | Agent searched unrelated `Style`, syntax and Markdown code/tests, no clearly grounded patch; unresolved | [Issue #3104](https://github.com/Textualize/rich/issues/3104) concerns HTML export `<code>` **`font-family: inherit`**, [PR #3105](https://github.com/Textualize/rich/pull/3105) changes `rich/_export_format.py` | **C-risk: missing issue content / offline URL** |
| `rich_3942` | “Update to markdown styles”; no exact behavior/desired style mapping | Agent edited **`tools/README.md`** strikethrough prose, unrelated to renderer; unresolved | [Rich PR #3942](https://github.com/Textualize/rich/pull/3942) changes **`rich/default_styles.py` and `rich/markdown.py`**, among other files | **C-risk: desired change not identifiable from title** |
| `fastapi_15280` | Only “Add support for `@app.vibe()`”; no signature or contract | Agent invented a method in `fastapi/applications.py`, failed broad verification and submitted; unresolved | [FastAPI PR #15280](https://github.com/fastapi/fastapi/pull/15280) specifies substantial decorator signature, provider prompt behavior, examples and docs | **C-risk: open-ended feature semantics unspecified** |
| `fastapi_9425` | Explicit: annotation exactly `"None"` permits HTTP 204 bodiless responses | Agent made a small change in `dependencies/utils.py`; **resolved = true** in frozen task result | [FastAPI PR #9425](https://github.com/fastapi/fastapi/pull/9425) handles `type(None)` after forward-ref evaluation; different implementation from agent's patch | **Positive control:** a valid fix need not textually match reference |

These are **post-hoc mechanism diagnoses, not blinded sample prevalence estimates**. In the *17 issue statements*, at least five (`fastapi_15280`, `rich_3105`, `rich_3934`, `rich_3942`, `rich_4079`) lacked the material behavioral details eventually found in their corresponding external PR/issue. We did **not** prove that the remaining task-specific repository state lacked recoverable evidence, nor establish a complete A/B/C ground-truth classification for all 17.

### Research inference and falsifiers

1. **Immediate negative result for prior B hypothesis:** These cases do not establish even a small *verified* group of B tasks in which (i) two materially different requirements were plausible, (ii) an already-available repository-only caller/test/sibling witness distinguished them, and (iii) acting on that witness could have prevented the observed wrong patch. Therefore the earlier “contrastive contract checker” is **NOT READY** for design, model run, submission, or a novelty claim. This is insufficient-support, not an empirical failure.
2. **Failure classes are heterogeneous:** A includes explicit multi-entry-point omission, patch semantics and tool/editor inability. C-risk includes missing *external issue information*. Those need different interventions: verifying an explicit requirement or editing accurately cannot logically retrieve unknown issue details from a forbidden external URL.
3. **Benchmark information restriction is part of the problem:** In the offline environment, a PR statement that only references a GitHub issue loses high-value symptom/reproduction detail. A future study must separate **task specification sufficiency** from **agent coding ability**, or it will incorrectly attribute data scarcity to reasoning.
4. **Gold edit mismatch is not itself failure:** `fastapi_9425` succeeded with a patch different from its upstream PR. Always use resolved outcomes, and in manual audits use the reference patch only as a possible explanatory contrast.
5. **Remaining original-capability lead (unproven):** For *explicitly specified* tasks, measure **requirements-to-code-surface completeness** (e.g., `fastapi_14448` endpoint vs dependency) and implementation invariant fidelity (e.g., `rich_3061` span positions). This is narrower and better evidenced than contrastive missing-contract inference, but may overlap existing program repair / test-based synthesis literature. No novelty or superiority claim is warranted.

**Next decision:** Do **not** implement Contrastive Contract Checking. If future genuine B cases with independent repository witnesses are found without post-hoc selection, reopen it. Otherwise prioritize independent evaluation of (1) specification completeness and offline-context access, (2) multi-entry-point patch coverage, and (3) semantic edit accuracy, with separate outcomes—not another “verify more” prompt. Any scored improvement would need held-out evidence and an actual mechanism study; user has not authorized another submission.

**Audit execution receipt:** read-only inspection of existing GitHub artifact and public upstream PR/issue pages; no new Actions runs, no Kaggle kernels/model inference, no score lookup, no `submission/` edits, no exposure of raw task traces or reference patches in the repository.
