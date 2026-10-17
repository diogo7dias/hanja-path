"""The order and the slot numbering of the served array are part of the contract.

Pages never sort the dataset themselves: they filter it and trust the order, and
they derive lesson membership from lesson and lessonPos. A reshuffled or gapped
array silently changes every lesson page, so it must fail the build.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
import validate_hanja

LESSON_RANGE = (0, 59)
SLOT_RANGE = (0, 9)


def problems(payload, expect):
    return validate_hanja.validate(payload, expect)


class SequenceTests(unittest.TestCase):
    def test_slots_must_be_dense_from_zero_inside_a_lesson(self):
        payload, expect = fixtures.mini()
        payload["hanja"][1]["lv"] = 0
        payload["hanja"][1]["lesson"] = 0
        payload["hanja"][1]["lessonPos"] = 5  # gap: slot 1 is missing
        payload["levels"][0]["n"] = 2
        payload["levels"] = payload["levels"][:1]
        expect["level_counts"] = (2,)
        self.assertTrue(any("lessonPos" in p for p in problems(payload, expect)))

    def test_entries_must_be_ordered_by_level_lesson_and_slot(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0], payload["hanja"][1] = payload["hanja"][1], payload["hanja"][0]
        self.assertTrue(any("order" in p.lower() for p in problems(payload, expect)))

    def test_lesson_index_must_be_within_range(self):
        payload, expect = fixtures.mini()
        payload["hanja"][2]["lesson"] = 60
        self.assertTrue(any("lesson" in p for p in problems(payload, expect)))

    def test_slot_must_be_within_range(self):
        payload, expect = fixtures.mini()
        payload["hanja"][2]["lessonPos"] = 10
        self.assertTrue(any("lessonPos" in p for p in problems(payload, expect)))

    def test_level_must_be_a_declared_level_id(self):
        payload, expect = fixtures.mini()
        payload["hanja"][2]["lv"] = 9
        self.assertTrue(any("lv" in p for p in problems(payload, expect)))

    def test_lesson_bucket_size_must_stay_inside_the_expected_range(self):
        payload, expect = fixtures.mini(count=2)
        payload["hanja"][1]["lv"] = 0  # two entries in one lesson, below the expected minimum
        payload["levels"] = payload["levels"][:1]
        payload["levels"][0]["n"] = 2
        expect["level_counts"] = (2,)
        expect["lesson_size"] = (3, 10)
        self.assertTrue(any("lesson" in p for p in problems(payload, expect)))


if __name__ == "__main__":
    unittest.main()
