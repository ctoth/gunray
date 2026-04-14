"""Tests for `gunray.dialectic` — Garcia & Simari 2004 Defs 3.4, 4.1-4.2, 4.7, 5.1; Proc 5.1."""

from __future__ import annotations

from gunray.arguments import Argument, build_arguments, is_subargument
from gunray.dialectic import (
    DialecticalNode,
    blocking_defeater,
    build_tree,
    counter_argues,
    mark,
    proper_defeater,
)
from gunray.preference import TrivialPreference
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


# -- Test 1 — counter-argument at root (Garcia 04 Def 3.4, Fig 2 left). --


def test_counter_argues_at_root_opus_flies() -> None:
    """Garcia 04 Def 3.4: ⟨r1@opus, flies(opus)⟩ and ⟨r2@opus, ~flies(opus)⟩
    counter-argue each other at their own conclusions."""
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    not_flies_opus = _find_argument(theory, _ga("~flies", "opus"))
    assert counter_argues(flies_opus, not_flies_opus, theory)
    assert counter_argues(not_flies_opus, flies_opus, theory)
