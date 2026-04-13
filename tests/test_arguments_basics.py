"""Unit and property tests for gunray.arguments (Garcia & Simari 2004 Def 3.1)."""

from __future__ import annotations

from hypothesis import given, settings

from gunray.arguments import Argument, is_subargument

from conftest import RULE_POOL, arguments_strategy, make_ground_atom


def test_empty_argument_is_hashable_and_equal_to_duplicate() -> None:
    atom = make_ground_atom("flies", "tweety")
    left = Argument(rules=frozenset(), conclusion=atom)
    right = Argument(rules=frozenset(), conclusion=atom)
    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}


def test_arguments_with_same_rules_but_different_conclusions_are_unequal() -> None:
    rules = frozenset({RULE_POOL[0]})
    a = Argument(rules=rules, conclusion=make_ground_atom("p", "x"))
    b = Argument(rules=rules, conclusion=make_ground_atom("q", "x"))
    assert a != b


def test_is_subargument_reflexive_and_strict_subset_and_empty_rules() -> None:
    atom = make_ground_atom("h", "x")
    empty = Argument(rules=frozenset(), conclusion=atom)
    single = Argument(rules=frozenset({RULE_POOL[0]}), conclusion=atom)
    double = Argument(rules=frozenset({RULE_POOL[0], RULE_POOL[1]}), conclusion=atom)

    assert is_subargument(empty, empty)
    assert is_subargument(single, single)
    assert is_subargument(double, double)

    assert is_subargument(single, double)
    assert not is_subargument(double, single)

    assert is_subargument(empty, single)
    assert is_subargument(empty, double)
    assert not is_subargument(single, empty)


@given(a=arguments_strategy())
@settings(max_examples=500, deadline=None)
def test_is_subargument_reflexive(a: Argument) -> None:
    assert is_subargument(a, a)


@given(a=arguments_strategy(), b=arguments_strategy())
@settings(max_examples=500, deadline=None)
def test_is_subargument_antisymmetric(a: Argument, b: Argument) -> None:
    if is_subargument(a, b) and is_subargument(b, a):
        assert a.rules == b.rules


@given(a=arguments_strategy(), b=arguments_strategy(), c=arguments_strategy())
@settings(max_examples=500, deadline=None)
def test_is_subargument_transitive(a: Argument, b: Argument, c: Argument) -> None:
    if is_subargument(a, b) and is_subargument(b, c):
        assert is_subargument(a, c)
