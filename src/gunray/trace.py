"""Structured execution traces for Gunray evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import GroundAtom


def _rule_fire_trace_list_factory() -> list["RuleFireTrace"]:
    return []


def _iteration_trace_list_factory() -> list["IterationTrace"]:
    return []


def _stratum_trace_list_factory() -> list["StratumTrace"]:
    return []


def _proof_attempt_trace_list_factory() -> list["ProofAttemptTrace"]:
    return []


def _classification_trace_list_factory() -> list["ClassificationTrace"]:
    return []


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
class ProofAttemptTrace:
    atom: GroundAtom
    result: str
    reason: str
    supporter_rule_ids: tuple[str, ...] = ()
    attacker_rule_ids: tuple[str, ...] = ()
    opposing_atoms: tuple[GroundAtom, ...] = ()


@dataclass(slots=True)
class ClassificationTrace:
    atom: GroundAtom
    result: str
    reason: str
    supporter_rule_ids: tuple[str, ...] = ()
    attacker_rule_ids: tuple[str, ...] = ()
    opposing_atoms: tuple[GroundAtom, ...] = ()


@dataclass(slots=True)
class DefeasibleTrace:
    config: TraceConfig = field(default_factory=TraceConfig)
    definitely: tuple[GroundAtom, ...] = ()
    supported: tuple[GroundAtom, ...] = ()
    strict_trace: DatalogTrace | None = None
    proof_attempts: list[ProofAttemptTrace] = field(
        default_factory=_proof_attempt_trace_list_factory
    )
    classifications: list[ClassificationTrace] = field(
        default_factory=_classification_trace_list_factory
    )

    def proof_attempts_for(
        self,
        atom: GroundAtom,
        *,
        result: str | None = None,
        reason: str | None = None,
    ) -> tuple[ProofAttemptTrace, ...]:
        return tuple(
            attempt
            for attempt in self.proof_attempts
            if _matches_atom_entry(attempt, atom=atom, result=result, reason=reason)
        )

    def classifications_for(
        self,
        atom: GroundAtom,
        *,
        result: str | None = None,
        reason: str | None = None,
    ) -> tuple[ClassificationTrace, ...]:
        return tuple(
            classification
            for classification in self.classifications
            if _matches_atom_entry(
                classification,
                atom=atom,
                result=result,
                reason=reason,
            )
        )


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


def _matches_atom_entry(
    entry: ProofAttemptTrace | ClassificationTrace,
    *,
    atom: GroundAtom,
    result: str | None,
    reason: str | None,
) -> bool:
    if entry.atom != atom:
        return False
    if result is not None and entry.result != result:
        return False
    if reason is not None and entry.reason != reason:
        return False
    return True
