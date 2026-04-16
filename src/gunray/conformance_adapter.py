"""Optional bridge from datalog-conformance-suite inputs to Gunray."""
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false

from __future__ import annotations

from typing import Any, cast

from .adapter import GunrayEvaluator
from .schema import DefeasibleTheory, Policy, Program, Rule
from .trace import TraceConfig

_suite_import_error: ImportError | None = None
SuiteDefeasibleTheory: type[Any] | None = None
SuitePolicy: type[Any] | None = None
SuiteProgram: type[Any] | None = None

try:
    from datalog_conformance.schema import DefeasibleTheory as _SuiteDefeasibleTheory
    from datalog_conformance.schema import Policy as _SuitePolicy
    from datalog_conformance.schema import Program as _SuiteProgram

    SuiteDefeasibleTheory = cast(type[Any], _SuiteDefeasibleTheory)
    SuitePolicy = cast(type[Any], _SuitePolicy)
    SuiteProgram = cast(type[Any], _SuiteProgram)
except ImportError as exc:  # pragma: no cover - exercised only without the optional extra
    _suite_import_error = exc


def _require_suite_support() -> None:
    if _suite_import_error is not None:
        raise ModuleNotFoundError(
            "gunray.conformance_adapter requires the datalog-conformance "
            "dependency. Install the dev extra."
        ) from _suite_import_error


def _copy_facts(raw_facts: dict[str, Any]) -> dict[str, list[tuple[Any, ...]]]:
    return {predicate: [tuple(row) for row in rows] for predicate, rows in raw_facts.items()}


def _translate_rule(rule: Any) -> Rule:
    return Rule(id=rule.id, head=rule.head, body=list(rule.body))


def _translate_program(program: Any) -> Program:
    return Program(
        facts=_copy_facts(program.facts),
        rules=list(program.rules),
    )


def _translate_theory(theory: Any) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=_copy_facts(theory.facts),
        strict_rules=[_translate_rule(rule) for rule in theory.strict_rules],
        defeasible_rules=[_translate_rule(rule) for rule in theory.defeasible_rules],
        defeaters=[_translate_rule(rule) for rule in theory.defeaters],
        superiority=list(theory.superiority),
        conflicts=list(theory.conflicts),
    )


def _translate_policy(policy: Policy | Any | None) -> Policy | None:
    if policy is None:
        return None
    if isinstance(policy, Policy):
        return policy
    _require_suite_support()
    assert SuitePolicy is not None
    if isinstance(policy, SuitePolicy):
        return Policy(policy.value)
    raise TypeError(f"Unsupported policy type: {type(policy).__name__}")


class GunrayConformanceEvaluator:
    """Bridge evaluator for datalog-conformance-suite runner inputs."""

    def __init__(self) -> None:
        self._core = GunrayEvaluator()

    def evaluate(
        self,
        item: Program | DefeasibleTheory | Any,
        policy: Policy | Any | None = None,
    ) -> object:
        if isinstance(item, Program | DefeasibleTheory):
            return self._core.evaluate(item, _translate_policy(policy))

        _require_suite_support()
        assert SuiteProgram is not None
        assert SuiteDefeasibleTheory is not None
        if isinstance(item, SuiteProgram):
            return self._core.evaluate(_translate_program(item))
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate(_translate_theory(item), _translate_policy(policy))
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory | Any,
        policy: Policy | Any | None = None,
        trace_config: TraceConfig | None = None,
    ) -> tuple[object, object]:
        if isinstance(item, Program | DefeasibleTheory):
            return self._core.evaluate_with_trace(item, _translate_policy(policy), trace_config)

        _require_suite_support()
        assert SuiteProgram is not None
        assert SuiteDefeasibleTheory is not None
        if isinstance(item, SuiteProgram):
            return self._core.evaluate_with_trace(_translate_program(item), None, trace_config)
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate_with_trace(
                _translate_theory(item),
                _translate_policy(policy),
                trace_config,
            )
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory | Any,
        property_name: str,
        policy: Policy | Any,
    ) -> bool:
        if isinstance(theory, DefeasibleTheory):
            return self._core.satisfies_klm_property(
                theory,
                property_name,
                _translate_policy(policy) or Policy.BLOCKING,
            )

        _require_suite_support()
        return self._core.satisfies_klm_property(
            _translate_theory(theory),
            property_name,
            _translate_policy(policy) or Policy.BLOCKING,
        )
