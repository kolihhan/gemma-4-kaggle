---
name: semantic-surface
description: Read-only examination of changed Python definitions and where the same symbols appear in other repository modules and tests. Use once after a real source edit when an issue may span multiple interfaces.
---

# Semantic Surface — evidence, not an oracle

This is a small automated code-impact observation. It **cannot** tell you what the requirement is or whether hidden tests pass.

After a concrete Python source edit on a multi-entrypoint feature, class/method compatibility change, or complex bug, invoke:

1. `load_skill("semantic-surface")`
2. `run_skill_script(skill_name="semantic-surface", file_path="scripts/surface.py", args={})`

The script reads the real `git diff`, identifies affected definitions with Python AST, then lists other files with lexical references to those symbols. It never mutates source or calls a model.

Inspect only the cited paths that could encode **actual issue requirements**, not every returned path. A symbol reference is not automatically a missing edit. Check the edited behavior using a narrowly relevant existing test or simple issue example if possible.

If `no_python_source_change`, `repository_scan_limit`, or no references, do not loop. Finish the best justified source patch and submit within the original task budget. Call the script at most once; do not invent a correctness result.
