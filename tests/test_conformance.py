from __future__ import annotations

from pathlib import Path
import sys

import pytest

from datalog_conformance.plugin import _load_multi_case_file
from datalog_conformance.runner import YamlTestRunner
from datalog_conformance.schema import SchemaError, TestCase as SuiteCase

import yaml


def _suite_root() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    suite_root = repo_root.parent / "datalog-conformance-suite" / "src" / "datalog_conformance" / "_tests"
    if not suite_root.exists():
        raise FileNotFoundError(f"Conformance suite not found at {suite_root}")
    return suite_root


def _discover_yaml_tests(test_dir: Path) -> list[tuple[Path, SuiteCase]]:
    cases: list[tuple[Path, SuiteCase]] = []
    for yaml_file in sorted(test_dir.rglob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if raw is None:
            continue
        if isinstance(raw, dict) and "tests" in raw:
            suite_cases = _load_multi_case_file(raw, yaml_file)
            cases.extend((yaml_file, case) for case in suite_cases)
            continue
        if not isinstance(raw, dict):
            raise SchemaError(f"{yaml_file}: expected mapping at root")
        cases.append((yaml_file, SuiteCase.from_dict(raw)))
    return cases


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "gunray_yaml_test_case" not in metafunc.fixturenames:
        return

    requested_tags = _parse_requested_tags(metafunc.config.getoption("--datalog-tags"))
    tests_dir = _suite_root()
    params: list[tuple[Path, SuiteCase]] = []
    ids: list[str] = []

    for yaml_path, case in _discover_yaml_tests(tests_dir):
        if requested_tags and not requested_tags.issubset(set(case.tags)):
            continue
        relative = yaml_path.relative_to(tests_dir).with_suffix("")
        params.append((yaml_path, case))
        ids.append(f"{relative.as_posix()}::{case.name}")

    metafunc.parametrize("gunray_yaml_test_case", params, ids=ids)


def _parse_requested_tags(raw: str | None) -> set[str]:
    if raw is None:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


@pytest.fixture
def gunray_yaml_test_case(request: pytest.FixtureRequest) -> tuple[Path, SuiteCase]:
    return request.param


@pytest.fixture
def runner(request: pytest.FixtureRequest) -> YamlTestRunner:
    import_path = request.config.getoption("--datalog-evaluator")
    if import_path is None:
        pytest.skip("Provide --datalog-evaluator=package.Class to run conformance suites")
    return YamlTestRunner.from_import_path(import_path)


@pytest.mark.conformance
@pytest.mark.timeout(120)
def test_yaml_conformance(
    runner: YamlTestRunner,
    gunray_yaml_test_case: tuple[Path, SuiteCase],
) -> None:
    yaml_path, case = gunray_yaml_test_case

    if case.skip is not None:
        pytest.skip(case.skip)

    suite_root = _suite_root()
    relative = yaml_path.relative_to(suite_root).with_suffix("")
    sys.stderr.write(f"[gunray] running {relative.as_posix()}::{case.name}\n")
    sys.stderr.flush()

    runner.run_test_case(case)
