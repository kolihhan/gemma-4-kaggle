# NO-GO — Causal-location root SequentialAgent, 2026-11-22

**Status: REJECTED BEFORE GPU OR OFFICIAL SUBMISSION.**

This branch staged a scout-then-coder root `SequentialAgent` and a possible
official-scoring script. No scoring workflow or submission GO marker was
created, and neither candidate nor scorer was launched.

## Evidence that invalidates the planned topology

The parent research branch's **existing authentic harness experiments** had
already isolated a root `SequentialAgent` failure:

- [Existing five-invocation official ADK stress run #42970282094](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42970282094):
  `ValueError: No LlmAgent model available for event compaction summarizer.`
- [Existing 31B matched real private grader #43808826562](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43808826562):
  mandatory coder-then-reviewer root SequentialAgent **1/3** versus original
  single-agent **1/3**, 0 rescues, 0 regressions, +7 grader tool calls.
- The current proposal reverses stage order, so the second result is **not**
  direct evidence against scout-then-coder quality; the **root compactor**
  failure still applies because it is the same root class.

## Decision

Do not run `scripts/submit_gemma_causal_sequence_once_20261122.py` and do
not create its GO marker. A root `LlmAgent` with an `AgentTool` wrapping
`SequentialAgent` was also already built and CPU validated in this repository,
but actual 31B uptake remains unproven. Merely rewrapping does not meet the
user's demand for differentiated, effective research.

**No GPU, no Kaggle score submission, no official score improvement.**

This is a deliberately preserved rejected branch; not a completed architecture
result. Before any future expensive Gemma test, use a distinct mechanism with
real causal evidence, not an already-known invalid or no-rescue topology.
