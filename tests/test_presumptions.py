"""End-to-end presumption tests.

Garcia & Simari 2004 §6.2 p. 32 defines a presumption as a defeasible
rule with empty body ``h -< true``. Gunray carries presumptions on the
``DefeasibleTheory.presumptions`` slot and plumbs them through the
argument pipeline as ordinary defeasible rules (kind="defeasible").

Note: the pipeline currently requires zero-arity presumption heads
because ``_positive_closure_for_grounding`` attempts to ground the
head under the empty binding before per-rule grounding runs (see
F-A report, finding on arg-bearing presumption heads).
"""

from __future__ import annotations

from gunray import DefeasibleEvaluator, DefeasibleTheory, MarkingPolicy, Rule


def _presumption_only_theory() -> DefeasibleTheory:
    """Zero-arity presumption, no defeating argument exists."""
    return DefeasibleTheory(
        facts={},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[],
        presumptions=[Rule(id="p1", head="innocent", body=[])],
        superiority=[],
        conflicts=[],
    )


def _rebutted_presumption_theory() -> DefeasibleTheory:
    """Presumption ``innocent -< true`` with a defeasible counter-argument.

    The ``~innocent :- has_conviction`` rule fires from the fact
    ``has_conviction`` and rebuts the presumption's conclusion.
    """
    return DefeasibleTheory(
        facts={"has_conviction": {()}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="d1", head="~innocent", body=["has_conviction"]),
        ],
        defeaters=[],
        presumptions=[Rule(id="p1", head="innocent", body=[])],
        superiority=[],
        conflicts=[],
    )


def test_presumption_holds_when_no_defeating_argument_exists() -> None:
    """A lone presumption is a YES answer because no counter-argument exists."""
    model = DefeasibleEvaluator().evaluate(
        _presumption_only_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    innocent = model.sections.get("yes", {}).get("innocent", set())
    assert () in innocent


def test_presumption_challenged_observed_behavior() -> None:
    """Record the pipeline's verdict when a defeasible rule rebuts a presumption.

    Under GeneralizedSpecificity (Simari & Loui 1992 Lemma 2.4), a
    presumption has an empty antecedent set. Scout §5.4 predicted the
    specificity comparison falls through to equi-specific (neither
    argument strictly more specific), so both arguments block and
    ``innocent``/``~innocent`` land in ``undecided``. We record the
    observed outcome rather than pinning it — if it changes, that is
    a deliberate semantic decision for the next iteration.
    """
    model = DefeasibleEvaluator().evaluate(
        _rebutted_presumption_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    sections = model.sections
    assert () in sections.get("yes", {}).get("~innocent", set())
    assert () in sections.get("no", {}).get("innocent", set())
