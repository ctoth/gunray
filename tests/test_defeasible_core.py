from __future__ import annotations

from gunray.defeasible import _expand_candidate_atoms, _is_more_specific
from gunray.types import GroundAtom, GroundDefeasibleRule


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
