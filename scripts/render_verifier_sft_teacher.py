#!/usr/bin/env python3
"""Bundle verifier SFT teacher runtime dependencies into one Kaggle code file."""

from __future__ import annotations

import base64


IMPORT_BLOCK = """import verifier_gold_teacher_runtime as gold
from verifier_gold_teacher_supervision import (
    DIFF_COMMAND,
    build_teacher_supervision_record,
    load_targeted_test_plan,
)
"""


def _encoded(source: str) -> str:
    return base64.b64encode(source.encode("utf-8")).decode("ascii")


def bundle_runtime(runtime_source: str, gold_source: str, helper_source: str) -> str:
    """Return a standalone script whose local modules are loaded from embedded source."""
    if runtime_source.count(IMPORT_BLOCK) != 1:
        raise ValueError(
            "verifier SFT teacher runtime import block changed; refusing ambiguous bundle"
        )

    bootstrap = f'''import base64 as _bundle_base64
import sys as _bundle_sys
import types as _bundle_types


def _load_embedded_module(name: str, encoded_source: str):
    module = _bundle_types.ModuleType(name)
    module.__file__ = f"<embedded:{{name}}>"
    _bundle_sys.modules[name] = module
    try:
        source = _bundle_base64.b64decode(encoded_source.encode("ascii")).decode("utf-8")
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    except BaseException:
        _bundle_sys.modules.pop(name, None)
        raise
    return module


_supervision_helper = _load_embedded_module(
    "verifier_gold_teacher_supervision", {_encoded(helper_source)!r}
)
gold = _load_embedded_module(
    "verifier_gold_teacher_runtime", {_encoded(gold_source)!r}
)
DIFF_COMMAND = _supervision_helper.DIFF_COMMAND
build_teacher_supervision_record = _supervision_helper.build_teacher_supervision_record
load_targeted_test_plan = _supervision_helper.load_targeted_test_plan
'''
    bundled = runtime_source.replace(IMPORT_BLOCK, bootstrap, 1)
    compile(bundled, "verifier_sft_teacher_runtime.py", "exec")
    return bundled
