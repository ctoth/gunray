from __future__ import annotations

from gunray.parser import evaluate_term, normalize_facts, parse_atom_text, parse_value_term
from gunray.types import Constant


def test_parse_atom_text_preserves_quoted_string_constant_identity() -> None:
    atom = parse_atom_text('p("1")')

    assert len(atom.terms) == 1
    (term,) = atom.terms
    assert isinstance(term, Constant)
    assert term.value == "1"
    assert type(term.value) is str


def test_normalize_facts_keeps_distinct_quoted_string_scalars_distinct() -> None:
    normalized = normalize_facts(
        {
            "p": [
                ("01",),
                ("true",),
                ("1.0",),
            ]
        }
    )

    assert normalized["p"] == {
        ("01",),
        ("true",),
        ("1.0",),
    }


def test_parse_value_term_treats_minus_chains_as_left_associative() -> None:
    term = parse_value_term("1-2-3")

    assert evaluate_term(term, {}) == -4


def test_parse_value_term_respects_left_associativity_for_mixed_plus_minus() -> None:
    term = parse_value_term("1+2-3")

    assert evaluate_term(term, {}) == 0
