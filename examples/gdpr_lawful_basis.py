"""GDPR lawful basis: explicit superiority layered on specificity.

Shows: Garcia & Simari 2004 §4.1 ``superiority`` relation composed
ahead of ``GeneralizedSpecificity`` so user-supplied rule priority
dominates the automatic criterion. Two independent defeasible paths
to ``lawful_basis`` — one via consent, one via contractual
necessity — survive differently when consent is withdrawn.

GDPR Art. 6(1) lists six lawful bases for processing personal data;
this example uses only two of them (6(1)(a) consent and 6(1)(b)
contractual necessity). The model is a cartoon, not legal advice.

Source: García & Simari 2004 §4.1 p. 17 (user superiority). The
preference criterion follows ``src/gunray/defeasible.py:134`` —
``CompositePreference(SuperiorityPreference, GeneralizedSpecificity)``.
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
        strict_rules=[
            # Strict link: a lawful basis entails lawful processing.
            Rule(
                id="s1",
                head="processing_lawful(X)",
                body=["lawful_basis(X)"],
            ),
        ],
        defeasible_rules=[
            # Consent path. ``consent_given`` is defeasibly supported
            # by a signed record so that a withdrawal rule can
            # undermine it; if it were a fact in Π, no defeasible
            # argument could attack it.
            Rule(id="d0", head="consent_given(X)", body=["consent_signed(X)"]),
            # Consent is a lawful basis (GDPR Art. 6(1)(a)).
            Rule(
                id="d1",
                head="lawful_basis(X)",
                body=["consent_given(X)"],
            ),
            # Filing a withdrawal defeasibly negates consent.
            Rule(
                id="d2",
                head="~consent_given(X)",
                body=["withdrawal_filed(X)"],
            ),
            # Contractual necessity is an independent lawful basis
            # (GDPR Art. 6(1)(b)).
            Rule(
                id="d3",
                head="lawful_basis(X)",
                body=["contractual_necessity(X)"],
            ),
        ],
        defeaters=[],
        # Explicit priority: a filed withdrawal beats the consent
        # rule. Without this pair d0 and d2 are equi-specific
        # (disjoint antecedents) and would merely block each other,
        # leaving consent ambiguous. The ``superiority=[...]``
        # parameter is exactly the point of this example.
        superiority=[("d2", "d0")],
        conflicts=[],
    )


lawful_basis_acme = GroundAtom(predicate="lawful_basis", arguments=("acme",))


def scenario_a() -> Answer:
    """Consent-given-then-withdrawn: lawful basis is contested.

    d2 (withdrawal) beats d0 (consent) via the explicit superiority
    pair, so ``~consent_given(acme)`` is warranted. That collapses
    d1's argument for ``lawful_basis(acme)``. With no alternative
    support, the query cannot be settled — ``answer`` returns
    ``UNDECIDED``, which is the faithful modelling of a lawful-basis
    dispute under the DeLP four-valued semantics (Garcia 04 Def 5.3).
    """
    theory = _build_theory(
        {
            "consent_signed": {("acme",)},
            "withdrawal_filed": {("acme",)},
        }
    )
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return answer(theory, lawful_basis_acme, criterion)


def scenario_b() -> Answer:
    """Consent-withdrawn but contractual necessity also holds.

    The consent path collapses exactly as in scenario A, but d3's
    argument for ``lawful_basis(acme)`` rests on
    ``contractual_necessity(acme)`` and has no counter-argument in
    this theory. It marks U and ``lawful_basis(acme)`` is
    warranted YES.
    """
    theory = _build_theory(
        {
            "consent_signed": {("acme",)},
            "withdrawal_filed": {("acme",)},
            "contractual_necessity": {("acme",)},
        }
    )
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return answer(theory, lawful_basis_acme, criterion)


result_a = scenario_a()
result_b = scenario_b()

assert result_a is Answer.UNDECIDED, f"scenario A: expected UNDECIDED, got {result_a!r}"
assert result_b is Answer.YES, f"scenario B: expected YES, got {result_b!r}"


if __name__ == "__main__":
    print("GDPR lawful basis (explicit superiority over specificity)")
    print("  s1:  processing_lawful(X) :- lawful_basis(X)   (strict)")
    print("  d0:  consent_given(X)    <= consent_signed(X)")
    print("  d1:  lawful_basis(X)     <= consent_given(X)")
    print("  d2:  ~consent_given(X)   <= withdrawal_filed(X)")
    print("  d3:  lawful_basis(X)     <= contractual_necessity(X)")
    print("  superiority: (d2, d0) — withdrawal beats consent")
    print()
    print("Scenario A — consent signed then withdrawn.")
    print("  Explicit priority lets d2 defeat d0; the consent-based")
    print("  argument for lawful_basis collapses and no alternative")
    print("  support remains.")
    print(f"  answer(lawful_basis(acme)) = {result_a.name}")
    print()
    print("Scenario B — same + contractual_necessity(acme).")
    print("  The contractual-necessity argument survives")
    print("  independently of the consent dispute.")
    print(f"  answer(lawful_basis(acme)) = {result_b.name}")
