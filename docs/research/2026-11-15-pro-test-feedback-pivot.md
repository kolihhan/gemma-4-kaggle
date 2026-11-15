# PRO mechanism study: editing latency vs edit quality vs test feedback

Status: **real completed, previously used 3-issue paired diagnostic** (2026-11-15). Not independent hidden-task confirmation.

## Competing hypotheses

- **H1 — budget/exploration failure:** Agent edits too late or never edits. Prediction: high no-edit or late-edit rates.
- **H2 — understanding/edit correctness failure:** Agent edits but produces patches not accepted by the grader. Prediction: edits with zero resolution even when editing starts earlier.
- **H3 — test-feedback/repair failure:** Agent does not obtain or use actionable post-edit test evidence. Prediction: few recognized targeted checks or failed checks without evidence-backed re-edit. Beware: opaque commands can hide real tests.

## Executed data

Existing genuine 31B private paired traces inspected with [read-only Action #43682311978](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43682311978). [Reducer](../../scripts/gemma_pro_mechanism_existing_traces.py) and [synthetic tests](../../tests/test_gemma_pro_mechanism_existing_traces.py). No raw private prompts, commands, patches or issues exported.

| Observation across identical 3 public-dev issues per arm | Pinned V2 | Alternate public prompt |
| --- | ---: | ---: |
| Actually resolved | 0/3 | 0/3 |
| At least one observed edit | 3/3 | 3/3 |
| First edit in latter half of actions | 1/3 | 2/3 |
| Recognized explicit or inline test calls | 0/3 | 0/3 |
| Edit but no recognized test | 3/3 | 3/3 |
| Trace contains opaque commands | 3/3 | 2/3 |
| Failed command after last edit | 1/3 | 1/3 |
| Total tool calls | 66 | 71 |
| Sum of task wall time | 827.61 s | 828.40 s |

Observed edits and no quality gain contradict the idea that earlier editing *alone* is the missing capability. H2/H3 remain live. **Zero recognized tests is not proof zero tests ran:** command classification cannot see all opaque Python execution or relevance. The canonical [system prompt](../../submission/prompts/system.md) *already* instructs narrow verification and repair, so repeating instructions is not a distinct mechanism.

## Next falsifiable treatment

Test a host/tool-level post-edit feedback mechanism (not another prompt rewrite): expose changed paths and a bounded targeted verification result when a legitimate local test is discoverable, allow one evidence-backed repair, preserve final submission time. Control: pinned V2 agent, same model, issues, time/call limits. Intervention: only feedback availability and its actual delivery/consumption.

Preregister fresh issue IDs/repositories before inspecting raw issues; exclude all known issues. Start with 3 paired tasks, identical 5-minute/28-call budget, no reference-solution exposure. Primary outcome **paired grader-resolved rescues minus regressions**. Secondary: first edit, recognized tests, re-edit after failure, tool calls, total time. Unknown test availability remains UNKNOWN rather than noncompliance. Zero net improvement with higher cost retires the mechanism; a one-task gain is preliminary until corroborated on a different source.

No new GPU launched from this diagnosis, no official submission. Best authenticated scored Gemma remains 0.18; new official submission #58350278 was last confirmed pending.

Additional references: [paired budget gate](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43678028748), [failure taxonomy](../evaluation/failure-taxonomy.md).
