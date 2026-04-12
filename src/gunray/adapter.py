"""Single-object dispatcher over Gunray-owned input types."""

from __future__ import annotations

from .closure import ClosureEvaluator
from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleTheory, Policy, Program
from .trace import TraceConfig


class GunrayEvaluator:
    """Dispatch Gunray inputs to the right engine."""

    def __init__(self) -> None:
        self._datalog = SemiNaiveEvaluator()
        self._defeasible = DefeasibleEvaluator()
        self._closure = ClosureEvaluator()

    def evaluate(self, item: Program | DefeasibleTheory, policy: Policy | None = None) -> object:
        if isinstance(item, Program):
            return self._datalog.evaluate(item)
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            if actual_policy in {
                Policy.RATIONAL_CLOSURE,
                Policy.LEXICOGRAPHIC_CLOSURE,
                Policy.RELEVANT_CLOSURE,
            }:
                return self._closure.evaluate(item, actual_policy)
            return self._defeasible.evaluate(item, actual_policy)
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory,
        policy: Policy | None = None,
        trace_config: TraceConfig | None = None,
    ) -> tuple[object, object]:
        if isinstance(item, Program):
            return self._datalog.evaluate_with_trace(item, trace_config)
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            if actual_policy in {
                Policy.RATIONAL_CLOSURE,
                Policy.LEXICOGRAPHIC_CLOSURE,
                Policy.RELEVANT_CLOSURE,
            }:
                return self._closure.evaluate_with_trace(item, actual_policy, trace_config)
            return self._defeasible.evaluate_with_trace(item, actual_policy, trace_config)
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory,
        property_name: str,
        policy: Policy,
    ) -> bool:
        return self._closure.satisfies_klm_property(theory, property_name, policy)
