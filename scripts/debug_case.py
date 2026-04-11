from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import yaml

from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.runner import (
    ConformanceFailure,
    YamlTestRunner,
    _extract_defeasible_sections,
    _extract_model_facts,
)
from datalog_conformance.schema import TestCase


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", help="Exact conformance case name")
    parser.add_argument(
        "--yaml",
        required=True,
        help="YAML path relative to the suite _tests directory, e.g. basic/foo.yaml",
    )
    parser.add_argument(
        "--evaluator",
        default="gunray.adapter.GunrayEvaluator",
        help="Import path for the evaluator under test",
    )
    args = parser.parse_args()

    package_tests_dir = get_tests_dir()
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root.parent / "datalog-conformance-suite" / "src" / "datalog_conformance" / "_tests"
    if not tests_dir.exists():
        tests_dir = package_tests_dir
    yaml_path = tests_dir / args.yaml
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"{yaml_path} did not load to a YAML mapping")
    if "tests" in raw:
        cases = _load_multi_case_file(cast(dict[object, object], raw), yaml_path)
    else:
        cases = [TestCase.from_dict(raw)]

    matches = [case for case in cases if case.name == args.case]
    if not matches:
        raise SystemExit(f"No case named {args.case!r} in {yaml_path}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple cases named {args.case!r} in {yaml_path}")

    case = matches[0]
    print(f"yaml: {yaml_path}")
    print(f"name: {case.name}")
    print(f"source: {case.source}")

    runner = YamlTestRunner.from_import_path(args.evaluator)
    evaluate = runner.evaluator.evaluate

    try:
        if case.program is not None:
            raw_model = evaluate(case.program)
            actual = _extract_model_facts(raw_model)
        elif case.theory is not None:
            raw_model = evaluate(case.theory)
            actual = _extract_defeasible_sections(raw_model)
        else:
            raise SystemExit("KLM property cases are not supported by this debugger")
        print("actual:")
        print(actual)
        print("expect:")
        print(case.expect)
        runner.run_test_case(case)
    except ConformanceFailure as exc:
        print("failure:")
        print(exc)
        return 1

    print("pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
