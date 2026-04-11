from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from datalog_conformance.plugin import _load_multi_case_file
from datalog_conformance.schema import Program, TestCase

from gunray.parser import parse_program


def suite_root() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return (
        repo_root.parent
        / "datalog-conformance-suite"
        / "src"
        / "datalog_conformance"
        / "_tests"
        / "basic"
    )


def load_cases() -> list[tuple[Path, TestCase]]:
    cases: list[tuple[Path, TestCase]] = []
    for yaml_path in sorted(suite_root().rglob("*.yaml")):
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue
        if "tests" in raw:
            loaded = _load_multi_case_file(cast(dict[object, object], raw), yaml_path)
            cases.extend((yaml_path, case) for case in loaded)
            continue
        cases.append((yaml_path, TestCase.from_dict(raw)))
    return cases


def main() -> int:
    for yaml_path, case in load_cases():
        if "basic" not in case.tags or case.program is None or case.expect is None:
            continue
        program = case.program
        assert isinstance(program, Program)
        facts, rules = parse_program(program)

        fact_predicates = set(facts)
        head_predicates = {head.predicate for rule in rules for head in rule.heads}
        visible_predicates = fact_predicates | head_predicates

        issues: list[str] = []
        for predicate, rows in case.expect.items():
            if rows and predicate not in visible_predicates:
                issues.append(f"nonempty expect for invisible predicate {predicate!r}")
            if not program.rules and rows and set(rows) - facts.get(predicate, set()):
                issues.append(
                    f"nonempty expect for {predicate!r} with no rules and missing fact rows"
                )

        if issues:
            relative = yaml_path.relative_to(suite_root().parent).as_posix()
            print(f"{relative}::{case.name}")
            for issue in issues:
                print(f"  - {issue}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
