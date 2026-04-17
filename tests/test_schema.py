import dataclasses

import pytest

from gunray import DefeasibleTheory, Program, Rule


def test_rule_is_frozen() -> None:
    rule = Rule(id="r1", head="p(X)", body=["q(X)"])

    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.head = "flies(X)"


def test_defeasible_theory_is_frozen() -> None:
    theory = DefeasibleTheory(
        facts={"p": {("a",)}},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        theory.facts = {}


def test_program_is_frozen() -> None:
    program = Program(facts={"p": {("a",)}}, rules=[])

    with pytest.raises(dataclasses.FrozenInstanceError):
        program.facts = {}


def test_rule_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="Rule.id"):
        Rule(id="", head="p(X)", body=[])


def test_rule_rejects_empty_head() -> None:
    with pytest.raises(ValueError, match="Rule.head"):
        Rule(id="r1", head="", body=["q(X)"])


def test_defeasible_theory_rejects_ghost_superiority_references() -> None:
    with pytest.raises(ValueError, match="ghost") as exc:
        DefeasibleTheory(
            facts={},
            strict_rules=[],
            defeasible_rules=[Rule(id="d1", head="p(X)", body=[])],
            defeaters=[],
            superiority=[("d1", "ghost")],
            conflicts=[],
        )

    assert "ghost" in str(exc.value)
