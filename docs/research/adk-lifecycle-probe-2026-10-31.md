# ADK Lifecycle / Verification-Gate Probe — 2026-10-31

## Question

After the E4B root-coder + verifier-AgentTool candidate repeatedly failed the verification/repair gate on `rich_3278`, is there a **supported declarative harness primitive** that can structurally enforce “do not submit a known-failing patch” without returning to an invalid root `SequentialAgent` or inventing unsupported Python tools?

## Sources checked

Current competition wheelhouse, probed directly on 2026-10-31:

- `adk_submission-0.2.13-py3-none-any.whl`
- `swegemma-0.2.11-py3-none-any.whl`

Probe workflow evidence:

- branch: `research/adk-lifecycle-probe`
- successful runs: `41217087061`, `41217195292`
- current source artifact: `adk-lifecycle-probe`

Also checked the current Kaggle competition Overview and Kaggle Staff model/LoRA announcements for mutable competition rules.

## VERIFIED — compiler primitives

### 1. `AgentTool` may wrap a workflow agent, not only an `LlmAgent`

`AgentToolEntry` contains only a `config_path` and `skip_summarization`. The resolver loads that path and validates it through the full `SandboxedAgentConfig` discriminated union, then recursively calls the same compiler before wrapping the result in ADK `AgentTool`.

The union includes:

- `LlmAgent`
- `SequentialAgent`
- `ParallelAgent`
- `LoopAgent`

Therefore a topology such as:

```text
root LlmAgent
  -> AgentTool
       -> SequentialAgent
            -> coder LlmAgent
            -> verifier LlmAgent
```

is schema/compiler-valid in `adk-submission 0.2.13`.

### 2. A root `LlmAgent` may also own workflow sub-agents

`SandboxedLlmAgentConfig.sub_agents` references arbitrary agent YAMLs, and recursive compilation uses the same full agent union. This means workflow agents can also exist under a root `LlmAgent` through ADK sub-agent relationships.

### 3. Callbacks exist in the schema but are effectively unavailable in the competition evaluator

The schema/compiler supports:

- before/after agent callbacks
- before/after model callbacks
- before/after tool callbacks

But current `swegemma` calls `compile_submission()` with:

- tool registry
- model registry
- code executor
- limits / generation constraints
- adapter information

It does **not** pass a `callback_registry`.

With no registry, the resolver returns no callback kwargs. A participant therefore cannot rely on a custom callback to inspect a test result and block `submit_patch`.

### 4. The tool registry is closed and contains the nine harness tools

The evaluator constructs the registry from the bound evaluation context:

1. `run_command`
2. `read_file`
3. `write_file`
4. `edit_file`
5. `submit_patch`
6. `get_status`
7. `get_code_neighbors`
8. `search_similar_code`
9. `get_code_subgraph`

Participant YAML can reference those registered names or define an `AgentTool`. It cannot ship an arbitrary Python tool implementation that wraps `submit_patch` with extra deterministic policy.

## VERIFIED — submission lifecycle

### `submit_patch` is not verification-aware

The current `submit_patch` tool:

1. captures the working-tree git diff;
2. strips protected test files;
3. assigns the diff to `ctx.submitted_patch`;
4. sets `ctx.patch_submitted = True`.

It does **not** inspect the last `run_command`, test exit code, or any verifier state.

The harness checks `context.patch_submitted` after an agent run and terminates the outer agent loop once it is true.

### Withholding `submit_patch` does not prevent an edited patch from being evaluated

If the session ends without an explicit submission, the evaluator checks the working tree. Any remaining diff is captured as a fallback `agent_patch` and sent to verification.

Therefore “tell the verifier not to submit on failure” is useful behavior guidance, but it is **not a hard evaluation gate**. A failing edited diff can still become the evaluated patch if execution ends or the budget is exhausted.

## Assessment of remaining topology options

### Root `LlmAgent` -> `AgentTool(Sequential coder -> verifier)`

**Mechanically supported, but not a justified next performance experiment.**

We already ran the core coder→verifier sequential lifecycle before the root-compaction migration. On the corrected verifier-policy run, the sequence completed and produced a patch before the root `SequentialAgent` later hit the compaction exception. The patch itself was already unresolved (`test_exit_code=1`) and contained a semantic regression; the verifier also ignored the requested targeted gate.

Wrapping essentially the same sequence in an `AgentTool` under a root `LlmAgent` would repair the compaction plumbing, but it does not add a new mechanism that improves semantic verification or blocks a bad submit. The current root-LlmAgent + verifier-AgentTool topology already proved that the model can invoke a verifier; its bottleneck is verifier reasoning/policy adherence, not compiler reachability.

### `LoopAgent`

Supported, with a bounded `max_iterations`, but it has no declarative stop condition tied to “targeted test passed”. It would repeat LLM agents, spend more calls/context, and still leave submit decisions to the model. Current evidence does not justify the added cost.

### `ParallelAgent`

Supported, but concurrent reasoning does not enforce a serial test/repair/submit invariant and does not directly target the observed F4/F5 failure.

### Callbacks / custom deterministic submit wrapper

Not available in the current scorer path as a participant-controlled solution.

## Decision

**STOP topology expansion for the verification gate.**

There is no current supported declarative primitive that turns the observed test result into a hard condition on `submit_patch`. The remaining workflow-agent options add orchestration but not the missing invariant. Another topology smoke would primarily retest already-observed E4B verifier behavior.

The next intervention should target the verifier model behavior itself.

## Next experiment direction — verifier-only E4B LoRA

Use the same E4B base model and current root-coder + verifier-AgentTool topology, but attach a small LoRA **only to the verifier**.

Why verifier-only:

- E4B already reaches repository inspection, editing, tests, and verifier invocation.
- The repeated failure is concentrated in targeted-test selection, interpreting failed verification, repairing from evidence, and refusing premature submission.
- Competition rules allow different LoRA adapters per agent while keeping one common base-model variant.
- Isolating the adapter to the verifier preserves attribution and avoids changing coder behavior at the same time.

Before training:

1. define a leakage-safe train/holdout split of public tasks;
2. identify clean holdout tasks whose gold patches verify under the current local scorer;
3. construct verifier supervision from real diffs/test evidence rather than task answers alone;
4. establish a multi-task base-E4B verifier baseline on the held-out clean tasks;
5. train the smallest adapter that can falsify the hypothesis.

Do not evaluate a trained adapter on any task whose reference patch / test evidence was used in its training examples.