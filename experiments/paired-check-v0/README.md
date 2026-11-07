# Paired repository check v0

## Hypothesis

A useful check selected by the agent can still be misread when the agent only
sees the edited program. Returning the same check on the task's original source
can improve the agent's next keep/revise/revert decision. Final independently
correct patches, within the original budget, are the outcome.

The global bottleneck remains unknown. This mechanism targets missing execution
feedback; it does not assume that verification dominates 31B's failures.

## Evidence and scope

The preceding CPU study locked 19 external GPT-5 mini / mini-swe-agent traces
across Flask, Requests, pytest and SymPy before inspection. Twelve recorded
agent checks produced reproducible issue-relevant output changes; nine would
add a baseline observation absent from the trace. Eight changes shared the
same exit code. Three changes toward the issue requirement still had unresolved
independent verdicts. This supports returning observations, not treating a
changed output as a correct patch. It supplies no estimate of 31B uptake or gain.

[Locked study and source locations](https://github.com/kolihhan/gemma-4-kaggle/blob/7c1a078a4dfe7abc827975bcffd2dcb485696df6/NOW.md)
records the 19-task denominator and hashes. The earlier four-case assertion
notebook remains archived. No task IDs, expected answers, or repository-specific
selection rules occur in this candidate's executable action.

## Implemented action

The official submission compiler supports executable Skill scripts through
`SkillToolset` and `AdkSandboxCodeExecutor`. The candidate registers one action
with discovery instructions. The agent chooses whether to use it, supplies the
Python program, reads the returned observations, and chooses its next action.

The script copies the harness's `_swegemma_baseline` tag and current source into
disposable directories. It runs the supplied program in each copy with a default
ten-second limit per run, returns stdout/stderr/exceptions and import provenance,
and checks that the source checkout stayed unchanged. This is a source-copy
mechanism inside the existing task sandbox, not a separate security boundary.

Missing baseline, snapshot limitations or source-origin failures produce
`skipped`/`inconclusive` evidence. The agent must interpret observations against
the issue. Python source imports are supported; checks delegated to an external
process, file-only checks and native extension builds can lack verified provenance.
Generated `_version.py` and package metadata can be reused in both copies.

## Matched arms

| Setting | Treatment `paired` | Control `repeat` |
| --- | --- | --- |
| First source snapshot | Original harness baseline | Current source |
| Second source snapshot | Current source | Current source |
| Agent-chosen program | Same interface | Same interface |
| Discovery, instructions, model, root prompt, sampling, limits | Identical between arms | Identical between arms |

The archives differ only in `COMPARISON_MODE`. Both extend the exact attributed
Budget-Fit V2: 31B, temperature 0.2, top-p 0.95, 8192 output tokens, 4096 thinking,
8 minutes, 28 native tool calls, 80 turns. Root prompt, sampling and evaluation
files remain byte-identical to V2. The added Skill tools and ADK discovery
instructions are an actual change to the available action space. Script
execution consumes the existing wall-time allowance. Live accounting overhead
has not been measured.

The standalone notebook defaults to `ARM = "paired"`; changing that value to
`repeat` builds the matched control. It requires CPU and writes `submission.zip`.
The canonical `submission/` and frozen base-evidence candidate remain unchanged.

## Actual CPU checks — 2026-11-07

- 20 tests passed in 3.933 seconds. These include both arms compiled by official
  `adk_submission==0.2.13`, activated via `load_skill`, and executed by official
  `run_skill_script` and `AdkSandboxCodeExecutor` against a local sandbox adapter.
  The model registry contains a stub that raises on any inference attempt.
- A clean Python process executed the notebook code twice for treatment and
  once for control. ZIP bytes matched the builder; treatment repeats matched
  exactly. `nbformat==5.10.4` accepted the notebook schema.
- Two previously inspected archived programs were reused only as engineering
  checks, with their original Python bodies. Flask #5014 returned
  `NO_ERROR_ON_EMPTY` on base and `ValueError` on edit, both exit zero. SymPy
  #24213 returned the dimensionality exception on base and the recorded numeric
  result on edit. Both imported copied source and left the parent unchanged.
  These are not a new research sample or model decisions.
- Tests also cover staged, committed, untracked and deleted source; src layout;
  ignored build metadata; timeouts; source-free false confidence; imports from
  the wrong checkout; failing assertions; and probe writes confined to copies.

Machine-readable hashes, versions and engineering outcomes:
[cpu-verification.json](cpu-verification.json).

```bash
python -m scripts.build_paired_check_candidate \
  --source-zip /path/to/the-pinned-v2/submission.zip \
  --notebook /path/to/gemma4-paired-check-skill-v0.ipynb
python -m unittest -v tests.test_paired_check_skill tests.test_paired_check_adk \
  tests.test_paired_check_notebook tests.test_prepare_public_budgetfit_v2
```

The tests expect the pinned V2 archive at `../kaggle-reads/budgetfit-v2-exact.zip`.
The integration test additionally requires the official wheel versions recorded
in the verification JSON. No model weights are needed.

## Decision and next falsification

Continue with this executable candidate. Actual 31B check selection, next-action
quality, patch correctness and hidden-set transfer remain **unexecuted**.
No new candidate submission, inference or training was performed in this build.

For a causal continuation, lock independent tasks before inference and start
both arms at the same checkpoint after selection of the same program. Keep the
model, root prompt, sampling and remaining time equal; record returned evidence,
next action, final independent grading, failures and costs. Tasks without an
eligible check stay in the denominator. The two notebook arms also allow an
end-to-end screen, which alone cannot isolate next-action causality.

If the agent rarely obtains useful source-verified feedback, modify or abandon
this action on coverage grounds. If useful feedback arrives but independent
patch correctness does not improve at matched cost, abandon this mechanism and
prioritize edit generation/action selection. Do not retune on the same 19 traces.
