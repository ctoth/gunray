import time

import pytest

import gunray.dialectic as dialectic
from gunray import DefeasibleEvaluator, DefeasibleTheory, ClosurePolicy, MarkingPolicy, Rule
from gunray.arguments import build_arguments
from gunray.dialectic import (
    DialecticalNode,
    blocking_defeater,
    build_tree,
    counter_argues,
    proper_defeater,
    render_tree,
)
from gunray.preference import TrivialPreference
from gunray.types import GroundAtom


def _linear_chain_theory(n: int) -> DefeasibleTheory:
    """Build a defeasible chain with one opposing defeater for the tail."""

    defeasible_rules = [
        Rule(id=f"d{i}", head=f"p{i}(X)", body=[f"p{i - 1}(X)"]) for i in range(1, n + 1)
    ]
    defeaters = [Rule(id="def1", head=f"~p{n}(X)", body=["p0(X)"])]
    return DefeasibleTheory(
        facts={"p0": {("a",)}},
        strict_rules=[],
        defeasible_rules=defeasible_rules,
        defeaters=defeaters,
        superiority=[],
        conflicts=[],
    )


@pytest.mark.timeout(30)
def test_linear_chain_evaluate_completes_under_30s() -> None:
    """The 20-rule long-chain case must fit inside the unit timeout."""

    theory = _linear_chain_theory(n=20)
    start = time.perf_counter()
    DefeasibleEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0, f"long-chain evaluate took {elapsed:.1f}s"


def _ga(predicate: str, *args: str) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


def _branching_attack_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={
            "a": {("x",)},
            "b": {("x",)},
            "c": {("x",)},
            "d": {("x",)},
        },
        strict_rules=[],
        defeasible_rules=[
            Rule(id="root", head="p(X)", body=["a(X)"]),
            Rule(id="left", head="~p(X)", body=["b(X)"]),
            Rule(id="middle", head="~p(X)", body=["c(X)"]),
            Rule(id="right", head="~p(X)", body=["d(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _find_argument(theory: DefeasibleTheory, conclusion: GroundAtom, rule_id: str):
    for argument in build_arguments(theory):
        has_rule = any(rule.rule_id == rule_id for rule in argument.rules)
        if argument.conclusion == conclusion and has_rule:
            return argument
    raise LookupError((conclusion, rule_id))


def test_build_tree_grounds_strict_context_once(monkeypatch: pytest.MonkeyPatch) -> None:
    theory = _branching_attack_theory()
    universe = build_arguments(theory)
    root = _find_argument(theory, _ga("p", "x"), "root")
    calls = 0
    original = dialectic._ground_theory

    def counted(theory_arg: DefeasibleTheory):
        nonlocal calls
        calls += 1
        return original(theory_arg)

    monkeypatch.setattr(dialectic, "_ground_theory", counted)

    build_tree(root, TrivialPreference(), theory, universe=universe)

    assert calls == 1


def test_build_tree_reuses_concordance_for_unchanged_line_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theory = _branching_attack_theory()
    universe = build_arguments(theory)
    root = _find_argument(theory, _ga("p", "x"), "root")
    calls = 0
    original = dialectic.strict_closure

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(dialectic, "strict_closure", counted)

    build_tree(root, TrivialPreference(), theory, universe=universe)

    assert calls <= 4


def test_render_tree_marks_each_node_at_most_once(monkeypatch: pytest.MonkeyPatch) -> None:
    leaf_count = 0

    def make_tree(depth: int) -> DialecticalNode:
        nonlocal leaf_count
        leaf_count += 1
        argument = dialectic.Argument(
            rules=frozenset(),
            conclusion=_ga(f"n{leaf_count}"),
        )
        if depth == 0:
            return DialecticalNode(argument=argument, children=())
        return DialecticalNode(
            argument=argument,
            children=(make_tree(depth - 1), make_tree(depth - 1)),
        )

    tree = make_tree(5)
    node_count = leaf_count
    calls = 0
    original = dialectic.mark

    def counted(node: DialecticalNode):
        nonlocal calls
        calls += 1
        return original(node)

    monkeypatch.setattr(dialectic, "mark", counted)

    render_tree(tree)

    assert calls <= node_count


def test_public_defeat_checks_accept_prebuilt_universe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theory = _branching_attack_theory()
    universe = build_arguments(theory)
    root = _find_argument(theory, _ga("p", "x"), "root")
    attacker = _find_argument(theory, _ga("~p", "x"), "left")

    def fail_build_arguments(theory_arg: DefeasibleTheory):
        raise AssertionError("public pairwise checks must not rebuild the argument universe")

    monkeypatch.setattr(dialectic, "build_arguments", fail_build_arguments)

    assert counter_argues(attacker, root, theory, universe=universe)
    assert not proper_defeater(attacker, root, TrivialPreference(), theory, universe=universe)
    assert blocking_defeater(attacker, root, TrivialPreference(), theory, universe=universe)
