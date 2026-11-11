# NOW — Verified Gemma 4 project state (2026-11-11 23:38 MYT)

> **This short default-branch entrypoint is a status index, not a replacement for experiment provenance.** Every changing Kaggle state must be re-checked using the authenticated submission ledger; do not treat this snapshot as live. The detailed, actively updated research and execution history currently resides on [`research/dual-agent-recovery-v0-20261108`](https://github.com/kolihhan/gemma-4-kaggle/tree/research/dual-agent-recovery-v0-20261108). Historical versions of this file remain in Git history.

## Competition result (official, authenticated)

- **Best completed/scored Public: 0.18** — Kaggle submission **58183466**, an attributed Budget-Fit V2 31B configuration with bounded 5-minute runtime. **Not our novel V3/V4/V5 architecture result.**
- **V4-CGR official code submission: 58222227** — authenticated ledger **COMPLETE**, Public **0.15** at 2026-11-11 15:36 UTC ([read-only Kaggle ledger check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42947403444)). **Below prior best 0.18**. Demoted from contender; do not repeat unchanged submission. One score is not causal proof of mechanism regression.
- [Actual V4 submission receipt and preflight](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42946421274). User-authorized V4 ZIP SHA-256 **5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be**.

## Research decisions, separated from engineering checks

- **Historical Contract & Impact optional Skill: not promoted.** [November 9 completed private 31B paired experiment](https://github.com/kolihhan/gemma-4-kaggle/blob/research/dual-agent-recovery-v0-20261108/experiments/architecture-contract-impact-v0/31b-paired-pilot-decision-2026-11-09.md): frozen V2 **0/4** resolved vs optional Skill **0/4** resolved; 107 vs 78 tool calls. Four selected public-dev tasks do not establish general comparative effectiveness or prove non-uptake.
- **Root SequentialAgent Scope→Coder: rejected for current wheelhouse.** ADK 1.36.1 session compaction fails with `No LlmAgent model available for event compaction summarizer` ([actual CPU failure](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42970282094)).
- **Wrapped Scope→Coder: scripted CPU pass, actual Gemma 31B failed first real task.** Root `LlmAgent` offers nested `AgentTool` with read-only Scope and sole-write Coder. [CPU gate](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42972954885) validated routing and compaction, but [real model pilot](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42988852829) called the tool **once, returned successfully zero times, error once, no patch, 0/1 resolved**. Thus current V5 is **not eligible for promotion or an unchanged retest**. Source in research branch only.

## Private real-model evidence — completed and assessed

- [One-task private 31B real model Action 42988852829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42988852829), immutable candidate SHA `25a656d65d580d3ed1bf4c54ab5a622a05afe231f1dd46fb2d861749fd08a1bd`, public-development issue `requests_7328`, 5-minute budget. The actual scorer returned `resolved=false`, `has_patch=false`, `tool_calls=17`, total `302.514s`.
- **Real AgentTool event:** called 1, returned 0, errored 1, occupied `289.911s`. This **confirms real model adoption on one task** but refutes successful execution of the full staged repair under the clock.
- [Read-only private trace classifier](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43050260136) observed 19 structured tool records: `read_file=12`, `search_similar_code=3`, `get_code_neighbors=2`, `get_status=2`; **no edit, write, shell or patch submission**. These events are not numerically identical to scorer `tool_calls`.
- The exact exception thrown by `AgentTool.run_async` was not captured, so **do not assert definitively that it was TimeoutError**. Runtime and behavior support an investigation-heavy, deadline-sensitive failure.
- [Detailed preregistered experiment decision and outcomes](https://github.com/kolihhan/gemma-4-kaggle/blob/research/dual-agent-recovery-v0-20261108/docs/research/2026-11-11-v4-official-v5-real-31b-results.md).

## Active research decision

1. **V4 0.15: close as no demonstrated gain; no duplicate official submission.** Keep best scored V2 bounded configuration at `0.18`.
2. **Current V5 wrapped Scope→Coder: freeze/demote.** Real model used the only workflow, but no patch after ~300 seconds. Do not burn more GPU on this identical topology or claim a success-rate gain from one negative task.
3. **Next hypothesis:** improve *time to first materialized edit* while preserving enough task evidence. Prefer simpler native-root model or demonstrably bounded analysis rather than a new cascade of model-mediated investigators. A true per-stage time/call budget must be enforceable, not only requested in prompt.
4. Before any next private 31B pilot: verify remaining GPU quota, predeclared distinct public-dev tasks, official task model/metrics, **same 5-minute baseline and treatment budget**, specific uptake/first-edit observables, and fail-stop logic. A clean matched V2 test is required for comparative claims.
5. Keep competition task contents/reference patches/private logs out of this PUBLIC repo. Do not modify solver artifacts via documentation changes.

## Public repository and navigation

- The repo is **PUBLIC**, not private; [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md) documents unresolved historical competition-data exposure. No new public raw tasks, reference patches, hidden grader content, private traces, or credentials.
- [AGENTS.md](AGENTS.md): repo rules; [RESEARCH_DOCTRINE.md](RESEARCH_DOCTRINE.md): anti-lock-in; [EVALUATION_POLICY.md](EVALUATION_POLICY.md): evidence and experiment controls.
- **Main/research branch divergence is real.** Do not infer `main/submission/` is the scored 31B ZIP, or that changing `NOW.md` changes competition artifacts.

**Last authoritative score check in this snapshot:** 2026-11-11 23:36 MYT (Kaggle authenticated ledger at 15:36 UTC). Updating these docs does not itself change solver behavior, jobs, quota, or scoring.
