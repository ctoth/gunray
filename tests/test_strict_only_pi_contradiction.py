from __future__ import annotations

import pytest
from conftest import small_theory_strategy
from hypothesis import assume, given, settings

# Test code reaches into the private _is_strict_only_theory helper to
# verify internal routing. Project CLAUDE.md bans cross-module private
# imports between peer src modules, but tests/ is not a peer module of
# src/gunray/ — test code is explicitly allowed to check internals.
from gunray.defeasible import DefeasibleEvaluator, _is_strict_only_theory
from gunray.errors import ContradictoryStrictTheoryError
from gunray.schema import DefeasibleTheory, MarkingPolicy, Rule


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
        DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)


def test_presumption_only_theory_does_not_take_strict_only_fast_path() -> None:
    """A theory with only presumptions is defeasible — must not route to Datalog.

    Garcia & Simari 2004 §6.2 p. 32: presumptions are defeasible rules
    with empty body. Routing them through the strict-only fast path
    would drop their defeasibility.
    """
    theory = DefeasibleTheory(
        facts={},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[],
        presumptions=[Rule(id="p1", head="foo", body=[])],
        superiority=[],
        conflicts=[],
    )

    assert _is_strict_only_theory(theory) is False


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
        DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)


@settings(max_examples=200)
@given(small_theory_strategy())
def test_hypothesis_strict_only_never_yes_contradicts(
    theory: DefeasibleTheory,
) -> None:
    """A successful strict-only evaluation must not answer YES to p and ~p."""
    if theory.defeasible_rules or theory.defeaters or theory.superiority:
        assume(False)

    try:
        model = DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    except ContradictoryStrictTheoryError:
        return

    yes = model.sections.get("yes", {})
    for predicate, rows in yes.items():
        complement_predicate = predicate[1:] if predicate.startswith("~") else f"~{predicate}"
        complement_rows = yes.get(complement_predicate, set())
        assert not rows & complement_rows, (
            f"Pi contradiction leaked into YES: {predicate} vs {complement_predicate}"
        )
