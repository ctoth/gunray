from __future__ import annotations

from datalog_conformance.schema import DefeasibleTheory, Policy, Program, Rule

from gunray import GunrayEvaluator


def test_datalog_trace_records_rule_fires() -> None:
    evaluator = GunrayEvaluator()
    program = Program(
        facts={"edge": {("a", "b"), ("b", "c")}},
        rules=["path(X, Y) :- edge(X, Y).", "path(X, Z) :- edge(X, Y), path(Y, Z)."],
    )

    model, trace = evaluator.evaluate_with_trace(program)

    assert model.facts["path"] == {("a", "b"), ("b", "c"), ("a", "c")}
    assert trace.strata
    assert any(
        fire.rule_text == "path(X, Y) :- edge(X, Y)."
        for stratum in trace.strata
        for iteration in stratum.iterations
        for fire in iteration.rule_fires
    )


def test_defeasible_trace_records_blocked_and_undecided_atoms() -> None:
    evaluator = GunrayEvaluator()
    theory = DefeasibleTheory(
        facts={"nixonian": {("nixon",)}, "quaker": {("nixon",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="republican(X)", body=["nixonian(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
            Rule(id="r3", head="~pacifist(X)", body=["republican(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    model, trace = evaluator.evaluate_with_trace(theory, Policy.BLOCKING)

    assert "undecided" in model.sections
    assert model.sections["undecided"]["pacifist"] == {("nixon",)}
    assert any(
        attempt.atom.predicate == "pacifist"
        and attempt.atom.arguments == ("nixon",)
        and attempt.result == "blocked"
        for attempt in trace.proof_attempts
    )
    assert any(
        classification.atom.predicate == "pacifist"
        and classification.atom.arguments == ("nixon",)
        and classification.result == "undecided"
        for classification in trace.classifications
    )


def test_defeasible_trace_marks_supported_but_unproved_body_as_undecided() -> None:
    evaluator = GunrayEvaluator()
    theory = DefeasibleTheory(
        facts={"penguin": {("tweety",)}},
        strict_rules=[
            Rule(id="r1", head="bird(X)", body=["penguin(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeasible_rules=[
            Rule(id="r3", head="flies(X)", body=["bird(X)"]),
            Rule(id="r4", head="nests_in_trees(X)", body=["flies(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    model, trace = evaluator.evaluate_with_trace(theory, Policy.BLOCKING)

    assert model.sections["undecided"]["nests_in_trees"] == {("tweety",)}
    assert any(
        classification.atom.predicate == "nests_in_trees"
        and classification.atom.arguments == ("tweety",)
        and classification.reason == "supported_only_by_unproved_bodies"
        for classification in trace.classifications
    )
