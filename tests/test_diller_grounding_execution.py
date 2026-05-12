from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    GroundAtom,
    GroundingMode,
    MarkingPolicy,
    Rule,
)

DILLER_PAGE_002 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-002.png"
DILLER_PAGE_005 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-005.png"
DILLER_PAGE_006 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-006.png"


def test_grounding_mode_surface_is_public_and_default_direct() -> None:
    """Diller execution is explicit; direct Garcia/Simari evaluation remains default."""

    assert DILLER_PAGE_002.endswith("page-002.png")
    assert GroundingMode.DIRECT.value == "direct"
    assert GroundingMode.DILLER_SIMPLIFIED.value == "diller_simplified"


def test_diller_strict_fact_simplification_executes_equivalently() -> None:
    """Diller page-006.png: strict/fact simplification can be used for evaluation."""

    assert DILLER_PAGE_006.endswith("page-006.png")
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[Rule(id="s_animal", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[Rule(id="r_flies", head="flies(X)", body=["animal(X)"])],
    )
    evaluator = DefeasibleEvaluator()

    direct = evaluator.evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    simplified, trace = evaluator.evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
        grounding_mode=GroundingMode.DILLER_SIMPLIFIED,
    )

    assert simplified.sections == direct.sections
    assert trace.grounding_inspection is not None
    assert trace.grounding_inspection.simplification.strict_rules_for_argumentation == ()
    assert trace.grounding_inspection.simplification.definite_fact_atoms == (
        GroundAtom("animal", ("tweety",)),
        GroundAtom("bird", ("tweety",)),
    )


def test_diller_route_preserves_default_negated_bodies() -> None:
    """Diller page-005.png route must not erase Garcia default-negation assumptions."""

    assert DILLER_PAGE_005.endswith("page-005.png")
    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}, "abnormal": {("tweety",)}},
        strict_rules=[Rule(id="s_animal", head="animal(X)", body=["bird(X)"])],
        defeasible_rules=[
            Rule(id="r_flies", head="flies(X)", body=["animal(X)", "not abnormal(X)"])
        ],
    )
    evaluator = DefeasibleEvaluator()

    direct = evaluator.evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    simplified, trace = evaluator.evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
        grounding_mode=GroundingMode.DILLER_SIMPLIFIED,
    )

    assert simplified.sections == direct.sections
    assert () not in simplified.sections["yes"].get("flies", set())
    assert trace.grounding_inspection is not None
    [ground_rule] = trace.grounding_inspection.simplification.defeasible_rules_for_argumentation
    assert ground_rule.default_negated_body == (GroundAtom("abnormal", ("tweety",)),)


@st.composite
def diller_supported_chain_theory(draw: st.DrawFn) -> DefeasibleTheory:
    constant_count = draw(st.integers(min_value=1, max_value=3))
    constants = tuple(f"c{i}" for i in range(constant_count))
    facts = {"p0": {(constant,) for constant in constants}}
    strict_count = draw(st.integers(min_value=0, max_value=3))
    strict_rules = tuple(
        Rule(id=f"s{i}", head=f"p{i + 1}(X)", body=[f"p{i}(X)"]) for i in range(strict_count)
    )
    body_predicate = f"p{draw(st.integers(min_value=0, max_value=strict_count))}"
    defeasible_rules = (
        Rule(id="r_h", head="h(X)", body=[f"{body_predicate}(X)"]),
        Rule(id="r_not_h", head="~h(X)", body=["p0(X)"]),
    )
    return DefeasibleTheory(
        facts=facts,
        strict_rules=strict_rules,
        defeasible_rules=defeasible_rules,
    )


@given(theory=diller_supported_chain_theory())
@settings(max_examples=50, deadline=None)
def test_hypothesis_diller_simplified_answers_match_direct(
    theory: DefeasibleTheory,
) -> None:
    """Diller Theorem 2 page-006.png: supported simplification is answer-equivalent."""

    evaluator = DefeasibleEvaluator()
    direct = evaluator.evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    simplified = evaluator.evaluate(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
        grounding_mode=GroundingMode.DILLER_SIMPLIFIED,
    )

    assert simplified.sections == direct.sections
