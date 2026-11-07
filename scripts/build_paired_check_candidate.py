"""Build matched 31B V2 candidates containing an agent-callable check script."""

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "experiments/paired-check-v0/skill"
MODES = ("paired", "repeat")


def payload(source, mode):
    if mode not in MODES:
        raise ValueError("unknown comparison mode")
    files = validate_source_zip(source)
    files["agent.yaml"] += "skills:\n  - skills/repository-check\n"
    files["skills/repository-check/SKILL.md"] = (SKILL / "SKILL.md").read_text()
    script = (SKILL / "scripts/compare.py").read_text()
    expected = 'COMPARISON_MODE = "paired"'
    if script.count(expected) != 1:
        raise ValueError("comparison mode marker changed")
    files["skills/repository-check/scripts/compare.py"] = script.replace(
        expected, f'COMPARISON_MODE = "{mode}"', 1
    )
    return files


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as result:
        for name, body in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 11, 7, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            result.writestr(entry, body.encode())
    return output.getvalue()


def notebook(source):
    archives = {mode: archive(payload(source, mode)) for mode in MODES}
    encoded = {mode: base64.b64encode(data).decode() for mode, data in archives.items()}
    hashes = {mode: hashlib.sha256(data).hexdigest() for mode, data in archives.items()}
    introduction = """# Gemma 4 · Paired repository check v0

Run All on CPU to write `/kaggle/working/submission.zip`. The `ARM` value selects
`paired` (base and current source) or the matched `repeat` control (current source
twice). The agent selects the Python check and decides what to do with its output.

The candidate adds a Skill action to lynnsakurai's Apache-2.0 Budget-Fit V2.
It retains the original 31B model, nine native tools, root prompt, sampling,
8-minute budget, 28-call limit, and 80 turns. Skill discovery adds the ADK tools
for loading and executing the script. Each script invocation runs two checks
with a default of ten seconds per snapshot inside the existing time allowance.

The comparison runner checks which copied repository modules were imported,
returns actual output and exceptions, and leaves the agent's source checkout
available for its next action. A check's output covers the behavior it actually
observes. Independent patch grading remains the outcome measure.

[Original V2 notebook](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue)
· [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
"""
    code = (
        "import base64, hashlib, os\nfrom pathlib import Path\n\n"
        'ARM = "paired"\n'
        f"ARCHIVES = {encoded!r}\nHASHES = {hashes!r}\n"
        "data = base64.b64decode(ARCHIVES[ARM], validate=True)\n"
        "assert hashlib.sha256(data).hexdigest() == HASHES[ARM]\n"
        'output = Path(os.environ.get("OUTPUT_DIR", "/kaggle/working"))\n'
        "output.mkdir(parents=True, exist_ok=True)\n"
        '(output / "submission.zip").write_bytes(data)\n'
        'print("ARM", ARM, "SHA256", HASHES[ARM])\n'
    )
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": [
            {"id": "overview", "cell_type": "markdown", "metadata": {}, "source": introduction},
            {"id": "cpu-builder", "cell_type": "code", "metadata": {}, "source": code,
             "outputs": [], "execution_count": None},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--notebook", type=Path, required=True)
    options = parser.parse_args()
    document = notebook(options.source_zip.read_bytes())
    options.notebook.parent.mkdir(parents=True, exist_ok=True)
    options.notebook.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(options.notebook)


if __name__ == "__main__":
    main()
