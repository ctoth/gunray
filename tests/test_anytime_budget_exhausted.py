from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    EnumerationExceeded,
    MarkingPolicy,
    Rule,
    build_arguments,
)


def _budget_theory(width: int = 2) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"a": {()}},
        defeasible_rules=tuple(Rule(id=f"r{i}", head=f"p{i}", body=("a",)) for i in range(width)),
    )


def test_build_arguments_budget_exhaustion_carries_partial_arguments() -> None:
    with pytest.raises(EnumerationExceeded) as raised:
        build_arguments(_budget_theory(), max_arguments=1)

    assert len(raised.value.partial_arguments) == 1
    assert raised.value.partial_trace is None
    assert "argument enumeration budget exceeded" in raised.value.reason


def test_evaluate_with_trace_budget_exhaustion_carries_partial_trace() -> None:
    with pytest.raises(EnumerationExceeded) as raised:
        DefeasibleEvaluator().evaluate_with_trace(
            _budget_theory(),
            marking_policy=MarkingPolicy.BLOCKING,
            max_arguments=1,
        )

    assert raised.value.partial_trace is not None
    assert raised.value.partial_trace.arguments == raised.value.partial_arguments
    assert raised.value.partial_trace.grounding_inspection is not None


@pytest.mark.property
@given(limit=st.integers(min_value=1, max_value=4))
def test_argument_budget_monotone_until_success(limit: int) -> None:
    theory = _budget_theory(width=4)

    try:
        smaller = build_arguments(theory, max_arguments=limit)
    except EnumerationExceeded as smaller_exc:
        with pytest.raises(EnumerationExceeded) as larger_raised:
            build_arguments(theory, max_arguments=limit - 1)
        assert len(larger_raised.value.partial_arguments) <= len(smaller_exc.partial_arguments)
    else:
        larger = build_arguments(theory, max_arguments=limit + 1)
        assert smaller == larger
