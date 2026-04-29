from __future__ import annotations

from conftest import small_theory_strategy
from hypothesis import given
from hypothesis import strategies as st

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    DefeasibleTrace,
    GunrayEvaluator,
    MarkingPolicy,
    Program,
    Rule,
    TraceConfig,
    complement,
    render_tree,
)
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


def _classic_tweety_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_defeasible_trace_captures_arguments() -> None:
    model, trace = DefeasibleEvaluator().evaluate_with_trace(
        _classic_tweety_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert trace.arguments
    for section, facts_map in model.sections.items():
        for predicate, rows in facts_map.items():
            for row in rows:
                atom = GroundAtom(predicate=predicate, arguments=row)
                matching = trace.arguments_for_conclusion(atom)
                if section == "yes":
                    assert matching, f"no argument for {atom} in {section}"
                if section == "no":
                    opposite = trace.arguments_for_conclusion(complement(atom))
                    assert matching or opposite, f"no argument pair for {atom} in {section}"


def test_defeasible_trace_captures_trees_and_markings() -> None:
    _, trace = DefeasibleEvaluator().evaluate_with_trace(
        _classic_tweety_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )
    tweety_flies = GroundAtom(predicate="flies", arguments=("tweety",))

    tree = trace.tree_for(tweety_flies)
    marking = trace.marking_for(tweety_flies)

    assert tree is not None
    assert marking in ("U", "D")
    rendered = render_tree(tree)
    assert isinstance(rendered, str) and rendered.strip()


def test_defeasible_trace_can_query_by_predicate_and_row() -> None:
    _, trace = DefeasibleEvaluator().evaluate_with_trace(
        _classic_tweety_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert trace.tree_for_parts("flies", ("tweety",)) is not None
    assert trace.marking_for_parts("flies", ("tweety",)) in ("U", "D")
    assert trace.arguments_for_conclusion_parts("flies", ("tweety",))


def test_deleted_fields_absent() -> None:
    """Post-restructure: the flat rule-fire trace fields are gone."""

    trace = DefeasibleTrace()

    assert not hasattr(trace, "proof_attempts")
    assert not hasattr(trace, "classifications")
    assert not hasattr(trace, "proof_attempts_for")
    assert not hasattr(trace, "classifications_for")


@given(small_theory_strategy())
def test_hypothesis_markings_have_trees(theory: DefeasibleTheory) -> None:
    """Every atom with a marking has a corresponding tree."""

    _, trace = DefeasibleEvaluator().evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
    )

    for atom in trace.markings:
        assert atom in trace.trees, f"{atom} marked but no tree"


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
        marking_policy=MarkingPolicy.BLOCKING,
        trace_config=TraceConfig(capture_derived_rows=True, max_derived_rows_per_rule_fire=2),
    )

    assert model.sections["yes"]["path"] == {("a", "b"), ("b", "c"), ("a", "c")}
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
def test_strict_only_trace_property_matches_yes_section(
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
        marking_policy=MarkingPolicy.BLOCKING,
        trace_config=TraceConfig(
            capture_derived_rows=True,
            max_derived_rows_per_rule_fire=row_limit,
        ),
    )

    assert trace.strict_trace is not None
    assert set(trace.strict) == set(trace.yes)

    yes_path_rows = model.sections.get("yes", {}).get("path", set())
    for fire in trace.strict_trace.find_rule_fires(head_predicate="path"):
        assert len(fire.derived_rows) <= row_limit
        assert all(row in yes_path_rows for row in fire.derived_rows)
