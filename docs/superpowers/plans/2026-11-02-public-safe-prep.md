# Public-Safe Repository Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make repository visibility safety explicit and prevent future agents from making this repository public while competition data or Kaggle public-code-sharing obligations remain unresolved.

**Architecture:** Keep experiment/scientific state unchanged. Add a repo-wide public-visibility gate document, surface it in canonical agent/state files, and preserve the existing fail-closed private-repository guard on the Kaggle data mirror workflow.

**Tech Stack:** Markdown, GitHub Actions.

**Spec:** User instruction on 2026-11-02 to make the repo public-safe and record the constraint for other agents.

## Global Constraints

- Do not change experiment data, LoRA configuration, evaluation contracts, prompts, blind sets, or submission artifacts.
- Competition Data must not be exposed to non-participants.
- Do not make the GitHub repository public while the existing full-data GitHub Release remains present.
- Any public sharing of Competition Code during the competition must satisfy the applicable Kaggle competition public-sharing rule.

## Review Focus

- Existing GitHub Release assets remain a hard blocker.
- Data mirror workflow must fail closed when repository visibility is public.
- Other agents must see the gate from canonical entry files.
- No scientific files should change.
- No claim of PUBLIC-SAFE READY before destructive cleanup and final verification.

---

### Task 1: Record public visibility gate

**Files:**
- Create: `PUBLIC_VISIBILITY.md`
- Modify: `AGENTS.md`
- Modify: `NOW.md`

- [ ] Record current status as `BLOCKED` with exact blockers and readiness checklist.
- [ ] Add an entry-point instruction requiring agents to read the gate before changing repository visibility.
- [ ] Add the blocker to current canonical state without changing experiment decisions.
- [ ] Re-read all three files and verify wording is consistent.

### Task 2: Verify existing mirror guard

**Files:**
- Inspect: `.github/workflows/mirror-full-kaggle-data.yml`

- [ ] Confirm the workflow refuses to mirror data when `github.event.repository.private` is not true.
- [ ] Do not alter the workflow if the guard is already fail-closed.

### Task 3: Final safety verification

- [ ] Confirm no experiment/scientific files changed.
- [ ] Confirm repository remains private and the status remains `BLOCKED` until Release cleanup and Kaggle public-code-sharing compliance are completed.
