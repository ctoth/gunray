"""Four-valued answer: Garcia & Simari 2004 Def 5.3."""

from __future__ import annotations

from enum import Enum


class Answer(Enum):
    """Garcia & Simari 2004 Def 5.3 — the answer of a DeLP query for a literal h:

    - YES: h is warranted from the program.
    - NO: the complement of h is warranted.
    - UNDECIDED: neither h nor its complement is warranted, but there
      exists at least one argument for h or its complement.
    - UNKNOWN: h is not in the language of the program.
    """

    YES = "yes"
    NO = "no"
    UNDECIDED = "undecided"
    UNKNOWN = "unknown"
