"""B1.5 driver — demonstrate ``render_tree`` + ``answer`` on a fixture.

Loads a conformance fixture by ``case`` name + relative yaml path,
prints the existing four-section model projection (backwards
compatible with the pre-B1.5 behavior), and then — the point of this
dispatch — prints Garcia & Simari 2004 Def 5.3 ``answer`` plus the
rendered dialectical tree for every literal that appears in the
fixture's ``expect`` block. This makes the renderer usable at a REPL
for B1.6 acceptable-line-condition debugging.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import yaml
from datalog_conformance.plugin import _load_multi_case_file, get_tests_dir
from datalog_conformance.schema import Policy, TestCase

from gunray.arguments import build_arguments
from gunray.conformance_adapter import GunrayConformanceEvaluator, _translate_theory
from gunray.dialectic import answer, build_tree, render_tree
from gunray.preference import TrivialPreference
from gunray.schema import DefeasibleModel
from gunray.schema import DefeasibleTheory as GunrayDefeasibleTheory
from gunray.trace import DefeasibleTrace
from gunray.types import GroundAtom, Scalar


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

    model: DefeasibleModel | None = None
    trace: DefeasibleTrace | None = None
    evaluate_error: str | None = None
    if args.engine == "gunray":
        evaluator = GunrayConformanceEvaluator()
        try:
            if args.show_trace:
                raw_model, raw_trace = evaluator.evaluate_with_trace(case.theory, Policy.BLOCKING)
                model = cast("DefeasibleModel", raw_model)
                trace = cast("DefeasibleTrace", raw_trace)
            else:
                model = cast(
                    "DefeasibleModel",
                    evaluator.evaluate(case.theory, Policy.BLOCKING),
                )
        except NotImplementedError as exc:
            # B1.6 rewires the defeasible path on the evaluator; until
            # then, defeasible theories raise here. The dialectic
            # section below is independent of the evaluator and still
            # runs.
            evaluate_error = str(exc)
    else:
        suite_root = Path(__file__).resolve().parents[2] / "datalog-conformance-suite"
        tests_root = suite_root / "tests"
        import sys

        sys.path.insert(0, str(tests_root))
        from depysible_test_support import run_depysible_adapter  # type: ignore[import-not-found]

        model = cast(
            "DefeasibleModel",
            run_depysible_adapter(case.theory, Policy.BLOCKING),
        )

    # 4-section projection — preserved for backwards compatibility with
    # the pre-B1.5 version of this script.
    print(f"case: {case.name}")
    if model is not None:
        for section, predicates in sorted(model.sections.items()):
            print(f"[{section}]")
            for predicate, rows in sorted(predicates.items()):
                print(f"{predicate}: {sorted(rows)}")
    elif evaluate_error is not None:
        print(f"[evaluator] skipped: {evaluate_error}")
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

    # B1.5 extension — dialectic per query literal. The fixture's
    # ``expect`` block enumerates the literals the user cares about;
    # iterate over them, compute Garcia 04 Def 5.3 ``answer``, and
    # render the dialectical tree for every argument we can build for
    # the query literal. Always uses ``TrivialPreference`` — Block-1
    # semantics per the refactor plan.
    criterion = TrivialPreference()
    native_theory: GunrayDefeasibleTheory = _translate_theory(case.theory)
    queries = _fixture_queries(case)
    if queries:
        print("[dialectic]")
        for literal in queries:
            result = answer(native_theory, literal, criterion)
            print(f"query {literal.predicate}{list(literal.arguments)} -> {result.value}")
            arguments_for_literal = [
                arg for arg in build_arguments(native_theory) if arg.conclusion == literal
            ]
            if not arguments_for_literal:
                print("  (no argument for this literal)")
                continue
            for arg in arguments_for_literal:
                tree = build_tree(arg, criterion, native_theory)
                rendered = render_tree(tree)
                for line in rendered.splitlines():
                    print(f"  {line}")
    return 0


def _fixture_queries(case: TestCase) -> list[GroundAtom]:
    """Return the literals named in ``case.expect``.

    A fixture's ``expect`` block is either a flat ``PredicateFacts``
    mapping (``{predicate: [[row], ...]}``) or a ``DefeasibleSections``
    mapping (``{section: {predicate: [[row], ...]}}``). This helper
    flattens both forms into the union of ``GroundAtom`` values the
    fixture claims are interesting for this case.
    """
    atoms: list[GroundAtom] = []
    seen: set[tuple[str, tuple[Scalar, ...]]] = set()

    def _push(predicate: str, row: tuple[Scalar, ...]) -> None:
        key = (predicate, row)
        if key in seen:
            return
        seen.add(key)
        atoms.append(GroundAtom(predicate=predicate, arguments=row))

    expect = case.expect
    if expect is None:
        return atoms

    # The two shapes distinguish by whether values are dict-of-rows
    # (sections) or list-of-rows (flat predicate facts). Try sections
    # first; fall back to flat.
    if all(isinstance(value, dict) for value in expect.values()):
        for _section, predicates in expect.items():
            if not isinstance(predicates, dict):
                continue
            for predicate, rows in predicates.items():
                for row in rows:
                    _push(predicate, tuple(row))
    else:
        for predicate, rows in expect.items():
            for row in rows:
                _push(predicate, tuple(row))
    return atoms


def _load_case(name: str, yaml_relpath: str) -> TestCase:
    package_tests_dir = get_tests_dir()
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = (
        repo_root.parent / "datalog-conformance-suite" / "src" / "datalog_conformance" / "_tests"
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
