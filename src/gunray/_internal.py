"""Package-internal helpers shared across Gunray modules."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from itertools import product
from typing import TypeAlias

from .compiled import compile_simple_matcher, iter_compiled_bindings
from .errors import ArityMismatchError, SafetyViolationError, UnboundVariableError
from .parser import ground_atom, parse_defeasible_theory
from .relation import IndexedRelation
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import FactTuple, NegationSemantics
from .semantics import (
    SemanticError,
    add_values,
    compare_values,
    subtract_values,
    values_equal,
)
from .trace import IterationTrace
from .types import (
    AddExpression,
    Atom,
    AtomTerm,
    Comparison,
    Constant,
    DefeasibleRule,
    GroundAtom,
    GroundDefeasibleRule,
    Rule,
    Scalar,
    SubtractExpression,
    Variable,
    Wildcard,
    variables_in_term,
)

Binding: TypeAlias = dict[str, object]
Bindings: TypeAlias = list[Binding]
RelationModel: TypeAlias = dict[str, IndexedRelation]
RelationOverrides: TypeAlias = dict[int, IndexedRelation]
ArityMap: TypeAlias = dict[str, int]
GroundRuleKey: TypeAlias = tuple[str, tuple[object, ...]]
FactRows: TypeAlias = set[tuple[Scalar, ...]]
FactModel: TypeAlias = Mapping[str, FactRows]
LiteralText: TypeAlias = str
RuleBodyText: TypeAlias = list[LiteralText]
RuleText: TypeAlias = str


@dataclass(frozen=True, slots=True)
class _GroundedTheory:
    """Grounded fact atoms and per-kind ground rule tuples."""

    fact_atoms: frozenset[GroundAtom]
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...]
    grounded_defeasible_rules: tuple[GroundDefeasibleRule, ...]
    grounded_defeater_rules: tuple[GroundDefeasibleRule, ...]


def _ground_theory(theory: SchemaDefeasibleTheory) -> _GroundedTheory:
    """Parse, ground, and bucket every rule of ``theory`` by kind."""

    facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)
    strict_rules = tuple(r for r in defeasible_rules if r.kind == "strict")
    body_rules = tuple(r for r in defeasible_rules if r.kind == "defeasible")
    defeater_rules = tuple(r for r in defeasible_rules if r.kind == "defeater")

    positive_model = _positive_closure_for_grounding(facts, defeasible_rules)

    grounded_strict_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance
        for rule in strict_rules
        for instance in _ground_rule_instances(rule, positive_model)
    )
    grounded_defeasible_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance for rule in body_rules for instance in _ground_rule_instances(rule, positive_model)
    )
    grounded_defeater_rules: tuple[GroundDefeasibleRule, ...] = tuple(
        instance
        for rule in defeater_rules
        for instance in _ground_rule_instances(rule, positive_model)
    )

    return _GroundedTheory(
        fact_atoms=_fact_atoms(facts),
        grounded_strict_rules=grounded_strict_rules,
        grounded_defeasible_rules=grounded_defeasible_rules,
        grounded_defeater_rules=grounded_defeater_rules,
    )


def _force_strict_for_closure(rule: GroundDefeasibleRule) -> GroundDefeasibleRule:
    """Return a rule with ``kind="strict"`` so strict closure propagates it."""

    return GroundDefeasibleRule(
        rule_id=rule.rule_id,
        kind="strict",
        head=rule.head,
        body=rule.body,
    )


def _strict_rule_to_program_text(head: LiteralText, body: RuleBodyText) -> RuleText:
    if not body:
        return f"{head}."
    return f"{head} :- {', '.join(body)}."


def _atom_sort_key(atom: GroundAtom) -> tuple[str, FactTuple]:
    return atom.predicate, atom.arguments


def _fact_atoms(
    facts: FactModel,
) -> frozenset[GroundAtom]:
    return frozenset(
        GroundAtom(predicate=predicate, arguments=tuple(row))
        for predicate, rows in facts.items()
        for row in rows
    )


def _positive_closure_for_grounding(
    facts: FactModel,
    rules: list[DefeasibleRule],
) -> RelationModel:
    """Saturate facts positively to discover candidate grounding bindings."""

    model: RelationModel = {
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
    model: RelationModel,
) -> tuple[GroundDefeasibleRule, ...]:
    """Return all ground instances of ``rule`` under ``model``."""

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

    seen: dict[GroundRuleKey, GroundDefeasibleRule] = {}
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
    model: RelationModel,
) -> Bindings:
    """Enumerate head-only variable bindings over the constant universe."""

    constants = sorted(
        {value for relation in model.values() for row in relation for value in row},
        key=repr,
    )
    variables = [term.name for term in rule.head.terms if isinstance(term, Variable)]
    if not variables:
        return [{}]
    if not constants:
        return []
    return [
        {name: value for name, value in zip(variables, values, strict=True)}
        for values in product(constants, repeat=len(variables))
    ]


def _normalize_rules(rules: list[Rule]) -> list[Rule]:
    normalized: list[Rule] = []
    for rule in rules:
        if len(rule.heads) <= 1:
            normalized.append(rule)
            continue
        for head in rule.heads:
            normalized.append(
                Rule(
                    heads=(head,),
                    positive_body=rule.positive_body,
                    negative_body=rule.negative_body,
                    constraints=rule.constraints,
                    source_text=rule.source_text,
                )
            )
    return normalized


def _validate_program(
    facts: dict[str, set[FactTuple]],
    rules: list[Rule],
    negation_semantics: NegationSemantics = NegationSemantics.SAFE,
) -> None:
    arities: ArityMap = {}

    for predicate, rows in facts.items():
        row_arity = 0 if not rows else len(next(iter(rows)))
        _check_arity(arities, predicate, row_arity)
        for row in rows:
            if len(row) != row_arity:
                raise ArityMismatchError(f"Inconsistent fact arity for predicate {predicate}")

    for rule in rules:
        positive_vars: set[str] = set()
        bound_vars: set[str] = set()
        for atom in rule.positive_body:
            _check_arity(arities, atom.predicate, atom.arity)
            _validate_positive_atom(atom, bound_vars)
            atom_vars = _binding_variables_in_atom(atom)
            bound_vars |= atom_vars
            positive_vars |= atom_vars
        for atom in rule.negative_body:
            _check_arity(arities, atom.predicate, atom.arity)
            if (
                negation_semantics is NegationSemantics.SAFE
                and _variables_in_atom(atom) - positive_vars
            ):
                raise SafetyViolationError(
                    "Variables in negated literals must be positively bound "
                    "under NegationSemantics.SAFE"
                )
        for constraint in rule.constraints:
            if _variables_in_comparison(constraint) - positive_vars:
                raise UnboundVariableError("Constraint variables must be bound earlier")
        for head in rule.heads:
            _check_arity(arities, head.predicate, head.arity)
            _validate_head(head, positive_vars)


def _match_positive_body(
    atoms: tuple[Atom, ...],
    model: RelationModel,
) -> Bindings:
    return list(_iter_positive_body_matches(atoms, model))


def _iter_positive_body_matches(
    atoms: tuple[Atom, ...],
    model: RelationModel,
) -> Iterator[Binding]:
    return _iter_positive_body_matches_with_overrides(atoms, model, {})


def _iter_positive_body_matches_with_overrides(
    atoms: tuple[Atom, ...],
    model: RelationModel,
    overrides: RelationOverrides,
) -> Iterator[Binding]:
    if not atoms:
        yield {}
        return

    ordered_atoms = _order_positive_body(atoms, model, overrides)
    yield from _iter_positive_body_matches_from_ordered_atoms(
        ordered_atoms,
        model,
        overrides,
    )


def _iter_positive_body_matches_from_ordered_atoms(
    ordered_atoms: list[tuple[int, Atom]],
    model: RelationModel,
    overrides: RelationOverrides,
) -> Iterator[Binding]:
    compiled = compile_simple_matcher(ordered_atoms)
    if compiled is not None:
        yield from iter_compiled_bindings(compiled, model, overrides)
        return
    yield from _iter_generic_positive_body_matches(ordered_atoms, model, overrides)


def _iter_generic_positive_body_matches(
    ordered_atoms: list[tuple[int, Atom]],
    model: RelationModel,
    overrides: RelationOverrides,
) -> Iterator[Binding]:
    yield from _iter_matches_from(ordered_atoms, 0, {}, model, overrides)


def _iter_matches_from(
    ordered_atoms: list[tuple[int, Atom]],
    offset: int,
    binding: Binding,
    model: RelationModel,
    overrides: RelationOverrides,
) -> Iterator[Binding]:
    if offset >= len(ordered_atoms):
        yield dict(binding)
        return

    index, atom = ordered_atoms[offset]
    rows = overrides.get(index, model.get(atom.predicate, IndexedRelation()))
    for row in _matching_rows(atom, binding, rows):
        changes = _bind_row(atom, row, binding)
        if changes is None:
            continue
        yield from _iter_matches_from(ordered_atoms, offset + 1, binding, model, overrides)
        _rollback_binding(binding, changes)


def _order_positive_body(
    atoms: tuple[Atom, ...],
    model: RelationModel,
    overrides: RelationOverrides,
    preferred_first_index: int | None = None,
) -> list[tuple[int, Atom]]:
    remaining = list(enumerate(atoms))
    ordered: list[tuple[int, Atom]] = []
    bound_vars: set[str] = set()

    if preferred_first_index is not None:
        preferred = next(
            (item for item in remaining if item[0] == preferred_first_index),
            None,
        )
        if preferred is not None and _expression_variables_in_atom(preferred[1]) <= bound_vars:
            ordered.append(preferred)
            bound_vars |= _binding_variables_in_atom(preferred[1])
            remaining.remove(preferred)

    while remaining:
        ready = [item for item in remaining if _expression_variables_in_atom(item[1]) <= bound_vars]
        if not ready:
            ready = remaining
        chosen = min(
            ready,
            key=lambda item: _positive_atom_cost(item, bound_vars, model, overrides),
        )
        ordered.append(chosen)
        bound_vars |= _binding_variables_in_atom(chosen[1])
        remaining.remove(chosen)

    return ordered


def _positive_atom_cost(
    item: tuple[int, Atom],
    bound_vars: set[str],
    model: RelationModel,
    overrides: RelationOverrides,
) -> tuple[float, int, int, int, str]:
    index, atom = item
    rows = overrides.get(index, model.get(atom.predicate, IndexedRelation()))
    constrained_terms = 0
    bound_term_variables = 0
    lookup_columns: list[int] = []
    for term_index, term in enumerate(atom.terms):
        if isinstance(term, Constant):
            constrained_terms += 1
            lookup_columns.append(term_index)
            continue
        if isinstance(term, Wildcard):
            continue
        if isinstance(term, Variable):
            if term.name in bound_vars:
                constrained_terms += 1
                bound_term_variables += 1
                lookup_columns.append(term_index)
            continue
        if variables_in_term(term) <= bound_vars:
            constrained_terms += 1

    return (
        rows.estimated_lookup_size(tuple(lookup_columns)),
        len(rows),
        -constrained_terms,
        -bound_term_variables,
        atom.predicate,
    )


def _expression_variables_in_atom(atom: Atom) -> set[str]:
    variables: set[str] = set()
    for term in atom.terms:
        if isinstance(term, (AddExpression, SubtractExpression)):
            variables |= variables_in_term(term)
    return variables


def _negative_body_holds(
    atoms: tuple[Atom, ...],
    binding: Binding,
    model: RelationModel,
) -> bool:
    for atom in atoms:
        rows = model.get(atom.predicate, IndexedRelation())
        for row in _matching_rows(atom, binding, rows):
            if _unify(atom, row, binding) is not None:
                return False
    return True


_UNBOUND = object()


def _matching_rows(
    atom: Atom,
    binding: Binding,
    rows: IndexedRelation,
) -> IndexedRelation | set[tuple[object, ...]]:
    if not rows:
        return rows

    columns: list[int] = []
    values: list[object] = []
    for index, term in enumerate(atom.terms):
        value = _bound_term_value(term, binding)
        if value is _UNBOUND:
            continue
        columns.append(index)
        values.append(value)

    if not columns:
        return rows
    return rows.lookup(tuple(columns), tuple(values))


def _bound_term_value(term: AtomTerm, binding: Binding) -> object:
    if isinstance(term, Constant):
        return term.value
    if isinstance(term, Wildcard):
        return _UNBOUND
    if isinstance(term, Variable):
        return binding.get(term.name, _UNBOUND)

    value = _value_from_term(term, binding)
    if value is None:
        return _UNBOUND
    return value


def _bind_row(
    atom: Atom,
    row: tuple[object, ...],
    binding: Binding,
) -> list[str] | None:
    if len(row) != atom.arity:
        return None

    assigned: list[str] = []
    for term, value in zip(atom.terms, row, strict=True):
        if isinstance(term, Constant):
            if not values_equal(term.value, value):
                _rollback_binding(binding, assigned)
                return None
            continue
        if isinstance(term, Wildcard):
            continue
        if isinstance(term, Variable):
            existing = binding.get(term.name, _UNBOUND)
            if existing is _UNBOUND:
                binding[term.name] = value
                assigned.append(term.name)
            elif not values_equal(existing, value):
                _rollback_binding(binding, assigned)
                return None
            continue
        if not _expression_matches(term, value, binding):
            _rollback_binding(binding, assigned)
            return None
    return assigned


def _rollback_binding(binding: Binding, assigned: list[str]) -> None:
    for name in reversed(assigned):
        del binding[name]


def _unify(
    atom: Atom,
    row: tuple[object, ...],
    binding: Binding,
) -> Binding | None:
    if len(row) != atom.arity:
        return None

    candidate = dict(binding)
    for term, value in zip(atom.terms, row, strict=True):
        if isinstance(term, Constant):
            if not values_equal(term.value, value):
                return None
            continue
        if isinstance(term, Wildcard):
            continue
        if isinstance(term, Variable):
            existing = candidate.get(term.name, _UNBOUND)
            if existing is _UNBOUND:
                candidate[term.name] = value
            elif not values_equal(existing, value):
                return None
            continue
        if not _expression_matches(term, value, candidate):
            return None
    return candidate


def _expression_matches(
    term: AddExpression | SubtractExpression,
    value: object,
    binding: Binding,
) -> bool:
    try:
        return values_equal(_value_from_term(term, binding), value)
    except SemanticError:
        return False


def _value_from_term(term: AtomTerm, binding: Binding) -> object | None:
    if isinstance(term, Constant):
        return term.value
    if isinstance(term, Variable):
        return binding.get(term.name)
    if isinstance(term, Wildcard):
        return None
    left = _value_from_term(term.left, binding)
    right = _value_from_term(term.right, binding)
    if left is None or right is None:
        return None
    if isinstance(term, SubtractExpression):
        try:
            return subtract_values(left, right)
        except SemanticError:
            return None
    try:
        return add_values(left, right)
    except SemanticError:
        return None


def _variables_in_atom(atom: Atom) -> set[str]:
    variables: set[str] = set()
    for term in atom.terms:
        variables |= variables_in_term(term)
    return variables


def _validate_head(head: Atom, positive_vars: set[str]) -> None:
    for term in head.terms:
        if isinstance(term, Wildcard):
            raise SafetyViolationError("Wildcards are not allowed in rule heads")
        if variables_in_term(term) - positive_vars:
            raise UnboundVariableError("Head variables must be bound by positive literals")


def _validate_positive_atom(atom: Atom, bound_vars: set[str]) -> None:
    for term in atom.terms:
        if isinstance(term, (AddExpression, SubtractExpression)) and (
            variables_in_term(term) - bound_vars
        ):
            raise UnboundVariableError("Expression variables must be bound earlier in the body")


def _binding_variables_in_atom(atom: Atom) -> set[str]:
    return {term.name for term in atom.terms if isinstance(term, Variable)}


def _variables_in_comparison(comparison: Comparison) -> set[str]:
    return variables_in_term(comparison.left) | variables_in_term(comparison.right)


def _constraints_hold(
    constraints: tuple[Comparison, ...],
    binding: Binding,
) -> bool:
    for comparison in constraints:
        left = _value_from_term(comparison.left, binding)
        right = _value_from_term(comparison.right, binding)
        if left is None or right is None:
            return False
        try:
            if not compare_values(left, comparison.operator, right):
                return False
        except SemanticError:
            return False
    return True


def _check_arity(arities: ArityMap, predicate: str, arity: int) -> None:
    existing = arities.get(predicate)
    if existing is None:
        arities[predicate] = arity
        return
    if existing != arity:
        raise ArityMismatchError(f"Predicate {predicate} has inconsistent arity")


def _apply_rule_with_overrides(
    rule: Rule,
    model: RelationModel,
    delta: RelationModel,
    overrides: RelationOverrides,
    preferred_first_index: int | None,
    iteration_trace: IterationTrace | None,
) -> int:
    from .evaluator import _apply_rule_with_overrides as apply_rule_with_overrides

    return apply_rule_with_overrides(
        rule,
        model,
        delta,
        overrides,
        preferred_first_index,
        iteration_trace,
    )
