"""Public grounding inspection built on Gunray's shared grounder."""

from __future__ import annotations

from ._internal import _ground_theory
from .grounding_types import (
    GroundingInspection,
    GroundingSimplification,
    GroundingSubstitution,
    GroundRuleInstance,
    GroundRuleKind,
    GroundRuleResolution,
)
from .parser import parse_defeasible_theory
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import DefeasibleRule
from .types import GroundAtom, Scalar


def inspect_grounding(theory: SchemaDefeasibleTheory) -> GroundingInspection:
    """Inspect the exact ground instances produced by Gunray's shared grounder."""

    return _ground_theory(theory).inspection


def compute_non_approximated(theory: SchemaDefeasibleTheory) -> frozenset[str]:
    """Return predicates determined only by facts, strict rules, and safe conflicts.

    This is a conservative Diller-Definition-12 style analysis over Gunray's
    typed defeasible theory surface. A predicate is rejected if a non-strict
    rule can derive it, if a strict derivation depends on an approximated
    predicate, or if one of its configured conflict partners is approximated.
    """

    facts, rules, conflicts = parse_defeasible_theory(theory)
    predicates = _theory_predicates(facts, rules, conflicts)
    non_strict_heads = {
        rule.head.predicate
        for rule in rules
        if rule.kind != "strict"
    }
    candidate = set(predicates - non_strict_heads)
    changed = True
    while changed:
        changed = False
        for predicate in tuple(sorted(candidate)):
            if not _predicate_is_non_approximated_candidate(
                predicate,
                candidate,
                predicates,
                rules,
                conflicts,
            ):
                candidate.remove(predicate)
                changed = True
    return frozenset(candidate)


def _theory_predicates(
    facts: dict[str, set[tuple[Scalar, ...]]],
    rules: list[DefeasibleRule],
    conflicts: set[tuple[str, str]],
) -> frozenset[str]:
    del conflicts
    predicates = set(facts)
    for rule in rules:
        predicates.add(rule.head.predicate)
        predicates.update(atom.predicate for atom in rule.body)
        predicates.update(atom.predicate for atom in rule.default_negated_body)
    return frozenset(predicates)


def _predicate_is_non_approximated_candidate(
    predicate: str,
    candidate: set[str],
    predicates: frozenset[str],
    rules: list[DefeasibleRule],
    conflicts: set[tuple[str, str]],
) -> bool:
    for rule in rules:
        if rule.head.predicate != predicate:
            continue
        if rule.kind != "strict":
            return False
        if any(atom.predicate not in candidate for atom in rule.body):
            return False
        if any(atom.predicate not in candidate for atom in rule.default_negated_body):
            return False
    for left, right in conflicts:
        if left == predicate and right in predicates and right not in candidate:
            return False
        if right == predicate and left in predicates and left not in candidate:
            return False
    return True


def _atom_sort_key(atom: GroundAtom) -> tuple[str, tuple[Scalar, ...]]:
    return atom.predicate, atom.arguments


def _instance_sort_key(
    instance: GroundRuleInstance,
) -> tuple[str, GroundRuleKind, tuple[str, tuple[Scalar, ...]], GroundingSubstitution]:
    return instance.rule_id, instance.kind, _atom_sort_key(instance.head), instance.substitution


def _simplify_strict_fact_grounding(
    fact_atoms: tuple[GroundAtom, ...],
    strict_rules: tuple[GroundRuleInstance, ...],
    defeasible_rules: tuple[GroundRuleInstance, ...],
    defeater_rules: tuple[GroundRuleInstance, ...],
    non_approximated_predicates: frozenset[str] = frozenset(),
) -> GroundingSimplification:
    """Resolve strict ground rules whose bodies are already definite facts.

    Diller et al. 2025 Definition 9 (p. 3) obtains ground substitutions
    by querying the least Datalog model for rule bodies. Algorithm 2
    (p. 7) then applies ASPIC+-specific simplifications, including
    resolving strict/fact-only material into the fact base while
    preserving complete extensions. Gunray only exposes the conservative
    DeLP-compatible fragment here: no defeasible or defeater rule is
    removed, and any strict rule whose body cannot be proven definite
    remains in the argumentation grounding report.
    """

    known_facts: set[GroundAtom] = set(fact_atoms)
    remaining = list(strict_rules)
    resolved: list[GroundRuleResolution] = []

    changed = True
    while changed:
        changed = False
        next_remaining: list[GroundRuleInstance] = []
        for rule in remaining:
            if all(atom in known_facts for atom in rule.body):
                known_facts.add(rule.head)
                resolved.append(GroundRuleResolution(rule=rule, produced_fact=rule.head))
                changed = True
                continue
            next_remaining.append(rule)
        remaining = next_remaining

    return GroundingSimplification(
        definite_fact_atoms=tuple(sorted(known_facts, key=_atom_sort_key)),
        resolved_strict_rules=tuple(
            sorted(resolved, key=lambda item: _instance_sort_key(item.rule))
        ),
        strict_rules_for_argumentation=tuple(sorted(remaining, key=_instance_sort_key)),
        defeasible_rules_for_argumentation=defeasible_rules,
        defeater_rules_for_argumentation=defeater_rules,
        non_approximated_predicates=tuple(sorted(non_approximated_predicates)),
    )
