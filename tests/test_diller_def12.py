from __future__ import annotations

from gunray import DefeasibleTheory, GroundAtom, Rule, compute_non_approximated, inspect_grounding


def test_strict_fact_chain_is_non_approximated() -> None:
    theory = DefeasibleTheory(
        facts={"penguin": {("opus",)}},
        strict_rules=[
            Rule(id="s1", head="bird(X)", body=["penguin(X)"]),
            Rule(id="s2", head="animal(X)", body=["bird(X)"]),
        ],
        defeasible_rules=[Rule(id="d1", head="flies(X)", body=["bird(X)"])],
    )

    assert compute_non_approximated(theory) == frozenset({"animal", "bird", "penguin"})


def test_defeasible_head_is_not_non_approximated() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[Rule(id="d1", head="flies(X)", body=["bird(X)"])],
    )

    assert compute_non_approximated(theory) == frozenset({"bird"})


def test_conflict_with_approximated_predicate_blocks_non_approximated() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[Rule(id="d1", head="~bird(X)", body=["bird(X)"])],
        conflicts=(("bird", "~bird"),),
    )

    assert compute_non_approximated(theory) == frozenset()


def test_inspect_grounding_reports_non_approximated_predicates() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="d1", head="flies(X)", body=["animal(X)"])],
    )

    simplification = inspect_grounding(theory).simplification

    assert simplification.non_approximated_predicates == ("animal", "bird")
    assert GroundAtom(predicate="animal", arguments=("tweety",)) in simplification.definite_fact_atoms
