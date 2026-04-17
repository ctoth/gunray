import dataclasses

import pytest

from gunray import DefeasibleTheory, Program, Rule


def test_rule_is_frozen() -> None:
    rule = Rule(id="r1", head="p(X)", body=["q(X)"])

    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.head = "flies(X)"  # pyright: ignore[reportAttributeAccessIssue]


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
        theory.facts = {}  # pyright: ignore[reportAttributeAccessIssue]


def test_program_is_frozen() -> None:
    program = Program(facts={"p": {("a",)}}, rules=[])

    with pytest.raises(dataclasses.FrozenInstanceError):
        program.facts = {}  # pyright: ignore[reportAttributeAccessIssue]


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


def test_defeasible_theory_accepts_presumptions_field() -> None:
    """Garcia & Simari 2004 §6.2 p. 32: presumption = defeasible rule with empty body."""
    theory = DefeasibleTheory(
        facts={},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[],
        presumptions=[Rule(id="p1", head="innocent(X)", body=[])],
        superiority=[],
        conflicts=[],
    )

    assert len(theory.presumptions) == 1
    assert theory.presumptions[0].id == "p1"

    with pytest.raises(dataclasses.FrozenInstanceError):
        theory.presumptions = []  # pyright: ignore[reportAttributeAccessIssue]


def test_defeasible_theory_rejects_presumption_with_non_empty_body() -> None:
    with pytest.raises(ValueError, match="p1.*empty body"):
        DefeasibleTheory(
            facts={},
            strict_rules=[],
            defeasible_rules=[],
            defeaters=[],
            presumptions=[Rule(id="p1", head="innocent(X)", body=["person(X)"])],
            superiority=[],
            conflicts=[],
        )


def test_defeasible_theory_allows_superiority_against_presumption_id() -> None:
    theory = DefeasibleTheory(
        facts={},
        strict_rules=[],
        defeasible_rules=[Rule(id="d1", head="~innocent(X)", body=["has_conviction(X)"])],
        defeaters=[],
        presumptions=[Rule(id="p1", head="innocent(X)", body=[])],
        superiority=[("d1", "p1")],
        conflicts=[],
    )

    assert ("d1", "p1") in theory.superiority
