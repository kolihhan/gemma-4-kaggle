# Gemma 31B patch checkpoint result and reproduce-before-edit experiment

## Score and failure evidence

The authenticated Kaggle account best is **0.180**, ref `58183466`. FastThink (`58294231`) is COMPLETE at **0.120**. It reduced thinking budget from 4,096 to 2,048 at the same 5-minute/60-call cap. The score argues against promoting that candidate and cannot identify hidden per-task failures. On November 14 at 10:16 MYT the account had one official slot. [Authenticated ledger](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43184026828/attempts/3)

In the private checkpoint run, the exact champion (`ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b`) solved 1 of 4 public-development issues. Each reference patch passed; each no-op failed. The agent edited at 87.1 s on the solved issue and finished in 159.9 s. The other three hit 300 s. On two failures with measurable phases, 587.6 of 600.0 s were outside observed tool execution, including model generation, context handling and waits. A third failure produced no diff. The two patched failures had eight distinct intermediate alternatives; five graded alternatives failed, with three ungraded by the fixed sampling cap. There was no observed recoverable patch on these failures. [Authenticated private evaluation](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43471068879)

## Frozen paired experiment

- **Mechanism.** Spend one short tool call testing the issue's exact executable example or named existing check when available. Reuse that command after editing. This can distinguish a true repair from a patch that changes the right file while preserving the wrong behavior. An absent or setup-blocked check sends the agent directly back to editing. No additional agent, tool, fitting, or workspace test file is involved.
- **Why this test.** Patch retention had no measured rescue in the checkpoint sample. FastThink had worse official performance. The incumbent already seeks early edits and optional post-edit checks. This experiment adds pre-edit behavioral feedback and repeated evaluation of the same evidence, one change to the instruction text.
- **Test.** Identical pinned 31B weights, official evaluator, 5 minutes, 60 tool calls, 80 turns, sampling, root, and tools. The control is the scored 5-minute/60-call configuration. The only treatment file diff is in `prompts/system.md`. Treatment archive SHA-256 `8d25aafe6e11fc6045243d23fb2ab80fedd583feaa095a0e2799e338897052c0`. Explicit tasks are `fastapi_15800`, `rich_3518`, `rich_4075`, `fastapi_14492`, from the previously screened public development task pool and disjoint with the immediately preceding checkpoint and EarlyEdit panels. The provider rechecks gold/no-op integrity. Arm order alternates, with each repository represented in both orders. The developer did not inspect sample issue text or gold diffs to choose the rule.
- **Decision.** Compare official-grader resolutions on all four paired tasks, including trial errors. Collect patch availability, duration, tool calls and recognizably repeated verification commands. Command metrics are lower bounds because shell edits and checks outside the recognized patterns can be missed. No net increase rejects promotion from this panel. Positive net resolutions with evidence of the targeted behavior justify a fresh matched confirmation, with cost checked against the competition-wide budget. These four issues cannot establish hidden-score generalization. The pilot makes no competition submission.


## Verified outcome — 2026-11-14 11:18 MYT

**Action:** [#43547354883](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43547354883), completed successfully at 03:18 UTC. The pinned 31B L4×4 private paired experiment ran all eight official-grader evaluations; all generated nonempty patches and no evaluator errors occurred.

| Task | Champion | Reproduce first | Recorded pre-edit checks (champion / treatment) | Same-command pre/post |
| --- | --- | --- | --- | --- |
| `fastapi_15800` | 0 | 0 | 0 / 0 | 0 / 0 |
| `rich_3518` | 1 | 1 | 0 / 0 | 0 / 0 |
| `rich_4075` | 0 | 0 | 0 / 0 | 0 / 0 |
| `fastapi_14492` | 1 | 1 | 0 / 0 | 0 / 0 |
| **Total** | **2/4** | **2/4** | **0 / 0** | **0 / 0** |

The observed command metric is a **lower bound** (recognizes `pytest`, `unittest` and `assert` commands); zero does not prove the agent executed no possible reproduction commands. The treatment has **zero net resolved tasks** and no observable uptake of the target verification mechanism. Thus **REJECT promotion and official submission of this exact instruction-only treatment**, per the preregistered no-net-increase gate. This does not falsify reproduction-first when implemented through a different workflow or tested on other issues. No Kaggle competition entry was created.


## Additional completed safe trace audit — 2026-11-14 12:06 MYT

Two separate CPU-only [Actions #43554709189](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43554709189) and [#43554924748](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43554924748) inspected the **existing** eight private scorer trajectories, with source SHA, frozen tasks, and all denominators validated; no model inference, training or Kaggle competition submission. Unit tests passed. Only allowlisted derived counts were exported; no issue text, tool arguments, patches or full output messages were copied to public GitHub.

- Baseline vs treatment: **41 vs 47** recorded `read_file` calls; **0 vs 1** graph calls, **19 vs 22** opaque shell commands and **0 vs 0** explicitly recognized test or inline-assertion calls. The large opaque class means "no recognized test" cannot be promoted into "no tests ran".
- **Specific new diagnostic:** On unsuccessful `fastapi_15800`, baseline trace contained **2** `submit_patch` calls (both `ok`), treatment **27** calls (all `ok` and all reporting a nonempty patch), including a longest **25 consecutive submit calls**. Trace attribution is unambiguous (zero parallel submissions). No tool-reported submit error was found. Other tasks had at most two submits per arm; `rich_4075` had none. This is a *single-task repeated-successful-submit generation/turn-termination pathology*, not evidence of a generally broken patch tool.
- Harness mechanics: `submit_patch` does not debit the tool-call ceiling; `patch_submitted` exits the outer loop only when the current ADK turn ends, per the bundled `HARNESS_README.md`. This explains how multiple successful submission requests can be observed before session stop, but **does not prove** which model or framework behavior caused this instance's 25-call streak.

**Decision:** do not submit or create a special-case retry/stop patch from this one failed task. The instruction-only treatment remains rejected at 2/4 vs 2/4. Structural turn-bound control is a possible *future* test only if it is expressible in the official declarative harness and a separate task/source-shift evaluation supports it. In the four-task result, neither graph removal nor a new test-first prompt has support as a broadly useful intervention.
