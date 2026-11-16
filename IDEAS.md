# IDEAS — Gemma Developer Agent (prioritized 2026-11-16)
No new private GPU, competing live job restart or official submission without checking [RULES](RULES.md), [VALIDATION](VALIDATION.md), current [NOW](NOW.md), and actual outstanding run states. Existing 3/4 task cohorts are **spent**.

| Rank | Hypothesis / falsifier | Discriminating experiment & predeclared advancement | Cost/risk | State |
| --- | --- | --- | --- | --- |
| 1 | Agent fails because post-edit error feedback is absent/unconsumed rather than because code edit is too late | Reanalyze *existing private 31B traces*: distinguish recognized test, opaque shell, observation returned, model subsequent action, scorer PASS; no new issue text exported. Gate: classify actual observability; if not identifiable, **INCONCLUSIVE** | CPU low, trace schema ambiguity high | IN PROGRESS AS DESIGN; no new raw trace read yet |
| 2 | A mandatory **legal native** test-feedback loop improves patch correctness | Validate supported action path and model uptake **before** preregistered ≥30 new paired gold-pass/noop-fail issues; score paired PASS CI; no regression-only promotion | GPU high; harness legality and test overhead | UNTESTED |
| 3 | Better repository localization/source evidence improves root-cause patch quality | **Orthogonal representation** (legal code-neighbor/code-subgraph tool policy) vs 31B V2 on independent paired issues, one intervention, bounded budget | GPU high; graph assets sometimes absent | UNTESTED |
| 4 | Targeted data/trajectory adaptation fixes semantic patch errors | **Orthogonal training** only on permitted non-hidden examples; model/adapter rights audit, independent issue-grader gate, distinguish complete trajectory training vs simple output imitation | GPU very high, leakage/overfit | UNTESTED |
| 5 | Smaller model uses surplus runtime for more effective candidate search | **Orthogonal architecture** with single legal 12B/E4B base; never rerun size-only tested 3 issues; new budget-matched/total-budget comparison and independent n gate | GPU high, old 12B alone worse 0/3 | NOT PROMOTED; new mechanism untested |

**ONE next action:** CPU-only post-edit feedback *trace observability audit* using already authenticated private outputs; if trace cannot isolate actionable feedback, label evidence insufficient and do not speculate about training fixes.
