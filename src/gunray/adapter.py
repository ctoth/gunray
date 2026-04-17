"""Single-object dispatcher over Gunray-owned input types."""

from __future__ import annotations

from .closure import ClosureEvaluator
from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleTheory, NegationSemantics, Policy, Program
from .trace import TraceConfig


class GunrayEvaluator:
    """Dispatch Gunray inputs to the right engine."""

    def __init__(self) -> None:
        self._datalog = SemiNaiveEvaluator()
        self._defeasible = DefeasibleEvaluator()
        self._closure = ClosureEvaluator()
        self._bridge: object | None = None

    def _suite_bridge(self) -> object:
        if self._bridge is None:
            from .conformance_adapter import GunrayConformanceEvaluator

            bridge = GunrayConformanceEvaluator()
            bridge._core = self  # reuse this evaluator's engines
            self._bridge = bridge
        return self._bridge

    def evaluate(
        self,
        item: Program | DefeasibleTheory,
        policy: Policy | None = None,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> object:
        if isinstance(item, Program):
            return self._datalog.evaluate(item, negation_semantics=negation_semantics)
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            if actual_policy in {
                Policy.RATIONAL_CLOSURE,
                Policy.LEXICOGRAPHIC_CLOSURE,
                Policy.RELEVANT_CLOSURE,
            }:
                return self._closure.evaluate(item, actual_policy)
            return self._defeasible.evaluate(
                item,
                actual_policy,
                negation_semantics=negation_semantics,
            )
        return self._suite_bridge().evaluate(item, policy)  # type: ignore[attr-defined]

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory,
        policy: Policy | None = None,
        trace_config: TraceConfig | None = None,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> tuple[object, object]:
        if isinstance(item, Program):
            return self._datalog.evaluate_with_trace(
                item,
                trace_config,
                negation_semantics=negation_semantics,
            )
        if isinstance(item, DefeasibleTheory):
            actual_policy = policy if policy is not None else Policy.BLOCKING
            if actual_policy in {
                Policy.RATIONAL_CLOSURE,
                Policy.LEXICOGRAPHIC_CLOSURE,
                Policy.RELEVANT_CLOSURE,
            }:
                return self._closure.evaluate_with_trace(item, actual_policy, trace_config)
            return self._defeasible.evaluate_with_trace(
                item,
                actual_policy,
                trace_config,
                negation_semantics=negation_semantics,
            )
        return self._suite_bridge().evaluate_with_trace(item, policy, trace_config)  # type: ignore[attr-defined]

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory,
        property_name: str,
        policy: Policy,
    ) -> bool:
        if isinstance(theory, DefeasibleTheory):
            return self._closure.satisfies_klm_property(theory, property_name, policy)
        return self._suite_bridge().satisfies_klm_property(theory, property_name, policy)  # type: ignore[attr-defined]
