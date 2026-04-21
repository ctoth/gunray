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

from gunray.errors import DuplicateRuleId

Scalar: TypeAlias = str | int | float | bool
FactTuple: TypeAlias = tuple[Scalar, ...]
PredicateFacts: TypeAlias = Mapping[str, Iterable[FactTuple]]
ModelFacts: TypeAlias = Mapping[str, set[FactTuple]]
DefeasibleSections: TypeAlias = Mapping[str, ModelFacts]


def _predicate_facts_factory() -> PredicateFacts:
    return {}


def _string_list_factory() -> list[str]:
    return []


def _rule_tuple_factory() -> tuple["Rule", ...]:
    return ()


def _pair_tuple_factory() -> tuple[tuple[str, str], ...]:
    return ()


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
    """Semantics for variables that appear only in negated body literals.

    ``SAFE`` is the standard stratified-Datalog safety requirement from
    Apt, Blair, and Walker 1988: every variable in a negated literal must
    be bound by a positive body literal. ``NEMO`` is Gunray's compatibility
    mode for the conformance suite's Nemo fixtures, which read such
    variables over the active Herbrand universe. The Nemo system/language
    citation is Ivliev, Gerlach, Meusel, Steinberg, and Kroetzsch 2024,
    "Nemo: Your Friendly and Versatile Rule Reasoning Toolkit", KR 2024,
    pp. 743-754, doi:10.24963/kr.2024/70.
    """

    SAFE = "safe"
    NEMO = "nemo"


@dataclass(frozen=True, slots=True)
class Program:
    """Core Datalog program."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    rules: list[str] = field(default_factory=_string_list_factory)


@dataclass(frozen=True, slots=True)
class Rule:
    """Shared rule structure for strict, defeasible, and defeater rules."""

    id: str
    head: str
    body: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "body", tuple(self.body))
        if not self.id:
            raise ValueError("Rule.id must be non-empty")
        if not self.head:
            raise ValueError(f"Rule.head must be non-empty (rule id={self.id!r})")


@dataclass(frozen=True, slots=True)
class DefeasibleTheory:
    """Defeasible Datalog theory.

    ``presumptions`` carries defeasible rules with empty body written
    ``h -< true`` in DeLP surface syntax. Garcia & Simari 2004 §6.2
    p. 32 defines a presumption as a defeasible rule whose body is
    empty; presumptions are a special case of defeasible rules and
    flow through the argument pipeline with ``kind="defeasible"``.
    Every ``Rule`` in ``presumptions`` must have an empty ``body``;
    ``__post_init__`` raises ``ValueError`` otherwise.
    """

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    strict_rules: tuple[Rule, ...] = field(default_factory=_rule_tuple_factory)
    defeasible_rules: tuple[Rule, ...] = field(default_factory=_rule_tuple_factory)
    defeaters: tuple[Rule, ...] = field(default_factory=_rule_tuple_factory)
    presumptions: tuple[Rule, ...] = field(default_factory=_rule_tuple_factory)
    superiority: tuple[tuple[str, str], ...] = field(default_factory=_pair_tuple_factory)
    conflicts: tuple[tuple[str, str], ...] = field(default_factory=_pair_tuple_factory)

    def __post_init__(self) -> None:
        for field_name in (
            "strict_rules",
            "defeasible_rules",
            "defeaters",
            "presumptions",
            "superiority",
            "conflicts",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))

        for rule in self.presumptions:
            if rule.body:
                raise ValueError(
                    f"DefeasibleTheory.presumptions rule {rule.id!r} must have "
                    "empty body (Garcia & Simari 2004 §6.2 p. 32)"
                )

        known_ids: set[str] = set()
        seen_sections: dict[str, str] = {}
        for section_name, rules in (
            ("strict_rules", self.strict_rules),
            ("defeasible_rules", self.defeasible_rules),
            ("defeaters", self.defeaters),
            ("presumptions", self.presumptions),
        ):
            for rule in rules:
                if rule.id in seen_sections:
                    raise DuplicateRuleId(
                        f"duplicate rule id {rule.id!r} in "
                        f"{seen_sections[rule.id]} and {section_name}"
                    )
                seen_sections[rule.id] = section_name
                known_ids.add(rule.id)

        for left, right in self.superiority:
            for rule_id, side in ((left, "left"), (right, "right")):
                if rule_id not in known_ids:
                    raise ValueError(
                        f"DefeasibleTheory.superiority {side} id {rule_id!r} "
                        "is not defined in strict/defeasible/defeaters rules"
                    )


@dataclass(frozen=True, slots=True)
class Model:
    """Standard Datalog model returned by evaluators."""

    facts: ModelFacts


@dataclass(frozen=True, slots=True)
class DefeasibleModel:
    """Defeasible model returned by evaluators."""

    sections: DefeasibleSections
