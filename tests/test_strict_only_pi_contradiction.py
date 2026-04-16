from __future__ import annotations

import pytest
from hypothesis import assume, given, settings

from conftest import small_theory_strategy
from gunray.defeasible import DefeasibleEvaluator
from gunray.errors import ContradictoryStrictTheoryError
from gunray.schema import DefeasibleTheory, Policy, Rule


def test_strict_only_theory_with_contradictory_pi_raises() -> None:
    """Garcia & Simari 2004 Def 3.1 cond 2: Pi must be non-contradictory."""
    theory = DefeasibleTheory(
        facts={"p": {("a",)}, "q": {("a",)}},
        strict_rules=[Rule(id="s1", head="~p(X)", body=["q(X)"])],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    with pytest.raises(ContradictoryStrictTheoryError):
        DefeasibleEvaluator().evaluate(theory, Policy.BLOCKING)


def test_strict_only_theory_respects_conflicts_field() -> None:
    """Conflicts between different predicates must fire on the shortcut."""
    theory = DefeasibleTheory(
        facts={"alive": {("x",)}, "dead": {("x",)}},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[("alive", "dead")],
    )

    with pytest.raises(ContradictoryStrictTheoryError):
        DefeasibleEvaluator().evaluate(theory, Policy.BLOCKING)


@settings(max_examples=200)
@given(small_theory_strategy())
def test_hypothesis_strict_only_never_definitely_contradicts(
    theory: DefeasibleTheory,
) -> None:
    """A successful strict-only evaluation must not definitely prove p and ~p."""
    if theory.defeasible_rules or theory.defeaters or theory.superiority:
        assume(False)

    try:
        model = DefeasibleEvaluator().evaluate(theory, Policy.BLOCKING)
    except ContradictoryStrictTheoryError:
        return

    definitely = model.sections.get("definitely", {})
    for predicate, rows in definitely.items():
        complement_predicate = predicate[1:] if predicate.startswith("~") else f"~{predicate}"
        complement_rows = definitely.get(complement_predicate, set())
        assert not rows & complement_rows, (
            f"Pi contradiction leaked into definitely: {predicate} vs "
            f"{complement_predicate}"
        )
