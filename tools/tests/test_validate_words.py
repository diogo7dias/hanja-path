"""Example words and the curated trio are learner-facing text, so they are pinned.

Each character page renders these words with their breakdown line. A word that
does not contain its own character, a Hangul gloss, a duplicate spelling, or a
count drift all reach the learner, so the counts and the two known exceptions
are part of the contract.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
import validate_hanja


def problems(payload, expect):
    return validate_hanja.validate(payload, expect)


def word(ko, hj, gl="family", b="집(家)"):
    return {"ko": ko, "hj": hj, "gl": gl, "b": b}


class WordTests(unittest.TestCase):
    def test_every_word_carries_the_character_it_teaches(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["words"] = [word("가가", "假價")]
        self.assertTrue(any("carries" in p or "does not contain" in p for p in problems(payload, expect)))

    def test_word_fields_must_not_be_empty(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["words"] = [word("가족", "家族", gl="")]
        self.assertTrue(any("empty" in p for p in problems(payload, expect)))

    def test_word_count_respects_the_cap(self):
        payload, expect = fixtures.mini()
        expect["max_words"] = 1
        payload["hanja"][0]["words"] = [word("가족", "家族"), word("국가", "國家")]
        self.assertTrue(any("words" in p for p in problems(payload, expect)))

    def test_one_character_may_not_repeat_a_korean_spelling(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["words"] = [word("가족", "家族"), word("가족", "家屬")]
        self.assertTrue(any("spelling" in p or "repeat" in p for p in problems(payload, expect)))

    def test_gloss_must_not_contain_hangul(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["words"] = [word("가족", "家族", gl="가족")]
        self.assertTrue(any("Hangul" in p for p in problems(payload, expect)))

    def test_hanja_outside_the_education_set_is_pinned(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["words"] = [word("월요일", "月曜日")]
        self.assertTrue(any("曜" in p for p in problems(payload, expect)))

    def test_number_of_characters_without_words_is_pinned(self):
        payload, expect = fixtures.mini()
        expect["missing_words"] = 1
        self.assertTrue(any("expected 1" in p for p in problems(payload, expect)))


class CuratedTests(unittest.TestCase):
    def test_curated_fields_are_all_or_none(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["eng"] = "house"
        self.assertTrue(any("only eng" in p or "eng" in p for p in problems(payload, expect)))

    def test_number_of_curated_characters_is_pinned(self):
        payload, expect = fixtures.mini()
        expect["curated"] = 1
        self.assertTrue(any("expected 1" in p for p in problems(payload, expect)))

    def test_sentence_needs_both_korean_and_english(self):
        payload, expect = fixtures.mini()
        payload["hanja"][0]["eng"] = "house"
        payload["hanja"][0]["tip"] = "집 안에 돼지"
        payload["hanja"][0]["s"] = {"ko": "가족과 외식했어요."}
        self.assertTrue(any("sentence" in p or "en" in p for p in problems(payload, expect)))


if __name__ == "__main__":
    unittest.main()
