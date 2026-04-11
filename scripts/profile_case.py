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
    _constraints_hold,
    _evaluate_stratum,
    _match_positive_body,
    _negative_body_holds,
    _normalize_rules,
    _validate_program,
)
from gunray.parser import ground_atom, parse_program
from gunray.relation import IndexedRelation
from gunray.stratify import stratify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", help="Exact conformance case name")
    parser.add_argument(
        "--yaml",
        required=True,
        help="YAML path relative to the suite _tests directory",
    )
    parser.add_argument(
        "--slow-ms",
        type=float,
        default=250.0,
        help="Log join calls at or above this duration in milliseconds",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=120.0,
        help="Abort instrumentation after this wall time budget",
    )
    parser.add_argument(
        "--run-full",
        action="store_true",
        help="Run the full evaluation instead of stopping after the first slow rule",
    )
    args = parser.parse_args()

    case = _load_case(args.case, args.yaml)
    program = _case_program(case)
    facts, parsed_rules = parse_program(program)
    rules = _normalize_rules(parsed_rules)
    _validate_program(facts, rules)
    strata = stratify(rules)

    model = {predicate: set(rows) for predicate, rows in facts.items()}
    started = time.perf_counter()

    print(f"case: {case.name}")
    print(f"rules: {len(rules)}")
    print(f"predicates: {len(model)}")
    for stratum_index, predicates in enumerate(strata):
        stratum_rules = [
            rule for rule in rules if rule.heads[0].predicate in predicates
        ]
        print(
            f"stratum {stratum_index}: predicates={sorted(predicates)} rules={len(stratum_rules)}"
        )
        _instrument_stratum(
            model=model,
            rules=stratum_rules,
            slow_ms=args.slow_ms,
            started=started,
            max_seconds=args.max_seconds,
            run_full=args.run_full,
        )

    print("completed")
    return 0


def _instrument_stratum(
    *,
    model: dict[str, set[tuple[object, ...]]],
    rules,
    slow_ms: float,
    started: float,
    max_seconds: float,
    run_full: bool,
) -> None:
    iteration = 0
    while True:
        iteration += 1
        changed = False
        print(f"iteration {iteration} start")
        for index, rule in enumerate(rules, start=1):
            elapsed = time.perf_counter() - started
            if elapsed > max_seconds:
                raise SystemExit(
                    f"aborting after {elapsed:.2f}s at iteration {iteration}, rule {index}: {rule.source_text}"
                )

            body_counts = [
                (atom.predicate, len(model.get(atom.predicate, set())))
                for atom in rule.positive_body
            ]
            print(
                f"rule {index}/{len(rules)}: {rule.source_text} body_counts={body_counts}"
            )
            join_started = time.perf_counter()
            bindings = _match_positive_body(rule.positive_body, model)
            join_ms = (time.perf_counter() - join_started) * 1000.0
            if join_ms >= slow_ms:
                print(
                    f"slow join {join_ms:.1f}ms bindings={len(bindings)} rule={rule.source_text}"
                )
                if not run_full:
                    return

            new_rows = 0
            for binding in bindings:
                if not _constraints_hold(rule.constraints, binding):
                    continue
                if not _negative_body_holds(rule.negative_body, binding, model):
                    continue
                derived = ground_atom(rule.heads[0], binding)
                bucket = model.setdefault(derived.predicate, IndexedRelation())
                if bucket.add(derived.arguments):
                    changed = True
                    new_rows += 1
            if new_rows:
                print(f"derived {new_rows} rows into {rule.heads[0].predicate}")

        if not changed:
            print(f"fixpoint after iteration {iteration}")
            return


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
    if not matches:
        raise SystemExit(f"No case named {name!r} in {yaml_path}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple cases named {name!r} in {yaml_path}")
    return matches[0]


def _case_program(case: TestCase) -> SchemaProgram:
    if case.program is not None:
        return case.program
    if case.theory is None:
        raise SystemExit("KLM property cases are not supported")
    theory = case.theory
    if theory.defeasible_rules or theory.defeaters or theory.superiority:
        raise SystemExit("profile_case.py currently supports only program or strict-only theory cases")
    return SchemaProgram(
        facts=theory.facts,
        rules=[
            _strict_rule_to_program_text(rule.head, rule.body)
            for rule in theory.strict_rules
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
