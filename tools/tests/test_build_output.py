"""Slice 1: the generator's output must be byte-identical to the file the site loads.

The site loads /hanja-data.js from the repo root. If the generator and that file
ever disagree, learners see data the build did not produce.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "tools" / "build.py"
SERVED = ROOT / "hanja-data.js"


class BuildOutputTests(unittest.TestCase):
    def test_build_reproduces_the_served_file_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "hanja-data.js"
            proc = subprocess.run(
                [sys.executable, str(BUILD), "--out", str(out)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.exists(), "build.py wrote no file")
            self.assertEqual(out.read_bytes(), SERVED.read_bytes())


if __name__ == "__main__":
    unittest.main()
