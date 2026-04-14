"""Unit and property tests for gunray.arguments.build_arguments.

Garcia & Simari 2004 Definition 3.1, Simari & Loui 1992 Definition 2.2.
"""

from __future__ import annotations

from gunray.arguments import Argument, build_arguments
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom


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


def test_tweety_flies_argument_exists() -> None:
    """Garcia & Simari 2004 Def 3.1: <{r1(tweety)}, flies(tweety)> is an argument."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    matching = [arg for arg in arguments if arg.conclusion == flies_tweety]
    assert matching, f"no argument for flies(tweety) in {arguments!r}"

    # The grounded r1 instance with X=tweety must appear in rules.
    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r1" in grounded_rule_ids:
            return
    raise AssertionError(
        f"no argument for flies(tweety) was backed by r1: {matching!r}"
    )


def test_opus_not_flies_argument_exists() -> None:
    """Opus's penguin rule must produce <{r2(opus)}, ~flies(opus)>."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    not_flies_opus = GroundAtom(predicate="~flies", arguments=("opus",))
    matching = [arg for arg in arguments if arg.conclusion == not_flies_opus]
    assert matching, f"no argument for ~flies(opus) in {arguments!r}"

    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r2" in grounded_rule_ids:
            return
    raise AssertionError(
        f"no argument for ~flies(opus) was backed by r2: {matching!r}"
    )


def _nixon_theory() -> DefeasibleTheory:
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


def test_nixon_diamond_has_both_arguments() -> None:
    """Garcia & Simari 2004 Def 3.1: both sides of Nixon must produce arguments."""

    theory = _nixon_theory()
    arguments = build_arguments(theory)

    pacifist_nixon = GroundAtom(predicate="pacifist", arguments=("nixon",))
    not_pacifist_nixon = GroundAtom(predicate="~pacifist", arguments=("nixon",))

    pacifist_args = [a for a in arguments if a.conclusion == pacifist_nixon]
    not_pacifist_args = [a for a in arguments if a.conclusion == not_pacifist_nixon]

    assert pacifist_args, f"no argument for pacifist(nixon): {arguments!r}"
    assert not_pacifist_args, (
        f"no argument for ~pacifist(nixon): {arguments!r}"
    )
