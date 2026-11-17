"""Build the one-mechanism 31B candidate from the byte-pinned Toolcap60 control."""

import hashlib
import io
from pathlib import Path
import zipfile

from scripts.build_toolcap60_timeout_recovery import STAMP, build as build_control


CONTROL_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
SKILL_NAME = "existing-test-retrieval"
SKILL = Path(__file__).resolve().parents[1] / "experiments" / "solver-v3" / SKILL_NAME


def build(source):
    control = build_control(source)
    if hashlib.sha256(control).hexdigest() != CONTROL_SHA:
        raise ValueError("Scored 0.18 control archive changed")
    with zipfile.ZipFile(io.BytesIO(control)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    agent = files["agent.yaml"].decode()
    if "skills:" in agent or agent.count("\ntools:") != 1:
        raise ValueError("Unrecognized control agent tool declaration")
    files["agent.yaml"] = (agent.rstrip() + f"\nskills:\n  - skills/{SKILL_NAME}\n").encode()
    files["prompts/system.md"] += (
        b"\n\nIf the issue names a concrete function, class, or exception, "
        b"use the existing-test-retrieval skill once before editing to check "
        b"whether an existing assertion constrains the repair. Load only this "
        b"skill. Continue immediately if it returns no match.\n"
    )
    for path in (SKILL / "SKILL.md", SKILL / "scripts" / "retrieve.py"):
        files[f"skills/{SKILL_NAME}/{path.relative_to(SKILL)}"] = path.read_bytes()
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, mode="w") as archive:
            for path, body in sorted(files.items()):
                info = zipfile.ZipInfo(path, date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, body)
        return control, buffer.getvalue()
