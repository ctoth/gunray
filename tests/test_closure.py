from __future__ import annotations

import pytest

import gunray.closure as closure_module
from gunray import DefeasibleTheory, Policy, Rule
from gunray.closure import (
    ClosureEvaluator,
    _conjunction_formula,
    _formula_entails,
    _literal_formula,
    _ranked_defaults,
)


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


def test_impossible_antecedent_is_handled_consistently_across_closure_policies() -> None:
    """Impossible antecedents should not diverge by helper accident.

    Morris, Ross, and Meyer 2020, Algorithm 4 (p.151; local page image
    ``papers/Morris_2020_DefeasibleDisjunctiveDatalog/pngs/page-010.png``)
    and Algorithm 5 (p.153; local page image
    ``papers/Morris_2020_DefeasibleDisjunctiveDatalog/pngs/page-012.png``)
    both reduce the final closure check to classical entailment of
    ``alpha -> beta`` after exceptional levels are removed. If ``alpha`` is
    impossible, the three public closure policies should therefore agree
    instead of splitting on whether an empty context is treated vacuously.
    """

    theory = DefeasibleTheory(
        facts={"a": [()]},
        strict_rules=[],
        defeasible_rules=[Rule(id="r1", head="p", body=["q"])],
    )
    ranked = _ranked_defaults(theory)
    antecedent = _conjunction_formula(["a", "~a"])
    consequent = _literal_formula("p")

    assert _formula_entails(ranked, theory, antecedent, consequent, Policy.RATIONAL_CLOSURE)
    assert _formula_entails(
        ranked, theory, antecedent, consequent, Policy.LEXICOGRAPHIC_CLOSURE
    )
    assert _formula_entails(ranked, theory, antecedent, consequent, Policy.RELEVANT_CLOSURE)


def test_public_closure_policies_do_not_materialize_all_worlds(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public closure surface should not depend on full truth-table expansion.

    Morris, Ross, and Meyer 2020 define Rational / Lexicographic / Relevant
    closure via ranking and entailment algorithms (Algorithms 3-5, pp.150-153;
    local page images `page-009.png` through `page-012.png`), not by
    enumerating all `2^n` propositional worlds at evaluation time.
    """

    def _fail(*_args, **_kwargs):
        raise AssertionError("world enumeration should not be used by public closure policies")

    if hasattr(closure_module, "product"):
        monkeypatch.setattr(closure_module, "product", _fail)

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
    evaluator.evaluate(theory, Policy.RATIONAL_CLOSURE)
    assert not hasattr(closure_module, "product")
