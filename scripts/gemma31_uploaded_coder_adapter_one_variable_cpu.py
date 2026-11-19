"""CPU-only matched Gemma 31B LoRA packaging gate.

Never runs a model or submits to Kaggle. Requires the exact scored 0.18 ZIP,
then adds only one root-agent adapter reference and the validated adapter files.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import zipfile

CONTROL_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
FILES = frozenset(("agent.yaml", "prompts/system.md", "configs/sampling.yaml", "eval_config.yaml"))
PREFIX = "adapters/main_lora/"

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def control(blob: bytes) -> dict[str, bytes]:
    if sha(blob) != CONTROL_SHA:
        raise ValueError("STOP: not the score-verified 0.18 ZIP")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if set(z.namelist()) != FILES or len(z.namelist()) != 4 or z.testzip():
            raise ValueError("STOP: wrong control ZIP members/corruption")
        d = {k: z.read(k) for k in FILES}
    agent = d["agent.yaml"].decode()
    ev = d["eval_config.yaml"].decode()
    if len(re.findall(r"(?m)^model:\s*" + re.escape(MODEL) + r"\s*$", agent)) != 1:
        raise ValueError("STOP: different control model")
    if re.search(r"(?m)^adapter\s*:", agent):
        raise ValueError("STOP: control already has an adapter")
    for key, value in (("max_time_minutes", 5), ("max_tool_calls", 60), ("max_turns", 80)):
        if len(re.findall(r"(?m)^\s*" + key + rf":\s*{value}\s*$", ev)) != 1:
            raise ValueError("STOP: scored budget changed")
    if "thinking_budget: 4096" not in d["configs/sampling.yaml"].decode():
        raise ValueError("STOP: thinking budget changed")
    return d

def inspect_weights(path: Path) -> dict:
    with path.open("rb") as f:
        size = f.seek(0, 2)
        if size < 16: raise ValueError("truncated safetensors")
        f.seek(0)
        header_n = struct.unpack("<Q", f.read(8))[0]
        if header_n > min(size - 8, 8 * 1024 * 1024):
            raise ValueError("bad safetensors header")
        header = json.loads(f.read(header_n))
        header.pop("__metadata__", None)
        aa = {k.removesuffix(".lora_A.weight") for k in header if k.endswith(".lora_A.weight")}
        bb = {k.removesuffix(".lora_B.weight") for k in header if k.endswith(".lora_B.weight")}
        if aa != bb or len(aa) != 90 or len(header) != 180:
            raise ValueError("STOP: different/missing 90 adapter module pairs")
        offset0 = 8 + header_n
        intervals = []
        active_b = False
        for key, v in header.items():
            lo, hi = v["data_offsets"]
            shape = v["shape"]
            if v["dtype"] != "BF16" or not shape or any(type(x) is not int or x <= 0 for x in shape):
                raise ValueError("unexpected tensor dtype/shape")
            if not (type(lo) is int and type(hi) is int and
                    0 <= lo < hi <= size - offset0 and hi - lo == math.prod(shape) * 2):
                raise ValueError("bad tensor offsets")
            intervals.append((lo, hi))
            f.seek(offset0 + lo)
            raw = f.read(hi - lo)
            for i in range(0, len(raw), 2):
                x = raw[i] | (raw[i + 1] << 8)
                if (x & 0x7F80) == 0x7F80:
                    raise ValueError("STOP: nonfinite LoRA A/B weight")
                if key.endswith(".lora_B.weight") and (x & 0x7FFF):
                    active_b = True
        intervals.sort()
        if intervals[0][0] != 0 or intervals[-1][1] != size - offset0 or any(
            a[1] != b[0] for a,b in zip(intervals, intervals[1:])
        ):
            raise ValueError("STOP: inconsistent tensor byte coverage")
        if not active_b:
            raise ValueError("STOP: all LoRA B tensors are zero")
    return {"modules": 90, "adapter_bytes": size, "weights_sha256": sha(path.read_bytes())}

def package(scored_zip: bytes, adapter_dir: Path) -> tuple[bytes,dict]:
    d = control(scored_zip)
    cfg_path = adapter_dir / "adapter_config.json"
    weights_path = adapter_dir / "adapter_model.safetensors"
    if not cfg_path.is_file() or not weights_path.is_file():
        raise FileNotFoundError("Missing real adapter_config.json / adapter_model.safetensors")
    cfg_bytes = cfg_path.read_bytes()
    cfg = json.loads(cfg_bytes)
    if (cfg.get("base_model_name_or_path") != "google/" + MODEL or
        cfg.get("r") != 16 or sorted(cfg.get("target_modules",[])) !=
        ["down_proj", "o_proj", "q_proj"]):
        raise ValueError("STOP: adapter base/rank/target lineage differs from uploaded notebook")
    meta = inspect_weights(weights_path)
    base_agent = d["agent.yaml"].decode()
    target = "model: " + MODEL
    edited = base_agent.replace(target, target + "\nadapter: main_lora", 1)
    if edited == base_agent or edited.count("adapter: main_lora") != 1:
        raise ValueError("STOP: cannot inject exactly one adapter reference")
    d["agent.yaml"] = edited.encode()
    d[PREFIX + "adapter_config.json"] = cfg_bytes
    d[PREFIX + "adapter_model.safetensors"] = weights_path.read_bytes()
    with io.BytesIO() as output:
        with zipfile.ZipFile(output, "w") as z:
            for name, b in sorted(d.items()):
                info = zipfile.ZipInfo(name, date_time=(2026,11,19,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info,b)
        candidate = output.getvalue()
    with zipfile.ZipFile(io.BytesIO(candidate)) as z:
        if z.testzip(): raise RuntimeError("candidate zip corrupt")
        assert z.read("agent.yaml").decode().replace("\nadapter: main_lora","",1) == base_agent
        for name, b in control(scored_zip).items():
            if name != "agent.yaml" and z.read(name) != b:
                raise RuntimeError("STOP: other scored config changed")
    return candidate, {
        "status":"PACKAGED_CPU_ONLY_NOT_SCORED",
        "champion_zip_sha256":sha(scored_zip),
        "candidate_zip_sha256":sha(candidate),
        "fixed_model":MODEL,
        "fixed_budget":"5min / 60 calls / 80 turns",
        "only_change":"adapter reference plus 2 adapter files",
        **meta
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--scored-zip",type=Path,required=True)
    p.add_argument("--adapter-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists(): raise FileExistsError("refuse overwrite")
    blob, report = package(args.scored_zip.read_bytes(),args.adapter_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(blob)
    print(json.dumps(report,indent=2))
    print("NO MODEL INFERENCE / NO KAGGLE SUBMISSION / NO SCORE CLAIM")

if __name__ == "__main__":
    main()
