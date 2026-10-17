"""Slice 4: the writer validates before it touches the served file.

A build that writes a broken dataset is worse than a build that fails: the site
would serve data nobody reviewed. So the writer must either produce a valid file
or change nothing at all.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
import validate_hanja
import write_data

SENTINEL = "/* untouched */\nwindow.HANJA = {};\n"


class WriterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def sentinel_target(self):
        target = self.dir / "hanja-data.js"
        target.write_text(SENTINEL, encoding="utf-8")
        return target

    def test_invalid_payload_leaves_the_target_untouched(self):
        target = self.sentinel_target()
        payload, expect = fixtures.mini()
        payload["total"] = 99
        with self.assertRaises(write_data.ContractError):
            write_data.write(payload, target, expect)
        self.assertEqual(target.read_text(encoding="utf-8"), SENTINEL)

    def test_no_partial_file_is_left_behind(self):
        target = self.sentinel_target()
        payload, expect = fixtures.mini()
        payload["hanja"][0]["idx"] = 7
        with self.assertRaises(write_data.ContractError):
            write_data.write(payload, target, expect)
        self.assertEqual(sorted(path.name for path in self.dir.iterdir()), ["hanja-data.js"])

    def test_valid_payload_writes_the_wrapped_file(self):
        target = self.dir / "hanja-data.js"
        payload, expect = fixtures.mini()
        write_data.write(payload, target, expect)
        text = target.read_text(encoding="utf-8")
        self.assertEqual(validate_hanja.validate_text(text), [])
        self.assertEqual(validate_hanja.validate(validate_hanja.parse_served(text), expect), [])
        self.assertIn(json.dumps(payload, ensure_ascii=False), text)


if __name__ == "__main__":
    unittest.main()
