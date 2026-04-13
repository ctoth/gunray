"""Public Gunray-owned schema and model types."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

Scalar: TypeAlias = str | int | float | bool
FactTuple: TypeAlias = tuple[Scalar, ...]
PredicateFacts: TypeAlias = Mapping[str, Iterable[FactTuple]]
ModelFacts: TypeAlias = Mapping[str, set[FactTuple]]
DefeasibleSections: TypeAlias = Mapping[str, ModelFacts]


def _predicate_facts_factory() -> PredicateFacts:
    return {}


def _string_list_factory() -> list[str]:
    return []


def _rule_list_factory() -> list["Rule"]:
    return []


def _pair_list_factory() -> list[tuple[str, str]]:
    return []


class Policy(str, Enum):
    """Named evaluation policies supported by Gunray."""

    BLOCKING = "blocking"
    PROPAGATING = "propagating"
    RATIONAL_CLOSURE = "rational_closure"
    LEXICOGRAPHIC_CLOSURE = "lexicographic_closure"
    RELEVANT_CLOSURE = "relevant_closure"


@dataclass(slots=True)
class Program:
    """Core Datalog program."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    rules: list[str] = field(default_factory=_string_list_factory)


@dataclass(slots=True)
class Rule:
    """Shared rule structure for strict, defeasible, and defeater rules."""

    id: str
    head: str
    body: list[str] = field(default_factory=_string_list_factory)


@dataclass(slots=True)
class DefeasibleTheory:
    """Defeasible Datalog theory."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    strict_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeasible_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeaters: list[Rule] = field(default_factory=_rule_list_factory)
    superiority: list[tuple[str, str]] = field(default_factory=_pair_list_factory)
    conflicts: list[tuple[str, str]] = field(default_factory=_pair_list_factory)


@dataclass(slots=True)
class Model:
    """Standard Datalog model returned by evaluators."""

    facts: ModelFacts


@dataclass(slots=True)
class DefeasibleModel:
    """Defeasible model returned by evaluators."""

    sections: DefeasibleSections
