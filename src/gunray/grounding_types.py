"""Public value types for Gunray grounding inspection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .types import GroundAtom, Scalar

GroundRuleKind = Literal["strict", "defeasible", "defeater"]
GroundingSubstitution = tuple[tuple[str, Scalar], ...]


@dataclass(frozen=True, slots=True)
class GroundRuleInstance:
    """A grounded rule instance and the source-level substitution that produced it."""

    rule_id: str
    kind: GroundRuleKind
    head: GroundAtom
    body: tuple[GroundAtom, ...]
    substitution: GroundingSubstitution
    default_negated_body: tuple[GroundAtom, ...] = ()


@dataclass(frozen=True, slots=True)
class GroundRuleResolution:
    """A strict ground rule resolved into the definite fact base."""

    rule: GroundRuleInstance
    produced_fact: GroundAtom


@dataclass(frozen=True, slots=True)
class GroundingSimplification:
    """Conservative Diller-style strict/fact grounding simplification report."""

    definite_fact_atoms: tuple[GroundAtom, ...]
    resolved_strict_rules: tuple[GroundRuleResolution, ...]
    strict_rules_for_argumentation: tuple[GroundRuleInstance, ...]
    defeasible_rules_for_argumentation: tuple[GroundRuleInstance, ...]
    defeater_rules_for_argumentation: tuple[GroundRuleInstance, ...]
    non_approximated_predicates: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ground_rules_for_argumentation(self) -> tuple[GroundRuleInstance, ...]:
        return (
            self.strict_rules_for_argumentation
            + self.defeasible_rules_for_argumentation
            + self.defeater_rules_for_argumentation
        )


@dataclass(frozen=True, slots=True)
class GroundingInspection:
    """Ground facts and rule instances grouped by Gunray rule kind."""

    fact_atoms: tuple[GroundAtom, ...]
    strict_rules: tuple[GroundRuleInstance, ...]
    defeasible_rules: tuple[GroundRuleInstance, ...]
    defeater_rules: tuple[GroundRuleInstance, ...]
    simplification: GroundingSimplification

    @property
    def all_rule_instances(self) -> tuple[GroundRuleInstance, ...]:
        return self.strict_rules + self.defeasible_rules + self.defeater_rules
