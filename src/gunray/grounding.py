"""Public grounding inspection built on Gunray's shared grounder."""

from __future__ import annotations

import json

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
from .schema import DefeasibleTheory, Rule
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import DefeasibleRule, GroundAtom, Scalar


def inspect_grounding(theory: SchemaDefeasibleTheory) -> GroundingInspection:
    """Inspect the exact ground instances produced by Gunray's shared grounder."""

    return _ground_theory(theory).inspection


def simplified_ground_theory(
    theory: SchemaDefeasibleTheory,
    inspection: GroundingInspection,
) -> DefeasibleTheory:
    """Convert a Diller strict/fact simplification report into a ground theory."""

    simplification = inspection.simplification
    source_to_ground_ids: dict[str, list[str]] = {}
    strict_rules = tuple(
        _schema_rule_from_ground_instance(instance, index, source_to_ground_ids)
        for index, instance in enumerate(simplification.strict_rules_for_argumentation)
    )
    defeasible_rules = tuple(
        _schema_rule_from_ground_instance(instance, index, source_to_ground_ids)
        for index, instance in enumerate(simplification.defeasible_rules_for_argumentation)
    )
    defeaters = tuple(
        _schema_rule_from_ground_instance(instance, index, source_to_ground_ids)
        for index, instance in enumerate(simplification.defeater_rules_for_argumentation)
    )

    return DefeasibleTheory(
        facts=_facts_from_ground_atoms(simplification.definite_fact_atoms),
        strict_rules=strict_rules,
        defeasible_rules=defeasible_rules,
        defeaters=defeaters,
        superiority=_ground_superiority(theory.superiority, source_to_ground_ids),
        conflicts=theory.conflicts,
    )


def compute_non_approximated(theory: SchemaDefeasibleTheory) -> frozenset[str]:
    """Return predicates determined only by facts, strict rules, and safe conflicts.

    This is a conservative Diller-Definition-12 style analysis over Gunray's
    typed defeasible theory surface. A predicate is rejected if a non-strict
    rule can derive it, if a strict derivation depends on an approximated
    predicate, or if one of its configured conflict partners is approximated.
    """

    facts, rules, conflicts = parse_defeasible_theory(theory)
    predicates = _theory_predicates(facts, rules, conflicts)
    non_strict_heads = {rule.head.predicate for rule in rules if rule.kind != "strict"}
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


def _facts_from_ground_atoms(
    atoms: tuple[GroundAtom, ...],
) -> dict[str, set[tuple[Scalar, ...]]]:
    facts: dict[str, set[tuple[Scalar, ...]]] = {}
    for atom in atoms:
        facts.setdefault(atom.predicate, set()).add(atom.arguments)
    return facts


def _schema_rule_from_ground_instance(
    instance: GroundRuleInstance,
    index: int,
    source_to_ground_ids: dict[str, list[str]],
) -> Rule:
    rule_id = _ground_rule_id(instance, index)
    source_to_ground_ids.setdefault(instance.rule_id, []).append(rule_id)
    body = tuple(_ground_atom_text(atom) for atom in instance.body) + tuple(
        f"not {_ground_atom_text(atom)}" for atom in instance.default_negated_body
    )
    return Rule(
        id=rule_id,
        head=_ground_atom_text(instance.head),
        body=body,
    )


def _ground_rule_id(instance: GroundRuleInstance, index: int) -> str:
    substitution = "_".join(
        f"{name}_{_rule_id_scalar(value)}" for name, value in instance.substitution
    )
    if substitution:
        return f"{instance.rule_id}__{substitution}"
    return f"{instance.rule_id}__ground_{index}"


def _rule_id_scalar(value: Scalar) -> str:
    text = str(value).replace("~", "not_")
    return "".join(
        character if character.isalnum() or character == "_" else "_" for character in text
    )


def _ground_atom_text(atom: GroundAtom) -> str:
    if not atom.arguments:
        return atom.predicate
    return f"{atom.predicate}({', '.join(_scalar_text(value) for value in atom.arguments)})"


def _scalar_text(value: Scalar) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def _ground_superiority(
    superiority: tuple[tuple[str, str], ...],
    source_to_ground_ids: dict[str, list[str]],
) -> tuple[tuple[str, str], ...]:
    grounded: list[tuple[str, str]] = []
    for higher, lower in superiority:
        for higher_id in source_to_ground_ids.get(higher, ()):
            for lower_id in source_to_ground_ids.get(lower, ()):
                grounded.append((higher_id, lower_id))
    return tuple(grounded)


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
