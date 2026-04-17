"""Tests for ``gunray.dialectic.explain`` — prose explanation renderer.

``explain`` walks a marked dialectical tree and returns a prose
transcript of the Garcia & Simari 2004 §6 "explaining answers"
analysis: which argument supports the root, which defeaters were
considered, and why each attacker wins or loses by preference.
"""

from __future__ import annotations

from conftest import theory_with_root_argument_strategy
from hypothesis import given, settings

from gunray.arguments import Argument, build_arguments
from gunray.dialectic import build_tree, explain
from gunray.preference import GeneralizedSpecificity, TrivialPreference
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom


def _ga(predicate: str, *args: str) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


def _tweety_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _direct_nixon_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"republican": {("nixon",)}, "quaker": {("nixon",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="~pacifist(X)", body=["republican(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _find_argument(theory: DefeasibleTheory, conclusion: GroundAtom) -> Argument:
    for arg in build_arguments(theory):
        if arg.conclusion == conclusion:
            return arg
    raise LookupError(f"no argument for {conclusion}")


def test_explain_leaf_node() -> None:
    """A childless tree explains to a YES verdict and a single supporting sentence."""
    theory = _tweety_theory()
    flies_tweety = _find_argument(theory, _ga("flies", "tweety"))
    tree = build_tree(flies_tweety, TrivialPreference(), theory)
    assert tree.children == ()
    text = explain(tree, TrivialPreference())
    lines = text.splitlines()
    assert lines[0] == "flies(tweety) is YES."
    assert "flies(tweety)" in lines[1]
    assert "r1" in lines[1]
    assert "bird(tweety)" in lines[1]
    assert len(lines) == 2


def test_explain_tweety_opus_tree_snapshot() -> None:
    """Snapshot of ``explain`` output for the Opus case under specificity.

    With ``GeneralizedSpecificity``, ``~flies(opus)`` is a *proper*
    defeater of ``flies(opus)``: ``penguin(X)`` strictly entails
    ``bird(X)`` via ``s1`` but not vice versa, so the specificity
    criterion strictly prefers ``r2``'s argument. The tree root marks
    ``D``; ``explain`` therefore answers ``NO``.
    """
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    criterion = GeneralizedSpecificity(theory)
    tree = build_tree(flies_opus, criterion, theory)
    expected = (
        "flies(opus) is NO.\n"
        "An argument supports flies(opus) from {bird(opus)} via r1.\n"
        "It is defeated by an argument for ~flies(opus) from "
        "{penguin(opus)} via r2, which is strictly more specific."
    )
    assert explain(tree, criterion) == expected


def test_explain_nixon_diamond_blocking_snapshot() -> None:
    """Snapshot for the Nixon Diamond under ``TrivialPreference``.

    Neither side is strictly preferred, so the defeat is *blocking*
    and ``explain`` reports that explicitly.
    """
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    expected = (
        "pacifist(nixon) is NO.\n"
        "An argument supports pacifist(nixon) from {quaker(nixon)} via r2.\n"
        "It is defeated by an argument for ~pacifist(nixon) from "
        "{republican(nixon)} via r1, "
        "which is a blocking defeater (neither side strictly preferred)."
    )
    assert explain(tree, TrivialPreference()) == expected


def test_explain_is_deterministic() -> None:
    """``explain`` is pure — two calls on the same tree are byte-identical."""
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    criterion = GeneralizedSpecificity(theory)
    tree = build_tree(flies_opus, criterion, theory)
    assert explain(tree, criterion) == explain(tree, criterion)


@given(theory_with_root=theory_with_root_argument_strategy())
@settings(max_examples=200, deadline=None)
def test_hypothesis_explain_contains_root_conclusion(
    theory_with_root: tuple[DefeasibleTheory, Argument],
) -> None:
    """Property: the prose output must include the root conclusion's predicate."""
    theory, root = theory_with_root
    tree = build_tree(root, TrivialPreference(), theory)
    text = explain(tree, TrivialPreference())
    assert root.conclusion.predicate in text


@given(theory_with_root=theory_with_root_argument_strategy())
@settings(max_examples=200, deadline=None)
def test_hypothesis_explain_is_deterministic(
    theory_with_root: tuple[DefeasibleTheory, Argument],
) -> None:
    """Property: any generated dialectical tree explains byte-identically."""
    theory, root = theory_with_root
    tree = build_tree(root, TrivialPreference(), theory)
    assert explain(tree, TrivialPreference()) == explain(tree, TrivialPreference())
