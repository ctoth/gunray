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
    Variable,
    compute_non_approximated,
    inspect_grounding,
)

DILLER_PAGE_002 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-002.png"
DILLER_PAGE_005 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-005.png"
DILLER_PAGE_006 = "papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-006.png"


def test_grounding_mode_surface_is_public_and_default_direct() -> None:
    """Diller execution is explicit; direct Garcia/Simari evaluation remains default."""

    assert DILLER_PAGE_002.endswith("page-002.png")
    assert GroundingMode.DIRECT.value == "direct"
    assert GroundingMode.DILLER_SIMPLIFIED.value == "diller_simplified"


def test_diller_example_1_shaped_grounding_executes_equivalently() -> None:
    """Diller page-002.png Example 1 shape: facts, strict rules, assumptions, attacks."""

    assert DILLER_PAGE_002.endswith("page-002.png")
    theory = DefeasibleTheory(
        facts={"f": {(1, 2)}},
        strict_rules=[Rule(id="s_b", head="b(X)", body=["f(X, 2)"])],
        defeasible_rules=[
            Rule(id="d_c1", head="c(1)", body=["a(1)"]),
            Rule(id="d_c2", head="c(2)", body=["a(2)"]),
            Rule(id="d_e1", head="e(1)", body=["c(1)"]),
            Rule(id="d_e2", head="e(2)", body=["c(2)"]),
        ],
        presumptions=[
            Rule(id="p_a1", head="a(1)"),
            Rule(id="p_a2", head="a(2)"),
        ],
        conflicts=(("a", "b"), ("c", "d"), ("n_d", "e")),
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
    assert {rule.rule_id for rule in trace.grounding_inspection.all_rule_instances} == {
        "d_c1",
        "d_c2",
        "d_e1",
        "d_e2",
        "p_a1",
        "p_a2",
        "s_b",
    }
    assert GroundAtom("b", (1,)) in trace.grounding_inspection.simplification.definite_fact_atoms


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


@given(theory=diller_supported_chain_theory())
@settings(max_examples=50, deadline=None)
def test_hypothesis_diller_simplification_invariants(
    theory: DefeasibleTheory,
) -> None:
    """Diller pages 005-006: simplification removes strict scaffolding, not rules."""

    inspection = inspect_grounding(theory)
    simplification = inspection.simplification

    assert set(simplification.defeasible_rules_for_argumentation) <= set(
        inspection.defeasible_rules
    )
    assert set(simplification.defeater_rules_for_argumentation) <= set(inspection.defeater_rules)
    assert len(simplification.defeasible_rules_for_argumentation) <= len(
        inspection.defeasible_rules
    )
    assert len(simplification.defeater_rules_for_argumentation) <= len(inspection.defeater_rules)

    strict_only = DefeasibleTheory(
        facts=theory.facts,
        strict_rules=theory.strict_rules,
        conflicts=theory.conflicts,
    )
    strict_model = DefeasibleEvaluator().evaluate(
        strict_only,
        marking_policy=MarkingPolicy.BLOCKING,
    )
    for atom in simplification.definite_fact_atoms:
        assert atom.arguments in strict_model.sections["yes"].get(atom.predicate, set())

    for rule in simplification.ground_rules_for_argumentation:
        atoms = (rule.head,) + rule.body + rule.default_negated_body
        assert all(not isinstance(value, Variable) for atom in atoms for value in atom.arguments)


@given(theory=diller_supported_chain_theory())
@settings(max_examples=50, deadline=None)
def test_hypothesis_non_approximated_is_monotone_for_independent_strict_facts(
    theory: DefeasibleTheory,
) -> None:
    """Diller page-005.png Definition 12: independent strict/fact predicates compose."""

    base = compute_non_approximated(theory)
    extended = DefeasibleTheory(
        facts={
            **theory.facts,
            "independent_fact": {("witness",)},
        },
        strict_rules=theory.strict_rules
        + (Rule(id="s_independent", head="independent_head(X)", body=["independent_fact(X)"]),),
        defeasible_rules=theory.defeasible_rules,
        defeaters=theory.defeaters,
        presumptions=theory.presumptions,
        superiority=theory.superiority,
        conflicts=theory.conflicts,
    )

    extended_predicates = compute_non_approximated(extended)

    assert base <= extended_predicates
    assert {"independent_fact", "independent_head"} <= extended_predicates
