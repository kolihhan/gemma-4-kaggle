# BREAKTHROUGH_PLAN · Gemma 4 SWE-agent
2026-11-18 · Phase A frozen at blind_review_A.md; Phase B/C decisions here do not rewrite blind evidence.

## Decision
[事实] Current authenticated best reference in repository: **0.18** Public, submission **#58183466**, scored 31B Toolcap60 / 5min / 60 calls / 80 turns. Goal >=0.25. Public N **inferred as 58** from a public score-grid enumeration, not officially published; if 58, 11 -> 15 PASS, net +4. One problem ~0.01724; unpaired single-model SE at 11/58 ~0.0515. A standalone +0.02 Public does NOT establish a mechanism improvement. #58469374 is a distinct Existing-Test Retrieval submitted candidate; do not infer outcome or poll PENDING.

[事实] The base 31B agent ALREADY exposes get_code_neighbors, get_code_subgraph and search_similar_code. Prompt says to use these selectively. A graph-tool existence check is not a new capability; a conditional *decision rule* must change which file is edited.

[事实] Previous evidence around behavioral witness on 3 paired tasks: 0 rescued / 1 regressed and patch output 3 -> 1. This rejects repeating that exact implementation unchanged, NOT behavioral testing across all SWE agents.

## Ranked structural candidates and pre-mortem
1. **Conditional one-hop implementation localization** (new single-variable candidate). [判断] If text search finds 2+ same-named definitions OR a thin wrapper, query one immediate caller/callee edge, inspect production implementation, then edit; otherwise keep baseline. Failure: native graph lookup may cost calls, point to an irrelevant function, or 31B may ignore prompt. Early stop: no genuine model uptake, repeated irrelevant graph targets, or worsening confirmed PASS. [CPU source](scripts/build_caller_hop_v1.py) commit d28bd1a; [frozen-control tests](tests/test_build_caller_hop_v1.py) commit 3936c21; [CPU gate](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44284119641) launched via commit 426e7a6. [事实] Corrected CPU gate [Actions 44285143644](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44285143644) **SUCCESS** with five deterministic packaging tests. This is **packaging / prompt contract**, NOT a resolution improvement.
2. **Before-red / after-green locked behavioral witness**. [判断] Can reject wrong candidate patch when the issue has an explicit, executable contract. Failure: witness tests fabricated irrelevant behavior, imported dependencies fail or consume budget; 3-case experience suggests poor uptake. Do not repeat prior V4 unchanged; require concrete evidence of useful witness uptake before new scoring.
3. **Second-cause candidate only after a failed first witness**. [判断] Can rescue multi-cause errors. Failure: increased time and accidental regression from second patch. Only permit one alternative and compare on the same locked test. No unbounded retries.

[判断] After Phase B/C, no candidate has a defensible P(Public>=0.25) >15% for one submission. The most viable lower-probability test is caller-hop because it changes the action policy while preserving the verified 0.18 baseline runtime/model budget.

## Submission queue
- **Completed CPU gate**: [Actions 44285143644](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44285143644) success; exactly one prompt mutation, same 31B, 5 minutes, 60 calls, 80 turns, native tools and sampling. Not real-model correctness.
- **Official Kaggle submission ACCEPTED**: [Actions 44285838454](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44285838454), commit c27e2de. Kaggle API and authenticated read-back confirmed **#58505571** with description `caller-hop-31b-one-variable-20261118`, status PENDING and blank score at 2026-11-18 10:32 UTC. CPU archive SHA256 `83945f61352f48f15ca183481cf3c15bab60f64a23a84e855e8fc69e299b71f0`. Authenticated quota was allowed_now=1, active=[], num_today=0 before submitting. No new dev GPU. Do not poll until next user turn. Prior to action, preregistered:
  1. CHANGE = one conditional caller/callee hop for ambiguous wrapper or duplicate function symbols; unchanged model, tools and budget.
  2. EXPECTATION = exploratory ~+1 net resolved Public issue (~+0.017 assuming N=58), with low P of net +4; NOT guaranteed.
  3. DECISION = report numerical score and, if available, per-instance final extracted patch/PASS/FAIL/duration/steps. Do not call one-issue improvement a breakthrough; user sets acceptance threshold; recommend >=2 single-model SE evidence to say breakthrough.
- Before official action check **authenticated** 1/day quota, active submissions and duplicate receipt *once*, fail-closed on unknown or unavailable; never restart pending/scoring or overwrite the best ZIP; use existing Kaggle submission API path and capture authoritative submission ID. Score run is allowed; new development GPU pilot is NOT allowed.
- At no point treat CPU tests, tool-call counts, patch existence, COMPLETE with blank score, or mere model trace as issue-resolution improvement.

[事实] New caller-hop submission ID: **#58505571**, authenticated in Actions log; last observed status PENDING and score blank. New competitive improvement **not yet established**. Best verified result remains 0.18.
