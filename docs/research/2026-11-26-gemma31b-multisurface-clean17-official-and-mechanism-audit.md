# 2026-11-26: Gemma 31B Multisurface, official trial + mechanism audit

## Scientific decision

The candidate was **submitted once at the owner's explicit request**, despite failing the previously frozen preregistered promotion gate. This does **not** alter that gate, does **not** promote the candidate as proven better, and does **not** justify another GPU sweep or leaderboard tuning. Maintain scored Champion **0.18** until an authenticated Kaggle terminal score confirms otherwise.

- Official Kaggle submission **#58931890**, marker `gemma31-multisurface-clean17-20261126`, authenticated at **2026-11-26 06:39:37 UTC**, state **PENDING** at receipt, public score blank. [Actual one-shot receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45769626525).
- Exact submitted ZIP SHA256: `7c8d68a51938595b34fa45168907cbecedee2fefd50fda9ecf487a84efb45781`. Champion SHA256: `ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b`. Only `prompts/system.md` differs. Registered from a private CPU-only Notebook, not a second GPU experiment.
- Kaggle quota checked: one legal slot, zero active submissions, remote SHA rechecked; one official submit attempt, authenticated receipt obtained. **Do not retry.**

## Genuine matched 31B local evidence

Actual pre-frozen same-scorer private [paired GPU run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45752093181): Gemma 4 31B QAT, 5 minutes, 60-call and 80-turn per task, 17 public-development gold/noop-valid tasks (12 FastAPI + 5 Rich), 34 evaluation arms, zero failures. Champion **9/17**, Candidate **10/17**. Outcomes: 8 both correct, **2 rescues**, **1 regression**, 6 neither. Exact McNemar two-sided p = **1.0** (2 vs 1 discordant). **Not a verified transfer or robust lift.**

| Metric | Champion | Candidate | Difference |
|---|---:|---:|---:|
| Resolved | 9/17 | 10/17 | +1 |
| Tool calls | 363 | 436 | +73 (+20.11%) |
| Total task seconds | 3826.54 | 4046.57 | +220.03 (+5.75%) |
| Errors | 0 | 0 | 0 |

Original frozen promotion criteria: `net>=2, regressions<=1, errors=0, seconds<=115%, tool_calls<=115%`. Failed net-rescue and tool-call criteria. The explicit owner-approved submission is an **external probe**, not a claim that the preregistered gate passed.

## Actual private, read-only retrospective mechanism audit

Aggregate-only [Action #45769760780](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45769760780) re-downloaded the **existing** Kaggle private scorer JSON, verified exact 17 paired identities and 34 records through `assess`, and reported only grouped counts. No GPU/model inference, no new private artifacts published, no raw issue IDs or model patches printed. Reproducible CPU-only script: [`scripts/diagnose_multisurface_clean17_20261126.py`](../../scripts/diagnose_multisurface_clean17_20261126.py).

| Paired outcome | Tasks | Extra Candidate calls | Candidate vs Champion patched | Extra task seconds |
|---|---:|---:|---:|---:|
| Both correct | 8 | +35 | 8 vs 8 | +46.01 |
| Candidate only | 2 | +20 | 2 vs 1 | +11.30 |
| Champion only | 1 | +4 | 1 vs 1 | -5.06 |
| Both fail | 6 | +14 | 5 vs 5 | +167.78 |
| **Total** | **17** | **+73** | **16 vs 15** | **+220.03** |

- Two rescues and one regression occur **exclusively on FastAPI**: FastAPI 5 both correct / 2 candidate-only / 1 champion-only / 4 neither. Rich 3 both correct / 0 discordant / 2 neither.
- **Only 20/73 additional calls** are located on the rescued tasks; **53/73** are on paired cases with no net score benefit or regression. This says where cost occurred, **not** whether those calls were semantically wasted.
- The 6 common failures incurred **+167.78/220.03 extra seconds (~76.3% of net slowdown)**; prioritize explaining these failed outcomes.
- Neither arm reached >=55 tool calls on any measured issue. Exceeding the 15% *aggregate cost threshold* is not evidence of hitting the 60-call hard per-task ceiling.
- On the two rescued tasks, patch presence increased from **1/2 to 2/2**. May be more reliable final patch production, or random outcome variation; **not causal evidence**. Patch length is not code correctness.

## Competing hypotheses and discriminating retrospective check

**H1: Multi-surface coverage improved root-cause handling for explicitly multi-entry-point FastAPI issues.** Predict a rescued task's Candidate trace demonstrates an additional *relevant* caller/interface read or patch coverage, and the Champion omits that requirement. Falsifier: same behavior/coverage in both arms; no evidence that extra actions address named requirements.

**H2: Broad exploration consumed calls and time without changing patch semantics.** Predict repeated inspections, low-value commands, delayed first valid edit, or missing actionable test/repair on the 6 shared failures. Falsifier: Candidate's added calls yield directly relevant evidence and patches, and failure lies in source semantics or grader mismatch.

**Next smallest useful audit (PRIVATE, CPU-only):** examine existing real per-task model tool traces and final patches, if retained, for: first mutation time, repeated command ratio, which named surfaces were read/edited, relevant test invocation and after-test repair. Compare paired trajectories **without sending oracle/gold/reference content to the model**. Save only aggregate outcome-conditioned classifications. Current scorer summary does not contain these trajectories, so no such causal finding is asserted here.

If traces unavailable, stop: additional prompt changes would be underdetermined. Next meaningful test must be preregistered, on new independently eligible tasks, with a mechanism-specific prediction and budget; no duplicate GPU work merely to increase sample size.

## External methodological contrast

- Nguyen Minh Thang, *Contain, Conform, Compare* (2026), https://arxiv.org/abs/2611.16485: 31B variants 37–44/70 without detected pairwise differences; emphasizes matched scorer and repository-cluster analysis.
- Patrick Passos, *One Run Is Not Enough* (2026), https://arxiv.org/abs/2611.19359: 98 matched 31B memory/no-memory tasks, 47 vs 48, exact McNemar p=1.0; reported substantial A/A run noise. Relevant warning against treating our 2 rescues / 1 regression as an established transferable mechanism.

## Next decision boundary

1. Await **authenticated terminal official** score for #58931890; preserve 0.18 Champion until then.
2. Review private trace evidence conditioned on rescued, regressed, both-fail without public/raw leakage; distinguish coverage benefit from repeated exploration.
3. **No re-submit of the same ZIP, no new GPU, no post-hoc revision of the 17-task score gate.** Any new candidate requires an independent mechanistic hypothesis and separate test.
