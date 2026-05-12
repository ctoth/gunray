from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gunray.arguments import Argument, build_arguments
from gunray.preference import GeneralizedSpecificity
from gunray.schema import DefeasibleTheory, Rule

STOLZENBURG_PAGE_008 = "papers/Stolzenburg_2003_ComputingGeneralizedSpecificity/pngs/page-007.png"
STOLZENBURG_PAGE_009 = "papers/Stolzenburg_2003_ComputingGeneralizedSpecificity/pngs/page-008.png"
STOLZENBURG_PAGE_010 = "papers/Stolzenburg_2003_ComputingGeneralizedSpecificity/pngs/page-009.png"
STOLZENBURG_PAGE_013 = "papers/Stolzenburg_2003_ComputingGeneralizedSpecificity/pngs/page-012.png"
STOLZENBURG_PAGE_014 = "papers/Stolzenburg_2003_ComputingGeneralizedSpecificity/pngs/page-013.png"


def _find_argument(arguments: frozenset[Argument], rule_id: str) -> Argument:
    for argument in arguments:
        if any(rule.rule_id == rule_id for rule in argument.rules):
            return argument
    raise AssertionError(f"missing argument for rule {rule_id!r}")


def test_garcia_example_35_still_pinned_to_page_images() -> None:
    """Garcia 2004 Def. 3.5 / Ex. 3.5, page-012.png and page-013.png."""

    theory = DefeasibleTheory(
        facts={"chicken": {("tina",)}, "scared": {("tina",)}},
        strict_rules=[Rule(id="s_chicken_bird", head="bird(X)", body=["chicken(X)"])],
        defeasible_rules=[
            Rule(id="r_bird_flies", head="flies(X)", body=["bird(X)"]),
            Rule(id="r_chicken_not_flies", head="~flies(X)", body=["chicken(X)"]),
            Rule(id="r_scared_chicken_flies", head="flies(X)", body=["chicken(X)", "scared(X)"]),
        ],
    )

    arguments = build_arguments(theory)
    bird_flies = _find_argument(arguments, "r_bird_flies")
    chicken_not_flies = _find_argument(arguments, "r_chicken_not_flies")
    scared_chicken_flies = _find_argument(arguments, "r_scared_chicken_flies")
    criterion = GeneralizedSpecificity(theory)

    assert criterion.prefers(chicken_not_flies, bird_flies)
    assert criterion.prefers(scared_chicken_flies, chicken_not_flies)


def test_stolzenburg_strict_background_prevents_pairwise_rule_priority_shortcut() -> None:
    """Stolzenburg pp.9-10: strict ``s(X) <- q(X)`` makes extra body ``s`` redundant.

    The page image at page-009.png introduces the counterexample; page-010.png
    says replacing the strict rule by a fact changes the result. This pins the
    strict-background boundary that a pairwise defeasible-rule priority shortcut
    would miss.
    """

    assert STOLZENBURG_PAGE_009.endswith("page-008.png")
    assert STOLZENBURG_PAGE_010.endswith("page-009.png")
    theory = DefeasibleTheory(
        facts={"q": {("a",)}},
        strict_rules=[Rule(id="s_q_to_s", head="s(X)", body=["q(X)"])],
        defeasible_rules=[
            Rule(id="r_plain", head="p(X)", body=["q(X)"]),
            Rule(id="r_extra", head="~p(X)", body=["q(X)", "s(X)"]),
        ],
    )

    arguments = build_arguments(theory)
    plain = _find_argument(arguments, "r_plain")
    extra = _find_argument(arguments, "r_extra")
    criterion = GeneralizedSpecificity(theory)

    assert not criterion.prefers(extra, plain)
    assert not criterion.prefers(plain, extra)


def test_stolzenburg_fact_replacement_changes_specificity_result() -> None:
    """Stolzenburg p.10: replacing strict ``s(X) <- q(X)`` with fact ``s(a)`` matters."""

    theory = DefeasibleTheory(
        facts={"q": {("a",)}, "s": {("a",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r_plain", head="p(X)", body=["q(X)"]),
            Rule(id="r_extra", head="~p(X)", body=["q(X)", "s(X)"]),
        ],
    )

    arguments = build_arguments(theory)
    plain = _find_argument(arguments, "r_plain")
    extra = _find_argument(arguments, "r_extra")
    criterion = GeneralizedSpecificity(theory)

    assert criterion.prefers(extra, plain)
    assert not criterion.prefers(plain, extra)


def test_stolzenburg_activation_set_algorithm_is_cited_on_public_criterion() -> None:
    """Stolzenburg Figure 3, page-014.png, is load-bearing for Gunray docs."""

    assert STOLZENBURG_PAGE_014.endswith("page-013.png")
    assert "Stolzenburg" in (GeneralizedSpecificity.__doc__ or "")
    assert "page-013.png" in (GeneralizedSpecificity.__doc__ or "")


@st.composite
def strict_chain_case(draw: st.DrawFn) -> tuple[int, int]:
    left_index = draw(st.integers(min_value=0, max_value=4))
    right_index = draw(st.integers(min_value=0, max_value=4))
    return left_index, right_index


def _chain_theory(left_index: int, right_index: int) -> tuple[DefeasibleTheory, str, str]:
    facts = {"p0": {("a",)}, "irrelevant": {("z",)}}
    strict_rules = [Rule(id=f"s{i}", head=f"p{i + 1}(X)", body=[f"p{i}(X)"]) for i in range(4)]
    left_rule_id = "r_left"
    right_rule_id = "r_right"
    return (
        DefeasibleTheory(
            facts=facts,
            strict_rules=strict_rules,
            defeasible_rules=[
                Rule(id=left_rule_id, head="h(X)", body=[f"p{left_index}(X)"]),
                Rule(id=right_rule_id, head="~h(X)", body=[f"p{right_index}(X)"]),
            ],
        ),
        left_rule_id,
        right_rule_id,
    )


@given(case=strict_chain_case())
@settings(max_examples=50, deadline=None)
def test_hypothesis_strict_chain_matches_independent_antecedent_oracle(
    case: tuple[int, int],
) -> None:
    """For strict chains, lower-index antecedents cover higher-index antecedents."""

    left_index, right_index = case
    theory, left_rule_id, right_rule_id = _chain_theory(left_index, right_index)
    arguments = build_arguments(theory)
    left = _find_argument(arguments, left_rule_id)
    right = _find_argument(arguments, right_rule_id)
    criterion = GeneralizedSpecificity(theory)

    left_prefers = left_index < right_index
    right_prefers = right_index < left_index

    assert criterion.prefers(left, right) is left_prefers
    assert criterion.prefers(right, left) is right_prefers


@given(case=strict_chain_case())
@settings(max_examples=50, deadline=None)
def test_hypothesis_adding_irrelevant_fact_predicate_preserves_comparison(
    case: tuple[int, int],
) -> None:
    """Stolzenburg p.8 non-trivial activation depends on relevant antecedent coverage."""

    left_index, right_index = case
    base, left_rule_id, right_rule_id = _chain_theory(left_index, right_index)
    with_extra_fact = DefeasibleTheory(
        facts={predicate: set(rows) for predicate, rows in base.facts.items()}
        | {"unused_fact": {("u",)}},
        strict_rules=list(base.strict_rules),
        defeasible_rules=list(base.defeasible_rules),
    )

    base_args = build_arguments(base)
    extra_args = build_arguments(with_extra_fact)
    base_left = _find_argument(base_args, left_rule_id)
    base_right = _find_argument(base_args, right_rule_id)
    extra_left = _find_argument(extra_args, left_rule_id)
    extra_right = _find_argument(extra_args, right_rule_id)

    assert GeneralizedSpecificity(base).prefers(base_left, base_right) is (
        GeneralizedSpecificity(with_extra_fact).prefers(extra_left, extra_right)
    )
