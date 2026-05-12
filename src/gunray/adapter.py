"""Single-object dispatcher over Gunray-owned input types."""

from __future__ import annotations

from typing import cast, overload

from .closure import ClosureEvaluator
from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator
from .schema import (
    ClosurePolicy,
    DefeasibleModel,
    DefeasibleTheory,
    GroundingMode,
    MarkingPolicy,
    Model,
    NegationSemantics,
    ProjectionSemantics,
    Program,
)
from .trace import DatalogTrace, DefeasibleTrace, TraceConfig


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

            self._bridge = GunrayConformanceEvaluator(core=self)
        return self._bridge

    @overload
    def evaluate(
        self,
        item: Program,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> Model: ...

    @overload
    def evaluate(
        self,
        item: DefeasibleTheory,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> DefeasibleModel: ...

    def evaluate(
        self,
        item: Program | DefeasibleTheory,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> Model | DefeasibleModel:
        if isinstance(item, Program):
            return self._datalog.evaluate(item, negation_semantics=negation_semantics)
        if isinstance(item, DefeasibleTheory):
            if closure_policy is not None:
                if grounding_mode is not GroundingMode.DIRECT:
                    raise ValueError("grounding_mode applies only to dialectical-tree evaluation")
                if projection_semantics is not ProjectionSemantics.GARCIA:
                    raise ValueError("projection_semantics applies only to defeasible projection")
                return self._closure.evaluate(item, closure_policy)
            return self._defeasible.evaluate(
                item,
                marking_policy=marking_policy,
                closure_policy=closure_policy,
                grounding_mode=grounding_mode,
                negation_semantics=negation_semantics,
                projection_semantics=projection_semantics,
                max_arguments=max_arguments,
            )
        return cast(Model | DefeasibleModel, self._suite_bridge().evaluate(item, None))  # type: ignore[attr-defined]

    @overload
    def evaluate_with_trace(
        self,
        item: Program,
        trace_config: TraceConfig | None = None,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> tuple[Model, DatalogTrace]: ...

    @overload
    def evaluate_with_trace(
        self,
        item: DefeasibleTheory,
        trace_config: TraceConfig | None = None,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]: ...

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory,
        trace_config: TraceConfig | None = None,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> tuple[Model | DefeasibleModel, DatalogTrace | DefeasibleTrace]:
        if isinstance(item, Program):
            return self._datalog.evaluate_with_trace(
                item,
                trace_config,
                negation_semantics=negation_semantics,
            )
        if isinstance(item, DefeasibleTheory):
            if closure_policy is not None:
                if grounding_mode is not GroundingMode.DIRECT:
                    raise ValueError("grounding_mode applies only to dialectical-tree evaluation")
                if projection_semantics is not ProjectionSemantics.GARCIA:
                    raise ValueError("projection_semantics applies only to defeasible projection")
                return self._closure.evaluate_with_trace(item, closure_policy, trace_config)
            return self._defeasible.evaluate_with_trace(
                item,
                trace_config,
                marking_policy=marking_policy,
                closure_policy=closure_policy,
                grounding_mode=grounding_mode,
                negation_semantics=negation_semantics,
                projection_semantics=projection_semantics,
                max_arguments=max_arguments,
            )
        return cast(
            tuple[Model | DefeasibleModel, DatalogTrace | DefeasibleTrace],
            self._suite_bridge().evaluate_with_trace(item, None, trace_config),  # type: ignore[attr-defined]
        )

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory,
        property_name: str,
        policy: ClosurePolicy,
    ) -> bool:
        if isinstance(theory, DefeasibleTheory):
            return self._closure.satisfies_klm_property(theory, property_name, policy)
        return self._suite_bridge().satisfies_klm_property(theory, property_name, policy)  # type: ignore[attr-defined]
