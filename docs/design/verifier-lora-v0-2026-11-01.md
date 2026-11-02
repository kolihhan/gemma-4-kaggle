# Verifier-only E4B LoRA v0 — 2026-11-01

## Intent

Target the observed E4B F4/F5 failures without changing coder behavior or adding orchestration.

F4/F5 is a verified recurring failure mode: broad test choice, weak interpretation of failing evidence, repeated repair loops, and premature `submit_patch`. **It is not yet proven to be the dominant cause of unresolved tasks.** Several development tasks reach the verifier with fundamentally wrong or missing patches, so verifier-only training may improve safety/discipline without proportionally improving resolved count.

## Chosen approach

Run one controlled verifier-only PEFT LoRA falsification experiment while keeping:

- base variant: `gemma-4-e4b-it-qat-w4a16-ct` for every agent;
- root coder: unchanged, no adapter;
- coder prompt: unchanged;
- topology: root `LlmAgent` + verifier `AgentTool`;
- verifier prompt/tools: unchanged for the first A/B;
- sampling: unchanged for the first A/B;
- runtime/task budget: unchanged;
- LoRA rank: frozen at `r=8` for v0.

Only the verifier adapter changes.

For adapter training, use the matching unquantized QAT E4B instruction checkpoint (`google/gemma-4-E4B-it-qat-q4_0-unquantized`) rather than a different model family. Current official Kaggle documentation permits different LoRA adapters per agent/subagent while requiring one common base variant per submission.

## Why this instead of alternatives

### A. Verifier-only LoRA — keep for v0

It provides the cleanest attribution for a real observed verifier failure mode. The experiment is justified as a falsification test, not because verifier causal dominance has been established.

### B. Coder + verifier LoRA — reject for v0

Too many variables for the first A/B. Some coder failures are real, but changing both components would make attribution poor.

### C. More topology / prompt changes — stop for now

The current scorer exposes no participant-controlled deterministic callback/tool gate tied to test success. `SequentialAgent` / `LoopAgent` add orchestration but do not enforce the missing invariant, and prior prompt iterations showed diminishing returns.

### D. 12B retry — reject for v0

Controlled 12B runs at thinking budgets 4096 and 1024 both failed to produce a useful patch within the task budget. Do not reopen 12B without materially new evidence.

## Evaluation roles

Canonical machine-readable contract: `docs/evaluation/verifier-lora-eval-contract-v1.json`.

### Development validation — existing gold-clean 9

The nine tasks from run `41276731977` are **development validation**, not final blind holdout evidence. Their base traces were manually inspected task-by-task and shaped this hypothesis.

Coverage:

- Rich: 4
- FastAPI: 5
- Requests: 0

Use them for behavior diagnostics and development resolved count. Do not claim Requests or broad cross-repository generalization from them.

### Blind evaluation — must be frozen before training/promotion

Freeze a separate blind set from tasks that have not been harvested, manually inspected, or otherwise development-seen.

Allowed before adapter freeze:

- task metadata for deterministic selection;
- automated harness/gold-control eligibility screening.

Not allowed before adapter freeze:

- manual inspection of blind base failure traces;
- manual inspection of blind reference patches;
- adapting training examples, prompts, topology, or task selection based on blind task-level outcomes.

Once blind IDs are frozen, remove them from every training/trace-harvest source.

If Requests cannot produce clean blind tasks under automated gold-control, record that limitation rather than manufacturing a generalization claim.

## Development causal-surface result

`8/9 reached verifier` establishes reachability, not verifier causal dominance.

Conservative diagnostic from the already-exposed development traces:

- essentially correct / strong verification surface: `rich_3067`;
- one narrow repair / verification plausibly useful: `fastapi_14463`, `fastapi_14986`, `rich_3934`;
- fundamentally wrong or no useful patch state: `fastapi_13920`, `fastapi_14851`, `rich_3061`, `rich_3942`;
- no verifier reached: `fastapi_14077`.

Full evidence: `docs/evaluation/verifier-lora-v0-adversarial-review-2026-11-01.md`.

This bounds expectations: verifier-only training has real causal surface, but it cannot rescue every current miss.

## Supervision format

v0 trains verifier behavior, not task-answer memorization.

Preferred sources, in order:

1. real base-E4B verifier traces from training tasks;
2. gold-patch verification traces on training tasks;
3. controlled negative examples from training tasks only.

Target behavior:

1. inspect current diff/status;
2. choose the smallest relevant verification command;
3. treat failing verification as evidence;
4. do not submit after a known failing relevant test;
5. make at most one narrow evidence-backed repair when justified;
6. rerun the relevant gate;
7. submit only after passing relevant verification.

Blind reference patches and blind traces are never training data.

## Training v0

Use PEFT/TRL SFT with the smallest adapter that can falsify the hypothesis:

- base: matching unquantized QAT E4B instruction checkpoint;
- LoRA rank: `r=8`;
- alpha: `16`;
- dropout: `0.05`;
- task: causal LM;
- save adapter only (`adapter_config.json`, `adapter_model.safetensors`);
- no merged model in the competition bundle;
- no hyperparameter sweep before the first clean A/B.

Do **not** start v0 training until the blind evaluation IDs are frozen and excluded from training/trace harvest.

## Evaluation contract

Compare base verifier vs adapter verifier with coder, prompt, tools, sampling, time limit, task-call limit, topology, and base family unchanged.

Required evidence:

1. development verifier behavior;
2. development resolved-task count;
3. independent frozen blind evaluation;
4. F4/F5 reduction;
5. targeted-test behavior;
6. premature-submit behavior;
7. runtime/tool-call cost.

Training loss is not a promotion metric. `1/9 -> 2/9` by itself is not sufficient evidence.

## Cheap falsification option

Before LoRA, run at most one verifier-specific reasoning/sampling falsification **only if** the harness can isolate that setting without changing coder behavior or topology. Do not grid-search and do not change multiple variables. If verifier-specific control cannot be isolated cleanly, skip it.

## Stop rules

Stop verifier-LoRA v0 if any of these hold:

- adapter cannot boot/serve reliably in the official Kaggle runtime;
- a clean blind set cannot be frozen without adaptive inspection;
- adapter improves training/development behavior but fails the frozen blind evaluation;
- runtime/tool-call cost erases correctness gain.

On blind failure, stop v0 rather than immediately sweeping rank, epochs, learning rate, or other knobs.

## Non-goals

- no coder adapter in v0;
- no 12B retry;
- no new agent topology;
- no leaderboard claim before an actual submission score;
- no blind task/reference evidence in training.
