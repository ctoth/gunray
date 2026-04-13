"""Unit and property tests for gunray.answer (Garcia & Simari 2004 Def 5.3)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gunray.answer import Answer


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
