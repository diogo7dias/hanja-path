"""The published layout lives in one place, and the served data must match it.

Level membership, lesson membership and the slot inside a lesson are derived from
these numbers. They used to be scattered magic numbers (600, 1200, 10, 3, 8) in
the generator, and the contract repeated them. Now both read tools/layout.py, and
this test checks the served data really follows it.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import layout
import validate_hanja

SERVED = ROOT / "hanja-data.js"


class LayoutTests(unittest.TestCase):
    def test_levels_split_at_the_documented_cuts(self):
        self.assertEqual(layout.LEVEL_CUTS, (600, 1200))
        self.assertEqual(layout.level_of(0), 0)
        self.assertEqual(layout.level_of(599), 0)
        self.assertEqual(layout.level_of(600), 1)
        self.assertEqual(layout.level_of(1199), 1)
        self.assertEqual(layout.level_of(1200), 2)
        self.assertEqual(layout.level_of(1794), 2)

    def test_lessons_group_ten_characters(self):
        self.assertEqual(layout.LESSON_SIZE, 10)
        self.assertEqual(layout.lesson_of(0), 0)
        self.assertEqual(layout.lesson_of(9), 0)
        self.assertEqual(layout.lesson_of(10), 1)
        self.assertEqual(layout.lesson_pos(10), 0)
        self.assertEqual(layout.lesson_pos(19), 9)

    def test_the_contract_takes_its_limits_from_the_layout(self):
        self.assertEqual(validate_hanja.BASELINE["max_words"], layout.MAX_WORDS)
        self.assertEqual(validate_hanja.BASELINE["max_related"], layout.MAX_RELATED)
        self.assertEqual(validate_hanja.BASELINE["lesson_size"][1], layout.LESSON_SIZE)
        self.assertEqual(validate_hanja.SLOT_RANGE[1], layout.LESSON_SIZE - 1)

    def test_served_data_follows_the_frozen_layout(self):
        payload = validate_hanja.load_served(SERVED)
        seen_in_level = {}
        for index, record in enumerate(payload["hanja"]):
            self.assertEqual(record["lv"], layout.level_of(index), record["c"])
            position = seen_in_level.get(record["lv"], 0)
            seen_in_level[record["lv"]] = position + 1
            self.assertEqual(record["lesson"], layout.lesson_of(position), record["c"])
            self.assertEqual(record["lessonPos"], layout.lesson_pos(position), record["c"])


if __name__ == "__main__":
    unittest.main()
