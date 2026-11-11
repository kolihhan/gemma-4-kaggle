# Four prequalified public-development repair tasks — frozen before a new 31B run

Date: 2026-11-12 MYT. **Public-development exploratory set, NOT blind / NOT a Kaggle leaderboard prediction.**

## Independence and historical validity

The exact four tasks were chosen using independent upstream PR descriptions and previously recorded **gold-pass / no-op-fail** metadata in `docs/evaluation/capacity-v0-{gold,noop}-screen-2026-11-04.json`, not by current model results. All four had gold pass and no-op fail on Nov 4; those results are **historical** and will be rechecked against the current official SWE-Gemma wheelhouse. Their public code and upstream explanations are known; no reference patch may be shown to an LLM.

| Frozen public-dev ID | Upstream PR | Why candidate |
|---|---|---|
| `fastapi_14458` | [FastAPI #14458](https://github.com/fastapi/fastapi/pull/14458) | Explicit issue: class used as a dependency vs an instance having async `__call__` |
| `fastapi_15589` | [FastAPI #15589](https://github.com/fastapi/fastapi/pull/15589) | Explicit header underscore/hyphen contract with `convert_underscores` |
| `rich_3894` | [Rich #3894](https://github.com/Textualize/rich/pull/3894) | Reproducer included: non-string unusual `__qualname__` attribute |
| `rich_3905` | [Rich #3905](https://github.com/Textualize/rich/pull/3905) | `Progress(disabled=True)` should not emit an extra blank line |

**Important:** The PR body is **not** the actual benchmark statement. It may contain spoilers, implementation hints or details omitted in the Kaggle-mounted task text. We have **not** inspected these four task statements from the private scorer at selection time. The CPU integrity screen will emit only length, URL flags, pointer-risk and official no-op/gold outcomes; these signals cannot fully certify information sufficiency.

## CPU-only hard gate before any further model compute

Use the existing official `verify_task` path, six? **eight** independent calls (2 per issue): empty candidate patch vs the reference gold patch. Keep raw issue statements, reference patches and test outputs **inside one private Kaggle CPU-only Notebook**. Do not export them into public GitHub or to model prompts. Treat every non-completed task as a negative gate, no task substitution.

A task is locally clean iff:
- gold passes and no-op fails under the **same current** scorer epoch;
- its benchmark-visible issue statement is sufficiently specific, determined later using an explicitly documented rubric and sanitized metadata (not just PR reputation);
- no evidence of source/wheel import shadowing, leaking reference, or inaccessible external issue-only description.

If the four fail to yield at least **two** clean candidates covering both repositories, stop before 31B inference. If they do, a future real-model comparison must freeze the denominator and budgets before any score run; compare **correct issue resolution** and total runtime, not merely patch presence, calls or local tests. Keep both successes and failures. No cherry-picking after seeing model outcomes.

The 2026-11-11 prior three-task comparison was **0/3 vs 0/3**, but independent [CPU task controls](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43070401519) found Requests gold fail and Rich 68-char URL pointer. It cannot be treated as a full three-task clean estimate.

## Why not PPO now

Training an RL repair policy with a broken or non-discriminating reward would optimize unreliable labels. The smaller defensible experiment is to establish an independent, source-applied gold/no-op working sample, then test one actual repair-loop mechanism against a frozen baseline. **PPO/GRPO/LoRA are not banned:** reconsider once a reliable reward and train/validation split exist. Gold patches must never be passed into the agent.

Code for this stage:
- `scripts/render_clean_four_integrity_cpu.py` reuses the existing official-score-controlled private three-task runtime, substituting exactly the frozen four IDs.
- `tests/test_render_clean_four_integrity_cpu.py` enforces historical eligibility and air-gapped CPU metadata.
- `.github/workflows/clean-four-integrity-cpu-once-20261112.yml` is a one-off, push-guarded workflow; no GPU, inference, or competition submission.
