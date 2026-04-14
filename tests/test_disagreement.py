"""Unit and property tests for gunray.disagreement (Garcia & Simari 2004 Def 3.3)."""

from __future__ import annotations

from hypothesis import assume, given, settings

from gunray.disagreement import complement, disagrees, strict_closure
from gunray.types import GroundAtom, GroundDefeasibleRule

from conftest import ground_atom_strategy, strict_context_strategy


def test_disagrees_on_complementary_literals() -> None:
    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    not_flies_tweety = GroundAtom(predicate="~flies", arguments=("tweety",))
    assert disagrees(flies_tweety, not_flies_tweety, ()) is True


def test_does_not_disagree_on_unrelated_literals() -> None:
    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    bird_tweety = GroundAtom(predicate="bird", arguments=("tweety",))
    assert disagrees(flies_tweety, bird_tweety, ()) is False


def test_disagrees_via_strict_rule() -> None:
    penguin_opus = GroundAtom(predicate="penguin", arguments=("opus",))
    bird_opus = GroundAtom(predicate="bird", arguments=("opus",))
    not_bird_opus = GroundAtom(predicate="~bird", arguments=("opus",))
    strict_bird_from_penguin = GroundDefeasibleRule(
        rule_id="s1",
        kind="strict",
        head=bird_opus,
        body=(penguin_opus,),
    )
    context = (strict_bird_from_penguin,)
    assert disagrees(penguin_opus, not_bird_opus, context) is True


@given(a=ground_atom_strategy(), b=ground_atom_strategy(), k=strict_context_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_disagrees_is_symmetric(
    a: GroundAtom,
    b: GroundAtom,
    k: tuple[GroundDefeasibleRule, ...],
) -> None:
    """Garcia & Simari 2004 Def 3.3: disagreement is a symmetric relation.

    ``Pi union {h1, h2}`` is set-theoretically identical to
    ``Pi union {h2, h1}``; the closure, and hence contradictoriness,
    must not depend on argument order.
    """

    assert disagrees(a, b, k) == disagrees(b, a, k)


@given(
    a=ground_atom_strategy(),
    b=ground_atom_strategy(),
    k1=strict_context_strategy(),
    k2=strict_context_strategy(),
)
@settings(max_examples=500, deadline=None)
def test_hypothesis_disagrees_is_monotonic_in_context(
    a: GroundAtom,
    b: GroundAtom,
    k1: tuple[GroundDefeasibleRule, ...],
    k2: tuple[GroundDefeasibleRule, ...],
) -> None:
    """Adding strict rules cannot remove a disagreement.

    If ``disagrees(a, b, K1)`` holds and ``K1`` is a subset of ``K2``
    (as rule sets), then the strict closure under ``K2`` is a
    superset of that under ``K1``, so any complementary pair in the
    former is still present in the latter. We build ``K2`` as
    ``K1 ++ k2`` so ``set(K1) <= set(K2)`` by construction.
    """

    superset = k1 + k2
    if disagrees(a, b, k1):
        assert disagrees(a, b, superset)


@given(a=ground_atom_strategy(), k=strict_context_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_disagrees_irreflexive_on_satisfiable_context(
    a: GroundAtom,
    k: tuple[GroundDefeasibleRule, ...],
) -> None:
    """``disagrees(a, a, K)`` is False whenever ``{a} union K`` is satisfiable.

    Garcia & Simari 2004 Def 3.3 requires contradictoriness in the
    closure; if the closure of ``{a}`` under K already contains ``a``
    and its complement, that is a prior defect of the context, not a
    disagreement between ``a`` and itself. We filter with ``assume``
    to satisfiable contexts only.
    """

    closure = strict_closure(frozenset({a}), k)
    # Reject contexts that are already internally contradictory with {a}.
    for atom in closure:
        assume(complement(atom) not in closure)
    assert disagrees(a, a, k) is False
