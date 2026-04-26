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
class GroundingInspection:
    """Ground facts and rule instances grouped by Gunray rule kind."""

    fact_atoms: tuple[GroundAtom, ...]
    strict_rules: tuple[GroundRuleInstance, ...]
    defeasible_rules: tuple[GroundRuleInstance, ...]
    defeater_rules: tuple[GroundRuleInstance, ...]

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

    return GroundingInspection(
        fact_atoms=fact_atoms,
        strict_rules=tuple(sorted(strict_rules, key=_instance_sort_key)),
        defeasible_rules=tuple(sorted(defeasible_rules, key=_instance_sort_key)),
        defeater_rules=tuple(sorted(defeater_rules, key=_instance_sort_key)),
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
