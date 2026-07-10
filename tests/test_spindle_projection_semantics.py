from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gunray import DefeasibleEvaluator, DefeasibleTheory, ProjectionSemantics, Rule
from gunray.arguments import Argument
from gunray.errors import ContradictoryStrictTheoryError
from gunray.preference import SuperiorityPreference
from gunray.types import GroundAtom, GroundDefeasibleRule

SPINDLE_PAGE_002 = "papers/Lam_2009_MakingSPINdle/pngs/page-002.png"
SPINDLE_PAGE_004 = "papers/Lam_2009_MakingSPINdle/pngs/page-004.png"
MAHER_PAGE_001 = "papers/Maher_1999_SemanticDecomposition/pngs/page-001.png"
MAHER_PAGE_003 = "papers/Maher_1999_SemanticDecomposition/pngs/page-003.png"
GOVERNATORI_PAGE_027 = "papers/Governatori_2004_ArgumentationSemantics/pngs/page-027.png"

Sections = dict[str, dict[str, set[tuple[str, ...]]]]


def _has(sections: Sections, section: str, predicate: str) -> bool:
    return () in sections.get(section, {}).get(predicate, set())


def _model(theory: DefeasibleTheory, projection: ProjectionSemantics) -> Sections:
    return DefeasibleEvaluator().evaluate(theory, projection_semantics=projection).sections


def test_spindle_projection_classifies_unsatisfied_rule_head_as_negative() -> None:
    """Page-image sources: ``SPINDLE_PAGE_002`` and ``MAHER_PAGE_001``."""

    theory = DefeasibleTheory(
        facts={"p": {()}},
        defeasible_rules=[
            Rule(id="r1", head="r", body=["p", "q"]),
        ],
    )

    garcia = _model(theory, ProjectionSemantics.GARCIA)
    spindle = _model(theory, ProjectionSemantics.SPINDLE)

    assert not _has(garcia, "no", "r")
    assert _has(spindle, "no", "r")


@given(
    head=st.sampled_from(("ready_review", "ship", "audit")),
    missing=st.sampled_from(("tests_pass", "approval", "evidence")),
)
@settings(max_examples=12, deadline=None)
def test_spindle_negative_projection_is_consistent_for_defined_unprovable_heads(
    head: str,
    missing: str,
) -> None:
    """Page-image sources: ``SPINDLE_PAGE_002`` and ``MAHER_PAGE_003``."""

    theory = DefeasibleTheory(
        facts={"code_complete": {()}},
        defeasible_rules=[
            Rule(id="r1", head=head, body=["code_complete", missing]),
        ],
    )

    garcia = _model(theory, ProjectionSemantics.GARCIA)
    spindle = _model(theory, ProjectionSemantics.SPINDLE)

    assert not _has(garcia, "no", head)
    assert _has(spindle, "no", head)


def test_spindle_projection_tolerates_contradictory_strict_facts() -> None:
    """Page-image source: ``SPINDLE_PAGE_002`` — definite provability (+Δ)
    is monotonic strict derivation with no Π-consistency condition, so an
    inconsistent strict theory still answers YES on both complements. The
    Garcia path keeps its ``ContradictoryStrictTheoryError`` bright line
    (P1-T1); only the SPINdle projection tolerates the inconsistency.
    Conformance sources: ``spindle_racket_fact_conflict`` and
    ``spindle_racket_fact_vs_strict_rule_conflict``."""

    theory = DefeasibleTheory(
        facts={"p": {()}, "~p": {()}},
    )

    spindle = _model(theory, ProjectionSemantics.SPINDLE)
    assert _has(spindle, "yes", "p")
    assert _has(spindle, "yes", "~p")

    with pytest.raises(ContradictoryStrictTheoryError):
        _model(theory, ProjectionSemantics.GARCIA)


def test_spindle_projection_tolerates_fact_versus_strict_rule_conflict() -> None:
    """Page-image source: ``SPINDLE_PAGE_002``; conformance source:
    ``spindle_racket_fact_vs_strict_rule_conflict`` (fact ``p`` and strict
    ``~p :- q`` both definitely provable)."""

    theory = DefeasibleTheory(
        facts={"p": {()}, "q": {()}},
        strict_rules=[Rule(id="r1", head="~p", body=["q"])],
        conflicts=[("p", "~p")],
    )

    spindle = _model(theory, ProjectionSemantics.SPINDLE)
    assert _has(spindle, "yes", "p")
    assert _has(spindle, "yes", "~p")
    assert _has(spindle, "yes", "q")

    with pytest.raises(ContradictoryStrictTheoryError):
        _model(theory, ProjectionSemantics.GARCIA)


def test_spindle_projection_keeps_default_garcia_path_unchanged() -> None:
    """Page-image source: ``GOVERNATORI_PAGE_027`` separates policy variants."""

    theory = DefeasibleTheory(
        facts={"p": {()}},
        defeasible_rules=[
            Rule(id="r1", head="r", body=["p", "q"]),
        ],
    )

    default = DefeasibleEvaluator().evaluate(theory).sections
    explicit_garcia = _model(theory, ProjectionSemantics.GARCIA)
    spindle = _model(theory, ProjectionSemantics.SPINDLE)

    assert default == explicit_garcia
    assert default != spindle


@given(uncovered_rule=st.sampled_from(("r1", "r2")))
@settings(max_examples=2, deadline=None)
def test_partial_superiority_coverage_does_not_change_garcia_criterion(
    uncovered_rule: str,
) -> None:
    """Page-image source: ``SPINDLE_PAGE_004`` justifies separate SPINdle policy."""

    left_rules = frozenset(
        {
            GroundDefeasibleRule("r1", "defeasible", GroundAtom("left_a", ()), ()),
            GroundDefeasibleRule("r2", "defeasible", GroundAtom("left_b", ()), ()),
        }
    )
    right_rules = frozenset(
        {
            GroundDefeasibleRule("r3", "defeasible", GroundAtom("right", ()), ()),
        }
    )
    covered_rule = "r1" if uncovered_rule == "r2" else "r2"
    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="r1", head="left_a", body=[]),
            Rule(id="r2", head="left_b", body=[]),
            Rule(id="r3", head="right", body=[]),
        ],
        superiority=((covered_rule, "r3"),),
    )
    left = Argument(rules=left_rules, conclusion=GroundAtom("left", ()))
    right = Argument(rules=right_rules, conclusion=GroundAtom("right", ()))

    assert SuperiorityPreference(theory).prefers(left, right) is False
