from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import yaml

from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.schema import Policy, TestCase

from gunray.adapter import GunrayEvaluator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("--yaml", required=True)
    parser.add_argument("--engine", choices=("gunray", "depysible"), default="gunray")
    args = parser.parse_args()

    case = _load_case(args.case, args.yaml)
    if case.theory is None:
        raise SystemExit("Only theory cases are supported")

    if args.engine == "gunray":
        model = GunrayEvaluator().evaluate(case.theory, Policy.BLOCKING)
    else:
        suite_root = Path(__file__).resolve().parents[2] / "datalog-conformance-suite"
        tests_root = suite_root / "tests"
        import sys

        sys.path.insert(0, str(tests_root))
        from depysible_test_support import run_depysible_adapter  # type: ignore[import-not-found]

        model = run_depysible_adapter(case.theory, Policy.BLOCKING)

    print(f"case: {case.name}")
    for section, predicates in sorted(model.sections.items()):
        print(f"[{section}]")
        for predicate, rows in sorted(predicates.items()):
            print(f"{predicate}: {sorted(rows)}")
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
