"""Issue-only manual witness for public CodeCarbon #830 (exploratory, not holdout).
No reference patch, hidden test, or model used by this script.
Execute only inside disposable offline benchmark container.
"""
import ast
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace, MethodType

import codecarbon.emissions_tracker as tracker
from codecarbon.core.config import get_hierarchical_config
from codecarbon.external.hardware import CPU


def main():
    source = Path(tracker.__file__).resolve()
    assert Path("/testbed") in source.parents
    tree = ast.parse(source.read_text())
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "BaseEmissionsTracker")
    init = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == "__init__")
    calls = [n for n in ast.walk(init) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "_set_from_conf"
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"
             and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == "force_cpu_power"]
    assert len(calls) == 1, "unsupported callsite shape"
    call = compile(ast.Expression(calls[0]), str(source), "eval")
    with tempfile.TemporaryDirectory() as root:
        old_cwd = os.getcwd()
        old_home = os.environ.get("HOME")
        old_config = {k:v for k,v in os.environ.items() if k.startswith("CODECARBON_")}
        try:
            os.chdir(root);os.environ["HOME"] = root
            for k in old_config:os.environ.pop(k)
            Path(".codecarbon.config").write_text("[codecarbon]\nforce_cpu_power = 45\n")
            config = get_hierarchical_config()
            assert config["force_cpu_power"] == "45"
            records = []
            for label, value in (("constructor", 45), ("config_file", tracker._sentinel)):
                self = SimpleNamespace(_external_conf=config)
                self._set_from_conf = MethodType(tracker.BaseEmissionsTracker._set_from_conf, self)
                try:
                    # Replay the untouched source's actual argument conversion, not a guessed conversion.
                    eval(call, vars(tracker), {"self":self,"force_cpu_power":value})
                    tdp = self._force_cpu_power
                    row = {"input":label,"tdp_type":type(tdp).__name__}
                    try:
                        power = CPU._calculate_power_from_cpu_load(tdp,50.0,"generic")
                        row.update({"outcome":"VALUE","power":power})
                    except Exception as exc:
                        row.update({"outcome":"EXCEPTION","error_type":type(exc).__name__,
                                    "issue_error_match":isinstance(exc,TypeError) and "can't multiply sequence by non-int" in str(exc)})
                except Exception as exc:
                    row = {"input":label,"outcome":"BLOCKED","error_type":type(exc).__name__}
                records.append(row)
            print("ISSUE_WITNESS="+json.dumps(records,sort_keys=True),flush=True)
        finally:
            os.chdir(old_cwd)
            if old_home is None:os.environ.pop("HOME",None)
            else:os.environ["HOME"]=old_home
            os.environ.update(old_config)


if __name__ == "__main__":
    main()
