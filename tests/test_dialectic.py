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


# -- Test 2 — counter-argument at sub-argument (Garcia 04 Def 3.4, Fig 2 right). --


def _chain_theory() -> DefeasibleTheory:
    """Defeasible chain with an attacker at a sub-argument's conclusion.

    Rules::
        r1: q(X) :- p(X).        (defeasible)
        r2: r(X) :- q(X).        (defeasible)
        r3: ~q(X) :- t(X).       (defeasible — attacker at sub-argument q)
        facts: p(a), t(a).
    """
    return DefeasibleTheory(
        facts={"p": {("a",)}, "t": {("a",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="q(X)", body=["p(X)"]),
            Rule(id="r2", head="r(X)", body=["q(X)"]),
            Rule(id="r3", head="~q(X)", body=["t(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_counter_argues_at_sub_argument_directional_fix() -> None:
    """Garcia 04 Def 3.4 (Fig 2 right): ``⟨{r3}, ~q(a)⟩`` attacks the
    *sub-argument* ``⟨{r1}, q(a)⟩`` of ``⟨{r1,r2}, r(a)⟩``.

    Under gunray's deleted root-only attack path, ``counter_argues``
    would return False because ``~q`` does not disagree with ``r``.
    The directional fix: descent into sub-arguments catches it.
    """
    theory = _chain_theory()
    r_arg = _find_argument(theory, _ga("r", "a"))
    not_q_arg = _find_argument(theory, _ga("~q", "a"))
    assert counter_argues(not_q_arg, r_arg, theory)


# -- Test 3 — proper vs blocking under TrivialPreference. --


def test_proper_and_blocking_defeaters_under_trivial_preference() -> None:
    """Garcia 04 Def 4.1 / 4.2: under ``TrivialPreference`` every
    counter-argument is a *blocking* defeater and none are *proper*
    defeaters (because nothing is strictly preferred)."""
    theory = _tweety_theory()
    flies = _find_argument(theory, _ga("flies", "opus"))
    not_flies = _find_argument(theory, _ga("~flies", "opus"))
    criterion = TrivialPreference()
    assert blocking_defeater(flies, not_flies, criterion, theory)
    assert blocking_defeater(not_flies, flies, criterion, theory)
    assert not proper_defeater(flies, not_flies, criterion, theory)
    assert not proper_defeater(not_flies, flies, criterion, theory)


# -- Test 4 — proper defeater under a mock preference. --


class _MockPreference:
    """A preference criterion that strictly prefers one fixed argument."""

    def __init__(self, winner: Argument) -> None:
        self._winner = winner

    def prefers(self, left: Argument, right: Argument) -> bool:
        return left == self._winner and right != self._winner


def test_proper_defeater_under_mock_preference() -> None:
    """Garcia 04 Def 4.1: with a criterion that strictly prefers the
    attacker over the defended sub-argument, the counter-argument is
    a *proper* defeater and therefore not merely blocking."""
    theory = _tweety_theory()
    flies = _find_argument(theory, _ga("flies", "opus"))
    not_flies = _find_argument(theory, _ga("~flies", "opus"))
    # MockPreference declares `not_flies` strictly preferred.
    criterion = _MockPreference(winner=not_flies)
    assert proper_defeater(not_flies, flies, criterion, theory)
    assert not blocking_defeater(not_flies, flies, criterion, theory)
    # The dispreferred direction is neither proper nor a blocker
    # *towards* a strictly better opponent — it's the strict loser.
    assert not proper_defeater(flies, not_flies, criterion, theory)


# -- Test 5 — Nixon Diamond tree shape (Garcia 04 Def 5.1 + Def 4.7). --


def test_nixon_diamond_tree_shape_under_trivial_preference() -> None:
    """Garcia 04 Def 5.1 with Def 4.7 cond 3 and cond 4.

    ``direct_nixon`` has two defeasible rules::
        r1: ~pacifist(X) :- republican(X).
        r2:  pacifist(X) :- quaker(X).
    Under ``TrivialPreference`` both sides are blocking defeaters of
    each other. The tree rooted at ``⟨{r2}, pacifist(nixon)⟩``:

    - the root has exactly one child, ``⟨{r1}, ~pacifist(nixon)⟩``
      (the hawk argument);
    - the hawk node has **no** children because the only candidate
      counter-attack is the pacifist argument again, which is a
      sub-argument of the root (violating Def 4.7 cond 3) AND would
      be a blocking defeater of a blocking defeater (violating cond
      4).
    """
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    hawk = _find_argument(theory, _ga("~pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    assert tree.argument == pacifist
    assert len(tree.children) == 1
    assert tree.children[0].argument == hawk
    assert tree.children[0].children == ()
