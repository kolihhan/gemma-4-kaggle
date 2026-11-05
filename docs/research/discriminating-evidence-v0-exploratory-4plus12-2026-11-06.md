# Discriminating Evidence v0 — reduced 4+12 exploratory contract

**Created 2026-11-06 MYT; research-only. No performance experiment has run.**

## Why this reduction exists

The previously preregistered 4 pilot + 24 confirmation variant at [discriminating-evidence-v0-gate-2026-11-05.md](discriminating-evidence-v0-gate-2026-11-05.md) failed its prospective replacement-buffer gate (0 Rich / 2 FastAPI spare). That failed protocol remains as historical evidence; do not edit it retroactively.

A new **4 pilot + 12 exploratory** protocol is **a separate pre-outcome design**, not a post-hoc reinterpretation of results. No 31B task evaluation, GPU run, or new Kaggle submission has occurred after original metadata selection. Reuse the exact parent hash-ordering and take a nested prefix of each per-repo series. The new design does not claim statistical power for improvement or transfer. Its purpose is to establish feasibility, discover if the mechanism can exist at all, and justify or reject a properly replicated later experiment.

## Candidate freeze and safeguards

Source: scripts/discriminating_evidence_preflight.py plus scripts/discriminating_evidence_exploratory.py. Input is **only eleven previously committed metadata/source-summary files**, NOT task statements, patches, test outputs, raw traces, or hidden score feedback.

- Initial ranked parent pools: 14 Rich and 16 FastAPI; exclude every already-known train-harvest, dev, blind, topology, capacity-v0 4+12, gold/no-op screened and public-summary exemplar ID.
- Feasibility: the exact **two Rich and two FastAPI** originally preselected as parent pilot. They stay designated pilot; cannot promote candidate with pilot results.
- Exploratory follow-up: **six Rich and six FastAPI**, the first six from the parent confirmation ordering for each repo.
- Prospective replacement queue: the rest, **six Rich and eight FastAPI**, taken strictly in frozen rank order. These are eligibility replacements only; never replace tasks based on their statements, model failures, outcomes or task difficulty.
- Never touch capacity-v0's separate 4+12 cohort in docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json, nor any verifier-LoRA reserved set.
- The selector's full manifest of metadata IDs, selection digest, and source hashes must be committed prior to issue data/eligibility/model inspection. A CI-printed selection is an intermediate reproduction artifact, not proof of task cleanliness.

**Initial status: NO_GO_HISTORY_AND_ELIGIBILITY_UNCHECKED.** The lower prospective count clears the *candidate pool* capacity condition only. Not blind-certified; not gold/no-op eligible; not authorized to launch a model.

## Fixed scientific mechanism and arm identity

H1: discriminating pre-edit evidence may improve root-cause selection and repair; merely running more tools does not establish it.

- **A: exact unchanged no-training 31B Kaggle reference** `57983156` (Public 0.08), ZIP SHA256 `42ac2e15e42118b51a2e8835ad5fc5e51cbbdfb472e65e3b8720b38b69738820`. Reuse scored package bytes and inherited settings; do not edit.
- **B: topology-matched null information handoff**. Same 31B initial evidence stage and same coder as C, same tool and total time limits, but coder is not allowed to see the diagnostic observations or any proxy of them in history, session, workspace files, or transfer metadata. It receives only original task and a fixed non-informative placeholder where required.
- **C: same two-stage topology with evidence transfer**. C coder receives bounded, pre-edit evidence, including two distinct hypotheses, one discriminating observation and a falsifier. C and B evidence work must be identical until handoff.

Both B/C must keep root `LlmAgent` (avoid known root SequentialAgent compaction failure), total 300s, 32 tool calls, 64 turns, 31B model, sampling 0.2/0.95/4096 thinking, no adapters. Read-only tool restrictions exclude explicit edit/write/submit from evidence role, but `run_command` can mutate; require git diff zero before coder. Do **not** invent unsupported callback or custom Python wrappers.

**Major unresolved feasibility**: ADK `output_key` is saved on final agent response, while an `LlmAgent` transferring to a sub-agent might not have finalized an evidence packet. Compiler support for `output_key` and `include_contents: none` does not prove the claimed transfer or B isolation. Before any GPU evaluation, demonstrate actual handoff via available model-free lifecycle inspection/probes and ultimately a four-task pilot; if isolation cannot be guaranteed, mark B/C **NO-GO**, do not silently weaken control.

## Gate sequence (frozen)

0. Recompute exactly this manifest; Git-history audit fixed to the instant **before** original 4+24 metadata selection (2026-11-05 15:59:38 UTC); inspect known public artifacts/releases metadata for exposure; run gold-pass and no-op-fail checks with only derived result flags. All four pilot and twelve exploratory candidates must be eligible or deterministically replaced by next frozen queue candidates in their own repo. No replacement by issue text or model outcome. If fewer than six+six are eligible, do not resample a new holdout without a separate contract. Audit cannot certify unrecorded human viewing.
1. CPU-only validate B/C YAML under the latest official scorer wheelhouse; prove presence/absence of packet and original task in respective coder contexts, no agent-root compaction failure, and unchanged **total** budget. Schema compilation alone is not a model-lifecycle smoke.
2. Four pilot tasks only if all prior gates pass **and** authorized inference resources are available. Evaluate A/C for transfer and zero-diff compliance, without treating pilot resolution as quality evidence.
3. If pilot demonstrates isolation, safe transfer and tolerable cost, run 12 independent paired A/C on **the same frozen denominator**. Do not inspect per-task results until both complete. Only if C has at least **three net additional solves over A** and no prohibitive cost do we run the **already specified** B on those same tasks, also without intermediate trace inspection.
4. For exploratory mechanism support, demand at least **two net additional solves over B**, valid and reused discriminating witnesses, no more than 10% extra mean wall time, and no budget / coverage regression. These counts are **heuristic triage criteria** on twelve cases, **not** statistical significance or publication-quality causal proof. Replicate on a genuinely new independent larger denominator before claiming improvement or pursuing additional Kaggle LB submissions.

Pilot cannot be reused to tune instructions before the frozen 12 without invalidating downstream independence; if fixing a compiler/lifecycle bug requires changing B/C behavior, refreeze config and reevaluate denominator provenance first.

## Falsification and interpretation

- No clean data or unsupported lifecycle: stop before costly model work.
- B/C packet leakage or nonzero pre-coder diff: stop; not a controlled experiment.
- Evidence packet exists but never reaches coder: mechanism not implemented.
- C <= A, or enough failures/timeouts to negate net value: reject complex two-stage route for now.
- C > A but C ~= B: stage/context effect, **not** evidence handoff.
- C > A and C > B with traced witness usage: only exploratory support; not a repeatable solution yet.
- Any result limited to Rich/FastAPI must not generalize to Requests or hidden issues.

## Operational limits

Do not train, LoRA, launch a Kaggle GPU, publish raw competition data, mutate `submission/`, submit a Kaggle score, alter old capacity/blind denominators, or claim improvement. CPU-only static checks/history/eligibility are in scope. Continue in this research branch and update its `NOW.md` after verified actions.

## Verified CPU progress (2026-11-06 MYT)

- Frozen metadata-only task list: [discriminating-evidence-v0-exploratory-selection-2026-11-06.json](../evaluation/discriminating-evidence-v0-exploratory-selection-2026-11-06.json). Selection SHA256 `20bca18b905161123ba0054d058a4f2b963cce6526c67b29e0175a81d17cc343`, nested in exact original parent sorted selection (no resampling).
- [Run 42064561734](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42064561734): 593 preselection Git source revisions / 14 refs scanned, 0 metadata candidate ID mentions outside allowed metadata paths. This **does not** certify all historical data exposure, and is not a model outcome.
- B/C schema renderer: [scripts/discriminating_evidence_schema.py](../../scripts/discriminating_evidence_schema.py) dynamically reconstructs exact scored baseline 31B ZIP hash, preserves eval/sampling budgets, creates equal-size B/C packages in /tmp with a single differing `prompts/coder_stage.md` packet interpolation. Unit tests confirm the intended only informational difference.
- **Implementation refinement before model evaluation:** root `LlmAgent` wraps `AgentTool(SequentialAgent(evidence LlmAgent -> coder LlmAgent))`. Evidence agent can write `output_key: evidence_packet` on its **final** response before sequential coder begins. Root remains an `LlmAgent` for compaction. This is stronger than relying on root-to-child transfer before root `output_key` is available, but remains unproven at model runtime.
- [Run 42065388698](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42065388698): **official scorer wheelhouse software downloaded (41 wheels); `validate_directory()` and `discover_declared_models()` passed for BOTH B and C**. This is software schema validation, not a real compiler invocation with bound tool/model registries, an ADK lifecycle trace, or a quality result.
- A prospective private **CPU-only** gold-reference eligibility sweep of all thirty frozen IDs was launched by [workflow discriminating-evidence-gold-cpu](../../.github/workflows/discriminating-evidence-gold-cpu.yml). It embeds only metadata IDs, privately hydrates competition data, publishes only derived pass/fail flags, uses no model, no GPU, no training and no competition submission.

**Remaining gates:** private gold result, same-repo preregistered replacement handling, no-op-fail eligibility, B/C bound compiler/lifecycle isolation, and 31B pilot feasibility. Do not infer model quality or a successful evidence transfer from these CPU-only results.
