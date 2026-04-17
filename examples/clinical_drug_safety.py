"""Clinical drug safety: three-level specificity on aspirin administration.

Shows: Simari & Loui 1992 Lemma 2.4 (``GeneralizedSpecificity``) ordering
three defeasible rules on aspirin safety through a strict patient-role
hierarchy, with zero ``superiority`` pairs — specificity alone picks the
winner at each level.

Strict role chain:

    cardiac_event_patient(X) -> warfarin_patient(X) -> patient(X)

Defaults say aspirin is safe for patients, unsafe for warfarin patients
(bleeding risk), and safe again for cardiac-event patients (the
post-infarct anti-platelet indication, where the ischemic risk
dominates). Each defeasible rule's body strictly entails the next-weaker
rule's body, so specificity orders d3 > d2 > d1.

Source: Garcia & Simari 2004 §4.1 p.17 (``GeneralizedSpecificity`` as
preference criterion); Simari & Loui 1992 Lemma 2.4. Preference
composition follows ``src/gunray/defeasible.py:134``.
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
        strict_rules=[
            # Clinical role hierarchy — a cardiac-event patient is
            # necessarily a warfarin patient (they were anticoagulated
            # when the event happened) and every such individual is a
            # patient. These are strict: no cardiologist disputes them.
            Rule(id="s1", head="warfarin_patient(X)", body=["cardiac_event_patient(X)"]),
            Rule(id="s2", head="patient(X)", body=["warfarin_patient(X)"]),
        ],
        defeasible_rules=[
            # Default: aspirin is generally safe for patients. We use
            # a string literal for the drug name because Gunray's rule
            # surface treats unquoted lowercase identifiers as
            # variables — see ``src/gunray/parser.py:192`` — so we
            # quote ``"aspirin"`` to make it a constant.
            Rule(id="d1", head='safe("aspirin",X)', body=["patient(X)"]),
            # Override: NSAID + anticoagulant bleeding risk — not safe
            # (more specific: warfarin_patient -> patient via s2).
            Rule(
                id="d2",
                head='~safe("aspirin",X)',
                body=["warfarin_patient(X)"],
            ),
            # Re-override: post-cardiac-event anti-platelet indication
            # dominates bleeding risk (most specific:
            # cardiac_event_patient -> warfarin_patient -> patient).
            Rule(
                id="d3",
                head='safe("aspirin",X)',
                body=["cardiac_event_patient(X)"],
            ),
        ],
        defeaters=[],
        presumptions=[],
        superiority=[],
        conflicts=[],
    )


def _safe_aspirin(name: str) -> GroundAtom:
    return GroundAtom(predicate="safe", arguments=("aspirin", name))


def _criterion(theory: DefeasibleTheory) -> CompositePreference:
    # Same composite the engine builds at ``defeasible.py:134``. With
    # an empty ``superiority`` list, ``SuperiorityPreference`` is inert
    # and every comparison reaches ``GeneralizedSpecificity``.
    return CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )


# Three scenarios. We only assert each patient's *strongest* role —
# weaker roles follow by s1/s2.
facts: PredicateFacts = {
    "patient": {("alice",)},
    "warfarin_patient": {("bob",)},
    "cardiac_event_patient": {("carol",)},
}
theory = _build_theory(facts)
criterion = _criterion(theory)

alice = _safe_aspirin("alice")
bob = _safe_aspirin("bob")
carol = _safe_aspirin("carol")

result_alice = answer(theory, alice, criterion)
result_bob = answer(theory, bob, criterion)
result_carol = answer(theory, carol, criterion)

assert result_alice is Answer.YES, f"alice: expected YES, got {result_alice!r}"
assert result_bob is Answer.NO, f"bob: expected NO, got {result_bob!r}"
assert result_carol is Answer.YES, f"carol: expected YES, got {result_carol!r}"


if __name__ == "__main__":
    print("Clinical drug safety — aspirin by patient class (lives at stake)")
    print("  strict s1: warfarin_patient(X)       :- cardiac_event_patient(X)")
    print("  strict s2: patient(X)                :- warfarin_patient(X)")
    print("  default d1:  safe(aspirin,X)         <= patient(X)")
    print("  deny    d2: ~safe(aspirin,X)         <= warfarin_patient(X)")
    print("  override d3: safe(aspirin,X)         <= cardiac_event_patient(X)")
    print("  superiority: (none) — specificity orders d3 > d2 > d1")
    print()
    print("Scenario A — alice is a patient with no anticoagulation.")
    print("  Only d1 applies; no counter-argument. Aspirin is safe.")
    print(f"  answer(safe(aspirin,alice)) = {result_alice.name}")
    print()
    print("Scenario B — bob is on warfarin. Bleeding risk dominates.")
    print("  d2 is strictly more specific than d1: withhold aspirin.")
    print(f"  answer(safe(aspirin,bob)) = {result_bob.name}")
    print()
    print("Scenario C — carol is post-cardiac-event on warfarin.")
    print("  d3 is strictly more specific than d2 (and d1): the")
    print("  anti-platelet indication outweighs the bleeding risk.")
    print(f"  answer(safe(aspirin,carol)) = {result_carol.name}")
