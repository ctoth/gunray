from __future__ import annotations

from gunray import DefeasibleEvaluator, DefeasibleTheory, GroundingInspection, MarkingPolicy, Rule
from gunray.grounding import inspect_grounding


def test_evaluate_with_trace_carries_grounding_inspection() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("opus",)}},
        strict_rules=[Rule(id="s1", head="animal(X)", body=("bird(X)",))],
        defeasible_rules=[Rule(id="r1", head="flies(X)", body=("bird(X)",))],
    )

    _model, trace = DefeasibleEvaluator().evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert isinstance(trace.grounding_inspection, GroundingInspection)
    assert trace.grounding_inspection == inspect_grounding(theory)
