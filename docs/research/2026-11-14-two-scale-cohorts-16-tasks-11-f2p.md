# Gemma 4 31B — Two frozen NVIDIA→Scale-SWE source cohorts: independent F2P repair-label audit (2026-11-14)

## Actual goal and boundary

Competition incumbent: **0.180** official public score (#58183466), **unchanged**. This work establishes reliable training data, not an improved Gemma solver or competition submission. The historical optional Skill and generic prompt interventions failed to improve model resolution, so a data-driven change remains a hypothesis. No QLoRA, 31B inference, adapter, or GPU run was launched in the source-data audit.

## Source population, provenance, deduplication

NVIDIA [Open-SWE-Traces v2.0](https://huggingface.co/datasets/nvidia/Open-SWE-Traces) `sweagent` public source rows `6..17` and `18..29` were selected in source order, **12 records per batch**, before executing the corresponding Docker F2P tests. Each batch contained **8** source-provider `resolved=1`, Python, permissively licensed, issue+model-patch+tool-feedback candidates. All 16 candidates' `hf_dataset_name` identifies [AweAI-Team/Scale-SWE](https://huggingface.co/datasets/AweAI-Team/Scale-SWE), not Nebius SWE-rebench. The **original 8** were joined to exact Scale-SWE `parent_commit`/`pr_commit`/`f2p_patch`/`f2p_script`/image via two HTTP-range Parquet shards in [#43598183954](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43598183954). The second eight reused the exact source join and official image test protocol via the same implementation.

[Read-only two-cohort overlap check #43603066062](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43603066062) terminal PASS: **16 distinct source task IDs**, **15 distinct repository names** (one repo repeated across the two cohorts), and **zero task-ID overlaps** between cohorts. The first attempt #43602911329 failed due to a transient Hugging Face viewer HTTP error; a bounded same-cohort retry succeeded. This does **not** prove disjointness from every hidden competition task or a task-independent model validation split. Any future training/evaluation split must group **by repository**, not just exact instance ID.

## Real independent F2P source-success check: 11 passes of 16 frozen examples

All checks were performed on source-specific Scale-SWE Docker images (network disabled, 5GB memory, 2 CPUs, no new privileges, no additional Linux capabilities, ≤1.5GB compressed image manifest), at the exact `parent_commit`, with source F2P tests installed. For each, require pytest baseline exit 1, JUnit failures ≥1 and errors 0; apply **NVIDIA model patch**, then rerun identical source-defined F2P selection and require pytest exit 0, tests ≥1, failures 0 and errors 0. Outputs show only count/status metadata and no code/patch/task names. GitHub Actions run `success` merely means the workflow ran, NOT the patch passed.

| Source cohort | True F2P confirmed | Model F2P failed | Infrastructure/test-patch applicability blocked |
|---|---:|---:|---:|
| Original rows 6–17, 8 eligible | **6** | **2** | **0** |
| New rows 18–29, 8 eligible | **5** | **1** | **2** |
| **Total** | **11** | **3** | **2** |

Receipts: original case 0 [#43599380451](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43599380451); original case 1 model-fail [#43599557316](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43599557316); original cases 2/3 [#43600254972](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43600254972); original cases 4/5/6/7 [#43600411080](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43600411080). All eight new cohort tasks [#43602635913](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43602635913).

New cohort per-case statuses, fixed ordering:
- indices **0, 2, 3, 6, 7**: baseline FAIL → NVIDIA model PASS.
- index **1**: baseline FAIL → model FAIL (JUnit errors 0).
- index **4**: model patch does not apply after the F2P fixture is installed (not a grader result).
- index **5**: F2P developer test patch itself does not apply (infrastructure/test-fixture blocked).

This source sample is small, deliberately source-order and source-success-conditioned, **not a statistically valid 11/16 success-rate estimate for new data**, and not proof hidden Kaggle generalization. Only the **11** locally replay-confirmed source repairs are positive **candidates for training**. They still need rights/context/source disjointness and final serializer validity before being actual SFT training rows.

## Failed reference-fix controls and accurate interpretation

For original source case 1, an isolated upstream reference/gold **evaluation-only** control [#43599819900](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43599819900) recovered FAIL→PASS (5 pytest tests passed), so the chosen fixture can be satisfied by the reference fix even though the NVIDIA model patch fails.

For original source case 4 (fifth in original cohort), the reference-control [#43600610325](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43600610325) *did not reach tests* because gold patch did not apply after installing F2P. Follow-up [source-vs-fixture application diagnostic #43602194451](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43602194451) verified **reference/gold patch fails `git apply --check` on the clean original parent too**; NVIDIA model patch passes apply-check in both clean and post-fixture states. The reference patch touches two paths; the NVIDIA patch one; one path overlaps; the upstream gold patch does **not** directly edit the synthetic F2P file. This rules out “fixture installation alone caused gold patch rejection,” but it does not identify the remaining source patch version/format difference. Treat model F2P fail as an observed model failure under the selected test, and reference integrity as **unresolved**, not as reference PASS or invalid fixture.

## Actual next bottleneck

The source-to-Docker replay mechanism is now real and selective; further repeats of metadata-format audits have diminishing returns. Prioritize scaling an **immutable, repo-disjoint, F2P-verified training-only set**, with clear source/repo/issue license and reproducible train/validation isolation, then a separate check of **exact scored Gemma 31B model checkpoint × QLoRA adapter × Kaggle ADK loading compatibility**. A few dozen examples or lower training loss alone cannot justify official promotion. Evaluate changes through task-disjoint **grader-resolved** 31B tests against the 0.180 incumbent before one controlled official competition submission.

**No raw external source prompt, model diff, reference diff, test code, task ID, license-controlled training artifact, or repository URL was committed to public repo or logs.**
