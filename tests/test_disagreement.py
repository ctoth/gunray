"""Unit and property tests for gunray.disagreement (Garcia & Simari 2004 Def 3.3)."""

from __future__ import annotations

from gunray.disagreement import disagrees
from gunray.types import GroundAtom


def test_disagrees_on_complementary_literals() -> None:
    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    not_flies_tweety = GroundAtom(predicate="~flies", arguments=("tweety",))
    assert disagrees(flies_tweety, not_flies_tweety, ()) is True
