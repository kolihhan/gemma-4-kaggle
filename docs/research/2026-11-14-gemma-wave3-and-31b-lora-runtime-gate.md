# Gemma 31B — third frozen external F2P wave and exact LoRA runtime gates (2026-11-14)

## Why this matters

Primary outcome is **new officially verified Kaggle resolution strictly above 0.180**, not training data volume, synthetic learning loss, or number of notebook jobs. Official [coding competition timeline](https://www.kaggle.com/competitions/gemma-4-developer-agent) states December 2, 2026 23:59 UTC final submission deadline; November 12 was the *separate paper track*. Official [coding model rules](https://www.kaggle.com/competitions/gemma-4-developer-agent) permit LoRA adapters bundled as `adapters/<name>/{adapter_config.json,adapter_model.safetensors}` and referenced by the root `agent.yaml`. The existing champion remains **0.180 (#58183466)**, not surpassed in this work.

## Wave 3: prespecified, actual Docker F2P

We used a **new fixed source-window** NVIDIA Open-SWE-Traces v2.0 `sweagent` viewer rows 30–53 inclusive, 24 records. Algorithm preregistered **take first 12** that pass source `resolved=1`, Python language, permissive source-repo license, nonempty model-produced patch, assistant+tool trace and actual `hf_dataset_name=Scale-SWE`. No replacement after observing outcomes. Source selection code: `scripts/freeze_scale_swe_wave3.py`; [real GitHub F2P run #43604539933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43604539933), max four concurrent CPU Docker jobs, all twelve terminal SUCCESS as workflows.

**Eight** independent source F2P successes, with baseline FAIL and NVIDIA *model patch* PASS in same isolated source Docker: indexes **1, 3, 4, 5, 6, 7, 9, 10** (all JUnit errors 0; after-patch tests count between 4 and 9). **Four** task-level failures: indexes **0, 2, 8, 11**, with pytest F2P failure still present after patch, no environment/JUnit error. These are outcomes of source-specific tests, **not** Kaggle hidden or public score.

| Cohort | Externally source-labelled candidate fixes | Independently source-replayed F2P passed | Model F2P failed | Setup/apply blocked |
|---|---:|---:|---:|---:|
| NVIDIA source rows 6–17 | 8 | 6 | 2 | 0 |
| NVIDIA source rows 18–29 | 8 | 5 | 1 | 2 |
| NVIDIA source rows 30–53, first 12 admissible | 12 | **8** | **4** | 0 |
| **Total** | **28** | **19** | **7** | **2** |

This is a **source-ordered, success-label-conditioned pilot**, not a random estimate of external labels, and not benchmark performance. Previous [two-cohort exact ID/repo overlap #43603066062](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43603066062) established original 16 unique task IDs/15 source repos. Wave3 inter-cohort exact task and repo overlap **has not been verified**. A subsequent train/holdout split must operate by repository and exclude all public competition dev tasks, all known prior experiment IDs, and overlap across the new wave.

## 31B LoRA compatibility has distinct evidence levels

Google's official [Gemma 4 QAT variant guidance](https://ai.google.dev/gemma/docs/core) documents matching `31B -qat-q4_0-unquantized` (trainable BF16 QAT weights) and `31B -qat-w4a16-ct` (vLLM inference compression). A public [31B W4 adapter](https://huggingface.co/eexian/gemma4-31b-w4-weighted-reasoning-lora) exists, but is third-party training evidence, not our adaptation result.

[Authenticated CPU JSON-only exact architecture comparison #43604885619](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43604885619) terminal SUCCESS:
- exact Google base QAT unquantized and W4A16-CT config share `Gemma4ForConditionalGeneration` architecture and all inspected language model structural keys (no mismatch in hidden size, layer count, attention heads, etc.).
- W4 serving quantization config is `pack-quantized`; QAT unquantized train config lacks quantization config.
- Public PEFT example config has `peft_type=LORA`, `task_type=CAUSAL_LM`, rank 16 and alpha 16; its target-module field is a string, not a list, so the first static parser had to be corrected. **Do not assume target policy equivalence or model compatibility from this alone.**

[Authenticated Kaggle resource check #43605147992](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43605147992) terminal SUCCESS: **22.74 h GPU** remaining at the time of the check. The exact Kaggle official model instances include QAT unquantized 31B variation 2 and compressed-tensors 31B variation 2. No GPU was used in those checks.

**First actual model execution gate launched:** [private synthetic one-step 31B QLoRA Action #43605569270](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43605569270), with a single private Kaggle L4 model mounting `google/gemma-4/transformers/gemma-4-31b-it-qat-q4_0-unquantized/2`. The script `kaggle/gemma31b_qlora_one_step_smoke.py` attempts NF4 4-bit load, rank-4 LoRA on q/v projections, one forward/backward/optimizer step with **synthetic issue text**, then PEFT adapter `.safetensors` export. **No real source sample or competition test data is trained on; no official Kaggle submission.** The run was still **in progress** at the last documented check, so no success/adapter artifact/model behavior has yet been authenticated. This is a hardware and API smoke, **not** a candidate solver train or scorer improvement. Do not relaunch it while queued/running.

## Method decision

- **Local bottleneck hypothesis:** validated patch-centric source rows are now available, but the exact Gemma 31B QAT→LoRA training→W4A16-CT inference pathway has not been executed end-to-end.
- **Global bottleneck hypothesis:** the 0.180 champion may primarily fail in requirement grounding, edit generation, tool planning and recovery, not syntax; patch-only SFT may improve a subset or make tool-use worse. Do not treat patch generation loss as hidden task resolved.
- **Restriction:** raw foreign SWE-agent tool-call imitation remains blocked by unverified native ADK feedback equivalence (240/267 action shapes only); the source F2P positive patch-output lane is opened for evidence-based SFT after repo-disjoint serialization.
- **Pivot trigger:** if the synthetic 31B LoRA GPU smoke cannot complete even 1 step, evaluate smaller-model prototype/single-card HF training then re-check exact 31B serving compatibility; if it can, build a *private*, repo-split actual source corpus from only 19 genuine F2P pass candidates and a larger non-overlapping source sample, validate prompts/context/completion-only labels, and train one bounded adapter. Evaluation must compare that trained agent against unchanged champion on genuinely disjoint scored tasks before official promotion.
- **Public data safety:** no raw external task text, model patches, gold/reference patches, test fixtures, private Kaggle model bytes or notebooks were committed to the public repo, new releases, or logs.
