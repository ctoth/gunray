from __future__ import annotations

from gunray.compiled import compile_simple_matcher, iter_compiled_bindings
from gunray.evaluator import (
    _apply_rule,
    _apply_rule_with_overrides,
    _iter_generic_positive_body_matches,
    _order_positive_body,
)
from gunray.relation import IndexedRelation
from gunray.types import AddExpression, Atom, Constant, Rule, Variable, Wildcard


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


def test_compiled_rule_application_matches_generic_delta() -> None:
    rule = Rule(
        heads=(Atom("path", (Variable("x"), Variable("z"))),),
        positive_body=(
            Atom("edge", (Variable("x"), Variable("y"))),
            Atom("edge", (Variable("y"), Variable("z"))),
        ),
        negative_body=(),
        constraints=(),
        source_text="path(x,z) :- edge(x,y), edge(y,z).",
    )
    model = {
        "edge": IndexedRelation({("a", "b"), ("b", "c"), ("c", "d")}),
        "path": IndexedRelation({("a", "c")}),
    }
    overrides: dict[int, IndexedRelation] = {}

    generic_delta = {"path": IndexedRelation()}
    ordered_atoms = _order_positive_body(rule.positive_body, model, overrides)
    _apply_rule(
        rule,
        model,
        generic_delta,
        _iter_generic_positive_body_matches(ordered_atoms, model, overrides),
    )

    compiled_delta = {"path": IndexedRelation()}
    _apply_rule_with_overrides(rule, model, compiled_delta, overrides)

    assert compiled_delta["path"].as_set() == generic_delta["path"].as_set()
