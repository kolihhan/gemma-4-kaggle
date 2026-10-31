# E4B Coder → Verifier v1 Design

## Intent

Test the smallest specialization justified by the `rich_3278` traces: separate patch creation from final verification/submission so the coding agent cannot terminate the task after a known failing test.

## Evidence

Across four clean `rich_3278` experiments, localization was fast and tool restrictions reduced patch size from ~4 KB to 319 chars, but the single E4B agent repeatedly called `submit_patch` after explicitly recognizing targeted-test failure. Removing `submit_patch` entirely made the trajectory worse: it expanded into destructive edits and context overflow. The remaining bottleneck is therefore lifecycle/repair discipline, not basic repository location.

## Approaches considered

1. **More single-agent prompt rules.** Rejected for this experiment: the model already ignored explicit “do not submit while targeted verification is failing” instructions.
2. **Root coder with a reviewer AgentTool.** Smaller structural change, but the root still owns `submit_patch` and can ignore the reviewer verdict; it does not enforce the observed failure boundary.
3. **Sequential coder → verifier. Chosen.** The coder edits/tests but has no `submit_patch`; the verifier sees the same workspace, independently inspects the diff/tests, may make one evidence-backed narrow repair, and exclusively owns `submit_patch`.

## Architecture

Root `SequentialAgent` runs exactly two E4B `LlmAgent`s in order:

- **Coder** — receives `{problem_description}`, inspects, edits, and runs targeted verification. Tools: `run_command`, `read_file`, `edit_file`, `get_status`, plus code-intelligence tools. No `write_file`, no `submit_patch`.
- **Verifier** — receives `{problem_description}`, starts from the coder’s existing working tree, inspects `git diff`, runs the narrowest relevant test, and may make one evidence-backed narrow repair. It exclusively owns `submit_patch`. If targeted verification passes, it submits the verified patch. If verification still fails after the bounded repair and no concrete next fix remains, it removes any clearly regressive extra changes, keeps the smallest defensible patch, and submits once to terminate the task rather than causing the outer harness to nudge and re-run the whole sequential pipeline.

Both agents use `gemma-4-e4b-it-qat-w4a16-ct` and the existing sampling config. The task budget remains 5 minutes / 32 tool calls / 64 turns. No LoRA, loop agent, third agent, or task-specific answer leakage.

## Goals

- Make premature submission structurally impossible for the coder.
- Preserve a small, interpretable patch/edit surface.
- Force one independent verification/repair pass before any submission decision.
- Give the verifier enough authority to fix one concrete regression instead of merely commenting on it.
- Change only orchestration/submit ownership; keep model and budget fixed for attribution.

## Non-goals

- No graph-policy experiment.
- No model-size comparison.
- No LoRA/training.
- No task-specific Rich regex hint or reference-patch exposure.
- No generic multi-agent framework beyond two sequential roles.
- No repeated sequential reruns after an unresolved verifier pass.

## Success criteria

1. Repo validation passes with a root `SequentialAgent` and exactly two sub-agents.
2. Static contract proves only the verifier exposes `submit_patch`, and neither role exposes `write_file`.
3. Current scorer compiles/runs the submission on the same `rich_3278` smoke path.
4. The trace shows the coder cannot submit and the verifier performs an independent diff/test gate before submission.
5. Compare `resolved`, patch size, tool calls, duration, test exit code, and dominant failure class against the four prior runs.
6. If still unresolved, do not add another orchestration layer until the new trace identifies a distinct bottleneck.
