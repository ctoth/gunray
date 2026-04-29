"""Unit and property tests for gunray.answer (Garcia & Simari 2004 Def 5.3).

This file covers two surfaces:

- The ``Answer`` enum itself (B1.2 foundation, Garcia 04 Def 5.3).
- The ``answer(theory, literal, criterion)`` query API (B1.5), which
  implements Def 5.3's four-valued warrant query on top of the
  dialectical tree machinery from B1.4.
"""

from __future__ import annotations

from conftest import ground_atom_strategy, small_theory_strategy
from hypothesis import given, settings
from hypothesis import strategies as st

from gunray.adapter import GunrayEvaluator
from gunray.answer import Answer
from gunray.dialectic import answer
from gunray.disagreement import complement
from gunray.preference import GeneralizedSpecificity, TrivialPreference
from gunray.schema import DefeasibleTheory, ClosurePolicy, MarkingPolicy, Rule
from gunray.types import GroundAtom


def _ga(predicate: str, *args: str) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


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


def _uncontested_flies_theory() -> DefeasibleTheory:
    """A theory where one side of a literal is warranted and the other
    side has no argument at all — exercises the YES and NO branches of
    ``answer`` under ``TrivialPreference``.

    Rules::
        d1: flies(X) :- bird(X).
        fact: bird(robin).

    ``⟨{d1@robin}, flies(robin)⟩`` exists and has no counter-argument
    (there is no rule producing ``~flies``). Its dialectical tree is
    a leaf, marks ``U``, and so ``flies(robin)`` is warranted → YES.
    ``~flies(robin)`` has no argument at all, so its tree cannot be
    constructed and the "warranted complement" path makes
    ``answer(theory, ~flies(robin), TrivialPreference())`` return NO.
    """
    return DefeasibleTheory(
        facts={"bird": {("robin",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="d1", head="flies(X)", body=["bird(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _direct_nixon_theory() -> DefeasibleTheory:
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


def test_answer_values_round_trip() -> None:
    assert Answer("yes") is Answer.YES
    assert Answer("no") is Answer.NO
    assert Answer("undecided") is Answer.UNDECIDED
    assert Answer("unknown") is Answer.UNKNOWN


def test_answer_has_exactly_four_members() -> None:
    assert set(Answer) == {
        Answer.YES,
        Answer.NO,
        Answer.UNDECIDED,
        Answer.UNKNOWN,
    }


@given(value=st.sampled_from(list(Answer)))
@settings(max_examples=500, deadline=None)
def test_answer_round_trip_for_every_member(value: Answer) -> None:
    assert Answer(value.value) is value


# -- B1.5 — answer(theory, literal, criterion) — Garcia 04 Def 5.3 -----------


def test_answer_tweety_flies_is_yes() -> None:
    """Scout 5.1: there is no rule producing ``~flies(tweety)`` so the
    root tree for ``flies(tweety)`` has no children, marks ``U``, and
    ``flies(tweety)`` is warranted → Garcia 04 Def 5.3 returns YES."""
    theory = _tweety_theory()
    result = answer(theory, _ga("flies", "tweety"), TrivialPreference())
    assert result is Answer.YES


def test_answer_opus_flies_is_undecided_under_trivial_preference() -> None:
    """Scout 5.1 / 5.2 spelled out the Block-1 opus answer verbatim:

        "answer(theory, flies(opus)) ... Under TrivialPreference that
         makes flies(opus) == UNDECIDED ... Under GeneralizedSpecificity
         ... flies(opus) == NO and ~flies(opus) == YES."

    The B1.5 prompt's "is_no" assertion is the Block-2 value. Under
    Block-1's TrivialPreference both arguments block each other, both
    trees mark ``D``, neither literal is warranted, and both have an
    argument, so Garcia 04 Def 5.3 returns ``UNDECIDED``. This test
    documents the Block-1 behavior; the Block-2 NO answer will land
    when ``GeneralizedSpecificity`` arrives. See
    ``notes/refactor_progress.md#deviations`` entry for this dispatch.
    """
    theory = _tweety_theory()
    result = answer(theory, _ga("flies", "opus"), TrivialPreference())
    assert result is Answer.UNDECIDED


def test_answer_opus_not_flies_is_undecided_under_trivial_preference() -> None:
    """Companion to ``test_answer_opus_flies_is_undecided_under_trivial_preference``.

    Under Block-1 TrivialPreference ``answer(theory, ~flies(opus))``
    also returns ``UNDECIDED``. The prompt's "is_yes" assertion is the
    Block-2 value; see the deviations entry in
    ``notes/refactor_progress.md``.
    """
    theory = _tweety_theory()
    result = answer(theory, _ga("~flies", "opus"), TrivialPreference())
    assert result is Answer.UNDECIDED


def test_answer_uncontested_flies_is_yes() -> None:
    """Exercise the YES branch of ``answer`` under TrivialPreference.

    ``_uncontested_flies_theory`` has a single defeasible rule
    ``flies(X) :- bird(X)`` and the fact ``bird(robin)``. No rule
    produces ``~flies``, so ``⟨{d1}, flies(robin)⟩`` has no counter-
    argument, its tree is a leaf marked ``U``, and ``flies(robin)``
    is warranted. Garcia 04 Def 5.3 returns ``YES``.
    """
    theory = _uncontested_flies_theory()
    result = answer(theory, _ga("flies", "robin"), TrivialPreference())
    assert result is Answer.YES


def test_answer_uncontested_not_flies_is_no() -> None:
    """Exercise the NO branch of ``answer`` under TrivialPreference.

    Same theory as ``test_answer_uncontested_flies_is_yes``: the
    complement literal ``~flies(robin)`` has no argument at all,
    but its complement ``flies(robin)`` is warranted (as verified
    above), so Garcia 04 Def 5.3 returns ``NO`` for the ``~flies``
    query.
    """
    theory = _uncontested_flies_theory()
    result = answer(theory, _ga("~flies", "robin"), TrivialPreference())
    assert result is Answer.NO


def test_answer_nixon_pacifist_is_undecided() -> None:
    """Scout 5.2 direct Nixon: both ``pacifist(nixon)`` and
    ``~pacifist(nixon)`` have arguments and neither warrants under
    ``TrivialPreference`` (both trees mark ``D``). Garcia 04 Def 5.3:
    UNDECIDED."""
    theory = _direct_nixon_theory()
    result = answer(theory, _ga("pacifist", "nixon"), TrivialPreference())
    assert result is Answer.UNDECIDED


def test_answer_unknown_predicate_is_unknown() -> None:
    """Garcia 04 Def 5.3 UNKNOWN case: if the literal's predicate is
    not in the language of the theory at all (neither in facts nor in
    any rule head/body), ``answer`` returns ``UNKNOWN``. A martian is
    strictly outside the Tweety universe."""
    theory = _tweety_theory()
    result = answer(theory, _ga("martian", "bob"), TrivialPreference())
    assert result is Answer.UNKNOWN


def test_answer_preserves_existing_enum_tests() -> None:
    """Verification that the B1.2 ``Answer`` enum contract is still
    alive alongside the new B1.5 ``answer`` query API. This is not a
    new contract — just a regression guard against accidental enum
    surgery while adding the query function."""
    assert Answer("yes") is Answer.YES
    assert Answer("no") is Answer.NO
    assert Answer("undecided") is Answer.UNDECIDED
    assert Answer("unknown") is Answer.UNKNOWN
    assert len(set(Answer)) == 4


# -- Hypothesis properties for ``answer`` (max_examples=500) ----------------


@given(theory=small_theory_strategy(), literal=ground_atom_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_answer_is_member_of_enum(
    theory: DefeasibleTheory,
    literal: GroundAtom,
) -> None:
    """Exhaustiveness: ``answer`` always returns a member of the
    ``Answer`` enum for any generated theory and literal. Guards
    against a future implementation falling off the end of Def 5.3's
    case analysis."""
    result = answer(theory, literal, TrivialPreference())
    assert result in Answer


@given(theory=small_theory_strategy(), literal=ground_atom_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_answer_is_pure(
    theory: DefeasibleTheory,
    literal: GroundAtom,
) -> None:
    """Determinism: two calls with the same inputs produce the same
    output. Guards against caching, nondeterministic hashing, or
    mutation in the dialectical tree machinery beneath ``answer``."""
    criterion = TrivialPreference()
    first = answer(theory, literal, criterion)
    second = answer(theory, literal, criterion)
    assert first == second


@given(theory=small_theory_strategy(), literal=ground_atom_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_answer_yes_implies_complement_no(
    theory: DefeasibleTheory,
    literal: GroundAtom,
) -> None:
    """Complement consistency: if ``answer(theory, h) == YES`` then
    ``answer(theory, complement(h)) == NO``. The converse is not
    necessarily true because the ``UNDECIDED`` case permits the
    complement to be UNDECIDED when neither literal is warranted but
    both have arguments.

    Phrased as an unconditional implication ``¬YES ∨ NO`` so
    Hypothesis does not filter out the majority of generated inputs
    (most literals on small theories return UNDECIDED or UNKNOWN).
    """
    criterion = TrivialPreference()
    if answer(theory, literal, criterion) is Answer.YES:
        assert answer(theory, complement(literal), criterion) is Answer.NO


# -- B2.3 — answer under GeneralizedSpecificity (Simari 92 Lemma 2.4) --------


def test_opus_flies_is_no_under_specificity() -> None:
    """Simari 92 §5 Opus/Penguin: under ``GeneralizedSpecificity``,
    ``~flies(opus)`` is warranted because ``penguin(opus)`` (the
    attacker's antecedent) strict-closes to ``bird(opus)`` (the
    defender's antecedent) but not vice versa. The attacker is
    therefore a proper defeater of the defender, the attack tree for
    ``flies(opus)`` marks ``D``, and Garcia 04 Def 5.3 returns NO.

    B1.5 flagged this as the "Opus deviation"; Block 2's specificity
    criterion resolves it.
    """
    theory = _tweety_theory()
    criterion = GeneralizedSpecificity(theory)
    result = answer(theory, _ga("flies", "opus"), criterion)
    assert result is Answer.NO


def test_opus_not_flies_is_yes_under_specificity() -> None:
    """Symmetric to ``test_opus_flies_is_no_under_specificity``.
    ``~flies(opus)`` wins over ``flies(opus)`` under Lemma 2.4, so
    Garcia 04 Def 5.3 returns YES for the negative literal."""
    theory = _tweety_theory()
    criterion = GeneralizedSpecificity(theory)
    result = answer(theory, _ga("~flies", "opus"), criterion)
    assert result is Answer.YES


def test_tweety_still_yes_under_specificity() -> None:
    """Regression: ``flies(tweety)`` stays YES under specificity.
    Tweety is not a penguin, so the only attacker ``~flies(tweety)``
    has no argument at all and the root tree is a leaf marked ``U``.
    Specificity cannot harm an unopposed argument."""
    theory = _tweety_theory()
    criterion = GeneralizedSpecificity(theory)
    result = answer(theory, _ga("flies", "tweety"), criterion)
    assert result is Answer.YES


def test_nixon_diamond_still_undecided_under_specificity() -> None:
    """Regression: equi-specific arguments remain UNDECIDED.
    Simari 92 §5 Nixon Diamond — both ``pacifist(nixon)`` and
    ``~pacifist(nixon)`` rest on raw facts with no strict-rule
    coverage between them, so neither argument is strictly more
    specific than the other. Lemma 2.4 returns ``False`` in both
    directions; the arguments remain blocking defeaters and Garcia
    04 Def 5.3 returns UNDECIDED."""
    theory = _direct_nixon_theory()
    criterion = GeneralizedSpecificity(theory)
    result = answer(theory, _ga("pacifist", "nixon"), criterion)
    assert result is Answer.UNDECIDED


def test_sections_projection_under_specificity() -> None:
    """Full pipeline test: evaluating the Tweety theory through
    ``GunrayEvaluator`` with ``MarkingPolicy.BLOCKING`` routes into
    ``DefeasibleEvaluator.evaluate_with_trace`` and must project
    Opus into the correct Def 5.3 sections once
    ``GeneralizedSpecificity`` is wired in:

    - ``flies(tweety)`` in ``defeasibly``
    - ``flies(opus)`` in ``not_defeasibly``
    - ``~flies(opus)`` in ``defeasibly``

    This exercises the evaluator wire, not just the ``answer`` query
    path, and is the green-gate test for the B2.3 evaluator-side
    change.
    """
    theory = _tweety_theory()
    model = GunrayEvaluator().evaluate(theory, marking_policy=MarkingPolicy.BLOCKING)
    assert isinstance(model, type(model))  # narrow for type checkers
    sections = model.sections  # type: ignore[attr-defined]

    defeasibly = sections.get("defeasibly", {})
    not_defeasibly = sections.get("not_defeasibly", {})

    assert ("tweety",) in defeasibly.get("flies", set())
    assert ("opus",) in defeasibly.get("~flies", set())
    assert ("opus",) in not_defeasibly.get("flies", set())
