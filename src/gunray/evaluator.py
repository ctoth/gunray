"""Bottom-up Datalog evaluation for the Gunray program schema."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from ._internal import (
    _constraints_hold,
    _iter_positive_body_matches_from_ordered_atoms,
    _negative_body_holds,
    _normalize_rules,
    _order_positive_body,
    _validate_program,
)
from .compiled import (
    CompiledSimpleRule,
    compile_simple_rule,
    iter_compiled_head_rows,
)
from .parser import ground_atom, parse_program
from .relation import IndexedRelation
from .schema import FactTuple, Model, NegationSemantics
from .schema import Program as SchemaProgram
from .stratify import stratify
from .trace import DatalogTrace, IterationTrace, RuleFireTrace, StratumTrace, TraceConfig
from .types import Rule


class SemiNaiveEvaluator:
    """Evaluate stratified Datalog programs under standard least-model semantics."""

    def evaluate(
        self,
        program: SchemaProgram,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> Model:
        model, _ = self.evaluate_with_trace(
            program,
            negation_semantics=negation_semantics,
        )
        return model

    def evaluate_with_trace(
        self,
        program: SchemaProgram,
        trace_config: TraceConfig | None = None,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> tuple[Model, DatalogTrace]:
        facts, parsed_rules = parse_program(program)
        rules = _normalize_rules(parsed_rules)
        _validate_program(facts, rules, negation_semantics)
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

