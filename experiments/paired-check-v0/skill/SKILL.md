---
name: repository-check
description: Run a Python check you select in two disposable repository snapshots and inspect actual outputs and imported source locations. Use when a check of an issue requirement could help decide whether to keep or revise an edit.
---

# Repository check

Choose the Python check and its expected behavior from the issue and repository.
Use this action when an equivalent baseline observation is absent from your context.
Keep the check focused enough to finish in ten seconds per snapshot.

Call `run_skill_script` with `skill_name="repository-check"`,
`file_path="scripts/compare.py"`, and `args={"code": "YOUR PYTHON CHECK"}`.
An optional `timeout` argument sets one snapshot's limit up to twenty seconds.
Use ordinary imports or `pytest.main` with an existing test node. The Python code
runs in each copy's working directory. Use relative repository paths.

Read both runs' `stdout`, `stderr`, `return_code`, and import provenance.
Use the labels to identify which source each observation came from.
`compared` means both runs imported copied repository code. Judge whether the
observations meet the issue. An equal exit code can still contain different behavior.
Use `skipped` or `inconclusive` as missing evidence.

Decide whether to keep, revise, or revert your edit using these observations and
the other repository evidence. Retain the existing submission deadline and budgets.
