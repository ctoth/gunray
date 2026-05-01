"""Package-internal helpers shared across Gunray modules."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import TypeAlias, cast, overload

from .anytime import EnumerationExceeded
from .compiled import compile_simple_matcher, iter_compiled_bindings
from .errors import ArityMismatchError, SafetyViolationError, UnboundVariableError
from .grounding_types import (
    GroundingInspection,
    GroundingSubstitution,
    GroundRuleInstance,
    GroundRuleKind,
)
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
BindingEnumeration: TypeAlias = Bindings | EnumerationExceeded
RelationModel: TypeAlias = dict[str, IndexedRelation]
RelationOverrides: TypeAlias = dict[int, IndexedRelation]
ArityMap: TypeAlias = dict[str, int]
GroundRuleKey: TypeAlias = tuple[str, tuple[object, ...]]
FactRows: TypeAlias = set[tuple[Scalar, ...]]
FactModel: TypeAlias = Mapping[str, FactRows]
LiteralText: TypeAlias = str
RuleBodyText: TypeAlias = Sequence[LiteralText]
RuleText: TypeAlias = str


@dataclass(frozen=True, slots=True)
class _GroundedTheory:
    """Grounded fact atoms and per-kind ground rule tuples."""

    fact_atoms: frozenset[GroundAtom]
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...]
    grounded_defeasible_rules: tuple[GroundDefeasibleRule, ...]
    grounded_defeater_rules: tuple[GroundDefeasibleRule, ...]
    conflicts: frozenset[tuple[str, str]]
    inspection: GroundingInspection


@dataclass(frozen=True, slots=True)
class _GroundRuleInstance:
    """Ground rule plus the binding that produced it."""

    rule: GroundDefeasibleRule
    substitution: tuple[tuple[str, object], ...]


def _ground_theory(theory: SchemaDefeasibleTheory) -> _GroundedTheory:
    """Parse, ground, and bucket every rule of ``theory`` by kind."""

    facts, defeasible_rules, conflicts = parse_defeasible_theory(theory)
    strict_rules = tuple(r for r in defeasible_rules if r.kind == "strict")
    body_rules = tuple(r for r in defeasible_rules if r.kind == "defeasible")
    defeater_rules = tuple(r for r in defeasible_rules if r.kind == "defeater")

    positive_model = _positive_closure_for_grounding(facts, defeasible_rules)

    strict_instances = tuple(
        instance
        for rule in strict_rules
        for instance in _ground_rule_instances_with_substitutions(rule, positive_model)
    )
    defeasible_instances = tuple(
        instance
        for rule in body_rules
        for instance in _ground_rule_instances_with_substitutions(rule, positive_model)
    )
    defeater_instances = tuple(
        instance
        for rule in defeater_rules
        for instance in _ground_rule_instances_with_substitutions(rule, positive_model)
    )

    fact_atoms = _fact_atoms(facts)
    public_strict = tuple(
        sorted(
            (_public_ground_rule_instance(item) for item in strict_instances),
            key=_instance_sort_key,
        )
    )
    public_defeasible = tuple(
        sorted(
            (_public_ground_rule_instance(item) for item in defeasible_instances),
            key=_instance_sort_key,
        )
    )
    public_defeater = tuple(
        sorted(
            (_public_ground_rule_instance(item) for item in defeater_instances),
            key=_instance_sort_key,
        )
    )

    return _GroundedTheory(
        fact_atoms=fact_atoms,
        grounded_strict_rules=tuple(instance.rule for instance in strict_instances),
        grounded_defeasible_rules=tuple(instance.rule for instance in defeasible_instances),
        grounded_defeater_rules=tuple(instance.rule for instance in defeater_instances),
        conflicts=frozenset(conflicts),
        inspection=GroundingInspection(
            fact_atoms=tuple(sorted(fact_atoms, key=_atom_sort_key)),
            strict_rules=public_strict,
            defeasible_rules=public_defeasible,
            defeater_rules=public_defeater,
            simplification=_simplify_strict_fact_grounding(
                tuple(sorted(fact_atoms, key=_atom_sort_key)),
                public_strict,
                public_defeasible,
                public_defeater,
                _compute_non_approximated(theory),
            ),
        ),
    )


def _public_ground_rule_instance(instance: _GroundRuleInstance) -> GroundRuleInstance:
    return GroundRuleInstance(
        rule_id=instance.rule.rule_id,
        kind=cast(GroundRuleKind, instance.rule.kind),
        head=instance.rule.head,
        body=instance.rule.body,
        substitution=_public_substitution(instance.substitution),
        default_negated_body=instance.rule.default_negated_body,
    )


def _public_substitution(
    substitution: tuple[tuple[str, object], ...],
) -> GroundingSubstitution:
    return tuple((name, cast(Scalar, value)) for name, value in substitution)


def _instance_sort_key(
    instance: GroundRuleInstance,
) -> tuple[str, GroundRuleKind, tuple[str, FactTuple], GroundingSubstitution]:
    return instance.rule_id, instance.kind, _atom_sort_key(instance.head), instance.substitution


def _simplify_strict_fact_grounding(
    fact_atoms: tuple[GroundAtom, ...],
    strict_rules: tuple[GroundRuleInstance, ...],
    defeasible_rules: tuple[GroundRuleInstance, ...],
    defeater_rules: tuple[GroundRuleInstance, ...],
    non_approximated_predicates: frozenset[str],
):
    from .grounding import _simplify_strict_fact_grounding as simplify

    return simplify(
        fact_atoms,
        strict_rules,
        defeasible_rules,
        defeater_rules,
        non_approximated_predicates,
    )


def _compute_non_approximated(theory: SchemaDefeasibleTheory) -> frozenset[str]:
    from .grounding import compute_non_approximated

    return compute_non_approximated(theory)


def _force_strict_for_closure(rule: GroundDefeasibleRule) -> GroundDefeasibleRule:
    """Return a rule with ``kind="strict"`` so strict closure propagates it."""

    return GroundDefeasibleRule(
        rule_id=rule.rule_id,
        kind="strict",
        head=rule.head,
        body=rule.body,
        default_negated_body=(),
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

    model: RelationModel = {predicate: IndexedRelation(rows) for predicate, rows in facts.items()}
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
    for atom in rule.default_negated_body:
        for term in atom.terms:
            names |= variables_in_term(term)
    return sorted(names)


def _ground_rule_instances(
    rule: DefeasibleRule,
    model: RelationModel,
) -> tuple[GroundDefeasibleRule, ...]:
    """Return all ground instances of ``rule`` under ``model``."""

    return tuple(
        instance.rule for instance in _ground_rule_instances_with_substitutions(rule, model)
    )


def _ground_rule_instances_with_substitutions(
    rule: DefeasibleRule,
    model: RelationModel,
) -> tuple[_GroundRuleInstance, ...]:
    """Return all ground instances of ``rule`` with their grounding substitutions."""

    variables = _rule_variable_names(rule)
    if not variables:
        head = ground_atom(rule.head, {})
        body = tuple(ground_atom(atom, {}) for atom in rule.body)
        default_negated_body = tuple(ground_atom(atom, {}) for atom in rule.default_negated_body)
        return (
            _GroundRuleInstance(
                rule=GroundDefeasibleRule(
                    rule_id=rule.rule_id,
                    kind=rule.kind,
                    head=head,
                    body=body,
                    default_negated_body=default_negated_body,
                ),
                substitution=(),
            ),
        )

    if rule.body:
        bindings = _match_positive_body(rule.body, model)
    else:
        bindings = _head_only_bindings(rule, model)

    seen: dict[GroundRuleKey, _GroundRuleInstance] = {}
    for binding in bindings:
        try:
            head = ground_atom(rule.head, binding)
        except KeyError:
            continue
        try:
            body = tuple(ground_atom(atom, binding) for atom in rule.body)
        except KeyError:
            continue
        try:
            default_negated_body = tuple(
                ground_atom(atom, binding) for atom in rule.default_negated_body
            )
        except KeyError:
            continue
        key = (rule.rule_id, head.arguments)
        seen[key] = _GroundRuleInstance(
            rule=GroundDefeasibleRule(
                rule_id=rule.rule_id,
                kind=rule.kind,
                head=head,
                body=body,
                default_negated_body=default_negated_body,
            ),
            substitution=tuple(sorted(binding.items())),
        )
    return tuple(seen.values())


@overload
def _head_only_bindings(
    rule: DefeasibleRule,
    model: RelationModel,
) -> Bindings: ...


@overload
def _head_only_bindings(
    rule: DefeasibleRule,
    model: RelationModel,
    *,
    max_candidates: None,
) -> Bindings: ...


@overload
def _head_only_bindings(
    rule: DefeasibleRule,
    model: RelationModel,
    *,
    max_candidates: int,
) -> BindingEnumeration: ...


def _head_only_bindings(
    rule: DefeasibleRule,
    model: RelationModel,
    *,
    max_candidates: int | None = None,
) -> BindingEnumeration:
    """Enumerate head-only bindings with an anytime candidate ceiling.

    Zilberstein 1996 treats resource-bounded enumeration as an anytime
    computation: once the caller-supplied bound is exceeded, return the
    exact amount completed and mark the unenumerated remainder vacuous.
    """

    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative")

    constants = sorted(
        {value for relation in model.values() for row in relation for value in row},
        key=repr,
    )
    variables = [term.name for term in rule.head.terms if isinstance(term, Variable)]
    if not variables:
        return [{}]
    if not constants:
        return []

    bindings: Bindings = []
    for values in product(constants, repeat=len(variables)):
        if max_candidates is not None and len(bindings) >= max_candidates:
            return EnumerationExceeded(
                partial_arguments=(),
                max_arguments=max_candidates,
                partial_count=len(bindings),
                reason=(
                    "head-only binding enumeration budget exceeded: "
                    f"{len(bindings)} candidates produced of {max_candidates} allowed"
                ),
            )
        bindings.append({name: value for name, value in zip(variables, values, strict=True)})
    return bindings


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
    from .evaluator import apply_rule_with_overrides

    return apply_rule_with_overrides(
        rule,
        model,
        delta,
        overrides,
        preferred_first_index,
        iteration_trace,
    )
