from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import yaml
from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.schema import Policy, TestCase

from gunray.adapter import GunrayEvaluator
from gunray.trace import DefeasibleTrace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("--yaml", required=True)
    parser.add_argument("--engine", choices=("gunray", "depysible"), default="gunray")
    parser.add_argument("--show-trace", action="store_true")
    args = parser.parse_args()

    case = _load_case(args.case, args.yaml)
    if case.theory is None:
        raise SystemExit("Only theory cases are supported")

    if args.engine == "gunray":
        if args.show_trace:
            model, trace = GunrayEvaluator().evaluate_with_trace(case.theory, Policy.BLOCKING)
        else:
            model = GunrayEvaluator().evaluate(case.theory, Policy.BLOCKING)
            trace = None
    else:
        suite_root = Path(__file__).resolve().parents[2] / "datalog-conformance-suite"
        tests_root = suite_root / "tests"
        import sys

        sys.path.insert(0, str(tests_root))
        from depysible_test_support import run_depysible_adapter  # type: ignore[import-not-found]

        model = run_depysible_adapter(case.theory, Policy.BLOCKING)
        trace = None

    print(f"case: {case.name}")
    for section, predicates in sorted(model.sections.items()):
        print(f"[{section}]")
        for predicate, rows in sorted(predicates.items()):
            print(f"{predicate}: {sorted(rows)}")
    if args.show_trace and isinstance(trace, DefeasibleTrace):
        print("[trace.proof_attempts]")
        for attempt in trace.proof_attempts:
            print(
                f"{attempt.atom.predicate}{attempt.atom.arguments}:"
                f" result={attempt.result}"
                f" reason={attempt.reason}"
                f" supporters={list(attempt.supporter_rule_ids)}"
                f" attackers={list(attempt.attacker_rule_ids)}"
            )
        print("[trace.classifications]")
        for classification in trace.classifications:
            print(
                f"{classification.atom.predicate}{classification.atom.arguments}:"
                f" result={classification.result}"
                f" reason={classification.reason}"
            )
    return 0


def _load_case(name: str, yaml_relpath: str) -> TestCase:
    package_tests_dir = get_tests_dir()
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = (
        repo_root.parent
        / "datalog-conformance-suite"
        / "src"
        / "datalog_conformance"
        / "_tests"
    )
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


if __name__ == "__main__":
    raise SystemExit(main())
