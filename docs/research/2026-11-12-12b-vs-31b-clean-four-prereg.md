# Predeclared capacity hypothesis: Gemma 4 12B vs 31B on four clean dev repairs

Date 2026-11-12 MYT. **This is public-development-only exploration, NOT a Kaggle leaderboard submission or blind research estimate.**

## Why this test is different

Previously, six matched V2/prompt-only 31B runs all failed and all produced patches. A contemporaneous official gold/no-op check showed **one out of three task evaluations had a failing reference patch** and Rich had a 68-character URL pointer, invalidating a clean three-task model-policy interpretation. Separately, an official private CPU control on [Action 43076716956](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43076716956) established four specific issues with **gold pass and no-op fail**: FastAPI #14458/#15589, Rich #3894/#3905 (two repositories). The benchmark-visible lengths are respectively **591, 1247, 1974, 1672 chars**. None were chosen using the upcoming 12B/31B outcomes.

Staff [authorizes 12B and 31B individually](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287), but prohibits mixing variants in one submission. This study uses **two separate private notebooks**, each declaring only **one model**, each running the same original code-repair workflow.

**Question:** With identical single-root Budget-Fit V2 system prompt, tool set, sampling, tool cap, turn cap and five-minute per-issue clock, does 31B produce measurably more correct patches than 12B, and what time/tool cost follows? Could smaller model efficiency alter expected 12-hour full-task success despite lower capacity?

## Immutable candidate source and one-variable contract

- Attributed Kaggle source `lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2` original zip SHA `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`.
- 31B 5-minute ZIP SHA `0dc7dc782a7be300388ab53937d53e9dfe9bd4679a82b21971557d846fc1778c`.
- 12B 5-minute ZIP SHA `4e065d23011664459fbf8b64cbe6750f15ffb37f693198844f6d533fd3acf669`.
- Control and treatment differ **ONLY in `agent.yaml` model name**, not in `prompts/system.md`, `configs/sampling.yaml`, tools, or `eval_config.yaml`.
- Both are **single-root, no LoRA**, **5min/28calls/80turns**, tensor parallel 4 and the same L4x4 class.
- Each notebook uses exactly one model source; Kaggle official `swegemma.evaluate.Evaluator` handles the four tasks. Gold patches never appear in generated agent inputs.
- [Exact ZIP build CPU Actions 43077446108](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43077446108) PASS, no GPU or submission.

## Resource and safety limits

One controller checks authenticated GPU remaining `>=8h`, with a fail-stop before inference if below. Push at most one private 12B and one private 31B notebook (sequentially, not concurrently). No official competition submission; do not consume daily score slot; no training. Each kernel gets at most 4 issue evaluations x five agent minutes + model startup + verification and is bounded by a kernel and GitHub Actions ceiling. If the first kernel fails or produces incomplete records, **do not** launch the second. No retry or restarts of an identical kernel.

Output from the private notebooks can contain sensitive trace data: the controller extracts **only allowlisted metadata** (task ID, resolved flag, patch length flag/count, tools, duration, grader exit status, error *class*), never task text, reference patches, agent messages, raw tool arguments, grader output or credentials into the public repository.

## Primary / secondary outcomes, preregistered

Primary = `resolved` count per arm, exact task denominator 4. Errors and timeouts are **not dropped** and count as unresolved.

Secondary = tool calls and elapsed time by arm, nonempty patch ratio, error class, grader exit code. Model initialization and workflow overhead reported separately from task duration; do not assume real Kaggle 12-hour throughput from one four-task developmental slice.

Decision:
- A 12B/31B difference in correct fixes **on these four** is preliminary evidence about model policy/capacity. No statistical claim or automatic official submission, even if one arm wins 1 task.
- 0/4 vs 0/4 means this sample fails to discriminate, and does not justify reflexively increasing model size or training PPO.
- If 12B edits faster but not correctly, efficiency alone does not count as improvement.
- If 31B materially more accurate despite slower runtime, test resource-adjusted expected completion on a larger fresh independent gold/noop-valid sample before choosing it for hidden scoring.
- If either model fails at model mount/server/tool parsing, label **infrastructure**, not quality.
- PPO/GRPO remain possible only with reliable training rewards and enough compute, not merely after a prompt-only 0/3 failure.

## Independence and exclusions

These are public upstream PRs and previously screened tasks. **Not blind and not generalizable to private repositories.** Only a single independent model-size variable changed. All four tasks from the frozen clean cohort are scored; no cherry-picked exclusions after seeing model output. Avoid unapproved direct leaderboard submission and avoid any new competition dataset public mirror.
