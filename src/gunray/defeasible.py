"""Blocking defeasible evaluation for the current conformance-suite theory fragment."""

from __future__ import annotations

from collections import defaultdict

from datalog_conformance.schema import (
    DefeasibleModel,
    DefeasibleTheory as SchemaDefeasibleTheory,
    Policy,
    Program as SchemaProgram,
)

from .evaluator import SemiNaiveEvaluator
from .evaluator import _match_positive_body
from .parser import ground_atom, normalize_facts, parse_defeasible_theory
from .relation import IndexedRelation
from .types import DefeasibleRule, GroundAtom, GroundDefeasibleRule
from .types import variables_in_term


class DefeasibleEvaluator:
    """Evaluate defeasible theories under the suite's blocking-style semantics."""

    def evaluate(self, theory: SchemaDefeasibleTheory, policy: Policy) -> DefeasibleModel:
        del policy
        if _is_strict_only_theory(theory):
            return _evaluate_strict_only_theory(theory)

        facts, rules, conflicts = parse_defeasible_theory(theory)
        superiority = {(stronger, weaker) for stronger, weaker in theory.superiority}

        definite_model = _positive_closure(
            facts=facts,
            rules=[rule for rule in rules if rule.kind == "strict"],
        )
        support_model = _positive_closure(
            facts=facts,
            rules=[rule for rule in rules if rule.kind != "defeater"],
        )

        definitely = _facts_to_atoms(definite_model)
        supported = _facts_to_atoms(support_model)
        grounded_rules, unsupported_heads = _ground_rules(rules, support_model)

        rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]] = defaultdict(list)
        for rule in grounded_rules:
            rules_by_head[rule.head].append(rule)

        proven = set(definitely)
        candidates = {
            atom
            for atom in rules_by_head
            if any(rule.kind != "defeater" for rule in rules_by_head[atom])
        } | set(definitely)

        changed = True
        while changed:
            changed = False
            for atom in sorted(candidates, key=_atom_sort_key):
                if atom in proven:
                    continue
                if _can_prove(atom, proven, definitely, rules_by_head, conflicts, superiority):
                    proven.add(atom)
                    changed = True

        not_defeasibly: set[GroundAtom] = set()
        undecided: set[GroundAtom] = set()
        for atom in candidates | unsupported_heads:
            if atom in proven:
                continue
            support_rules = [
                rule
                for rule in rules_by_head.get(atom, [])
                if rule.kind != "defeater"
            ]
            if any(set(rule.body) <= proven for rule in support_rules):
                not_defeasibly.add(atom)
            elif any(set(rule.body) <= supported for rule in support_rules):
                undecided.add(atom)
            else:
                not_defeasibly.add(atom)

        sections = {
            "definitely": _atoms_to_section(definitely),
            "defeasibly": _atoms_to_section(proven),
            "not_defeasibly": _atoms_to_section(not_defeasibly),
            "undecided": _atoms_to_section(undecided),
        }
        return DefeasibleModel(
            sections={name: facts_map for name, facts_map in sections.items() if facts_map}
        )


def _is_strict_only_theory(theory: SchemaDefeasibleTheory) -> bool:
    return not theory.defeasible_rules and not theory.defeaters and not theory.superiority


def _evaluate_strict_only_theory(theory: SchemaDefeasibleTheory) -> DefeasibleModel:
    program = SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )
    model = SemiNaiveEvaluator().evaluate(program)
    sections = {
        "definitely": {predicate: set(rows) for predicate, rows in model.facts.items()},
        "defeasibly": {predicate: set(rows) for predicate, rows in model.facts.items()},
    }
    return DefeasibleModel(
        sections={name: facts_map for name, facts_map in sections.items() if facts_map}
    )


def _strict_rule_to_program_text(head: str, body: list[str]) -> str:
    if not body:
        return f"{head}."
    return f"{head} :- {', '.join(body)}."


def _positive_closure(
    facts: dict[str, set[tuple[object, ...]]],
    rules: list[DefeasibleRule],
) -> dict[str, IndexedRelation]:
    model = {
        predicate: IndexedRelation(rows)
        for predicate, rows in facts.items()
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


def _ground_rules(
    rules: list[DefeasibleRule],
    support_model: dict[str, IndexedRelation],
) -> tuple[list[GroundDefeasibleRule], set[GroundAtom]]:
    grounded: list[GroundDefeasibleRule] = []
    unsupported_heads: set[GroundAtom] = set()

    for rule in rules:
        bindings = _match_positive_body(rule.body, support_model)
        if not bindings:
            if not _rule_variables(rule):
                unsupported_heads.add(ground_atom(rule.head, {}))
            continue
        for binding in bindings:
            grounded.append(
                GroundDefeasibleRule(
                    rule_id=rule.rule_id,
                    kind=rule.kind,
                    head=ground_atom(rule.head, binding),
                    body=tuple(ground_atom(atom, binding) for atom in rule.body),
                )
            )

    return grounded, unsupported_heads


def _can_prove(
    atom: GroundAtom,
    proven: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
) -> bool:
    if atom in definitely:
        return True

    opposing_atoms = {
        other
        for other in rules_by_head
        if (atom.predicate, other.predicate) in conflicts and other.arguments == atom.arguments
    } | {
        other
        for other in definitely
        if (atom.predicate, other.predicate) in conflicts and other.arguments == atom.arguments
    }
    if opposing_atoms & definitely:
        return False

    supporting_rules = [
        rule
        for rule in rules_by_head.get(atom, [])
        if rule.kind != "defeater" and set(rule.body) <= proven
    ]
    if not supporting_rules:
        return False

    attackers: list[GroundDefeasibleRule] = []
    for opposing_atom in opposing_atoms:
        attackers.extend(
            rule
            for rule in rules_by_head.get(opposing_atom, [])
            if set(rule.body) <= proven
        )

    if not attackers:
        return True
    if any(attacker.kind == "strict" for attacker in attackers):
        return False

    for supporter in supporting_rules:
        if _supporter_survives(
            supporter, atom, proven, rules_by_head, opposing_atoms, superiority
        ):
            return True
    if not superiority and len(supporting_rules) > len(attackers):
        return True
    return False


def _supporter_survives(
    supporter: GroundDefeasibleRule,
    atom: GroundAtom,
    proven: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    opposing_atoms: set[GroundAtom],
    superiority: set[tuple[str, str]],
) -> bool:
    del atom

    for opposing_atom in opposing_atoms:
        attackers = [
            rule
            for rule in rules_by_head.get(opposing_atom, [])
            if set(rule.body) <= proven
        ]
        for attacker in attackers:
            if attacker.kind == "strict":
                return False
            if (supporter.rule_id, attacker.rule_id) not in superiority:
                return False
    return True


def _facts_to_atoms(facts: dict[str, IndexedRelation]) -> set[GroundAtom]:
    return {
        GroundAtom(predicate=predicate, arguments=tuple(row))
        for predicate, rows in facts.items()
        for row in rows
    }


def _atoms_to_section(atoms: set[GroundAtom]) -> dict[str, set[tuple[object, ...]]]:
    section: dict[str, set[tuple[object, ...]]] = defaultdict(set)
    for atom in atoms:
        section[atom.predicate].add(atom.arguments)
    return dict(section)


def _rule_variables(rule: DefeasibleRule) -> set[str]:
    variables: set[str] = set()
    for term in rule.head.terms:
        variables |= variables_in_term(term)
    for atom in rule.body:
        for term in atom.terms:
            variables |= variables_in_term(term)
    return variables


def _atom_sort_key(atom: GroundAtom) -> tuple[str, tuple[object, ...]]:
    return atom.predicate, atom.arguments
