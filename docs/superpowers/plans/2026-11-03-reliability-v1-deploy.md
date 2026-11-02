# Reliability v1 Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the frozen Reliability-v1 candidate to Kaggle, collect development diagnostics and real submission feedback, without storing raw Competition Data in GitHub.

**Architecture:** Keep `submission/` byte-frozen, render two private Kaggle kernels from it (diagnostic and submission builder), and orchestrate both through one GitHub Actions workflow. The development result and leaderboard submission run independently after static validation so the seen 17-task set cannot select the candidate.

**Tech Stack:** Python 3.12, unittest, GitHub Actions, Kaggle CLI 2.2.5, Kaggle private kernels.

**Spec:** `docs/design/reliability-v1-learning-loop-2026-11-03.md`

## Global Constraints

- No Competition Data committed to GitHub or uploaded as an Action artifact.
- Reliability-v1 submission files must match the pre-registered SHA-256 hashes exactly.
- Existing 17-task set is development-only and cannot gate submission.
- E4B model, sampling, budgets, and graph/code-intelligence tool surface stay frozen.
- Exactly one competition submission is created by the deployment workflow.

## Review Focus

- Candidate file/hash drift must fail closed.
- Verifier/sub-agent files must not leak into `submission.zip`.
- Diagnostic and submission jobs must not depend on each other's result.
- Kaggle scoring may remain pending after the Action polling window; submission ref must still be retained.
- Raw competition files must never appear in uploaded GitHub artifacts.

---

### Task 1: Freeze and validate candidate
- [x] Add regression tests for exact file set, single-root tool surface, and generic Reliability-v1 guards.
- [x] Install the already-frozen candidate files and verify tests pass locally.

### Task 2: Render runtime-only Kaggle kernels
- [x] Render diagnostic kernel by embedding the frozen submission into the existing scorer runtime and frozen manifest.
- [x] Render a tiny private builder kernel that emits only `/kaggle/working/submission.zip`.
- [x] Test both render paths and metadata contracts.

### Task 3: Deploy and collect feedback
- [x] Pre-register leaderboard/development predictions and anti-overfit rules.
- [x] Add static validation, diagnostic, and competition-submission jobs.
- [x] Ensure diagnostic and submit jobs fan out independently after static validation.
- [x] Upload only compact diagnostic/submission feedback artifacts.
- [ ] Observe the real workflow run and record run/submission refs and eventual score.
