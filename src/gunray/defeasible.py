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
        grounded_strict_rules = tuple(
            rule for rule in grounded_rules if rule.kind == "strict"
        )
        specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]] = {}

        rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]] = defaultdict(list)
        for rule in grounded_rules:
            rules_by_head[rule.head].append(rule)

        proven = set(definitely)
        proof_candidates = {
            atom
            for atom in rules_by_head
            if any(rule.kind != "defeater" for rule in rules_by_head[atom])
        } | set(definitely)
        classified_candidates = _expand_candidate_atoms(
            proof_candidates | set(rules_by_head) | set(definitely),
            conflicts,
        )

        changed = True
        while changed:
            changed = False
            for atom in sorted(proof_candidates, key=_atom_sort_key):
                if atom in proven:
                    continue
                if _can_prove(
                    atom,
                    proven,
                    definitely,
                    supported,
                    rules_by_head,
                    conflicts,
                    superiority,
                    grounded_strict_rules,
                    specificity_cache,
                ):
                    proven.add(atom)
                    changed = True

        not_defeasibly: set[GroundAtom] = set()
        undecided: set[GroundAtom] = set()
        for atom in classified_candidates | unsupported_heads:
            if atom in proven:
                continue
            support_rules = [
                rule
                for rule in rules_by_head.get(atom, [])
                if rule.kind != "defeater"
            ]
            supported_rules = [
                rule
                for rule in support_rules
                if _attacker_body_available(rule, supported, definitely)
            ]
            if not supported_rules:
                not_defeasibly.add(atom)
                continue
            if _has_blocking_peer(
                atom,
                supported_rules,
                supported,
                definitely,
                rules_by_head,
                conflicts,
                superiority,
                grounded_strict_rules,
                specificity_cache,
            ):
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
    supported: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
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
        if rule.kind != "defeater" and _rule_body_available(rule, proven, definitely)
    ]
    if not supporting_rules:
        return False

    attackers: list[GroundDefeasibleRule] = []
    for opposing_atom in opposing_atoms:
        attackers.extend(
            rule
            for rule in rules_by_head.get(opposing_atom, [])
            if _attacker_body_available(rule, supported, definitely)
        )

    if not attackers:
        return True
    if any(attacker.kind == "strict" for attacker in attackers):
        return False

    for supporter in supporting_rules:
        if _supporter_survives(
            supporter,
            atom,
            supported,
            definitely,
            rules_by_head,
            opposing_atoms,
            superiority,
            grounded_strict_rules,
            specificity_cache,
        ):
            return True
    return False


def _supporter_survives(
    supporter: GroundDefeasibleRule,
    atom: GroundAtom,
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    opposing_atoms: set[GroundAtom],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> bool:
    del atom

    for opposing_atom in opposing_atoms:
        attackers = [
            rule
            for rule in rules_by_head.get(opposing_atom, [])
            if _attacker_body_available(rule, supported, definitely)
        ]
        for attacker in attackers:
            if attacker.kind == "strict":
                return False
            if (supporter.rule_id, attacker.rule_id) in superiority:
                continue
            if _is_more_specific(
                supporter,
                attacker,
                grounded_strict_rules,
                specificity_cache,
            ):
                continue
            if attacker.kind == "defeater":
                return False
            if _is_more_specific(
                attacker,
                supporter,
                grounded_strict_rules,
                specificity_cache,
            ):
                return False
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


def _expand_candidate_atoms(
    atoms: set[GroundAtom],
    conflicts: set[tuple[str, str]],
) -> set[GroundAtom]:
    expanded = set(atoms)
    for atom in list(atoms):
        for left, right in conflicts:
            if left != atom.predicate:
                continue
            expanded.add(GroundAtom(predicate=right, arguments=atom.arguments))
    return expanded


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


def _rule_body_available(
    rule: GroundDefeasibleRule,
    proven: set[GroundAtom],
    definitely: set[GroundAtom],
) -> bool:
    body = set(rule.body)
    if rule.kind == "strict":
        return body <= definitely
    return body <= proven


def _attacker_body_available(
    rule: GroundDefeasibleRule,
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
) -> bool:
    body = set(rule.body)
    if rule.kind == "strict":
        return body <= definitely
    return body <= supported


def _is_more_specific(
    left: GroundDefeasibleRule,
    right: GroundDefeasibleRule,
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> bool:
    left_body = frozenset(left.body)
    right_body = frozenset(right.body)
    left_closure = _strict_body_closure(left_body, grounded_strict_rules, cache)
    right_closure = _strict_body_closure(right_body, grounded_strict_rules, cache)
    return set(right.body) <= left_closure and not set(left.body) <= right_closure


def _strict_body_closure(
    seeds: frozenset[GroundAtom],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> set[GroundAtom]:
    cached = cache.get(seeds)
    if cached is not None:
        return cached

    closure = set(seeds)
    changed = True
    while changed:
        changed = False
        for rule in grounded_strict_rules:
            if set(rule.body) <= closure and rule.head not in closure:
                closure.add(rule.head)
                changed = True
    cache[seeds] = closure
    return closure


def _has_blocking_peer(
    atom: GroundAtom,
    support_rules: list[GroundDefeasibleRule],
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> bool:
    opposing_atoms = {
        other
        for other in rules_by_head
        if (atom.predicate, other.predicate) in conflicts and other.arguments == atom.arguments
    } | {
        GroundAtom(predicate=right, arguments=atom.arguments)
        for left, right in conflicts
        if left == atom.predicate
    }

    for supporting_rule in support_rules:
        for opposing_atom in opposing_atoms:
            for attacker in rules_by_head.get(opposing_atom, []):
                if attacker.kind in {"strict", "defeater"}:
                    continue
                if not _attacker_body_available(attacker, supported, definitely):
                    continue
                if (supporting_rule.rule_id, attacker.rule_id) in superiority:
                    continue
                if (attacker.rule_id, supporting_rule.rule_id) in superiority:
                    continue
                if _is_more_specific(
                    supporting_rule,
                    attacker,
                    grounded_strict_rules,
                    specificity_cache,
                ):
                    continue
                if _is_more_specific(
                    attacker,
                    supporting_rule,
                    grounded_strict_rules,
                    specificity_cache,
                ):
                    continue
                return True
    return False
