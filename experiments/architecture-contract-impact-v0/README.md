# Contract & Impact — executable architecture candidate (2026-11-09)

**State: CPU package and official ADK Skill execution verified. NO 31B inference or Kaggle score.** This is a full root workflow rewrite plus a deterministic Skill, not a Recovery Reviewer prompt edit. The exact V2 ZIP remains a frozen external comparison baseline and supplies only the same model/native tools/sampling/eval-budget source for the new builder.

## Mechanism and source

- Read the [architecture search reset](../../docs/design/architecture-search-reset-2026-11-09.md).
- [builder](../../scripts/build_contract_impact_candidate.py) validates the source ZIP hash through `validate_source_zip`, retains all nine native tools and original 31B sampling/8-minute/28-call/80-turn config, rewrites the full root instruction and adds `skills/contract-impact/`.
- [Skill script](skill/scripts/contract.py) reads git changes and a model-supplied structured contract; does **not** run tests, infer hidden requirements, modify the tree or declare patch correctness.
- [Skill description](skill/SKILL.md) distinguishes explicit issue/repository evidence from model hypotheses and unknowns. Claimed passing tests remain marked **agent-reported**, never independent truth.
- No additional LLM agents, weights or adapters are added. All extra Skill calls are part of the same budget.

## Verified on CPU

[Official ADK/GitHub Actions 42551996131](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42551996131) passed:

1. **9 focused unit tests** including partial multi-entrypoint changes, missing requirement information, hypothesis-as-fact prevention, unverified checks, unsafe paths, untracked files and root package contracts.
2. Pulled byte-pinned externally attributed Budget-Fit V2 `submission.zip` as source and produced deterministic architecture ZIP SHA-256 **`4858587c922ae275417199d8c11c00abce2249e42992657e134ba8d6dc2df975`**.
3. **1 official ADK CPU compiler/Skill invocation test**: model registry uses an inference-forbidden 31B stub; `load_skill` and `run_skill_script` executed in a local sandbox. The script detected that an intended second implementation file was unchanged, without modifying the repository.
4. Python syntax compilation passed. No actual Gemma model call, training, official competition submission or external leaderboard score.

## What remains unknown

- Whether the 31B agent **chooses** the Skill at useful moments, supplies trustworthy evidence, or improves issue correctness; CPU fixture only verifies the tool can be called.
- Added latency, model token cost and actual 12-hour global feasibility.
- Whether any gain would come from root workflow rewrite or structured Skill; they change together in this end-to-end prototype.
- A model-supplied impact file map can be incomplete or wrong; the tool structurally checks **declared** coverage, not the true necessary scope. A documented `review_final_not_certified` means **not** grader-pass.

## Falsifiable evaluation before promotion

**H1:** Relative to exact single-root V2 at matched total 31B compute, grounded contract/impact analysis reduces incomplete cross-entrypoint or missed explicit-requirement repairs enough to increase independently verified final issue resolution.

Use a preregistered exposure-clean task set, ideally across repositories, with unchanged native tools and resource caps. Keep missing-spec cases, tool failures, non-invocations, and timeouts. Measure issue-level independent correctness, requirement/impact misses, actual Skill uptake, cost and final patch submission. Do not infer correctness from this tool's self-reported check field. If H1 fails, reject this candidate rather than stacking reviewer prompts. If H1 holds, separate the root workflow effect from the structured Skill in a subsequent matched ablation and test disjoint confirmation.

**Execution boundary:** no automatic GPU inference, no Kaggle official submission, no modifications to frozen/canonical submission. A new official submission requires a research-based justification and explicit user approval.
