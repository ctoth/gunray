"""Single-object protocol adapter for the conformance suite."""

from __future__ import annotations

from datalog_conformance.schema import DefeasibleTheory, Policy, Program

from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator


class GunrayEvaluator:
    """Dispatch conformance-suite inputs to the right engine."""

    def __init__(self) -> None:
        self._datalog = SemiNaiveEvaluator()
        self._defeasible = DefeasibleEvaluator()

    def evaluate(self, item: Program | DefeasibleTheory, policy: Policy | None = None) -> object:
        if isinstance(item, Program):
            return self._datalog.evaluate(item)
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            return self._defeasible.evaluate(item, actual_policy)
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory,
        policy: Policy | None = None,
    ) -> tuple[object, object]:
        if isinstance(item, Program):
            return self._datalog.evaluate_with_trace(item)
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            return self._defeasible.evaluate_with_trace(item, actual_policy)
        raise TypeError(f"Unsupported input type: {type(item).__name__}")
