"""Bottom-up Datalog evaluation for the Gunray program schema."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import cast

from .compiled import (
    CompiledSimpleRule,
    compile_simple_matcher,
    compile_simple_rule,
    iter_compiled_bindings,
    iter_compiled_head_rows,
)
from .errors import ArityMismatchError, SafetyViolationError, UnboundVariableError
from .parser import ground_atom, parse_program
from .relation import IndexedRelation
from .schema import FactTuple, Model
from .schema import Program as SchemaProgram
from .semantics import (
    SemanticError,
    add_values,
    compare_values,
    subtract_values,
    values_equal,
)
from .stratify import stratify
from .trace import DatalogTrace, IterationTrace, RuleFireTrace, StratumTrace, TraceConfig
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
    variables_in_term,
)


class SemiNaiveEvaluator:
    """Evaluate stratified Datalog programs under standard least-model semantics."""

    def evaluate(self, program: SchemaProgram) -> Model:
        model, _ = self.evaluate_with_trace(program)
        return model

    def evaluate_with_trace(
        self,
        program: SchemaProgram,
        trace_config: TraceConfig | None = None,
    ) -> tuple[Model, DatalogTrace]:
        facts, parsed_rules = parse_program(program)
        rules = _normalize_rules(parsed_rules)
        _validate_program(facts, rules)
        strata = stratify(rules)
        actual_trace_config = trace_config or TraceConfig()
        trace = DatalogTrace(config=actual_trace_config)

        model = {predicate: IndexedRelation(rows) for predicate, rows in facts.items()}
        for predicates in strata:
            stratum_rules = [rule for rule in rules if rule.heads[0].predicate in predicates]
            _evaluate_stratum(model, stratum_rules, trace, actual_trace_config)

        return Model(
            facts={
                predicate: cast(set[FactTuple], relation.as_set())
                for predicate, relation in model.items()
            }
        ), trace


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


def _validate_program(facts: dict[str, set[FactTuple]], rules: list[Rule]) -> None:
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
        for atom in rule.negative_body:
            _check_arity(arities, atom.predicate, atom.arity)
        for constraint in rule.constraints:
            if _variables_in_comparison(constraint) - positive_vars:
                raise UnboundVariableError("Constraint variables must be bound earlier")
        for head in rule.heads:
            _check_arity(arities, head.predicate, head.arity)
            _validate_head(head, positive_vars)


def _evaluate_stratum(
    model: dict[str, IndexedRelation],
    rules: list[Rule],
    trace: DatalogTrace | None = None,
    trace_config: TraceConfig | None = None,
) -> None:
    actual_trace_config = trace_config or TraceConfig()
    stratum_predicates = {rule.heads[0].predicate for rule in rules}
    stratum_trace = StratumTrace(predicates=tuple(sorted(stratum_predicates)))
    if trace is not None:
        trace.strata.append(stratum_trace)

    delta = {
        predicate: IndexedRelation(model.get(predicate, IndexedRelation()).as_set())
        for predicate in stratum_predicates
    }
    first_iteration = True
    iteration_number = 0
    while first_iteration or any(delta_relation for delta_relation in delta.values()):
        iteration_number += 1
        next_delta = {predicate: IndexedRelation() for predicate in stratum_predicates}
        iteration_trace = IterationTrace(
            iteration=iteration_number,
            delta_sizes={predicate: len(rows) for predicate, rows in delta.items() if len(rows)},
        )
        stratum_trace.iterations.append(iteration_trace)
        previous_only = {
            predicate: model.get(predicate, IndexedRelation()).difference(delta_relation)
            for predicate, delta_relation in delta.items()
        }
        for rule in rules:
            recursive_positions = [
                index
                for index, atom in enumerate(rule.positive_body)
                if atom.predicate in stratum_predicates
            ]
            for delta_offset, delta_position in enumerate(recursive_positions):
                atom = rule.positive_body[delta_position]
                delta_rows = delta.get(atom.predicate)
                if delta_rows is None or not delta_rows:
                    continue
                overrides = {delta_position: delta_rows}
                for earlier_position in recursive_positions[:delta_offset]:
                    earlier_atom = rule.positive_body[earlier_position]
                    overrides[earlier_position] = previous_only[earlier_atom.predicate]
                _apply_rule_with_overrides(
                    rule,
                    model,
                    next_delta,
                    overrides,
                    preferred_first_index=delta_position,
                    iteration_trace=iteration_trace,
                    trace_config=actual_trace_config,
                )
            if recursive_positions or not first_iteration:
                continue
            _apply_rule_with_overrides(
                rule,
                model,
                next_delta,
                {},
                preferred_first_index=None,
                iteration_trace=iteration_trace,
                trace_config=actual_trace_config,
            )
        if not any(delta_relation for delta_relation in next_delta.values()):
            return
        for predicate, rows in next_delta.items():
            bucket = model.setdefault(predicate, IndexedRelation())
            for row in rows:
                bucket.add(row)
        delta = next_delta
        first_iteration = False


def _apply_rule(
    rule: Rule,
    model: dict[str, IndexedRelation],
    delta: dict[str, IndexedRelation],
    bindings: Iterable[dict[str, object]],
    trace_config: TraceConfig | None = None,
) -> tuple[int, tuple[tuple[object, ...], ...]]:
    actual_trace_config = trace_config or TraceConfig()
    derived_count = 0
    captured_rows: list[tuple[object, ...]] = []
    for binding in bindings:
        if not _constraints_hold(rule.constraints, binding):
            continue
        if not _negative_body_holds(rule.negative_body, binding, model):
            continue
        derived = ground_atom(rule.heads[0], binding)
        if derived.arguments in model.get(derived.predicate, IndexedRelation()):
            continue
        delta_bucket = delta.setdefault(derived.predicate, IndexedRelation())
        if delta_bucket.add(derived.arguments):
            derived_count += 1
            _capture_derived_row(captured_rows, derived.arguments, actual_trace_config)
    return derived_count, tuple(captured_rows)


def _apply_rule_with_overrides(
    rule: Rule,
    model: dict[str, IndexedRelation],
    delta: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
    preferred_first_index: int | None,
    iteration_trace: IterationTrace | None,
    trace_config: TraceConfig | None = None,
) -> int:
    actual_trace_config = trace_config or TraceConfig()
    ordered_atoms = _order_positive_body(
        rule.positive_body,
        model,
        overrides,
        preferred_first_index=preferred_first_index,
    )
    if not rule.negative_body and not rule.constraints:
        compiled_rule = compile_simple_rule(rule.heads[0], ordered_atoms)
        if compiled_rule is not None:
            derived_count, captured_rows = _apply_compiled_rule(
                compiled_rule,
                model,
                delta,
                overrides,
                actual_trace_config,
            )
            _record_rule_fire(
                iteration_trace,
                rule.source_text,
                rule.heads[0].predicate,
                preferred_first_index,
                derived_count,
                captured_rows,
            )
            return derived_count
    bindings = _iter_positive_body_matches_from_ordered_atoms(
        ordered_atoms,
        model,
        overrides,
    )
    derived_count, captured_rows = _apply_rule(
        rule,
        model,
        delta,
        bindings,
        actual_trace_config,
    )
    _record_rule_fire(
        iteration_trace,
        rule.source_text,
        rule.heads[0].predicate,
        preferred_first_index,
        derived_count,
        captured_rows,
    )
    return derived_count


def _apply_compiled_rule(
    compiled_rule: CompiledSimpleRule,
    model: dict[str, IndexedRelation],
    delta: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
    trace_config: TraceConfig | None = None,
) -> tuple[int, tuple[tuple[object, ...], ...]]:
    actual_trace_config = trace_config or TraceConfig()
    head_rows = model.get(compiled_rule.head_predicate, IndexedRelation())
    delta_bucket = delta.setdefault(compiled_rule.head_predicate, IndexedRelation())
    derived_count = 0
    captured_rows: list[tuple[object, ...]] = []
    for row in iter_compiled_head_rows(compiled_rule, model, overrides):
        if row in head_rows:
            continue
        if delta_bucket.add(row):
            derived_count += 1
            _capture_derived_row(captured_rows, row, actual_trace_config)
    return derived_count, tuple(captured_rows)


def _match_positive_body(
    atoms: tuple[Atom, ...],
    model: dict[str, IndexedRelation],
) -> list[dict[str, object]]:
    return list(_iter_positive_body_matches(atoms, model))


def _iter_positive_body_matches(
    atoms: tuple[Atom, ...],
    model: dict[str, IndexedRelation],
) -> Iterator[dict[str, object]]:
    return _iter_positive_body_matches_with_overrides(atoms, model, {})


def _iter_positive_body_matches_with_overrides(
    atoms: tuple[Atom, ...],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
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
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
    compiled = compile_simple_matcher(ordered_atoms)
    if compiled is not None:
        yield from iter_compiled_bindings(compiled, model, overrides)
        return
    yield from _iter_generic_positive_body_matches(ordered_atoms, model, overrides)


def _iter_generic_positive_body_matches(
    ordered_atoms: list[tuple[int, Atom]],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
    yield from _iter_matches_from(
        ordered_atoms,
        0,
        {},
        model,
        overrides,
    )


def _record_rule_fire(
    iteration_trace: IterationTrace | None,
    rule_text: str,
    head_predicate: str,
    delta_position: int | None,
    derived_count: int,
    derived_rows: tuple[tuple[object, ...], ...],
) -> None:
    if iteration_trace is None:
        return
    iteration_trace.rule_fires.append(
        RuleFireTrace(
            rule_text=rule_text,
            head_predicate=head_predicate,
            delta_position=delta_position,
            derived_count=derived_count,
            derived_rows=derived_rows,
        )
    )


def _capture_derived_row(
    captured_rows: list[tuple[object, ...]],
    row: tuple[object, ...],
    trace_config: TraceConfig,
) -> None:
    if not trace_config.capture_derived_rows:
        return
    if trace_config.max_derived_rows_per_rule_fire <= 0:
        return
    if len(captured_rows) >= trace_config.max_derived_rows_per_rule_fire:
        return
    captured_rows.append(row)


def _iter_matches_from(
    ordered_atoms: list[tuple[int, Atom]],
    offset: int,
    binding: dict[str, object],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
    if offset >= len(ordered_atoms):
        yield dict(binding)
        return

    index, atom = ordered_atoms[offset]
    rows = overrides.get(index, model.get(atom.predicate, IndexedRelation()))
    for row in _matching_rows(atom, binding, rows):
        changes = _bind_row(atom, row, binding)
        if changes is None:
            continue
        yield from _iter_matches_from(
            ordered_atoms,
            offset + 1,
            binding,
            model,
            overrides,
        )
        _rollback_binding(binding, changes)


def _order_positive_body(
    atoms: tuple[Atom, ...],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
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
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
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
        rows.average_lookup_size(tuple(lookup_columns)),
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
    binding: dict[str, object],
    model: dict[str, IndexedRelation],
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
    binding: dict[str, object],
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


def _bound_term_value(term: AtomTerm, binding: dict[str, object]) -> object:
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
    binding: dict[str, object],
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


def _rollback_binding(binding: dict[str, object], assigned: list[str]) -> None:
    for name in reversed(assigned):
        del binding[name]


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
