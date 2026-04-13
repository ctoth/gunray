from __future__ import annotations

import pytest

from gunray import Program, SemiNaiveEvaluator
from gunray.errors import SafetyViolationError


def test_rejects_variable_that_appears_only_in_single_negated_literal() -> None:
    program = Program(
        facts={"person": {("alice",)}},
        rules=[
            "ok(X) :- person(X), not banned(X, Y).",
        ],
    )

    with pytest.raises(SafetyViolationError, match="negated literals"):
        SemiNaiveEvaluator().evaluate(program)
