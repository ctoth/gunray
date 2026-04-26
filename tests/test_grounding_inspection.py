from __future__ import annotations

from gunray import DefeasibleTheory, GroundAtom, Rule, inspect_grounding


def test_inspect_grounding_exposes_fact_atoms_and_rule_instances() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("opus",), ("tweety",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=["bird(X)"])],
        defeaters=[Rule(id="d1", head="~flies(X)", body=["penguin(X)"])],
        superiority=[],
        conflicts=[],
    )

    inspection = inspect_grounding(theory)

    assert inspection.fact_atoms == (
        GroundAtom(predicate="bird", arguments=("opus",)),
        GroundAtom(predicate="bird", arguments=("tweety",)),
        GroundAtom(predicate="penguin", arguments=("opus",)),
    )
    assert {
        (instance.rule_id, instance.kind, instance.head, instance.substitution)
        for instance in inspection.strict_rules
    } == {
        (
            "s1",
            "strict",
            GroundAtom(predicate="animal", arguments=("opus",)),
            (("X", "opus"),),
        ),
        (
            "s1",
            "strict",
            GroundAtom(predicate="animal", arguments=("tweety",)),
            (("X", "tweety"),),
        ),
    }
    assert {
        (instance.rule_id, instance.kind, instance.head, instance.body, instance.substitution)
        for instance in inspection.defeasible_rules
    } == {
        (
            "r1",
            "defeasible",
            GroundAtom(predicate="flies", arguments=("opus",)),
            (GroundAtom(predicate="bird", arguments=("opus",)),),
            (("X", "opus"),),
        ),
        (
            "r1",
            "defeasible",
            GroundAtom(predicate="flies", arguments=("tweety",)),
            (GroundAtom(predicate="bird", arguments=("tweety",)),),
            (("X", "tweety"),),
        ),
    }
    assert {
        (instance.rule_id, instance.kind, instance.head, instance.substitution)
        for instance in inspection.defeater_rules
    } == {
        (
            "d1",
            "defeater",
            GroundAtom(predicate="~flies", arguments=("opus",)),
            (("X", "opus"),),
        )
    }


def test_inspection_groups_all_ground_rule_instances() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=["bird(X)"])],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    inspection = inspect_grounding(theory)

    assert inspection.all_rule_instances == inspection.strict_rules + inspection.defeasible_rules
