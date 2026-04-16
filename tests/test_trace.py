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
    """B1.6 re-land of the Nixon undecided trace assertion.

    The atom-level classifier from B1.2 was scorched in favor of the
    Garcia & Simari 2004 §5 paper pipeline. ``DefeasibleTrace`` still
    carries ``proof_attempts`` and ``classifications`` lists, now
    populated from the dialectical-tree pipeline by
    ``DefeasibleEvaluator._evaluate_via_argument_pipeline``: every
    undecided atom yields one ``ClassificationTrace`` (result =
    ``undecided``) and one ``ProofAttemptTrace`` (result =
    ``blocked``).
    """
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
    """B1.6 re-land of the Nixon conflict-detail helper assertion.

    The ``DefeasibleTrace.proof_attempts_for`` and
    ``classifications_for`` helpers survived B1.2 scorched earth (see
    ``trace.py``). B1.6 wires their populating data via the paper
    pipeline rather than the deleted classifier.

    **Re-land detail**: the original test asserted
    ``attacker_rule_ids == ("r3",)`` — that was wrong. The argument
    against ``pacifist(nixon)`` chains ``r1: republican(X) :- nixonian(X)``
    THEN ``r3: ~pacifist(X) :- republican(X)``, so the attacker rule
    set is ``("r1", "r3")``. The deleted classifier never modeled the
    chained rule and surfaced only ``r3``; the paper pipeline
    surfaces both because both are needed to derive the opposing
    literal. The semantic invariant — "the conflict-detail helpers
    expose the supporter, attacker, and opposing literal of a
    blocked atom" — is preserved.
    """
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
    assert undecided[0].attacker_rule_ids == ("r1", "r3")
    assert undecided[0].opposing_atoms == (opponent,)


def test_defeasible_trace_marks_supported_but_unproved_body_as_undecided() -> None:
    """B1.6 re-land of the ``nests_in_trees`` body-failure case.

    **Original assertion** (deleted classifier era): the literal
    ``nests_in_trees(tweety)`` lands in ``undecided`` with
    classification reason ``supported_only_by_unproved_bodies``.

    **Paper-correct behavior** (Garcia & Simari 2004 Def 3.1
    cond 2): the strict closure of ``Π = {penguin(tweety)}`` under
    ``r1: bird :- penguin`` and ``r2: ~flies :- penguin`` already
    contains ``~flies(tweety)``. Adding the defeasible rule
    ``r3: flies :- bird`` to ``Π`` yields a closure containing both
    ``flies(tweety)`` and ``~flies(tweety)`` — contradictory. By
    Def 3.1 cond 2, NO argument for ``flies(tweety)`` can exist,
    and therefore NO argument for ``nests_in_trees(tweety)`` can
    exist either. Both literals are omitted from every section.

    The semantic invariant the original test guarded was:
    *"a defeasible head whose body cannot be derived must not be
    asserted defeasibly."* The paper pipeline preserves that
    invariant by excluding ``nests_in_trees(tweety)`` from the
    ``defeasibly`` section. The departure from the original test is
    that the paper pipeline does NOT classify the literal as
    ``undecided`` either — UNDECIDED requires *some* argument for
    the literal or its complement (Def 5.3), and there is none.
    See ``notes/refactor_progress.md#deviations`` (B1.6 entry) for
    the full disagreement record.
    """
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

    # Semantic invariant: the unsupported defeasible head must NOT
    # land in defeasibly, definitely, or not_defeasibly.
    defeasibly = model.sections.get("defeasibly", {}).get("nests_in_trees", set())
    definitely = model.sections.get("definitely", {}).get("nests_in_trees", set())
    not_defeasibly = model.sections.get("not_defeasibly", {}).get("nests_in_trees", set())
    assert ("tweety",) not in defeasibly
    assert ("tweety",) not in definitely
    assert ("tweety",) not in not_defeasibly

    # And the strict ``~flies(tweety)`` does land in definitely.
    assert ("tweety",) in model.sections["definitely"]["~flies"]

    # The trace's classifications list does not record an entry for
    # ``nests_in_trees(tweety)`` because the paper pipeline produces
    # no argument for it at all. Guard against accidental
    # re-introduction of a non-paper classification reason.
    no_nests_classification = not any(
        classification.atom.predicate == "nests_in_trees"
        and classification.atom.arguments == ("tweety",)
        for classification in trace.classifications
    )
    assert no_nests_classification


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

    assert (
        trace.find_rule_fires(
            head_predicate=head_predicate,
            derived_count_at_least=minimum_count,
        )
        == expected
    )


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
