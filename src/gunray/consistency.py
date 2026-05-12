"""Goldszmidt/Pearl p-consistency for small conditional databases.

This module is deliberately separate from ``DefeasibleEvaluator``. Goldszmidt
and Pearl 1992 study database coherence for strict and defeasible conditionals;
they do not define a replacement answer semantics for Garcia/Simari arguments.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


def _empty_antecedent_factory() -> tuple[str, ...]:
    return ()


def _conditional_tuple_factory() -> tuple["ConditionalSentence", ...]:
    return ()


@dataclass(frozen=True, slots=True)
class ConditionalSentence:
    """A propositional conditional sentence over zero-arity literals.

    ``antecedent`` is a conjunction of literals. ``consequent`` is a single
    literal. A literal may use Gunray's strong-negation spelling, for example
    ``"~flies"``.
    """

    id: str
    antecedent: tuple[str, ...] = field(default_factory=_empty_antecedent_factory)
    consequent: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "antecedent", tuple(self.antecedent))
        if not self.id:
            raise ValueError("ConditionalSentence.id must be non-empty")
        if not self.consequent:
            raise ValueError(f"ConditionalSentence.consequent must be non-empty ({self.id!r})")
        for literal in (*self.antecedent, self.consequent):
            _validate_literal(literal, self.id)


@dataclass(frozen=True, slots=True)
class ConditionalDatabase:
    """Mixed strict/defeasible conditional database."""

    strict_conditionals: tuple[ConditionalSentence, ...] = field(
        default_factory=_conditional_tuple_factory
    )
    defeasible_conditionals: tuple[ConditionalSentence, ...] = field(
        default_factory=_conditional_tuple_factory
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "strict_conditionals", tuple(self.strict_conditionals))
        object.__setattr__(self, "defeasible_conditionals", tuple(self.defeasible_conditionals))
        seen: set[str] = set()
        for sentence in (*self.strict_conditionals, *self.defeasible_conditionals):
            if sentence.id in seen:
                raise ValueError(f"duplicate conditional sentence id {sentence.id!r}")
            seen.add(sentence.id)


@dataclass(frozen=True, slots=True)
class ConsistencyReport:
    """Result of Goldszmidt/Pearl two-phase p-consistency analysis."""

    is_consistent: bool
    tolerated_layers: tuple[tuple[str, ...], ...]
    offending_sentence_ids: frozenset[str]


Assignment = dict[str, bool]


def analyze_p_consistency(database: ConditionalDatabase) -> ConsistencyReport:
    """Analyze p-consistency by Goldszmidt/Pearl's tolerance procedure.

    Page-image basis:
    ``papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-003.png``.
    First every strict sentence must be tolerated by the strict set. Then
    defeasible sentences are removed in tolerated layers until all are removed
    or the remaining defeasible set is the offending set.
    """

    strict = database.strict_conditionals
    strict_offenders = frozenset(
        sentence.id for sentence in strict if not _is_tolerated(sentence, strict)
    )
    if strict_offenders:
        return ConsistencyReport(
            is_consistent=False,
            tolerated_layers=(),
            offending_sentence_ids=strict_offenders,
        )

    remaining = list(database.defeasible_conditionals)
    tolerated_layers: list[tuple[str, ...]] = []
    while remaining:
        constraints = (*strict, *remaining)
        layer = tuple(sentence for sentence in remaining if _is_tolerated(sentence, constraints))
        if not layer:
            return ConsistencyReport(
                is_consistent=False,
                tolerated_layers=tuple(tolerated_layers),
                offending_sentence_ids=frozenset(sentence.id for sentence in remaining),
            )
        tolerated_layers.append(tuple(sentence.id for sentence in layer))
        layer_ids = {sentence.id for sentence in layer}
        remaining = [sentence for sentence in remaining if sentence.id not in layer_ids]

    return ConsistencyReport(
        is_consistent=True,
        tolerated_layers=tuple(tolerated_layers),
        offending_sentence_ids=frozenset(),
    )


def strictly_p_entails(
    database: ConditionalDatabase,
    sentence: ConditionalSentence,
) -> bool:
    """Return whether ``sentence`` is strictly p-entailed by the strict set.

    Goldszmidt/Pearl page 003 distinguishes strict p-entailment from classical
    material entailment: a vacuous material implication is not strictly
    p-entailed unless the queried conditional can itself be verified by a
    proper assignment over the strict database.
    """

    strict = database.strict_conditionals
    if any(not _is_tolerated(item, strict) for item in strict):
        return False
    return _materially_entails(strict, sentence) and _is_tolerated(sentence, strict)


def _is_tolerated(
    sentence: ConditionalSentence,
    constraints: Iterable[ConditionalSentence],
) -> bool:
    constraint_tuple = tuple(constraints)
    for assignment in _truth_assignments(_atoms((sentence, *constraint_tuple))):
        if not _verified(sentence, assignment):
            continue
        if all(_materially_satisfied(item, assignment) for item in constraint_tuple):
            return True
    return False


def _materially_entails(
    constraints: Iterable[ConditionalSentence],
    sentence: ConditionalSentence,
) -> bool:
    constraint_tuple = tuple(constraints)
    for assignment in _truth_assignments(_atoms((*constraint_tuple, sentence))):
        if not all(_materially_satisfied(item, assignment) for item in constraint_tuple):
            continue
        if not _materially_satisfied(sentence, assignment):
            return False
    return True


def _truth_assignments(atoms: tuple[str, ...]) -> Iterable[Assignment]:
    for mask in range(1 << len(atoms)):
        yield {atom: bool(mask & (1 << index)) for index, atom in enumerate(atoms)}


def _atoms(sentences: Iterable[ConditionalSentence]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _literal_atom(literal)
                for sentence in sentences
                for literal in (*sentence.antecedent, sentence.consequent)
            }
        )
    )


def _verified(sentence: ConditionalSentence, assignment: Assignment) -> bool:
    return all(_literal_value(item, assignment) for item in sentence.antecedent) and _literal_value(
        sentence.consequent,
        assignment,
    )


def _materially_satisfied(sentence: ConditionalSentence, assignment: Assignment) -> bool:
    return not all(
        _literal_value(item, assignment) for item in sentence.antecedent
    ) or _literal_value(
        sentence.consequent,
        assignment,
    )


def _literal_value(literal: str, assignment: Assignment) -> bool:
    atom = _literal_atom(literal)
    value = assignment[atom]
    if literal.startswith("~"):
        return not value
    return value


def _literal_atom(literal: str) -> str:
    return literal[1:] if literal.startswith("~") else literal


def _validate_literal(literal: str, sentence_id: str) -> None:
    atom = _literal_atom(literal)
    if not atom:
        raise ValueError(f"empty literal in conditional sentence {sentence_id!r}")
    if "(" in atom or ")" in atom:
        raise ValueError(
            "ConditionalSentence supports zero-arity propositional literals, "
            f"got {literal!r} in {sentence_id!r}"
        )
