"""RBAC break-glass: cascading overrides via generalized specificity alone.

Shows: Simari & Loui 1992 Lemma 2.4 (``GeneralizedSpecificity``) picking
the winner across three levels of rule specificity with *zero*
``superiority`` pairs — the strict role hierarchy

    incident_commander(X) → terminated(X) → team_member(X)

makes the body of each defeasible access rule strictly entail the body
of the less specific one, so every pairwise comparison is settled by
specificity alone.

Defaults allow team members, deny terminated users (more specific), and
re-allow incident commanders (most specific — the break-glass).

Source: García & Simari 2004 §4.1 p. 17 (``GeneralizedSpecificity`` as
a preference criterion over defeasible arguments), built on Simari &
Loui 1992 Lemma 2.4. Preference composition follows
``src/gunray/defeasible.py:134``.
"""

from __future__ import annotations

from gunray import (
    Answer,
    CompositePreference,
    DefeasibleTheory,
    DialecticalNode,
    GeneralizedSpecificity,
    Rule,
    SuperiorityPreference,
    answer,
    build_arguments,
    build_tree,
    explain,
    render_tree,
)
from gunray.schema import PredicateFacts
from gunray.types import GroundAtom


def _build_theory(facts: PredicateFacts) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=facts,
        strict_rules=[
            # Role hierarchy as strict rules. Having either stronger
            # role strictly implies the weaker ones, so any argument
            # using a stronger-role premise semantically activates
            # everything a weaker-role argument would.
            Rule(id="s1", head="terminated(X)", body=["incident_commander(X)"]),
            Rule(id="s2", head="team_member(X)", body=["terminated(X)"]),
        ],
        defeasible_rules=[
            # Default: team members have access.
            Rule(id="d1", head="access(X)", body=["team_member(X)"]),
            # Override: terminated users are denied (more specific —
            # terminated(X) strictly implies team_member(X) via s2).
            Rule(id="d2", head="~access(X)", body=["terminated(X)"]),
            # Break-glass: a declared incident commander regains
            # access (most specific — incident_commander(X) strictly
            # implies terminated(X) via s1 and team_member(X) via s1+s2).
            Rule(id="d3", head="access(X)", body=["incident_commander(X)"]),
        ],
        defeaters=[],
        presumptions=[],
        # No superiority pairs — the whole point is that specificity
        # alone orders the three rules.
        superiority=[],
        conflicts=[],
    )


def _access(name: str) -> GroundAtom:
    return GroundAtom(predicate="access", arguments=(name,))


def _criterion(theory: DefeasibleTheory) -> CompositePreference:
    # Same composite the engine uses at ``defeasible.py:134``: an empty
    # ``superiority`` list makes ``SuperiorityPreference`` inert, so
    # every comparison reaches ``GeneralizedSpecificity``.
    return CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )


# Three individuals. The strict role hierarchy means we only assert
# each person's *strongest* role; the weaker roles follow via s1/s2.
facts: PredicateFacts = {
    "team_member": {("alice",)},
    "terminated": {("bob",)},
    "incident_commander": {("carol",)},
}
theory = _build_theory(facts)
criterion = _criterion(theory)

alice_access = _access("alice")
bob_access = _access("bob")
carol_access = _access("carol")

result_alice = answer(theory, alice_access, criterion)
result_bob = answer(theory, bob_access, criterion)
result_carol = answer(theory, carol_access, criterion)

assert result_alice is Answer.YES, f"alice: expected YES, got {result_alice!r}"
assert result_bob is Answer.NO, f"bob: expected NO, got {result_bob!r}"
assert result_carol is Answer.YES, f"carol: expected YES, got {result_carol!r}"


def _tree_for(atom: GroundAtom) -> DialecticalNode:
    """Find the argument concluding ``atom`` and build its marked tree.

    Garcia & Simari 2004 Def 5.1: the dialectical tree is rooted at a
    specific argument, so we pick the argument whose conclusion is the
    query literal. The break-glass case has exactly one such argument
    (``⟨{d3}, access(carol)⟩``), making this unambiguous.
    """
    arguments = build_arguments(theory)
    root = next(arg for arg in arguments if arg.conclusion == atom and arg.rules)
    return build_tree(root, criterion, theory, universe=tuple(arguments))


if __name__ == "__main__":
    print("Access control — break-glass via generalized specificity")
    print("  strict s1:  terminated(X)   :- incident_commander(X)")
    print("  strict s2:  team_member(X)  :- terminated(X)")
    print("  default d1: access(X)       <= team_member(X)")
    print("  deny    d2: ~access(X)      <= terminated(X)")
    print("  break   d3: access(X)       <= incident_commander(X)")
    print("  superiority: (none) — specificity orders d3 > d2 > d1")
    print()
    print("Scenario A — alice is a team member only.")
    print("  Only d1 applies; no counter-argument exists.")
    print(f"  answer(access(alice)) = {result_alice.name}")
    print()
    print("Scenario B — bob is terminated (strictly a team member too).")
    print("  d2 is more specific than d1 and properly defeats it.")
    print(f"  answer(access(bob)) = {result_bob.name}")
    print()
    print("Scenario C — carol is an incident commander (break-glass).")
    print("  d3 is strictly more specific than d2, which is strictly")
    print("  more specific than d1, so d3's access argument is warranted.")
    print(f"  answer(access(carol)) = {result_carol.name}")
    print()
    print("Dialectical tree for access(carol):")
    print(render_tree(_tree_for(carol_access)))
    print()
    print("Prose explanation (Garcia & Simari 2004 §6):")
    print(explain(_tree_for(carol_access), criterion))
