# 12B `rich_3278` Controlled A/B

## Intent

Measure whether the current unresolved `rich_3278` behavior is primarily an E4B capability/policy-adherence limit rather than a topology problem.

## Controlled variable

Change only the base model from `gemma-4-e4b-it-qat-w4a16-ct` to `gemma-4-12b-it-qat-w4a16-ct` and apply Kaggle Staff's required 12B vLLM `--hf-overrides` mapping to `Gemma4ForCausalLM` / `gemma4`.

Keep unchanged:

- root coder `LlmAgent` + one verifier `AgentTool` topology;
- coder/verifier prompts;
- tool ownership and verifier-only `submit_patch`;
- sampling config;
- `rich_3278` task;
- 5 minute / 32 tool-call / 64-turn budget;
- Kaggle L4 x4 runtime shape.

## Success signal

Primary: `resolved=true` on `rich_3278`.

Secondary evidence: targeted-test adherence, final `test_exit_code`, patch size, tool calls, duration, and whether the verifier submits after a known failing gate.

## Non-goals

No prompt rewrite, third agent, graph-policy change, LoRA, training, task-specific hint, or reference-patch exposure.

## Decision rule

- If 12B resolves the task or materially improves verification behavior, keep the topology and expand to the fixed clean-task sample before adding architecture.
- If 12B fails in the same verification-gate pattern, stop prompt-only iteration on this gate and evaluate a structural verification wrapper/tool policy or training intervention.
