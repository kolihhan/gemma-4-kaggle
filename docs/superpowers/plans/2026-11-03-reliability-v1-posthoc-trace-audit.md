# Reliability-v1 Post-hoc Trace Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure evidence/edit/verification/repair mechanics from two already-completed development runs without new model inference.

**Architecture:** Add one stdlib Python analyzer that converts SWE trace JSON into compact per-run aggregate mechanics. Add synthetic unit tests for trace parsing and causal metrics. Add one one-shot GitHub Action that downloads existing Kaggle kernel outputs, runs the analyzer on topology single-root and Reliability-v1, writes compact JSON only, and uploads only those summaries.

**Tech Stack:** Python 3.12 stdlib, unittest, GitHub Actions, Kaggle CLI.

**Spec:** `docs/design/reliability-v1-posthoc-trace-audit-2026-11-03.md`

## Global Constraints

- Do not change `submission/**`.
- Do not push a Kaggle kernel or request GPU.
- Do not rerun the 17-task diagnostic.
- Do not persist raw traces, messages, tool arguments, patches, problem statements, or reference fields.
- Treat the 17 tasks as development-only mechanism evidence, never promotion evidence.

## Review Focus

- Trace steps with no `tool_calls` must not break analysis.
- Observation content may be JSON text or a dictionary; exit codes must normalize safely.
- `run_command` test classification must distinguish targeted pytest / assert probes from broad pytest.
- Script-side source mutations must be detected conservatively; uncertain cases must not be invented as edits.
- Failed verification followed by repair/retest must be ordered correctly rather than counted from unordered totals.

---

### Task 1: Trace mechanics analyzer

**Files:**
- Create: `scripts/analyze_root_trace_mechanics.py`
- Create: `tests/test_analyze_root_trace_mechanics.py`

**Interfaces:**
- Consumes: a trace directory containing `trace_*.json` and a `verifier_baseline_results.json` evaluator summary.
- Produces: JSON with per-run aggregate counts plus compact per-task mechanics containing only IDs/booleans/counts/categories.

- [ ] **Step 1: Write synthetic tests** for targeted pre-edit evidence, failed post-edit verification without repair, failed verification with repair/retest, submit-after-failure, broad-test classification, and benign non-mutating `run_command`.
- [ ] **Step 2: Run the focused test module and confirm it fails before implementation.**
- [ ] **Step 3: Implement trace normalization, conservative action classification, ordered mechanics extraction, aggregation, and CLI output.**
- [ ] **Step 4: Run focused tests and `py_compile`; require zero failures.**
- [ ] **Step 5: Run the analyzer against the already-downloaded topology-single-root traces locally and confirm it emits no raw message/tool-argument fields.**

### Task 2: Cheap one-shot A/B Action

**Files:**
- Create: `.github/workflows/audit-reliability-v1-trace-mechanics-once.yml`

**Interfaces:**
- Consumes existing Kaggle kernels `kolihhan/gemma4-topology-single-41458804862` and `kolihhan/gemma4-reliability-v1-diag-41485671952`.
- Produces `topology-mechanics.json`, `reliability-v1-mechanics.json`, and `comparison.json` only.

- [ ] **Step 1: Add workflow with CPU GitHub runner only; install pinned Kaggle CLI and download both existing kernel outputs.**
- [ ] **Step 2: Run focused analyzer tests before analysis.**
- [ ] **Step 3: Analyze both trace directories and assert both contain exactly 17 tasks.**
- [ ] **Step 4: Build aggregate A/B comparison and assert output contains no raw trace/message/tool-argument fields.**
- [ ] **Step 5: Upload compact summary directory only; never upload downloaded kernel output.**
- [ ] **Step 6: Let the workflow trigger once from its own creation and inspect its job logs/artifact.**

### Task 3: Research interpretation and source-of-truth update

**Files:**
- Modify: `docs/research/reliability-v1-diagnostic-interpretation-2026-11-03.md`
- Modify: `NOW.md`

**Interfaces:**
- Consumes: verified compact A/B mechanics artifact.
- Produces: updated mechanism ranking and next decision without candidate changes.

- [ ] **Step 1: Record FACT vs INFERENCE from the A/B mechanics.**
- [ ] **Step 2: Re-rank evidence-first, test-aware retrieval, adaptive compute, edit reliability, and bounded rescue only where the mechanics justify it.**
- [ ] **Step 3: Keep the next candidate unselected while Reliability-v1 public score is pending unless the new evidence creates a decisive non-LB falsification.**
- [ ] **Step 4: Re-read `submission/**` hashes/diff to verify the frozen candidate was not changed.**
