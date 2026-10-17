"""The repo serves one copy of the site, generated from one place.

mockups/ used to hold a byte-identical second copy of all 12 site files, tracked
in git and published under /mockups/. Every fix had to be applied twice, and the
generator wrote into it. These tests keep that from coming back.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepoLayoutTests(unittest.TestCase):
    def test_the_duplicate_site_tree_is_gone(self):
        self.assertFalse((ROOT / "mockups").exists(), "mockups/ is back; the site must live once")

    def test_the_duplicate_name_is_ignored_by_git(self):
        lines = [line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
        self.assertIn("mockups/", lines)

    def test_pages_load_the_data_file_from_the_repo_root(self):
        pages = sorted(ROOT.glob("*.html"))
        self.assertEqual(len(pages), 11)
        for page in pages:
            for source in re.findall(r'src="([^"]+)"', page.read_text(encoding="utf-8")):
                if source.endswith("hanja-data.js"):
                    self.assertEqual(source, "hanja-data.js", page.name)

    def test_the_generator_writes_the_served_file_by_default(self):
        source = (ROOT / "tools" / "build.py").read_text(encoding="utf-8")
        self.assertIn('OUT = ROOT / "hanja-data.js"', source)


if __name__ == "__main__":
    unittest.main()
