# NOW — Bottleneck reassessment (2026-11-07 MYT)

**Priority revision.** The leading hypothesis is failure to turn available code/feedback into a correct, changed repair. Navigation efficiency remains a competing hypothesis. External 31B thinking-off records improved edit feedback and reduced repeats while staying at 14/33; a recovery-instruction screen showed little compliance and 7/33 versus baseline 9/33. These populations do not identify our thinking-on 31B hidden failure distribution. [Evidence, scope and updated decision](docs/research/flexon-budget-policy-review-2026-11-07.md#bottleneck-reassessment-after-the-comparator-review).

**Next measurement.** In the existing same-budget continuation/retry comparison, independently record whether a correct candidate ever appeared, whether it survived into the final patch, and whether intended edits reached the source tree. This separates generation, selection and malformed execution instead of treating every failure as missing verification. Model execution and independent candidate grading remain unexecuted. No new feature, training, inference, submission or frozen-candidate change was performed.

---

# NOW — Flexon public V10 comparator review (2026-11-07 MYT)

**Research finding.** Retrieved and CPU-rebuilt `flexonafft/gemma-4-budget-aware-coding-agent-v2`, explicitly pinned to Kaggle V10. The 3,713-byte local ZIP exactly matched its official output: SHA-256 `6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`. Official compilation passed with an inference stub. Its agent, sampling and evaluation files are byte-identical to our 0.17 V2 control; only the root prompt differs. The public indexed page records 0.22 V10, which we have not independently reproduced or attributed to an individual behavior.

**Decision.** Retain this as an external policy comparator and execution-efficiency hypothesis. Early editing and failed-match recovery are already in our V2. More explicit search/read batching and a total graph-tool ban are differences; their effect on 31B decisions remains unexecuted. No automatic scheduler or executable recovery controller is implemented in the external package. [Source identity, exact comparison, CPU checks, uncertainty and falsifier](docs/research/flexon-budget-policy-review-2026-11-07.md).

**Effect on current work.** Keep the paired-check prototype and its matched control unchanged. Additional script/discovery/dual-execution cost must earn independent patch-quality gains; it has not yet done so. Our verified own best remains 0.17. This review performed no model inference, training, new submission or frozen-candidate change.

---

# NOW — Executable paired-check candidate (2026-11-07 MYT)

**Decision.** Continue with an agent-callable source comparison action, built on the exact attributed 31B Budget-Fit V2. The agent selects its Python check and decides its next action. The Skill script returns that check on original/current source; a matched control returns current/current. The original model, root prompt, sampling, 8-minute allowance, 28-call configuration and 80 turns are unchanged. ADK adds Skill discovery and script tools in both arms.

**Verified CPU result.** Twenty tests passed, including the official compiler, skill activation and script-execution adapter, with inference configured to raise. The standalone notebook schema passed and fresh CPU executions generated deterministic ZIPs. Two previously inspected Flask/SymPy programs also returned the recorded source differences through the new runner. These checks establish execution and packaging, not agent selection or patch quality. [Mechanism, evidence, commands, limitations and falsifier](experiments/paired-check-v0/README.md) · [Exact hashes and CPU results](experiments/paired-check-v0/cpu-verification.json).

**Artifacts.** One CPU notebook, `gemma4-paired-check-skill-v0.ipynb`, selects either arm. Treatment ZIP SHA-256 `df88261b4aa2a9f1337fb0f3860fd197266fae7ac16c7f38ba89ef7bfcbad729`; matched-control ZIP `0570da416031931d9cc7363d0a111a7c52e30dab1032138c4c54e8147f17236a`. Neither has been submitted. Canonical `submission/` and the frozen candidate are unchanged.

**Frozen submission update.** The original scheduled workflow succeeded and submitted the unchanged base-evidence ZIP, official ref **58081411**. Its authenticated receipt at 05:58:06 UTC / 13:58 MYT recorded PENDING and no score. [Exact receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42344893898/job/128320398058). The authenticated read-only check at 07:33:24 UTC / 15:33 MYT still returned **PENDING**, with empty Public and Private scores. [Latest status](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42351756224/job/128341200017). The check did not submit or run inference.

**Still unexecuted.** 31B action uptake, selection quality, next-action effects and independent patch correctness. A causal comparison must start at the same selected-check checkpoint and preserve the remaining budget, with tasks locked before inference and missing checks retained. A notebook screen is weaker end-to-end outcome evidence. If useful observations fail to improve correctness at matched cost, retire this mechanism rather than tune on the 19 inspected external traces. No training, new model inference or submission of this candidate was performed.

---

# NOW — Paired execution feedback CPU experiment (2026-11-07 MYT)

**Decision.** Advance the narrower agent decision experiment. Show the base observation when the agent's own check reaches the relevant behavior and its trajectory lacks an equivalent base observation. This replay establishes when useful feedback is available. A matched 31B continuation is still required to measure its effect on decisions and independently correct patches.

**Protocol and evidence.** Locked 19 archived GPT-5 mini / mini-swe-agent SWE-bench Verified tasks before opening the trajectories. In each of Flask, Requests, pytest and SymPy, took up to six task IDs ordered by SHA-256 of `gemma4-decision-cpu-v0:` followed by the task ID. None overlapped the local Kaggle development task index. No replacements. Used the first eligible recorded agent command after its last relevant source write and the terminal patch printed from `patch.txt`. The archive's submission field was empty, so the displayed patch was recovered from its tool reply and checked against the before and after Git blob IDs. Each command ran twice on base and twice on the edited tree in a local CPU sandbox. Older checkouts received a compatibility replay with the same command and dependencies on both sides. The reference patch was excluded from probe selection and replay. [Pinned trajectories](https://huggingface.co/datasets/tarsur385/swebench-verified-trajectories/tree/773748a7c1222e8a642a7059821498e14293562a/swebench_verified_raw/gpt-5-mini) · [Pinned task data](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/blob/78f471b/data/test-00000-of-00001.parquet)

| CPU result | Count of 19 | Issue IDs |
| --- | ---: | --- |
| Repeatable issue-relevant output change | 12 | Flask 5014. Requests 1142, 2931, 5414. pytest 5262, 7571, 10051. SymPy 11618, 24213, 24443, 24562, 24661. |
| No observable change from the recorded command | 4 | Requests 1724, 2317. pytest 8399. SymPy 17318. |
| Test blocked in setup | 1 | Requests 6028. The HTTP fixture was unavailable in the offline replay. |
| No eligible recorded post-edit check | 2 | pytest 6202, 7205. |

**What the feedback buys.** Eight of the 12 changed cases had identical exit codes on base and edit. Three of the 12 already had equivalent base observations in their original traces (Requests 5414 and SymPy 24443, 24562). The other nine would add a base observation relative to the recorded tool history under a compatible environment. Eleven changes moved the checked behavior toward the issue requirement, but three of those runs remained unresolved in the independent archive verdict (Requests 2931, pytest 10051, SymPy 24562). For example, the agent's Rational probe changed the requested value to 1/200, while the archived grader still recorded unresolved. The remaining change replaced an incorrect distance with an exception (SymPy 11618). Preserve behavior output and use independent grading to judge decisions.

**Next falsification.** Start both arms at the same 31B V2 checkpoint after the agent chooses a check. Use the same test command, model, prompt and time allowance. The control gets edited-tree results and the treatment gets base plus edited-tree results. Measure whether the model's next action and final independent correctness improve on cases locked before inference. Count the tasks where no useful difference can be returned. If previously unseen relevant feedback fails to improve correctness at the same cost, deprioritize this mechanism. The 12-of-19 CPU rate is descriptive of this external sample.

Protocol SHA-256 `f49e223e2009f14dcd3b4c9ec78f65b84e2ac53eb076c059548dd732061b5478`. Selected commands SHA-256 `c5bb7f771b0a6ecb7efb4a9a865628095c48fc962af19ed9624e389c413198e7`. This experiment used archived trajectories and CPU execution only.

---

# NOW — Agent decision research pivot (2026-11-07 MYT)

**Decision.** Archive the two-call assertion notebook as a CPU prototype. This supersedes the advancement decision below. The development cases showed that an auditor could construct two behavior checks. They supplied no independent evidence that the agent would choose a useful check or use its result to make a better decision.

**Research question.** Does giving the agent evidence of what its own edit changed improve its choice to keep, revise or revert the patch? The agent chooses the check and the next action. The proposed intervention changes the evidence returned by the sandbox. A matched control runs the same agent-chosen check twice on the edited tree. The treatment runs it once on the base tree and once on the edited tree. Match the checkpoint, model, prompt and total budget. Score on issues fixed in advance outside development and use independent correctness checks. Retain tasks without an eligible check in the denominator.

**Falsifier.** If informative paired observations occur but do not improve independent patch correctness at the same cost, set aside this feedback hypothesis and investigate edit generation and action selection. If informative observations are rare, the intervention has inadequate coverage. This is a research proposal. The frozen base-evidence retry retains its existing schedule.

---

# NOW — Two-call assertion selection audit (2026-11-07 MYT)

**Historical decision (superseded above).** Continue with one CPU packaging candidate for test selection. The existing conditional `base-evidence-retry-v0` schedule stays on its original plan. The 31B Budget-Fit V2 control `58019162` scored 0.17 Public at 8 minutes and the 5-minute variant `58045795` scored 0.15. [Frozen experiment state](https://github.com/kolihhan/gemma-4-kaggle/blob/fea90cd8233cbb49a713393e7071db091f9f8c7a/NOW.md#L1-L9)

**Evidence.** Locked four failures in the public faithful 31B development records before opening the issue text or reference. These runs had thinking off. A bounded search and one narrow read found a testable requirement on FastAPI #13713 and Rich #3278. After locking the assertions, the same CPU probes were run on the base and on independent reference-patched copies.

| Case | Result |
| --- | --- |
| FastAPI #13713 | The OpenAPI root field is absent on base and equals the supplied metadata on reference. The literal constructor spelling in the issue fails on both. The reference exposes `openapi_external_docs`. The predeclared root-only probe checks the output requirement and resolves the exposed slot by suffix. The historical run spent 37 calls paging the application file and recorded an empty patch. |
| Rich #3278 | Base retained all 16 tested private escape sequences. The reference removed all 16 and preserved surrounding text. The historical run repeated malformed edits 71 times and hit 80 turns. |
| FastAPI #15023 | Skip. The task lacks an expected change to a specific streaming example. The historical run made 35 searches and recorded an empty patch. Assertion unexecuted. |
| Rich #3942 | Skip. The task lacks target elements and expected styles. The historical record names 15 malformed edit repeats. Assertion unexecuted. |

[FastAPI development notes and call summaries](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-14-faithful-v54-AB/notes.md#L25-L30) · [Rich development notes and call summaries](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-21-faithful-bf-off-AB/notes.md#L24-L30) · [FastAPI base schema](https://github.com/fastapi/fastapi/blob/5c1f87c56387a96dbdddb2b1c4ec9ba48dcebc4e/fastapi/openapi/models.py#L423-L440) · [Rich base decoder](https://github.com/Textualize/rich/blob/4c5d305bb902ce97011666ada19e48d0b27b49e1/rich/ansi.py#L119-L165)

**CPU packaging.** `gemma4-budgetfit-v2-two-call-assertion.ipynb` generated identical `submission.zip` files in two local IPython executions. SHA-256 `fc828ec9253fc520f5f22e85943d73543be4154d6fb63761f2be3bc2b2e93e8d`. The source was lynnsakurai's Apache-2.0 V2 archive `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`. Reversing the one test-selection replacement restored the exact original prompt. The other three archive members matched byte for byte, including model, tools, sampling, 8 minutes, 28 calls and 80 turns.

**Scope of the result.** Two requirements were recoverable in an auditor's two-call replay. Historical summaries identify navigation and editing bottlenecks, with incomplete tool timelines. Model compliance, patch resolution, and transfer to the hidden set remain unmeasured. No training, model inference or submission was performed in the audit. An independent follow-up would hold budgets fixed and compare how often the agent picks a grounded, runnable check within two calls and whether it improves correct patches.

---

# NOW — Base evidence retry v0 (2026-11-06 MYT)

**Ready for one conditional Kaggle submission.** The private CPU notebook `gemma4-base-evidence-retry-v0-20261106` v1 produced the pinned ZIP `1944471ce98386371ebe52a0d3e6a9cc211ff81803684eeaff5f344532234c1b`. A local CPU build matched that hash. The workflow is active and is scheduled for November 7 at 08:13 MYT. It verifies the notebook ZIP, checks for a prior receipt, and requires both an available slot and no active Kaggle entry on the account before submitting. Ten offline cases passed, including a pending entry, zero quota, a changed ZIP, and a missing response. [CPU build](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42202422197) · [Scheduled workflow](https://github.com/kolihhan/gemma-4-kaggle/actions/workflows/scheduled-gemma4-retry-nov07.yml)

**Latest Kaggle status at 00:40 MYT on November 7.** The five-minute cap audit `58045795` is COMPLETE at **0.15 Public**. The exact eight-minute Budget-Fit V2 control `58019162` is COMPLETE at **0.17 Public**. The observed five-minute score is 0.02 lower in one run per cap. The earlier active entry has finished. The scheduled retry will check the new day's allowance at launch. [Authenticated status](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42171026894/job/128018297926)

**Comparison.** The archive diff against the pinned V2 verified identical 31B model, sampling configuration, and evaluation limits. The candidate adds a read-only diagnosis helper for a relevant failed assertion, adds the conditions for calling it, and rewords the root agent's role line. Treat one official score as a screen of the combined change. Measuring the effect of base-only evidence requires an equal-cost helper with a conventional evidence handoff.

**Next.** Verify the official receipt and compare the terminal Public score to `58019162`. If the scheduled run reports an unavailable slot or an unconfirmed receipt, inspect that outcome before any further submission.

---

# NOW — Independent Research Verdict (2026-11-06 MYT)

**Research priority.** Test whether a fresh attempt can reuse repository observations that still hold on a clean checkout. Use the reproduced 31B Budget-Fit V2 as the practical comparator. The hypothesis concerns the information carried across a retry. The dominant bottleneck on the hidden set remains UNKNOWN.

## A. What we know

| Official entry | Public score | Existing authenticated record |
| --- | --- | --- |
| E4B baseline / E4B Reliability-v1 | 0.03 / 0.03 | [Kaggle receipts](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688) |
| 31B, original Reliability-v1 policy | 0.08 | [Kaggle receipt and feedback check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42003198673) |
| 31B, exact attributed public Budget-Fit V2 | 0.17 | [Kaggle receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160680339) |
| V2 with the existing five-minute cap audit | PENDING at 13:53 MYT on Nov 6 | [Last recorded receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42171026894) |

- **FACT.** Reliability-v1 and the earlier single root each resolved 1/17 on the inspected E4B development set. Reliability-v1 was about 12% faster and produced about 20% smaller nonempty patches. The trace audit found five Reliability-v1 cases that submitted after a recognized nonzero test command without an intervening edit. The verifier LoRA was historically trained and the inspected development comparison went from 1/9 to 2/9, with two gains and one loss. Its matched blind effect is UNKNOWN. [E4B review](docs/research/why-reliability-v1-only-003-2026-11-04.md) · [Test-command audit](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41987818297) · [LoRA development run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41447650864)
- **FACT.** The independent public [Mobius study](https://mobius.style/2026/10/31/kaggle-gemma4-scaffold-capacity/) measured model-dependent scaffold effects under a repaired local scorer (E4B 10.0% to 15.4%, 12B 25.2% to 23.1%, 104 issues per cell). I reconciled all six published cell rates and re-tabulated the released outcomes after excluding documented project diagnostics, verifier training samples and named reservations. The stricter slice contained 22 issues across three repositories and 660 min/max task-runs. Per issue and scaffold, I averaged all 20 ordered pairs of distinct seeds. A rescue means the first seed failed and the second solved. [Pinned run records](https://github.com/mobius-style/gemma4-scaffold-capacity/blob/7356b06b0f5c8b5cc185a03b8ac2b4b68d210425/data/runs.jsonl)

| Local model and scaffold | One draw | Oracle, either of two full draws | Added solves within 360s combined recorded time |
| --- | ---: | ---: | ---: |
| 12B minimal | 17.3% | 22.7% | 0 of 24 rescue pairs |
| 12B maximal | 17.3% | 24.1% | 0 of 30 rescue pairs |
| E4B minimal / maximal | 8.2% / 10.0% | 13.2% / 12.3% | 22 of 22 / 10 of 10 rescue pairs |

- **INFERENCE.** Candidate diversity exists, and its cost depends on the model. The 12B results challenge using a full second run by default. A wider 42-issue sensitivity slice, before additional training and diagnostic exclusions, also had zero fitting 12B rescues out of 120 rescue pairs. These are dependent pair counts on public tasks. The stricter slice is FastAPI-heavy (17 FastAPI, 3 Rich, 2 Requests). The recorded durations are from the local harness and the oracle assumes perfect selection.
- **UNKNOWN.** The split between 31B generation, selection, runtime and task-specification failures. The scored API receipt exposed aggregate status and scores. The 0.08 to 0.17 contrast changes several variables together. An external team also recorded 0.10 and 0.15 from the same ZIP within one observed host epoch. [Bundle comparison](docs/research/semantic-repair-gap-audit-2026-11-06.md#what-the-source-actually-shows-about-v2-vs-our-31b) · [External host study](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/)

## B. Where the research went wrong

The F4/F5 diagnosis treated a nonzero command and the absence of a recognized pre-edit test as evidence of a dominant failure cause. A collection error, an irrelevant check and a wrong patch can produce the same observation. The repeated E4B denominator supplied diagnostics for that system. Its results cannot identify causes in the scored 31B system. The evidence-stage experiment stopped at eligibility (19/30 gold passes, all 19 fail no-op, too few eligible FastAPI tasks). Contrastive Contract Checking also lost priority because the later source audit found zero demonstrated repository-visible witnesses for competing specifications in the cases it reviewed. These are distinct negative findings about eligibility and support for a hypothesis. [Eligibility run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42068107095) · [Case audit](docs/research/semantic-repair-gap-audit-2026-11-06.md#completed-case-level-falsification-audit--existing-trajectories-only-2026-11-06)

## C. Three competing hypotheses

1. **Restart with observations verified against the base checkout.** At a fixed checkpoint, give one fresh same-model attempt an observation packet containing matching source excerpts and reproducible, issue-relevant command results. Omit the previous diagnosis and diff. An observation that depends on the abandoned edits is stale after rollback. SWE-Replay reuses a trajectory prefix. RestartSmart can inherit edits and gained 3.0 points on Gemma 31B at 20.5% extra tokens in one setting, with inconclusive separation from its cold-restart control. The proposed distinction is the rule for which observations survive rollback and its value at equal cost. It is repo-independent in form. It could discard useful partial progress or cost more to check than it saves. Falsifier is no worthwhile resolution gain against both continuation and an equally short ordinary observation handoff. [SWE-Replay](https://arxiv.org/abs/2601.22129) · [FailFast/RestartSmart, Tables 3 and 8](https://arxiv.org/abs/2608.03222)
2. **Represent explicit requirements by the code paths they govern.** Tie each required behavior and preservation constraint to its public entry points and the implementation they share. Use dependency tools and source inspection to separate coverage gaps from locations that converge on the same fix. SpecRover already extracts intent, LocAgent already uses graph localization, and Working Set already models versioned dependencies. The narrower hypothesis is that explicit path coverage yields correct fixes under a matched context budget. This could transfer across repository layouts, although dynamic dispatch and single-path issues limit coverage. Falsifier is improved path coverage without improved held-out resolution or preservation at equal cost. [SpecRover](https://arxiv.org/abs/2408.02232) · [LocAgent](https://aclanthology.org/2025.acl-long.426/) · [Working Set](https://arxiv.org/abs/2608.16630)
3. **Train the editing policy on paired execution feedback.** At identical repository states, pair a behavior-relevant assertion with an infrastructure or irrelevant failure that has the same exit code. Supervise recovery choices by eventual independent correctness. SWE-Gym and newer trajectory training support learning agent behavior. Counterfactual Rollout Replay already learns from forks. The specific research question is whether controlling for the failure source teaches portable feedback use. Its value depends on realistic pairs and transfer across runner formats. Falsifier is better feedback classification without more correct final patches than matched outcome-only training on unseen repos. Same-base LoRA is allowed in principle. Data, compute, serving and transfer remain unverified for this approach. [SWE-Gym](https://proceedings.mlr.press/v267/pan25g.html) · [Teaching Agents to Code Reliably](https://arxiv.org/abs/2610.03984) · [Counterfactual Rollout Replay](https://arxiv.org/abs/2609.33875)

## D. Decision

Prioritize hypothesis 1. It addresses a measured gap between candidate diversity and the cost of redoing a full run. Its effect can be isolated without training or requiring agents to recover requirements absent from the task. Path coverage has a narrower demonstrated failure surface here. Policy training has stronger external results but greater validation cost. The distinctive claim is selective reuse of base-valid observations under a shared deadline. Originality and efficacy are provisional. If most stalled prefixes lack usable observations, or if all arms rarely generate any correct patch, redirect toward representation or the editing policy.

Kaggle permits one common Gemma 4 variant (31B, 12B, E4B or E2B) per submission, optional LoRA, and sandboxed tools. The 12-hour solver budget includes sandbox setup and excludes final validation. The design fits an offline workspace and one model in principle. The documented AgentTool creates a child session and copies parent state. Clean workspace, state isolation and budget accounting require validation before any harness adoption. [Kaggle rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes) · [ADK AgentTool source](https://github.com/google/adk-python/blob/v1.36.1/src/google/adk/tools/agent_tool.py)

## E. Next discriminating research action

When authorized, run **one paired three-arm checkpoint trial** on a locked initial screen of 24 eligible issues from at least three repositories outside prior development, reserves and adapter data, with two seeds per issue. Check independent fail-to-pass and preservation tests and gold-pass/no-op-fail before inspecting model outcomes. Use the exact 31B V2 baseline, shared prefix, fixed halfway checkpoint at a tool boundary and identical remaining solver budget. A continues. B restarts on clean base with a short recency-ranked packet of observed facts. C uses the same clean restart and packet template, with records admitted only if their source bytes match the base or their read-only behavior reproduces there. Match packet length to the shorter eligible packet. Count early finishes identically and keep no-evidence cases in the denominator.

Interleave arms on the same pinned scorer and host. Charge packet checks, reset and setup to the budget and count tasks lost at a global cutoff as unresolved. Measure verified final resolutions, rescued and broken pairs, candidate availability and elapsed solver time. This screen budgets up to about 13 L4x4 host-hours inside the agent loop at V2's 8-minute per-task cap with a shared prefix, plus setup and grading. Judge deployment feasibility against 12 total solver hours on roughly 120 tasks, using measured scheduling overhead. [Kaggle task count](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746008)

Advance if C improves correct resolutions against both controls at equal cost. If B and C both beat A and their difference is tightly small, keep the simpler reset explanation. If the paired uncertainty excludes a worthwhile gain (prespecify 5 percentage points) against either control, retire the selective-transfer claim. Wide intervals mean INCONCLUSIVE. A correct draft already available to the same arm before the cutoff, followed by an incorrect final patch, identifies room for better selection or retention. Rare correct candidates across all arms shift attention upstream. This verdict used existing records and public research only.

---

# NOW — case-level research verdict (2026-11-06 MYT)

**RESEARCH-ONLY RESULT: CONTRASTIVE CONTRACT CHECKING DOWNRANKED.** Inspected the **existing** 17-task E4B topology single-root development trace artifact `13150931817` (Actions `41458804862`) and upstream original PR/issue evidence for ten concrete cases. The resulting [case-level audit](docs/research/semantic-repair-gap-audit-2026-11-06.md#completed-case-level-falsification-audit--existing-trajectories-only-2026-11-06) found **no demonstrated repository-recoverable competing-behavior witness (class B)** in reviewed concrete cases. This is **insufficient supporting evidence**, not a scored rejection of the method.

**Distinct, supported sources of failure:** explicit requirement with incomplete/wrong edit (e.g. `fastapi_14448`, `rich_3061`), explicit requirement but failing edit-tool/navigation (`fastapi_14873`), versus externally specified requirement missing from offline task text (`rich_3934`, `rich_4079`, `rich_3105`). One positive control `fastapi_9425` **resolved** with a patch different from upstream reference; gold-text equality is not correctness. **At least five of 17 issue statements are materially underspecified** without their offsite issue/PR detail. Do not generalize prevalence to hidden 31B tasks or imply no repository clue can ever exist.

**Next research direction (not authorized to implement or submit):** audit **specification sufficiency**, **multi-entry-point requirement coverage** and **edit semantic correctness** separately. Reopen class B / contrastive-contract intervention only after actual pre-edit repository evidence discriminates two legitimate interpretations in multiple independent examples. No benchmark runs, Kaggle submissions/status checks, model inference, training, or `submission/` edits in this research turn.

---

# NOW — mechanism-first research audit (2026-11-06 MYT)

**ACTIVE DIRECTION: RESEARCH ONLY.** User explicitly corrected course: do not use Kaggle submissions, repeated status probes, prompt/budget tweaks, or deployment as a surrogate for independent research. **No Kaggle submit, GPU/TPU run, model inference, training, or `submission/` changes in this work.**

**New independent source audit:** [Semantic Repair Gap — 2026-11-06](docs/research/semantic-repair-gap-audit-2026-11-06.md). It triangulates own 17-task E4B development evidence, scored 31B bundles, and the public Budget-Fit author's *different* exposed trace sample. Key limitation: 31B hidden task-level failures are not visible. The 0.08 → 0.17 displayed score is a multi-variable system contrast, **not proof that any component caused the gain**.

**Mechanism question:** on issues where the agent already finds relevant source, can a repository-visible discriminating witness resolve *two plausible competing interpretations of an underspecified behavior* before editing? Distinguish explicit requirements (A), repository-recoverable gaps (B), and genuinely unrecoverable gaps (C). This is a **hypothesis, not a proven new technique**. Plain test-first, graph localization, regression-test selection and more subagents overlap known prior art and cannot be claimed as novel.

**Next research action, before any implementation decision:** inspect a few *already inspected* development examples for actual source-visible A/B/C evidence (reference patches audit-only), then reject or refine this hypothesis. Do not invent case labels, train, re-evaluate models, or repurpose held-out sets. A pure prompt instruction to “verify more” is insufficient and was not selected.

**Previous submission receipt, historical only:** `58045795` was accepted, with status PENDING at last authenticated check 2026-11-06 05:53 UTC; there is no new result in this research audit. No new submission should be driven by that result.

---

# NOW — Kaggle-only audit / official cap5 submission accepted (2026-11-06 12:44 MYT)

**USER-SELECTED METHOD: Audit → official Kaggle code submission → read-only score verification. No self-run model/issue experiments.**

**OFFICIAL ENTRY ACCEPTED:** Kaggle ref **`58045795`**, `SubmissionStatus.PENDING` at authenticated read-back **2026-11-06 04:44:31 UTC**; Public Score and Private Score both empty. [Successful official recovery workflow 42164252901](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42164252901) independently fetched the already-built private CPU-only Kaggle artifact, verified ZIP SHA256 `c9eeb05c2b5c3c9a48689a6afd22ed48334efccd685999539c60567c8ef76551`, matched 3 unchanged original members byte-for-byte and the original `eval_config.yaml` after reversing exactly `max_time_minutes: 8 → 5`. The official submission API returned ref `58045795` and its existence in the authenticated Kaggle submission list was verified. **No score claim is yet possible.** This public V2 derivative is **not original novel research**.

**CONTROL:** exact attributed public Budget-Fit V2 `58019162` COMPLETE Public **0.17**, originally upstream ref `lynnsakurai/.../2` (Apache-2.0), ZIP `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`. Original homegrown 31B `57983156` COMPLETE Public **0.08**. Only comparison `58045795` vs `58019162` is an identical-model/tool/prompt/sampling/budget-other-fields **single-variable cap change**, not a reliable task-level causal proof. Predeclared rationale and interpretive limits in [Research Reset](docs/research/independent-strategy-reset-2026-11-06.md).

**Operational failure diagnosed/resolved without a second builder:** original [submit workflow 42162206978](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42162206978) failed because it polled the metadata ID `kolihhan/gemma4-audit-cap5-42162206978`, while Kaggle automatically slugified the supplied **title** and created `kolihhan/gemma-4-public-v2-cap5-official-audit`. [Read-only inspection 42164107617](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42164107617) identified the real slug. The recovery workflow reused that exact pre-existing COMPLETE private CPU build. No retraining, new GPU notebook, raw competition-data mirror or duplicate Kaggle code submission.

**NEXT:** query **exact submission `58045795`** using authenticated Kaggle CLI until terminal; report score and difference versus 0.17 **without tuning/resubmitting based on Public LB**, and stop after this one candidate. The previously reported 0 GPU quota did not block this official code submission. Do not promote into canonical `submission/` solely from Public score.

---

# NOW — official 31B reference result and inference gate (2026-11-06 12:10 MYT)

**VERIFIED latest:** exact attributed public V2 reproduction Kaggle ref `58019162` is **COMPLETE, Public 0.17, Private empty**. Authenticated [read-only run 42160680339](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160680339) at 2026-11-06 04:08:31 UTC. Prior scored 31B original baseline `57983156` Public 0.08; +0.09 displayed difference represents a *bundle* of configuration/tool/prompt/budget changes, not original research or a causal ablation. V2 is a **single-root pretrained 31B** and confirms no complex multi-agent topology is needed for this score, not that extra agents could never improve it.

**RESOURCE BLOCKER:** [authenticated `kaggle quota` run 42160889153](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160889153) at 2026-11-06 04:10:34 UTC: **GPU 0.00h remaining, reset 2026-11-07 00:00 UTC / 08:00 MYT; TPU 19.97h remaining**. No GPU launch was attempted; do not claim a 31B experiment ran or switch hardware silently.

**NEXT:** pause the proposed 5-vs-8 minute diagnostic because the exact V2 system (8 minutes) scored 0.17 and differs from the 5-minute system in several settings. Both are under a global 12-hour/approx.120-task competition limit; a higher per-task cap need not mean higher average runtime. When legit GPU quota permits, first obtain/inspect **one private 31B V2 trajectory on already-inspected development issue(s)**, or reuse any existing uninspected V2 trajectories, to identify whether the bottleneck is patch semantics, tool/context loops, localization, or time. Choose ONE single-variable test only after a concrete failure mechanism is observed. Do not touch reserved cohorts, alter canonical `submission/`, train, LoRA, or submit another copy.

**REPORT:** [Independent Research Reset, updated Nov 6](docs/research/independent-strategy-reset-2026-11-06.md). Research decision is hypothesis review, not an improved original agent.

---

# NOW — Independent Gemma 4 research reset (2026-11-06 MYT)

**ACTIVE RESEARCH DIRECTION: REASSESS THE BOTTLENECK. Do not continue the evidence-before-mutation B/C lane or build more candidate-selection infrastructure by default.** This decision is documented in [Independent Research Reset](docs/research/independent-strategy-reset-2026-11-06.md) and is not a negative performance result for that candidate, which was never evaluated.

**Verified score evidence:** E4B Reliability-v1 Public 0.03 (`57921371`), same-policy 31B Public 0.08 (`57983156`); the attributed external V2 reproduction (`58019162`) was PENDING **at its last authenticated check 2026-11-05**; do not claim it scored without checking a fresh terminal response. The V2 package changes 5→8 minutes, tools, policy and turns; cannot attribute improvement to an individual factor.

**Research diagnosis:** Existing E4B 17-dev traces show poor solution reliability, and five tasks submitted after a nonzero test command without an edit, but they **do not demonstrate verification is the dominant reason 31B failed**. The original evidence-stage and 4+12 protocols stalled at eligibility, not at an actual model/causal test.

**Latest eligibility check, already completed:** [gold CPU run 42066105011](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42066105011), 19/30 reference-patch pass (Rich 13/14; FastAPI 6/16); [no-op CPU run 42067120930](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42067120930), **19/19 no-op fails** among gold-passing tasks; [final readiness 42068107095](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42068107095) SUCCESS as engineering check but **NO_GO_INSUFFICIENT_ELIGIBLE_TASKS** (4 pilot + only 10 exploratory). None measures agent quality.

**Next scientific decision, not another agent build:** distinguish capability/patch semantics, useful work per wall-time, localization, and harness reliability. The report proposes one conditional single-variable 31B **5-vs-8-minute dev diagnostic**, with the same model/config/tasks, global 12-hour budget normalization, and explicit interpretive limits. The external Agentless/SWE-agent research is counterevidence to automatically adding more agents, not a transplant recipe. No new model run is authorized here while private GPU quota blocks startup.

**Scope:** no new training/LoRA, Kaggle submission, model inference, GPU, raw data mirror, repo visibility/security changes, `submission/` edits, or modifications to any existing frozen cohort. Keep prior negative results and original contracts for historical provenance. Do not call research protocols a score improvement.

---

# NOW — discriminating-evidence 4+12 CPU eligibility checkpoint (2026-11-06 MYT)

**Research decision: NO-GO for balanced 4+12 exploratory A/B/C quality runs.** A separate, pre-outcome reduction from 4+24 reserved 4 pilot +12 exploratory IDs plus same-repo ordered replacements. [Exploratory contract](docs/research/discriminating-evidence-v0-exploratory-4plus12-2026-11-06.md), [frozen metadata-only manifest](docs/evaluation/discriminating-evidence-v0-exploratory-selection-2026-11-06.json). Neither contract certifies complete blindness.

**Actual no-model reference gold CPU result:** [Action 42066105011](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42066105011) SUCCESS, 30 screened, **Rich 13/14 gold pass; FastAPI 6/16 gold pass** (10 FastAPI failures report test exit 2, cause not classified). The preregistered balanced pilot+exploratory needs 8 FastAPI, so **NO-GO regardless of no-op outcome**. The candidate pool must not be resampled or strengthened based on outcome. Only safe result flags stored in [docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json](docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json).

**Verified static/compliance findings:**
- Deterministic 4+12 selection digest `20bca18b905161123ba0054d058a4f2b963cce6526c67b29e0175a81d17cc343`; original capacity-v0 4+12 remains reserved and untouched.
- [Action 42064561734](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42064561734) scanned 593 preselection Git source revisions and 14 refs, 0 tracked-ID historical mentions. This is NOT complete blind certification.
- [Action 42065388698](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42065388698) validated B/C YAML under fresh official 41-wheel scorer; 31B base, no adapters, frozen budget; both schema PASS. Runtime transfer, information isolation and quality remain UNTESTED; root LlmAgent -> AgentTool(SequentialAgent(evidence->coder)) is a proposal, not proven end-to-end.
- Private CPU no-op screening is linked to the exact passing gold set: [Action 42067120930](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42067120930). The eligibility-only frozen-order readiness check awaits it: [Actions workflow discriminating-evidence-ready-cpu](https://github.com/kolihhan/gemma-4-kaggle/actions/workflows/discriminating-evidence-ready-cpu.yml). These runs cannot reverse the FastAPI shortfall.

**Execution boundary:** no 31B model inference, no GPU use, training, LoRA, competition submission, new public raw Kaggle data mirror or edit to canonical `submission/` in this research lane. Scientific next decision: obtain independently eligible FastAPI tasks under a new prospectively justified data plan, or retire this lane and prioritize the existing separately reserved capacity-v0 E4B-vs-31B causal test when GPU startup is feasible; do not fabricate a small quality win from gold/no-op control results.

---

# NOW — discriminating-evidence research checkpoint (2026-11-05)

**This branch is research-only. Status: NO-GO for model inference, holdout evaluation and Kaggle submission.** No training or LoRA. The inherited capacity-v0 state is preserved below, but its open 31B hypothesis is not execution authorization for this branch.

- New experiment contract: [docs/research/discriminating-evidence-v0-gate-2026-11-05.md](docs/research/discriminating-evidence-v0-gate-2026-11-05.md).
- CPU-only reproducible gate: scripts/discriminating_evidence_preflight.py. Run python -m unittest -v tests.test_discriminating_evidence_preflight.
- **Verified CI:** [run 42060942156](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42060942156), success, 4/4 tests; selected metadata-only 4 pilot + 24 proposed confirmation, **Rich 14 candidates (zero replacements)**, FastAPI 16 candidates (two replacements). Selection fingerprint 13be4ff5205813de3ae869b65a7f7b5a37806589fa633f39dff8fd9dd265a137.
- **NO-GO reason:** an independent 24-task confirmation cannot yet have a robust eligibility replacement buffer; historical provenance and official gold-pass/no-op-fail checks remain undone. Not certified blind. The old capacity-v0 4+12 is still reserved and unmodified.
- The harness supports declarative LlmAgent subagents, output_key and include_contents: none in documentation, but a model-free *actual scorer-wheelhouse compiler check for B/C* and a dynamic evidence-isolation smoke have **NOT** been performed. Prior root-SequentialAgent compaction bug remains a design constraint.
- The scored 31B A baseline remains Kaggle ref 57983156, Public 0.08. At last authenticated query the attributed public Budget-Fit V2 ref 58019162 was PENDING; do not treat its author's reported score as ours.
- **Next allowed decision:** broaden/prove a genuinely uninspected replacement-safe denominator, OR explicitly freeze a smaller exploratory-only experiment with limited claims; then validate B/C against current official wheelhouse. Do not launch GPU, mutate submission/, train, or submit in this research branch.

---

# NOW — 2026-11-04

Updated: 2026-11-05 (new attributed public 31B V2 reference submitted ref 58019162 PENDING)

**Latest read-only scoring check: 2026-11-05 22:06 MYT / 14:06 UTC — submission 58019162 remains PENDING, Public/Private scores empty.** [Actions 42041728306](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42041728306) SUCCESS. No new submission, GPU use, or training. Do not infer an official score from the source author's 0.18.

## Attributed public 31B V2 reproduction officially submitted — 2026-11-05

**LATEST OWN SUBMISSION: Kaggle ref 58019162, PENDING (Public Score not yet available)**. Source: the openly published Apache-2.0 [Budget-Fit notebook by lynnsakurai](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue), precisely **Version 2**, whose author reports Best Score **0.18 V2**. This is **not yet our result and not an original innovation**. Our prior independent 31B model-only scored ref **57983156 remains 0.08**.

- Actual version-aware public Kaggle API retrieval: [Actions 42007379647](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007379647). V2 and V3 returned **different ZIP bytes**. Pinned V2 `submission.zip` SHA-256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`.
- Contract and byte-identical private builder preflight: [Actions 42007948296](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007948296), **SUCCESS, 4/4 tests**. Compiler sanity and exact output ZIP SHA pass. No training or GPU.
- **Official submission accepted**: [Actions 42008171687](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42008171687), Kaggle API returned `ref: 58019162`; authenticated submission listing returned `SubmissionStatus.PENDING` at **2026-11-05 10:09:09 UTC**. Description `attributed-public-budgetfit-v2-repro:no-train`. Private CPU builder ref `kolihhan/gemma4-budgetfit-v2-reference-42008171687`, version 1, produced the **same exact scored public V2 ZIP bytes**. Personal Kaggle GPU quota was not consumed; official scorer runs separately.
- No changes to canonical `submission/`, no LoRA, no additional scored submission or local holdout model evaluation. All source attribution, controls, thresholds and next original intervention gate: [public-budgetfit-v2-reproduction-2026-11-05.md](docs/research/public-budgetfit-v2-reproduction-2026-11-05.md).
- **Next**: query exact ref **58019162** read-only until terminal; never assume the author's 0.18 is ours. If it scores, compare our 0.08 with the reproduced bundle carefully; the bundle changes policy, tools, sampling and time budgets together and may be scored in a different host epoch. Do not launch another candidate while this submission is pending.

## Official Kaggle feedback availability probe — 2026-11-05

**Verified submission `57983156`: COMPLETE, Public LB 0.08, Private Score empty.** Authenticated read-only [GitHub Actions 42003198673](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42003198673) checked the Kaggle competition submission-detail endpoint: the returned human-readable fields were reference, status, public/private score and description. **No per-issue failure labels, hidden tests, patches or grader traces were exposed by this detail response.** The Kaggle CLI episode query returned no recognized structured episode IDs; this endpoint is documented for simulation competitions, while Gemma 4 is a scored patch-resolution prediction competition, so it is not a supported route to hidden issue traces. Do not misinterpret the episode command returning exit 0 as usable episode logs. No new submission, GPU, or data download occurred.

**Interpretation:** Distinguish official hidden-issue aggregate LB from **private Kaggle local diagnostic kernel traces on already-inspected public development issues**. The latter are usable for process research but are not scoring feedback from submission 57983156. If Kaggle later adds a dedicated grader feedback download, verify it afresh. The official submission page is https://www.kaggle.com/competitions/gemma-4-developer-agent/submissions .

## Test-command evidence and repair audit — 2026-11-05

**Verified CPU-only, no-training read of previously completed E4B development traces.** This is a process diagnosis, **not** an explanation derived from 31B hidden task logs. Official 31B Kaggle Public LB remains **0.08** (ref 57983156); no new submission or GPU evaluation was launched.

- [Final read-only GitHub Actions 41987818297](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41987818297): **SUCCESS, 19 unit tests passed**, safe artifact 13397016902 (ZIP SHA-256 f962e9daaac457706786eb38cf42a52b9e832c76858cc065f20240ac8db21175). Outputs contain aggregate counts only; raw commands, issue text, task IDs and patches remain in ephemeral/private run inputs. Archived compact evidence: [trace-test-evidence-v0-2026-11-05.json](docs/evaluation/trace-test-evidence-v0-2026-11-05.json).
- **Reliability-v1 E4B, previously inspected 17 dev tasks:** 11/17 contain a classifier-confirmed test command, 6/17 contain neither a confirmed nor a plausible overlooked test command; 13 test command calls in total, **12 explicitly nonzero** exits, **1 zero** exit, **0 unknown** exits. **0/17** tasks contain a confirmed pre-edit test. **5/17** tasks submitted a patch after a nonzero test command exit with no intervening mutation. **3/17** attempted a subsequent mutation after a nonzero test exit. **One unresolved task's last recognized test command exited 0**, so local test success is not sufficient proof of issue resolution.
- **Predecessor single-root E4B, previously inspected same 17 dev tasks:** 11/17 confirmed a test command, 6/17 without candidate tests; 17 recognized test command calls, **16 nonzero**, 1 zero, no pre-edit test, **9/17** submitted after a nonzero test exit without a mutation, **1/17** attempted mutation after a nonzero exit.
- **Quality check:** The previous permissive analyzer could synthetically miscount echo pytest as testing. A new anchored-executable sensitivity audit excludes this and identifies possible unclassified invocations separately. In actual traces, **zero** legacy unsafe recognitions and **zero** plausible unclassified invocations; **zero** multi-tool trace steps, so no shared-observation ambiguity in these counts. This strengthens the process finding beyond earlier counts of targeted tests only.
- **Interpretation boundary:** A nonzero test *command* exit may reflect environment, import, or collection problems rather than a wrong patch; no per-test output cause classification was performed. These 17 dev tasks are not the hidden 31B scoring set, and one Public LB score does not prove capacity or architecture causality.
- **Next discriminating step:** Do not add more prompt text just to demand testing; the existing soft instruction already says not to submit known-failing patches. Test whether a feasible runtime and validated workflow can enforce or induce a meaningful **verify → interpret failure → repair/retest** transition on a separately untouched, pre-registered denominator. No GPU private Kaggle pilot while quota still rejects startup, and no speculative scored submission.

## After-0.08 diagnosis execution checkpoint — 2026-11-05

**Outcome: Existing E4B trace-mechanics finding survived a stronger parser audit; new private 31B task-level diagnosis is GPU-QUOTA BLOCKED, not attempted.** No training, LoRA, or new scored Kaggle submission was created. The official pretrained 31B Public LB remains **0.08** (submission `57983156`), E4B Reliability-v1 remains **0.03**.

- Verified frozen CPU preregistration/preflight after a minor source-audit regression fix: [Actions 41980757540](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41980757540) **SUCCESS**. The earlier check incorrectly considered the *later-created frozen cohort metadata* a pre-selection exposure. The exemption now validates exact structured fields, supported IDs, counts, no task/patch text, and `certifies_blind=false` before skipping the manifest in a present-tree source scan. Historical Git cutoff audit remains separate and strict; **do not claim fully certified blind**.
- One explicitly authorized private 31B L4×4 startup/array-tool feasibility attempt was rejected on push: [Actions 41980782896](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41980782896), **`BLOCKED_GPU_QUOTA`, GPU run NOT STARTED, zero task evaluations**. Private Kaggle GPU quota remains a blocker even though the official competition submission ran successfully. The startup workflow was restored to **manual-dispatch only**, preventing accidental repeated GPU pushes.
- Instead, audited **existing** (not newly generated) E4B 17-task traces with a conservative opt-in v2 parser recognizing only safe `cd ... && pytest target` or equivalent shell wrappers where the overall exit still reflects the test. [Actions 41981385025](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41981385025) **SUCCESS**; artifact `13393822468`, SHA-256 `dbbb61634f22d241a95607e4386dc31eee29e865ac4ea0fbb9b54df3258098f2`. **Every measured aggregate stayed unchanged** from v1 to v2 in both historical E4B arms.
- Reliability-v1 existing E4B dev: **1/17 resolved**, **14/17 no *classifier-recognized* targeted test**, **0/17 classifier-recognized pre-edit targeted evidence**, **2 observed post-edit targeted failures with no subsequent edit**, **2 submits after recognized failed targeted test**. This strengthens the *process* signal, but complex test commands may still be unrecognized. These are E4B data, **not 31B hidden or fresh local task diagnostics**. Do not pretend the same counts explain individual 31B Public LB failures.
- Evidence snapshot (metadata only): [docs/evaluation/gemma4-31b-postscore-diagnostic-checkpoint-2026-11-05.json](docs/evaluation/gemma4-31b-postscore-diagnostic-checkpoint-2026-11-05.json).
- **Next gate:** No new 31B GPU pilot while quota is exhausted. Preserve frozen 4-task pilot + 12-task independent confirmation untouched. Once a legitimate GPU/private scorer runtime is available, run fixed-policy paired feasibility before testing any architecture change. Do not train or submit merely to bypass quota.

## Untrained 31B scored result — 2026-11-05

**OFFICIAL RESULT: COMPLETE; PUBLIC LB 0.08.** Submission `57983156` (`untrained-31b-v0:same-policy-as-reliability-v1`) was checked read-only via authenticated Kaggle CLI on **2026-11-05 06:18:27 UTC / 14:18:27 MYT**. Returned `SubmissionStatus.COMPLETE`, `publicScore: "0.08"`, `privateScore: ""`. Primary verification: [successful GitHub Actions read-only probe 41979509173](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41979509173), job `127086109897`. No additional submission or training happened during this probe.

- **Control E4B Reliability-v1:** Kaggle ref `57921371`, displayed Public LB **0.03** (previously recorded COMPLETE).
- **Treatment pretrained 31B, no LoRA:** Kaggle ref `57983156`, displayed Public LB **0.08**. Difference **+0.05 points**, approximately **2.67×** the displayed control score. The 31B artifact changes only the root `agent.yaml` model name; prompt, tools, sampling and budgets remain unchanged.
- **Supported claim:** The submitted 31B variant achieved a better official Public score than the earlier E4B submission. **Not supported:** deterministic task-level improvement, causal proof that model capacity alone is responsible, fully equivalent scorer epochs, private-LB generalization, or significance claims. Public LB is a limited, potentially noisy comparison.
- **Decision:** Preserve these scored artifacts and IDs, do not re-submit the same ZIP, do not reintroduce self-training/LoRA. Next meaningful work is analysis of the bottleneck and controlled, uninspected evaluation (frozen 4+12 cohort if resource capacity and provenance allow); no automatic GPU or new leaderboard submissions authorized.

## Untrained Gemma 4 31B official Kaggle submission — 2026-11-04

**OFFICIAL SUBMISSION ACCEPTED; SCORING PENDING.** User explicitly authorized submitting an untrained pretrained Gemma 4 31B variant without running any self-training or LoRA, superseding the prior research-only no-submit hold. This is a **new untrained model-only comparison**, not completion of the frozen local 4+12 capacity experiment.

- **Kaggle submission ref:** `57983156`; accepted via Kaggle API at **2026-11-04 11:38:59.950 UTC**. Read-back from Kaggle CLI shows `SubmissionStatus.PENDING`, Public score blank and Private score blank at ~11:39 UTC.
- **Submission description:** `untrained-31b-v0:same-policy-as-reliability-v1`.
- [GitHub Actions successful workflow 41822538668](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41822538668), job `126548987873`. Kaggle private **CPU-only ZIP builder** kernel `kolihhan/gemma4-untrained-31b-submit-41822538668`, version **1**. No Kaggle notebook GPU was used to build the artifact. **Official scored runtime may use Kaggle GPUs**, as required by competition.
- **ZIP SHA-256:** `42ac2e15e42118b51a2e8835ad5fc5e51cbbdfb472e65e3b8720b38b69738820`. Workflow fetched the private builder's `submission.zip` and verified exact byte-for-byte SHA and every member against deterministic local build before calling `competition_submit_code`.
- Source E4B Reliability-v1 submission ref `57921371` was **COMPLETE, Public LB 0.03**. The new 31B submission changes **only `agent.yaml` root model field** from `gemma-4-e4b-it-qat-w4a16-ct` to `gemma-4-31b-it-qat-w4a16-ct`. All five frozen source files are hash-validated, remaining prompt/tools/sampling/budgets unchanged. **No adapters or self-training**. Static contract tests and Kaggle read-back passed.
- Relevant new sources: `scripts/render_untrained_31b_submission.py`, `tests/test_untrained_31b_submission.py`, `.github/workflows/submit-untrained-31b-once.yml`. First workflow attempt `41822409300` failed in local Python import before Kaggle kernel creation; fixed module entry, then accepted on second workflow run. The submit workflow includes pre-submit dedupe and pending-slot check to prevent duplicate submissions.
- **No scored result yet.** The Public LB may differ due to model class, model/runtime topology, throughput, and host epoch. No model-capacity causal claim or task-level correctness comparison can be made just from future LB delta. Do not create another 31B submission until this ID is terminal and reviewed; do not silently tune the E4B prompt to this outcome.
- Next read-only check: `kaggle competitions submission 57983156` or `kaggle competitions submissions gemma-4-developer-agent -v`. Record terminal public score, submission status, and elapsed time with exact probe timestamp. Keep frozen 4+12 preselected cohort unexposed unless independently authorized for a separate experiment.

## Capacity v0 double-eligibility + frozen 4+12 cohort — 2026-11-04

**Actual CPU-only execution completed (no model, no training, no GPU, no scored Kaggle submission).**

- [Private CPU replacement no-op run 41817822401](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41817822401): **SUCCESS**, 10/10 gold-passing replacements were **no-op-fail**, no no-op-pass or ambiguous records. Source artifact `13315174170`, verified ZIP SHA-256 `14b7d69c2afd5d04075e770cbf70215bded62b9b73156b5cf8aff19c6deb42c1`. Metadata-only [screen](docs/evaluation/capacity-v0-replacement-noop-2026-11-04.json), Rich 4 + FastAPI 6.
- Original frozen 16 had 10 gold-pass + independent no-op-fail. With this replacement pool, six missing positions can be filled by **frozen SHA rank, without task-text or model-result selection**.
- [CPU-only frozen allocation CI 41818760587](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41818760587): **SUCCESS** using actual vetted artifacts; manifest returned **feasibility 4** (Rich 2/FastAPI 2) + disjoint **confirmation 12** (Rich 6/FastAPI 6), six ranked replacements. Artifact `13315922648`, ZIP SHA-256 `5047248721f904fb99c792504d720737811fb842dddb9b6d7e9d5a7c8412bce9`.
- Frozen [cohort metadata](docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json) and deterministic [allocator](scripts/freeze_capacity_paired_v0.py) are now versioned. A contract test verifies the committed cohort matches recomputation and fails closed on provenance/order/count/overlap drift.

**Limitations:** Gold-pass plus no-op-fail is **benchmark eligibility**, not agent task resolution, a leaderboard improvement, or proof of fully uninspected historical data. Git-source pre-exposure scanning found no earlier source mentions in 467 checked revisions, but past private artifacts/unrecorded views remain unverified. The four-task pilot is for model/runtime feasibility, not candidate promotion.

**Current execution boundary:** Follow the submission-first/no-new-training directive. The E4B and 31B comparison is still **NOT run** because of Kaggle weekly GPU quota and the separately paused Colab path. Do not automatically resume GPU runs, LoRA, or leaderboard submissions. The frozen E4B Reliability-v1 submission remains unchanged at recorded Public LB **0.03**.

## Submission-first audit completed — 2026-11-04 (read-only + metadata archive)

**Latest deliverable:** [submission-first research decision](docs/research/submission-first-no-training-decision-2026-11-04.md), based on scored baseline `57879765` and Reliability-v1 `57921371` (both displayed Public **0.03**), inspected development-trace mechanics, prior 12B one-task negative, and publicly scored **no-training** 31B comparators. No new model/GPU/LoRA/leaderboard run occurred.

**Bottleneck priority, not causality:** (1) issue semantics/root-cause/patch correctness; (2) targeted evidence plus repair transitions; (3) E4B capacity/policy; (4) harness/scorer epoch; (5) budget alone. The inspected 17-task trace classifier is conservative and can miss compound-shell verification. A larger model is not guaranteed to improve performance, and the two public 31B systems have different prompts, topologies, budgets and host epochs.

**Recovered prior CPU artifact, no new compute:** [gold-screen Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800), artifact `13308702997`, ZIP SHA-256 `944b8acaac1e5f349f81bb0c941348dbc7c5694a57a48ce0ea843023a416711b`. Metadata-only [results](docs/evaluation/capacity-v0-replacement-gold-2026-11-04.json): **10/16 gold-pass**, Rich **4/4**, FastAPI **6/12**. These are **not** clean holdout replacements yet: independent no-op-fail screening is still missing. Do not confuse gold-check pass with model quality.

**Active instruction remains:** pause self-training, pause Colab/31B GPU execution and speculative submissions. The existing preregistered untrained same-policy E4B-vs-31B design is only a **conditional future experiment**, pending GPU feasibility and fully screened/provenance-clean paired tasks. No new candidate has been promoted; frozen `submission/` unchanged.

## Submission-first / no-new-training decision — 2026-11-04

**Current user directive:** Stop self-training/LoRA expansion and prioritize the existing scored Kaggle submissions. Put the optional Colab 31B feasibility notebook and Kaggle 31B GPU gate **on hold**, rather than treating them as required next steps. This is a priority change, not a deletion or a claim that all fine-tuning is intrinsically ineffective.

**Latest verified official per-user result**, from the read-only Kaggle CLI in [Actions 41585360688](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688), 2026-11-04 03:13 UTC:
- Baseline E4B submission `57879765`: `COMPLETE`, displayed Public LB **0.03**.
- Reliability-v1 E4B submission `57921371`: `COMPLETE`, displayed Public LB **0.03**; predicted **0.08 [0.05, 0.12]**; improvement **0.00 displayed**; private scores unavailable.
- This is **no demonstrated leaderboard improvement**, not proof that the submissions solve identical hidden tasks or that a specific mechanism failed.

**Process evidence, nonblind inspected development diagnostic (17 Rich/FastAPI tasks):** **1/17 resolved**, 13 nonempty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted test, two observed targeted-test failures with no subsequent repair mutation, zero time/tool-cap exhaustions. These observations support a *hypothesis* of weak issue understanding → testing/repair decisions; they do not prove root-cause causality or characterize the hidden benchmark. See `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**Priority decision:**
1. **No additional self-trained verifier LoRA, no Colab training, no adaptation of the 9-example adapter into the scored submission.** Prior successful LoRA optimization is engineering evidence only; the tiny training set and lack of independent improvement do not justify promotion.
2. **No speculative new Kaggle submission** or re-submit of the 0.03 bundle. Preserve the frozen Reliability-v1 artifact and current baseline for comparison.
3. Focus on **submission evidence and untrained pretrained-Gemma agent design**: compare publicly reproducible successful submissions, trace evidence before edits, targeted tests and repair-after-fail; favor mechanism-first changes that can be independently checked. A 31B pretrained-model baseline remains an option *only after* a separate feasibility/compute decision; no GPU run is authorized by this status entry.
4. Do not chase 0.03 by patching inspected 17 task IDs. For any eventual new proposal, freeze a clean denominator and prediction before evaluation; do not claim generalization from one Public LB sample.
5. The optional Colab notebook remains committed but **not an active execution task**. Kaggle 31B quota remains blocked; no change to official submission.

**Next research-only step:** rank the actual submission failure hypotheses by evidence, compare public untrained 31B and E4B policies without training, and identify one low-compute, untouched evaluation whose result would change a real decision.

## Colab 31B synthetic-only feasibility alternative — 2026-11-04

**User-requested alternative to Kaggle GPU-quota blockade:** Added `notebooks/capacity_31b_colab_smoke.ipynb` on `exp/capacity-boundary-v0`. **Notebook created and statically validated; NOT executed on any Colab GPU yet.**

- [Static CI 41805674499](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41805674499): PASS; source/cell syntax and no-competition-data contract verified.
- Model checkpoint: `google/gemma-4-31B-it-qat-w4a16-ct`; frozen original synthetic probe code pinned at commit `b13087b402ceef0aa0aa2ce55d1f7aa2c99108c3` and verified with Git blob hash; 32K max context, 0.90 GPU-memory utilization, no LoRA.
- Fail-closed resource gate before installs/downloads: exactly one GPU with >=32 GiB **free** GPU memory, compute capability >=8.0, >=30 GiB free disk. These are screening heuristics and do not guarantee model fit. A 16 GiB Colab T4 fails by design; Colab GPU types/quotas are not guaranteed.
- For qualifying Colab runtimes, install vLLM, attempt one 31B TP=1 startup, then reuse original **plain / scalar tool / array tool synthetic probes**. Save only structured scalar metrics locally; do not mirror raw data or auto-upload logs.
- **Scientific boundary:** Colab uses a separate GPU topology (TP=1) and installed vLLM, not the four-L4 Kaggle official scorer wheelhouse. A successful Colab probe is merely supplementary model/parser feasibility evidence. It does not unblock the Kaggle quota, validate official scorer equivalence, score tasks, or authorize any 4+12 model A/B or leaderboard submission.
- A Colab account owner must attach/select a capable GPU and execute the notebook. No integrated Colab execution was available from this GitHub-only workflow. Future results must be recorded with GPU identity, versions, error classification, and whether they were reproduced in the official Kaggle environment.

**Next action:** User runs the notebook in Colab on a compatible GPU and shares the metrics JSON. On failure, distinguish insufficient hardware / installation / model initialization / parser errors. Keep Kaggle 31B blocked until an official compatible kernel can actually start.

## Capacity v0 replacement checkpoint — 2026-11-04 (CPU-only)

**Verified original eligibility (no model):** original 16 metadata-preselected IDs yielded **10/16 gold-pass** and, for those exact ten gold-pass IDs, **10/10 no-op-fail**. The per-ID no-op record was downloaded and checked against the original private [run 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), artifact `13300818683`, then retained as metadata-only `docs/evaluation/capacity-v0-noop-screen-2026-11-04.json`. No raw patches, issue text, or hidden tests were committed.

**Frozen original gaps:** pilot Rich 0 / FastAPI 1; confirmation Rich 1 / FastAPI 4. Six replacements are needed in total (**Rich 1 + FastAPI 5**), all still subject to independent gold-pass AND no-op-fail screening.

**New deterministic metadata-only replacement gate:**
- `scripts/build_capacity_replacements_v0.py` preserves preregistered selector SHA `4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593`, excludes all original 16 and the original known-exposure corpus, and ranks additional candidates using the frozen source SHA namespace. No old holdout, training, or manually seen tasks are intentionally reassigned.
- [CPU Actions 41803046378](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803046378): **11/11 tests PASS**; queue **Rich 18 + FastAPI 28**; preselection tracked Git-source history scan **467 revisions**, **0 mentions** among first **16** queued prospective screening candidates. Historical Git source cleanliness **does not certify blind status** across previous private artifacts or unrecorded inspections.
- The first screening cohort was frozen as **4 Rich + 12 FastAPI** (the exact first 16 Git-source-audited replacement-queue IDs), before seeing replacement task outcomes.
- [Private Kaggle CPU gold-control Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800) was launched using a fail-closed Kaggle push guard and a metadata-only artifact policy. **Gold outcomes were not yet available at this checkpoint.** It has no GPU, model inference, or leaderboard submission.

**Next gate:** inspect the per-ID safe gold artifact on completion, run private CPU no-op verification **only on gold-pass replacement IDs**, then fill the missing Rich/FastAPI slots strictly in original ranked order. If the preregistered 16 replacement screens cannot fill six gaps, screen the next unexposed queue prefix without selecting on model results, or explicitly reduce/retire the planned comparison if clean source candidates run out. Do not pronounce blind certification from Git-source audit alone.

**31B GPU remains independently BLOCKED by Kaggle weekly quota**, not failed model inference. No new 31B run, no new LB score, and the frozen Reliability-v1 candidate remains unchanged. Verifier-LoRA's adapter artifact is a separate older research branch, not promoted.

## Latest PIC decision — 31B startup BLOCKED BY GPU QUOTA

**Verified external blocker:** GitHub Actions [41794811345](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794811345), job 126456289520, attempted to push a *private synthetic-only* 31B L4x4 startup kernel. Kaggle printed **"Kernel push error: Maximum weekly GPU quota of 30.00 hours reached."** CLI exit code was nevertheless 0. The subsequent HTTP 404 was for a kernel that was never created. Read-only status probe [41795018386](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795018386) confirmed no notebook/result. **NO model weights loaded, no GPU inference, no candidate issues tested and no new leaderboard submission.**

**Safeguards now implemented:** The 31B GPU workflow is **manual-only** (no auto-push on source commits); a new CLI push checker rejects zero-exit quota errors and requires an explicit successful push confirmation. CPU GitHub Action [41795366875](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795366875) reports **9/9 tests PASS**, including the push-failure guard. Historical preselection Git-source audit scans **467 revisions** and found **0 pre-existing document/source mentions among the 16 candidate IDs**; this is stronger than checking only the current tree, but does *not* certify full blind status across past private artifacts/unrecorded views.

**Decision:** Do not launch or re-run 31B GPU until account quota availability is verified. Startup/tool-call behavior remains UNKNOWN (not failed). Do not fill all 16 tasks merely to keep busy if model feasibility is still blocked; the 10 gold-pass/no-op-fail tasks remain frozen and unused by a model. An E4B-only evidence/repair lane is a potential separate pivot, not authorized as an automatic fallback by the quota error.

Canonical report: docs/research/capacity-v0-31b-gpu-quota-blocker-2026-11-04.md

## North star

Build a competitive Gemma 4 software-engineering agent by learning which mechanisms transfer to Kaggle hidden evaluation, not by patching inspected tasks or chasing Public LB noise.

Research must remain anti-overfit, resource-aware, mechanism-first, and willing to reopen model/training/topology classes when evidence changes. Read `RESEARCH_DOCTRINE.md` before preserving or rejecting a major method class.

## Terminal scoring / active decision

**Reliability-v1 is terminal; its preregistered Public-LB prediction failed.**

Fresh read-only probe on **2026-11-04 03:13 UTC / 11:13 MYT**:
- baseline ref `57879765`: **COMPLETE**, Public LB **0.03**;
- Reliability-v1 ref `57921371`: **COMPLETE**, Public LB **0.03**, private score not available;
- frozen prediction: **0.08 [0.05, 0.12]**; observed result **0.03**, **-0.05** vs point, **0.02** below lower bound;
- observed displayed Public-LB gain over baseline: **0.00**.

Source: GitHub Actions run `41585360688`, latest job `126363546071`. Canonical calibration: `docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md`.

**Activated predeclared branch: Public LB < 0.05.** Do **not** automatically implement evidence-before-mutation-v0. Open an architecture/model-policy capacity discriminating lane, while explicitly preserving uncertainty about *which* mechanism failed.

Frozen Reliability-v1 submission remains untouched. No duplicate submission, no rerun of inspected 17-task denominator, and no task-specific prompt tuning.

## Root-cause investigation after the 0.03 miss

Research audit: `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**First-party evidence:** 1/17 resolved, 13/17 non-empty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted tests, 0 repairs after the two recognized failed targeted checks. Existing development result JSON shows **0/17 five-minute time-cap hits** (max ~201 sec) and **0/17 tool-cap exhaustions** (max 30 of 32).

**Main diagnostic hypothesis:** issue semantics/evidence → root cause → correct edit/repair is unreliable. Reliability-v1 reduced broad tests (14→10) without increasing recognized targeted tests (3→3), suggesting a possible verification-starvation trade-off rather than a knowledge gain.

**Not established:** hidden scorer task-level failure classes, same solved IDs across baseline/v1, model-capacity ceiling, partial hidden runtime/harness failures. The 17 development tasks are Rich/FastAPI-only and were inspected. Gold-pass/no-op-fail selection weakens blanket broken-harness explanations for that 17, not for hidden private-repo tasks.

**Decision correction:** the <0.05 pivot opens capacity as a *testable alternative*, not as the proven root cause. Before an expensive comparison, run a cheap scorer/model-source feasibility gate and freeze a genuinely untouched paired denominator. Do not assume that 5 minutes/32 calls caused the local 1/17 (neither limit was reached).

## Public leaderboard and open-method recon (2026-11-04)

Canonical evidence: `docs/research/public-leaderboard-vs-open-methods-2026-11-04.md`.

- Latest third-party CLIST Public LB snapshot: leader **0.29**, several teams **0.24**; **leader's method not publicly established**. Do not assign an unknown top agent a model or architecture.
- Disclosed scored stronger systems: **31B no-LoRA two-role v19 0.17**, with tracing/localization and thinking off; **31B single-root Budget-Fit 0.18**, using eight-minute cap, 28 tools and 4096 thinking budget. Neither proves multi-agent or thinking mode is universally superior.
- Factorial self-hosted study (3 model sizes × 2 scaffolds × 5 seeds × 104 public tasks): richer E4B scaffold improved local resolved rate **10.0% → 15.4%** while 12B min **25.2%** exceeded E4B max. The study used GGUF/llama.cpp and a repaired local verifier: **not official hidden LB**, not a directly controlled comparison with our E4B QAT.
- Caveat: identical public bundles have been observed scoring differently by up to 0.05 in hosted experiments; do not read a causal mechanism from single LB points.
- Our E4B 0.03 is lower than these 31B open systems, but the difference bundles model class, policy, budgets, harness epoch and hidden task draws. Stronger evidence for model capacity as a **candidate**, not a proven root cause.
- Official competition provides a **$10,000 E2B/E4B small-model prize**, but current filtered small-model standings have not been independently verified.

**Decision:** Preserve the planned capacity probe as a controlled falsification test; explicitly keep test-aware evidence/scaffold design as a competing hypothesis. Do not copy public leader configs without determining what mechanism is actually responsible.

## Capacity-v0 execution checkpoint — 2026-11-04

**Model-only CPU preflight: VERIFIED GREEN.** Run [41782383957](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782383957), job 126416680873:
- 7/7 integrity/selection/exposure-scanning tests passed;
- old frozen E4B submission hash contract passed;
- E4B vs 31B exact file-set check passed; only one agent model declaration differs;
- Kaggle official model instance metadata found both E4B and 31B;
- 41 current official scorer wheels fetched;
- both model declarations passed the same scorer's submission schema checks;
- 149 repo research/source files scanned for the 16 candidates, zero unexpected mentions;
- candidate feasibility n=4 (2 Rich, 2 FastAPI); confirmation reserve n=12 (6 per repo);
- frozen selector SHA256: 4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593.

Source code/contract:
- scripts/capacity_preflight_v0.py; tests/test_capacity_preflight_v0.py;
- .github/workflows/capacity-preflight-v0.yml;
- docs/evaluation/capacity-boundary-v0-preregistration-2026-11-04.md.

**Gold eligibility:** 10/16 passed; **No-op eligibility:** 10/10 gold-passing candidates failed no-op verification, giving **10 doubly eligible tasks**. Private CPU actions: [gold 41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), [no-op 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489).

**Remaining gates before any expensive model run:** gold-pass + no-op-fail eligibility, prior-run/human exposure provenance limitations, and 31B runtime/startup resource feasibility on L4x4. Do not call the 16 candidates certified independent blind; the source-text audit cannot inspect private historical notebook artifacts or unrecorded human views. Do not alter frozen Reliability-v1 or publish competition data.

## Capacity eligibility update — 2026-11-04 14:28 MYT

**Gold reference screen completed successfully.** Private Kaggle CPU action [41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), metadata-only artifact `13299564669` (SHA256 `12a7ff7a377258eee08dd639ebd60726bdeb260649892c451c1d47d81e9e2f`):
- 16 preselected metadata IDs screened;
- **10/16 gold-pass**, 6 failed the official reference-patch verification;
- feasibility cohort 3/4 gold-pass; original confirmation reserve 7/12 gold-pass;
- Rich: 7 gold-pass out of 8, FastAPI: 3 gold-pass out of 8;
- source metadata preserved at `docs/evaluation/capacity-v0-gold-screen-2026-11-04.json`; contains no raw issue statements or patch bytes.

**No-op control now COMPLETE.** Private Kaggle CPU action [41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), job `126429235397`, completed successfully. The safe output reports `CAPACITY_NOOP_SCREENED=10` and `CAPACITY_NOOP_FAIL_COUNT=10`, artifact `13300818683`. All ten gold-passing tasks require a non-empty solution under the checked official no-op verifier. No model inference or GPU was used.

**Decision:** Continue gold-pass AND no-op-fail filtering, then replenish failed candidates using preregistered within-repo SHA-ranked metadata order before inspecting any A/B model results. Do not call the 16 raw candidates clean. Do not launch E4B/31B GPU while eligibility is incomplete. Do not change the frozen Reliability-v1 submission, sampler, prompts or budgets.

## PIC handoff — eligibility gate closed, replacements needed (2026-11-04)

**Verified:** CPU model/schema preflight GREEN (7/7); reference-patch gold pass 10/16; no-op fail 10/10 of gold pass; **10/16 total doubly eligible**. Gold and no-op remain separate controls. Private job `126429235397` and artifact `13300818683` establish the no-op gate; confirm exact per-task metadata from that artifact before finalizing a replacement manifest.

**Original frozen shape:** feasibility 4 = Rich 2 + FastAPI 2, currently gold/no-op eligible Rich 2 + FastAPI 1 (**missing FastAPI 1**). Confirmation 12 = Rich 6 + FastAPI 6, currently eligible Rich 5 + FastAPI 2 (**missing Rich 1 + FastAPI 4**). Overall **six replacement tasks needed: one Rich, five FastAPI**, from *new uninspected IDs* and fixed within-repo SHA ordering.

**PIC mandatory next steps:**
1. Verify the safe no-op artifact at the per-ID level and commit a vetted derived metadata-only eligibility record (no raw traces/test material).
2. Formally construct the next within-repo SHA-ranked replacement queue from the pre-existing 90-task source metadata; exclude the initial 16, previous training/holdout, known exposures and any ambiguous provenance. Freeze replacement order *before seeing model results*.
3. Run just enough private Kaggle CPU gold-pass AND no-op-fail screening to fill the **1 Rich + 5 FastAPI gaps**; stop early if provenance or eligible pool fails. Keep pilot and confirmation strata separate. If no clean replacements exist, **reduce/retire the preregistered comparison explicitly rather than silently changing the denominator**.
4. After a frozen eligible denominator, audit 31B vLLM startup on Kaggle L4×4 and command/tool/parser behavior, then run the *same-policy* four-task paired **E4B/31B feasibility** test only if justified by costs. That four-task pilot cannot promote 31B or establish a statistical win.
5. If feasible, use the untouched independent 12-task confirmation. Record resolved, unique solves, time, tool calls, empty patch rate, verifier exits and cost; follow the pre-registered threshold and pivot on genuine evidence.

**Not yet done:** clean replacement cohorts, GPU startup, paired model inference, any new competition LB score. **No submitted reliability-v1 artifacts changed.**

## Frozen control / development evidence

Reliability-v1 is the current frozen E4B single-root control.

Canonical development diagnostic:
- run `41485671952`;
- job `125417231948`;
- 17 / 17 completed;
- **1 / 17 resolved**;
- 13 non-empty patches, 4 empty;
- mean tool calls `10.41`;
- mean duration `89.21 s`;
- call-cap exhaustions `0`;
- 12 / 12 non-empty unresolved patches had non-zero evaluator verification exit.

Relative to the earlier single-root run on the same inspected denominator:
- resolved stayed **1 -> 1**;
- total evaluator runtime fell about **12%**;
- mean non-empty patch size fell about **20%**.

Interpretation: Reliability-v1 became more restrained/efficient, not demonstrably more capable on the inspected development set.

## Trace-mechanics audit

Canonical audit:
- run `41590900152`;
- job `125767140355`;
- artifact `13209917848`;
- no new model inference or Kaggle task execution;
- analyzer tests **8/8 PASS**;
- safe-output gate PASS.

Same-classifier earlier single-root -> Reliability-v1:
- resolved: `1 -> 1`;
- targeted behavioral evidence before first mutation: `0 -> 0` tasks;
- targeted-test calls: `3 -> 3`;
- tasks with no targeted test: `15 -> 14`;
- broad-test calls: `14 -> 10`;
- localization-tool calls: `0 -> 4`;
- mutations: `40 -> 39`;
- failed targeted check followed by repair mutation: `0 -> 0`;
- submit after latest classifier-recognized targeted failure: `1 -> 2`.

The analyzer is conservative; use these values for same-classifier mechanism comparison, not as exhaustive semantic labels.

## Current global hypotheses

### H-lifecycle — evidence before mutation

Status: **OPEN, but no longer the automatic first candidate after the <0.05 pivot trigger.**

Current mechanism:

> Obtain the cheapest discriminating behavioral witness before mutation when a concrete contract exists, then reuse that witness after editing where feasible.

Why it remains plausible:
- both inspected single-root variants show 0/17 classifier-recognized targeted pre-edit behavioral evidence;
- soft repair/submission lifecycle instructions were not reliably followed;
- simply reducing calls/runtime did not improve solved count.

Canonical design:
- `docs/design/evidence-before-mutation-v0-2026-11-03.md`

Implementation plan:
- `docs/superpowers/plans/2026-11-03-evidence-before-mutation-v0.md`

### H-capacity — E4B/model-policy ceiling

Status: **SELECTED for next discriminating research lane; not proven as the dominant bottleneck.**

External evidence includes a materially stronger public 31B-era no-LoRA system, but that comparison is confounded by model size, topology, prompts, budgets, and development history.

Important recovered repository evidence:
- old E4B/12B same-lineage `rich_3278` smokes already exist;
- E4B produced a wrong patch inside five minutes;
- 12B default-thinking timed out with 0 patch;
- 12B thinking-budget-1024 also timed out with 0 patch despite more tool activity.

Canonical note:
- `docs/research/recovered-12b-capacity-evidence-2026-11-03.md`

Therefore:
- do **not** repeat the old naive 12B-first experiment;
- capacity does **not** mean `swap E4B -> 12B`;
- if the capacity trigger fires, the next experiment must add new information, e.g. a preregistered 31B same-policy probe or a frozen strong-public model-policy reproduction.

Corrected fallback design:
- `docs/design/model-capacity-probe-v0-2026-11-03.md`

### H-training — trajectory/policy distillation or SFT

Status: **REOPENED for feasibility, not causally prioritized yet.**

Do not confuse this with historical verifier-LoRA v0. Verifier-LoRA remains **NOT TESTED**, not falsified. Broader policy/trajectory training becomes higher priority only if untouched evidence shows the lifecycle is correctly instantiated but E4B still systematically reasons/edits incorrectly, or a capacity probe shows a clear model-policy ceiling.

## Evidence-before-mutation causal guard

A simple comparison of:
- A: frozen Reliability-v1 single-root;
- C: two-role evidence -> coder;

is not enough to prove evidence transfer caused any gain because topology, independent model invocation, context partition, and latency also change.

Pre-register a conditional third arm:
- **A** — frozen Reliability-v1 incumbent;
- **B** — topology-matched null handoff: evidence root still runs, but coder is prevented from receiving its evidence/history;
- **C** — same topology, coder receives evidence/history.

Resource-aware rule:
1. freeze A/B/C plus untouched denominator before trace inspection;
2. run A and C first;
3. if C does not beat A by the practical promotion rule, stop and do not pay for B;
4. only if C > A, run already-frozen B before inspecting task-level traces;
5. strong evidence-mechanism claim requires C to beat B meaningfully as well as A.

Canonical review:
- `docs/research/evidence-before-mutation-v0-causal-identifiability-review-2026-11-03.md`.

## Current ADK / scorer runtime blocker

A cheap source probe against the current official scorer wheelhouse verified:
- `google_adk-1.36.1`;
- `adk_submission-0.2.13`;
- `swegemma-0.2.11`.

The historical compaction path still raises when the root agent is not an `LlmAgent` and no explicit summarizer model exists.

Therefore **do not use a root `SequentialAgent`** for evidence-v0 under the current wheelhouse.

Current safe provisional topology:

`root evidence LlmAgent -> coder LlmAgent`

Properties:
- root has no `edit_file`, `write_file`, or `submit_patch`;
- coder is the only mutation/submission role;
- zero-diff-before-coder remains mandatory because `run_command` can mutate;
- transfer is model-controlled, so successful transfer/compliance must be measured rather than assumed.

Canonical probe:
- `docs/research/current-compaction-probe-2026-11-03.md`;
- workflow run `41624178623`;
- job `125877217844`.

## Predeclared score fork — terminal branch now activated

### Public LB < 0.05 — TRIGGERED (observed 0.03)

The live candidate underperformed the preregistered interval.

Do **not** automatically implement evidence-v0 first. Reopen the architecture checkpoint and choose the smallest new experiment that separates lifecycle/policy limitations from model-policy capacity. Use the recovered 12B evidence; do not repeat it.

### Public LB 0.05–0.12

The live result is consistent with preregistration.

Evidence-before-mutation remains the first causal mechanism test. H-capacity stays explicitly open and second-line. If evidence-v0 forms high-quality pre-edit evidence but correctness does not improve, pivot rather than stacking more evidence prompts.

### Public LB > 0.12

Lifecycle/policy changes transferred better than expected.

Proceed with the untouched evidence-v0 causal test, but do not treat one LB score as proof of mechanism. Keep the A/B/C causal guard.

## Resource policy

- Existing artifact answers a question -> reuse it.
- Cheap GitHub Actions / source probes / static validation -> use freely in this public repo.
- Kaggle GPU/full task evaluations -> only when they can falsify a named hypothesis or change a decision.
- No duplicate active submissions/diagnostics.
- No compute to obtain another sample from an already-inspected denominator.
- No verifier-LoRA catch-up run merely for bookkeeping.
- No repeated 12B `rich_3278` smoke.

## Next action — revised after quota rejection

1. **Hard stop on GPU:** Do not push the 31B model again while Kaggle's weekly 30-hour quota is exhausted. The exact reset time is UNKNOWN. Future check must verify account quota and inspect active workloads before any manual dispatch.
2. **When quota is available, one explicit manual startup smoke:** use the now fail-closed workflow .github/workflows/capacity-31b-startup-smoke-v0.yml; record start, plain request, scalar tool, array-shaped tool, and total cost. This is zero-task feasibility only, not a model-capacity measurement.
3. **Before issue evaluation:** keep original selection immutable, verify historical exposure beyond Git where feasible, and replenish eligibility by preregistered within-repo SHA order (1 Rich, 5 FastAPI missing) if 31B startup actually works. The gold/no-op current result is 10/16 eligible; no task text/ref patches shared.
4. **If startup works and resources justify it:** execute the pre-registered four-task paired E4B/31B pilot; only then consider the 12-task independent confirmation. No changes to Reliability-v1, no per-task hyperparameter tuning, no leaderboard claims from pilot.
5. **If quota remains unavailable:** hold the capacity experiment; evaluate separately whether the 0.03 failure warrants a cheap, independent E4B evidence/test/repair mechanism hypothesis. Do not silently call a model-class limitation proven.

No new model inference or Public LB score has been produced by this checkpoint.
