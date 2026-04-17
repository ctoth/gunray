"""Innocent until proven guilty: presumption overridden by specific evidence.

Shows: Garcia & Simari 2004 §6.2 p. 32 presumption (``innocent -< true``,
empty body) defeated by arg-bearing defeasible rules, with a blocking
defeater modelling "coerced confession" — an attack that denies the
confession rule without claiming innocence directly.

Source: García & Simari 2004 §6.2 p. 32 (presumptions as empty-body
defeasible rules). Preference is the canonical composite
``SuperiorityPreference`` → ``GeneralizedSpecificity`` used by
``DefeasibleEvaluator`` (see ``src/gunray/defeasible.py:134``).

Heads are intentionally zero-arity throughout. F-A documented that
arg-bearing presumption heads crash ``_positive_closure_for_grounding``
at ``_internal.py:139`` during ``build_arguments``; the zero-arity form
exercises the pipeline cleanly.
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
from gunray.types import GroundAtom


def _build_theory(facts: dict[str, set[tuple[object, ...]]]) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=facts,
        strict_rules=[],
        defeasible_rules=[
            # Evidence rule — defeasibly supports guilt.
            Rule(id="d1", head="~innocent", body=["evidence_against"]),
            # Confession rule — separately supports guilt.
            Rule(id="d2", head="~innocent", body=["confession"]),
        ],
        defeaters=[
            # Blocking defeater: a coerced confession lets us doubt
            # the confession-based guilt argument without asserting
            # innocence on its own.
            Rule(id="df1", head="innocent", body=["coerced_confession"]),
        ],
        presumptions=[
            # García & Simari 2004 §6.2 p. 32 — presumption as
            # empty-body defeasible rule, written ``h -< true`` in
            # the DeLP surface syntax.
            Rule(id="p1", head="innocent", body=[]),
        ],
        # Explicit priority: the evidence rule overrides the
        # coercion-based defeater. Without this pair, df1 is
        # equi-specific with d1 (disjoint antecedents) and would
        # *block* d1 too. Garcia & Simari 2004 §4.1 — user
        # superiority composed ahead of specificity.
        superiority=[("d1", "df1")],
        conflicts=[],
    )


innocent_atom = GroundAtom(predicate="innocent", arguments=())


def scenario_a() -> Answer:
    """Scenario A: evidence only, no confession, no coercion.

    The presumption ``innocent`` has empty antecedent; the evidence
    argument ``⟨{d1}, ~innocent⟩`` has antecedent ``{evidence_against}``
    and is strictly more specific under Simari & Loui 1992 Lemma 2.4.
    Specificity prefers the evidence argument, so ``~innocent`` wins.
    """
    theory = _build_theory({"evidence_against": {()}})
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return answer(theory, innocent_atom, criterion)


def scenario_b() -> Answer:
    """Scenario B: evidence, confession, coerced confession all true.

    The confession-based guilt argument ``⟨{d2}, ~innocent⟩`` is
    counter-argued by the defeater ``⟨{df1}, innocent⟩`` built on
    ``coerced_confession``. The two are equi-specific (disjoint
    antecedents), so the defeater *blocks* d2 rather than properly
    defeating it. But the evidence argument ``⟨{d1}, ~innocent⟩`` is
    unaffected by coercion and still strictly outweighs the
    presumption, so ``~innocent`` still wins.
    """
    theory = _build_theory(
        {
            "evidence_against": {()},
            "confession": {()},
            "coerced_confession": {()},
        }
    )
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return answer(theory, innocent_atom, criterion)


result_a = scenario_a()
result_b = scenario_b()

assert result_a is Answer.NO, f"scenario A: expected NO, got {result_a!r}"
assert result_b is Answer.NO, f"scenario B: expected NO, got {result_b!r}"


if __name__ == "__main__":
    print("Innocent until proven guilty (presumption + defeater)")
    print("  presumption p1: innocent -< true")
    print("  d1:             ~innocent :- evidence_against")
    print("  d2:             ~innocent :- confession")
    print("  defeater df1:    innocent <~ coerced_confession")
    print()
    print("Scenario A — evidence_against only.")
    print("  The evidence argument is more specific than the")
    print("  empty-body presumption, so ~innocent is warranted.")
    print(f"  answer(innocent) = {result_a.name}")
    print()
    print("Scenario B — evidence + confession + coerced_confession.")
    print("  df1 blocks the confession-based guilt argument, but")
    print("  the evidence argument still beats the presumption.")
    print(f"  answer(innocent) = {result_b.name}")
