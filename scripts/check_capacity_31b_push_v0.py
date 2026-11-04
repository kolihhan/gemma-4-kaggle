#!/usr/bin/env python3
"""Fail closed on Kaggle kernels push output, including zero-exit quota errors."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def classify_push(output: str, client_exit_code: int) -> str:
    if client_exit_code != 0:
        return "CLIENT_EXIT_NONZERO"
    if re.search(r"Kernel push error\s*:", output, flags=re.IGNORECASE):
        if re.search(r"maximum weekly gpu quota|gpu quota.*reached", output, re.IGNORECASE):
            return "BLOCKED_GPU_QUOTA"
        return "REJECTED"
    if re.search(r"Kernel version \d+ successfully pushed", output, re.IGNORECASE):
        return "CONFIRMED"
    return "UNCONFIRMED"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--client-exit-code", type=int, required=True)
    args = p.parse_args()
    classification = classify_push(
        args.log.read_text(encoding="utf-8", errors="replace"), args.client_exit_code
    )
    print("CAPACITY_31B_KERNEL_PUSH_CLASS=", classification)
    if classification == "BLOCKED_GPU_QUOTA":
        print("CAPACITY_31B_GPU_RUN=NOT_STARTED")
    if classification != "CONFIRMED":
        print("CAPACITY_31B_PUSH_GATE=FAIL_CLOSED")
        return 2
    print("CAPACITY_31B_PUSH_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
