from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import yaml

from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.runner import ConformanceFailure, YamlTestRunner
from datalog_conformance.schema import TestCase


def iter_cases(tests_dir: Path):
    for yaml_path in sorted(tests_dir.rglob("*.yaml")):
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if raw is None:
            continue
        if not isinstance(raw, dict):
            continue
        if "tests" in raw:
            loaded = _load_multi_case_file(cast(dict[object, object], raw), yaml_path)
            for case in loaded:
                yield yaml_path, case
        else:
            yield yaml_path, TestCase.from_dict(raw)


def case_id(tests_dir: Path, yaml_path: Path, case: TestCase) -> str:
    try:
        relative = yaml_path.relative_to(tests_dir).with_suffix("")
        return f"{relative.as_posix()}::{case.name}"
    except ValueError:
        return f"{yaml_path.stem}::{case.name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evaluator",
        default="gunray.adapter.GunrayEvaluator",
        help="Import path for the evaluator under test",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tags; all must be present",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional case limit after filtering",
    )
    parser.add_argument(
        "--kind",
        choices=("all", "program", "theory"),
        default="all",
        help="Restrict to core program cases or defeasible theory cases",
    )
    args = parser.parse_args()

    required_tags = {item.strip() for item in args.tags.split(",") if item.strip()}
    package_tests_dir = get_tests_dir()
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root.parent / "datalog-conformance-suite" / "src" / "datalog_conformance" / "_tests"
    if not tests_dir.exists():
        tests_dir = package_tests_dir
    runner = YamlTestRunner.from_import_path(args.evaluator)

    total = 0
    passed = 0
    failed = 0

    for yaml_path, case in iter_cases(tests_dir):
        if required_tags and not required_tags.issubset(set(case.tags)):
            continue
        if args.kind == "program" and case.program is None:
            continue
        if args.kind == "theory" and case.theory is None:
            continue
        if case.skip is not None:
            continue
        if args.limit and total >= args.limit:
            break
        total += 1
        identifier = case_id(tests_dir, yaml_path, case)
        try:
            runner.run_test_case(case)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {identifier}")
            if isinstance(exc, ConformanceFailure):
                print(f"  {exc}")
            else:
                print(f"  {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"PASS {identifier}")

    print(f"SUMMARY total={total} passed={passed} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
