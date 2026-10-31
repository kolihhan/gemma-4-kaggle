# Verifier-only E4B LoRA v0 — 2026-11-01

## Intent

Target the observed E4B F4/F5 failures without changing coder behavior or adding more orchestration.

The current E4B coder already reaches inspect → edit → test → verifier. The remaining repeated failures are concentrated in the verifier: selecting a useful test, interpreting a failing result, making a narrow repair, and avoiding premature `submit_patch`.

## Chosen approach

Train a small PEFT LoRA only for `swe_e4b_verifier` while keeping:

- base variant: `gemma-4-e4b-it-qat-w4a16-ct` for every agent;
- root coder: unchanged, no adapter;
- topology: root `LlmAgent` + verifier `AgentTool`;
- prompts/tools/sampling: unchanged for the first adapter A/B;
- canonical `main/submission/`: untouched until the adapter beats the base verifier on held-out tasks.

For adapter training, use the matching unquantized QAT E4B instruction checkpoint (`google/gemma-4-E4B-it-qat-q4_0-unquantized`) rather than training against a different model family. Kaggle staff explicitly states that LoRA adapters for the newly supported smaller variants should be trained against the corresponding unquantized variants, and the competition allows different adapters per agent while requiring one common base variant.

## Why this instead of the alternatives

### A. Verifier-only LoRA — chosen

Best attribution. It changes the component where the failure is observed and preserves the coder that already reaches useful edits.

### B. LoRA on coder + verifier — rejected for v0

Too many variables. A gain or regression would be hard to attribute, and coder behavior is not the current dominant bottleneck.

### C. More topology / prompt changes — stopped

The current scorer exposes no participant-controlled deterministic callback/tool gate tied to test success. `SequentialAgent` / `LoopAgent` add orchestration but do not enforce the missing invariant. More prompt wording has already shown diminishing returns.

## Data split

Public task data is used only for development. The split is task-level within seen repositories, not a claim of repository-level generalization.

### Never-holdout development-seen set

The existing 10-task deterministic diagnostic sample is permanently excluded from the LoRA holdout because it has already influenced system design:

- `rich_3278`
- `rich_2725`
- `rich_3930`
- `httpx_3672`
- `fastapi_14361`
- `fastapi_14266`
- `fastapi_14609`
- `requests_6592`
- `requests_7502`
- `requests_6757`

`httpx_3672` is also excluded from v0 training/evaluation because its current gold-control path is harness-confounded.

### Holdout v0

Select 12 tasks from the remaining corpus:

- FastAPI: 6
- Rich: 4
- Requests: 2

Selection must be deterministic and spread across reference-patch-size buckets. The manifest stores only task IDs, repo, bucket, and split metadata. No holdout reference patch or holdout verification evidence may be used to construct training examples.

Before model evaluation, every proposed holdout task must pass a gold-reference control under the current official verifier (`resolved=true`, `test_exit_code=0`). Tasks that fail the gold control are marked harness-confounded and replaced deterministically from the same repo/bucket when possible.

## Supervision format

v0 trains verifier behavior, not task-answer memorization.

Training examples should mirror Gemma 4 tool-calling conversations and emphasize real verification state transitions:

1. inspect current diff/status;
2. choose the smallest relevant test;
3. read test output as evidence;
4. if the test fails, do not submit;
5. make at most one narrow evidence-backed repair when justified;
6. rerun the targeted gate;
7. call `submit_patch` only after a passing relevant verification.

Preferred sources, in order:

1. real base-E4B verifier traces from training-split tasks;
2. gold-patch verification traces on training-split tasks;
3. controlled negative examples derived only from training-split tasks.

Reference patches are labels for data construction only and must never be exposed during blind base/adapted evaluation.

## Training v0

Use PEFT/TRL SFT with the smallest adapter that can falsify the hypothesis:

- base: matching unquantized QAT E4B instruction checkpoint;
- LoRA rank: start at `r=8`;
- alpha: `16`;
- dropout: `0.05`;
- task: causal LM;
- save adapter only (`adapter_config.json`, `adapter_model.safetensors`);
- no merged model in the competition bundle.

Do not tune hyperparameters before the first held-out A/B. If v0 cannot improve verifier behavior on clean holdout tasks, stop before increasing rank/epochs.

## Evaluation contract

Compare base verifier vs adapter verifier on exactly the same clean held-out tasks with coder, prompt, tools, sampling, time limit, and topology unchanged.

Primary metric:

- resolved tasks.

Secondary diagnostics:

- verifier reached;
- targeted vs broad test choice;
- submit after last failing test;
- repair count;
- tool calls;
- elapsed time;
- final patch size;
- F4/F5 counts.

Promotion requires a real held-out improvement, not lower training loss.

## Stop rules

Stop verifier-LoRA v0 if any of these hold:

- adapter cannot boot/serve reliably in the official Kaggle runtime;
- gold holdout is too confounded to form a clean multi-task set;
- adapter improves training traces but not clean held-out resolution/F4/F5 behavior;
- runtime/tool-call cost increases enough to erase any correctness gain.

## Non-goals

- no coder adapter in v0;
- no 12B retry;
- no new agent topology;
- no leaderboard claim before an actual submission score;
- no use of holdout reference patches/test evidence in training.
