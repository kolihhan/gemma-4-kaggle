# Mandatory Scope → Coder — new structural architecture, 2026-11-11

## Final wrapped-root compaction gate — 2026-11-11 14:33 MYT

**PASS on official ADK 1.36.1; actual automatic EventCompaction verified.** [Actions 42972954885](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42972954885) passed six focused static tests, generated the unchanged wrapped candidate SHA256 `25a656d65d580d3ed1bf4c54ab5a622a05afe231f1dd46fb2d861749fd08a1bd`, exercised the typed root `mandatory_scope_then_patch` AgentTool call, actual nested `read_file → edit_file → submit_patch` in a synthetic workspace, and observed the `scope_packet` arrive at the Coder.

**Compaction evidence:** `5` user invocation IDs, `1` EventCompaction **already stored in ADK's session** before the direct diagnostic call to its official sliding-window function, and still `1` afterward. Thus it was **automatically created by the actual runner**, not manufactured by the test. The Runner's returned event stream contained zero compaction events; treating that stream as the authoritative session ledger was a measurement bug. The official v1.36.1 `_run_compaction_for_sliding_window` is a coroutine which appends to `session_service`, not an async generator. [Earlier test 42972449767](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42972449767) failed incorrectly because it required a *new* event after one already existed; latest test counts stored events both before and after. No further compaction summary was forced.

**Decision:** Keep the **wrapped-root** structural candidate for consideration. The **direct root SequentialAgent** remains **REJECTED** because it deterministically threw `No LlmAgent model available for event compaction summarizer` on the same official ADK release. Root `LlmAgent` provides compatible compaction and confines mutation capabilities to the mandatory nested workflow *if called*. Model compliance is still optional at the root, and correctness remains **UNMEASURED**. No real 31B inference, GPU training or Kaggle code submission occurred during these CPU gates. Any future private clean-task paired 31B pilot must directly record root AgentTool uptake and actual independent resolved issues under matched total time/call budget; failing uptake or no gain rejects the topology.

---

## Measured official ADK outcome — root SequentialAgent REJECTED (2026-11-11 14:11 MYT)

- [CPU run 42969323985](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42969323985) **SUCCESS** with a scripted one-turn ADK Runner: `read_file → edit_file → submit_patch`; the `scope_packet` reached the writer; candidate SHA256 `dbf2ae3a536edc322dd827194ea548d9ae9f2ec7ec92b2e5251086229ad7b27f`. **This was NOT a proof of root app compaction.**
- [Compaction stress 42970282094](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42970282094) **FAILED as expected** after five actual user invocations under the official 1.36.1 ADK App, with `ValueError: No LlmAgent model available for event compaction summarizer.` The direct root SequentialAgent architecture is **NOT eligible** for 31B inference or official submission. The failure confirms the historical root-compaction issue and refutes a false green CPU-only promotion.
- **Separate next arm:** [LlmAgent-root wrapped builder](../../scripts/build_wrapped_scope_coder_candidate.py) and [official nested/compaction probe](../../scripts/probe_wrapped_scope_coder_official.py) put the same inner mandatory Scope→Coder `SequentialAgent` behind the root's **only `AgentTool`**. Any native source edit must pass the inner workflow because no direct editing/shell/submit tools are declared at the root. The root still decides whether to invoke the tool, so adoption is a live empirical risk. The wrapped arm has not been independently scored by Gemma 31B; do not call it a performance improvement.
- The wrapped candidate's first [CPU run 42971014203](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42971014203) compiled the bundle and executed nested `read_file → edit_file → submit_patch`; an overstrict actual-compaction-event assertion failed on its short synthetic session, without any missing-root-model error.
- **Follow-up definitive gate:** [official CPU Actions 42971506685](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42971506685) **SUCCESS** on the pinned `adk_submission 0.2.13` / `google-adk 1.36.1` wheelhouse. All six static tests passed. Candidate ZIP SHA256 `25a656d65d580d3ed1bf4c54ab5a622a05afe231f1dd46fb2d861749fd08a1bd`. Real compiled ADK function events `call:mandatory_scope_then_patch → result:mandatory_scope_then_patch`; nested real native tool calls `read_file → edit_file → submit_patch`; scope packet read by coder. The **exact official default compaction summarizer model-resolution function** successfully resolved the `LlmAgent` root model, unlike the rejected Sequential root. Critically, **`actual_compaction_events=0`** and `compaction_fully_exercised=false` despite five short invocations, so genuine long-history summarization remains **NOT VERIFIED**. Do not call this a scored breakthrough, proof of root workflow compaction under large context, or proof of Gemma 31B uptake. No GPU, new Kaggle Notebook push, training, or competition submission occurred.
- **Next gate:** a genuinely emitted compaction event under workload large enough to need summarization, then a single disjoint matched-budget private 31B pilot with real AgentTool uptake and independently resolved issue metric before promotion. The root may skip its one AgentTool; this is a fundamental model-compliance risk, not fixed by the CPU scripted model.

---


**Historical original design context:** The direct root `SequentialAgent` candidate failed real compaction, and the separately wrapped root `LlmAgent` candidate now passes actual official CPU auto-compaction as recorded above. Neither candidate has measured independent Gemma 31B issue-resolution gains.

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
