from __future__ import annotations

import inspect

from datalog_conformance.schema import DefeasibleTheory as SuiteDefeasibleTheory
from datalog_conformance.schema import Policy as SuitePolicy
from datalog_conformance.schema import Rule as SuiteRule

from gunray import DefeasibleModel, DefeasibleTheory, DefeasibleTrace, MarkingPolicy, Program
from gunray.adapter import GunrayEvaluator
from gunray.conformance_adapter import GunrayConformanceEvaluator
from gunray.schema import Model
from gunray.trace import DatalogTrace


def test_suite_bridge_uses_public_constructor_injection() -> None:
    source = inspect.getsource(GunrayEvaluator._suite_bridge)

    assert "._core" not in source
    assert "core=self" in source


def test_conformance_bridge_accepts_core_constructor_argument() -> None:
    core = GunrayEvaluator()

    bridge = GunrayConformanceEvaluator(core=core)

    assert bridge is not None


def test_evaluate_with_trace_returns_public_datalog_types() -> None:
    model, trace = GunrayEvaluator().evaluate_with_trace(Program())

    assert isinstance(model, Model)
    assert isinstance(trace, DatalogTrace)


def test_evaluate_with_trace_returns_public_defeasible_types() -> None:
    model, trace = GunrayEvaluator().evaluate_with_trace(
        DefeasibleTheory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert isinstance(model, DefeasibleModel)
    assert isinstance(trace, DefeasibleTrace)


def test_conformance_adapter_returns_suite_sections_for_suite_theory() -> None:
    theory = SuiteDefeasibleTheory(
        facts={"phd_member": [("bob",)]},
        strict_rules=[
            SuiteRule(id="r1", head="dept_member(X)", body=["phd_member(X)"]),
        ],
        defeasible_rules=[
            SuiteRule(id="r2", head="teach_course(X)", body=["dept_member(X)"]),
            SuiteRule(id="r3", head="~teach_course(X)", body=["phd_member(X)"]),
        ],
    )

    model = GunrayConformanceEvaluator().evaluate(theory, SuitePolicy.BLOCKING)

    assert model.sections["definitely"]["phd_member"] == {("bob",)}
    assert model.sections["definitely"]["dept_member"] == {("bob",)}
    assert model.sections["defeasibly"]["phd_member"] == {("bob",)}
    assert model.sections["not_defeasibly"]["teach_course"] == {("bob",)}
    assert "yes" not in model.sections
