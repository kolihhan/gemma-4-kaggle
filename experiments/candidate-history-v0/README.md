# Candidate-history diagnostic v0

**Status:** executable CPU diagnostic, not a new agent candidate. The official
ADK callback and sandbox interface were exercised with scripted CPU responses.
No real-model inference, training, competition submission or candidate promotion
was performed. The existing paired-check and frozen submission are unchanged.

## Question and current evidence

Did a test-passing patch ever exist at an observed tool boundary, and did it
survive into the final tree? This separates a lost good candidate from failure
to produce a passing candidate under the measured conditions. A missing patch
plus failed edit calls is recorded separately; it is not automatically proof of
an incapable model or a solely broken execution interface.

The existing own E4B archive was inventoried, without rerunning inference or
patch grading. It contains all 17 tasks from the already-inspected topology
single-root run [41458804862](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41458804862),
artifact 13150931817. Archive SHA-256:
`635dea845453d36ebd5ce5dc55472abd85c635a0333bf4d1d30c3fccd516e16f`.

| Recorded final outcome | Tasks |
| --- | ---: |
| Nonempty patch, unresolved | 12 |
| Nonempty patch, reported resolved | 1 |
| No patch, failed edit calls observed | 2 |
| No patch, other/no edit-call error observed | 2 |

All 17 lack a complete, independently graded boundary history. The 16 unresolved
cases cannot establish whether a good earlier candidate was lost. Some traces
contain printed diffs, which do not establish a complete sequence including
staged, committed and untracked changes. These descriptive counts are scoped
to E4B, not the scored thinking-on 31B. The external 31B summary files also do
not supply a complete sequence of source snapshots and independent grades.

[Machine-readable archive inventory](../../docs/evaluation/candidate-history-archive-inventory-2026-11-07.json).

## 2026-11-09 — Submission-boundary correction (CPU-verified)

**Why this matters:** the terminal workspace patch is not necessarily the patch at a
`submit_patch` request. Treating them as the same silently contaminates the
generation-vs-selection diagnosis.

The private-only observer now captures the source **immediately before**
`submit_patch`, records its returned/error callback separately, and still
captures the terminal tree. `grade_history` reports:

- `diagnosis` with `diagnosis_scope=terminal_tree_only` for backwards compatibility;
- `submit_attempts`, `submit_attempt_revision`, `submit_attempt_grade`;
- `submit_observation` and `submit_selection_diagnosis`, conservatively unknown
  for no request, an unconfirmed request, failed tool call or multiple requests.

A returned tool result is **not proof Kaggle accepted a submitted patch**.
A passing grade is evidence for the registered independent check only, not
necessarily the full issue. Candidate History remains an evaluation-side plugin,
never a submitted agent capability.

[33 passing tests in official ADK CPU Actions](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42550027757)
cover a correct candidate lost before submission, a correct submitted-attempt
candidate followed by a failing terminal tree, failed/missing/multiple submit
callbacks, and the unchanged agent-facing tool response. This adds **no** real
Gemma 31B model-quality evidence.

## Executable mechanism

`scripts/candidate_history.py` observes the source immediately before the run,
after tools, and in a finalizer. Each distinct patch against the fixed harness
baseline is SHA-256 identified. It includes committed, staged, unstaged and
nonignored untracked changes without changing the Git index. Two reads must
agree; failed captures mark history incomplete. The history directory must be
outside the agent workspace.

`History.for_sandbox` uses the sandbox's existing `run_command` interface.
`adk_plugin` observes tool completion and errors, returns `None`, and leaves the
tool response unchanged. A reported tool error does not override actual source
changes. Observer commands consume wall time; their cost is recorded. Their
effect on a real 31B/Docker session has not been measured.

After the agent has finished, the frozen independent check runs against copied
baseline source with each recorded patch applied. Its baseline must fail and
its reference-patched control must pass. The existing source-check runner
verifies copied-source imports and flags wrong-checkout imports/timeouts.
Blocked checks, missing history or invalid controls cannot become a claim that
the model never produced a correct candidate. Reference patches and grades are
used only after the run, outside agent-visible context.

Passing means passing that independent check, not universal correctness. A live
task evaluation needs frozen required tests and preservation checks; a narrow
probe alone is not a complete issue-level oracle. The local grading helper
runs source code; real untrusted candidates must be graded inside the task
sandbox. No such candidate execution occurred in these CPU controls.

## CPU results

Twenty-seven focused tests passed in 10.195 seconds, including the 14 existing
source-runner tests. Python compilation and ZIP-archive inventory succeeded.
The official `google-adk==1.36.1` Runner executed two scripted tool calls through
the observer; it saw unchanged `{status: ok}` tool responses. Only after that
run did the independent grader identify the passing intermediate patch that
was overwritten. The fixture uses no neural model.

Four scripted CPU trajectories used an independently fixed requirement:
`twice(2) == 4` and `twice(-2) == -4`. This tests the recorder and grader, not an
agent's ability to discover either assertion.

| Scripted trajectory | Actual diagnostic result |
| --- | --- |
| Correct implementation retained | `retained_passing_candidate` |
| Correct implementation overwritten with a positive-only fix | `discarded_passing_candidate` |
| Positive-only fix, never a passing boundary | `no_passing_candidate_observed` |
| Failed edit, source unchanged | `no_materialized_source_patch` |

Missing final capture, hash tampering, missing-source imports and invalid
positive controls are tested. In particular, an unfinished history cannot label
its last seen passing patch as the final patch.

[CPU receipts](cpu-verification.json). These are instrumentation controls, not
four solved model tasks or a measured repair-rate improvement.

## Reproduce or attach to a private evaluation

```bash
python -m unittest -v tests.test_candidate_history tests.test_candidate_history_adk \
  tests.test_candidate_history_inventory tests.test_paired_check_skill
python -m scripts.inventory_candidate_history --archive /private/e4b.zip \
  --output /private/archive-inventory.json
```

The ADK integration test requires the official wheel versions above and
`adk-eval-core==0.1.0`; no model weights are loaded. The grader reuses the existing
`experiments/paired-check-v0/skill/scripts/compare.py` execution helper.

For private harness integration, initialize `History.for_sandbox` after the
harness creates `_swegemma_baseline`; call `start()` before the first model
request, append `adk_plugin(history)` to the evaluation App's plugins, and call
`finish()` in a `finally` block. The submission agent remains byte-identical.
Keep a separate run manifest with task, model, config/wheel hashes, seed and
budget. Inference, live container instrumentation and task-level grading remain
unexecuted. This is not automatically installed in any Kaggle kernel.

## Decision

Continue to the actual 31B diagnostic when the CPU-only restriction is lifted.
The recorded quota at 17:56 MYT is 28.99 GPU hours, so lack of quota is not the
current blocker. The original round explicitly prohibited model inference;
this execution retained that boundary. The frozen official entry 58081411 was
still PENDING at the same read-only check.

If passing candidates are frequently lost, prioritize selection/stop control.
If none appears in complete, eligible histories, prioritize generation or
information use under that budget. If edits do not reach source, inspect the
execution interface first. A result on a few inspected development tasks is
diagnostic evidence only; it cannot establish hidden-set gains or justify
benchmark-specific rules. Current actual 31B mechanism effects are unmeasured.
