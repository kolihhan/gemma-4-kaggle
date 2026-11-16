# PRO Gemma 4: frozen SequentialAgent 31B real grader result — no rescue
2026-11-16. Evidence: [GitHub Action #43808826562](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43808826562), completed job 133105673464. Unlike a notebook title or successful push, the completed job downloaded genuine Kaggle scorer JSON, asserted matching issue IDs and printed the paired grader result.

## Preregistered experiment
[Immutable candidate contract](../../experiments/solver-v3/pro-sequential31b-native-verifier-20261116.json):
- H_seq: mandatory native SequentialAgent coder → verifier can convert a missed issue into a pass by reviewing/testing a patch, compared with single 31B V2.
- Alternative: two stages waste calls/context without improving correctness.
- Same three previously inspected FastAPI/Rich/Requests development issues as the frozen 31B V2 control; matched 5min/28 scorer-tool-call/80-turn limit, same base Gemma 4 31B and sampling. New frozen ZIP SHA256 `dd3b582cd6d97ef2314ffdef64738b06b302c6cc0234fb7513258858e38a2c0a`.
- Original preregistered promotion: at least 2/3 grader PASS, no errors, actual reviewer reached ≥2/3, AND disjoint subsequent validation; stop exact topology if 1/3 with extra calls/time or no reviewer uptake. Never submit to official leaderboard on three spent tasks.

## REAL result
| Metric | Pinned V2 31B | Mandatory SequentialAgent 31B |
| --- | ---: | ---: |
| Same matched public-development tasks | 3 | 3 |
| Official development grader-resolved issues | **1/3** | **1/3** |
| Patches | 3 | 3 |
| Evaluation errors | 0 | 0 |
| Genuine scorer tool calls | 62 | 69 |
| Scorer duration total seconds | 604.94 | 606.50 |
| Unique rescues / regressions | — | **0 / 0** |

- Paired success-rate difference **0.0 percentage points** over **n=3**. Exact enumerated paired task bootstrap point-estimate distribution is degenerate `[0,0]` because every observed pair agrees; **this does NOT support equivalence**, nor an informative population CI. With 0/3 discordant issues, exact two-sided 95% upper limit on the discordant-issue *rate* is ~0.7076, demonstrating uncertainty.
- Actual reviewer-stage commands, whether a targeted test executed, and whether its feedback caused a repair: **UNKNOWN**. The real scoring result printout explicitly says reviewer uptake not yet attributed. A mandatory YAML stage is not proof of actual useful test uptake. A manual or downstream trace review would be required before mechanistic claims.
- This is **not independent**: three spent public-dev issues. It is **not an official Public LB submission or change**.

## Decision
**NOT PROMOTED; retire this exact 31B SequentialAgent configuration against its preregistered stop gate.** The observed PASS result stays 1/3 with +7 scorer calls and +1.56 seconds, so this exact implementation has no positive pilot evidence. This *does not disprove* all two-stage agents or test-feedback architectures: n=3, no unique rescues and no reviewer action attribution. DO NOT launch a duplicate run on the same task IDs.

**Official scored Kaggle best remains 0.18** #58183466. One previous COMPLETE #58350278 has no numeric score. No new training, Kaggle GPU or official submission initiated by this report.

**One next action:** CPU-only reviewer-stage uptake / test-command audit of the existing private kernel output, if accessible; otherwise record UNKNOWN and pivot to designing a truly new legal feedback mechanism rather than copying this topology.
