"""Paper-example and property tests for ``SuperiorityPreference``.

Garcia & Simari 2004 §4.1 — rule priority criterion. Given an explicit
priority relation on defeasible rules, an argument ``<A1, h1>`` is
preferred to ``<A2, h2>`` iff every rule in ``A1`` dominates every rule
in ``A2`` under the transitive closure of the priority relation.

This module pins paper-flavoured examples plus Hypothesis properties
verifying the strict-partial-order axioms (irreflexivity, transitivity,
antisymmetry over acyclic priority relations) and the first-criterion-
to-fire semantics of ``CompositePreference`` (asymmetry + monotonicity).
"""

from __future__ import annotations

import random

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from gunray.arguments import Argument, build_arguments
from gunray.preference import (
    CompositePreference,
    GeneralizedSpecificity,
    SuperiorityPreference,
)
from gunray.schema import DefeasibleTheory, Rule

from conftest import small_theory_strategy


# ---------------------------------------------------------------------------
# Paper-example theories
# ---------------------------------------------------------------------------


def _direct_pair_theory() -> DefeasibleTheory:
    """Two conflicting defeasible rules with identical antecedents.

    ``r1: flies :- bird`` and ``r2: ~flies :- bird`` are equi-specific
    under Lemma 2.4 (identical antecedents → mutual coverage), so only
    the explicit superiority list ``[(r1, r2)]`` can break the tie.
    """

    return DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["bird(X)"]),
        ],
        defeaters=[],
        superiority=[("r1", "r2")],
        conflicts=[],
    )


def _transitive_chain_theory() -> DefeasibleTheory:
    """Three equi-specific rules with chained superiority ``r1 > r2 > r3``."""

    return DefeasibleTheory(
        facts={"p": {("a",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="q(X)", body=["p(X)"]),
            Rule(id="r2", head="r(X)", body=["p(X)"]),
            Rule(id="r3", head="s(X)", body=["p(X)"]),
        ],
        defeaters=[],
        superiority=[("r1", "r2"), ("r2", "r3")],
        conflicts=[],
    )


def _partial_dominance_theory() -> DefeasibleTheory:
    """Two-rule left arg vs one-rule right arg with only partial dominance.

    ``left.rules = {r1, r2}``, ``right.rules = {r3}``,
    ``superiority = [(r1, r3)]``. ``r2`` has no priority entry over
    ``r3``, so the dominance check must fail (every rule in left must
    dominate every rule in right).
    """

    # We construct the arguments by hand below — the theory is just a
    # vehicle to ground the rules consistently.
    return DefeasibleTheory(
        facts={"p": {("a",)}, "q": {("a",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="x(X)", body=["p(X)"]),
            Rule(id="r2", head="y(X)", body=["q(X)"]),
            Rule(id="r3", head="z(X)", body=["p(X)"]),
        ],
        defeaters=[],
        superiority=[("r1", "r3")],
        conflicts=[],
    )


def _composite_inversion_theory() -> DefeasibleTheory:
    """Specificity says r1 > r2; superiority says r2 > r1.

    ``r1: ~flies :- penguin`` is strictly more specific than
    ``r2: flies :- bird`` under Lemma 2.4 (penguin → bird strictly).
    But the explicit superiority pair ``(r2, r1)`` says r2 is the
    higher-priority rule. Composition with superiority-first must
    return ``r2`` as the preferred argument.
    """

    return DefeasibleTheory(
        facts={"bird": {("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="~flies(X)", body=["penguin(X)"]),
            Rule(id="r2", head="flies(X)", body=["bird(X)"]),
        ],
        defeaters=[],
        superiority=[("r2", "r1")],
        conflicts=[],
    )


def _opus_specificity_only_theory() -> DefeasibleTheory:
    """Standard Opus theory with no superiority pairs.

    ``r2: ~flies :- penguin`` is strictly more specific than
    ``r1: flies :- bird``. With no superiority pairs, the composite
    must fall through to ``GeneralizedSpecificity`` and prefer ``r2``.
    """

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


def _strict_only_theory() -> DefeasibleTheory:
    """Theory whose only arguments are strict-only (empty rule set)."""

    return DefeasibleTheory(
        facts={"p": {("a",)}},
        strict_rules=[Rule(id="s1", head="q(X)", body=["p(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="r(X)", body=["p(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _find_argument(args: frozenset[Argument], rule_id: str) -> Argument:
    for arg in args:
        if any(r.rule_id == rule_id for r in arg.rules):
            return arg
    raise AssertionError(f"no argument found for rule id {rule_id!r}")


def _find_strict_only(args: frozenset[Argument]) -> Argument:
    for arg in args:
        if not arg.rules:
            return arg
    raise AssertionError("no strict-only argument found")


# ---------------------------------------------------------------------------
# Task 4 — paper-example unit tests
# ---------------------------------------------------------------------------


def test_superiority_direct_pair() -> None:
    """Direct ``(r1, r2)`` superiority pair: r1 strictly preferred to r2."""

    theory = _direct_pair_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")
    r2_arg = _find_argument(args, "r2")
    criterion = SuperiorityPreference(theory)

    assert criterion.prefers(r1_arg, r2_arg) is True
    assert criterion.prefers(r2_arg, r1_arg) is False


def test_superiority_transitive_closure() -> None:
    """Transitive closure: ``(r1, r2)`` and ``(r2, r3)`` → ``(r1, r3)``."""

    theory = _transitive_chain_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")
    r3_arg = _find_argument(args, "r3")
    criterion = SuperiorityPreference(theory)

    assert criterion.prefers(r1_arg, r3_arg) is True
    assert criterion.prefers(r3_arg, r1_arg) is False


def test_superiority_strict_vs_defeasible_incomparable() -> None:
    """Strict-only argument vs defeasible argument: neither preferred.

    Strict-only arguments carry an empty rule set; the dominance check
    is vacuously satisfied for the empty side, but the paper treats
    strict and defeasible arguments as incomparable under the rule
    priority criterion. The test pins ``prefers`` returning False in
    both directions for the edge case.
    """

    theory = _strict_only_theory()
    args = build_arguments(theory)
    strict_arg = _find_strict_only(args)
    defeasible_arg = _find_argument(args, "r1")
    criterion = SuperiorityPreference(theory)

    assert criterion.prefers(strict_arg, defeasible_arg) is False
    assert criterion.prefers(defeasible_arg, strict_arg) is False


def test_superiority_self_irreflexive() -> None:
    """``prefers(a, a) is False`` for every argument."""

    theory = _direct_pair_theory()
    args = build_arguments(theory)
    criterion = SuperiorityPreference(theory)
    for arg in args:
        assert criterion.prefers(arg, arg) is False


def test_superiority_partial_dominance_fails() -> None:
    """``left.rules = {r1, r2}`` vs ``right.rules = {r3}`` with only ``(r1, r3)``.

    ``r2`` has no superiority entry over ``r3``. The dominance check
    must require *every* rule in left to dominate *every* rule in right,
    so partial dominance fails and ``prefers`` returns False.
    """

    theory = _partial_dominance_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")
    r2_arg = _find_argument(args, "r2")
    r3_arg = _find_argument(args, "r3")

    # Synthesise a multi-rule "left" argument by union of r1 and r2's
    # rule sets; conclusion choice is irrelevant for the priority check.
    left_rules = r1_arg.rules | r2_arg.rules
    left = Argument(rules=left_rules, conclusion=r1_arg.conclusion)
    criterion = SuperiorityPreference(theory)

    assert criterion.prefers(left, r3_arg) is False


def test_composite_superiority_over_specificity() -> None:
    """Specificity says r1 > r2; superiority says r2 > r1.

    Under first-criterion-to-fire semantics with superiority placed
    first, superiority monopolises the answer for this pair:
    ``composite.prefers(r2, r1)`` is True and the symmetric call
    ``composite.prefers(r1, r2)`` must be False (asymmetry).
    """

    theory = _composite_inversion_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")  # ~flies :- penguin (more specific)
    r2_arg = _find_argument(args, "r2")  # flies :- bird     (superior)

    spec = GeneralizedSpecificity(theory)
    sup = SuperiorityPreference(theory)
    composite = CompositePreference(sup, spec)

    # Sanity: specificity alone prefers r1; superiority alone prefers r2.
    assert spec.prefers(r1_arg, r2_arg) is True
    assert sup.prefers(r2_arg, r1_arg) is True

    # First-fire: superiority is consulted first. It prefers r2 over r1,
    # so the composite prefers r2 over r1 and — crucially — does NOT
    # prefer r1 over r2 even though specificity would have said yes.
    # Asymmetry holds by construction of the first-fire rule.
    assert composite.prefers(r2_arg, r1_arg) is True
    assert composite.prefers(r1_arg, r2_arg) is False


class _MockPreference:
    """Minimal preference criterion for first-fire wiring tests.

    Stores an explicit ``(left_id, right_id)`` pair and returns True
    only for that exact direction. Used to prove that composite order
    matters and that the first criterion to fire monopolises the
    answer, regardless of what a later criterion would have said.
    """

    def __init__(self, prefer_pair: tuple[str, str] | None = None) -> None:
        self._pair = prefer_pair

    def prefers(self, left: Argument, right: Argument) -> bool:
        if self._pair is None:
            return False
        left_id = next(iter(sorted(r.rule_id for r in left.rules)), "")
        right_id = next(iter(sorted(r.rule_id for r in right.rules)), "")
        return (left_id, right_id) == self._pair


def test_composite_first_criterion_to_fire_mock() -> None:
    """First-fire: criterion ordering decides which direction wins.

    Two mock criteria disagree on direction for the pair (a, b).
    ``CompositePreference(first, second)`` must return ``first``'s
    answer and never consult ``second`` once ``first`` has fired in
    either direction. Swapping the order flips the answer.
    """

    # Use any theory whose build_arguments returns two distinct
    # single-rule arguments we can name by rule id.
    theory = _direct_pair_theory()
    args = build_arguments(theory)
    a = _find_argument(args, "r1")
    b = _find_argument(args, "r2")

    prefer_a_over_b = _MockPreference(("r1", "r2"))
    prefer_b_over_a = _MockPreference(("r2", "r1"))

    # Superiority-like criterion first, specificity-like criterion
    # second: the first to fire wins.
    sup_first = CompositePreference(prefer_a_over_b, prefer_b_over_a)
    assert sup_first.prefers(a, b) is True
    assert sup_first.prefers(b, a) is False

    # Swap order: now the other criterion decides.
    spec_first = CompositePreference(prefer_b_over_a, prefer_a_over_b)
    assert spec_first.prefers(a, b) is False
    assert spec_first.prefers(b, a) is True

    # Asymmetry holds in both orderings.
    for composite in (sup_first, spec_first):
        assert not (composite.prefers(a, b) and composite.prefers(b, a))


def test_composite_first_criterion_falls_through_when_silent() -> None:
    """Silent-on-both means the composite consults the next criterion."""

    theory = _direct_pair_theory()
    args = build_arguments(theory)
    a = _find_argument(args, "r1")
    b = _find_argument(args, "r2")

    silent = _MockPreference(None)  # prefers nothing in either direction
    prefer_a_over_b = _MockPreference(("r1", "r2"))

    composite = CompositePreference(silent, prefer_a_over_b)
    assert composite.prefers(a, b) is True
    assert composite.prefers(b, a) is False


def test_composite_specificity_fallback() -> None:
    """No superiority pairs: composite falls through to specificity."""

    theory = _opus_specificity_only_theory()
    args = build_arguments(theory)
    r1_arg = _find_argument(args, "r1")  # flies :- bird
    r2_arg = _find_argument(args, "r2")  # ~flies :- penguin (more specific)

    spec = GeneralizedSpecificity(theory)
    sup = SuperiorityPreference(theory)
    composite = CompositePreference(sup, spec)

    assert sup.prefers(r2_arg, r1_arg) is False  # no superiority pair
    assert spec.prefers(r2_arg, r1_arg) is True  # specificity says yes
    assert composite.prefers(r2_arg, r1_arg) is True  # fallback fires
    assert composite.prefers(r1_arg, r2_arg) is False


# ---------------------------------------------------------------------------
# Task 5 — Hypothesis property tests
# ---------------------------------------------------------------------------


@st.composite
def theory_with_random_superiority(
    draw: st.DrawFn,
) -> tuple[DefeasibleTheory, tuple[Argument, ...]]:
    """Draw a small theory and decorate it with a random acyclic
    superiority list over its defeasible rule ids.

    Uses a topological order over the rule ids: only ``(higher, lower)``
    pairs are emitted, which guarantees acyclicity.
    """

    base = draw(small_theory_strategy())
    rule_ids = [r.id for r in base.defeasible_rules]
    pairs: list[tuple[str, str]] = []
    if len(rule_ids) >= 2:
        # Random topological order via a drawn permutation seed.
        seed = draw(st.integers(min_value=0, max_value=2**31 - 1))
        order = list(rule_ids)
        random.Random(seed).shuffle(order)
        # Emit a random subset of (earlier, later) pairs.
        for i, higher in enumerate(order):
            for lower in order[i + 1 :]:
                if draw(st.booleans()):
                    pairs.append((higher, lower))

    theory = DefeasibleTheory(
        facts={pred: set(rows) for pred, rows in base.facts.items()},
        strict_rules=list(base.strict_rules),
        defeasible_rules=list(base.defeasible_rules),
        defeaters=[],
        superiority=pairs,
        conflicts=[],
    )
    args = tuple(build_arguments(theory))
    assume(len(args) > 0)
    return theory, args


@given(pair=theory_with_random_superiority(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_superiority_is_irreflexive(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """``SuperiorityPreference.prefers(a, a) is False`` for any argument."""

    theory, args = pair
    criterion = SuperiorityPreference(theory)
    a = args[data.draw(st.integers(min_value=0, max_value=len(args) - 1))]
    assert criterion.prefers(a, a) is False


@given(pair=theory_with_random_superiority(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_superiority_is_transitive(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Closure semantics: ``prefers(a,b)`` & ``prefers(b,c)`` → ``prefers(a,c)``."""

    theory, args = pair
    criterion = SuperiorityPreference(theory)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    c = args[data.draw(idx)]
    if criterion.prefers(a, b) and criterion.prefers(b, c):
        assert criterion.prefers(a, c)


@given(pair=theory_with_random_superiority(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_superiority_is_antisymmetric(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """Acyclic superiority ⇒ never both ``prefers(a, b)`` and ``prefers(b, a)``.

    The strategy only emits (higher, lower) pairs over a randomly
    chosen topological order, so the priority relation is acyclic by
    construction. Antisymmetry must hold.
    """

    theory, args = pair
    criterion = SuperiorityPreference(theory)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    assert not (criterion.prefers(a, b) and criterion.prefers(b, a))


@given(pair=theory_with_random_superiority(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_composite_is_monotonic(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """First-fire monotonicity: ``Composite.prefers(a, b)`` ⇒ at least
    one child criterion prefers ``a`` over ``b`` at the point the
    composite fires. (Under first-criterion-to-fire semantics the
    child that fires is the *first* one to prefer either direction;
    this property verifies the weaker monotonicity guarantee that
    *some* child agreed with the composite's answer.)
    """

    theory, args = pair
    sup = SuperiorityPreference(theory)
    spec = GeneralizedSpecificity(theory)
    composite = CompositePreference(sup, spec)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    if composite.prefers(a, b):
        assert sup.prefers(a, b) or spec.prefers(a, b)


@given(pair=theory_with_random_superiority(), data=st.data())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hypothesis_composite_is_asymmetric(
    pair: tuple[DefeasibleTheory, tuple[Argument, ...]],
    data: st.DataObject,
) -> None:
    """First-fire asymmetry: ``Composite.prefers(a, b)`` and
    ``Composite.prefers(b, a)`` are never both True.

    When each underlying criterion is a strict partial order (which
    ``SuperiorityPreference`` is over acyclic superiority lists and
    ``GeneralizedSpecificity`` is by Simari & Loui 1992 Lemma 2.4),
    first-criterion-to-fire composition preserves asymmetry: the
    first criterion to express an opinion monopolises the answer
    for that pair, and a strict partial order cannot prefer both
    directions simultaneously.
    """

    theory, args = pair
    sup = SuperiorityPreference(theory)
    spec = GeneralizedSpecificity(theory)
    composite = CompositePreference(sup, spec)
    idx = st.integers(min_value=0, max_value=len(args) - 1)
    a = args[data.draw(idx)]
    b = args[data.draw(idx)]
    assert not (composite.prefers(a, b) and composite.prefers(b, a))
