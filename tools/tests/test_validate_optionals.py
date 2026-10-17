"""Optional fields are all-or-none, and the gaps are part of the contract.

16 of the 1795 characters carry no radical data, and their example words are
what the study page renders. If the count drifts, the site shows a different set
of characters than the one that was reviewed, so the exact gaps are pinned.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
import validate_hanja


def problems(payload, expect):
    return validate_hanja.validate(payload, expect)


def with_radical(record, number=1, name="一", related=()):
    record["rad"] = number
    record["radName"] = name
    record["related"] = list(related)


class OptionalGroupTests(unittest.TestCase):
    def test_radical_fields_are_all_or_none(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], related=[])
        del payload["hanja"][0]["related"]  # rad and radName without related
        self.assertTrue(any("radical" in p or "rad" in p for p in problems(payload, expect)))

    def test_number_of_characters_without_radicals_is_pinned(self):
        payload, expect = fixtures.mini()
        expect["missing_rad"] = 1  # all three entries omit the fields
        self.assertTrue(any("expected 1" in p for p in problems(payload, expect)))

    def test_radical_number_stays_in_the_kangxi_range(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], number=0, related=[])
        self.assertTrue(any("rad" in p for p in problems(payload, expect)))

    def test_one_radical_number_always_has_the_same_name(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], number=40, name="宀", related=[])
        with_radical(payload["hanja"][1], number=40, name="心", related=[])
        self.assertTrue(any("radName" in p for p in problems(payload, expect)))

    def test_related_may_not_contain_the_character_itself(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], related=["家"])
        self.assertTrue(any("related" in p for p in problems(payload, expect)))

    def test_related_must_be_an_education_character(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], related=["龍"])
        self.assertTrue(any("related" in p for p in problems(payload, expect)))

    def test_related_must_share_the_radical(self):
        payload, expect = fixtures.mini()
        with_radical(payload["hanja"][0], number=40, name="宀", related=["佳"])
        with_radical(payload["hanja"][1], number=9, name="人", related=[])
        self.assertTrue(any("radical" in p for p in problems(payload, expect)))

    def test_related_length_respects_the_cap(self):
        payload, expect = fixtures.mini()
        expect["max_related"] = 1
        with_radical(payload["hanja"][0], related=["佳", "街"])
        with_radical(payload["hanja"][1], related=[])
        self.assertTrue(any("related" in p for p in problems(payload, expect)))


if __name__ == "__main__":
    unittest.main()
