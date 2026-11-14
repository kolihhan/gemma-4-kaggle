"""Synthetic processor-chat-template token count behavior; no HF models."""
import unittest
from kaggle.gemma31b_private_source_token_preflight import lengths, pack_completion_only

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
    def test_completion_only_labels_exclude_all_issue_tokens(self):
        row={"prompt":"Synthetic issue with redacted private context",
             "completion":"diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-0\n+1\n",
             "repo_hash":"synthetic"}
        p=pack_completion_only(FakeProcessor(),FakeTokenizer(),row,max_tokens=1024)
        n=p["source_tokens"]
        self.assertGreater(n,0)
        self.assertEqual(p["input_ids"][:n], [3]*n)
        self.assertEqual(p["labels"][:n], [-100]*n)
        self.assertEqual(p["labels"][n:-1],p["input_ids"][n:-1])
        self.assertEqual(p["labels"][-1],FakeTokenizer.eos_token_id)
        self.assertEqual(len(p["input_ids"]),len(p["labels"]))
        self.assertEqual(len(p["attention_mask"]),len(p["input_ids"]))
        self.assertEqual(p["labels"].count(-100),n)
        with self.assertRaisesRegex(ValueError,"no_truncation"):
            pack_completion_only(FakeProcessor(),FakeTokenizer(),row,max_tokens=n+1)

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
