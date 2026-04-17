"""Platypus: species-specific defeasible rule defeats the mammal default.

Shows: Garcia & Simari 2004 Definition 5.3 returning ``YES`` when
``GeneralizedSpecificity`` prefers the argument rooted at the more
specific premise (platypus, which strictly entails mammal but not vice
versa).
Source: synthetic variant of Simari & Loui 1992 Section 5 p.29
Opus/Penguin (see ``tests/test_specificity.py``).
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
    facts={"platypus": {("plato",)}},
    strict_rules=[Rule(id="s1", head="mammal(X)", body=["platypus(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="~lays_eggs(X)", body=["mammal(X)"]),
        Rule(id="r2", head="lays_eggs(X)", body=["platypus(X)"]),
    ],
    defeaters=[],
    superiority=[],
    conflicts=[],
)

lays_eggs_plato = GroundAtom(predicate="lays_eggs", arguments=("plato",))
criterion = GeneralizedSpecificity(theory)
result = answer(theory, lays_eggs_plato, criterion)

assert result is Answer.YES, f"expected YES, got {result!r}"


if __name__ == "__main__":
    print("Platypus")
    print("  fact: platypus(plato)")
    print("  s1:   mammal(X)       :- platypus(X)  (strict)")
    print("  r1:   ~lays_eggs(X)  <= mammal(X)")
    print("  r2:    lays_eggs(X)  <= platypus(X)")
    print()
    print("r2 is rooted at the more specific premise: platypus strictly")
    print("entails mammal, but not the reverse. GeneralizedSpecificity")
    print("lets r2 properly defeat r1, so the dialectical tree for")
    print("lays_eggs(plato) marks U and the answer is warranted YES.")
    print()
    print(f"answer(lays_eggs(plato)) = {result.name}")
