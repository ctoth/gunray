from __future__ import annotations

from gunray import Program, SemiNaiveEvaluator


def test_negated_literal_allows_existentially_local_variable() -> None:
    program = Program(
        facts={"person": {("alice",)}},
        rules=[
            "ok(X) :- person(X), not banned(X, Y).",
        ],
    )

    model = SemiNaiveEvaluator().evaluate(program)

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

    model = SemiNaiveEvaluator().evaluate(program)

    assert model.facts["ok"] == {("alice",)}
