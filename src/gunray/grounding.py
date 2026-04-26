"""Public grounding inspection built on Gunray's shared grounder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from ._internal import (
    _ground_rule_instances_with_substitutions,
    _positive_closure_for_grounding,
)
from .parser import parse_defeasible_theory
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .types import GroundAtom, Scalar

GroundRuleKind = Literal["strict", "defeasible", "defeater"]
GroundingSubstitution = tuple[tuple[str, Scalar], ...]


@dataclass(frozen=True, slots=True)
class GroundRuleInstance:
    """A grounded rule instance and the source-level substitution that produced it."""

    rule_id: str
    kind: GroundRuleKind
    head: GroundAtom
    body: tuple[GroundAtom, ...]
    substitution: GroundingSubstitution


@dataclass(frozen=True, slots=True)
class GroundRuleResolution:
    """A strict ground rule resolved into the definite fact base."""

    rule: GroundRuleInstance
    produced_fact: GroundAtom


@dataclass(frozen=True, slots=True)
class GroundingSimplification:
    """Conservative Diller-style strict/fact grounding simplification report."""

    definite_fact_atoms: tuple[GroundAtom, ...]
    resolved_strict_rules: tuple[GroundRuleResolution, ...]
    strict_rules_for_argumentation: tuple[GroundRuleInstance, ...]
    defeasible_rules_for_argumentation: tuple[GroundRuleInstance, ...]
    defeater_rules_for_argumentation: tuple[GroundRuleInstance, ...]

    @property
    def ground_rules_for_argumentation(self) -> tuple[GroundRuleInstance, ...]:
        return (
            self.strict_rules_for_argumentation
            + self.defeasible_rules_for_argumentation
            + self.defeater_rules_for_argumentation
        )


@dataclass(frozen=True, slots=True)
class GroundingInspection:
    """Ground facts and rule instances grouped by Gunray rule kind."""

    fact_atoms: tuple[GroundAtom, ...]
    strict_rules: tuple[GroundRuleInstance, ...]
    defeasible_rules: tuple[GroundRuleInstance, ...]
    defeater_rules: tuple[GroundRuleInstance, ...]
    simplification: GroundingSimplification

    @property
    def all_rule_instances(self) -> tuple[GroundRuleInstance, ...]:
        return self.strict_rules + self.defeasible_rules + self.defeater_rules


def inspect_grounding(theory: SchemaDefeasibleTheory) -> GroundingInspection:
    """Inspect the exact ground instances produced by Gunray's shared grounder."""

    facts, rules, _conflicts = parse_defeasible_theory(theory)
    positive_model = _positive_closure_for_grounding(facts, rules)
    fact_atoms = tuple(
        sorted(
            (
                GroundAtom(predicate=predicate, arguments=tuple(row))
                for predicate, rows in facts.items()
                for row in rows
            ),
            key=_atom_sort_key,
        )
    )

    strict_rules: list[GroundRuleInstance] = []
    defeasible_rules: list[GroundRuleInstance] = []
    defeater_rules: list[GroundRuleInstance] = []

    for rule in rules:
        target = _target_bucket(rule.kind, strict_rules, defeasible_rules, defeater_rules)
        for instance in _ground_rule_instances_with_substitutions(rule, positive_model):
            target.append(
                GroundRuleInstance(
                    rule_id=instance.rule.rule_id,
                    kind=cast(GroundRuleKind, instance.rule.kind),
                    head=instance.rule.head,
                    body=instance.rule.body,
                    substitution=_public_substitution(instance.substitution),
                )
            )

    strict_instances = tuple(sorted(strict_rules, key=_instance_sort_key))
    defeasible_instances = tuple(sorted(defeasible_rules, key=_instance_sort_key))
    defeater_instances = tuple(sorted(defeater_rules, key=_instance_sort_key))

    return GroundingInspection(
        fact_atoms=fact_atoms,
        strict_rules=strict_instances,
        defeasible_rules=defeasible_instances,
        defeater_rules=defeater_instances,
        simplification=_simplify_strict_fact_grounding(
            fact_atoms,
            strict_instances,
            defeasible_instances,
            defeater_instances,
        ),
    )


def _target_bucket(
    kind: str,
    strict_rules: list[GroundRuleInstance],
    defeasible_rules: list[GroundRuleInstance],
    defeater_rules: list[GroundRuleInstance],
) -> list[GroundRuleInstance]:
    if kind == "strict":
        return strict_rules
    if kind == "defeasible":
        return defeasible_rules
    return defeater_rules


def _public_substitution(
    substitution: tuple[tuple[str, object], ...],
) -> GroundingSubstitution:
    return tuple((name, cast(Scalar, value)) for name, value in substitution)


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

    Diller et al. 2025, page images 004-007, use ASPIC+-specific
    Transformations 1-2 and Algorithm 2 to move strict/fact-only
    conclusions into the fact base while preserving accepted
    conclusions. Gunray only exposes the conservative DeLP-compatible
    fragment here: no defeasible or defeater rule is removed, and any
    strict rule whose body cannot be proven definite remains in the
    argumentation grounding report.
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
