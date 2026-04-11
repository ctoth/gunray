"""Bottom-up Datalog evaluation for the conformance-suite program schema."""

from __future__ import annotations

from datalog_conformance.schema import Model, Program as SchemaProgram

from .errors import ArityMismatchError, SafetyViolationError, UnboundVariableError
from .parser import ground_atom, parse_program
from .semantics import (
    SemanticError,
    add_values,
    compare_values,
    subtract_values,
    values_equal,
)
from .stratify import stratify
from .types import (
    AddExpression,
    Atom,
    AtomTerm,
    Comparison,
    Constant,
    Rule,
    SubtractExpression,
    Variable,
    Wildcard,
)
from .types import variables_in_term


class SemiNaiveEvaluator:
    """Evaluate stratified Datalog programs under standard least-model semantics."""

    def evaluate(self, program: SchemaProgram) -> Model:
        facts, parsed_rules = parse_program(program)
        rules = _normalize_rules(parsed_rules)
        _validate_program(facts, rules)
        strata = stratify(rules)

        model = {predicate: set(rows) for predicate, rows in facts.items()}
        for predicates in strata:
            stratum_rules = [
                rule for rule in rules if rule.heads[0].predicate in predicates
            ]
            _evaluate_stratum(model, stratum_rules)

        return Model(facts=model)


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


def _validate_program(facts: dict[str, set[tuple[object, ...]]], rules: list[Rule]) -> None:
    arities: dict[str, int] = {}

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
        head_vars = set().union(*(_variables_in_atom(head) for head in rule.heads)) if rule.heads else set()
        constraint_vars = set().union(
            *(_variables_in_comparison(constraint) for constraint in rule.constraints)
        ) if rule.constraints else set()
        for atom in rule.negative_body:
            _check_arity(arities, atom.predicate, atom.arity)
            shared_negative_vars = set().union(
                *(
                    _variables_in_atom(other)
                    for other in rule.negative_body
                    if other is not atom
                )
            ) if len(rule.negative_body) > 1 else set()
            required_positive_vars = _variables_in_atom(atom) & (
                positive_vars | head_vars | constraint_vars | shared_negative_vars
            )
            if required_positive_vars - positive_vars:
                raise SafetyViolationError("Variables in negated literals must be positively bound")
        for constraint in rule.constraints:
            if _variables_in_comparison(constraint) - positive_vars:
                raise UnboundVariableError("Constraint variables must be bound earlier")
        for head in rule.heads:
            _check_arity(arities, head.predicate, head.arity)
            _validate_head(head, positive_vars)


def _evaluate_stratum(
    model: dict[str, set[tuple[object, ...]]],
    rules: list[Rule],
) -> None:
    while True:
        changed = False
        for rule in rules:
            bindings = _match_positive_body(rule.positive_body, model)
            for binding in bindings:
                if not _constraints_hold(rule.constraints, binding):
                    continue
                if not _negative_body_holds(rule.negative_body, binding, model):
                    continue
                derived = ground_atom(rule.heads[0], binding)
                bucket = model.setdefault(derived.predicate, set())
                if derived.arguments not in bucket:
                    bucket.add(derived.arguments)
                    changed = True
        if not changed:
            return


def _match_positive_body(
    atoms: tuple[Atom, ...],
    model: dict[str, set[tuple[object, ...]]],
) -> list[dict[str, object]]:
    if not atoms:
        return [{}]

    bindings: list[dict[str, object]] = [{}]
    for atom in atoms:
        next_bindings: list[dict[str, object]] = []
        rows = model.get(atom.predicate, set())
        for binding in bindings:
            for row in rows:
                candidate = _unify(atom, row, binding)
                if candidate is not None:
                    next_bindings.append(candidate)
        bindings = next_bindings
        if not bindings:
            return []
    return bindings


def _negative_body_holds(
    atoms: tuple[Atom, ...],
    binding: dict[str, object],
    model: dict[str, set[tuple[object, ...]]],
) -> bool:
    for atom in atoms:
        rows = model.get(atom.predicate, set())
        for row in rows:
            if _unify(atom, row, binding) is not None:
                return False
    return True


def _unify(
    atom: Atom,
    row: tuple[object, ...],
    binding: dict[str, object],
) -> dict[str, object] | None:
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
            existing = candidate.get(term.name)
            if existing is None:
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
    binding: dict[str, object],
) -> bool:
    try:
        return values_equal(_value_from_term(term, binding), value)
    except SemanticError:
        return False


def _value_from_term(term: AtomTerm, binding: dict[str, object]) -> object | None:
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
        if isinstance(term, (AddExpression, SubtractExpression)) and variables_in_term(term) - bound_vars:
            raise UnboundVariableError("Expression variables must be bound earlier in the body")


def _binding_variables_in_atom(atom: Atom) -> set[str]:
    return {term.name for term in atom.terms if isinstance(term, Variable)}


def _variables_in_comparison(comparison: Comparison) -> set[str]:
    return variables_in_term(comparison.left) | variables_in_term(comparison.right)


def _constraints_hold(
    constraints: tuple[Comparison, ...],
    binding: dict[str, object],
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


def _check_arity(arities: dict[str, int], predicate: str, arity: int) -> None:
    existing = arities.get(predicate)
    if existing is None:
        arities[predicate] = arity
        return
    if existing != arity:
        raise ArityMismatchError(f"Predicate {predicate} has inconsistent arity")
