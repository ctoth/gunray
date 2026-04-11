from __future__ import annotations

from gunray.defeasible import _expand_candidate_atoms
from gunray.types import GroundAtom


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
