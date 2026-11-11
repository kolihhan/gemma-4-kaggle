# Why 0.18, what has actually worked elsewhere, and the next one-shot submission

**Scope:** factual competition/evaluator/benchmark and **officially scored** evidence through 2026-11-12 00:45 MYT. This is an independent review of our own experiment record, not a claim that a new Kaggle score exists.

## Executive decision

1. The hypothesis "we only need more orchestrated analysis" is contradicted by a real V5 no-edit failure: on `requests_7328`, the nested `AgentTool` was invoked 1 time, consumed **289.911 seconds**, errored, and yielded **no source patch** (0/1). The LlmAgent root fixed ADK compaction but did not fix task correctness.
2. The hypothesis "fast edit alone makes the fix correct" is also contradicted: a matched 5-minute native-root V2 control on **the same issue** produced **3,454 patch characters**, 19 tool calls, and still **failed tests / resolved=false**. This one task is a post-hoc mechanism observation, not independent success-rate evidence.
3. A real **0.22 Public** was reported for the Kaggle public `flexonafft/gemma-4-budget-aware-coding-agent-v2/10` (version source `https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2?scriptVersionId=357955943`). We have independently downloaded its exact public `submission.zip` and tied its serialized file hash to the public version-scoring ledger. It changes **only the system prompt** relative to original **8-minute** public Budget-Fit V2; same Gemma 31B, ADK agent config, sampling and task/tool caps. **Our user's 0.18 submission was a 5-minute V2 derivative**; comparing it with the original **8-minute** 0.22 version also confounds run time.
4. There are **eight observational scored results** for the same `flexonafft` config-files SHA: `0.12–0.22`, mean `0.1562`, median `0.16`. These records are neither randomized nor paired; do not infer a 0.22 expectation from the maximum or infer the exact cause of variation. Our observed best **0.18** remains the verified achievement.
5. **User expressly requested another official submission.** Kaggle's authenticated `competition_get_submission_limits` at **2026-11-11 16:30 UTC** gave `allowed_now=0`, `limited_by_total=false`, and no active submissions. Therefore we must **not claim the entry happened**. A conservative external GitHub Actions one-off date gate is configured for **2026-11-12 00:30 UTC / 08:30 MYT** on the **default branch**, conditioned on a legal slot, exact source SHA, official compiler, versioned Kaggle CPU builder verification, and authenticated receipt. No forced retries if blocked/ambiguous.
6. Our next original competitive improvement should target **first valid edit AND correctness verification**, not simply more reads, more prompts, or extra model stages. The 0.22 public ZIP is a **properly attributed benchmark reproduction**, not our original algorithm or a promise of 0.25+.

## Score size, evaluator and uncertainty

The official competition evaluates code patches by **PASS/FAIL validation tests for each issue** and reports the fraction passed. It grants **12 hours total patch generation across all test tasks**, including sandbox setup and excluding patch verification. Models supported as of 2026-11-12 include 31B, 12B, E4B and E2B but all agents in one submission must use the same model variant.

Official: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes
Staff model announcement: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287

The community's score-lattice analysis infers **58 Public issues** (not an organizer's exact disclosure): https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743506 . If this interpretation is right, displayed `0.18` corresponds to **11/58**, `0.22` to **13/58**, and desired `0.25` to **15/58**. Thus the apparent 0.18→0.25 problem is approximately **four additional correctly patched tasks**, not better-looking traces. These task counts rely on the 58-task/truncation inference.

Participant thread on skill/sequential runtime failures and exact same-file score movement: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/750350 . This supports assessing runtime overhead but is not an independently controlled experiment. Independent community 31-task evaluation reports task-limit/timeout trade-offs and multiple outcomes for fixed configurations: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696 . Keep the official score separate from development results.

## Our actual verified evidence

| Candidate / experiment | Model, time, settings | Actual observation | Interpretation |
|---|---|---|---|
| Best user-owned submission `58183466` | 31B, V2 derived / 5min | Public **0.18** | verified best completed, not an original new architecture |
| V4-CGR `58222227` | 31B, 5min/28 | Public **0.15** | not promoted; one result does not identify causal regression |
| Contract & Impact optional Skill | private 31B, matched four tasks | V2 **0/4** vs Skill **0/4** | no observed gain; low-power all-fail evaluation |
| Root `SequentialAgent` | scripted ADK official | default compaction failure `No LlmAgent model available` | cannot deploy this root under current wheelhouse |
| Wrapped V5 (LlmAgent→AgentTool→Scope→Coder) | real private 31B, 5min | on `requests_7328`, 1 call, 0 returns, 1 exception, 0 patch, 0/1 | stage is too costly/failed; exact exception unresolved |
| Native-root V2 on same V5 failed task | private 31B, 5min/28 | 19 tool calls, patch 3454 chars, tests exit 1, 0/1 resolved | early editing possible but correctness remains bottleneck |
| Public `flexonafft` V10 original ZIP | public, 31B, 8min/28 | historical Public 0.22; exact-config 8 observations 0.12–0.22 | viable source candidate but uncertain rerun; prompt-only change from original 8min V2 |
| Separate `bliverrigpdoge` prompt-vs-V2 | private, 3 paired public-dev issues, both 31B /5min | [Action 43057377220](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43057377220) running at audit snapshot | NOT the scored flexonafft candidate; keep distinctions |

All verified internal outcomes are linked from [main/NOW.md](https://github.com/kolihhan/gemma-4-kaggle/blob/main/NOW.md).

## Provenance: exact original 0.22 source

- Original scored code URL: https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2?scriptVersionId=357955943 ; author's public notebook shows **Apache 2.0** license (web-public current page may show a different visible latest version).
- Notebook `/10` **actual public output** `submission.zip`: SHA256 `6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`.
- Scored serialized four-file SHA256 `56010e9e9d4c7f33856ce49d12ec3edae5c912261986e999a4aa989b3cd463cb` matched **the exact downloaded ZIP's four member texts**, not just a misleading notebook title.
- Changed against original public 8min V2: ONLY `prompts/system.md` (v10 prompt SHA256 `7f8dde62578a247ffbfc1a519b712ae65849fcfae1ee70c49e0628cab74cbef6`; original V2 prompt SHA256 `a42c35081c08f316fc76b02886c82d4073e6c143b63c40a86085b382b8bf113e`).
- Identical source files `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`: same 31B, sampling including thinking_budget 4096, 8min, 28 tool calls, 80 turns.
- Verified public scorer version metadata [Action 43055057050](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43055057050). Exact V10 archive member comparison [Action 43059134412](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43059134412); ledger-vs-output SHA match [Action 43059370313](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43059370313).
- One-shot source integrity/validator [Action 43060142518](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43060142518) **SUCCESS**, four CPU unit tests and official `swegemma` wheelhouse validation. **This was not model inference, scoring, or submission.**

## Hypothesis ranking

**H1 — source localization / tool-call efficiency.** More relevant than adding subagents; V5 spent its budget browsing. Public strong prompts instruct narrow search, early edit and targeted tests. But V2 already has many of these rules; simply restating them risks no gain.

**H2 — correctness after editing.** V2 demonstrates a materialized patch can still fail the exact validation tests. Diagnose the actual failure and feedback: API contract missed, incorrect exception/status, incomplete cross-file edit, test setup problems, or patch introduced regression. A future test-guided repair capability needs **measured effect on independent resolved issues**, not just a prettier patch.

**H3 — effective 12h throughput.** 8min per-task maxima across ~120 tasks could overspend the overall patch-generation budget. An 8min public version scoring 0.22 means it can still work, but no universal time optimum follows. Test total task distribution, not only selected successes. Smaller 12B/E4B could be faster but may be less capable; no own matched evidence to promote a model switch.

**H4 — stochastic scoring / changed evaluation conditions.** Identical file-set scores span 0.10. We must not optimize to a single leaderboard draw or interpret gains smaller than this scale as reliably causal. Only task-paired eval under controlled budgets can test a mechanism.

**H5 — fixed model capability / incomplete issue text.** Some offline issue descriptions omit essential external context. Neither additional agent orchestration nor a longer prompt can conjure unavailable data. Training, test-time policy search or richer deterministic repository signals may be necessary eventually, but current constraints favor no new training and careful use of the public scorer.

## One-shot actual submission contract

1. The main-branch workflow `.github/workflows/submit-attributed-scored-v10-quota-reset-20261112.yml` is date-gated for **2026-11-12 00:30 UTC**. GitHub cron availability is external; **scheduled attempt is not a confirmed submission**.
2. The workflow uses immutable commit `69fba2905f49a834a7c4f126dd8e2ee68c80d04c`, runs source/transport regression tests, verifies authenticated `num_allowed_now>=1` and no active entry, installs official wheelhouse, compiles the exact SHA-pinned public ZIP, verifies CPU Kaggle builder version and remote byte identity, calls `competition_submit_code` once, then requires the authenticated Kaggle submission marker/ID. Duplicate marker returns without another call; client exception triggers read-only receipt recovery only, not a second submit.
3. If quota remains 0, certificate validation fails, score is still pending, the schedule doesn't execute, or the receipt is missing, **report exact blocker**. Do not invent a score, call it our original code or retry on a different candidate automatically.
4. There is **no guaranteed score increase** from this 0.22 reproduction. Best confirmed user-owned Public remains **0.18** until Kaggle finishes scoring and a new authenticated terminal result exists.
5. Further original improvements should use clean issue-level tests: compare failure classes, time-to-first-edit, source patch correctness, runtime and errors. Reject nested AgentTool V5 as currently built; prompt changes alone are exploratory.

**Research status:** Official next entry planned in Github Actions. No new official Submission ID at the time of writing.
