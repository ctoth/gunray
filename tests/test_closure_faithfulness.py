from __future__ import annotations

from pathlib import Path
from typing import TypeAlias, cast

import yaml
from datalog_conformance.references import PropositionalClosureEvaluator
from datalog_conformance.schema import (
    DefeasibleTheory as SuiteTheory,
)
from datalog_conformance.schema import (
    Policy as SuitePolicy,
)
from datalog_conformance.schema import (
    Rule as SuiteRule,
)
from datalog_conformance.schema import (
    TestCase as SuiteCase,
)
from hypothesis import given, settings
from hypothesis import strategies as st

import gunray.closure as gunray_closure
from gunray import DefeasibleTheory, Policy, Rule
from gunray.closure import ClosureEvaluator

_MORRIS_CLOSURE_FILE = (
    Path(__file__).resolve().parents[2]
    / "datalog-conformance-suite"
    / "src"
    / "datalog_conformance"
    / "_tests"
    / "defeasible"
    / "closure"
    / "morris_core_examples.yaml"
)

_ATOMS = ("a", "b", "c")
RawTheory: TypeAlias = tuple[
    frozenset[str],
    tuple[tuple[str, tuple[str, ...]], ...],
    tuple[tuple[str, tuple[str, ...]], ...],
]
_POLICY_PAIRS = (
    (Policy.RATIONAL_CLOSURE, SuitePolicy.RATIONAL_CLOSURE),
    (Policy.LEXICOGRAPHIC_CLOSURE, SuitePolicy.LEXICOGRAPHIC_CLOSURE),
    (Policy.RELEVANT_CLOSURE, SuitePolicy.RELEVANT_CLOSURE),
)


def _raw_theory_strategy():
    facts = st.frozensets(st.sampled_from(_ATOMS), max_size=len(_ATOMS))
    literal = st.sampled_from([*_ATOMS, *(f"~{atom}" for atom in _ATOMS)])
    body = st.lists(literal, unique=True, max_size=2).map(lambda items: tuple(sorted(items)))
    rule = st.tuples(literal, body)
    strict_rules = st.lists(rule, unique=True, max_size=2).map(lambda items: tuple(sorted(items)))
    defeasible_rules = st.lists(rule, unique=True, max_size=3).map(
        lambda items: tuple(sorted(items))
    )
    return st.tuples(facts, strict_rules, defeasible_rules)


def _raw_formula_strategy(atoms: tuple[str, ...]):
    if not atoms:
        return st.just(("true",))
    literal = st.sampled_from([*atoms, *(f"~{atom}" for atom in atoms)])
    base = st.one_of(st.just(("true",)), literal.map(lambda item: ("literal", item)))
    return st.recursive(
        base,
        lambda children: st.one_of(
            st.tuples(st.just("and"), children, children),
            st.tuples(st.just("or"), children, children),
        ),
        max_leaves=4,
    )


def test_morris_closure_corpus_matches_ranked_world_reference() -> None:
    """Morris 2020 Examples 6 and 6-variant should match the ranked-world oracle.

    The corpus cases are derived from the page-image-backed Morris materials
    already checked into ``../datalog-conformance-suite`` and cite Example 6 /
    the subset-ranking discussion on pp.156-158 (local ``page-015.png``
    through ``page-017.png``).
    """

    raw = yaml.safe_load(_MORRIS_CLOSURE_FILE.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    data = cast(dict[object, object], raw)
    entries = cast(list[object], data["tests"])

    reference = PropositionalClosureEvaluator()
    evaluator = ClosureEvaluator()

    for case in _load_morris_closure_cases(entries, data):
        assert case.theory is not None
        assert case.expect_per_policy is not None

        gunray_theory = _to_gunray_theory(case.theory)
        for gunray_policy, suite_policy in _POLICY_PAIRS[:2]:
            actual = evaluator.evaluate(gunray_theory, gunray_policy)
            expected = reference.evaluate(case.theory, suite_policy)
            assert actual.sections == expected.sections


@settings(max_examples=40, deadline=None)
@given(
    raw_theory=_raw_theory_strategy(),
    data=st.data(),
)
def test_formula_entailment_matches_ranked_world_reference_for_small_theories(
    raw_theory: RawTheory,
    data: st.DataObject,
) -> None:
    """Small-theory closure entailment should match the exact ranked-world reference.

    This directly checks the reduced Gunray implementation against an oracle
    that still evaluates over all propositional worlds. That is the concrete
    faithfulness benchmark missing from review issue 20 for Morris 2020
    Algorithms 3-6 (pp.150-153; local ``page-009.png`` through
    ``page-012.png``).
    """

    atoms = _atoms_for_raw_theory(raw_theory)
    antecedent = data.draw(_raw_formula_strategy(atoms), label="antecedent")
    consequent = data.draw(_raw_formula_strategy(atoms), label="consequent")

    gunray_theory, suite_theory = _build_theories(raw_theory)
    gunray_ranked = gunray_closure._ranked_defaults(gunray_theory)
    import datalog_conformance.references.closure as suite_closure

    suite_ranked_defaults = suite_closure._ranked_defaults(suite_theory)
    for gunray_policy, suite_policy in _POLICY_PAIRS:
        actual = gunray_closure._formula_entails(
            gunray_ranked,
            gunray_theory,
            _to_gunray_formula(antecedent),
            _to_gunray_formula(consequent),
            gunray_policy,
        )
        expected = suite_closure._formula_entails(
            suite_ranked_defaults,
            suite_theory,
            _to_suite_formula(suite_closure, antecedent),
            _to_suite_formula(suite_closure, consequent),
            suite_policy,
        )
        assert actual is expected


@settings(max_examples=30, deadline=None)
@given(raw_theory=_raw_theory_strategy())
def test_or_property_matches_ranked_world_reference_for_small_theories(
    raw_theory: RawTheory,
) -> None:
    """The public Or check should agree with the ranked-world reference.

    Morris 2020 Appendix C.2 gives the canonical relevant-closure Or failure
    on pp.166-167 (local ``page-025.png`` through ``page-026.png``). This
    property broadens that comparison to randomly generated reduced theories.
    """

    gunray_theory, suite_theory = _build_theories(raw_theory)
    evaluator = ClosureEvaluator()
    reference = PropositionalClosureEvaluator()

    for gunray_policy, suite_policy in _POLICY_PAIRS:
        actual = evaluator.satisfies_klm_property(gunray_theory, "Or", gunray_policy)
        expected = reference.satisfies_klm_property(suite_theory, "Or", suite_policy)
        assert actual is expected


def _build_theories(raw_theory: RawTheory) -> tuple[DefeasibleTheory, SuiteTheory]:
    facts, strict_rules, defeasible_rules = raw_theory
    return _to_gunray_theory_from_raw(
        facts, strict_rules, defeasible_rules
    ), _to_suite_theory_from_raw(facts, strict_rules, defeasible_rules)


def _atoms_for_raw_theory(raw_theory: RawTheory) -> tuple[str, ...]:
    facts, strict_rules, defeasible_rules = raw_theory
    atoms = set(facts)
    for head, body in (*strict_rules, *defeasible_rules):
        atoms.add(head.removeprefix("~"))
        atoms.update(literal.removeprefix("~") for literal in body)
    return tuple(sorted(atoms))


def _load_morris_closure_cases(
    entries: list[object], data: dict[object, object]
) -> list[SuiteCase]:
    base_source = data.get("source")
    base_verification = data.get("verification")
    raw_base_tags = data.get("tags", [])
    base_tags = list(cast(list[object], raw_base_tags)) if isinstance(raw_base_tags, list) else []

    cases: list[SuiteCase] = []
    for entry in entries:
        assert isinstance(entry, dict)
        merged = dict(cast(dict[object, object], entry))
        if "source" not in merged and base_source is not None:
            merged["source"] = base_source
        if "verification" not in merged and base_verification is not None:
            merged["verification"] = base_verification
        if base_tags:
            local_tags_obj = merged.get("tags", [])
            assert isinstance(local_tags_obj, list)
            local_tags = cast(list[object], local_tags_obj)
            merged["tags"] = [*base_tags, *local_tags]
        cases.append(SuiteCase.from_dict(merged))
    return cases


def _to_gunray_theory(theory: SuiteTheory) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={predicate: [tuple(row) for row in rows] for predicate, rows in theory.facts.items()},
        strict_rules=[
            Rule(id=rule.id, head=rule.head, body=list(rule.body)) for rule in theory.strict_rules
        ],
        defeasible_rules=[
            Rule(id=rule.id, head=rule.head, body=list(rule.body))
            for rule in theory.defeasible_rules
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _to_gunray_theory_from_raw(
    facts: frozenset[str],
    strict_rules: tuple[tuple[str, tuple[str, ...]], ...],
    defeasible_rules: tuple[tuple[str, tuple[str, ...]], ...],
) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={predicate: [()] for predicate in sorted(facts)},
        strict_rules=[
            Rule(id=f"s{index}", head=head, body=list(body))
            for index, (head, body) in enumerate(strict_rules, start=1)
        ],
        defeasible_rules=[
            Rule(id=f"d{index}", head=head, body=list(body))
            for index, (head, body) in enumerate(defeasible_rules, start=1)
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _to_suite_theory_from_raw(
    facts: frozenset[str],
    strict_rules: tuple[tuple[str, tuple[str, ...]], ...],
    defeasible_rules: tuple[tuple[str, tuple[str, ...]], ...],
) -> SuiteTheory:
    return SuiteTheory(
        facts={predicate: [()] for predicate in sorted(facts)},
        strict_rules=[
            SuiteRule(id=f"s{index}", head=head, body=list(body))
            for index, (head, body) in enumerate(strict_rules, start=1)
        ],
        defeasible_rules=[
            SuiteRule(id=f"d{index}", head=head, body=list(body))
            for index, (head, body) in enumerate(defeasible_rules, start=1)
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _to_gunray_formula(raw_formula: object) -> gunray_closure.Formula:
    if raw_formula == ("true",):
        return gunray_closure.Formula(kind="true")
    assert isinstance(raw_formula, tuple)
    kind = raw_formula[0]
    if kind == "literal":
        return gunray_closure._literal_formula(cast(str, raw_formula[1]))
    if kind == "and":
        return gunray_closure.Formula(
            kind="and",
            left=_to_gunray_formula(raw_formula[1]),
            right=_to_gunray_formula(raw_formula[2]),
        )
    if kind == "or":
        return gunray_closure._or_formula(
            _to_gunray_formula(raw_formula[1]),
            _to_gunray_formula(raw_formula[2]),
        )
    raise ValueError(f"Unsupported raw formula kind: {kind!r}")


def _to_suite_formula(module: object, raw_formula: object) -> object:
    if raw_formula == ("true",):
        return module.Formula(kind="true")
    assert isinstance(raw_formula, tuple)
    kind = raw_formula[0]
    if kind == "literal":
        return module._literal_formula(cast(str, raw_formula[1]))
    if kind == "and":
        return module.Formula(
            kind="and",
            left=_to_suite_formula(module, raw_formula[1]),
            right=_to_suite_formula(module, raw_formula[2]),
        )
    if kind == "or":
        return module._or_formula(
            _to_suite_formula(module, raw_formula[1]),
            _to_suite_formula(module, raw_formula[2]),
        )
    raise ValueError(f"Unsupported raw formula kind: {kind!r}")
