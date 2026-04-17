from __future__ import annotations

import gunray.evaluator as evaluator
from gunray._internal import (
    _iter_generic_positive_body_matches,
    _order_positive_body,
)
from gunray.compiled import compile_simple_matcher, iter_compiled_bindings
from gunray.evaluator import SemiNaiveEvaluator, _apply_rule, apply_rule_with_overrides
from gunray.relation import IndexedRelation
from gunray.schema import Program
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
    actual = _sorted_bindings(list(iter_compiled_bindings(compiled, model, overrides)))
    expected = _sorted_bindings(
        list(_iter_generic_positive_body_matches(ordered_atoms, model, overrides))
    )
    assert actual == expected


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
    apply_rule_with_overrides(
        rule,
        model,
        compiled_delta,
        overrides,
        preferred_first_index=None,
        iteration_trace=None,
    )

    assert compiled_delta["path"].as_set() == generic_delta["path"].as_set()


def test_order_positive_body_prefers_delta_atom_when_safe() -> None:
    atoms = (
        Atom("big", (Variable("x"), Variable("y"))),
        Atom("delta", (Variable("y"), Variable("z"))),
        Atom("small", (Variable("z"),)),
    )
    model = {
        "big": IndexedRelation({("a", "b"), ("b", "c"), ("c", "d")}),
        "delta": IndexedRelation({("b", "c")}),
        "small": IndexedRelation({("c",)}),
    }

    ordered = _order_positive_body(
        atoms,
        model,
        {1: model["delta"]},
        preferred_first_index=1,
    )

    assert ordered[0][0] == 1


def test_order_positive_body_prefers_lower_lookup_fanout() -> None:
    atoms = (
        Atom("seed", (Variable("x"),)),
        Atom("small_total_high_fanout", (Variable("x"), Variable("y"))),
        Atom("large_total_low_fanout", (Variable("x"), Variable("z"))),
    )
    model = {
        "seed": IndexedRelation({("k",)}),
        "small_total_high_fanout": IndexedRelation(
            {
                ("k", 1),
                ("k", 2),
                ("k", 3),
            }
        ),
        "large_total_low_fanout": IndexedRelation(
            {
                ("k", 1),
                ("m1", 1),
                ("m2", 1),
                ("m3", 1),
                ("m4", 1),
                ("m5", 1),
            }
        ),
    }

    ordered = _order_positive_body(atoms, model, {}, preferred_first_index=0)

    assert [item[0] for item in ordered[:2]] == [0, 2]


def test_order_positive_body_does_not_materialize_costing_indexes() -> None:
    atoms = (
        Atom("seed", (Variable("x"),)),
        Atom("left", (Variable("x"), Variable("y"))),
        Atom("right", (Variable("x"), Variable("z"))),
    )
    model = {
        "seed": IndexedRelation({("k",)}),
        "left": IndexedRelation({("k", 1), ("k", 2), ("m", 3)}),
        "right": IndexedRelation({("k", 1), ("n", 2), ("o", 3)}),
    }

    _order_positive_body(atoms, model, {}, preferred_first_index=0)

    assert model["left"]._indexes == {}
    assert model["right"]._indexes == {}


def test_simple_rules_are_compiled_once_per_ordered_plan(monkeypatch) -> None:
    program = Program(
        facts={"edge": {("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")}},
        rules=[
            "path(X,Y) :- edge(X,Y).",
            "path(X,Z) :- path(X,Y), edge(Y,Z).",
        ],
    )
    calls = 0
    original = evaluator.compile_simple_rule

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(evaluator, "compile_simple_rule", counted)

    SemiNaiveEvaluator().evaluate(program)

    assert calls == 2
