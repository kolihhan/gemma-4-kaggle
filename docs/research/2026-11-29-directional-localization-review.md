# Directional localization review — 2026-11-29

Read GraphScent arXiv:2611.17527 v1 text mirror sections 3–5 and Appendices A–B (PDF screenshot unavailable due cache miss). Author's Table 5, live T=0 localization, B=24:
| 31B method | All 211 LW@1 | BM25-hard 94 LW@1 |
|---|---:|---:|
| Flat BM25 | 41.7 | 12.8 |
| Static Dir-PPR | 42.2 | 13.8 |
| Fixed-Dir | 43.6 | 20.2 |
| GraphScent | 43.6 | 23.4 |
| No-Gate | 44.5 | 24.5 |
| Rev-Dir | 43.1 | 14.9 |

These are author-reported localization percentages, not task resolution or Kaggle score. Positive directional signal is upstream caller/enclosing parent as observable evidence; propagate forward toward callee/child, not automatically edit the caller. 24 separate stateless T=0 thinking-off ordinal judgments and one listwise ranking; cannot infer cheap single-call equivalent. Calibration uses gold-derived relation histograms out-of-repository, not permissible to inject task-specific gold data. The strongest 31B no-gate ablation exceeds full method on this cohort; gate superiority not general. On 31B post2025 panel GraphScent 41.8 vs BM25 44.9. Avoid selecting only hard subset.

## Independent source audit
G-HRR https://github.com/Tarekswd/g-hrr-gemma4 claims 18->44% in README. Inspected actual scripts/run_experiments.py and src/experiments/experiment_runner.py. BenchmarkCohortGenerator fabricates numbered issues and generic statements, random repo assignment; ExperimentRunner assigns predefined probabilities by system/difficulty, executes passed=random.random()<prob, generates random tokens/tool counts/duration. The provided runner is simulation rather than real model+test execution. This does not establish whether an unpublished separate genuine experiment exists; exclude its claimed empirical gains from decision evidence.

Owner scripts/build_caller_hop_v1.py exact conditional one-hop prompt already submitted #58505571 .13; don't rebrand it. HARNESS_README get_code_neighbors returns flat neighbors (filter by relation, not direction); get_code_subgraph supplies explicit from/to/type only for selected nodes. Existing native tools can express selective directional exploration, but no verified closed-compiler host loop performing GraphScent's stateless 24 calls or automatic evidence injection. Optional skill and wrapped tool adoption/overhead known negative. A prompt-only direction variant is not a novel controller.

Read-only source workflow .github/workflows/gemma-graphscent-source-readonly-20261129.yml commit 7151cf8758fbe01d4a5834f6451d445ca99bcdfc attempts to pull author public reproduction notebook without execution. Aggregate AST/regex inspection only, not proof of live measurements or official deployability. No inference, training, new Kaggle kernel, or submission. Owner's 'go' following limited GPU suggestion authorizes bounded exploration; no GPU launched because a distinct deployable mechanism and actual eligible test are not established. Preserve Champion and pending C (last receipt 22:13 MYT). No more repeated local qualification or caller-hop prompt. 
