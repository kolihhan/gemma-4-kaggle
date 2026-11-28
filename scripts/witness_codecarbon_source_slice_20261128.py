"""CodeCarbon #830 source-slice witness, not a full package integration test.
Run in a disposable offline container. Extract exact function bodies from
checked-out source, not a reimplementation; no reference-derived selection.
"""
import ast
import configparser
import copy
import json
import logging
import os
from pathlib import Path
import tempfile
from types import MethodType, SimpleNamespace
from typing import List

ROOT = Path("/testbed/codecarbon")


def find(tree, typ, name):
    matches = [n for n in tree.body if isinstance(n, typ) and n.name == name]
    assert len(matches) == 1, (typ.__name__, name)
    return matches[0]


def module(path):
    return ast.parse(path.read_text(), filename=str(path))


def install(node, scope, path):
    node = copy.deepcopy(node)
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), scope)


def main():
    cfgpath = ROOT / "core/config.py"
    trpath = ROOT / "emissions_tracker.py"
    hwpath = ROOT / "external/hardware.py"
    scope = dict(configparser=configparser, os=os, Path=Path, List=List,
                 logger=logging.getLogger("slice"), __version__="diagnostic",
                 _sentinel=object())
    cfg = module(cfgpath)
    for name in ("clean_env_key", "parse_env_config", "get_hierarchical_config"):
        install(find(cfg, ast.FunctionDef, name), scope, cfgpath)
    tr = find(module(trpath), ast.ClassDef, "BaseEmissionsTracker")
    install(find(tr, ast.FunctionDef, "_set_from_conf"), scope, trpath)
    init = find(tr, ast.FunctionDef, "__init__")
    calls = [n for n in ast.walk(init) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "_set_from_conf"
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"
             and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant)
             and n.args[1].value == "force_cpu_power"]
    assert len(calls) == 1
    call = compile(ast.Expression(calls[0]), str(trpath), "eval")
    cpu = find(module(hwpath), ast.ClassDef, "CPU")
    install(find(cpu, ast.FunctionDef, "_calculate_power_from_cpu_load"), scope, hwpath)
    with tempfile.TemporaryDirectory() as tmp:
        old = os.getcwd()
        home = os.environ.get("HOME")
        config_env = {k:v for k,v in os.environ.items() if k.lower().startswith("codecarbon_")}
        try:
            os.chdir(tmp); os.environ["HOME"] = tmp
            for k in config_env: os.environ.pop(k)
            Path(".codecarbon.config").write_text("[codecarbon]\nforce_cpu_power = 45\n")
            config = scope["get_hierarchical_config"]()
            assert config["force_cpu_power"] == "45"
            records = []
            for label, value in (("constructor", 45), ("config_file", scope["_sentinel"])):
                receiver = SimpleNamespace(_external_conf=config)
                receiver._set_from_conf = MethodType(scope["_set_from_conf"], receiver)
                eval(call, scope, {"self": receiver, "force_cpu_power": value})
                tdp = receiver._force_cpu_power
                row = {"input": label, "tdp_type":type(tdp).__name__}
                try:
                    row.update(outcome="VALUE",power=scope["_calculate_power_from_cpu_load"](tdp,50.0,"generic"))
                except Exception as exc:
                    row.update(outcome="EXCEPTION",error_type=type(exc).__name__,
                               issue_error_match=isinstance(exc,TypeError) and "can't multiply sequence by non-int" in str(exc))
                records.append(row)
            print("SLICE_WITNESS="+json.dumps(records,sort_keys=True),flush=True)
        finally:
            os.chdir(old)
            if home is None: os.environ.pop("HOME",None)
            else: os.environ["HOME"]=home
            os.environ.update(config_env)


if __name__ == "__main__":
    main()
