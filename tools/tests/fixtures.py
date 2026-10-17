"""Small valid payloads for validator tests.

The served file has 1795 entries, which is too heavy to mutate in unit tests, so
the exact counts live in an ``expect`` mapping. ``mini`` returns a coherent
payload plus the matching expectations, and each test overrides one field.
"""

CHARS = ("家", "佳", "街", "假", "價")


def mini(count=3):
    """A valid payload of ``count`` entries, one per level, and its expectations."""
    records = []
    for index in range(count):
        char = CHARS[index]
        records.append(
            {
                "c": char,
                "r": "가",
                "h": "집",
                "lv": index,
                "idx": index,
                "lesson": 0,
                "lessonPos": 0,
                "rad": index + 1,
                "radName": "一",
                "related": [],
                "words": [{"ko": "가", "hj": char, "gl": "a gloss", "b": "집(%s)" % char}],
            }
        )
    payload = {
        "total": count,
        "levels": [{"id": index, "ko": "급", "en": "L%d" % index, "n": 1} for index in range(count)],
        "hanja": records,
    }
    expect = {
        "total": count,
        "level_counts": tuple([1] * count),
        "lesson_size": (1, 10),
        "max_words": 3,
        "max_related": 8,
        "missing_rad": 0,
        "missing_rad_chars": frozenset(),
        "missing_words": 0,
        "missing_words_chars": frozenset(),
        "curated": 0,
        "curated_chars": frozenset(),
        "non_education_words": frozenset(),
    }
    return payload, expect
