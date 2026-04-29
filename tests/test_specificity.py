"""Paper-example and property tests for ``GeneralizedSpecificity``.

Simari & Loui 1992 Lemma 2.4 reduces strict specificity to an
antecedent-only check over the necessary context ``K_N`` (the strict
rule set). This test module pins the canonical examples from the
literature (Opus/Penguin, Nixon Diamond, Royal African Elephants) and
four Hypothesis properties that encode the strict-partial-order
axioms the criterion must satisfy.
"""

from __future__ import annotations

from conftest import small_theory_strategy
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from gunray.arguments import Argument, build_arguments
from gunray.preference import GeneralizedSpecificity
from gunray.schema import DefeasibleTheory, Rule

# ---------------------------------------------------------------------------
# Paper-example theories
# ---------------------------------------------------------------------------


def _opus_theory() -> DefeasibleTheory:
    """Simari 92 §5 p.29 Opus / Penguin canonical specificity example."""

    return DefeasibleTheory(
        facts={"bird": {("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _nixon_theory() -> DefeasibleTheory:
    """Simari 92 §5 p.30 / Goldszmidt 92 Example 1 Nixon Diamond.

    Uses the simpler form (``republican(nixon)`` / ``quaker(nixon)``
    directly as facts). Under Simari 92 specificity neither defeasible
    argument is preferred; both premises are equi-specific.
    """

    return DefeasibleTheory(
        facts={"republican": {("nixon",)}, "quaker": {("nixon",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="~pacifist(X)", body=["republican(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _tweety_theory() -> DefeasibleTheory:
    """Garcia & Simari 04 §3 Tweety/Opus combined theory.

    ``tweety`` is only a bird; ``opus`` is a penguin (hence bird by
    the strict rule). ``~flies(tweety)`` has no defeasible support.
    """

    return DefeasibleTheory(
        facts={
            "bird": {("tweety",), ("opus",)},
            "penguin": {("opus",)},
        },
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _elephant_theory() -> DefeasibleTheory:
    """Simari 92 §5 p.32 Royal African Elephants (off-path preemption).

    ``royal_elephant(clyde)`` is strict-closed to
    ``african_elephant(clyde)`` and ``elephant(clyde)``. The defeasible
    rule rooted at the more-specific premise ``african_elephant`` must
    be preferred over the one rooted at the less-specific premise
    ``elephant``.
    """

    return DefeasibleTheory(
        facts={"royal_elephant": {("clyde",)}},
        strict_rules=[
            Rule(id="s1", head="elephant(X)", body=["african_elephant(X)"]),
            Rule(id="s2", head="african_elephant(X)", body=["royal_elephant(X)"]),
        ],
        defeasible_rules=[
            Rule(id="d1", head="~gray(X)", body=["elephant(X)"]),
            Rule(id="d2", head="gray(X)", body=["african_elephant(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _strict_only_theory() -> DefeasibleTheory:
    """Minimal theory whose only arguments are empty-rule strict conclusions."""

    return DefeasibleTheory(
        facts={"p": {("a",)}},
        strict_rules=[Rule(id="s1", head="q(X)", body=["p(X)"])],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _garcia_tina_theory() -> DefeasibleTheory:
    """Garcia & Simari 2004 p. 108 Example 3.5 Tina bird/chicken theory."""

    return DefeasibleTheory(
        facts={"chicken": {("tina",)}, "scared": {("tina",)}},
        strict_rules=[Rule(id="s_chicken_bird", head="bird(X)", body=["chicken(X)"])],
        defeasible_rules=[
            Rule(id="r_bird_flies", head="flies(X)", body=["bird(X)"]),
            Rule(id="r_chicken_not_flies", head="~flies(X)", body=["chicken(X)"]),
            Rule(
                id="r_scared_chicken_flies",
                head="flies(X)",
                body=["chicken(X)", "scared(X)"],
            ),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _find_argument(args: frozenset[Argument], rule_id: str) -> Argument:
    """Locate the argument whose rule set contains ``rule_id``."""

    for arg in args:
        if any(r.rule_id == rule_id for r in arg.rules):
            return arg
    raise AssertionError(f"no argument found for rule id {rule_id!r}")


# ---------------------------------------------------------------------------
# Paper-example unit tests
# ---------------------------------------------------------------------------


def test_opus_prefers_penguin_over_bird() -> None:
    """Simari 92 §5 p.29: penguin is strictly more specific than bird.

    The strict rule ``bird(X) :- penguin(X)`` means every scenario
    activating ``r2`` also activates ``r1`` but not vice versa, so
    Lemma 2.4 yields a strict preference of ``r2`` over ``r1``.
    """

    theory = _opus_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")
    r2_arg = _find_argument(args, "r2")
    criterion = GeneralizedSpecificity(theory)

    assert criterion.prefers(r2_arg, r1_arg) is True
    assert criterion.prefers(r1_arg, r2_arg) is False


def test_tweety_flies_unopposed() -> None:
    """Garcia 04 §3 Tweety: ``GeneralizedSpecificity`` constructs cleanly.

    Tweety has no counter-argument for ``~flies(tweety)`` so there is
    nothing to compare. This smoke test asserts only that instantiating
    the criterion over the full theory does not explode.
    """

    theory = _tweety_theory()
    criterion = GeneralizedSpecificity(theory)
    args = build_arguments(theory)
    # Sanity: every argument is self-equi-specific.
    for arg in args:
        assert criterion.prefers(arg, arg) is False


def test_nixon_diamond_equi_specific() -> None:
    """Simari 92 §5 p.30 Nixon Diamond: neither argument is preferred.

    ``republican`` and ``quaker`` are both raw facts and neither
    antecedent is strict-entailed by the other, so Lemma 2.4 returns
    equi-specific for both defeasible arguments.
    """

    theory = _nixon_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")
    r2_arg = _find_argument(args, "r2")
    criterion = GeneralizedSpecificity(theory)

    assert criterion.prefers(r1_arg, r2_arg) is False
    assert criterion.prefers(r2_arg, r1_arg) is False


def test_royal_elephants_off_path() -> None:
    """Simari 92 §5 p.32 Royal African Elephants: off-path preemption.

    The defeasible rule rooted at the more-specific premise
    ``african_elephant`` is strictly preferred over the one rooted at
    the less-specific ``elephant``. The strict cascade
    ``elephant ← african_elephant`` encodes the class relationship.
    """

    theory = _elephant_theory()
    args = build_arguments(theory)
    d1_arg = _find_argument(args, "d1")  # ~gray via elephant
    d2_arg = _find_argument(args, "d2")  # gray via african_elephant
    criterion = GeneralizedSpecificity(theory)

    assert criterion.prefers(d2_arg, d1_arg) is True
    assert criterion.prefers(d1_arg, d2_arg) is False


def test_garcia_example_35_reports_specificity_direction() -> None:
    """Garcia & Simari 2004 p. 108 Ex. 3.5: Tina's chicken rules outrank bird."""

    theory = _garcia_tina_theory()
    args = build_arguments(theory)
    bird_flies = _find_argument(args, "r_bird_flies")
    chicken_not_flies = _find_argument(args, "r_chicken_not_flies")
    scared_chicken_flies = _find_argument(args, "r_scared_chicken_flies")
    criterion = GeneralizedSpecificity(theory)

    chicken_vs_bird = criterion.compare(chicken_not_flies, bird_flies)
    assert chicken_vs_bird.relation == "left"
    assert chicken_vs_bird.left_prefers is True
    assert chicken_vs_bird.right_prefers is False
    assert chicken_vs_bird.citation == "Garcia & Simari 2004, p. 108"

    scared_vs_chicken = criterion.compare(scared_chicken_flies, chicken_not_flies)
    assert scared_vs_chicken.relation == "left"
    assert scared_vs_chicken.left_prefers is True
    assert scared_vs_chicken.right_prefers is False
    assert scared_vs_chicken.citation == "Garcia & Simari 2004, p. 108"


def test_strict_only_arguments_incomparable() -> None:
    """Empty-rule arguments are equi-specific (vacuous coverage)."""

    theory = _strict_only_theory()
    args = build_arguments(theory)
    strict_only = [a for a in args if not a.rules]
    assert len(strict_only) >= 2  # p(a) and q(a)
    criterion = GeneralizedSpecificity(theory)
    for left in strict_only:
        for right in strict_only:
            assert criterion.prefers(left, right) is False


def test_generalized_specificity_does_not_prefer_defeasible_over_strict_empty_rules() -> None:
    """Simari 92 Lemma 2.4: a purely strict argument is not dominated."""
    theory = DefeasibleTheory(
        facts={"p": {("a",)}, "q": {("a",)}},
        strict_rules=[Rule(id="s1", head="h(X)", body=["p(X)"])],
        defeasible_rules=[Rule(id="d1", head="h(X)", body=["q(X)"])],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )
    criterion = GeneralizedSpecificity(theory)
    args = list(build_arguments(theory))
    strict_arg = next(arg for arg in args if not arg.rules and arg.conclusion.predicate == "h")
    defeasible_arg = next(
        arg
        for arg in args
        if any(rule.rule_id == "d1" for rule in arg.rules) and arg.conclusion.predicate == "h"
    )

    assert not criterion.prefers(defeasible_arg, strict_arg)


def test_self_comparison_never_prefers() -> None:
    """``prefers(a, a) is False`` for every argument over Opus theory."""

    theory = _opus_theory()
    criterion = GeneralizedSpecificity(theory)
    for arg in build_arguments(theory):
        assert criterion.prefers(arg, arg) is False


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------


@st.composite
def theory_with_arguments(
    draw: st.DrawFn,
) -> tuple[DefeasibleTheory, tuple[Argument, ...]]:
    theory = draw(small_theory_strategy())
    args = tuple(build_arguments(theory))
    assume(len(args) > 0)
    return theory, args


@given(pair=theory_with_arguments(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_specificity_is_irreflexive(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Strict partial order axiom: ``prefers(a, a) is False`` for all ``a``."""

    theory, args = pair
    criterion = GeneralizedSpecificity(theory)
    a = args[data.draw(st.integers(min_value=0, max_value=len(args) - 1))]
    assert criterion.prefers(a, a) is False


@given(pair=theory_with_arguments(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_specificity_is_antisymmetric(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Strict partial order: never both ``prefers(a,b)`` and ``prefers(b,a)``."""

    theory, args = pair
    criterion = GeneralizedSpecificity(theory)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    assert not (criterion.prefers(a, b) and criterion.prefers(b, a))


@given(pair=theory_with_arguments(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_specificity_is_transitive(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Strict partial order: ``prefers(a,b)`` & ``prefers(b,c)`` → ``prefers(a,c)``."""

    theory, args = pair
    criterion = GeneralizedSpecificity(theory)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    c = args[data.draw(idx)]
    if criterion.prefers(a, b) and criterion.prefers(b, c):
        assert criterion.prefers(a, c)


@given(pair=theory_with_arguments(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_specificity_is_determined(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Purity: repeated calls with the same inputs return the same result."""

    theory, args = pair
    criterion = GeneralizedSpecificity(theory)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    first = criterion.prefers(a, b)
    second = criterion.prefers(a, b)
    third = GeneralizedSpecificity(theory).prefers(a, b)
    assert first == second == third


@given(small_theory_strategy())
@settings(max_examples=200, deadline=None)
def test_hypothesis_genspec_does_not_dominate_empty_rules_side(
    theory: DefeasibleTheory,
) -> None:
    """No argument with non-empty rules strictly prefers an empty-rules argument."""
    criterion = GeneralizedSpecificity(theory)
    args = list(build_arguments(theory))
    empty_args = [arg for arg in args if not arg.rules]
    nonempty_args = [arg for arg in args if arg.rules]

    for empty in empty_args:
        for nonempty in nonempty_args:
            assert not criterion.prefers(nonempty, empty), (
                f"Non-empty {nonempty} preferred over empty {empty}"
            )
