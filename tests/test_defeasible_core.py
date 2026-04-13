from __future__ import annotations

from pathlib import Path

from gunray import DefeasibleTheory, Policy, Rule
from gunray.ambiguity import resolve_ambiguity_policy
from gunray.defeasible import (
    DefeasibleEvaluator,
    _expand_candidate_atoms,
    _has_blocking_peer,
    _is_more_specific,
    _supporter_survives,
)
from gunray.types import GroundAtom, GroundDefeasibleRule


def test_readme_discloses_reduced_specificity_and_defeat_contract() -> None:
    readme = Path(__file__).resolve().parents[1] / "README.md"
    text = " ".join(readme.read_text(encoding="utf-8").split())

    assert "strict-body specificity heuristic" in text
    assert "not full DeLP/ASPIC-style dialectical argument comparison" in text


def test_expand_candidate_atoms_adds_conflicting_complements() -> None:
    atoms = {GroundAtom(predicate="q", arguments=())}
    conflicts = {
        ("q", "~q"),
        ("~q", "q"),
    }

    expanded = _expand_candidate_atoms(atoms, conflicts)

    assert expanded == {
        GroundAtom(predicate="q", arguments=()),
        GroundAtom(predicate="~q", arguments=()),
    }


def test_is_more_specific_uses_strict_body_closure() -> None:
    supporter = GroundDefeasibleRule(
        rule_id="r2",
        kind="defeasible",
        head=GroundAtom(predicate="~teach_course", arguments=("bob",)),
        body=(GroundAtom(predicate="phd_member", arguments=("bob",)),),
    )
    attacker = GroundDefeasibleRule(
        rule_id="r1",
        kind="defeasible",
        head=GroundAtom(predicate="teach_course", arguments=("bob",)),
        body=(GroundAtom(predicate="dept_member", arguments=("bob",)),),
    )
    strict_rule = GroundDefeasibleRule(
        rule_id="s1",
        kind="strict",
        head=GroundAtom(predicate="dept_member", arguments=("bob",)),
        body=(GroundAtom(predicate="phd_member", arguments=("bob",)),),
    )

    assert _is_more_specific(
        supporter,
        attacker,
        (strict_rule,),
        {},
    )


def test_equally_specific_defeasible_attacker_blocks_supporter() -> None:
    supporter = GroundDefeasibleRule(
        rule_id="r2",
        kind="defeasible",
        head=GroundAtom(predicate="pacifist", arguments=("nixon",)),
        body=(GroundAtom(predicate="quaker", arguments=("nixon",)),),
    )
    attacker = GroundDefeasibleRule(
        rule_id="r3",
        kind="defeasible",
        head=GroundAtom(predicate="~pacifist", arguments=("nixon",)),
        body=(GroundAtom(predicate="republican", arguments=("nixon",)),),
    )

    survives = _supporter_survives(
        supporter,
        supporter.head,
        {
            GroundAtom(predicate="quaker", arguments=("nixon",)),
            GroundAtom(predicate="republican", arguments=("nixon",)),
        },
        set(),
        {attacker.head: [attacker]},
        {attacker.head},
        set(),
        (),
        {},
    )

    assert not survives


def test_equal_strength_opponents_are_classified_as_blocking_peers() -> None:
    pacifist = GroundDefeasibleRule(
        rule_id="r2",
        kind="defeasible",
        head=GroundAtom(predicate="pacifist", arguments=("nixon",)),
        body=(GroundAtom(predicate="quaker", arguments=("nixon",)),),
    )
    anti_pacifist = GroundDefeasibleRule(
        rule_id="r3",
        kind="defeasible",
        head=GroundAtom(predicate="~pacifist", arguments=("nixon",)),
        body=(GroundAtom(predicate="republican", arguments=("nixon",)),),
    )

    assert _has_blocking_peer(
        pacifist.head,
        [pacifist],
        resolve_ambiguity_policy(Policy.PROPAGATING),
        {
            GroundAtom(predicate="quaker", arguments=("nixon",)),
            GroundAtom(predicate="republican", arguments=("nixon",)),
        },
        {
            GroundAtom(predicate="quaker", arguments=("nixon",)),
            GroundAtom(predicate="republican", arguments=("nixon",)),
        },
        set(),
        {
            pacifist.head: [pacifist],
            anti_pacifist.head: [anti_pacifist],
        },
        {
            ("pacifist", "~pacifist"),
            ("~pacifist", "pacifist"),
        },
        set(),
        (),
        {},
    )


def test_blocking_fixed_point_leaves_nixon_conflict_undecided() -> None:
    theory = DefeasibleTheory(
        facts={
            "nixonian": [("nixon",)],
            "quaker": [("nixon",)],
        },
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="republican(X)", body=["nixonian(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
            Rule(id="r3", head="~pacifist(X)", body=["republican(X)"]),
        ],
    )

    model = DefeasibleEvaluator().evaluate(theory, Policy.BLOCKING)

    assert ("nixon",) not in model.sections.get("defeasibly", {}).get("pacifist", set())
    assert ("nixon",) in model.sections.get("undecided", {}).get("pacifist", set())
    assert ("nixon",) in model.sections.get("undecided", {}).get("~pacifist", set())
