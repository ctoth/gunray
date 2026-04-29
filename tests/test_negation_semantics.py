from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import datalog_conformance
import pytest
import yaml
from datalog_conformance.plugin import _load_multi_case_file

from gunray import (
    DefeasibleEvaluator,
    DefeasibleTheory,
    MarkingPolicy,
    NegationSemantics,
    Program,
    Rule,
    SemiNaiveEvaluator,
)
from gunray.conformance_adapter import GunrayConformanceEvaluator, _translate_rule
from gunray.errors import SafetyViolationError


def _unsafe_program() -> Program:
    return Program(
        facts={"p": {("a",)}},
        rules=["r(X) :- p(X), not q(Y)."],
    )


def test_safe_mode_rejects_variable_only_in_negative_literal() -> None:
    with pytest.raises(SafetyViolationError):
        SemiNaiveEvaluator().evaluate(
            _unsafe_program(),
            negation_semantics=NegationSemantics.SAFE,
        )


def test_nemo_mode_accepts_variable_only_in_negative_literal() -> None:
    model = SemiNaiveEvaluator().evaluate(
        _unsafe_program(),
        negation_semantics=NegationSemantics.NEMO,
    )

    assert "r" in model.facts


def test_default_mode_is_safe() -> None:
    with pytest.raises(SafetyViolationError):
        SemiNaiveEvaluator().evaluate(_unsafe_program())


def test_defeasible_evaluator_default_mode_is_safe() -> None:
    theory = DefeasibleTheory(
        facts={"p": {("a",)}},
        strict_rules=[Rule(id="s1", head="r(X)", body=["p(X)", "not q(Y)"])],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    with pytest.raises(SafetyViolationError):
        DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)


def test_conformance_adapter_routes_nemo_fixtures_to_nemo_mode() -> None:
    nemo_file = _conformance_fixture_file("negation", "nemo_negation.yaml")
    raw = yaml.safe_load(nemo_file.read_text(encoding="utf-8"))
    case = next(
        item
        for item in _load_multi_case_file(raw, nemo_file)
        if item.name == "nemo_negation_projectedX"
    )

    assert case.program is not None
    model = GunrayConformanceEvaluator().evaluate(case.program)

    assert "projectedX" in model.facts


def test_translate_rule_rejects_unknown_suite_fields() -> None:
    suite_rule = SimpleNamespace(id="r1", head="q(X)", body=["p(X)"], source="suite.yaml")

    with pytest.raises(ValueError, match="Unsupported conformance Rule attributes: source"):
        _translate_rule(suite_rule)


def _conformance_fixture_file(*parts: str) -> Path:
    roots: list[Path] = []
    if datalog_conformance.__file__ is not None:
        roots.append(Path(datalog_conformance.__file__).resolve().parent / "_tests")
    roots.append(
        Path(__file__).resolve().parents[2]
        / "datalog-conformance-suite"
        / "src"
        / "datalog_conformance"
        / "_tests"
    )
    for root in roots:
        candidate = root.joinpath(*parts)
        if candidate.exists():
            return candidate
    locations = ", ".join(str(root.joinpath(*parts)) for root in roots)
    raise FileNotFoundError(f"Conformance fixture not found at any of: {locations}")
