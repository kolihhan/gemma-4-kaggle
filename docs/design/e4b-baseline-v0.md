# E4B Baseline v0 Design

## Intent

Create the smallest credible competition submission that can diagnose where a Gemma 4 coding agent fails. Baseline v0 is an experiment instrument first, not a maximum-score architecture.

## Goals

- Produce one valid declarative submission rooted at `submission/agent.yaml`.
- Use current allowed model `gemma-4-e4b-it-qat-w4a16-ct`.
- Give the model enough official tools to inspect, modify, test, and submit a patch.
- Keep reasoning/tool policy explicit enough that failure traces are interpretable.
- Bound per-task time/tool use so the design respects the competition-wide runtime constraint.

## Non-goals

- No LoRA in v0.
- No sub-agents / multi-agent orchestration.
- No custom skill package.
- No learned router or classifier.
- No attempt to maximize leaderboard score before baseline traces exist.

## Architecture

One `LlmAgent` receives the competition task and all 9 official harness tools.

The intended control loop is:

1. **Inspect / locate** — understand the issue, list/search the workspace, read the smallest useful code/test context.
2. **Hypothesize** — state a compact root-cause hypothesis supported by observed code or test behavior.
3. **Edit** — make the smallest convention-preserving patch that addresses that hypothesis.
4. **Test** — run targeted tests or a narrow executable assertion.
5. **Repair** — use actual failure output; do not repeat the same failed action without new evidence.
6. **Sanity check** — inspect status/diff and budget.
7. **Submit** — call `submit_patch` once the patch has been verified as far as the task budget allows.

## Tool policy

All official tools remain available:

- workspace: `read_file`, `edit_file`, `write_file`
- execution/lifecycle: `run_command`, `get_status`, `submit_patch`
- code intelligence: `get_code_neighbors`, `search_similar_code`, `get_code_subgraph`

The prompt does **not** force graph-first behavior. Cheap targeted tree/grep/read operations are often sufficient. Graph tools should be used when semantic search or caller/callee relationships are likely to reduce tool calls or disambiguate ownership.

## Initial generation configuration

Start from the competition-provided sample values rather than inventing a tuning sweep:

- temperature: `0.2`
- top_p: `0.95`
- max_output_tokens: `16384`
- thinking budget: `4096`
- include thoughts: `true`

These are baseline values, not established optima.

## Provisional evaluation budget

`submission/eval_config.yaml` starts at:

- command timeout: `300 s`
- max tool calls: `32`
- max task time: `5 min`
- max turns: `64`

This is an **engineering hypothesis**, not an official recommended budget. With a 12-hour total competition runtime and roughly 120 hidden tasks, 5 minutes/task leaves some aggregate headroom while still allowing a repair loop. Actual traces decide the next budget.

## Evidence discipline

The agent must not receive the reference `patch` or `test_patch` from `tasks.jsonl`. Those fields are only for offline analysis/ground-truth evaluation.

A run is meaningful only when we record task id, git commit, model/config, resolved result, elapsed time, tool usage when available, patch size/files, tests run, repairs, and terminal failure class.

## Experiment sequence after v0

Change one major variable at a time:

- **E0 — Baseline v0:** single E4B agent, no LoRA.
- **E1 — Navigation:** explicit graph-use policy if LOCATE/UNDERSTAND failures dominate.
- **E2 — Test/repair:** stronger targeted-test and repair behavior if TEST/REPAIR failures dominate.
- **E3 — Context/state:** compact evidence/state strategy if CONTEXT/BUDGET failures dominate.
- **E4 — Specialization:** add a sub-agent only if decomposition evidence justifies overhead.
- **E5 — Training:** LoRA only if a stable behavioral failure remains after prompt/tool-policy fixes.
- **Model comparison:** once E0 is stable, compare E4B against 12B/31B on the same fixed sample if compute permits.

## Success criterion for v0

Not “high score.” The first success criterion is simpler:

1. current scorer accepts the E4B submission;
2. at least one public task completes end-to-end with a produced patch/result;
3. the fixed diagnostic sample yields traces that can be assigned to the failure taxonomy.
