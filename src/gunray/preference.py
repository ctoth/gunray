"""Preference criterion: Garcia & Simari 2004 section 4.

The defeat relation (Garcia & Simari 2004 Def 4.1 / 4.2) is
parameterized over an abstract preference relation ``>`` on
arguments. Real criteria (generalized specificity per Simari & Loui
1992 Lemma 2.4) land in Block 2; Block 1 only needs the protocol and
a trivial "prefer nothing" instance so that the dialectical tree can
be tested without a real criterion.
"""

from __future__ import annotations

from typing import Protocol

from .arguments import Argument


class PreferenceCriterion(Protocol):
    """Garcia & Simari 2004 section 4: abstract preference criterion ``>`` on arguments."""

    def prefers(self, left: Argument, right: Argument) -> bool:
        """Return True iff ``left`` is strictly preferred to ``right``."""
        ...


class TrivialPreference:
    """A preference criterion that prefers nothing over nothing.

    Under ``TrivialPreference`` every counter-argument is a blocking
    defeater (Garcia & Simari 2004 Def 4.2) and none are proper
    defeaters (Garcia & Simari 2004 Def 4.1). Useful for testing the
    dialectical-tree machinery in isolation from any real specificity
    criterion.
    """

    def prefers(self, left: Argument, right: Argument) -> bool:
        return False
