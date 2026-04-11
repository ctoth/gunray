from __future__ import annotations

import argparse
import faulthandler
import time
from pathlib import Path
from typing import cast

import yaml
from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.runner import _extract_defeasible_sections, _extract_model_facts
from datalog_conformance.schema import TestCase

from gunray.adapter import GunrayEvaluator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", help="Exact conformance case name")
    parser.add_argument("--yaml", required=True, help="YAML path relative to suite _tests")
    parser.add_argument(
        "--dump-after",
        type=float,
        default=0.0,
        help="Dump a traceback after this many seconds while the case is still running",
    )
    args = parser.parse_args()

    case = _load_case(args.case, args.yaml)
    evaluator = GunrayEvaluator()
    if args.dump_after > 0:
        faulthandler.dump_traceback_later(args.dump_after, repeat=True)

    started = time.perf_counter()
    try:
        if case.program is not None:
            raw_model = evaluator.evaluate(case.program)
            facts = _extract_model_facts(raw_model)
        elif case.theory is not None:
            raw_model = evaluator.evaluate(case.theory)
            facts = _extract_defeasible_sections(raw_model)
        else:
            raise SystemExit("KLM property cases are not supported")
    finally:
        if args.dump_after > 0:
            faulthandler.cancel_dump_traceback_later()
    elapsed = time.perf_counter() - started

    print(f"case: {case.name}")
    print(f"elapsed_seconds: {elapsed:.3f}")
    for section, predicates in sorted(facts.items()):
        row_count = sum(len(rows) for rows in predicates.values())
        print(
            f"section={section} predicates={len(predicates)} rows={row_count}"
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
    if not matches:
        raise SystemExit(f"No case named {name!r} in {yaml_path}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple cases named {name!r} in {yaml_path}")
    return matches[0]


if __name__ == "__main__":
    raise SystemExit(main())
