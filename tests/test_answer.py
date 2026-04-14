"""Unit and property tests for gunray.answer (Garcia & Simari 2004 Def 5.3).

This file covers two surfaces:

- The ``Answer`` enum itself (B1.2 foundation, Garcia 04 Def 5.3).
- The ``answer(theory, literal, criterion)`` query API (B1.5), which
  implements Def 5.3's four-valued warrant query on top of the
  dialectical tree machinery from B1.4.
"""

from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from gunray.answer import Answer
from gunray.arguments import build_arguments
from gunray.dialectic import answer
from gunray.disagreement import complement
from gunray.preference import TrivialPreference
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom
from conftest import ground_atom_strategy, small_theory_strategy


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
