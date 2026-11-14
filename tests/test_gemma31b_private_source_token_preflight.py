"""Synthetic processor-chat-template token count behavior; no HF models."""
import unittest
from kaggle.gemma31b_private_source_token_preflight import lengths

class FakeProcessor:
    def apply_chat_template(self,messages,tokenize,add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert messages[0]["content"][0]["type"]=="text"
        return "<bos><start_of_turn>user\nSynthetic question<end_of_turn>\n<start_of_turn>model\n"

class FakeTokenizer:
    eos_token_id=2
    def encode(self,text,add_special_tokens):
        assert add_special_tokens is False
        return [3]*len(text.split())

class SourceTokenTests(unittest.TestCase):
    def test_processor_template_precedes_completion_without_truncation(self):
        rows=[{"prompt":"Synthetic question","completion":"diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-0\n+1\n",
               "repo_hash":"safe_hash"}]
        data=lengths(FakeProcessor(),FakeTokenizer(),rows)
        self.assertEqual(len(data),1)
        self.assertGreater(data[0]["total_tokens"],data[0]["source_tokens"])
        self.assertEqual(data[0]["completion_tokens"],
                         len(FakeTokenizer().encode(rows[0]["completion"],add_special_tokens=False))+1)

if __name__=="__main__":
    unittest.main()
