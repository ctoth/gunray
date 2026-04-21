"""Optional bridge from datalog-conformance-suite inputs to Gunray."""
# pyright: reportMissingTypeStubs=false

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Protocol, TypeAlias, cast

import yaml

from .adapter import GunrayEvaluator
from .schema import DefeasibleTheory, NegationSemantics, Policy, Program, Rule
from .trace import TraceConfig

RuleAttributeName: TypeAlias = str
RuleAttributeMap: TypeAlias = Mapping[RuleAttributeName, object]
RuleAttributeNames: TypeAlias = frozenset[RuleAttributeName]

_SUPPORTED_RULE_ATTRIBUTES: RuleAttributeNames = frozenset(("id", "head", "body"))
_suite_import_error: ImportError | None = None
_datalog_conformance: Any | None = None
_load_multi_case_file_func: Any | None = None
SuiteDefeasibleTheory: type[Any] | None = None
SuitePolicy: type[Any] | None = None
SuiteProgram: type[Any] | None = None
_nemo_fingerprints: set[tuple[Any, ...]] | None = None

try:
    import datalog_conformance as _raw_datalog_conformance
    from datalog_conformance.plugin import _load_multi_case_file as _raw_load_multi_case_file
    from datalog_conformance.schema import DefeasibleTheory as _SuiteDefeasibleTheory
    from datalog_conformance.schema import Policy as _SuitePolicy
    from datalog_conformance.schema import Program as _SuiteProgram

    _datalog_conformance = _raw_datalog_conformance
    _load_multi_case_file_func = _raw_load_multi_case_file
    SuiteDefeasibleTheory = cast(type[Any], _SuiteDefeasibleTheory)
    SuitePolicy = cast(type[Any], _SuitePolicy)
    SuiteProgram = cast(type[Any], _SuiteProgram)
except ImportError as exc:  # pragma: no cover - exercised only without the optional extra
    _suite_import_error = exc


class SuiteRuleLike(Protocol):
    """Subset of datalog-conformance Rule consumed by Gunray."""

    id: str
    head: str
    body: Iterable[str]


def _require_suite_support() -> None:
    if _suite_import_error is not None:
        raise ModuleNotFoundError(
            "gunray.conformance_adapter requires the datalog-conformance "
            "dependency. Install the dev extra."
        ) from _suite_import_error


def _copy_facts(raw_facts: dict[str, Any]) -> dict[str, list[tuple[Any, ...]]]:
    return {predicate: [tuple(row) for row in rows] for predicate, rows in raw_facts.items()}


def _translate_rule(rule: SuiteRuleLike) -> Rule:
    _raise_on_unknown_suite_rule_attributes(rule)
    return Rule(id=rule.id, head=rule.head, body=tuple(rule.body))


def _raise_on_unknown_suite_rule_attributes(rule: SuiteRuleLike) -> None:
    raw_attrs = getattr(rule, "__dict__", None)
    if not isinstance(raw_attrs, Mapping):
        return

    attrs = cast(RuleAttributeMap, raw_attrs)
    unknown_attrs = sorted(set(attrs) - _SUPPORTED_RULE_ATTRIBUTES)
    if unknown_attrs:
        raise ValueError("Unsupported conformance Rule attributes: " + ", ".join(unknown_attrs))


def _translate_program(program: Any) -> Program:
    return Program(
        facts=_copy_facts(program.facts),
        rules=list(program.rules),
    )


def _translate_theory(theory: Any) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=_copy_facts(theory.facts),
        strict_rules=tuple(_translate_rule(rule) for rule in theory.strict_rules),
        defeasible_rules=tuple(_translate_rule(rule) for rule in theory.defeasible_rules),
        defeaters=tuple(_translate_rule(rule) for rule in theory.defeaters),
        superiority=tuple(theory.superiority),
        conflicts=tuple(theory.conflicts),
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


def _facts_fingerprint(facts: Any) -> tuple[tuple[str, tuple[tuple[Any, ...], ...]], ...]:
    return tuple(
        sorted(
            (predicate, tuple(sorted(tuple(row) for row in rows)))
            for predicate, rows in facts.items()
        )
    )


def _rule_fingerprint(rule: Any) -> tuple[str, str, tuple[str, ...]]:
    return rule.id, rule.head, tuple(rule.body)


def _item_fingerprint(item: Any) -> tuple[Any, ...]:
    if hasattr(item, "rules"):
        return (
            "program",
            _facts_fingerprint(item.facts),
            tuple(item.rules),
        )
    return (
        "theory",
        _facts_fingerprint(item.facts),
        tuple(_rule_fingerprint(rule) for rule in item.strict_rules),
        tuple(_rule_fingerprint(rule) for rule in item.defeasible_rules),
        tuple(_rule_fingerprint(rule) for rule in item.defeaters),
        tuple(item.superiority),
        tuple(item.conflicts),
    )


def _suite_nemo_fingerprints() -> set[tuple[Any, ...]]:
    global _nemo_fingerprints
    if _nemo_fingerprints is not None:
        return _nemo_fingerprints

    _require_suite_support()
    assert _datalog_conformance is not None
    assert _load_multi_case_file_func is not None
    suite_path = Path(next(iter(_datalog_conformance.__path__))).resolve()
    tests_root = suite_path / "_tests"
    fingerprints: set[tuple[Any, ...]] = set()
    nemo_negation_files = (
        tests_root / "negation" / "nemo_negation.yaml",
        tests_root / "defeasible" / "strict_only" / "strict_only_negation_nemo_negation.yaml",
    )
    for yaml_file in nemo_negation_files:
        if not yaml_file.exists():
            continue
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if raw is None:
            continue
        if isinstance(raw, dict) and "tests" in raw:
            cases = _load_multi_case_file_func(raw, yaml_file)
        else:
            from datalog_conformance.schema import TestCase as _SuiteCase

            cases = [_SuiteCase.from_dict(raw)]
        for case in cases:
            if "nemo" not in set(case.tags):
                continue
            if case.program is not None:
                fingerprints.add(_item_fingerprint(case.program))
            if case.theory is not None:
                fingerprints.add(_item_fingerprint(case.theory))
    _nemo_fingerprints = fingerprints
    return fingerprints


def _negation_semantics_for_suite_item(item: Any) -> NegationSemantics:
    if _item_fingerprint(item) in _suite_nemo_fingerprints():
        return NegationSemantics.NEMO
    return NegationSemantics.SAFE


class GunrayConformanceEvaluator:
    """Bridge evaluator for datalog-conformance-suite runner inputs."""

    def __init__(self, *, core: GunrayEvaluator | None = None) -> None:
        self._core = core or GunrayEvaluator()

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
            return self._core.evaluate(
                _translate_program(item),
                negation_semantics=_negation_semantics_for_suite_item(item),
            )
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate(
                _translate_theory(item),
                _translate_policy(policy),
                negation_semantics=_negation_semantics_for_suite_item(item),
            )
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
            return self._core.evaluate_with_trace(
                _translate_program(item),
                None,
                trace_config,
                negation_semantics=_negation_semantics_for_suite_item(item),
            )
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate_with_trace(
                _translate_theory(item),
                _translate_policy(policy),
                trace_config,
                negation_semantics=_negation_semantics_for_suite_item(item),
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
