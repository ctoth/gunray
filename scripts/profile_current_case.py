from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import cast

import yaml

from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.schema import Program as SchemaProgram
from datalog_conformance.schema import TestCase

from gunray.defeasible import _strict_rule_to_program_text
from gunray.evaluator import (
    _apply_rule,
    _apply_rule_with_overrides,
    _iter_positive_body_matches,
    _iter_positive_body_matches_with_overrides,
    _normalize_rules,
    _validate_program,
)
from gunray.parser import parse_program
from gunray.relation import IndexedRelation
from gunray.stratify import stratify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("--yaml", required=True)
    parser.add_argument("--max-seconds", type=float, default=120.0)
    parser.add_argument("--slow-ms", type=float, default=250.0)
    args = parser.parse_args()

    case = _load_case(args.case, args.yaml)
    program = _case_program(case)
    facts, parsed_rules = parse_program(program)
    rules = _normalize_rules(parsed_rules)
    _validate_program(facts, rules)
    strata = stratify(rules)

    model = {predicate: IndexedRelation(rows) for predicate, rows in facts.items()}
    started = time.perf_counter()

    print(f"case: {case.name}")
    for stratum_index, predicates in enumerate(strata):
        stratum_rules = [rule for rule in rules if rule.heads[0].predicate in predicates]
        print(f"stratum {stratum_index} predicates={sorted(predicates)} rules={len(stratum_rules)}")
        _profile_stratum(
            model=model,
            rules=stratum_rules,
            started=started,
            max_seconds=args.max_seconds,
            slow_ms=args.slow_ms,
        )
    print("completed")
    return 0


def _profile_stratum(
    *,
    model: dict[str, IndexedRelation],
    rules,
    started: float,
    max_seconds: float,
    slow_ms: float,
) -> None:
    stratum_predicates = {rule.heads[0].predicate for rule in rules}
    delta = {
        predicate: IndexedRelation(model.get(predicate, IndexedRelation()).as_set())
        for predicate in stratum_predicates
    }
    first_iteration = True
    iteration = 0
    while first_iteration or any(delta_relation for delta_relation in delta.values()):
        iteration += 1
        next_delta = {predicate: IndexedRelation() for predicate in stratum_predicates}
        previous_only = {
            predicate: model.get(predicate, IndexedRelation()).difference(delta_relation)
            for predicate, delta_relation in delta.items()
        }
        print(
            "iteration"
            f" {iteration} delta_sizes="
            f"{ {predicate: len(rows) for predicate, rows in delta.items() if len(rows)} }"
        )
        for rule_index, rule in enumerate(rules, start=1):
            elapsed = time.perf_counter() - started
            if elapsed > max_seconds:
                raise SystemExit(
                    f"aborting after {elapsed:.2f}s at iteration {iteration}, rule {rule_index}: {rule.source_text}"
                )

            recursive_positions = [
                index
                for index, atom in enumerate(rule.positive_body)
                if atom.predicate in stratum_predicates
            ]
            rule_started = time.perf_counter()
            before_sizes = {
                predicate: len(rows)
                for predicate, rows in next_delta.items()
            }
            if recursive_positions:
                for delta_position in recursive_positions:
                    atom = rule.positive_body[delta_position]
                    delta_rows = delta.get(atom.predicate)
                    if delta_rows is None or not delta_rows:
                        continue
                    overrides = {delta_position: delta_rows}
                    for earlier_position in recursive_positions:
                        if earlier_position == delta_position:
                            break
                        earlier_atom = rule.positive_body[earlier_position]
                        overrides[earlier_position] = previous_only[earlier_atom.predicate]
                    _apply_rule_with_overrides(
                        rule,
                        model,
                        next_delta,
                        overrides,
                        preferred_first_index=delta_position,
                    )
            elif first_iteration:
                _apply_rule_with_overrides(
                    rule,
                    model,
                    next_delta,
                    {},
                    preferred_first_index=None,
                )
            rule_ms = (time.perf_counter() - rule_started) * 1000.0
            added_rows = {
                predicate: len(rows) - before_sizes[predicate]
                for predicate, rows in next_delta.items()
                if len(rows) - before_sizes[predicate] > 0
            }
            if rule_ms >= slow_ms:
                print(
                    f"slow rule {rule_ms:.1f}ms"
                    f" added_rows={added_rows}"
                    f" next_delta_sizes={ {predicate: len(rows) for predicate, rows in next_delta.items() if len(rows)} }"
                    f" text={rule.source_text}"
                )

        if not any(delta_relation for delta_relation in next_delta.values()):
            return
        for predicate, rows in next_delta.items():
            bucket = model.setdefault(predicate, IndexedRelation())
            for row in rows:
                bucket.add(row)
        delta = next_delta
        first_iteration = False


def _load_case(name: str, yaml_relpath: str) -> TestCase:
    package_tests_dir = get_tests_dir()
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root.parent / "datalog-conformance-suite" / "src" / "datalog_conformance" / "_tests"
    if not tests_dir.exists():
        tests_dir = package_tests_dir
    yaml_path = tests_dir / yaml_relpath
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"{yaml_path} did not load to a YAML mapping")
    if "tests" in raw:
        cases = _load_multi_case_file(cast(dict[object, object], raw), yaml_path)
    else:
        cases = [TestCase.from_dict(raw)]
    matches = [case for case in cases if case.name == name]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one case named {name!r} in {yaml_path}")
    return matches[0]


def _case_program(case: TestCase) -> SchemaProgram:
    if case.program is not None:
        return case.program
    if case.theory is None:
        raise SystemExit("KLM property cases are not supported")
    theory = case.theory
    if theory.defeasible_rules or theory.defeaters or theory.superiority:
        raise SystemExit("Only strict-only theories are supported")
    return SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )


if __name__ == "__main__":
    raise SystemExit(main())
