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
from itertools import combinations, product

from collections.abc import Mapping

from .disagreement import complement, strict_closure
from .evaluator import _match_positive_body
from .parser import ground_atom, parse_defeasible_theory
from .relation import IndexedRelation
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import (
    DefeasibleRule,
    GroundAtom,
    GroundDefeasibleRule,
    Scalar,
    Variable,
    variables_in_term,
)


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

    facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)
    strict_rules = tuple(r for r in defeasible_rules if r.kind == "strict")
    body_rules = tuple(r for r in defeasible_rules if r.kind == "defeasible")
    defeater_rules = tuple(r for r in defeasible_rules if r.kind == "defeater")

    # Build the positive model so that grounding can bind body variables
    # to concrete constants. This mirrors the deleted `_positive_closure`
    # helper (scout report Section 4.6): start from the fact model and
    # saturate under strict+defeasible+defeater rules positively. This
    # is only used to *discover candidate bindings* for grounding; it
    # does not influence which atoms are derivable under Pi alone.
    positive_model = _positive_closure_for_grounding(
        facts,
        defeasible_rules,
    )

    grounded_strict = tuple(
        _ground_rule_instances(rule, positive_model) for rule in strict_rules
    )
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance for group in grounded_strict for instance in group
    )

    grounded_defeasible_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance
        for rule in body_rules
        for instance in _ground_rule_instances(rule, positive_model)
    )
    grounded_defeater_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance
        for rule in defeater_rules
        for instance in _ground_rule_instances(rule, positive_model)
    )

    # Pi = strict facts, closed under ground strict rules.
    fact_atoms = _fact_atoms(facts)
    pi_closure = strict_closure(fact_atoms, grounded_strict_rules)

    arguments: set[Argument] = set()

    # Every atom in the strict-only closure is a trivial argument
    # <empty, h>. Garcia 04 Def 3.1 condition (1) permits the
    # degenerate case where h has a strict derivation.
    for atom in pi_closure:
        arguments.add(Argument(rules=frozenset(), conclusion=atom))

    # Condition (2) needs to be checkable per subset. Compute it using
    # the ground strict rules + the ground rules in the subset (treating
    # defeasible rules like strict rules for the purpose of closure).
    minimal_for_conclusion: dict[
        GroundAtom, list[frozenset[GroundDefeasibleRule]]
    ] = {}

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
                survivors = [
                    existing for existing in prior if not (rule_set < existing)
                ]
                survivors.append(rule_set)
                minimal_for_conclusion[head] = survivors

    # Defeaters cannot conclude arguments (Garcia 04 Def 3.6). Filter
    # any minimal set that consists solely of a defeater-backed head.
    defeater_head_set = {rule.head for rule in grounded_defeater_rules}

    for head, minimal_sets in minimal_for_conclusion.items():
        for rule_set in minimal_sets:
            # If the head only arises because of a defeater kind rule,
            # skip. We key this on whether the literal head matches a
            # defeater head and none of the `rule_set` produces it
            # defeasibly. Since `rule_set` is drawn from defeasible
            # rules only, this condition is already satisfied — we
            # just need to make sure the literal isn't exclusively a
            # defeater conclusion with no defeasible backing. For B1
            # the filter is conservative: any head reached by rule_set
            # is fine so long as rule_set contains a defeasible rule
            # with that head.
            if not any(r.head == head for r in rule_set):
                continue
            if head in defeater_head_set and not any(
                r.kind == "defeasible" and r.head == head for r in rule_set
            ):
                continue
            arguments.add(Argument(rules=rule_set, conclusion=head))

    return frozenset(arguments)


def _force_strict_for_closure(rule: GroundDefeasibleRule) -> GroundDefeasibleRule:
    """Return a rule with ``kind="strict"`` so ``strict_closure`` propagates it.

    ``strict_closure`` filters on ``kind == "strict"``. For Def 3.1
    condition (1) we want rules in ``A`` to also propagate, so we wrap
    each defeasible rule as a strict-kind shadow with the same head
    and body.
    """

    return GroundDefeasibleRule(
        rule_id=rule.rule_id,
        kind="strict",
        head=rule.head,
        body=rule.body,
    )


def _has_contradiction(closure: frozenset[GroundAtom]) -> bool:
    for atom in closure:
        if complement(atom) in closure:
            return True
    return False


def _fact_atoms(
    facts: Mapping[str, set[tuple[Scalar, ...]]],
) -> frozenset[GroundAtom]:
    return frozenset(
        GroundAtom(predicate=predicate, arguments=tuple(row))
        for predicate, rows in facts.items()
        for row in rows
    )


def _positive_closure_for_grounding(
    facts: Mapping[str, set[tuple[Scalar, ...]]],
    rules: list[DefeasibleRule],
) -> dict[str, IndexedRelation]:
    """Recreation of the deleted ``_positive_closure`` helper.

    Scout report Section 4.6: saturate the fact model under every
    rule's positive body (ignoring strong-negation interaction). This
    is used only to discover candidate variable bindings — final
    non-contradiction checking happens via ``strict_closure`` later.
    """

    model: dict[str, IndexedRelation] = {
        predicate: IndexedRelation(rows) for predicate, rows in facts.items()
    }
    while True:
        changed = False
        for rule in rules:
            bindings = _match_positive_body(rule.body, model)
            for binding in bindings:
                grounded = ground_atom(rule.head, binding)
                bucket = model.setdefault(grounded.predicate, IndexedRelation())
                if bucket.add(grounded.arguments):
                    changed = True
        if not changed:
            return model


def _rule_variable_names(rule: DefeasibleRule) -> list[str]:
    names: set[str] = set()
    for term in rule.head.terms:
        names |= variables_in_term(term)
    for atom in rule.body:
        for term in atom.terms:
            names |= variables_in_term(term)
    return sorted(names)


def _ground_rule_instances(
    rule: DefeasibleRule,
    model: dict[str, IndexedRelation],
) -> tuple[GroundDefeasibleRule, ...]:
    """Return all ground instances of ``rule`` under ``model``.

    A rule with no variables grounds to a single instance. Otherwise
    we enumerate bindings produced by ``_match_positive_body`` over
    the rule body. If the body is empty (a variable-free rule is
    handled above), this falls back to the head variables times the
    constant universe.
    """

    variables = _rule_variable_names(rule)
    if not variables:
        head = ground_atom(rule.head, {})
        body = tuple(ground_atom(atom, {}) for atom in rule.body)
        return (
            GroundDefeasibleRule(
                rule_id=rule.rule_id,
                kind=rule.kind,
                head=head,
                body=body,
            ),
        )

    if rule.body:
        bindings = _match_positive_body(rule.body, model)
    else:
        bindings = _head_only_bindings(rule, model)

    # Deduplicate ground instances.
    seen: dict[tuple[str, tuple[object, ...]], GroundDefeasibleRule] = {}
    for binding in bindings:
        try:
            head = ground_atom(rule.head, binding)
        except KeyError:
            continue
        try:
            body = tuple(ground_atom(atom, binding) for atom in rule.body)
        except KeyError:
            continue
        key = (rule.rule_id, head.arguments)
        seen[key] = GroundDefeasibleRule(
            rule_id=rule.rule_id,
            kind=rule.kind,
            head=head,
            body=body,
        )
    return tuple(seen.values())


def _head_only_bindings(
    rule: DefeasibleRule,
    model: dict[str, IndexedRelation],
) -> list[dict[str, object]]:
    """Enumerate head-only variable bindings over the constant universe.

    Used when a rule has variables in the head but an empty positive
    body (rare in Block 1 tests). The constant universe is taken from
    the positive model.
    """

    constants = sorted(
        {
            value
            for relation in model.values()
            for row in relation
            for value in row
        },
        key=repr,
    )
    variables = [
        term.name for term in rule.head.terms if isinstance(term, Variable)
    ]
    if not variables:
        return [{}]
    if not constants:
        return []
    return [
        {name: value for name, value in zip(variables, values, strict=True)}
        for values in product(constants, repeat=len(variables))
    ]
