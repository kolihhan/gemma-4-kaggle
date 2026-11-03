# Current ADK compaction probe — 2026-11-03

Status: **VERIFIED against the current official scorer wheelhouse; research/planning evidence only.**

## Question

Can `evidence-before-mutation-v0` safely use a root `SequentialAgent` to hard-code `evidence -> coder` ordering, or does the historical ADK event-compaction failure still exist in the current competition runtime?

## Probe

Cheap GitHub Actions source inspection only; no Kaggle GPU/model inference/task run.

- workflow: `.github/workflows/probe-current-compaction-source-once.yml`
- run: `41624178623`
- job: `125877217844`
- current official wheelhouse downloaded from `metric/gemma-4-developer-agent-wheelhouse`
- relevant versions observed:
  - `google_adk-1.36.1`
  - `adk_submission-0.2.13`
  - `swegemma-0.2.11`

The workflow read Python sources directly from wheel archives; it did not install the scorer/model stack.

## Result

The historical failure path is still present verbatim in current `google_adk 1.36.1`.

`google/adk/apps/compaction.py` currently contains the equivalent of:

```python
if not isinstance(agent, LlmAgent):
    raise ValueError(
        'No LlmAgent model available for event compaction summarizer.'
    )
```

The source probe reported:

```text
EXACT_OLD_ERROR_PRESENT=1
```

Therefore a root `SequentialAgent` is **not a safe competition design** while event compaction is configured without an explicit custom summarizer. The old root-compaction failure cannot be treated as fixed merely because the ADK/wheelhouse version changed.

## Design consequence

Retire the provisional implementation-plan choice of:

```text
root SequentialAgent
  -> evidence LlmAgent
  -> coder LlmAgent
```

Use a root `LlmAgent` so the harness can obtain a compaction summarizer model.

The smallest two-role treatment remains:

```text
root evidence LlmAgent
  -> coder LlmAgent
```

Structural safety properties:

- root evidence agent has no `edit_file`, `write_file`, or `submit_patch`;
- coder is the only role with mutation/submission tools;
- root gathers a bounded pre-edit witness and then transfers to the coder;
- because `run_command` can still mutate, zero-diff-before-coder remains mandatory and trace-audited.

This does **not** make transfer itself deterministic: transfer is still model-controlled. A compliance smoke must therefore verify that the root actually transfers and that no pre-coder workspace mutation occurs.

## Causal-control consequence

For the topology-matched null-handoff B arm:

- use the same root evidence `LlmAgent` and same coder;
- keep the same root reasoning/tool work;
- make the B coder read the original task through session-state templating but use `include_contents: none`, hiding the root evidence/history;
- C uses the same topology but allows the coder to receive the evidence-stage history/handoff.

This keeps model stages/topology matched while varying whether the coder receives the pre-edit evidence information.

## Decision

- Do not implement a root `SequentialAgent` under the current scorer wheelhouse.
- Keep `evidence-before-mutation-v0` provisional while Reliability-v1 ref `57921371` is pending.
- Correct the implementation plan before any future treatment branch is created.
- Re-check this runtime assumption if the official wheelhouse changes materially before implementation.
