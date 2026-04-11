"""Internal immutable syntax and rule-model types for Gunray."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


Scalar: TypeAlias = str | int | float | bool
Binding: TypeAlias = dict[str, Scalar]


@dataclass(frozen=True, slots=True)
class Variable:
    name: str


@dataclass(frozen=True, slots=True)
class Wildcard:
    token: str


@dataclass(frozen=True, slots=True)
class Constant:
    value: Scalar


@dataclass(frozen=True, slots=True)
class AddExpression:
    left: "ValueTerm"
    right: "ValueTerm"


@dataclass(frozen=True, slots=True)
class SubtractExpression:
    left: "ValueTerm"
    right: "ValueTerm"


@dataclass(frozen=True, slots=True)
class Comparison:
    left: "ValueTerm"
    operator: str
    right: "ValueTerm"


PatternTerm: TypeAlias = Variable | Wildcard | Constant
ValueTerm: TypeAlias = Variable | Constant | AddExpression | SubtractExpression
AtomTerm: TypeAlias = PatternTerm | AddExpression | SubtractExpression


@dataclass(frozen=True, slots=True)
class Atom:
    predicate: str
    terms: tuple[AtomTerm, ...]

    @property
    def arity(self) -> int:
        return len(self.terms)


@dataclass(frozen=True, slots=True)
class Rule:
    heads: tuple[Atom, ...]
    positive_body: tuple[Atom, ...]
    negative_body: tuple[Atom, ...]
    constraints: tuple[Comparison, ...]
    source_text: str


@dataclass(frozen=True, slots=True)
class GroundAtom:
    predicate: str
    arguments: tuple[Scalar, ...]

    @property
    def arity(self) -> int:
        return len(self.arguments)


@dataclass(frozen=True, slots=True)
class DefeasibleRule:
    rule_id: str
    kind: str
    head: Atom
    body: tuple[Atom, ...]


@dataclass(frozen=True, slots=True)
class GroundDefeasibleRule:
    rule_id: str
    kind: str
    head: GroundAtom
    body: tuple[GroundAtom, ...]


def variables_in_term(term: AtomTerm) -> set[str]:
    """Return the bound variable names referenced by a term."""

    if isinstance(term, Variable):
        return {term.name}
    if isinstance(term, (AddExpression, SubtractExpression)):
        return variables_in_term(term.left) | variables_in_term(term.right)
    return set()
