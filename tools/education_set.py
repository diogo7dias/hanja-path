#!/usr/bin/env python3
"""The education character set, shared by the generator and the word-bank tool.

build_words.py needs to know which characters are in the education set. It used
to parse that list out of the served hanja-data.js, the same file the generator
writes, which made the two scripts depend on each other. This module is the
hand-off instead: the generator writes tools/educ.json, the word-bank tool reads
it, and neither has to know about the served file.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILE = HERE / "educ.json"
FIELDS = ("c", "r", "h")


def dump(payload, path=None):
    """Write the education set (character, reading, hun) out of a payload."""
    target = Path(path) if path else FILE
    chars = [{field: record[field] for field in FIELDS} for record in payload["hanja"]]
    text = json.dumps({"total": len(chars), "chars": chars}, ensure_ascii=False, indent=0) + "\n"
    target.write_text(text, encoding="utf-8")
    return target


def load(path=None):
    """Return the education set as {character: {"c", "r", "h"}}."""
    source = Path(path) if path else FILE
    data = json.loads(source.read_text(encoding="utf-8"))
    return {record["c"]: record for record in data["chars"]}
