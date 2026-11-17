"""Render private, separately mounted 31B solver and native CPU grader."""

import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_gemma31_existing_tests import build

IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
DATASET = "metric/gemma-4-developer-agent-wheelhouse"
SOLVER_INPUTS = "kolihhan/gemma4-pair31-solver-source-nov17-v1"
CLICK_TESTS = "kolihhan/gemma4-click16-assets-nov17-v2"
SOLVERS = ["kolihhan/gemma4-test-retrieval31a-nov17", "kolihhan/gemma4-test-retrieval31b-nov17"]
GRADER = "kolihhan/gemma4-test-retrieval31-grades-nov17"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["solve", "grade"])
    parser.add_argument("--shard", type=int, choices=[0, 1], default=0)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(Path("experiments/solver-v3/gemma31-existing-test-retrieval-20261117.json").read_text())
    lock = Path("docs/evaluation/gemma-31-matched-validation-membership-2026-11-17.json").read_bytes()
    if sha256(lock).hexdigest() != plan["membership_sha256"]:
        raise ValueError("Frozen cohort changed")
    cases = json.loads(lock)["cases"]
    if len(cases) != 31 or len({case["instance_id"] for case in cases}) != 31:
        raise ValueError("Expected all 31 unique paired cases")
    assets = {"PLAN": plan, "MODEL_NAME": MODEL}
    meta = {
        "code_file": "experiment.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": args.phase == "solve", "enable_tpu": False,
        "enable_internet": False, "dataset_sources": [DATASET], "docker_image": IMAGE,
    }
    if args.phase == "solve":
        start, stop = [(0, 16), (16, 31)][args.shard]
        control, treatment = build(args.source.read_bytes())
        assets.update(CASES=[{k: row[k] for k in ("instance_id", "repo")} for row in cases],
                      OFFSET=start, STOP=stop, ARM_ZIPS={
                          k: base64.b64encode(v).decode()
                          for k, v in {"control": control, "retrieval": treatment}.items()
                      })
        prefix = Path("kaggle/verifier_baseline_runtime.py").read_text().split("\ndef materialize_submission", 1)[0]
        body = Path("kaggle/gemma31_pair_solver.py").read_text()
        meta.update(id=SOLVERS[args.shard], competition_sources=[],
                    kernel_sources=[SOLVER_INPUTS], model_sources=[f"google/gemma-4/Other/{MODEL}/2"])
        print("CANDIDATE_ARCHIVE_SHA256=" + sha256(treatment).hexdigest())
    else:
        assets.update(CASES=cases, CLICK_LOCK=json.loads(lock)["click_control_cohort_sha256"])
        prefix = Path("kaggle/paired_three_task_integrity_cpu.py").read_text().split("\nasync def evaluate_controls", 1)[0]
        body = Path("kaggle/gemma31_pair_grade.py").read_text()
        meta.update(id=GRADER, competition_sources=["gemma-4-developer-agent"],
                    kernel_sources=[*SOLVERS, CLICK_TESTS], model_sources=[])
    runtime = "\n".join([prefix, *(f"{key} = {value!r}" for key, value in assets.items()), body])
    compile(runtime, "experiment.py", "exec")
    meta["title"] = meta["id"].split("/")[-1]
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "experiment.py").write_text(runtime)
    (args.out / "kernel-metadata.json").write_text(json.dumps(meta, sort_keys=True))


if __name__ == "__main__":
    main()
