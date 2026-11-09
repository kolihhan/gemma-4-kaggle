---
name: contract-impact
description: Read-only structure check for task requirements, affected source paths, and check evidence. Use before finalizing a multi-file or semantically complex repair. This is NOT a correctness oracle.
---

# Contract & Impact

Extract explicit requirements from the task and repository. Missing information is
an **unknown**, never an invented requirement. Record each requirement's source
(`issue`, `repository`, or `hypothesis`), concrete evidence, expected edit
targets, and verification status. Source locations are evidence, not ground truth.

Call `run_skill_script` with `skill_name="contract-impact"`,
`file_path="scripts/contract.py"`, and an `args` object containing:

```json
{
  "request": "{"requirements":[{"id":"R1","statement":"behavior","source":"issue","evidence":"issue line/quoted phrase","edit_targets":["package/module.py"],"check":{"status":"not_run","evidence":""}}],"unknowns":[]}"
}
```

`request` is a JSON **string**, not a nested object. Optionally pass
`workspace="/workspace"`. `edit_targets` are expected **mutation** paths;
investigated-only caller/test paths should not be listed there. Prefer
`not_run`, `blocked` or `unknown` until an actual focused check is run.
If you claim `reported_pass`/`reported_fail`, provide the observed command
and concise output; the script does not execute or independently verify it.

The tool compares declarations with real tracked/untracked source changes.
`review_final_not_certified` does **not** mean the task passes hidden tests.
A missing target may reflect an incorrect assumption about impact; recheck
rather than blindly editing every declared file.

After the analysis, use native file/shell/test tools to resolve the most
consequential gap; reuse the contract only when new evidence or edits change it.
Keep time for targeted verification and `submit_patch`. One useful inspection
beats repeated planning calls.
