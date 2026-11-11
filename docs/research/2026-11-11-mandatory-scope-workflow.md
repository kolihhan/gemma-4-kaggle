# Mandatory Scope → Coder — new structural architecture, 2026-11-11

**Status:** executable experimental builder, structural tests passed. Official ADK CPU lifecycle gate running; no real 31B repair-rate result, no scoring submission, no extra GPU. See the final GitHub Actions result before treating this as compiler-verified.

## Correct the older research inference first

The original **optional** Contract & Impact 31B candidate was already tested on a four-task public-development matched pilot on 2026-11-09. It resolved **0/4**, identical to Budget-Fit V2's **0/4**, produced 3/4 nonempty patches vs 4/4 for V2 and used 78 vs 107 native calls. There were no conclusive Skill tool-call events. [Paired data and exact limits](../../experiments/architecture-contract-impact-v0/31b-paired-pilot-decision-2026-11-09.md). This experimental package is **not** competitive evidence, and the optional-Skill model must not be promoted or merely relabeled V5.

## New architectural mechanism, independent from the old candidate

**Missing capability:** explicit contract information needs to survive reliably into the source writer's context. In the old candidate it was an optional model-decided Skill, so a model could skip the entire analysis action. Tuning the wording cannot impose a control-flow edge.

**Intervention:** declarative, root `SequentialAgent` from the official ADK compiler, with exactly two child `LlmAgent` stages:

1. **read_only_scope**: native read-only tools `read_file`, `get_status`, `get_code_neighbors`, `search_similar_code`, `get_code_subgraph`; **no** `run_command`, `edit_file`, `write_file` or `submit_patch`. Must produce `output_key: scope_packet` which labels explicit requirements, observed source facts, impacted candidate paths, unknowns, and next discriminating action. It can be wrong.
2. **sole_patch_writer**: receives `{scope_packet}` via actual ADK session-state templating; has the full nine V2 native tools; owns edits, bounded tests, final diff, and `submit_patch`.

This design is **not a custom Python tool** or an unsupported callback. It is an official declarative ADK workflow, independent of any model-decided Skill call, custom trainer or additional API. The root cannot access tools itself; stage 1 cannot call mutation tools by declaration. The model can still hallucinate an incorrect impact map and the coder can ignore it. **Control-flow enforcement is not semantic correctness.**

**Source and frozen resource contract:**
- [builder](../../scripts/build_two_stage_scope_coder_candidate.py), [structural regression tests](../../tests/test_two_stage_scope_coder.py), [official scripted-ADK lifecycle probe](../../scripts/probe_two_stage_scope_coder_official.py)
- Exact Apache-2.0 third-party Budget-Fit V2 ZIP is validated as source, used for the same single allowed 31B base model, nine native tools and writer sampling.
- One shared **5 minute / 28 tool calls / 80 turns** task envelope; the mandatory first stage consumes resources from the same cap. There is **no** additional model weight, adapter, GPU hardware or hidden reference/test data.

## Competing predictions / falsifiers

| Hypothesis | Observable prediction | Reject / pivot if |
|---|---|---|
| H1: optional Skill non-uptake blocks useful analysis | Stage order and packet delivery observed in the actual compiled ADK events without any model-chosen Tool call | ADK root workflow or state handoff fails in official harness |
| H2: notes lead to more complete patches | On disjoint tasks, matched to V2, fewer missed explicit requirements / affected entry points and higher independently resolved issue rate | Equal/worse resolved rate, or extra stage consumes time without benefit |
| H3: root SequentialAgent is compatible | Official runner and compaction/continuation path complete successfully | Prior root SequentialAgent context-compaction bug recurs, or the harness requires a root model field |
| H4: model generation already dominant | Even accurate, retrieved facts fail to produce correct source edits | Reopen coder adaptation or bounded candidate search; do not pile on more analysis |

**Known risk:** The repo's prior 2026-10-31 [ADK lifecycle probe](../research/adk-lifecycle-probe-2026-10-31.md) reports root `SequentialAgent` context compaction failure and absence of a user-definable callback registry. This candidate is therefore **not promotable just because `Runner.run_async` works once**. It needs a real harness-compatible compaction test before paying for new 31B inference. A root `LlmAgent` that wraps the workflow in an `AgentTool` is a possible fallback, but since tool invocation is model-mediated it is not automatically equivalent to mandatory execution.

**Decision sequence:** Static tests → actual compiler and ADK lifecycle with scripted model → official harness compaction/nudge compatibility gate → only if both pass, one clean matched-budget private 31B task pilot with instrumented tool events and independent issue-grading; control remains frozen V2. No extra official Kaggle submission on this evidence. Competition V4 submission `58222227` remains independent and must be scored before deciding to replace it.

## What would change the decision

Success of synthetic CPU tools proves the stage is structurally reachable, not that Gemma 31B will infer the right contracts. The next eligible pilot must retain all failures/timeouts/empty patches, use preselected issue IDs not tuned from the old four FastAPI/Rich examples, disclose both arm costs and independent resolved counts, and prohibit leaking reference patches into the agent sandbox.

Do not promote a 0/4→0/4 or “fewer calls” outcome; do not burn another public Kaggle submission to see if the model follows a stage. No claim of novelty, accepted paper result, or improved leaderboard score is made.
