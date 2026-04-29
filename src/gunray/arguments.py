"""Argument structures: Garcia & Simari 2004 Def 3.1, Simari & Loui 1992 Def 2.2.

Garcia & Simari 2004 Def 3.1: An argument structure ``<A, h>`` for a
literal ``h`` from a de.l.p. ``P = (Pi, Delta)`` is a pair where
``A`` is a subset of ``Delta`` such that

    1. ``h`` has a defeasible derivation from ``Pi union A``,
    2. ``Pi union A`` is non-contradictory,
    3. ``A`` is minimal: no proper subset of ``A`` satisfies (1) and (2).

Simari & Loui 1992 Def 2.2 gives the same pair with slightly
different wording, based on "activation" of a rule set.

This module defines both the value type (``Argument``) and the naive
enumeration ``build_arguments`` that produces all argument structures
for a theory by brute-force subset enumeration. Efficiency is a
Block 2+ concern.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .anytime import EnumerationExceeded
from ._internal import _force_strict_for_closure, _ground_theory
from .disagreement import has_contradiction, strict_closure
from .errors import ContradictoryStrictTheoryError
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import GroundAtom, GroundDefeasibleRule


@dataclass(frozen=True, slots=True)
class Argument:
    """A pair ``<A, h>``.

    Garcia & Simari 2004 Def 3.1: an argument structure for a literal
    ``h`` from a de.l.p. ``P = (Pi, Delta)`` is a pair ``<A, h>`` with
    ``A`` a subset of ``Delta`` such that (1) ``h`` has a defeasible
    derivation from ``Pi | A``, (2) ``Pi | A`` is non-contradictory,
    and (3) ``A`` is minimal. This dataclass carries the pair;
    conditions (1)-(3) are enforced by ``build_arguments`` (B1.3).
    """

    rules: frozenset[GroundDefeasibleRule]
    conclusion: GroundAtom


def is_subargument(a: Argument, b: Argument) -> bool:
    """Return True iff ``a``'s rule set is a subset of ``b``'s.

    Garcia & Simari 2004 Fig 1 (nested triangles) — a sub-argument of
    ``<A, h>`` is an argument ``<A', h'>`` with ``A'`` a subset of
    ``A``. This is a reflexive partial order on ``Argument`` values
    keyed by ``rules``.
    """

    return a.rules <= b.rules


def build_arguments(
    theory: SchemaDefeasibleTheory,
    *,
    max_arguments: int | None = None,
) -> frozenset[Argument]:
    """Enumerate all argument structures for ``theory``.

    Implements Garcia & Simari 2004 Def 3.1 / Simari & Loui 1992
    Def 2.2 by naive subset enumeration. For every subset ``A`` of
    the grounded defeasible rule base we check conditions (1)-(3):

    1. Some literal ``h`` is defeasibly derivable from ``Pi union A``.
    2. ``Pi union A`` is non-contradictory (closure has no
       complementary pair).
    3. No proper subset ``A' subset A`` also derives ``h`` under
       conditions (1)-(2).

    The strict-only conclusions (those derivable from ``Pi`` alone)
    are represented by ``Argument(frozenset(), h)``. Defeater rules
    (``kind == "defeater"``) are carried as premises but are never
    the head of a constructed argument — Garcia 04 Def 3.6 treats
    them as defeaters only.
    """

    grounded = _ground_theory(theory)
    grounded_strict_rules = grounded.grounded_strict_rules
    grounded_defeasible_rules = grounded.grounded_defeasible_rules
    grounded_defeater_rules = grounded.grounded_defeater_rules
    fact_atoms = grounded.fact_atoms
    conflicts = grounded.conflicts
    if max_arguments is not None and max_arguments < 0:
        raise ValueError("max_arguments must be non-negative")

    # Pi = strict facts, closed under ground strict rules.
    pi_closure = strict_closure(fact_atoms, grounded_strict_rules)
    if has_contradiction(pi_closure, conflicts=conflicts):
        raise ContradictoryStrictTheoryError("Pi is contradictory under strict rules and facts")

    arguments: set[Argument] = set()

    # Every atom in the strict-only closure is a trivial argument
    # <empty, h>. Garcia 04 Def 3.1 condition (1) permits the
    # degenerate case where h has a strict derivation.
    for atom in pi_closure:
        _add_argument_with_budget(
            arguments,
            Argument(rules=frozenset(), conclusion=atom),
            max_arguments,
        )

    # Nute-style defeater participation (see
    # ``notes/b2_defeater_participation.md``). Garcia & Simari 2004
    # defines only strict and defeasible rules; gunray's third
    # ``kind="defeater"`` category is imported from the DePYsible /
    # Spindle lineage and follows the standard Nute / Antoniou reading:
    # a ground defeater ``d`` whose body has a strict derivation from
    # ``Pi`` produces a one-rule argument ``<{d}, head(d)>`` that
    # participates in the dialectical tree as an attacker but is
    # filtered out by ``dialectic._is_warranted`` so it never warrants
    # a YES/NO answer to a query.
    for rule in grounded_defeater_rules:
        if not all(atom in pi_closure for atom in rule.body):
            continue
        # Non-contradiction guard (Def 3.1 cond 2 analogue): rejecting
        # ``{d}`` if ``Pi union {d}`` would be contradictory.
        combined = grounded_strict_rules + (_force_strict_for_closure(rule),)
        if has_contradiction(strict_closure(fact_atoms, combined), conflicts=conflicts):
            continue
        _add_argument_with_budget(
            arguments,
            Argument(rules=frozenset({rule}), conclusion=rule.head),
            max_arguments,
        )

    # Bottom-up minimal argument construction. The first implementation
    # enumerated every subset of the grounded defeasible rule base; a
    # 20-rule chain therefore forced 2**20 closure checks before it could
    # discover the obvious single chain of arguments. Def 3.1 only needs
    # minimal rule sets that actually derive each rule body, so we build
    # those directly and prune supersets per conclusion as soon as a
    # smaller derivation is known.
    supports_for_conclusion: dict[GroundAtom, set[frozenset[GroundDefeasibleRule]]] = {
        atom: {frozenset()} for atom in pi_closure
    }
    minimal_for_conclusion: dict[GroundAtom, set[frozenset[GroundDefeasibleRule]]] = {}
    changed = True
    while changed:
        changed = False
        for rule in grounded_defeasible_rules:
            body_rule_sets = tuple(supports_for_conclusion.get(atom) for atom in rule.body)
            if any(rule_sets is None for rule_sets in body_rule_sets):
                continue
            for supports in product(*(rule_sets or {frozenset()} for rule_sets in body_rule_sets)):
                rule_set = frozenset({rule}).union(*supports)
                if _has_redundant_nonempty_subset(
                    rule_set,
                    rule.head,
                    fact_atoms,
                    grounded_strict_rules,
                    conflicts,
                ):
                    continue
                combined_rules = grounded_strict_rules + tuple(
                    _force_strict_for_closure(r) for r in rule_set
                )
                if has_contradiction(strict_closure(fact_atoms, combined_rules), conflicts=conflicts):
                    continue
                if _add_minimal_argument(
                    arguments,
                    minimal_for_conclusion,
                    supports_for_conclusion,
                    rule.head,
                    rule_set,
                    max_arguments,
                ):
                    changed = True

    return frozenset(arguments)


def _add_minimal_argument(
    arguments: set[Argument],
    minimal_for_conclusion: dict[GroundAtom, set[frozenset[GroundDefeasibleRule]]],
    supports_for_conclusion: dict[GroundAtom, set[frozenset[GroundDefeasibleRule]]],
    conclusion: GroundAtom,
    rule_set: frozenset[GroundDefeasibleRule],
    max_arguments: int | None,
) -> bool:
    existing_sets = minimal_for_conclusion.setdefault(conclusion, set())
    if any(existing <= rule_set for existing in existing_sets):
        return False

    supersets = {existing for existing in existing_sets if rule_set < existing}
    for existing in supersets:
        existing_sets.remove(existing)
        supports_for_conclusion[conclusion].remove(existing)
        arguments.discard(Argument(rules=existing, conclusion=conclusion))

    _raise_if_budget_exceeded(arguments, max_arguments)
    existing_sets.add(rule_set)
    supports_for_conclusion.setdefault(conclusion, set()).add(rule_set)
    arguments.add(Argument(rules=rule_set, conclusion=conclusion))
    return True


def _has_redundant_nonempty_subset(
    rule_set: frozenset[GroundDefeasibleRule],
    conclusion: GroundAtom,
    fact_atoms: frozenset[GroundAtom],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    for rule in rule_set:
        reduced = rule_set - {rule}
        if not reduced:
            continue
        combined_rules = grounded_strict_rules + tuple(
            _force_strict_for_closure(candidate) for candidate in reduced
        )
        closure = strict_closure(fact_atoms, combined_rules)
        if conclusion in closure and not has_contradiction(closure, conflicts=conflicts):
            return True
    return False


def _add_argument_with_budget(
    arguments: set[Argument],
    argument: Argument,
    max_arguments: int | None,
) -> None:
    if argument in arguments:
        return
    _raise_if_budget_exceeded(arguments, max_arguments)
    arguments.add(argument)


def _raise_if_budget_exceeded(
    arguments: set[Argument],
    max_arguments: int | None,
) -> None:
    if max_arguments is not None and len(arguments) >= max_arguments:
        raise EnumerationExceeded(
            partial_arguments=tuple(arguments),
            max_arguments=max_arguments,
        )
