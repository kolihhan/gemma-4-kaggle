# 2026-11-12 — Real 31B paired test-feedback audit, zero new inference

## Provenance and completed execution

- Pre-registered matched 31B single native-root comparison: [Action 43057377220](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43057377220), six evaluations on three public-development issues, V2 **0/3 resolved** vs public-prompt-only **0/3 resolved**, each arm **3/3 patches**; scorer `test_exit_code=1` for all six.
- Original safe action-count readback: [Action 43064306933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43064306933).
- Improved conservative feedback audit: [Action 43068582144](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43068582144), **COMPLETED SUCCESS**. This executed only GitHub CPU tests and read an existing private Kaggle output; **no model inference, training, GPU consumption or competition submission**.

## Actual independent feedback-evidence observations

| Safe observation | V2 5min (3 tasks) | Public-prompt 5min (3 tasks) | Total |
|---|---:|---:|---:|
| Resolved | 0 | 0 | **0/6** |
| Trace records available | 3 | 3 | **6/6** |
| Recognized explicit test-runner / inline assertion calls | 0 | 0 | **0** |
| Opaque or unclassified shell/Python commands | 16 | 9 | **25** |
| Run commands with structured nonzero exit metadata | 8 | 5 | **13** |

These **13** nonzero command exits are not necessarily failed tests; commands can fail for environment, repository or non-test reasons. The parser cannot safely classify **25** opaque commands, which may include ad-hoc verification. All six terminal *grader* exits were 1, but hidden grader output is not model feedback and cannot be used to assert model saw or ignored it. Do not equate the action count with the scorer tool-call count.

Individual task statistics are in the safe derived Action artifact; no raw commands, task statements, code, model responses or reference patches are in this PUBLIC GitHub repo.

## Research conclusion and method selection

**Established:** Both matched prompts edited every selected issue, yet resolved none. Neither prompt induced an independently identified explicit test-runner invocation on these six runs; the tool outputs include some failed commands. The test-feedback loop is weakly observable, **not proven absent**.

**Not established:** Semantic patch mistakes are the dominant cause; all commands with nonzero exit are tests; the model had actionable failing assertions; a test-only prompt would resolve any task; PPO/GRPO/SFT would improve hidden performance.

**Do not repeat V4-CGR as a superficial test-first patch.** V4 packaged a generated locked pytest witness and skill-controlled before/after verification; the actual official entry scored **0.15** vs account best **0.18**. Its precise failure mechanism was not isolated, but its real result provides no promotion evidence. V5 mandatory nested Scope→Coder consumed almost all time and produced no patch on its single observed issue.

### Highest-value next experiment, conditional on evidence

1. **Identify model-visible feedback type before designing a new agent:** distinguish structured nonzero command feedback from assertion/traceback, dependency/collection, and script-edit errors *inside private Kaggle execution only*. Export only safe categories and sequence indicators, never raw feedback.
2. If relevant failures reach the model and it continues without correction, test a **single-root feedback-to-repair policy** with an explicit falsifier (subsequent targeted test passes AND a disjoint issue resolves) against pinned V2, controlling total time/tool budget. No nested AgentTool, no synthetic witness stage by default.
3. If the main limitations are missing issue requirements, inadequate code generation, or no available verification oracle, **do not** spend more on prompting; reopen data-driven adaptation / model-capacity or a different benchmark, with a validated training/eval split and reward feasibility.
4. Keep the best officially scored account entry **0.18** (58183466) and the separate date-gated attributed external V10 code submission unchanged. There is **no new scored submission from this audit**.

### PPO / GRPO restriction (reopenable)

PPO/GRPO remain **not started** because no trustworthy clean success/failure reward corpus or measured sample efficiency benefit exists at the current 31B compute budget. Reopen if independent task-based policy failures and a reliable reward loop exist, or if supervised trajectory/repair adaptation produces transferable evidence that warrants a larger training investment. RL is not prohibited forever; it is not justified merely by failing six development examples.

## Privacy and reproducibility

- Script: `scripts/audit_paired_31b_feedback_v2.py`.
- Synthetic tests: `tests/test_audit_paired_31b_feedback_v2.py`.
- CPU-only readback workflow: `.github/workflows/audit-paired-31b-feedback-readonly-v2.yml`.
- No `submission/` edits, no new public task/trace mirrors, no competition API submit call, no model weights, no private grader content.
