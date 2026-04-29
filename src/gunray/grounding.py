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
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import GroundAtom, Scalar


def inspect_grounding(theory: SchemaDefeasibleTheory) -> GroundingInspection:
    """Inspect the exact ground instances produced by Gunray's shared grounder."""

    return _ground_theory(theory).inspection


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
    )
