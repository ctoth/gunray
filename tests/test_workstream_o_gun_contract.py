from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

import gunray.dialectic as dialectic
from gunray import (
    ClosurePolicy,
    DefeasibleEvaluator,
    DefeasibleTheory,
    DialecticalNode,
    EnumerationExceeded,
    GroundAtom,
    MarkingPolicy,
    Rule,
    build_arguments,
    parse_atom_text,
)


def test_public_mark_memoizes_shared_subtrees(monkeypatch: pytest.MonkeyPatch) -> None:
    shared_leaf = DialecticalNode(
        argument=dialectic.Argument(frozenset(), GroundAtom("leaf", ())),
        children=(),
    )
    left = DialecticalNode(
        argument=dialectic.Argument(frozenset(), GroundAtom("left", ())),
        children=(shared_leaf,),
    )
    right = DialecticalNode(
        argument=dialectic.Argument(frozenset(), GroundAtom("right", ())),
        children=(shared_leaf,),
    )
    root = DialecticalNode(
        argument=dialectic.Argument(frozenset(), GroundAtom("root", ())),
        children=(left, right),
    )
    visited: list[int] = []
    original = dialectic.mark

    def counted(node: DialecticalNode):
        visited.append(id(node))
        return original(node)

    monkeypatch.setattr(dialectic, "mark", counted)

    assert dialectic.mark(root) == "U"
    assert len(visited) == len(set(visited))


def test_explicit_conflicts_are_seen_by_dialectical_path() -> None:
    theory = DefeasibleTheory(
        facts={"a": {()}, "b": {()}},
        defeasible_rules=(
            Rule(id="r1", head="p", body=("a",)),
            Rule(id="r2", head="q", body=("b",)),
        ),
        conflicts=(("p", "q"),),
    )

    model = DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)

    assert "p" not in model.sections.get("defeasibly", {})
    assert "q" not in model.sections.get("defeasibly", {})
    assert () in model.sections["undecided"]["p"]
    assert () in model.sections["undecided"]["q"]


def test_superiority_rejects_self_pair() -> None:
    with pytest.raises(ValueError, match="self"):
        DefeasibleTheory(
            defeasible_rules=(Rule(id="r1", head="p"),),
            superiority=(("r1", "r1"),),
        )


def test_superiority_rejects_cycle() -> None:
    with pytest.raises(ValueError, match="cycle"):
        DefeasibleTheory(
            defeasible_rules=(
                Rule(id="r1", head="p"),
                Rule(id="r2", head="q"),
            ),
            superiority=(("r1", "r2"), ("r2", "r1")),
        )


def test_strict_only_trace_populates_argument_view() -> None:
    theory = DefeasibleTheory(
        facts={"edge": {("a", "b")}},
        strict_rules=(Rule(id="s1", head="path(X, Y)", body=("edge(X, Y)",)),),
    )

    _model, trace = DefeasibleEvaluator().evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
    )

    path = GroundAtom("path", ("a", "b"))
    assert path in {argument.conclusion for argument in trace.arguments}
    assert trace.arguments_for_conclusion(path)
    assert trace.tree_for(path) == DialecticalNode(
        argument=trace.arguments_for_conclusion(path)[0],
        children=(),
    )
    assert trace.marking_for(path) == "U"


def test_build_arguments_budget_raises_with_partial_arguments() -> None:
    theory = DefeasibleTheory(
        facts={"a": {()}},
        defeasible_rules=(
            Rule(id="r1", head="p", body=("a",)),
            Rule(id="r2", head="q", body=("a",)),
        ),
    )

    with pytest.raises(EnumerationExceeded) as raised:
        build_arguments(theory, max_arguments=1)

    assert len(raised.value.partial_arguments) == 1
    assert raised.value.partial_trace is None
    assert "argument enumeration budget exceeded" in raised.value.reason


def test_evaluate_with_trace_budget_raises_with_partial_trace() -> None:
    theory = DefeasibleTheory(
        facts={"a": {()}},
        defeasible_rules=(
            Rule(id="r1", head="p", body=("a",)),
            Rule(id="r2", head="q", body=("a",)),
        ),
    )

    with pytest.raises(EnumerationExceeded) as raised:
        DefeasibleEvaluator().evaluate_with_trace(
            theory,
            marking_policy=MarkingPolicy.BLOCKING,
            max_arguments=1,
        )

    assert len(raised.value.partial_arguments) == 1
    assert raised.value.partial_trace is not None
    assert raised.value.partial_trace.arguments == raised.value.partial_arguments


@pytest.mark.property
@given(limit=st.integers(min_value=1, max_value=4))
def test_argument_budget_monotone_until_success(limit: int) -> None:
    theory = DefeasibleTheory(
        facts={"a": {()}},
        defeasible_rules=tuple(Rule(id=f"r{i}", head=f"p{i}", body=("a",)) for i in range(4)),
    )

    try:
        smaller = build_arguments(theory, max_arguments=limit)
    except EnumerationExceeded as smaller_exc:
        with pytest.raises(EnumerationExceeded) as larger_raised:
            build_arguments(theory, max_arguments=limit - 1)
        assert len(larger_raised.value.partial_arguments) <= len(smaller_exc.partial_arguments)
    else:
        larger = build_arguments(theory, max_arguments=limit + 1)
        assert smaller == larger


def test_parser_accepts_zero_arity_parentheses() -> None:
    assert parse_atom_text("p()") == parse_atom_text("p")


def test_policy_surface_is_split() -> None:
    assert MarkingPolicy.BLOCKING.value == "blocking"
    assert ClosurePolicy.RATIONAL_CLOSURE.value == "rational_closure"
    with pytest.raises(TypeError):
        DefeasibleEvaluator().evaluate(DefeasibleTheory(), MarkingPolicy.BLOCKING)
