from __future__ import annotations

from gunray import NegationSemantics, Program, SemiNaiveEvaluator
from gunray._internal import _unify
from gunray.types import Atom, Variable


def test_negated_literal_allows_existentially_local_variable() -> None:
    program = Program(
        facts={"person": {("alice",)}},
        rules=[
            "ok(X) :- person(X), not banned(X, Y).",
        ],
    )

    model = SemiNaiveEvaluator().evaluate(
        program,
        negation_semantics=NegationSemantics.NEMO,
    )

    assert model.facts["ok"] == {("alice",)}


def test_negated_literal_blocks_when_any_matching_row_exists() -> None:
    program = Program(
        facts={
            "person": {("alice",), ("bob",)},
            "banned": {("bob", "infractions")},
        },
        rules=[
            "ok(X) :- person(X), not banned(X, Y).",
        ],
    )

    model = SemiNaiveEvaluator().evaluate(
        program,
        negation_semantics=NegationSemantics.NEMO,
    )

    assert model.facts["ok"] == {("alice",)}


def test_unify_distinguishes_none_value_from_unbound() -> None:
    """A binding containing ``None`` is bound and must not be treated as absent."""

    atom = Atom(predicate="p", terms=(Variable("X"),))
    bindings = {"X": None}

    assert _unify(atom, ("a",), bindings) is None
