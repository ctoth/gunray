"""Pollock's red-light defeater: blocking without counter-claiming.

Shows: the canonical Pollock 1995 ``Cognitive Carpentry`` *undercutting*
defeater — illumination by red light blocks the inference from
``looks_red(X)`` to ``red(X)`` without asserting that X is not red.

Garcia & Simari 2004 Definition 3.1 cites the notion of defeaters
distinct from strict/defeasible rules; Pollock 1995 is the original
source for the epistemological distinction between *rebutting* and
*undercutting* defeat that motivates gunray's ``defeaters`` slot.

- Defeasible: red(X) :- looks_red(X).
- Defeater:  ~red(X) :- illuminated_by_red_light(X).

The defeater has head ``~red(X)`` but lives in the ``defeaters``
slot, so it cannot *support* a warranted argument for ``~red(X)`` —
it can only block arguments for ``red(X)``. That is exactly Pollock's
undercutter: evidence that the ordinary inference is unreliable here,
without independent evidence that the conclusion is false.

Scenarios:
  A. Only ``looks_red(apple)``: ``red(apple)`` is warranted (YES).
  B. ``looks_red(apple)`` + ``illuminated_by_red_light(apple)``:
     neither ``red(apple)`` nor ``~red(apple)`` is warranted
     (UNDECIDED) — the defeater blocks the positive argument and the
     defeater itself cannot conclude ``~red(apple)``.

Source: Pollock 1995, *Cognitive Carpentry*, MIT Press, on
undercutting defeat; Garcia & Simari 2004 Def 3.1 p.9 for the
defeater-vs-defeasible-rule distinction. Marking follows Procedure
5.1 in Garcia & Simari 2004 §5 p.19.
"""

from __future__ import annotations

from gunray import (
    Answer,
    CompositePreference,
    DefeasibleTheory,
    GeneralizedSpecificity,
    Rule,
    SuperiorityPreference,
    answer,
)
from gunray.schema import PredicateFacts
from gunray.types import GroundAtom


def _build_theory(facts: PredicateFacts) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=facts,
        strict_rules=[],
        defeasible_rules=[
            Rule(id="d1", head="red(X)", body=["looks_red(X)"]),
        ],
        defeaters=[
            # Undercutter: having head ``~red(X)`` and living in the
            # ``defeaters`` slot means this blocks d1's argument
            # without being able to *support* a warrant for ~red(X).
            Rule(id="u1", head="~red(X)", body=["illuminated_by_red_light(X)"]),
        ],
        presumptions=[],
        superiority=[],
        conflicts=[],
    )


def _red(name: str) -> GroundAtom:
    return GroundAtom(predicate="red", arguments=(name,))


def _not_red(name: str) -> GroundAtom:
    return GroundAtom(predicate="~red", arguments=(name,))


def _criterion(theory: DefeasibleTheory) -> CompositePreference:
    return CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )


# Scenario A: apple looks red, no funny lighting.
facts_a: PredicateFacts = {"looks_red": {("apple",)}}
theory_a = _build_theory(facts_a)
criterion_a = _criterion(theory_a)
result_a_red = answer(theory_a, _red("apple"), criterion_a)

# Scenario B: apple looks red under red illumination. Undercut.
facts_b: PredicateFacts = {
    "looks_red": {("apple",)},
    "illuminated_by_red_light": {("apple",)},
}
theory_b = _build_theory(facts_b)
criterion_b = _criterion(theory_b)
result_b_red = answer(theory_b, _red("apple"), criterion_b)
result_b_not_red = answer(theory_b, _not_red("apple"), criterion_b)

assert result_a_red is Answer.YES, f"A: expected YES for red(apple), got {result_a_red!r}"
assert result_b_red is not Answer.YES, (
    f"B: red(apple) must NOT be warranted under red light, got {result_b_red!r}"
)
assert result_b_not_red is not Answer.YES, (
    f"B: the undercutter must not warrant ~red(apple) either, got {result_b_not_red!r}"
)


if __name__ == "__main__":
    print("Pollock's red-light undercutter (1995, Cognitive Carpentry)")
    print("  defeasible d1: red(X)  <= looks_red(X)")
    print("  defeater    u1: ~red(X) <~ illuminated_by_red_light(X)")
    print()
    print("Scenario A — looks_red(apple) only.")
    print("  d1 has no counter-argument; the inference stands.")
    print(f"  answer(red(apple)) = {result_a_red.name}")
    print()
    print("Scenario B — looks_red(apple) AND illuminated_by_red_light(apple).")
    print("  u1 blocks d1 without claiming the apple is not red.")
    print(f"  answer(red(apple))  = {result_b_red.name}")
    print(f"  answer(~red(apple)) = {result_b_not_red.name}")
    print()
    print("Neither conclusion is warranted: the undercutter's job is to")
    print("remove d1's support, not to prove the opposite.")
