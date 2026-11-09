# Solver V3 — code-grounded, checkpointed single-writer agent (research contract)

**Status:** Architecture proposal; NOT implemented, measured, promoted, or submitted. This is the intended substantial next refactor, distinct from the already-running V2 tool-cap60 one-variable experiment. Current authentic Public best: **0.17**.

## The actual problem

The previous four-task 31B V2 pilot ended with nonempty patches on 4/4 tasks and an independent resolution rate of 0/4. Contract & Impact's full root prompt + optional Skill also resolved 0/4; optional Skill invocation was not observable. Merely adding tokens, stages, a second LLM, extra prompts or CPU-only tests cannot establish improved patch correctness.

Two causal possibilities remain unseparated: **(a)** the solver did not generate a semantically correct repair; **(b)** it generated one but failed to preserve/verify/select it. A third is insufficient issue context. Solver V3 must be able to distinguish these without assuming one already wins.

## Architecture (not another Reviewer)

```
Original task + repository source
            |
  Single 31B Root Coder (same closed-model constraint)
     |       |        |
     |    Repo Evidence/Localization
     |       |
     |    Candidate Edit A --- reversible worktree snapshot
     |       |                    |
     |       v                    v
     |    Focused verification + real tool-result evidence
     |       |                    |
     |       +--> retain A / revise to B / restore best state
     |                                  |
     +--> Verify final actual diff and submit_patch
```

1. **Single writer, real source evidence.** Keep exactly one root Coder responsible for writing and `submit_patch`. Inspect the issue behavior, source-level entry points and relevant tests. If the task lacks requirements, record an unknown rather than inventing an oracle.
2. **Deterministic versioned repair state.** A private sandbox-side controller records *materialized* patch hashes and test outcomes, rather than trusting the agent's prose. A correct candidate cannot silently disappear when subsequent edits fail or are reversed. Nonempty final patch is necessary but not proof of correctness.
3. **Verification-aware candidate selection.** Compare a small number of actual candidate worktree states under the same total compute and test budget. Prefer a candidate only on applicable, discriminating tests and explicit requirements, not test count or green syntax. If no candidate earns support, preserve the most defensible state without claiming resolution.
4. **Budget-controlled action policy.** No free extra 31B agent; reserve capacity for a usable patch and independent finalization. Any added state manager must pay its latency cost against the same total 12-hour evaluation window.
5. **Real tool invocation guarantee.** The earlier optional Skill showed zero exact invocation markers in incomplete logs. V3 may not assume an instruction is execution. Before any expensive 31B run, verify the *actual ADK function-call events* and whether the controller can run under the restricted official tool registry and sandbox. If no reliable supported implementation route exists, reject this architecture rather than promoting a decorative diagram.

## Intervention and falsifiers

| Component | Missing capability targeted | Minimal independent falsifier |
| --- | --- | --- |
| Versioned patch states | Intermediate good code overwritten before submit | Actual tool-boundary snapshots never show an independently passing candidate discarded |
| Evidence-driven test use | Semantic errors persist despite test feedback | Model repeatedly selects wrong fixes after independently discriminating test feedback at matched budget |
| Bounded candidate search | Only one implementation hypothesis explored | Additional candidates add latency but no independently passing outcome |
| Stronger Coder model policy / clean LoRA | No correct candidate ever generated | Reproducible clean-held-out improvement fails to transfer |

Do **not** stack components automatically. If a different Coder policy or LoRA becomes the strongest explanation, switch architectures. The current deterministic observer is private-only: `scripts/candidate_history.py` and its submission-boundary tests may be reused as **measurement**, not mislabeled as a submitted capability.

## Evaluation

- Original byte-pinned V2 remains the control. Do not compare with a different task budget without labeling the effect.
- Evaluate on disjoint preregistered development tasks across repositories. Prior four Contract & Impact tasks and the separate four tool-cap pilot tasks are **exposed** and cannot become confirmation.
- Record actual final resolution, nonempty patches, preserved intermediate candidates, tool-call budgets, elapsed model/total time, typed tool invocation, and timeouts.
- Ablate checkpointing against equally budgeted ordinary Coder continuation. A second LLM only if it beats a same-cost Coder; an extra stage without new information is not a win.
- A new official Kaggle submission requires a valid scored candidate and available quota; never infer a gain from an Action or ADK CPU pass.

## Immediate delivery distinction

The **current new official submission attempt** is the narrow, reproducible V2 tool-cap60 candidate under `scripts/build_v2_toolcap_submission.py` and `.github/workflows/v2-toolcap60-official-once.yml`. That pathway changes *only* one budget dimension and is explicitly **not Solver V3** or a research breakthrough. It will refuse a formal submission if its already-running private 31B comparison fails the safety/evidence gate, or if official ADK compilation/quota checks fail. The final verified submission receipt is the only evidence of a new official entry.
