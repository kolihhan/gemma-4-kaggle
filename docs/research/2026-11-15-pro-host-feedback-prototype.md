# PRO round 2 — executable host post-edit feedback prototype

**2026-11-15. Synthetic mechanistic validation only; not an agent correctness result.**

The prior six real 31B traces show **3/3 edits, 0/3 resolved per arm** with no clearly recognized targeted post-edit tests (opaque commands prevent proving test absence). The canonical prompt already asks for focused testing; another instruction is not a new mechanism.

## Distinct proposed mechanism

`scripts/gemma_host_postedit_feedback_prototype_20261115.py` is a **host-side tool prototype** rather than a prompt update. From changed workspace paths (not hidden/reference patches), it:

1. finds an existing exactly named adjacent or `tests/test_<module>.py` test, or returns an explicit no-test status;
2. executes at most one matched test under a 20-second cap via subprocess argv, no shell, no network or install;
3. returns allowlisted `PASS / FAIL / TEST_UNAVAILABLE / TEST_TIMEOUT / NO_TARGETED_TEST_DISCOVERED` with an actionable repair flag only on a genuine test failure;
4. refuses relative-path traversal and does not print source, issue text, commands, patches or test output.

**Actual verification:** [Action #43683710899](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43683710899) **SUCCESS** on a small temporary Python project. Tested passing assertions, failing assertions, no matching test, path-traversal rejection, and distinction of pytest infrastructure error from genuine test failure. This demonstrates **bounded feedback delivery on synthetic files**. It does not show that test discovery will work on FastAPI/Rich/Requests/HTTPX tasks, that the ADK Agent consumes it, that it triggers a re-edit, or that graders accept repairs.

## Competing hypotheses and preregistered next pilot

- **H-feedback:** On tasks with discoverable affected tests, making the actual failure available and consumable after edits yields more corrections before submission.
- **H-semantics:** Tests are often irrelevant, unavailable, already run opaquely, or the agent misdiagnoses failures; feedback will increase tool usage without improving resolved tasks.

**Next gate** (not yet executed): implement the smallest compatible intervention inside a private candidate/evaluator path, first proving test feedback is delivered to and consumed by the 31B agent. Compare frozen V2 vs feedback treatment on the same 3 **new preselected** issue IDs, excluding all previously inspected issues, with identical model, max 5min, max 28 calls and 80 turns. Score primary **paired grader-confirmed rescues minus regressions**. Count actual post-edit test invocations, failed-test→re-edit transitions and wall/call costs secondarily. No solution/reference patch may be exposed to the agent. If a task lacks discoverable local tests, the honest treatment is *no feedback*, not a fabricated PASS.

**Stop:** no resolution rescue, or rescue outweighed by regressions/cost => reject this treatment class. A 1-of-3 rescue stays preliminary until a separately sourced pilot reproduces it. Do not submit to Kaggle until a source-disjoint correctness gain is demonstrated.

## Yuanzhe Zhou method translation

The [CMI winning team writeup](https://www.kaggle.com/competitions/cmi-detect-behavior-with-sensor-data/writeups/cmi-1st-place-solution) shows grouped evaluation and architecture/input diversity; do not treat CI green or short run time as task success. Zhou's [Kaggle public discussion](https://www.kaggle.com/yuanzhezhou/discussion) emphasizes local CV when LB validation differs. This is a reason to demand actual grader-resolved deltas rather than repeatedly editing the same 3 tasks.

**Status:** prototype implemented and tested; agent integration, real paired validation, GPU and new official submission **NOT DONE**. Scored best remains **0.18** until an authenticated newer numeric score appears.
