"""Unit and property tests for gunray.arguments (Garcia & Simari 2004 Def 3.1)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gunray.arguments import Argument, is_subargument
from gunray.types import GroundAtom, GroundDefeasibleRule


def _atom(predicate: str, *args: str | int) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


def _rule(rule_id: str, head_predicate: str) -> GroundDefeasibleRule:
    head = _atom(head_predicate, "x")
    return GroundDefeasibleRule(rule_id=rule_id, kind="defeasible", head=head, body=())


_RULE_POOL: tuple[GroundDefeasibleRule, ...] = (
    _rule("r1", "p"),
    _rule("r2", "q"),
    _rule("r3", "s"),
    _rule("r4", "t"),
)
_CONCLUSION: GroundAtom = _atom("h", "x")


def test_empty_argument_is_hashable_and_equal_to_duplicate() -> None:
    atom = _atom("flies", "tweety")
    left = Argument(rules=frozenset(), conclusion=atom)
    right = Argument(rules=frozenset(), conclusion=atom)
    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}


def test_arguments_with_same_rules_but_different_conclusions_are_unequal() -> None:
    rules = frozenset({_RULE_POOL[0]})
    a = Argument(rules=rules, conclusion=_atom("p", "x"))
    b = Argument(rules=rules, conclusion=_atom("q", "x"))
    assert a != b


def test_is_subargument_reflexive_and_strict_subset_and_empty_rules() -> None:
    atom = _atom("h", "x")
    empty = Argument(rules=frozenset(), conclusion=atom)
    single = Argument(rules=frozenset({_RULE_POOL[0]}), conclusion=atom)
    double = Argument(rules=frozenset({_RULE_POOL[0], _RULE_POOL[1]}), conclusion=atom)

    assert is_subargument(empty, empty)
    assert is_subargument(single, single)
    assert is_subargument(double, double)

    assert is_subargument(single, double)
    assert not is_subargument(double, single)

    assert is_subargument(empty, single)
    assert is_subargument(empty, double)
    assert not is_subargument(single, empty)


@st.composite
def _arguments(draw: st.DrawFn) -> Argument:
    indices = draw(
        st.sets(st.integers(min_value=0, max_value=len(_RULE_POOL) - 1), max_size=len(_RULE_POOL))
    )
    rules = frozenset(_RULE_POOL[i] for i in indices)
    return Argument(rules=rules, conclusion=_CONCLUSION)


@given(a=_arguments())
@settings(max_examples=500, deadline=None)
def test_is_subargument_reflexive(a: Argument) -> None:
    assert is_subargument(a, a)


@given(a=_arguments(), b=_arguments())
@settings(max_examples=500, deadline=None)
def test_is_subargument_antisymmetric(a: Argument, b: Argument) -> None:
    if is_subargument(a, b) and is_subargument(b, a):
        assert a.rules == b.rules


@given(a=_arguments(), b=_arguments(), c=_arguments())
@settings(max_examples=500, deadline=None)
def test_is_subargument_transitive(a: Argument, b: Argument, c: Argument) -> None:
    if is_subargument(a, b) and is_subargument(b, c):
        assert is_subargument(a, c)
