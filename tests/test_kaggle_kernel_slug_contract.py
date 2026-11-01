import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = [
    ROOT / ".github" / "workflows" / "run-verifier-gold-sweep.yml",
    ROOT / ".github" / "workflows" / "run-verifier-blind-gold-sweep.yml",
    ROOT / ".github" / "workflows" / "run-verifier-training-gold-sweep.yml",
]


def kaggle_slug(title: str) -> str:
    """Mirror the ordinary Kaggle title -> notebook slug normalization we rely on."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def extract_contract(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    ref_match = re.search(r"^\s*KERNEL_REF:\s*([^\s]+)\s*$", text, flags=re.MULTILINE)
    id_match = re.search(r'^\s*"id":\s*"([^"]+)"', text, flags=re.MULTILINE)
    title_match = re.search(r'^\s*"title":\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not ref_match or not id_match or not title_match:
        raise AssertionError(f"missing literal Kaggle kernel contract in {path}")
    return ref_match.group(1), id_match.group(1), title_match.group(1)


class KaggleKernelSlugContractTests(unittest.TestCase):
    def test_kernel_ref_metadata_id_and_title_slug_are_identical(self):
        for path in WORKFLOWS:
            with self.subTest(workflow=path.name):
                kernel_ref, metadata_id, title = extract_contract(path)
                self.assertEqual(kernel_ref, metadata_id)
                owner, slug = metadata_id.split("/", 1)
                self.assertEqual(owner, "kolihhan")
                self.assertEqual(
                    slug,
                    kaggle_slug(title),
                    msg=(
                        f"{path.name}: Kaggle resolves title {title!r} to "
                        f"{kaggle_slug(title)!r}, so status/log/output must poll that slug"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
