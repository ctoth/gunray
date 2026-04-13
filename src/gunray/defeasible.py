"""Blocking defeasible evaluation for the current Gunray theory fragment."""

from __future__ import annotations

from collections import defaultdict
from typing import cast

from .ambiguity import AmbiguityPolicy, attacker_basis_atoms, resolve_ambiguity_policy
from .evaluator import SemiNaiveEvaluator, _match_positive_body
from .parser import ground_atom, parse_defeasible_theory
from .relation import IndexedRelation
from .schema import DefeasibleModel, FactTuple, ModelFacts, Policy
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import Program as SchemaProgram
from .trace import (
    ClassificationTrace,
    DatalogTrace,
    DefeasibleTrace,
    ProofAttemptTrace,
    TraceConfig,
)
from .types import DefeasibleRule, GroundAtom, GroundDefeasibleRule, variables_in_term


class DefeasibleEvaluator:
    """Evaluate defeasible theories under Gunray's supported semantics."""

    def evaluate(self, theory: SchemaDefeasibleTheory, policy: Policy) -> DefeasibleModel:
        model, _ = self.evaluate_with_trace(theory, policy)
        return model

    def evaluate_with_trace(
        self,
        theory: SchemaDefeasibleTheory,
        policy: Policy,
        trace_config: TraceConfig | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]:
        actual_trace_config = trace_config or TraceConfig()
        trace = DefeasibleTrace(config=actual_trace_config)
        if _is_strict_only_theory(theory):
            model, strict_trace = _evaluate_strict_only_theory_with_trace(
                theory,
                actual_trace_config,
            )
            trace.strict_trace = strict_trace
            trace.definitely = tuple(
                sorted(_section_to_atoms(model.sections.get("definitely", {})), key=_atom_sort_key)
            )
            trace.supported = trace.definitely
            return model, trace

        facts, rules, conflicts = parse_defeasible_theory(theory)
        superiority = {(stronger, weaker) for stronger, weaker in theory.superiority}
        ambiguity_policy = resolve_ambiguity_policy(policy)

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
        trace.definitely = tuple(sorted(definitely, key=_atom_sort_key))
        trace.supported = tuple(sorted(supported, key=_atom_sort_key))
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

        while True:
            next_proven = set(definitely)
            for atom in sorted(proof_candidates, key=_atom_sort_key):
                if _can_prove(
                    atom,
                    proven,
                    definitely,
                    supported,
                    ambiguity_policy,
                    rules_by_head,
                    conflicts,
                    superiority,
                    grounded_strict_rules,
                    specificity_cache,
                    trace,
                ):
                    next_proven.add(atom)
            if next_proven == proven:
                break
            proven = next_proven

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
                trace.classifications.append(
                    ClassificationTrace(
                        atom=atom,
                        result="not_defeasibly",
                        reason="no_supported_rules",
                        supporter_rule_ids=tuple(rule.rule_id for rule in support_rules),
                    )
                )
                continue
            active_support_rules = [
                rule
                for rule in supported_rules
                if _rule_body_available(rule, proven, definitely)
            ]
            if not active_support_rules:
                undecided.add(atom)
                trace.classifications.append(
                    ClassificationTrace(
                        atom=atom,
                        result="undecided",
                        reason="supported_only_by_unproved_bodies",
                        supporter_rule_ids=tuple(rule.rule_id for rule in supported_rules),
                    )
                )
                continue
            if (
                ambiguity_policy.name is Policy.PROPAGATING
                and _has_live_opposition(
                    atom,
                    ambiguity_policy,
                    proven,
                    supported,
                    definitely,
                    rules_by_head,
                    conflicts,
                )
            ):
                undecided.add(atom)
                trace.classifications.append(
                    ClassificationTrace(
                        atom=atom,
                        result="undecided",
                        reason="propagating_live_opposition",
                        supporter_rule_ids=tuple(rule.rule_id for rule in active_support_rules),
                    )
                )
                continue
            blocking_peer = _find_blocking_peer(
                atom,
                active_support_rules,
                ambiguity_policy,
                proven,
                supported,
                definitely,
                rules_by_head,
                conflicts,
                superiority,
                grounded_strict_rules,
                specificity_cache,
            )
            if blocking_peer is not None:
                supporting_rule, attacker = blocking_peer
                undecided.add(atom)
                trace.classifications.append(
                    ClassificationTrace(
                        atom=atom,
                        result="undecided",
                        reason="equal_strength_peer_conflict",
                        supporter_rule_ids=(supporting_rule.rule_id,),
                        attacker_rule_ids=(attacker.rule_id,),
                        opposing_atoms=(attacker.head,),
                    )
                )
            else:
                not_defeasibly.add(atom)
                trace.classifications.append(
                    ClassificationTrace(
                        atom=atom,
                        result="not_defeasibly",
                        reason="supported_but_overruled",
                        supporter_rule_ids=tuple(rule.rule_id for rule in active_support_rules),
                    )
                )

        sections = {
            "definitely": _atoms_to_section(definitely),
            "defeasibly": _atoms_to_section(proven),
            "not_defeasibly": _atoms_to_section(not_defeasibly),
            "undecided": _atoms_to_section(undecided),
        }
        return DefeasibleModel(
            sections={name: facts_map for name, facts_map in sections.items() if facts_map}
        ), trace


def _is_strict_only_theory(theory: SchemaDefeasibleTheory) -> bool:
    return not theory.defeasible_rules and not theory.defeaters and not theory.superiority


def _evaluate_strict_only_theory(theory: SchemaDefeasibleTheory) -> DefeasibleModel:
    model, _ = _evaluate_strict_only_theory_with_trace(theory, TraceConfig())
    return model


def _evaluate_strict_only_theory_with_trace(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
) -> tuple[DefeasibleModel, DatalogTrace]:
    program = SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )
    model, trace = SemiNaiveEvaluator().evaluate_with_trace(program, trace_config)
    sections = {
        "definitely": {predicate: set(rows) for predicate, rows in model.facts.items()},
        "defeasibly": {predicate: set(rows) for predicate, rows in model.facts.items()},
    }
    return DefeasibleModel(
        sections={name: facts_map for name, facts_map in sections.items() if facts_map}
    ), trace


def _strict_rule_to_program_text(head: str, body: list[str]) -> str:
    if not body:
        return f"{head}."
    return f"{head} :- {', '.join(body)}."


def _positive_closure(
    facts: dict[str, set[FactTuple]],
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
    ambiguity_policy: AmbiguityPolicy,
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
    trace: DefeasibleTrace | None,
) -> bool:
    if atom in definitely:
        _record_proof_attempt(trace, atom, "proved", "strict_fact_or_rule", (), (), ())
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
    sorted_opponents = tuple(sorted(opposing_atoms, key=_atom_sort_key))
    if opposing_atoms & definitely:
        _record_proof_attempt(
            trace,
            atom,
            "blocked",
            "conflict_with_definite_opponent",
            (),
            (),
            sorted_opponents,
        )
        return False

    supporting_rules = [
        rule
        for rule in rules_by_head.get(atom, [])
        if rule.kind != "defeater" and _rule_body_available(rule, proven, definitely)
    ]
    if not supporting_rules:
        _record_proof_attempt(
            trace,
            atom,
            "blocked",
            "no_active_support_rule",
            (),
            (),
            sorted_opponents,
        )
        return False

    attacker_basis = attacker_basis_atoms(
        ambiguity_policy,
        proven=proven,
        supported=supported,
    )

    attackers: list[GroundDefeasibleRule] = []
    for opposing_atom in opposing_atoms:
        attackers.extend(
            rule
            for rule in rules_by_head.get(opposing_atom, [])
            if _attacker_body_available(rule, attacker_basis, definitely)
        )

    if not attackers:
        _record_proof_attempt(
            trace,
            atom,
            "proved",
            "unopposed_support",
            tuple(rule.rule_id for rule in supporting_rules),
            (),
            sorted_opponents,
        )
        return True
    if any(attacker.kind == "strict" for attacker in attackers):
        _record_proof_attempt(
            trace,
            atom,
            "blocked",
            "strict_attacker",
            tuple(rule.rule_id for rule in supporting_rules),
            tuple(rule.rule_id for rule in attackers),
            sorted_opponents,
        )
        return False

    for supporter in supporting_rules:
        if _supporter_survives(
            supporter,
            atom,
            attacker_basis,
            definitely,
            rules_by_head,
            opposing_atoms,
            superiority,
            grounded_strict_rules,
            specificity_cache,
        ):
            _record_proof_attempt(
                trace,
                atom,
                "proved",
                f"surviving_supporter:{supporter.rule_id}",
                (supporter.rule_id,),
                tuple(rule.rule_id for rule in attackers),
                sorted_opponents,
            )
            return True
    _record_proof_attempt(
        trace,
        atom,
        "blocked",
        "all_supporters_overruled",
        tuple(rule.rule_id for rule in supporting_rules),
        tuple(rule.rule_id for rule in attackers),
        sorted_opponents,
    )
    return False


def _supporter_survives(
    supporter: GroundDefeasibleRule,
    atom: GroundAtom,
    attacker_basis: set[GroundAtom],
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
            if _attacker_body_available(rule, attacker_basis, definitely)
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
        GroundAtom(predicate=predicate, arguments=cast(FactTuple, tuple(row)))
        for predicate, rows in facts.items()
        for row in rows
    }


def _atoms_to_section(atoms: set[GroundAtom]) -> dict[str, set[FactTuple]]:
    section: dict[str, set[FactTuple]] = defaultdict(set)
    for atom in atoms:
        section[atom.predicate].add(atom.arguments)
    return dict(section)


def _section_to_atoms(section: ModelFacts) -> set[GroundAtom]:
    return {
        GroundAtom(predicate=predicate, arguments=arguments)
        for predicate, rows in section.items()
        for arguments in rows
    }


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


def _atom_sort_key(atom: GroundAtom) -> tuple[str, FactTuple]:
    return atom.predicate, atom.arguments


def _record_proof_attempt(
    trace: DefeasibleTrace | None,
    atom: GroundAtom,
    result: str,
    reason: str,
    supporter_rule_ids: tuple[str, ...],
    attacker_rule_ids: tuple[str, ...],
    opposing_atoms: tuple[GroundAtom, ...],
) -> None:
    if trace is None:
        return
    trace.proof_attempts.append(
        ProofAttemptTrace(
            atom=atom,
            result=result,
            reason=reason,
            supporter_rule_ids=supporter_rule_ids,
            attacker_rule_ids=attacker_rule_ids,
            opposing_atoms=opposing_atoms,
        )
    )


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


def _find_blocking_peer(
    atom: GroundAtom,
    support_rules: list[GroundDefeasibleRule],
    ambiguity_policy: AmbiguityPolicy,
    proven: set[GroundAtom],
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> tuple[GroundDefeasibleRule, GroundDefeasibleRule] | None:
    attacker_basis = attacker_basis_atoms(
        ambiguity_policy,
        proven=proven,
        supported=supported,
    )
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
                if not _attacker_body_available(attacker, attacker_basis, definitely):
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
                return supporting_rule, attacker
    return None


def _has_live_opposition(
    atom: GroundAtom,
    ambiguity_policy: AmbiguityPolicy,
    proven: set[GroundAtom],
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
) -> bool:
    attacker_basis = attacker_basis_atoms(
        ambiguity_policy,
        proven=proven,
        supported=supported,
    )
    opposing_atoms = {
        other
        for other in rules_by_head
        if (atom.predicate, other.predicate) in conflicts and other.arguments == atom.arguments
    } | {
        other
        for other in definitely
        if (atom.predicate, other.predicate) in conflicts and other.arguments == atom.arguments
    }
    return any(
        _attacker_body_available(rule, attacker_basis, definitely)
        for opposing_atom in opposing_atoms
        for rule in rules_by_head.get(opposing_atom, [])
        if rule.kind != "strict"
    )


def _has_blocking_peer(
    atom: GroundAtom,
    support_rules: list[GroundDefeasibleRule],
    ambiguity_policy: AmbiguityPolicy,
    proven: set[GroundAtom],
    supported: set[GroundAtom],
    definitely: set[GroundAtom],
    rules_by_head: dict[GroundAtom, list[GroundDefeasibleRule]],
    conflicts: set[tuple[str, str]],
    superiority: set[tuple[str, str]],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    specificity_cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> bool:
    return (
        _find_blocking_peer(
            atom,
            support_rules,
            ambiguity_policy,
            proven,
            supported,
            definitely,
            rules_by_head,
            conflicts,
            superiority,
            grounded_strict_rules,
            specificity_cache,
        )
        is not None
    )
