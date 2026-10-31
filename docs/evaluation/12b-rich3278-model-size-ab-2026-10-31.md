# 12B `rich_3278` Model-Size A/B — 2026-10-31

## Question

Does Gemma 4 12B materially improve the current root-coder `LlmAgent` + verifier `AgentTool` configuration on the clean `rich_3278` diagnostic, without changing topology, prompts, task budget, tool budget, or turn budget?

## Control

Current E4B candidate, official Kaggle L4 smoke run `41199444320`:

- model: `gemma-4-e4b-it-qat-w4a16-ct`
- thinking budget: 4096
- duration: 253.37 s
- tool calls: 18 / 32
- patch: 275 chars, one file
- `test_exit_code=1`
- `resolved=false`
- coder reached edit/test; verifier AgentTool was invoked

The E4B failure is primarily verification/repair quality: it reaches the coding lifecycle but does not reliably obey the targeted verification gate or converge from test feedback.

## Experiment A — 12B, thinking budget 4096

Branch: `exp/12b-rich3278-ab`  
PR: #1 (closed unmerged)  
Kaggle run: `41206261407`

Held constant:

- root coder + verifier AgentTool topology
- coder/verifier prompts
- sampling values except model choice
- 5-minute task budget
- 32 tool calls
- 64 turns

Changed:

- E4B → `gemma-4-12b-it-qat-w4a16-ct`
- required official 12B vLLM HF override

Result:

- 12B booted successfully on L4 ×4, TP=4
- duration: 304.35 s
- tool calls: 3 / 32
- patch: 0 chars
- `test_exit_code=-1`
- `resolved=false`
- verifier never reached
- trace tokens: 20,130 prompt / 7,416 completion / 27,546 total

Primary failure: **F8 BUDGET**. The model spent too much wall time reasoning before meaningful actions and emitted one intended `read_file` as ordinary text rather than a parsed tool call.

## Experiment B — 12B, thinking budget 1024

Branch: `exp/12b-thinking1024-rich3278`  
PR: #2 (closed unmerged)  
Kaggle run: `41215364633`

This follow-up changed exactly one agent variable relative to Experiment A:

- `thinking_budget: 4096 → 1024`

The branch diff also contains the matching contract-test expectation and workflow branch trigger; prompts, topology, runtime logic, and evaluation budgets did not change.

TDD evidence:

- RED run `41215255226`: 25 tests, exactly one expected failure because production still had 4096.
- GREEN run `41215313144`: compile, 25/25 tests, 129-task corpus gate, and restore-CLI smoke all passed after setting 1024.

Kaggle result:

- infrastructure: PASS
- duration: 302.32 s
- tool calls: 18 / 32
- tool mix from trace: 11 `read_file`, 7 `run_command`, 0 `edit_file`
- patch: 0 chars
- `test_exit_code=-1`
- `resolved=false`
- verifier never reached
- trace steps: 27
- trace tokens: 192,885 prompt / 15,722 completion / 208,607 total

Behavioral finding:

Lowering the thinking budget materially increased action throughput (3 → 18 calls), but not useful task progress. The model repeatedly reread the same `rich/ansi.py` regex, repeatedly reconstructed/mis-copied it in ad-hoc Python commands, produced another malformed text-only tool call, and never edited the working tree. Repeated context accumulation caused prompt-token volume to grow roughly 9.6× versus the 4096 run.

Primary failure: **F8 BUDGET**.  
Secondary: **F6 CONTEXT** / **F7 TOOL** (repeated rereads and malformed tool-call emission).

## Decision

**STOP the 12B path for now. Do not merge either 12B branch into the canonical candidate.**

The 1024 follow-up falsified the narrow hypothesis that 12B was failing only because the default 4096 thinking budget was too slow. Reducing thinking did recover tool throughput, but 12B still failed to reach edit, targeted test, or verifier on a clean task that E4B at least progresses through.

The canonical candidate therefore remains E4B root `LlmAgent` + verifier `AgentTool` until a supported structural or training intervention demonstrates a resolved case.

## Constraint on the next intervention

The competition submission schema is declarative-only and resolves tools through a closed host `ToolRegistry`; competitors cannot simply add an arbitrary Python `submit_patch`/verification wrapper. Therefore a future "deterministic verification gate" must not be assumed unless it can be expressed using supported harness primitives.

The next experiment should be chosen from supported agent topology / lifecycle primitives or LoRA/training, and it should explicitly target the repeated E4B F4/F5 verification-and-repair failures.