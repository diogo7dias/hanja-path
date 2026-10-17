"""Slice 2: the validator CLI must accept the file the site actually loads."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "tools" / "validate_hanja.py"
SERVED = ROOT / "hanja-data.js"


class ValidateCliTests(unittest.TestCase):
    def test_served_file_passes_with_no_arguments(self):
        proc = subprocess.run(
            [sys.executable, str(VALIDATE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()
