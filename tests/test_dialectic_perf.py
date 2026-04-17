import time

import pytest

from gunray import DefeasibleEvaluator, DefeasibleTheory, Policy, Rule


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
    DefeasibleEvaluator().evaluate(theory, Policy.BLOCKING)
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0, f"long-chain evaluate took {elapsed:.1f}s"
