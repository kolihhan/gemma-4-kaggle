# Verifier-only LoRA v0 — adversarial review

Date: 2026-11-01

## VERDICT

**KEEP WITH SMALL CORRECTIONS**

Verifier F4/F5 behavior is a real, repeated failure mode and a verifier-only LoRA remains a useful controlled falsification experiment. The evidence does **not** establish that verifier behavior is the dominant cause of unresolved tasks, and the previously named nine-task held-out set is no longer a valid final blind set because its traces were manually inspected and used to form the hypothesis.

Do not train/promote against the old nine as final holdout evidence. Treat them as development validation, freeze a separate blind set before adapter training/freeze, and keep the first LoRA A/B otherwise unchanged.

## FACTS

- Active experiment branch at review start: `exp/verifier-lora-v0`, draft PR #4.
- Base model family: `gemma-4-e4b-it-qat-w4a16-ct`.
- Current topology: root coder `LlmAgent` + verifier `AgentTool`.
- First LoRA A/B design keeps coder weights/prompt, topology, verifier prompt/tools, sampling, and runtime/task budget fixed; only the verifier adapter changes.
- Frozen v0 rank is `r=8`.
- Successful base development run `41276731977` evaluated 9 gold-clean tasks: **1/9 resolved**, verifier reached **8/9**, `submit_patch` called **5/9**, and **4/9** submitted after the verifier's most recent relevant test was still failing.
- Verifier testing was biased toward broad tests: **9 broad vs 4 targeted** commands in the recorded diagnostic.
- `rich_3061` and `fastapi_14851` exhausted the 32-call budget; `fastapi_14851` ended with an 11,938-character patch and failed.
- The gold-clean nine contain **Rich 4 + FastAPI 5 + Requests 0**. The two proposed Requests holdout tasks failed gold-control and were excluded.
- The nine base traces have now been manually inspected in detail. Their task-level failures, test choices, premature submissions, and outcomes have influenced the verifier-LoRA hypothesis.
- 12B remains stopped: controlled `rich_3278` trials at thinking budgets 4096 and 1024 produced no useful patch before the task budget; lowering thinking increased tool activity but not progress.
- Current official Kaggle documentation permits 31B, 12B, E4B, and E2B, requires one common base variant per submission, and permits different LoRA adapters per agent/subagent.

## PROBLEMS

### P0 — the old nine are development validation, not final blind evidence

Manual inspection of their base failure traces is adaptive evaluation. They can still measure development behavior and regression, but they cannot provide an independent final estimate of adapter generalization.

### P0 — `8/9 reached verifier` does not prove verifier causal dominance

Reaching the verifier only establishes control-flow reachability. Several tasks arrive with a bad or missing patch, so changing verifier behavior may reduce unsafe submission without increasing resolved tasks.

Conservative trace-based causal-surface diagnostic:

| Task | State entering / around verifier | Diagnostic class |
|---|---|---|
| `rich_3067` | task-aligned small fix; verifier eventually ran targeted `tests/test_highlighter.py`, passed, then submitted; resolved | essentially correct / verification surface |
| `fastapi_14463` | task-aligned shallow-copy fix existed, but no clean passing relevant gate before submission | one narrow repair / verification plausibly useful |
| `fastapi_14986` | task-aligned OpenAPI/Swagger edits, but verifier submitted after failed verification | one narrow repair / verification plausibly useful |
| `rich_3934` | narrow semantic change attempted, failing evidence remained and verifier drifted into changing tests / repeated repair | one narrow repair might rescue, unproven |
| `fastapi_13920` | coder invented a placeholder `is_typealiastype(...): return False`; verifier accepted it after failing tests | fundamentally wrong patch |
| `fastapi_14077` | coder introduced invalid/unstable status-import edits and never reached verifier | coder-stage failure / no verifier surface in this run |
| `fastapi_14851` | speculative invasive rewrite, duplicate imports/handler machinery, 11.9k-char final patch, budget exhaustion | fundamentally wrong patch |
| `rich_3061` | speculative `expand_tabs` rewrite with repeated failed edits; verifier exhausted budget without a verified repair | fundamentally wrong / no clean repair state |
| `rich_3942` | failing Markdown edits; verifier submitted despite failed verification; final evaluator patch was 0 chars | no useful verified patch |

This diagnostic is intentionally about **causal surface**, not gold-patch equivalence. It supports a verifier-only experiment, but it bounds expectations: only a subset of current misses look plausibly recoverable by verifier behavior alone.

### P1 — Requests is absent from development validation

The development set cannot support claims about Requests or broad cross-repository generalization. A blind set should include Requests only if automated gold-control can produce clean eligible Requests tasks; otherwise report that limitation rather than silently substituting a generalization claim.

### P1 — promotion criteria must separate safer refusal from actual resolution

A verifier that stops premature submissions can improve F4/F5 while leaving resolved count unchanged. That is a useful behavioral gain, not sufficient promotion evidence.

## HYPOTHESES

- **H1:** verifier-only LoRA can reduce broad-test selection, repeated repair loops, and submit-after-failure behavior on development tasks.
- **H2:** those behavior changes are large enough to increase resolved-task count on the development set.
- **H3:** the gain transfers to a genuinely blind set frozen before adapter adaptation.
- **H4:** improved verifier discipline does not consume enough extra time/tool calls to erase correctness gains.
- **UNKNOWN:** how many of the current coder-stage failures can be rescued by verifier-only training; the present nine are too small and adaptively inspected to estimate this reliably.

## SMALLEST CORRECTIONS

1. Reclassify the current nine as **development validation**.
2. Freeze a second blind evaluation set from tasks that have not been harvested or manually inspected. Selection may use metadata only; eligibility may use automated harness/gold-control only.
3. Do not manually inspect blind base failure traces or blind reference patches before the adapter is frozen.
4. Keep `r=8` and the current fixed-factor A/B. Do not add a coder adapter, topology change, or hyperparameter sweep.
5. Keep the development nine for behavior diagnostics, but limit claims to Rich/FastAPI.
6. Promote only with resolved-task evidence on the frozen blind set plus F4/F5, targeted-test, premature-submit, and cost diagnostics.
7. If blind evaluation fails, stop verifier-LoRA v0 rather than immediately tuning rank/epochs/LR.

## EXECUTION PLAN

1. Freeze the evaluation-role contract in the repo: old nine = development validation; blind set = pending freeze.
2. Reserve blind candidates from the currently unharvested/uninspected side of the public corpus using metadata-only deterministic selection.
3. Run automated gold-control eligibility screening on those candidates without opening base failure traces.
4. Persist the resulting blind IDs and remove them from any future training/trace-harvest source.
5. Only then build verifier training examples from training tasks and run one `r=8` base-vs-adapter A/B with all other factors fixed.
6. Evaluate development behavior/resolution, then run the frozen blind evaluation once the adapter is frozen.
7. Stop v0 on blind failure; otherwise consider promotion.

## Executed in this review

- Added `docs/evaluation/verifier-lora-eval-contract-v1.json` to make the dev/blind distinction explicit.
- Added `tests/test_verifier_eval_contract.py` to enforce that the inspected nine are development validation, record the missing Requests coverage, require training-harvest/blind disjointness, and block adapter artifacts from the candidate submission while blind evaluation is still pending.

The next safe execution step is therefore **blind-set reservation + automated gold-control screening**, not LoRA training yet.
