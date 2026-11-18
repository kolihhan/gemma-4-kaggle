"""Single pre-registered Gemma 31B conditional caller-hop official scoring attempt.

Reuses repository's existing authenticated quota, remote private CPU
builder and competition-submit machinery. No development GPU. Fail closed
if a prior active scorer or today's one-slot limit blocks submission.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from scripts import submit_existing_test_retrieval_official_once_20261117 as existing
from scripts.build_caller_hop_v1 import build as caller_hop_build
from scripts.build_toolcap60_timeout_recovery import build as scored_control_build
from scripts.prepare_public_budgetfit_v2 import validate_source_zip
from scripts.submit_v2_toolcap60_official_once import compile_without_inference

KERNEL = "kolihhan/gemma4-caller-hop-31b-nov18-v1"
MARKER = "caller-hop-31b-one-variable-20261118"
ROOT = Path("/tmp/gemma4-caller-hop-official-once")
EXPECTED_CONTROL_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
HYPOTHESIS = {
    "change": "one conditional native caller/callee graph lookup when same-name/wrapper search is ambiguous",
    "fixed_model": "gemma-4-31b-it-qat-w4a16-ct",
    "fixed_budget": "5min 60tools 80turns",
    "predicted_public_gain": "+0.017 if 1 additional of inferred 58 issues passes; highly uncertain",
    "kill": "official Public <= 0.18, blank score, model ignoring graph evidence, or more unresolved patches",
    "not_breakthrough": "single score delta below ~2*SE cannot establish a mechanism",
    "prior_scored_best": "0.18 #58183466",
}


def _reuse_legacy_submission_path() -> None:
    # Existing tested Kaggle CPU builder + official submission API path;
    # state changes only inside this Python process.
    existing.KERNEL = KERNEL
    existing.MARKER = MARKER
    existing.ROOT = ROOT


def quota():
    _reuse_legacy_submission_path()
    return existing.quota()


def prepare():
    _reuse_legacy_submission_path()
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("REFUSE_NONEMPTY_TARGET")
    source_folder = ROOT / "source"
    source_folder.mkdir(parents=True)
    subprocess.run(
        ["kaggle", "kernels", "output", existing.SOURCE, "-p", str(source_folder), "-o"],
        check=True, timeout=200, stdout=subprocess.DEVNULL,
    )
    source = (source_folder / "submission.zip").read_bytes()
    validate_source_zip(source)
    control = scored_control_build(source)
    if hashlib.sha256(control).hexdigest() != EXPECTED_CONTROL_SHA:
        raise RuntimeError("SCORED_018_CONTROL_HASH_DRIFT")
    candidate = caller_hop_build(source)
    with zipfile.ZipFile(io.BytesIO(control)) as z:
        original = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(io.BytesIO(candidate)) as z:
        if z.testzip() is not None:
            raise RuntimeError("CORRUPT_CANDIDATE_ZIP")
        treatment = {n: z.read(n) for n in z.namelist()}
    if set(treatment) != set(original):
        raise RuntimeError("BASELINE_MEMBER_SET_DRIFT")
    if {k for k in original if original[k] != treatment[k]} != {"prompts/system.md"}:
        raise RuntimeError("CANDIDATE_MUST_CHANGE_PROMPT_ONLY")
    if treatment["agent.yaml"] != original["agent.yaml"]:
        raise RuntimeError("MODEL_OR_NATIVE_TOOL_DRIFT")
    if treatment["eval_config.yaml"] != original["eval_config.yaml"]:
        raise RuntimeError("TASK_BUDGET_DRIFT")
    if treatment["configs/sampling.yaml"] != original["configs/sampling.yaml"]:
        raise RuntimeError("SAMPLING_DRIFT")
    # Official ADK contract, without LLM or tools being run.
    compile_without_inference(candidate)
    digest = hashlib.sha256(candidate).hexdigest()
    (ROOT / "candidate.zip").write_bytes(candidate)
    (ROOT / "candidate.sha256").write_text(digest)
    (ROOT / "hypothesis.json").write_text(json.dumps(HYPOTHESIS, indent=2))
    import nbformat
    encoded = base64.b64encode(candidate).decode("ascii")
    code = (
        "import base64,hashlib\nfrom pathlib import Path\n"
        + f"data=base64.b64decode({encoded!r},validate=True)\n"
        + f"want={digest!r}\n"
        + "assert hashlib.sha256(data).hexdigest()==want\n"
        + "Path('/kaggle/working/submission.zip').write_bytes(data)\n"
        + "print('GEMMA_CALLER_HOP_BUILDER_HASH='+want)\n"
    )
    compile(code, 'caller_hop_private_cpu_builder.py', 'exec')
    nb = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "31B one-hop conditional caller localization; pinned Toolcap60 scored control; "
            "private CPU-only submission ZIP builder, no model execution."
        ),
        nbformat.v4.new_code_cell(code),
    ])
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3",
    }
    nbformat.validate(nb)
    folder = ROOT / "kernel"
    folder.mkdir()
    (folder / "builder.ipynb").write_text(nbformat.writes(nb))
    meta = {
        "id": KERNEL, "title": KERNEL.split("/")[-1],
        "code_file": "builder.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": False, "enable_tpu": False, "enable_internet": False,
        "competition_sources": [existing.COMPETITION],
        "dataset_sources": [], "kernel_sources": [], "model_sources": [],
    }
    (folder / "kernel-metadata.json").write_text(json.dumps(meta, sort_keys=True, indent=2))
    print("GEMMA_CALLER_HOP_SOURCE_CONTROL_SHA256="+EXPECTED_CONTROL_SHA, flush=True)
    print("GEMMA_CALLER_HOP_CANDIDATE_SHA256="+digest, flush=True)
    print("GEMMA_CALLER_HOP_OFFICIAL_CPU_COMPILE=PASS", flush=True)
    print("GEMMA_NEW_GPU_INFERENCE=FALSE", flush=True)


def submit():
    _reuse_legacy_submission_path()
    # The reused route rechecks authenticated quota / active scorer BEFORE
    # pushing the private CPU builder and again before the official submit.
    # It also refuses duplicate marker, non-new kernel and byte-mismatched ZIP.
    # Final receipt lookup only; NEVER poll a pending competition score.
    return existing.submit()


if __name__ == "__main__":
    modes = {"quota": quota, "prepare": prepare, "submit": submit}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        raise SystemExit("usage: python -m scripts.submit_caller_hop_v1_once quota|prepare|submit")
    modes[sys.argv[1]]()
