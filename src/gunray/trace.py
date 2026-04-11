"""Structured execution traces for Gunray evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import GroundAtom


@dataclass(slots=True)
class RuleFireTrace:
    rule_text: str
    delta_position: int | None
    derived_count: int


@dataclass(slots=True)
class IterationTrace:
    iteration: int
    delta_sizes: dict[str, int]
    rule_fires: list[RuleFireTrace] = field(default_factory=list)


@dataclass(slots=True)
class StratumTrace:
    predicates: tuple[str, ...]
    iterations: list[IterationTrace] = field(default_factory=list)


@dataclass(slots=True)
class DatalogTrace:
    strata: list[StratumTrace] = field(default_factory=list)


@dataclass(slots=True)
class ProofAttemptTrace:
    atom: GroundAtom
    result: str
    reason: str
    supporter_rule_ids: tuple[str, ...] = ()
    attacker_rule_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class ClassificationTrace:
    atom: GroundAtom
    result: str
    reason: str


@dataclass(slots=True)
class DefeasibleTrace:
    definitely: tuple[GroundAtom, ...] = ()
    supported: tuple[GroundAtom, ...] = ()
    proof_attempts: list[ProofAttemptTrace] = field(default_factory=list)
    classifications: list[ClassificationTrace] = field(default_factory=list)
