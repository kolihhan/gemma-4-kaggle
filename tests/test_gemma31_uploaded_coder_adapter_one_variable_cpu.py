"""CPU-only regression checks for the exact 0.18 + 31B coder LoRA gate."""
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from scripts import gemma31_uploaded_coder_adapter_one_variable_cpu as gate

def baseline():
    m={
        "agent.yaml":f"agent_class: LlmAgent\nmodel: {gate.MODEL}\ninstruction: !include prompts/system.md\n",
        "prompts/system.md":"fixed scored instructions\n",
        "configs/sampling.yaml":"thinking_config:\n  thinking_budget: 4096\n",
        "eval_config.yaml":"evaluation:\n  max_time_minutes: 5\n  max_tool_calls: 60\n  max_turns: 80\n",
    }
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for k,v in m.items():z.writestr(k,v)
    return out.getvalue(),m

def adapter(directory, *, nonzero=True, nonfinite=False):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    cfg={"base_model_name_or_path":"google/"+gate.MODEL,
         "r":16,"lora_alpha":16,"target_modules":["down_proj","o_proj","q_proj"]}
    (directory/"adapter_config.json").write_text(json.dumps(cfg))
    head={}
    body=b""
    for layer in range(30):
        for proj in ("q_proj","o_proj","down_proj"):
            for ab in ("A","B"):
                key=f"base_model.model.model.language_model.layers.{layer}.mlp.{proj}.lora_{ab}.weight"
                value=b"\x80\x3f\x00\x40"
                if ab=="B" and not nonzero:value=b"\x00\x00\x00\x00"
                if ab=="A" and nonfinite and layer==0 and proj=="q_proj":value=b"\x80\x7f\x80\x3f"
                head[key]={"dtype":"BF16","shape":[2],"data_offsets":[len(body),len(body)+len(value)]}
                body+=value
    header=json.dumps(head).encode()
    (directory/"adapter_model.safetensors").write_bytes(struct.pack("<Q",len(header))+header+body)
    return directory

class TestOneVariableGate(unittest.TestCase):
    def test_exact_control_differential(self):
        raw, originals=baseline()
        old=gate.CONTROL_SHA
        with tempfile.TemporaryDirectory() as temp:
            try:
                gate.CONTROL_SHA=hashlib.sha256(raw).hexdigest()
                new, metadata=gate.package(raw,adapter(Path(temp)/"main_lora"))
                self.assertEqual(metadata["modules"],90)
                self.assertEqual(metadata["status"],"PACKAGED_CPU_ONLY_NOT_SCORED")
                with zipfile.ZipFile(io.BytesIO(new)) as z:
                    self.assertEqual(len(z.namelist()),6)
                    for name in ("prompts/system.md","configs/sampling.yaml","eval_config.yaml"):
                        self.assertEqual(z.read(name),originals[name].encode())
                    self.assertEqual(z.read("agent.yaml").decode().replace("\nadapter: main_lora",""),originals["agent.yaml"])
            finally:
                gate.CONTROL_SHA=old

    def test_wrong_control_hash_rejected(self):
        raw,_=baseline()
        with self.assertRaisesRegex(ValueError,"not the score-verified"):gate.control(raw)

    def test_missing_weights_rejected(self):
        raw,_=baseline()
        with tempfile.TemporaryDirectory() as d:
            old=gate.CONTROL_SHA
            try:
                gate.CONTROL_SHA=hashlib.sha256(raw).hexdigest()
                with self.assertRaises(FileNotFoundError):gate.package(raw,Path(d))
            finally:gate.CONTROL_SHA=old

    def test_zero_lora_b_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=adapter(Path(d)/"a",nonzero=False)
            with self.assertRaisesRegex(ValueError,"zero"):gate.inspect_weights(a/"adapter_model.safetensors")

    def test_nonfinite_lora_a_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=adapter(Path(d)/"a",nonfinite=True)
            with self.assertRaisesRegex(ValueError,"nonfinite"):gate.inspect_weights(a/"adapter_model.safetensors")

if __name__=="__main__":
    unittest.main()
