import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


def kaggle_slug(title: str) -> str:
    """Mirror the ordinary Kaggle title -> notebook slug normalization we rely on."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def extract_contract(path: Path) -> tuple[str, str, str] | None:
    text = path.read_text(encoding="utf-8")
    ref_match = re.search(r"^\s*KERNEL_REF:\s*([^\s]+)\s*$", text, flags=re.MULTILINE)
    id_match = re.search(r'^\s*"id":\s*"([^"]+)"', text, flags=re.MULTILINE)
    title_match = re.search(r'^\s*"title":\s*"([^"]+)"', text, flags=re.MULTILINE)
    matches = (ref_match, id_match, title_match)
    if not any(matches):
        return None
    if not all(matches):
        # Some workflows may construct kernel metadata dynamically; this guard
        # is intentionally for workflows whose identity is fully literal and
        # therefore mechanically checkable.
        return None
    assert ref_match and id_match and title_match
    return ref_match.group(1), id_match.group(1), title_match.group(1)


class KaggleKernelSlugContractTests(unittest.TestCase):
    def test_all_literal_kernel_contracts_match_kaggle_title_slug(self):
        checked = 0
        for path in sorted(WORKFLOW_DIR.glob("*.yml")):
            contract = extract_contract(path)
            if contract is None:
                continue
            checked += 1
            with self.subTest(workflow=path.name):
                kernel_ref, metadata_id, title = contract
                self.assertEqual(
                    kernel_ref,
                    metadata_id,
                    msg=f"{path.name}: poll/output ref must equal pushed metadata id",
                )
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
        self.assertGreaterEqual(checked, 3, "expected multiple literal Kaggle kernel contracts")


if __name__ == "__main__":
    unittest.main()
