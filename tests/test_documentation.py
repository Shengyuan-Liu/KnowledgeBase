"""Check basic integrity of the project's Markdown documentation."""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = sorted((ROOT / "docs").rglob("*.md"))


class DocumentationTests(unittest.TestCase):
    def test_documents_have_a_title_and_balanced_code_fences(self):
        self.assertTrue(DOCUMENTS, "Expected project documentation")
        for path in DOCUMENTS:
            with self.subTest(document=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("# "), "Missing document title")
                fences = re.findall(r"^```.*$", content, flags=re.MULTILINE)
                self.assertEqual(len(fences) % 2, 0, "Unclosed code fence")

    def test_relative_markdown_links_resolve(self):
        for path in DOCUMENTS:
            content = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", content):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(document=path.name, target=target):
                    self.assertFalse(Path(parsed.path).is_absolute())
                    resolved = (path.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    self.assertTrue(resolved.exists(), "Broken local document link")

    def test_documentation_contains_no_chinese_text(self):
        for path in DOCUMENTS:
            with self.subTest(document=path.name):
                self.assertIsNone(
                    re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", path.read_text(encoding="utf-8")),
                    "Project documentation must use English",
                )


if __name__ == "__main__":
    unittest.main()
