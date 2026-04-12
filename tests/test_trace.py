from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from gunray import DefeasibleTheory, GunrayEvaluator, Policy, Program, Rule, TraceConfig
from gunray.types import GroundAtom

_NODES = ("a", "b", "c", "d")
_FORWARD_EDGES = tuple(
    (_NODES[left], _NODES[right])
    for left in range(len(_NODES))
    for right in range(left + 1, len(_NODES))
)


@st.composite
def _edge_sets(draw: st.DrawFn) -> set[tuple[str, str]]:
    return set(draw(st.lists(st.sampled_from(_FORWARD_EDGES), unique=True)))


def _edge_facts(edges: set[tuple[str, str]]) -> dict[str, set[tuple[str, str]]]:
    if not edges:
        return {}
    return {"edge": edges}


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


@given(edges=_edge_sets(), row_limit=st.integers(min_value=0, max_value=3))
def test_datalog_trace_property_captured_rows_land_in_final_model(
    edges: set[tuple[str, str]],
    row_limit: int,
) -> None:
    evaluator = GunrayEvaluator()
    program = Program(
        facts=_edge_facts(edges),
        rules=["path(X, Y) :- edge(X, Y).", "path(X, Z) :- edge(X, Y), path(Y, Z)."],
    )

    model, trace = evaluator.evaluate_with_trace(
        program,
        trace_config=TraceConfig(
            capture_derived_rows=True,
            max_derived_rows_per_rule_fire=row_limit,
        ),
    )

    all_fires = trace.all_rule_fires()
    path_rows = model.facts.get("path", set())
    for fire in all_fires:
        assert len(fire.derived_rows) <= row_limit
        assert all(row in path_rows for row in fire.derived_rows)


@given(
    edges=_edge_sets(),
    minimum_count=st.integers(min_value=0, max_value=3),
    head_predicate=st.sampled_from(("path", "edge", "missing")),
)
def test_datalog_trace_property_find_rule_fires_matches_manual_filter(
    edges: set[tuple[str, str]],
    minimum_count: int,
    head_predicate: str,
) -> None:
    evaluator = GunrayEvaluator()
    program = Program(
        facts=_edge_facts(edges),
        rules=["path(X, Y) :- edge(X, Y).", "path(X, Z) :- edge(X, Y), path(Y, Z)."],
    )

    _, trace = evaluator.evaluate_with_trace(program)

    expected = tuple(
        fire
        for fire in trace.all_rule_fires()
        if fire.head_predicate == head_predicate and fire.derived_count >= minimum_count
    )

    assert trace.find_rule_fires(
        head_predicate=head_predicate,
        derived_count_at_least=minimum_count,
    ) == expected


@given(edges=_edge_sets(), row_limit=st.integers(min_value=0, max_value=3))
def test_strict_only_trace_property_matches_definite_section(
    edges: set[tuple[str, str]],
    row_limit: int,
) -> None:
    evaluator = GunrayEvaluator()
    theory = DefeasibleTheory(
        facts=_edge_facts(edges),
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
        trace_config=TraceConfig(
            capture_derived_rows=True,
            max_derived_rows_per_rule_fire=row_limit,
        ),
    )

    assert trace.strict_trace is not None
    assert set(trace.definitely) == set(trace.supported)

    definitely_path_rows = model.sections.get("definitely", {}).get("path", set())
    for fire in trace.strict_trace.find_rule_fires(head_predicate="path"):
        assert len(fire.derived_rows) <= row_limit
        assert all(row in definitely_path_rows for row in fire.derived_rows)
