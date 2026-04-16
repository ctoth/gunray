from __future__ import annotations

import json
import string
from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gunray.errors import ParseError
from gunray.parser import (
    _is_constraint,
    evaluate_term,
    parse_atom_text,
    parse_constraint_text,
    parse_defeasible_rule,
    parse_rule_text,
    parse_value_term,
    split_top_level,
)
from gunray.schema import Rule as SchemaRule
from gunray.types import Comparison, Constant, Variable, Wildcard

_LOWER = string.ascii_lowercase
_UPPER = string.ascii_uppercase
_DIGITS = string.digits
_IDENTIFIER_TAIL = _LOWER + _DIGITS + "_"
_QUOTED_CHARS = _LOWER + _UPPER + _DIGITS + ' ,()\\"'
_INTEGER_OPERATORS: dict[str, Callable[[int, int], int]] = {
    "+": lambda left, right: left + right,
    "-": lambda left, right: left - right,
}


@st.composite
def _predicate_names(draw: st.DrawFn) -> str:
    head = draw(st.sampled_from(tuple(_LOWER)))
    tail = draw(st.text(alphabet=_IDENTIFIER_TAIL, min_size=0, max_size=6))
    return f"{head}{tail}"


@st.composite
def _variable_names(draw: st.DrawFn) -> str:
    head = draw(st.sampled_from(tuple(_UPPER)))
    tail = draw(st.text(alphabet=_IDENTIFIER_TAIL, min_size=0, max_size=6))
    return f"{head}{tail}"


@st.composite
def _quoted_literals(draw: st.DrawFn) -> tuple[str, str]:
    value = draw(st.text(alphabet=_QUOTED_CHARS, min_size=0, max_size=8))
    return json.dumps(value), value


@st.composite
def _top_level_items(draw: st.DrawFn) -> str:
    base = st.one_of(
        _predicate_names(),
        _variable_names(),
        _quoted_literals().map(lambda item: item[0]),
        st.integers(min_value=-10_000, max_value=10_000).map(str),
    )
    return draw(
        st.recursive(
            base,
            lambda inner: st.one_of(
                st.tuples(_predicate_names(), st.lists(inner, min_size=1, max_size=3)).map(
                    lambda item: f"{item[0]}({', '.join(item[1])})"
                ),
                st.lists(inner, min_size=1, max_size=3).map(lambda items: f"({', '.join(items)})"),
            ),
            max_leaves=6,
        )
    )


@st.composite
def _integer_expression_chains(draw: st.DrawFn) -> tuple[str, int]:
    values = draw(st.lists(st.integers(min_value=0, max_value=20), min_size=2, max_size=6))
    operators = draw(
        st.lists(
            st.sampled_from(tuple(_INTEGER_OPERATORS)),
            min_size=len(values) - 1,
            max_size=len(values) - 1,
        )
    )
    expression = str(values[0])
    expected = values[0]
    for operator, value in zip(operators, values[1:], strict=True):
        expression = f"{expression}{operator}{value}"
        expected = _INTEGER_OPERATORS[operator](expected, value)
    return expression, expected


@st.composite
def _comparison_texts(draw: st.DrawFn) -> tuple[str, str]:
    left, _ = draw(_integer_expression_chains())
    right, _ = draw(_integer_expression_chains())
    operator = draw(st.sampled_from(("<=", ">=", "==", "!=", "<", ">")))
    return f"({left} {operator} {right})", operator


@st.composite
def _simple_atom_texts(draw: st.DrawFn) -> str:
    predicate = draw(_predicate_names())
    terms = draw(
        st.lists(
            st.one_of(
                _variable_names(),
                st.integers(min_value=-9, max_value=9).map(str),
                _quoted_literals().map(lambda item: item[0]),
                st.sampled_from(("_", "_rest")),
            ),
            min_size=0,
            max_size=3,
        )
    )
    if not terms:
        return predicate
    return f"{predicate}({', '.join(terms)})"


@st.composite
def _rule_body_items(draw: st.DrawFn) -> list[tuple[str, str]]:
    item_count = draw(st.integers(min_value=1, max_value=5))
    items: list[tuple[str, str]] = []
    for _ in range(item_count):
        kind = draw(st.sampled_from(("positive", "negative", "constraint")))
        if kind == "positive":
            items.append((kind, draw(_simple_atom_texts())))
            continue
        if kind == "negative":
            items.append((kind, f"not {draw(_simple_atom_texts())}"))
            continue
        comparison, _ = draw(_comparison_texts())
        items.append((kind, comparison))
    return items


def test_split_top_level_handles_nested_calls_and_quoted_commas() -> None:
    text = 'p(X, inner("a,b", q(1, 2))), (x, y), "left,right"'

    assert split_top_level(text) == [
        'p(X, inner("a,b", q(1, 2)))',
        "(x, y)",
        '"left,right"',
    ]


def test_split_top_level_handles_escaped_quotes_inside_strings() -> None:
    text = '"say \\"hi, there\\"", p(X, "still, together"), tag'

    assert split_top_level(text) == [
        '"say \\"hi, there\\""',
        'p(X, "still, together")',
        "tag",
    ]


def test_parse_rule_text_partitions_positive_negative_and_constraints() -> None:
    rule = parse_rule_text('ok(X) :- person(X), not banned(X, Y), ("1" == "1"), (X <= 3).')

    assert rule.heads == (parse_atom_text("ok(X)"),)
    assert rule.positive_body == (parse_atom_text("person(X)"),)
    assert rule.negative_body == (parse_atom_text("banned(X, Y)"),)
    assert rule.constraints == (
        parse_constraint_text('("1" == "1")'),
        parse_constraint_text("(X <= 3)"),
    )


def test_parse_defeasible_rule_parses_head_and_body_atoms() -> None:
    rule = parse_defeasible_rule(
        SchemaRule(id="r1", head="~flies(X)", body=["bird(X)", 'tag(X, "forest,bird")']),
        kind="defeasible",
    )

    assert rule.rule_id == "r1"
    assert rule.kind == "defeasible"
    assert rule.head == parse_atom_text("~flies(X)")
    assert rule.body == (
        parse_atom_text("bird(X)"),
        parse_atom_text('tag(X, "forest,bird")'),
    )


def test_parse_constraint_text_recognizes_all_supported_operators() -> None:
    operators = ("<=", ">=", "==", "!=", "<", ">")

    for operator in operators:
        comparison = parse_constraint_text(f"(1 {operator} 2)")

        assert comparison == Comparison(
            left=parse_value_term("1"),
            operator=operator,
            right=parse_value_term("2"),
        )


def test_parse_atom_text_rejects_missing_predicate_name() -> None:
    with pytest.raises(ParseError, match="Missing predicate name|Unsupported atom syntax"):
        parse_atom_text("(X)")


def test_parse_rule_text_rejects_empty_rule() -> None:
    with pytest.raises(ParseError, match="Empty rule"):
        parse_rule_text("   ")


def test_parse_constraint_text_rejects_missing_operator() -> None:
    with pytest.raises(ParseError, match="Unsupported comparison literal"):
        parse_constraint_text("(value)")


def test_parse_atom_text_rejects_unterminated_string_literal() -> None:
    with pytest.raises(ParseError, match="Unterminated string literal"):
        parse_atom_text('p("value)')


def test_parse_atom_text_rejects_unbalanced_parentheses() -> None:
    with pytest.raises(ParseError, match="Unbalanced parentheses"):
        parse_atom_text("p(q(X)")


@given(items=st.lists(_top_level_items(), min_size=1, max_size=5))
def test_split_top_level_property_round_trips_generated_top_level_items(items: list[str]) -> None:
    text = ", ".join(items)

    assert split_top_level(text) == items


@given(value=_quoted_literals())
def test_parse_atom_text_property_preserves_quoted_string_identity(
    value: tuple[str, str],
) -> None:
    literal, expected = value
    atom = parse_atom_text(f"p({literal})")

    assert len(atom.terms) == 1
    (term,) = atom.terms
    assert isinstance(term, Constant)
    assert term.value == expected
    assert type(term.value) is str


@given(expression=_integer_expression_chains())
def test_parse_value_term_property_matches_left_associative_integer_arithmetic(
    expression: tuple[str, int],
) -> None:
    text, expected = expression

    assert evaluate_term(parse_value_term(text), {}) == expected


@given(comparison=_comparison_texts())
def test_parse_constraint_text_property_preserves_operator(
    comparison: tuple[str, str],
) -> None:
    text, expected_operator = comparison
    parsed = parse_constraint_text(text)

    assert parsed.operator == expected_operator


@given(left=_integer_expression_chains(), right=_integer_expression_chains())
def test_is_constraint_property_only_matches_top_level_comparisons(
    left: tuple[str, int],
    right: tuple[str, int],
) -> None:
    left_text, _ = left
    right_text, _ = right

    assert _is_constraint(f"({left_text} < {right_text})")
    assert not _is_constraint(f"wrap({left_text} < {right_text})")


@given(body_items=_rule_body_items())
def test_parse_rule_text_property_partitions_body_items_by_kind(
    body_items: list[tuple[str, str]],
) -> None:
    rule = parse_rule_text(f"head(X) :- {', '.join(text for _, text in body_items)}.")
    expected_positive = tuple(
        parse_atom_text(text) for kind, text in body_items if kind == "positive"
    )
    expected_negative = tuple(
        parse_atom_text(text[4:].strip()) for kind, text in body_items if kind == "negative"
    )
    expected_constraints = tuple(
        parse_constraint_text(text) for kind, text in body_items if kind == "constraint"
    )

    assert rule.positive_body == expected_positive
    assert rule.negative_body == expected_negative
    assert rule.constraints == expected_constraints


@given(atom_text=_simple_atom_texts())
def test_parse_atom_text_property_produces_supported_term_node_types(atom_text: str) -> None:
    atom = parse_atom_text(atom_text)

    for term in atom.terms:
        assert isinstance(term, Variable | Constant | Wildcard)
