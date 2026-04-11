from __future__ import annotations

from gunray.compiled import compile_simple_matcher, iter_compiled_bindings
from gunray.evaluator import (
    _iter_generic_positive_body_matches,
    _order_positive_body,
)
from gunray.relation import IndexedRelation
from gunray.types import AddExpression, Atom, Constant, Variable, Wildcard


def _sorted_bindings(bindings: list[dict[str, object]]) -> list[tuple[tuple[str, object], ...]]:
    return sorted(tuple(sorted(binding.items())) for binding in bindings)


def test_compiled_matcher_matches_generic_join() -> None:
    atoms = (
        Atom("edge", (Variable("x"), Variable("y"))),
        Atom("edge", (Variable("y"), Variable("z"))),
        Atom("mark", (Variable("z"),)),
    )
    model = {
        "edge": IndexedRelation({("a", "b"), ("b", "c"), ("b", "d")}),
        "mark": IndexedRelation({("c",)}),
    }
    overrides: dict[int, IndexedRelation] = {}
    ordered_atoms = _order_positive_body(atoms, model, overrides)
    compiled = compile_simple_matcher(ordered_atoms)

    assert compiled is not None
    assert _sorted_bindings(list(iter_compiled_bindings(compiled, model, overrides))) == _sorted_bindings(
        list(_iter_generic_positive_body_matches(ordered_atoms, model, overrides))
    )


def test_compiled_matcher_handles_constants_wildcards_and_same_row_equalities() -> None:
    atoms = (
        Atom("pair", (Constant("k"), Variable("x"), Variable("x"))),
        Atom("tag", (Variable("x"), Wildcard("_"))),
    )
    model = {
        "pair": IndexedRelation(
            {
                ("k", 1, 1),
                ("k", 1, 2),
                ("m", 1, 1),
            }
        ),
        "tag": IndexedRelation({(1, "ok"), (2, "no")}),
    }
    overrides = {1: IndexedRelation({(1, "ok")})}
    ordered_atoms = _order_positive_body(atoms, model, overrides)
    compiled = compile_simple_matcher(ordered_atoms)

    assert compiled is not None
    assert _sorted_bindings(list(iter_compiled_bindings(compiled, model, overrides))) == [
        (("x", 1),),
    ]


def test_compiled_matcher_rejects_expression_terms() -> None:
    atoms = [
        (
            0,
            Atom(
                "p",
                (
                    Variable("x"),
                    AddExpression(Variable("y"), Constant(1)),
                ),
            ),
        )
    ]

    assert compile_simple_matcher(atoms) is None
