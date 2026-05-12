from __future__ import annotations

from itertools import permutations

from hypothesis import given, settings
from hypothesis import strategies as st

from gunray.consistency import (
    ConditionalDatabase,
    ConditionalSentence,
    analyze_p_consistency,
    strictly_p_entails,
)

GOLDSZMIDT_PAGE_001 = (
    "papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-001.png"
)
GOLDSZMIDT_PAGE_003 = (
    "papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-003.png"
)
GOLDSZMIDT_PAGE_004 = (
    "papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-004.png"
)


def c(sentence_id: str, antecedent: tuple[str, ...], consequent: str) -> ConditionalSentence:
    return ConditionalSentence(id=sentence_id, antecedent=antecedent, consequent=consequent)


def test_bird_penguin_exception_defaults_are_p_consistent() -> None:
    """Page-image source: ``GOLDSZMIDT_PAGE_003`` bird/penguin example."""

    database = ConditionalDatabase(
        strict_conditionals=(c("s_penguin_bird", ("penguin",), "bird"),),
        defeasible_conditionals=(
            c("d_birds_fly", ("bird",), "flies"),
            c("d_penguins_do_not_fly", ("penguin",), "~flies"),
        ),
    )

    report = analyze_p_consistency(database)

    assert report.is_consistent
    assert report.offending_sentence_ids == frozenset()
    assert {frozenset(layer) for layer in report.tolerated_layers} == {
        frozenset({"d_birds_fly"}),
        frozenset({"d_penguins_do_not_fly"}),
    }


def test_quaker_republican_database_reports_offending_set() -> None:
    """Page-image sources: ``GOLDSZMIDT_PAGE_003`` and ``GOLDSZMIDT_PAGE_004``."""

    database = ConditionalDatabase(
        strict_conditionals=(
            c("s_quakers_pacifist", ("quaker",), "pacifist"),
            c("s_republicans_not_pacifist", ("republican",), "~pacifist"),
        ),
        defeasible_conditionals=(
            c("d_nixonites_republican", ("nixonite",), "republican"),
            c("d_nixonites_quaker", ("nixonite",), "quaker"),
            c("d_pacifists_persecuted", ("pacifist",), "persecuted"),
        ),
    )

    report = analyze_p_consistency(database)

    assert not report.is_consistent
    assert report.tolerated_layers == (("d_pacifists_persecuted",),)
    assert report.offending_sentence_ids == frozenset(
        {"d_nixonites_republican", "d_nixonites_quaker"}
    )


def test_strict_p_entailment_uses_only_strict_conditionals() -> None:
    """Page-image source: ``GOLDSZMIDT_PAGE_003`` strict p-entailment note."""

    database = ConditionalDatabase(
        strict_conditionals=(c("s_not_a", (), "~a"),),
        defeasible_conditionals=(c("d_a_b", ("a",), "b"),),
    )

    assert not strictly_p_entails(database, c("query_vacuous", ("a",), "b"))
    assert strictly_p_entails(database, c("query_strict", (), "~a"))


@st.composite
def small_database(draw: st.DrawFn) -> ConditionalDatabase:
    literals = ("a", "b", "c", "~a", "~b", "~c")
    antecedents = st.tuples(st.sampled_from(literals)).map(tuple) | st.just(())
    consequent = st.sampled_from(literals)
    strict_count = draw(st.integers(min_value=0, max_value=2))
    defeasible_count = draw(st.integers(min_value=0, max_value=3))
    strict = tuple(
        c(f"s{i}", draw(antecedents), draw(consequent)) for i in range(strict_count)
    )
    defeasible = tuple(
        c(f"d{i}", draw(antecedents), draw(consequent)) for i in range(defeasible_count)
    )
    return ConditionalDatabase(strict_conditionals=strict, defeasible_conditionals=defeasible)


@given(database=small_database())
@settings(max_examples=40, deadline=None)
def test_consistency_verdict_is_independent_of_defeasible_order(
    database: ConditionalDatabase,
) -> None:
    reports = [
        analyze_p_consistency(
            ConditionalDatabase(
                strict_conditionals=database.strict_conditionals,
                defeasible_conditionals=tuple(items),
            )
        )
        for items in permutations(database.defeasible_conditionals)
    ]

    assert {report.is_consistent for report in reports} == {reports[0].is_consistent}
    assert {report.offending_sentence_ids for report in reports} == {
        reports[0].offending_sentence_ids
    }


@given(database=small_database())
@settings(max_examples=40, deadline=None)
def test_tolerated_layer_members_do_not_depend_on_input_order(
    database: ConditionalDatabase,
) -> None:
    report = analyze_p_consistency(database)
    reordered = analyze_p_consistency(
        ConditionalDatabase(
            strict_conditionals=database.strict_conditionals,
            defeasible_conditionals=tuple(reversed(database.defeasible_conditionals)),
        )
    )

    assert tuple(frozenset(layer) for layer in report.tolerated_layers) == tuple(
        frozenset(layer) for layer in reordered.tolerated_layers
    )


@given(database=small_database())
@settings(max_examples=40, deadline=None)
def test_offending_ids_are_drawn_from_input(database: ConditionalDatabase) -> None:
    report = analyze_p_consistency(database)
    input_ids = {item.id for item in database.strict_conditionals + database.defeasible_conditionals}

    assert report.offending_sentence_ids <= input_ids


@given(database=small_database())
@settings(max_examples=40, deadline=None)
def test_report_matches_independent_bruteforce_oracle(database: ConditionalDatabase) -> None:
    report = analyze_p_consistency(database)

    assert report.is_consistent == _bruteforce_consistent(database)


def _bruteforce_consistent(database: ConditionalDatabase) -> bool:
    strict = database.strict_conditionals
    if any(not _is_tolerated(sentence, strict) for sentence in strict):
        return False
    remaining = set(database.defeasible_conditionals)
    while remaining:
        tolerated = {sentence for sentence in remaining if _is_tolerated(sentence, strict + tuple(remaining))}
        if not tolerated:
            return False
        remaining -= tolerated
    return True


def _is_tolerated(
    sentence: ConditionalSentence,
    constraints: tuple[ConditionalSentence, ...],
) -> bool:
    atoms = sorted(
        {
            literal.removeprefix("~")
            for item in (sentence, *constraints)
            for literal in (*item.antecedent, item.consequent)
        }
    )
    for mask in range(1 << len(atoms)):
        assignment = {
            atom: bool(mask & (1 << index))
            for index, atom in enumerate(atoms)
        }
        if not _verified(sentence, assignment):
            continue
        if all(_materially_satisfied(item, assignment) for item in constraints):
            return True
    return False


def _verified(sentence: ConditionalSentence, assignment: dict[str, bool]) -> bool:
    return all(_literal_value(item, assignment) for item in sentence.antecedent) and _literal_value(
        sentence.consequent,
        assignment,
    )


def _materially_satisfied(
    sentence: ConditionalSentence,
    assignment: dict[str, bool],
) -> bool:
    return not all(_literal_value(item, assignment) for item in sentence.antecedent) or _literal_value(
        sentence.consequent,
        assignment,
    )


def _literal_value(literal: str, assignment: dict[str, bool]) -> bool:
    if literal.startswith("~"):
        return not assignment[literal[1:]]
    return assignment[literal]
