# 2026-11-14 — External patch replay source FOUND: provenance fixed and 2 real git-apply successes

## Evaluated task and comparison boundary

We aim to improve the **Gemma 4 31B coding agent's official Kaggle score above the actual best 0.180**, not to optimize metadata pass counts. No model was changed or trained in this operation and no official competition entry submitted. The new causal hypothesis is that externally sourced, independently correct code repair examples may teach a better patch-writing policy than previously failed optional tools and generic prompt wrappers. No such benefit is established by data-read or application-only tests.

The frozen prospective **data-side** cohort was NVIDIA [Open-SWE-Traces](https://huggingface.co/datasets/nvidia/Open-SWE-Traces) v2.0 / `sweagent` rows 6..17 inclusive: 12 viewer records, eight labeled successful external Python patch candidates. All IDs, model patch bytes and source information were kept inside short-lived GitHub Actions runners; nothing raw was committed, logged, mirrored or used for hidden benchmarking. Earlier CPU gate has 240/267 legal syntax-only action mappings and 0 native ADK feedback-equivalent source tool trajectories.

## Why upstream source join was previously blocked

An earlier [dataset viewer filter attempt #43595992574](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43595992574) returned HTTP 500 for 8/8 and [search attempt #43596279707](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43596279707) failed 2/2 with HTTP 500. These are service availability, **not proof of absent data**.

We built a range-based Parquet source index and **independently verified** the upstream Nebius SWE-rebench-V2 `default/train` consists of 32,079 rows and one 428,839,266-byte Parquet file with **251 row groups**, with HTTP Range 206 and all required provenance fields ([read-only #43597092130](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43597092130)). The subsequent [exact eight-ID Parquet lookup #43597459259](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43597459259) completed on the source file, reading only `instance_id` for 251 row groups (no gold patch). **0/8** exact NVIDIA IDs were present.

**Critical source discovery:** NVIDIA's current README describes **two task sources**, [AweAI-Team/Scale-SWE](https://huggingface.co/datasets/AweAI-Team/Scale-SWE) and SWE-rebench-V2. The NVIDIA table entry describing `instance_id` as “from SWE-rebench-V2” is **not exhaustive for v2.0**. [Authenticated provenance-field probe #43597689110](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43597689110) shows **8/8** frozen records' `hf_dataset_name` are **Scale-SWE**, resolving the source mismatch. Do not imply the Nebius dataset is broken.

## Correct Scale-SWE source join: 8/8 matched

[Public shard metadata Action #43597999965](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43597999965) confirmed **two auto-Parquet files** in `default/train`, total **271,786,997 compressed bytes**. A fresh public Scale-SWE `/filter` query returned HTTP 500 for the first 2 frozen IDs ([#43597877708](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43597877708)); this was bypassed with the same proven columnar HTTP Range method, NOT retried indefinitely.

[Actual source-Parquet join #43598183954](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43598183954) **SUCCESS**, exactly **8/8 NVIDIA frozen successful IDs** uniquely matched to original Scale-SWE metadata:
- Exact issue `instance_id` and `user/repo` equals source repo;
- Valid source **`parent_commit`** and `pr_commit` (40-hex) for fixing/base states;
- Nonempty original `problem_statement`, `image_url`, failing test list and `f2p_patch` or `f2p_script`.
- Both source files had **93 row groups** in total; 49 skipped by metadata min/max, 44 scanned for IDs; projected compressed columns for matched rowgroups **4,779,850 bytes**.
- **Never fetched the gold `patch` column**. Reference diffs are not the NVIDIA model-generated patch and must NOT be used as supervised targets.

These are **replay prerequisites**, not independent patch correctness proof.

## First actual patch application: 2/2 clean on original parent Git commits

[CPU Git source replay check #43598668997](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43598668997) **terminal SUCCESS** on first **2 of 8** frozen source-success rows, in original selection order without cherry-picking.

For each public upstream `user/repo`, the runner initialized a clean ephemeral repo, shallow/partial fetched the exact Scale-SWE `parent_commit`, checked out a detached state, fed the **NVIDIA model-produced patch** (not the reference/gold patch) to `git apply --check`, applied it, and checked `git diff --check`. **Both passed (2/2)**. No source-provided commands, repo code, test scripts, or assertions were executed; raw Git outputs, names, URLs, model patch, source issue/test text, parent SHA and repository folders never entered logs or new public artifacts.

The first workflow attempt [#43598499299](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43598499299) encountered an upstream HTTP error before Git verification. We deduplicated NVIDIA viewer reads from **six to two** and retained the same exact two tasks; the second actual workflow succeeded. We did **not** count the source-access outage as an incorrect patch.

## Explicit conclusions and next high-value experiment

**FACT:** Eight source joins have correct parent Git SHAs and test inputs; 2/2 tested NVIDIA model patches apply cleanly at their matching exact parent Git commits. This is a stronger filter than syntactically plausible Git diffs.

**NOT ESTABLISHED:** Source producer `resolved=1` labels independently reproduce under our environment; whether source images still exist and can execute failing/pass tests; whether 31B QLoRA can learn from this source, fit available hardware, or transfer to competition distribution; any hidden or official score improvement.

**Next:** For at most **one** frozen, patch-application-clean candidate, check source image availability and bounded image size; if available and within CPU memory/disk, run source-defined F2P tests **both before and after** model patch in separate isolated containers, with identical test patches/sandbox. A positive example requires base FAIL and model PASS with no unverified task replacement, while inspecting the producer's licensed task instructions and avoiding gold/reference patch use. Then expand source-disjoint training only on verified positives; do not tune any future competition confirmation tasks with them. No GPU/model training until a diverse clean demonstration set and adapter feasibility check exist.

**Code receipts:** `scripts/probe_swe_rebench_parquet_access.py`; `scripts/join_swe_traces_parquet_source.py`; `scripts/probe_nvidia_swe_source_origin.py`; `scripts/probe_scale_swe_parquet_catalog.py`; `scripts/join_scale_swe_parquet_eight.py`; `scripts/check_scale_swe_model_patch_apply.py`; corresponding pure contract tests and one-shot GitHub Actions.

**Scored official Gemma incumbent remains 0.180, entry #58183466**. No new official submission, GPU usage or training this session.
