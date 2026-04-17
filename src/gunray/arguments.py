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
from itertools import combinations

from ._internal import _force_strict_for_closure, _ground_theory
from .disagreement import complement, strict_closure
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


def build_arguments(theory: SchemaDefeasibleTheory) -> frozenset[Argument]:
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

    # Pi = strict facts, closed under ground strict rules.
    pi_closure = strict_closure(fact_atoms, grounded_strict_rules)
    if _has_contradiction(pi_closure):
        raise ContradictoryStrictTheoryError(
            "Pi is contradictory under strict rules and facts"
        )

    arguments: set[Argument] = set()

    # Every atom in the strict-only closure is a trivial argument
    # <empty, h>. Garcia 04 Def 3.1 condition (1) permits the
    # degenerate case where h has a strict derivation.
    for atom in pi_closure:
        arguments.add(Argument(rules=frozenset(), conclusion=atom))

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
        if _has_contradiction(strict_closure(fact_atoms, combined)):
            continue
        arguments.add(Argument(rules=frozenset({rule}), conclusion=rule.head))

    # Condition (2) needs to be checkable per subset. Compute it using
    # the ground strict rules + the ground rules in the subset (treating
    # defeasible rules like strict rules for the purpose of closure).
    minimal_for_conclusion: dict[GroundAtom, list[frozenset[GroundDefeasibleRule]]] = {}

    rule_universe = list(grounded_defeasible_rules)
    for size in range(0, len(rule_universe) + 1):
        for subset in combinations(rule_universe, size):
            rule_set = frozenset(subset)
            # Closure under Pi + A treats both strict and defeasible
            # rules in A as propagating heads — this is the "defeasible
            # derivation from Pi union A" of Def 3.1 condition (1).
            combined_rules = grounded_strict_rules + tuple(
                _force_strict_for_closure(r) for r in subset
            )
            closure = strict_closure(fact_atoms, combined_rules)

            # Condition (2): non-contradiction.
            if _has_contradiction(closure):
                continue

            # Condition (1): collect heads defeasibly derivable that
            # actually required `rule_set`. For size 0 we already
            # handled strict-only conclusions above.
            if not rule_set:
                continue

            for rule in subset:
                head = rule.head
                if head not in closure:
                    continue

                # Minimality (condition 3): reject if any proper
                # subset also produces this head under a
                # non-contradictory Pi union A'.
                prior = minimal_for_conclusion.get(head, [])
                if any(existing < rule_set for existing in prior):
                    continue

                # This rule_set derives `head` minimally so far. Drop
                # any previously stored supersets; add rule_set.
                survivors = [existing for existing in prior if not (rule_set < existing)]
                survivors.append(rule_set)
                minimal_for_conclusion[head] = survivors

    # Emit defeasible-rule arguments. ``rule_set`` is drawn from
    # defeasible-kind rules only, so no filtering by kind is needed
    # here — defeater-kind arguments are emitted above in the
    # Nute/Antoniou pass.
    for head, minimal_sets in minimal_for_conclusion.items():
        for rule_set in minimal_sets:
            if not any(r.head == head for r in rule_set):
                continue
            arguments.add(Argument(rules=rule_set, conclusion=head))

    return frozenset(arguments)


def _has_contradiction(closure: frozenset[GroundAtom]) -> bool:
    for atom in closure:
        if complement(atom) in closure:
            return True
    return False

