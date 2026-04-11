from __future__ import annotations

from datalog_conformance.schema import DefeasibleTheory, Policy, Rule

from gunray.closure import ClosureEvaluator


def test_example6_distinguishes_rational_from_lexicographic_closure() -> None:
    theory = DefeasibleTheory(
        facts={"s": [()]},
        strict_rules=[
            Rule(id="c1", head="p", body=["a"]),
            Rule(id="c2", head="p", body=["s"]),
        ],
        defeasible_rules=[
            Rule(id="d1", head="m", body=["p"]),
            Rule(id="d2", head="a", body=["p"]),
            Rule(id="d3", head="t", body=["p"]),
            Rule(id="d4", head="~t", body=["s"]),
        ],
    )

    evaluator = ClosureEvaluator()
    rational = evaluator.evaluate(theory, Policy.RATIONAL_CLOSURE)
    lexicographic = evaluator.evaluate(theory, Policy.LEXICOGRAPHIC_CLOSURE)

    assert "m" not in rational.sections["defeasibly"]
    assert "a" not in rational.sections["defeasibly"]
    assert "m" in lexicographic.sections["defeasibly"]
    assert "a" in lexicographic.sections["defeasibly"]


def test_or_counterexample_fails_only_for_relevant_closure() -> None:
    theory = DefeasibleTheory(
        facts={},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="b", body=["a"]),
            Rule(id="r2", head="c", body=["b"]),
            Rule(id="r3", head="~c", body=["a"]),
            Rule(id="r4", head="d", body=["a"]),
            Rule(id="r5", head="d", body=["g"]),
            Rule(id="r6", head="e", body=["d"]),
            Rule(id="r7", head="h", body=["g"]),
            Rule(id="r8", head="~e", body=["h"]),
            Rule(id="r9", head="e", body=["g"]),
        ],
    )

    evaluator = ClosureEvaluator()

    assert evaluator.satisfies_klm_property(theory, "Or", Policy.RATIONAL_CLOSURE)
    assert evaluator.satisfies_klm_property(theory, "Or", Policy.LEXICOGRAPHIC_CLOSURE)
    assert not evaluator.satisfies_klm_property(theory, "Or", Policy.RELEVANT_CLOSURE)
