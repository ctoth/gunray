"""Nixon Diamond: equi-specific defeasible rules leave pacifism UNDECIDED.

Shows: Garcia & Simari 2004 Definition 5.3 returning ``UNDECIDED`` when
two arguments block each other and neither is preferred under
``GeneralizedSpecificity``.
Source: Simari & Loui 1992 Section 5 p.30 (lifted from
``tests/test_specificity.py`` lines 42-60).
"""

from __future__ import annotations

from gunray import (
    Answer,
    DefeasibleTheory,
    GeneralizedSpecificity,
    Rule,
    answer,
)
from gunray.types import GroundAtom

theory = DefeasibleTheory(
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

pacifist_nixon = GroundAtom(predicate="pacifist", arguments=("nixon",))
criterion = GeneralizedSpecificity(theory)
result = answer(theory, pacifist_nixon, criterion)

assert result is Answer.UNDECIDED, f"expected UNDECIDED, got {result!r}"


if __name__ == "__main__":
    print("Nixon Diamond")
    print("  fact: republican(nixon), quaker(nixon)")
    print("  r1: ~pacifist(X) <= republican(X)")
    print("  r2:  pacifist(X) <= quaker(X)")
    print()
    print("Both defeasible arguments draw on disjoint facts of equal")
    print("specificity; GeneralizedSpecificity prefers neither, so the")
    print("arguments block one another in the dialectical tree.")
    print()
    print(f"answer(pacifist(nixon)) = {result.name}")
