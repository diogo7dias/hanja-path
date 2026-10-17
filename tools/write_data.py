#!/usr/bin/env python3
"""The single writer of the served hanja-data.js.

The order matters: validate the payload, render the file, validate the rendered
wrapper, and only then replace the served file in one move. A build that fails
therefore changes nothing, so the site can never serve an unvalidated dataset.
"""
import json
import os
from pathlib import Path

import validate_hanja

HEADER = validate_hanja.HEADER
PREFIX = validate_hanja.PREFIX
TRAILER = ";\n"


class ContractError(Exception):
    """Raised instead of writing a file that would break the contract."""

    def __init__(self, problems):
        super().__init__("%d contract problem(s)" % len(problems))
        self.problems = list(problems)


def render(payload):
    """The exact bytes of the served file, wrapper included."""
    return "%s\n%s%s%s" % (HEADER, PREFIX, json.dumps(payload, ensure_ascii=False), TRAILER)


def write(payload, path, expect=None):
    """Validate and write the served file, or raise ContractError and change nothing."""
    problems = validate_hanja.validate(payload, expect)
    if problems:
        raise ContractError(problems)

    text = render(payload)
    problems = validate_hanja.validate_text(text)
    if problems:
        raise ContractError(problems)

    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, target)
