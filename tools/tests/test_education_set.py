"""The word-bank tool must read the education set, not the served site file.

build_words.py needs the list of 1795 education characters. It used to parse that
list out of the served hanja-data.js, which is the file the generator writes, so
the two scripts depended on each other. The list now travels in tools/educ.json.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import education_set
import validate_hanja

BUILD = TOOLS / "build.py"
EDUC = TOOLS / "educ.json"
SERVED = ROOT / "hanja-data.js"
WORD_BANK_TOOL = TOOLS / "build_words.py"


class EducationSetTests(unittest.TestCase):
    def test_it_lists_the_education_characters_with_their_readings(self):
        education = education_set.load(EDUC)
        self.assertEqual(len(education), 1795)
        self.assertEqual(education["家"]["r"], "가")

    def test_it_does_not_need_the_served_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            alone = Path(tmp) / "educ.json"
            education_set.dump(validate_hanja.load_served(SERVED), alone)
            self.assertEqual(len(education_set.load(alone)), 1795)

    def test_its_characters_match_the_served_file(self):
        payload = validate_hanja.load_served(SERVED)
        self.assertEqual(
            set(education_set.load(EDUC)),
            {record["c"] for record in payload["hanja"]},
        )

    def test_build_refreshes_the_education_set_it_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            educ = Path(tmp) / "educ.json"
            out = Path(tmp) / "hanja-data.js"
            proc = subprocess.run(
                [sys.executable, str(BUILD), "--out", str(out), "--educ", str(educ)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(len(education_set.load(educ)), 1795)

    def test_word_bank_no_longer_reads_the_served_file(self):
        source = WORD_BANK_TOOL.read_text(encoding="utf-8")
        self.assertNotIn("hanja-data.js", source)
        self.assertIn("education_set", source)


if __name__ == "__main__":
    unittest.main()
