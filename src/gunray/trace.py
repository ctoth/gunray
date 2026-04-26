"""Structured execution traces for Gunray evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from .types import GroundAtom, Scalar

if TYPE_CHECKING:
    from .arguments import Argument
    from .dialectic import DialecticalNode


def _rule_fire_trace_list_factory() -> list["RuleFireTrace"]:
    return []


def _iteration_trace_list_factory() -> list["IterationTrace"]:
    return []


def _stratum_trace_list_factory() -> list["StratumTrace"]:
    return []


def _tree_dict_factory() -> dict[GroundAtom, "DialecticalNode"]:
    return {}


def _marking_dict_factory() -> dict[GroundAtom, Literal["U", "D"]]:
    return {}


@dataclass(frozen=True, slots=True)
class TraceConfig:
    capture_derived_rows: bool = False
    max_derived_rows_per_rule_fire: int = 10


@dataclass(slots=True)
class RuleFireTrace:
    rule_text: str
    head_predicate: str
    delta_position: int | None
    derived_count: int
    derived_rows: tuple[tuple[object, ...], ...] = ()


@dataclass(slots=True)
class IterationTrace:
    iteration: int
    delta_sizes: dict[str, int]
    rule_fires: list[RuleFireTrace] = field(default_factory=_rule_fire_trace_list_factory)

    def find_rule_fires(
        self,
        *,
        rule_text: str | None = None,
        head_predicate: str | None = None,
        derived_count_at_least: int | None = None,
    ) -> tuple[RuleFireTrace, ...]:
        return tuple(
            fire
            for fire in self.rule_fires
            if _matches_rule_fire(
                fire,
                rule_text=rule_text,
                head_predicate=head_predicate,
                derived_count_at_least=derived_count_at_least,
            )
        )


@dataclass(slots=True)
class StratumTrace:
    predicates: tuple[str, ...]
    iterations: list[IterationTrace] = field(default_factory=_iteration_trace_list_factory)

    def find_rule_fires(
        self,
        *,
        rule_text: str | None = None,
        head_predicate: str | None = None,
        derived_count_at_least: int | None = None,
    ) -> tuple[RuleFireTrace, ...]:
        matches: list[RuleFireTrace] = []
        for iteration in self.iterations:
            matches.extend(
                iteration.find_rule_fires(
                    rule_text=rule_text,
                    head_predicate=head_predicate,
                    derived_count_at_least=derived_count_at_least,
                )
            )
        return tuple(matches)


@dataclass(slots=True)
class DatalogTrace:
    config: TraceConfig = field(default_factory=TraceConfig)
    strata: list[StratumTrace] = field(default_factory=_stratum_trace_list_factory)

    def all_rule_fires(self) -> tuple[RuleFireTrace, ...]:
        matches: list[RuleFireTrace] = []
        for stratum in self.strata:
            matches.extend(stratum.find_rule_fires())
        return tuple(matches)

    def find_rule_fires(
        self,
        *,
        rule_text: str | None = None,
        head_predicate: str | None = None,
        derived_count_at_least: int | None = None,
    ) -> tuple[RuleFireTrace, ...]:
        matches: list[RuleFireTrace] = []
        for stratum in self.strata:
            matches.extend(
                stratum.find_rule_fires(
                    rule_text=rule_text,
                    head_predicate=head_predicate,
                    derived_count_at_least=derived_count_at_least,
                )
            )
        return tuple(matches)


@dataclass(slots=True)
class DefeasibleTrace:
    config: TraceConfig = field(default_factory=TraceConfig)
    definitely: tuple[GroundAtom, ...] = ()
    supported: tuple[GroundAtom, ...] = ()
    strict_trace: DatalogTrace | None = None
    arguments: tuple["Argument", ...] = ()
    trees: dict[GroundAtom, "DialecticalNode"] = field(default_factory=_tree_dict_factory)
    markings: dict[GroundAtom, Literal["U", "D"]] = field(default_factory=_marking_dict_factory)

    def tree_for(self, atom: GroundAtom) -> "DialecticalNode | None":
        return self.trees.get(atom)

    def tree_for_parts(
        self,
        predicate: str,
        arguments: tuple[Scalar, ...] = (),
    ) -> "DialecticalNode | None":
        return self.tree_for(GroundAtom(predicate=predicate, arguments=arguments))

    def marking_for(self, atom: GroundAtom) -> Literal["U", "D"] | None:
        return self.markings.get(atom)

    def marking_for_parts(
        self,
        predicate: str,
        arguments: tuple[Scalar, ...] = (),
    ) -> Literal["U", "D"] | None:
        return self.marking_for(GroundAtom(predicate=predicate, arguments=arguments))

    def arguments_for_conclusion(self, atom: GroundAtom) -> tuple["Argument", ...]:
        return tuple(argument for argument in self.arguments if argument.conclusion == atom)

    def arguments_for_conclusion_parts(
        self,
        predicate: str,
        arguments: tuple[Scalar, ...] = (),
    ) -> tuple["Argument", ...]:
        return self.arguments_for_conclusion(GroundAtom(predicate=predicate, arguments=arguments))


def _matches_rule_fire(
    fire: RuleFireTrace,
    *,
    rule_text: str | None,
    head_predicate: str | None,
    derived_count_at_least: int | None,
) -> bool:
    if rule_text is not None and fire.rule_text != rule_text:
        return False
    if head_predicate is not None and fire.head_predicate != head_predicate:
        return False
    if derived_count_at_least is not None and fire.derived_count < derived_count_at_least:
        return False
    return True
