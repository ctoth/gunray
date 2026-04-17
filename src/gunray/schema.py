"""Public Gunray-owned schema and model types."""

# Policy.PROPAGATING was deprecated in Block 2 — see
# notes/policy_propagating_fate.md. Antoniou 2007 §3.5 is not in this
# refactor's source-of-truth paper set (Garcia & Simari 2004,
# Simari & Loui 1992). The ambiguity-blocking vs ambiguity-propagating
# distinction comes from Antoniou's DR-Prolog meta-program (c7 vs
# c7') and has no seam in the Garcia 04 dialectical-tree pipeline
# gunray implements.

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
    """Named evaluation policies supported by Gunray.

    Post-Block-2, ``BLOCKING`` is the only supported value for the
    dialectical-tree defeasible path (Garcia & Simari 2004 Def 5.1 +
    Def 4.7 acceptable argumentation lines). Argument preference is
    resolved via ``preference.GeneralizedSpecificity`` (Simari & Loui
    1992 Lemma 2.4). ``PROPAGATING`` was deprecated — see
    ``notes/policy_propagating_fate.md`` for the decision and the
    re-introduction path if a future consumer needs Antoniou 2007
    §3.5 ambiguity-propagating semantics.

    The three closure values — ``RATIONAL_CLOSURE``,
    ``LEXICOGRAPHIC_CLOSURE``, ``RELEVANT_CLOSURE`` — route into
    ``closure.ClosureEvaluator`` instead of the dialectical-tree
    path and are unrelated to the BLOCKING/PROPAGATING distinction.
    """

    BLOCKING = "blocking"
    RATIONAL_CLOSURE = "rational_closure"
    LEXICOGRAPHIC_CLOSURE = "lexicographic_closure"
    RELEVANT_CLOSURE = "relevant_closure"


class NegationSemantics(str, Enum):
    """Semantics for variables that appear only in negated body literals."""

    SAFE = "safe"
    NEMO = "nemo"


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
