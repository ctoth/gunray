"""Anytime cardinality ceilings for adversarial enumerators."""

from __future__ import annotations

from gunray import EnumerationExceeded
from gunray._internal import _head_only_bindings
from gunray.parser import parse_defeasible_rule
from gunray.relation import IndexedRelation
from gunray.schema import Rule


def test_head_only_bindings_returns_enumeration_exceeded_past_ceiling() -> None:
    """Zilberstein 1996 anytime framing: cap head-only Cartesian expansion."""

    rule = parse_defeasible_rule(
        Rule(id="p1", head="p(X, Y)", body=[]),
        kind="defeasible",
    )
    model = {
        "constant": IndexedRelation((f"c{i}",) for i in range(33)),
    }

    result = _head_only_bindings(rule, model, max_candidates=1_000)

    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1_000
    assert result.remainder_provenance == "vacuous"
