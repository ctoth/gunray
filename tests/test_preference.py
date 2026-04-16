"""Unit and property tests for gunray.preference (Garcia & Simari 2004 section 4)."""

from __future__ import annotations

from conftest import RULE_POOL, arguments_strategy, make_ground_atom
from hypothesis import given, settings

from gunray.arguments import Argument
from gunray.preference import PreferenceCriterion, TrivialPreference


def test_trivial_preference_satisfies_protocol_and_returns_false() -> None:
    criterion: PreferenceCriterion = TrivialPreference()
    atom = make_ground_atom("h", "x")
    left = Argument(rules=frozenset({RULE_POOL[0]}), conclusion=atom)
    right = Argument(rules=frozenset({RULE_POOL[1]}), conclusion=atom)
    assert criterion.prefers(left, right) is False
    assert criterion.prefers(right, left) is False
    assert criterion.prefers(left, left) is False


@given(a=arguments_strategy(), b=arguments_strategy())
@settings(max_examples=500, deadline=None)
def test_trivial_preference_prefers_nothing(a: Argument, b: Argument) -> None:
    assert TrivialPreference().prefers(a, b) is False
