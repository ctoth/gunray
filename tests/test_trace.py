from __future__ import annotations

from datalog_conformance.schema import DefeasibleTheory, Policy, Program, Rule

from gunray import GunrayEvaluator, TraceConfig
from gunray.types import GroundAtom


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


def test_datalog_trace_can_filter_rule_fires_and_capture_rows() -> None:
    evaluator = GunrayEvaluator()
    program = Program(
        facts={"edge": {("a", "b"), ("b", "c")}},
        rules=["path(X, Y) :- edge(X, Y).", "path(X, Z) :- edge(X, Y), path(Y, Z)."],
    )

    _, trace = evaluator.evaluate_with_trace(
        program,
        trace_config=TraceConfig(capture_derived_rows=True, max_derived_rows_per_rule_fire=1),
    )

    recursive_fires = trace.find_rule_fires(
        rule_text="path(X, Z) :- edge(X, Y), path(Y, Z).",
        head_predicate="path",
        derived_count_at_least=1,
    )

    assert recursive_fires
    assert all(len(fire.derived_rows) <= 1 for fire in recursive_fires)
    assert any(fire.derived_rows == (("a", "c"),) for fire in recursive_fires)


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


def test_defeasible_trace_helpers_expose_conflict_details() -> None:
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

    _, trace = evaluator.evaluate_with_trace(theory, Policy.BLOCKING)
    atom = GroundAtom(predicate="pacifist", arguments=("nixon",))
    opponent = GroundAtom(predicate="~pacifist", arguments=("nixon",))

    blocked_attempts = trace.proof_attempts_for(atom, result="blocked")
    undecided = trace.classifications_for(
        atom,
        result="undecided",
        reason="equal_strength_peer_conflict",
    )

    assert blocked_attempts
    assert any(attempt.opposing_atoms == (opponent,) for attempt in blocked_attempts)
    assert len(undecided) == 1
    assert undecided[0].supporter_rule_ids == ("r2",)
    assert undecided[0].attacker_rule_ids == ("r3",)
    assert undecided[0].opposing_atoms == (opponent,)


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


def test_strict_only_trace_exposes_underlying_datalog_trace() -> None:
    evaluator = GunrayEvaluator()
    theory = DefeasibleTheory(
        facts={"edge": {("a", "b"), ("b", "c")}},
        strict_rules=[
            Rule(id="r1", head="path(X, Y)", body=["edge(X, Y)"]),
            Rule(id="r2", head="path(X, Z)", body=["edge(X, Y)", "path(Y, Z)"]),
        ],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    model, trace = evaluator.evaluate_with_trace(
        theory,
        Policy.BLOCKING,
        trace_config=TraceConfig(capture_derived_rows=True, max_derived_rows_per_rule_fire=2),
    )

    assert model.sections["definitely"]["path"] == {("a", "b"), ("b", "c"), ("a", "c")}
    assert trace.strict_trace is not None
    strict_fires = trace.strict_trace.find_rule_fires(
        head_predicate="path",
        derived_count_at_least=1,
    )
    assert strict_fires
    assert any(("a", "c") in fire.derived_rows for fire in strict_fires)
