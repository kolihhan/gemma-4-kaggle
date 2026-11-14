# Gemma 31B — Semantic Surface terminal and data-driven pivot decision (2026-11-14)

## VERIFIED: frozen real-model result

One official-harness **private** 31B paired Kaggle kernel completed: [Actions #43586412434](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43586412434), 8 task evaluations, successful GitHub conclusion, **not a competition submission**.

- Model: Gemma 4 31B identical weights, sampling, 5m/60 tools/80 turns. Champion ZIP SHA256 `ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b`, candidate ZIP SHA256 `b705301954c8f56a39644b3bde1d24da1213615bf07dac4d2710b1c62251bc69`.
- Tasks: `fastapi_13537`, `fastapi_14479`, `rich_3953`, `rich_3471`.
- Same-task correct fixes: champion **1/4**, treatment **1/4**. Both solve only `fastapi_13537`. Zero rescues/regressions. All eight emit nonempty patches, all eight results completed.
- Mechanism: treatment **0 `load_skill` and 0 `run_skill_script`** observed across 4 tasks. The git+AST tool was real and passed synthetic CPU tests, but the model did not invoke it; its information never influenced the actual repair through this intended mechanism. This is a failure of **optional Skill uptake**, not an empirical test of whether a correctly invoked AST analysis would improve fixes.
- By preregistered gate, **reject promotion**; no re-run or same four-task tuning. No official score or new model training resulted. Existing official best **0.180** (#58183466).

## Retrospective cohort provenance correction

The original pre-run documentation described the four tasks as `uninspected`; this was **too strong**. [Read-only CPU manifest audit #43591055317](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43591055317) validates that **2/4**, `fastapi_14479` and `rich_3953`, already occurred in the older E4B verifier-LoRA **train trace harvest (18 tasks), gold-clean train subset, and targeted-check metadata**. The original four-task rule excluded many known diagnostic IDs but omitted these frozen training-side IDs.

These pre-existing research exposures **invalidate a wholly untouched/novel cohort claim**. This is **not** evidence that their reference patches were supplied to either model during this experiment: no model training was performed in this run, the scoring environment is the official isolated grader, and pilot inputs contain the ordinary task context. We cannot assert broad source independence.

- New `scripts/audit_semantic_surface_exposure.py` scans **only prior task-ID metadata**. It returns the overlap and provides `require_unexposed` to fail closed on any known prior training/old blind-reservation IDs before selecting a future confirmation set. It is a necessary filter, **not** proof that all possible historical exposures were detected.
- The terminal **no improvement / zero uptake** observation still stands. The exposure issue further weakens any efficacy/generalization claim, though the result was already negative.

## Global mechanism pivot: training is not automatically the fix

The old verifier training path offers **0/18 approved positive imitation traces** after independent grader and behavior checks, from [verifier harvest audit](../../docs/evaluation/verifier-lora-training-harvest-v0.md). Of 18 training-side tasks, **12** have gold-clean references in `verifier-lora-training-gold-screen-v0.json`; only **6** have task-targeted hand-built verification commands in `verifier-lora-targeted-tests-v0.json`. Gold reference passing is necessary benchmark integrity, not a correct *agent-tool action sequence* by itself. These old resources were designed for **E4B verifier LoRA**, not same-policy **31B patch-writer SFT**.

**Do not train raw failed tool traces.** That would reinforce broad tests, wrong repair behavior, and ungrounded submissions. Training 31B directly would require model-specific available base weights/QLoRA compatibility, sourced task-only supervision with grader-positive actions, a frozen independent set with no exposure, resource feasibility, and a single factor A/B against the actual 0.180 incumbent. Existing training files/90 training IDs are not automatically 90 valid positive examples.

| Candidate method class | Real evidence | Current decision |
|---|---|---|
| Optional AST code-surface Skill | 0 calls, 1/4 vs 1/4 | **Rejected** in current model-mediated architecture |
| Same model, generic test-first prompt | 2/4 vs 2/4 | **Rejected** |
| Root wrapped Scope/Coder AgentTool | 1 private task, failed to return, no patch | **Rejected as already tested** |
| Smaller 12B model swap | 2/4 vs 31B 3/4, no speed win on same tasks | **Not prioritized** |
| Verifier-only SFT from existing traces | 0/18 approved positives; E4B lineage | **Blocked on supervision, not GPU alone** |
| Coder-policy learning / high-quality trajectory distillation | Model-stage hypothesis fits repeated semantics misses; no clean prepared positive training corpus | **Research lane reopened, NOT validated or launched** |

**Next discriminator:** independently curate a *training-only* set of **complete issue → observed code evidence → independently correct patch** trajectories rather than blindly using reference diffs or failed agents. Assess density/variety, reward validity, and exposure-separated confirmation *before training*. If sufficiently many verified diverse demonstrations are not available, fail closed on SFT/QLoRA and consider another legal base agent/model policy rather than synthetic reward hacking.

**No hidden score inference, no leaderboard tuning, no direct new official submission.**
