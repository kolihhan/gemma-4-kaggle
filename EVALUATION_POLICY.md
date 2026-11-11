# Evaluation Policy — Kaggle Gemma 4 Developer Agent

## Evidence hierarchy

1. **Official outcome**: authenticated Kaggle submission ledger and reported score for a terminal submission. An accepted, pending, failed or unscored receipt is not a result.
2. **Independent issue correctness**: a private, pinned official `swegemma` evaluator result with the original issue/task and a valid source patch; report full denominator, all failures and timeouts.
3. **Actual model-mediated mechanism**: recorded typed ADK model/tool/function events showing that an *unmodified real Gemma* chose an intended action and used its observation.
4. **Execution/engineering gate**: compile, schema, SDK transport, scripted-model CPU validation, patch ZIP verification and compaction safety. This is **not** competitive evidence.
5. **Hypothesis/secondary report**: source reviews, participant posts and theory. Label assumptions and alternate explanations; do not equate public notebook title with an authenticated score.

## Non-negotiable experiment contract

- Preregister task selection, source identifiers, baseline/treatment ZIP digests, model, evaluator, total time, maximum tool calls/turns, task-order policy, primary outcome and stop condition **before** reading outcomes.
- Use identical task text, model weights, native tool access and evaluator setup. Equalize meaningful **total wall-time and model-tool budget**; nested agents' extra calls, compaction, and sandbox preparation count toward realistic costs. Disclose changes in sampling/prompt/topology and budget.
- For a mechanism/uptake-only pilot: measure actual root `AgentTool` invocation, read-only stage completion, handoff packet observed, first edit, native tool calls, final patch materialization, errors, and wall-time. One task cannot estimate improvement in resolution rate.
- For matched correctness comparisons: each arm receives the same predeclared clean task; alternate arm order; report resolved, regressions, empty patches, test/collection errors, timeouts, median/aggregate latency, total compute and total candidate completions. Do not discard failed/queued runs.
- **No reference patches, grader expectations, or hidden eval results enter an agent's live workspace.** Private raw competition data/traces remain on Kaggle and must not be committed or uploaded as new public artifacts.
- A successful CPU scripted test is not evidence of autonomous behavior or a useful solution. A leaderboard point change alone is not causal proof. Preserve negative results.
- Distinguish true untouched confirmation from public-development sample or a repeatedly inspected set. Do not call a four-task, all-fail pilot proof of universal architecture failure.
- Resource gate: check current authenticated Kaggle GPU quota, competing kernels, and official submission ledger before launching; use a unique private kernel, cap runtime, prefer one informative test, no repeated full pilot by default.
- Formal Kaggle submission requires the current eligible competition quota, a frozen digest and an explicitly authorized one-shot action. Do not automate repeated official submissions. Never claim success without a real submission ID and terminal score.

## Decision thresholds

- An architecture is *eligible* for a private real-model pilot only when official compiler/ADK tests are green, root/tool interfaces are compatible, and the pilot could discriminate a specific competing hypothesis.
- Promote an architecture only after credible independent resolved-task improvement **and** acceptable latency/aggregate task-completion cost, not because stage order or state transfer works.
- If root tool uptake fails, terminate that topology's promotion; if the agent calls the tool but no useful new evidence reaches the writer, reconsider the missing-information hypothesis; if useful evidence reaches the writer but edits fail, investigate code generation and repair rather than adding more analysis.
- Reopen search, candidate selection, simpler root coders, or model-policy adaptation when evidence reveals a different bottleneck; no permanent method ban without a pivot condition ([RESEARCH_DOCTRINE.md](RESEARCH_DOCTRINE.md)).

## Historical note

Previous research experiments live in [the research branch](https://github.com/kolihhan/gemma-4-kaggle/tree/research/dual-agent-recovery-v0-20261108). This policy is governance, **not** a new experiment, score, candidate ZIP or task-selection manifest.
