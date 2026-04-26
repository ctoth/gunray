from __future__ import annotations

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    GroundAtom,
    Policy,
    Rule,
    inspect_grounding,
)


def test_strict_fact_rules_are_reported_as_resolved_diller_s4() -> None:
    """Diller 2025 page images 004-007: strict/fact-only heads may move to facts."""

    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=["animal(X)"])],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    simplification = inspect_grounding(theory).simplification

    assert simplification.definite_fact_atoms == (
        GroundAtom(predicate="animal", arguments=("tweety",)),
        GroundAtom(predicate="bird", arguments=("tweety",)),
    )
    assert [
        (resolution.rule.rule_id, resolution.produced_fact)
        for resolution in simplification.resolved_strict_rules
    ] == [("s1", GroundAtom(predicate="animal", arguments=("tweety",)))]
    assert simplification.strict_rules_for_argumentation == ()
    assert [rule.rule_id for rule in simplification.ground_rules_for_argumentation] == ["r1"]


def test_resolving_strict_fact_rules_preserves_checked_conclusions() -> None:
    """Oracle for the conservative fragment, not full ASPIC+ Transformation 2."""

    original = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=["animal(X)"])],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )
    manually_simplified = DefeasibleTheory(
        facts={"bird": {("tweety",)}, "animal": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=["animal(X)"])],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    evaluator = DefeasibleEvaluator()

    assert (
        evaluator.evaluate(original, Policy.BLOCKING).sections
        == evaluator.evaluate(
            manually_simplified,
            Policy.BLOCKING,
        ).sections
    )
