#!/usr/bin/env python3
"""The published layout of the education set.

Every page derives level, lesson and slot membership from these numbers, and the
contract checks the generated data against them, so they live here instead of
being repeated as magic numbers in the generator and in the validator.
"""
LEVEL_CUTS = (600, 1200)
LESSON_SIZE = 10
MAX_WORDS = 3
MAX_RELATED = 8


def level_of(index):
    """Level id of the index-th education character."""
    for level, cut in enumerate(LEVEL_CUTS):
        if index < cut:
            return level
    return len(LEVEL_CUTS)


def lesson_of(position):
    """Lesson index inside a level for the position-th character of that level."""
    return position // LESSON_SIZE


def lesson_pos(position):
    """Slot inside a lesson for the position-th character of that level."""
    return position % LESSON_SIZE
