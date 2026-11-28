"""Aggregate-only retrospective evidence acquisition audit; never execute trace commands."""
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.audit_four_arm_evidence_20261127 import commands, categories, response, load
from scripts.render_fork_v1_20261127 import assess as assess_fork, RESULT as FORK
from scripts.render_multisurface_clean17_20261126 import assess as assess_multi, RESULT as MULTI


def inline_probe(segment):
    # Read-only by interpretation, not a security guarantee. Never execute code.
    if len(segment) < 3 or segment[0].rsplit("/", 1)[-1] not in ("python", "python3") or segment[1] != "-c":
        return False
    try:
        nodes = list(ast.walk(ast.parse(segment[2])))
    except (SyntaxError, ValueError):
        return False
    # Exclude obvious source mutation / file operations, retain unknown as unknown.
    if any(isinstance(n, ast.Call) and (
        (isinstance(n.func, ast.Name) and n.func.id in {"open", "exec", "eval", "compile"})
        or (isinstance(n.func, ast.Attribute) and n.func.attr in
            {"write_text", "write_bytes", "write", "writelines", "unlink", "rename", "replace", "mkdir", "rmdir", "touch", "system", "run", "Popen", "check_call", "check_output"})
    ) for n in nodes):
        return False
    calls = [n for n in nodes if isinstance(n, ast.Call)]
    print_call = any(isinstance(n.func, ast.Name) and n.func.id == "print" for n in calls)
    imports = any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in nodes)
    return imports and print_call and len(calls) > 1


def audit_trace(trace):
    c = Counter()
    phase = "pre"
    seen = set()
    for step in trace.get("steps", []):
        calls = step.get("tool_calls") or []
        if not isinstance(calls, list):
            continue
        # Same-step edit+test ordering is unidentifiable.
        entries = []
        for call in calls:
            if not isinstance(call, dict):
                continue
            name = call.get("function_name")
            a = call.get("arguments")
            if name in ("edit_file", "write_file"):
                entries.append(("edit", None, set()))
            elif name == "run_command" and isinstance(a, dict) and isinstance(a.get("command"), str):
                cmd = a["command"]
                entries.append(("shell", cmd, categories(cmd)))
        edit = any(kind == "edit" or "source_mutation" in labels for kind, _, labels in entries)
        for kind, cmd, labels in entries:
            if kind != "shell":
                continue
            if "source_mutation" in labels:
                continue
            at = "ambiguous" if edit and phase == "pre" else phase
            explicit = bool(labels & {"explicit_test", "inline_assert"})
            inline = not explicit and any(inline_probe(s) for s in commands(cmd))
            if explicit:
                category = "explicit_test_or_assert"
            elif inline:
                category = "possible_print_probe"
            elif "opaque_python" in labels:
                category = "opaque_python"
            else:
                continue
            key = (at, category, cmd)
            if key in seen:
                continue
            seen.add(key)
            state, _ = response(step.get("observation")) if len(calls) == 1 else ("unknown", None)
            c[at + "_" + category + "_requests"] += 1
            c[at + "_" + category + "_" + state] += 1
            c[at + "_" + category + "_episodes"] = 1
        if edit:
            phase = "post"
            c["recognized_edit_episode"] = 1
    c["episodes"] = 1
    return c


def run(fork, prior):
    all_rows = []
    for root, file, assess, arms in [
        (fork, FORK, assess_fork, ("champion_5min", "fork_5min")),
        (prior, MULTI, assess_multi, ("champion_5min", "multisurface_5min")),
    ]:
        rows = load(root, file, assess)
        traces = {}
        for p in root.rglob("trace_*.json"):
            key = (p.stem.removeprefix("trace_"), arms[int("public-prompt" in p.relative_to(root).parts)])
            if key not in rows:
                continue
            if key in traces:
                raise ValueError("duplicate trace")
            traces[key] = p
        if set(traces) != set(rows):
            raise ValueError("incomplete trace coverage")
        for key, row in rows.items():
            all_rows.append((key[0], bool(row["resolved"]), audit_trace(json.loads(traces[key].read_text()))))
    groups = defaultdict(list)
    for tid, ok, counts in all_rows:
        groups[tid].append((ok, counts))
    assert len(groups) == 17 and all(len(v) == 4 for v in groups.values())
    result = defaultdict(Counter)
    for values in groups.values():
        n = sum(ok for ok, _ in values)
        label = "always_pass" if n == 4 else "always_fail" if n == 0 else "mixed"
        result[label]["tasks"] += 1
        for _, counts in values:
            result[label].update(counts)
    return {"groups": result, "unique_tasks": 17, "episodes": 68, "semantic_relevance_verified": False,
            "execution_confirmed_only_when_structured_exit": True,
            "pre means before first recognized edit; opaque mutation may precede it": True,
            "no_new_model": True, "no_raw_export": True}


def smoke():
    def shell(cmd, exit_code=0):
        return {"tool_calls": [{"function_name": "run_command", "arguments": {"command": cmd}}],
                "observation": {"results": [{"content": json.dumps({"status": "ok", "exit_code": exit_code})}]}}
    def edit():
        return {"tool_calls": [{"function_name": "edit_file", "arguments": {}}]}
    assert inline_probe(["python", "-c", "from package import f; print(f(1))"])
    assert not inline_probe(["python", "-c", "from pathlib import Path; print(Path('x').write_text('y'))"])
    assert not inline_probe(["python", "-c", "print(1)"])
    t = {"steps": [shell("timeout 10s python -m pytest tests/test_x.py -q", 1),
                   shell("timeout 10s python -m pytest tests/test_x.py -q", 1),
                   shell("python -c 'from package import f; print(f(1))'"),
                   edit(), shell("pytest tests/test_x.py -q")]}
    c = audit_trace(t)
    assert c["pre_explicit_test_or_assert_requests"] == 1
    assert c["pre_explicit_test_or_assert_nonzero"] == 1
    assert c["pre_possible_print_probe_zero"] == 1
    assert c["post_explicit_test_or_assert_zero"] == 1
    mixed = shell("pytest tests/test_x.py -q")
    mixed["tool_calls"] += edit()["tool_calls"]
    c = audit_trace({"steps": [mixed]})
    assert c["ambiguous_explicit_test_or_assert_unknown"] == 1


if __name__ == "__main__":
    import sys
    smoke()
    print("PREEDIT_AUDIT_SMOKE=8 assertions passed", flush=True)
    print("PREEDIT_EVIDENCE=" + json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True), flush=True)
