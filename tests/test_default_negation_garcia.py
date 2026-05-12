from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    GroundAtom,
    MarkingPolicy,
    Rule,
    build_arguments,
    counter_argues,
)
from gunray._internal import _force_strict_for_closure
from gunray.disagreement import strict_closure
from gunray.errors import ParseError

GARCIA_PAGE_029 = "papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-029.png"
GARCIA_PAGE_030 = "papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-030.png"
GARCIA_PAGE_031 = "papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-031.png"


def test_definition_6_1_ignores_default_negation_for_derivability_only() -> None:
    """Garcia page-030.png Def 6.1: not-literals are ignored only for derivation."""

    assert GARCIA_PAGE_030.endswith("page-030.png")
    theory = DefeasibleTheory(
        facts={"q": {()}},
        defeasible_rules=[Rule(id="r_p", head="p", body=["q", "not s"])],
    )

    model, trace = DefeasibleEvaluator().evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert () in model.sections["yes"]["p"]
    [argument] = trace.arguments_for_conclusion_parts("p")
    [rule] = tuple(argument.rules)
    assert rule.default_negated_body == (GroundAtom("s", ()),)


def test_definition_6_2_rejects_self_defeating_argument() -> None:
    """Garcia page-030.png Def 6.2 rejects deriving L through a rule using not L."""

    assert GARCIA_PAGE_030.endswith("page-030.png")
    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="r_a", head="a", body=["b"]),
            Rule(id="r_b", head="b", body=["not a"]),
        ],
    )

    arguments = build_arguments(theory)

    assert not any(argument.conclusion == GroundAtom("a", ()) for argument in arguments)
    assert any(argument.conclusion == GroundAtom("b", ()) for argument in arguments)


def test_definition_6_3_argument_attacks_default_negation_assumption() -> None:
    """Garcia page-031.png Def 6.3: an argument for L attacks assumptions not L."""

    assert GARCIA_PAGE_031.endswith("page-031.png")
    theory = DefeasibleTheory(
        facts={"q": {()}, "s": {()}},
        defeasible_rules=[Rule(id="r_p", head="p", body=["q", "not s"])],
    )
    arguments = build_arguments(theory)
    attacker = next(
        argument for argument in arguments if argument.conclusion == GroundAtom("s", ())
    )
    target = next(argument for argument in arguments if argument.conclusion == GroundAtom("p", ()))

    model = DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)

    assert counter_argues(attacker, target, theory, universe=arguments)
    assert () not in model.sections["yes"].get("p", set())
    assert () in model.sections["undecided"]["p"]


def test_example_6_1_is_not_strong_negation_priority_rewrite() -> None:
    """Garcia page-031.png Example 6.1: the strong-negation rewrite is not equivalent."""

    assert GARCIA_PAGE_031.endswith("page-031.png")
    original = DefeasibleTheory(
        facts={"q": {()}, "s": {()}},
        defeasible_rules=[
            Rule(id="r_p", head="p", body=["q", "not s"]),
            Rule(id="r_a", head="a", body=["q"]),
            Rule(id="r_not_a", head="~a", body=["~p"]),
        ],
    )
    transformed = DefeasibleTheory(
        facts={"q": {()}, "s": {()}},
        defeasible_rules=[
            Rule(id="r_p", head="p", body=["q"]),
            Rule(id="r_not_p", head="~p", body=["s"]),
            Rule(id="r_a", head="a", body=["q"]),
            Rule(id="r_not_a", head="~a", body=["~p"]),
        ],
        superiority=(("r_not_p", "r_p"),),
    )
    evaluator = DefeasibleEvaluator()

    original_model = evaluator.evaluate(original, marking_policy=MarkingPolicy.BLOCKING)
    transformed_model = evaluator.evaluate(transformed, marking_policy=MarkingPolicy.BLOCKING)

    assert () not in original_model.sections["yes"].get("~p", set())
    assert () in transformed_model.sections["yes"]["~p"]
    assert original_model.sections != transformed_model.sections


@given(has_forbidden_fact=st.booleans())
@settings(max_examples=20, deadline=None)
def test_hypothesis_accepted_arguments_do_not_contradict_default_assumptions(
    has_forbidden_fact: bool,
) -> None:
    """Garcia page-030.png Def 6.2: accepted rule sets do not defeat themselves."""

    facts = {"q": {()}}
    if has_forbidden_fact:
        facts["s"] = {()}
    theory = DefeasibleTheory(
        facts=facts,
        defeasible_rules=[Rule(id="r_p", head="p", body=["q", "not s"])],
    )

    for argument in build_arguments(theory):
        shadow_rules = tuple(_force_strict_for_closure(rule) for rule in argument.rules)
        fact_atoms = frozenset(
            GroundAtom(predicate, row) for predicate, rows in facts.items() for row in rows
        )
        pi_closure = strict_closure(fact_atoms, ())
        closure = strict_closure(
            fact_atoms,
            shadow_rules,
        )
        default_assumptions = {
            atom for rule in argument.rules for atom in rule.default_negated_body
        }
        assert not default_assumptions & (closure - pi_closure)


@given(constant=st.sampled_from(("a", "b", "c")))
@settings(max_examples=10, deadline=None)
def test_hypothesis_warranted_literal_attacks_default_dependent_argument(
    constant: str,
) -> None:
    """Garcia page-031.png Def 6.3: warranting L cannot warrant a not L argument."""

    theory = DefeasibleTheory(
        facts={"support": {(constant,)}, "blocked": {(constant,)}},
        defeasible_rules=[Rule(id="r_h", head="h(X)", body=["support(X)", "not blocked(X)"])],
    )

    model = DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)

    assert (constant,) in model.sections["yes"]["blocked"]
    assert (constant,) not in model.sections["yes"].get("h", set())


@given(predicate=st.sampled_from(("p", "q", "r")))
@settings(max_examples=10, deadline=None)
def test_hypothesis_strict_rules_reject_default_negated_bodies(predicate: str) -> None:
    """Garcia page-029.png: default negation is allowed only in defeasible bodies."""

    assert GARCIA_PAGE_029.endswith("page-029.png")
    theory = DefeasibleTheory(
        facts={"base": {()}},
        strict_rules=[Rule(id="s_bad", head=predicate, body=["base", "not blocked"])],
    )

    with pytest.raises(ParseError):
        DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)


@given(predicate=st.sampled_from(("h", "k", "m")))
@settings(max_examples=10, deadline=None)
def test_hypothesis_removing_irrelevant_default_negation_preserves_answers(
    predicate: str,
) -> None:
    """Garcia page-030.png Def 6.1: irrelevant not-literals do not affect derivation."""

    with_default = DefeasibleTheory(
        facts={"base": {()}},
        defeasible_rules=[Rule(id="r_h", head=predicate, body=["base", "not irrelevant"])],
    )
    without_default = DefeasibleTheory(
        facts={"base": {()}},
        defeasible_rules=[Rule(id="r_h", head=predicate, body=["base"])],
    )
    evaluator = DefeasibleEvaluator()

    assert (
        evaluator.evaluate(with_default, marking_policy=MarkingPolicy.BLOCKING).sections
        == evaluator.evaluate(without_default, marking_policy=MarkingPolicy.BLOCKING).sections
    )
