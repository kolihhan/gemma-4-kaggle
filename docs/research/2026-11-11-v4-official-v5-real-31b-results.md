# V4 official score and V5 real 31B mechanism failure — 2026-11-11

## Decision

**Reject V4 as a leaderboard improvement** and **do not promote the wrapped Scope→Coder V5**. The user-authorized official V4 submission scored **0.15 Public** (below the previously completed best **0.18**). The actual V5 one-task private Gemma 31B run **did invoke the nested AgentTool once**, but the call never returned successfully, consumed essentially the entire issue budget and produced **no code patch**.

The next hypothesis should prioritize **getting a correct materialized edit before spending the task budget**, instead of adding an optional/mandatory investigation stage. No new GPU runs or official competition submissions are authorized by this report.

## Verifiable source evidence

1. **Kaggle official result:** authenticated read-only [Action 42947403444, latest attempt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42947403444) at **2026-11-11 15:36 UTC** returned `ref=58222227`, `description=solver-v4-cgr-one-shot-20261110`, `status=SubmissionStatus.COMPLETE`, `publicScore=0.15`. The old best `58183466` remains **0.18**. Single official score does not prove a causal V4 regression; there is already evidence of score variability. This is nevertheless insufficient for promotion and not a reason to repeat the same candidate.
2. **Private real-model experiment:** [Action 42988852829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42988852829) SUCCESS as an execution orchestrator; actual independent one-task `swegemma` result: `instance_id=requests_7328`, `model=gemma-4-31b-it-qat-w4a16-ct`, `agenttool_calls=1`, `agenttool_returns=0`, `agenttool_errors=1`, `agenttool_seconds=289.911`, `duration_seconds=302.5137457`, `tool_calls=17`, `patch_chars=0`, `has_patch=false`, `resolved=false`, `test_exit_code=-1`. The evaluator row says `status=completed`, which means evaluation returned a result **NOT that the task was solved**.
3. **Read-only, sanitized private diagnostic** [Action 43050088652](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43050088652) confirmed one-task output and 13 private output files. It reports error class word hits but DOES NOT prove the precise exception responsible for the AgentTool's failure.
4. **Actual structured tool-event metadata** [Action 43050260136](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43050260136) shows **19 tool-event records**: `read_file=12`, `search_similar_code=3`, `get_code_neighbors=2`, `get_status=2`; **`edit_file=0`, `write_file=0`, `run_command=0`, `submit_patch=0`** in this structured trace. These event records may include responses and are *not* numerically interchangeable with the scorer's `tool_calls=17`. No private prompts, task text, reference patches, tool arguments or raw traces were printed in the public Actions logs.
5. **CPU mechanics:** [Action 42972954885](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42972954885) validated scripted-model nested stage execution and actual automatic ADK session compaction. That is not a demonstration that real 31B finishes the investigation/coder workflow within 5 minutes.

## Evidence interpretation

**Supported:** Model-mediated tool uptake **occurred at least once** in the real task, refuting the strongest “the model will never call the only AgentTool” failure mode on this sample. The wrapped tool failed to return; near-all the 300-second task budget elapsed; **no source edit was observed** and the issue was not resolved.

**Strong inference, not a proven exception class:** The multi-agent read/search-heavy trajectory exhausted time before useful editing. It could be due to slow 31B inference, too much investigation, nested model/state overhead, an exception or a combination. The probe records only that `AgentTool.run_async` threw a `BaseException`; it does not log its precise type, so it is incorrect to assert a specific `TimeoutError` or `CancelledError` root cause.

**Unknown:** Exact stage ownership of each read (Scope vs Coder), content usefulness of reads, whether the missing patch reflects deadline cancellation versus internal error, unobserved cases, and matched V2 issue performance under the exact 5-minute clock. One task is a mechanism/feasibility observation, not a comparative success-rate estimate.

## Predeclared decision and next experiment

- **Freeze and demote the current V5 wrapped ZIP** `25a656d65d580d3ed1bf4c54ab5a622a05afe231f1dd46fb2d861749fd08a1bd`. No second private GPU run on unchanged architecture; no leaderboard submission.
- Do **not** move straight to a four-task V2-vs-V5 pilot. With no V5 patch in the first run, that is presently a low-information and expensive comparison.
- Prioritize a **time-to-first-edit** mechanism: a simpler native-root 31B coder using the same allowed tools, minimal bounded initial reads or a deterministic time/call budget for the first scope step, no nested extra model unless actual evidence demands it. Do not assume another prompt will fix it. Specify how to enforce the bound at the harness/tool layer, or mark it as non-enforceable.
- Before new GPU: CPU-validate configuration and tracing; preregister a clean public-development task and a no-reference-patch context, a **5-minute shared budget**, first-edit/first-patch observables and stop criteria, plus remaining GPU quota. A matched frozen 5-minute V2 control is required before claiming improvement. One task is not a leaderboard predictor.
- The simpler alternative should explicitly differentiate **missing information**, **slow generation**, **failed tool execution**, and **incorrect patches**; do not keep treating every failure as insufficient task analysis.

## Privacy / reproducibility

All experiments use private Kaggle data at execution time; repo is public. Action logs include only allowlisted outcome metadata and tool names. The selection manifest is [`experiments/wrapped-scope-31b-adoption-v1/manifest.json`](../../experiments/wrapped-scope-31b-adoption-v1/manifest.json). One immutable Kaggle private kernel `kolihhan/gemma4-wrapped-uptake-42988852829` was pushed. Official Kaggle V4 result is completely separate. No GPU or submission was started during these read-only post-run diagnostics.
