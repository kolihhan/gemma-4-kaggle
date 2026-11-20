# Gemma: registered-Kernel recovery, real public-source test-retrieval negative, and header-fix v2

2026-11-20. **Do not treat green GitHub workflow status as a model accuracy result.**

## 1. The 'failed' CPU private Notebook was actually COMPLETE

- The original [GHA #44756429496](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44756429496) **FAILED** in its final download step after a successful Kernel push, because it queried an ID not registered under that slug; the source lookup returned Kaggle `kernels.get` permission denied.
- **Real authenticated existing-only [recovery GHA #44763330552](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44763330552) SUCCESS:** Notebook is actually named `kolihhan/private-gemma-native-test-opportunity-cpu` (derived from the Notebook title rather than metadata ID). The completed CPU output safe JSON was fetched and schema-checked without accessing grader reference patches publicly. No GPU, no model inference, no official submission.
- Four previously inspected official public-dev tasks have readable snapshot tar path lists with **362 / 498 FastAPI** and **62 / 63 Rich** Python test files. All four produced **zero parsed touched `.py` source paths** under the v1 `diff --git a/` only parser. Therefore **0 filename matches is NOT evidence of no relevant tests**, and v1 cannot resolve the original test-discoverability hypothesis.
- Workload remains four historical, gold-pass/no-op-fail tasks; not an unseen correctness test.

## 2. Real upstream developer-commit test retrieval pilot: STOP exact mechanism

Complete genuine GitHub Actions [#44763807938](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44763807938). Evaluated tests that public developers co-modified in 53 source-change cases across previously available public repository tests; repository heads pinned by output SHA.

| Retrieval proxy, 53 publicly observed cases | Exact basename C0 | Token/path ranker C1 |
|---|---:|---:|
| Hit @1 on developer co-changed test | **21/53** | **23/53** |
| Hit @3 | N/A | **26/53** |
| Same-case rescues / regressions @1 | — | **2 / 0** |

**Frozen gate FAIL:** a minimum of +5 @1 hits was required; observed +2. Rich accounted for +2, FastAPI 0 gain. Co-modification is a noisy proxy: tests may exist but were not edited, or a developer may alter tests unrelated to the source file. No evidence about PASS, model-visible output or frozen 31B agent improvement. **Do NOT integrate this exact test path ranker into the agent or launch a GPU run on it.**

## 3. Targeted v2 measurement repair

v1 parsing only supported `diff --git a/... b/...`; v2 [patch-header extractor](../../kaggle/gemma_visible_test_opportunity_cpu_v2_20261120.py) adds `+++ b/...`, `*** Update File: ...`, `*** Add File: ...` and `Index:` formats, while preserving the strict private-only reference-patch boundary. It exports ONLY safe per-task counts and file-format flags, never source file paths or gold content.

New [GHA #44764497251](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44764497251) passed pure-Python parser smoke and **pushed exactly one new private CPU-only kernel** to the official Kaggle runtime. It derives the actual registered Notebook slug by matching its fixed title, rather than assuming metadata ID. **At document creation its output is pending; no v2 source-path or test-match result can be claimed.** It is a correction to invalid measurement, not new model training or Kaggle score.

## Next decision

- If v2 parses zero source files, **retire this gold-patch-backed test-discoverability census** as non-informative; do not claim no tests exist.
- If v2 parses source files but most have no exact-basename tests, **reject exact basename as a general verification strategy**, consistent with the failed public-proxy gate.
- If v2 finds candidate tests, still need a model-visible, no-hidden-grader path and fresh paired actual 31B grader-resolved test before claims of improved performance. Do not use gold touched paths as model inputs.
- Official Kaggle best remains **0.18** ref #58183466; the submitted Coder LoRA **0.12** ref #58558350 is worse. No score gain or new official code submission here.
## FINAL v2 official-private CPU result — terminal SUCCESS (2026-11-20)

**[GHA #44764497251](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44764497251) completed SUCCESS**, including private Kaggle script terminal COMPLETE and downloaded schema-checked safe aggregate. Registered private slug `kolihhan/gemma-visible-path-v2-20261120`. This is a parser-corrected replay of the SAME four previously certified official public-dev tasks, not new model inference.

| Frozen public-development task | Repo-family Python test files in original snapshot | Gold source `.py` paths parsed | Exact basename-related tests found |
|---|---:|---:|---:|
| FastAPI task ordinal 1 | 362 | 1 | 0 |
| FastAPI task ordinal 2 | 498 | 1 | 0 |
| Rich task ordinal 3 | 62 | 1 | 0 |
| Rich task ordinal 4 | 63 | 1 | 1 |

All four gold patches are nonempty and are **unified diff** format: per task 1 `---` header and 1 `+++` header, **zero** `diff --git` headers. The v1 parser had zero input on all four; v2 supports unified patch paths and recovered **4/4** valid modified source `.py` paths. **Exact basename test retrieval found a candidate for only 1/4**; the other three may have related tests under different names or indirect packages, unknown. Actual availability/execution of a relevant test, model consumption of test feedback and additional grader PASS remain UNOBSERVED. Do not call this a solver negative or a confirmation that tests are absent.

Together with 53-case actual public commit test-proxy C1 23 vs C0 21 (+2, prereg fail), stop promoting exact-basename and weak token-rank retrieval as the main competitive lever. Next mechanism should distinguish **incorrect patch semantics** from incomplete localization on real scored model traces, and only then nominate a new actionable 31B change.

**Official score unchanged:** best 0.18 #58183466; no GPU, model training or official submission this correction.