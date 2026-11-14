# 2026-11-14 — SWE-agent v2.0 → Gemma ADK tool-action compatibility, real CPU evidence

## Goal and evidence standard

Research goal: improve real 31B coding-agent **grader-resolved tasks** beyond existing official best **0.180** (#58183466). This report examines whether NVIDIA Open-SWE-Traces v2.0's independently labelled successful Python repair trajectories can teach *legal* Gemma ADK tool actions **without duplicating external tool dialects**. No model was trained or scored; these are data-conversion gates only.

Source [NVIDIA Open-SWE-Traces](https://huggingface.co/datasets/nvidia/Open-SWE-Traces), public `v2.0/sweagent` split, **fixed consecutive viewer rows 6..17 inclusive (12 rows)** chosen before inspecting their contents. Eight meet the preliminary row gate: `resolved=1` integer, Python, eligible declared repository license, not in four known Gemma public-development repos, nonempty model-produced diff, both assistant and tool feedback. Labels come from the source dataset, **not our own grader**. Pilot is nonrandom and too small to estimate generalization. No issue text, commands, paths, model patch bytes, full trace, or tool feedback were printed or committed.

## Actual source structure

[Read-only shape probe #43594105297](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43594105297), **PASS**:
- 8 eligible successful source rows have 267 assistant function tool calls: **195 `bash`**, **56 `str_replace_editor`**, **16 `submit`**.
- Editor calls: 29 `str_replace`, 21 `view`, 6 `create`.
- 259 tool reply messages; structurally `role=tool`, keys `content,role,tool_calls`. The bridge cannot assume their original contents are the ADK tool JSON response contract.

[Initial strict bridge #43594521130](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43594521130), **PASS**:
- **211/267** action signatures provisionally mapped: `bash(command)` → `run_command(command)` (195), and `submit()` → `submit_patch()` (16). All 56 editor paths initially rejected: they were absolute paths outside `/workspace`.
- All 8 failed full-trajectory syntax conversion; 0 direct ADK training traces authorized.

[Source-path metadata diagnostic #43594725381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43594725381), **PASS**:
- Of 56 editor paths, **54** were under `/testbed/` and 2 under another absolute root (no path values logged).
- [SWE-agent's official editor config](https://github.com/SWE-agent/SWE-agent/blob/main/tools/edit_anthropic/config.yaml) explicitly documents absolute paths such as `/testbed/file.py`; [its implementation](https://github.com/SWE-agent/SWE-agent/blob/main/tools/edit_anthropic/bin/str_replace_editor) implements strict editor semantics. This is *source framework* evidence for a conditional path rebase, not proof that every external environment and Gemma's sandbox are equivalent.

[Revised STRICT documented root rebase #43594949739](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43594949739), **PASS**:
- Normalize only `/testbed/<relative>` (and native `/workspace/<relative>`) into ADK's repository-relative `filepath`, reject other absolute paths and path traversal.
- **240/267 = 89.9%** syntax-level provisional mappings: 195 `run_command`, **29 `edit_file`**, 16 `submit_patch`. **4/8** eligible trajectories have **all tool calls** provisionally mappable at the syntax level.
- Remaining **27/267** unconverted = 19 `view` with incompatible output/truncation semantics; 6 `create` with file-existence semantics not yet verified; 2 editor paths not under the documented root.
- Even for mapped `edit_file`, upstream editor requires unique exact substring replacement while ADK uses exact/flexible/regex fallbacks. ADK's `run_command` sandbox, stdout truncation, lifecycle and `submit_patch` effect are not guaranteed identical. An argument renaming alone cannot guarantee correct physical edits.
- **259 source tool replies; zero with the observed ADK `status: ok|error` JSON envelope** in this sample. Thus native feedback reconstruction is completely unverified. All real transcript tool actions and outputs stayed in-memory in private Actions runner; only aggregate statuses and counts printed.
- **0/8 full, semantically approved ADK training trajectories**; separate from `4/8` *syntax-only fully convertible actions*. Do not claim `4/8` are ready for SFT or use the original alien tool-feedback strings as native `status` responses.

## Reproducible implementation

- `scripts/probe_sweagent_action_shapes.py` + `tests/test_probe_sweagent_action_shapes.py` — bounded 12-row metadata; no raw values exported.
- `scripts/bridge_sweagent_adk.py` + `tests/test_bridge_sweagent_adk.py` — actual source event parsing, allowlisted tool names, strict in-memory argument transformation, safe paths, unsupported editor-mode and tool-result refusal, no training-record export.
- `.github/workflows/gemma-sweagent-adk-bridge-cpu.yml` — exact source sample and CPU tests. The first attempt timed out while reading large Hugging Face JSON; fixed by splitting the **same 12 rows** into two 6-row reads. A syntactically passing test isn't counted as a scored model gain.
- Independent official harness contract: `HARNESS_README.md` sections 6.1–6.3. Native ADK `read_file` has 150-line/10k-character caps and independent return JSON; `edit_file` has distinct matching semantics; `submit_patch` finalizes an agent run. All code inside the bridge deliberately marks converted actions `*_semantics_unverified`.

## Scientific decision and pivot

1. **Do not discard external training as impossible:** this real data provides 240 candidate action shapes; a documented path rebasing step repairs 29 of 56 editor-action translation failures.
2. **Reject raw end-to-end tool-trajectory imitation for now:** none has proven feedback equivalence; simply changing tool names would fabricate what the model should observe and may train a policy that fails the live harness.
3. **Most promising next alternative** is an **answer-/patch-centric curation lane**: from independently source-verified successful public-project examples, select issue + public repository context + externally independently graded correct patch, with licensing, task/source-disjointness, true local tests and exact output target checked. This can avoid pretending that source-tool replies are ADK-native. It is a *research candidate*, not currently a ready-made 31B LoRA dataset.
4. Training-weight feasibility **is materially different from data availability**. [Google's Gemma model guide](https://ai.google.dev/gemma/docs/core) confirms 31B QAT unquantized checkpoints exist; [Google's QLoRA guide](https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora) provides a base 31B-compatible training recipe. These public sources do **not** establish a runnable memory-safe QLoRA job on the user's current Colab/HF/Kaggle quota, nor a compatible deployment adapter on the exact Kaggle scored compressed-tensors 31B base. No GPU/training initiated.
5. Before any expensive model fine-tune or official submission, validate actual examples and one short adapted training/inference round-trip on **source-separated training/eval**; promote only on a measured independent increase of grader `resolved` under the full competition runtime and task budget. Do not reuse this 8-row source pilot as an evaluation set after adapting to its content.

**Restriction:** No direct tool-call SFT from unverified external feedback. **Why:** 0/259 compatible observed ADK-shaped response envelopes, 27 unconverted actions, and different editor command semantics. **Pivot trigger:** trace-level feedback schema translation backed by native ADK execution and correctness-preserving test, or patch-only supervision that does not require foreign tool feedback. **Status: ACTIVE, reversible.**


## Additional verified patch-only alternate: source task→model fix pairs (same cohort)

[Final CPU source schema Action #43595475020](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43595475020) **PASS** on the same 12 preselected SWE-agent v2.0 rows: **8/8** preliminarily source-success-admitted rows have **one nonempty `role=user` string of 1,000–4,999 characters**, plus a syntactically consistent source `model_patch.patch` unified diff. Seven model-produced patches are **1,000–4,999 characters**, one **20,000+ characters**. Metadata includes `model_patch`, `reference_patch`, `category`; source `instance_id` and `repo` exist as top-level columns. **Never use `reference_patch` as a model training target**. There is no separately exposed `base_commit` or `snapshot_id` in this tiny sample's allowlisted metadata; task `instance_id` may be sufficient to find external SWE-rebench-V2 source snapshots later, but this has not been verified. We did not save source user prompt, either diff, tool trace or task ID values.

This proves only *a feasible text/patch **data shape***. It does not prove the user message is a standalone accurate issue statement (it may contain scaffold instructions), the source checkout can be reconstructed, the model patch independently applies/passes the current benchmark, or that the resulting short-answer task teaches the multi-turn 31B coding agent to use its legal tools. **0 independently replayed patches, 0 true verified local training examples** at this checkpoint.

Implementation: `scripts/probe_external_patch_supervision.py`, `tests/test_probe_external_patch_supervision.py`, `.github/workflows/gemma-external-patch-schema-cpu.yml` (GitHub Actions run link above). Continue only on a provenance-separated set, with source repository snapshot and real regression test replays; no raw source content in the public GitHub repository or logs.


## Source-environment linkage attempt — blocked by public API (not a negative data result)

The upstream [Nebius SWE-rebench-V2](https://huggingface.co/datasets/nebius/SWE-rebench-V2) documents `instance_id`, `repo`, `base_commit`, `problem_statement`, `test_patch`, `FAIL_TO_PASS`, `image_name`, and installation configuration, which are **the right primitives for independent source snapshot + grader replay**. It is a potential join by the external NVIDIA `instance_id`, not evidence the sampled eight IDs have already been matched.

- New source-ID-safe code `scripts/probe_external_source_join.py`, `tests/test_probe_external_source_join.py`, `.github/workflows/gemma-swe-source-join-cpu.yml` forbids exporting raw issue/patch/test text; it verifies that joined records agree exactly on ID/repo/license and include a 40-hex base SHA, nonempty failing tests, test patch, issue and image reference before counting as replay candidates.
- The initial real [Actions #43595812022](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43595812022) succeeded mechanically but **all eight public /filter requests were unavailable**, no matches. A one-variable safe HTTP-status diagnostic [#43595992574](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43595992574) confirms **HTTP 500 for 8/8** equality queries, not no matching rows. Hugging Face [Dataset Viewer /filter documentation](https://huggingface.co/docs/dataset-viewer/en/filter) warns that larger datasets may have partial indexing; here the specific HTTP 500 means the service did not return a valid query result.
- **Decision:** do not retry identical failed HTTP queries, pretend the 8 source commits were found, use the upstream gold patch as the model target, or launch 31B QLoRA. Independent patch replays are still **0**, and verified 31B-admissible training rows still **0**. If pursuing this data lane, first use a distinct source-access path (read-only streaming indexed Parquet, snapshot/commit export, or a tested alternate public endpoint) with a frozen small cohort, clear resource cap and non-exporting provenance checks.

This failure is a **public data access bottleneck**, not a statement about SWE-rebench-V2 scientific validity, NVIDIA source label reliability, or the potential of patch-centric SFT.
