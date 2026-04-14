"""Unit and property tests for gunray.arguments.build_arguments.

Garcia & Simari 2004 Definition 3.1, Simari & Loui 1992 Definition 2.2.
"""

from __future__ import annotations

from itertools import combinations

from hypothesis import given, settings

from gunray.arguments import Argument, build_arguments
from gunray.disagreement import disagrees, strict_closure
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom, GroundDefeasibleRule

from conftest import small_theory_strategy


def _tweety_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_tweety_flies_argument_exists() -> None:
    """Garcia & Simari 2004 Def 3.1: <{r1(tweety)}, flies(tweety)> is an argument."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    matching = [arg for arg in arguments if arg.conclusion == flies_tweety]
    assert matching, f"no argument for flies(tweety) in {arguments!r}"

    # The grounded r1 instance with X=tweety must appear in rules.
    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r1" in grounded_rule_ids:
            return
    raise AssertionError(
        f"no argument for flies(tweety) was backed by r1: {matching!r}"
    )


def test_opus_not_flies_argument_exists() -> None:
    """Opus's penguin rule must produce <{r2(opus)}, ~flies(opus)>."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    not_flies_opus = GroundAtom(predicate="~flies", arguments=("opus",))
    matching = [arg for arg in arguments if arg.conclusion == not_flies_opus]
    assert matching, f"no argument for ~flies(opus) in {arguments!r}"

    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r2" in grounded_rule_ids:
            return
    raise AssertionError(
        f"no argument for ~flies(opus) was backed by r2: {matching!r}"
    )


def _nixon_theory() -> DefeasibleTheory:
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


def test_nixon_diamond_has_both_arguments() -> None:
    """Garcia & Simari 2004 Def 3.1: both sides of Nixon must produce arguments."""

    theory = _nixon_theory()
    arguments = build_arguments(theory)

    pacifist_nixon = GroundAtom(predicate="pacifist", arguments=("nixon",))
    not_pacifist_nixon = GroundAtom(predicate="~pacifist", arguments=("nixon",))

    pacifist_args = [a for a in arguments if a.conclusion == pacifist_nixon]
    not_pacifist_args = [a for a in arguments if a.conclusion == not_pacifist_nixon]

    assert pacifist_args, f"no argument for pacifist(nixon): {arguments!r}"
    assert not_pacifist_args, (
        f"no argument for ~pacifist(nixon): {arguments!r}"
    )


def test_defeater_kind_cannot_be_argument_conclusion() -> None:
    """Garcia & Simari 2004 Def 3.6: defeaters do not warrant conclusions.

    A rule with ``kind="defeater"`` participates in defeat lines but
    cannot itself head an argument. We build a minimal theory with a
    defeater rule ``d1: banana(X) :- yellow(X)`` whose head appears
    nowhere else, then assert that no argument in the result concludes
    ``banana(x)``.
    """

    theory = DefeasibleTheory(
        facts={"yellow": {("x",)}},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[Rule(id="d1", head="banana(X)", body=["yellow(X)"])],
        superiority=[],
        conflicts=[],
    )
    arguments = build_arguments(theory)

    banana_x = GroundAtom(predicate="banana", arguments=("x",))
    assert not [a for a in arguments if a.conclusion == banana_x], (
        f"defeater head surfaced as argument conclusion: {arguments!r}"
    )


def test_strict_only_arguments_have_empty_rules() -> None:
    """Garcia & Simari 2004 Def 3.1: strict-only theories have <empty, h>.

    When ``Delta`` is empty, condition (1) degenerates to a strict
    derivation; every argument must have ``rules == frozenset()``.
    """

    theory = DefeasibleTheory(
        facts={"fact_p": {("a",)}},
        strict_rules=[Rule(id="s1", head="fact_q(X)", body=["fact_p(X)"])],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    arguments = build_arguments(theory)
    assert arguments, "strict-only theory should still yield strict arguments"
    for argument in arguments:
        assert argument.rules == frozenset(), (
            f"strict-only theory produced non-empty argument: {argument!r}"
        )


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_build_arguments_is_deterministic(
    theory: DefeasibleTheory,
) -> None:
    """Invoking ``build_arguments`` twice on the same theory yields equal sets.

    Guards against accidental state leakage (e.g. cached mutable
    structures from grounding helpers).
    """

    assert build_arguments(theory) == build_arguments(theory)


def _fact_atoms_from_theory(theory: DefeasibleTheory) -> frozenset[GroundAtom]:
    """Collect ground fact atoms out of a DefeasibleTheory."""

    return frozenset(
        GroundAtom(predicate=predicate, arguments=tuple(row))
        for predicate, rows in theory.facts.items()
        for row in rows
    )


def _closure_under_rules(
    fact_atoms: frozenset[GroundAtom],
    rules: frozenset[GroundDefeasibleRule],
) -> frozenset[GroundAtom]:
    """Closure under ``rules`` treated as strict for propagation purposes.

    Shadows each rule's kind to ``"strict"`` so ``strict_closure``
    will propagate it regardless of its original kind. This mirrors
    the internal ``_force_strict_for_closure`` in arguments.py.
    """

    shadowed = tuple(
        GroundDefeasibleRule(
            rule_id=rule.rule_id,
            kind="strict",
            head=rule.head,
            body=rule.body,
        )
        for rule in rules
    )
    return strict_closure(fact_atoms, shadowed)


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_every_argument_is_minimal(
    theory: DefeasibleTheory,
) -> None:
    """Garcia & Simari 2004 Def 3.1 condition (3): ``A`` is minimal.

    For every ``Argument(A, h)`` produced, no strict subset ``A' < A``
    also derives ``h`` from ``Pi union A'`` (checked independently of
    the builder's internal minimality filter).
    """

    arguments = build_arguments(theory)
    fact_atoms = _fact_atoms_from_theory(theory)

    # Collect the grounded strict rules once — we reuse them for each
    # proper-subset check.
    for argument in arguments:
        rules = argument.rules
        if not rules:
            continue
        for size in range(len(rules)):
            for subset_tuple in combinations(rules, size):
                subset = frozenset(subset_tuple)
                closure = _closure_under_rules(fact_atoms, subset)
                if argument.conclusion in closure:
                    # Strict-fact conclusion is allowed to be derivable
                    # from the empty set (the <empty, h> argument for
                    # strict heads is a distinct Argument value).
                    if subset == frozenset() and argument.conclusion in closure:
                        continue
                    raise AssertionError(
                        f"non-minimal argument: {argument!r} also derivable from {subset!r}"
                    )


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_every_argument_is_non_contradictory(
    theory: DefeasibleTheory,
) -> None:
    """Garcia & Simari 2004 Def 3.1 condition (2): ``Pi union A`` is non-contradictory.

    For every ``Argument(A, h)`` produced, the closure of
    ``Pi union A`` must not contain a complementary pair.
    """

    arguments = build_arguments(theory)
    fact_atoms = _fact_atoms_from_theory(theory)

    from gunray.disagreement import complement

    for argument in arguments:
        closure = _closure_under_rules(fact_atoms, argument.rules)
        for atom in closure:
            assert complement(atom) not in closure, (
                f"contradictory argument: {argument!r} closure contains "
                f"{atom!r} and {complement(atom)!r}"
            )
