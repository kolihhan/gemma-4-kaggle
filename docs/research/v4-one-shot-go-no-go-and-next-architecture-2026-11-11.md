# Gemma 4 — V4-CGR one-shot decision and architecture pivot contract

Date: 2026-11-11 (MYT). Owner role: Research PIC. **This is a decision gate, not a scored improvement.**

## What is actually known

- **User-account official best:** Public **0.18**, submission **58183466**, COMPLETE, attributed Budget-Fit V2 Toolcap60 SafeTime5. Do **not** ascribe the result to V3/V4.
- **V4-CGR candidate:** One Gemma 4 31B, 5min/28 tool calls/80 turns, SHA256 **5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be**. Its official injected ADK **scripted/no-inference** CPU pipeline PASS; **zero independent real Gemma 31B issue-resolution evidence, zero official V4 receipts**.
- **Previously queued Notebook:** `kolihhan/gemma4-toolcap-31b-42609260933` is a **V2 Toolcap** diagnostic, **not V4**. At [authenticated Actions 42869971831](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42869971831), still `QUEUED` and no failure message. Kaggle weekly GPU remaining **17.76 hours** of 30; refresh **2026-11-14 00:00 UTC**. Do **not** blame GPU quota exhaustion without new evidence, restart the queued job or claim it tests V4.
- **Kaggle official competition submission quota:** Last authenticated daily call [Actions 42848511113 attempt 3](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848511113) at 2026-11-10 ~17:50 UTC: **allowed_now=0, num_today=1, active=[]**. No Kaggle entry may be submitted at the checkpoint.
- **Competition benchmark:** The public third-party standings snapshot [CLIST](https://clist.by/standings/google-the-gemma-4-developer-agent-competition-coding-artificial-intelligence-custom-metric-70662440/) showed leading score **0.29** and many **0.22–0.24** scores on 2026-11-11. This is an external scoreboard snapshot, *not* a matched architecture result, and the leading solutions were not established as public code. The user’s best 0.18 is still materially behind the displayed leaders.

## Crucial risk: model-mediated capability uptake

V4 appended a generated issue-specific pytest witness and tool instructions on top of V3-R and Budget-Fit V2, *without* changing the 31B model or budget. The official CPU scripted-model probe **forces** the intended `load_skill → run_skill_script(before) → edit_file → run_skill_script(after) → submit_patch` chain. **This establishes interface reachability only.**

Independent study: [Pilkwang Kim, *Measuring an Agent While Its Evaluator Moved*, §8–10](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/) reports an issue-specific pre-edit check carried out end to end in only **1/8 selected opportunities**, and a related helper skipped **7/16**. Those are *different bundles and selected tasks*, **not** an estimate for our V4, but they severely weaken the assumption that merely adding a Skill will change real model behavior. The same study documents long identical tool-call loops and nontrivial patch materialization loss. Our own earlier E4B evidence found frequent nonempty but unresolved patches; there is still no real 31B V4 failure distribution.

**Global bottleneck hypothesis:** wrong semantic interpretation / incomplete affected-surface repair, plus possible low uptake of complex model-mediated workflow, is more plausible than a packaging deficit. There is no validated evidence yet to choose self-generated tests over explicit impact/contract checking.

## The ONE permissible exploratory V4 official experiment

Once **fresh authenticated quota** permits a code submission and there is no duplicate V4 marker or active scoring:

- Use only [default-branch guarded manual action](https://github.com/kolihhan/gemma-4-kaggle/blob/main/.github/workflows/submit-v4-cgr-manual.yml), pinned to exact preflighted source SHA `b9ab80af9da55e0808971011a91ae925b3f5d05c` and exact V4 ZIP SHA above. Requires explicit workflow inputs, rechecks quota, built ZIP, real Kaggle receipt. No automated schedule or rerun of stale checkout.
- Capture submission ID, COMPLETE/ERROR status, scored Public result, private score if available, full-run completion/timeout and CPU builder version. Do not assert hidden task-level results if the competition returns only aggregate score.
- **Reject** V4 if runtime errors/empty score, fails to complete, or official score falls below the previously verified **0.18**. If equal or displays a one-task-sized small increase (0.20, etc.), classify **INCONCLUSIVE**, *not* an innovation; inspect real model tool-uptake data if the platform makes traces accessible.
- If `load_skill` / `run_skill_script` is absent or irrelevant for most observed opportunities, **retire CGR** as an imposed optional routine and avoid further prompt nudges on the same public population.
- A higher number such as **0.22+** is **PROMISING but NOT proved causal**: same-bundle Public scores can vary; never declare the self-generated witness responsible without real trace evidence, matched-budget comparator and independent issues. A leap near **0.24+**, if valid and complete, deserves prioritizing the bundle for further disjoint tests, not immediate novelty claims.
- The read-only public hash audit [Actions 42868703115](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42868703115) saw 29 observations in six repeated-bundle groups, 84 correlated pairs, median absolute pairwise difference 0.02 and observed maximum within-hash range 0.10; do not treat 84 correlated pairs as 84 independent repeats or the spread as a fixed noise floor.

## A substantive architecture pivot: Contract & Impact (not a V4 patch)

If V4 fails uptake or correctness:

1. **Target failure class**: issue may list a behavioral requirement but current solution touches one branch/API while leaving related callers, dependencies or edge-case invariants uncovered.
2. **Actual mechanism**: externalized typed *behavior contract + impacted-entrypoint map + evidence provenance* before selecting mutation scope. A stateful check maps each requirement to reachable call sites or explicit UNKNOWN, then only allows a scoped edit once the decision is grounded. This is **not** simply adding another paragraph to V4's prompt.
3. **Existing implementation**: [Contract & Impact architecture](../../experiments/architecture-contract-impact-v0/README.md) is already a CPU-valid independent candidate, SHA `4858587c922ae275417199d8c11c00abce2249e42992657e134ba8d6dc2df975`, official CPU [Actions 42551996131](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42551996131) PASS. This is an **available engineering starting point**, not an independently successful 31B solver.
4. **Discriminating test**: frozen Budget-Fit V2 vs Contract & Impact on clean, repository-disjoint 31B tasks with matched 5min/tool budget and an instrumented action trace; outcome is *resolved tasks* and change in missed-requirement cases, not length of plan or number of new skills.
5. **Falsifier**: no additional correct requirement evidence, poor stage uptake, more tool/time overhead, or no independent fixes. If so, reject this topology and reopen model-policy adaptation / bounded patch-search subject to resources and licence/compliance evidence.
6. **Explicit restrictions**: no new training/GPU queue or Kaggle slot while V4 official decision pending; no hidden patches fed to the agent; no new public data mirrors.

**Bottom line:** V4 is an executable but unproven research hypothesis. One legal exploration is justified to gather a real scored observation; repeating the same optional test-first trick is not. If results disappoint, use the already existing **different architecture** as the next hypothesis rather than prolong the V3→V4 micro-patch chain.
