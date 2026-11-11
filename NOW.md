# NOW — Verified Gemma 4 project state (2026-11-11 16:28 MYT)

> **This short default-branch entrypoint is a status index, not a replacement for experiment provenance.** Every changing Kaggle state must be re-checked using the authenticated submission ledger; do not treat this snapshot as live. The detailed, actively updated research and execution history currently resides on [`research/dual-agent-recovery-v0-20261108`](https://github.com/kolihhan/gemma-4-kaggle/tree/research/dual-agent-recovery-v0-20261108). Historical versions of this file remain in Git history.

## Competition result (official, authenticated)

- **Best completed/scored Public: 0.18** — Kaggle submission **58183466**, an attributed Budget-Fit V2 31B configuration with bounded 5-minute runtime. **Not our novel V3/V4/V5 architecture result.**
- **Actual V4-CGR official code submission: 58222227**, accepted 2026-11-11 02:34 UTC. The independent read-only authenticated [ledger recheck](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42947403444) at 2026-11-11 08:28 UTC returned **PENDING**, empty Public/Private scores. **No evidence of V4 improvement yet; do not resubmit the same candidate.**
- [Actual V4 submission receipt and preflight](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42946421274). User-authorized V4 ZIP SHA-256 **5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be**.

## Research decisions, separated from engineering checks

- **Historical Contract & Impact optional Skill: not promoted.** [November 9 completed private 31B paired experiment](https://github.com/kolihhan/gemma-4-kaggle/blob/research/dual-agent-recovery-v0-20261108/experiments/architecture-contract-impact-v0/31b-paired-pilot-decision-2026-11-09.md): frozen V2 **0/4** resolved vs optional Skill **0/4** resolved; 107 vs 78 tool calls. Four selected public-dev tasks do not establish general comparative effectiveness or prove non-uptake.
- **Root SequentialAgent Scope→Coder: rejected for current wheelhouse.** ADK 1.36.1 session compaction fails with `No LlmAgent model available for event compaction summarizer` ([actual CPU failure](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42970282094)).
- **Wrapped Scope→Coder: CPU runtime-valid, research-only.** Root `LlmAgent` offers one nested `AgentTool` enclosing read-only Scope and sole-write Coder. The official scripted-model CPU harness verified native edit/tool order, state handoff and **1 actual automatic session compaction event** ([runtime gate](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42972954885)). **No actual Gemma 31B tool uptake or independently resolved issues measured.** Exact experiment code is in the research branch, **not in `main/submission/`**. Do not call it “V5 winner.”

## Active experiment decision

1. Keep official V4 `58222227` frozen until scored; perform read-only status checks.
2. A future **private** real-model test must first measure whether Gemma 31B calls the wrapped AgentTool, whether the investigation yields nontrivial evidence, when editing begins, whether the patch materializes, and time/tool cost. Compare against a **new, time-matched** single-Agent V2 control; original V2's 8-minute control cannot isolate V5's 5-minute architecture effect.
3. Use preselected disjoint public-development tasks excluding all previously observed pilot/audit IDs, with full-task text and no reference-patch access to the model. A very small pilot can test uptake/feasibility, **not statistical correctness gains**. Count no-op, error, and timeout as outcomes.
4. Do not send a new Kaggle competition submission, train, mirror competition data into public GitHub, or promote a new agent solely from CPU PASS. Respect GPU quota before any private inference.

## Public repository and navigation

- The repo is **PUBLIC**, not private; [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md) documents unresolved historical competition-data exposure. No new public raw tasks, reference patches, hidden grader content, private traces, or credentials.
- [AGENTS.md](AGENTS.md): repo rules; [RESEARCH_DOCTRINE.md](RESEARCH_DOCTRINE.md): anti-lock-in; [EVALUATION_POLICY.md](EVALUATION_POLICY.md): evidence and experiment controls.
- **Main/research branch divergence is real.** Do not infer `main/submission/` is the scored 31B ZIP, or that changing `NOW.md` changes competition artifacts.

**Last authoritative check in this snapshot:** 2026-11-11 16:28 MYT. Updating these docs does not itself change solver behavior, jobs, quota, or scoring.
