"""Peer-review reviewer assignment under multi-axis conflict of interest.

Shows: a defeasible eligibility decision where disqualifiers live on
three *independent fact axes* — co-authorship, same-institution, and
doctoral-advisor lineage — and a waiver applies only on one axis. A
single scalar priority cannot capture this: removing a co-authorship
flag can flip the answer while same-institution and advisor status
are unchanged, because the axes are not comparable on one line.

Strict ontology (not a chain, a branch-merge):

    same_institution(X,Y) -> co_worker(X,Y)
    advisor_of(X,Y)       -> co_worker(X,Y)

The two strict rules collapse *different* evidentiary axes into the
same derived predicate, so ``co_worker`` can be reached by two
incomparable routes.

Defeasible layer (one default + three disqualifiers):

    d1: eligible(X,Y)  <= bid(X,Y)                     (reviewer bid)
    d2: ~eligible(X,Y) <= recent_coauthor(X,Y)
    d3: ~eligible(X,Y) <= co_worker(X,Y)
    d4: ~eligible(X,Y) <= advisor_of(X,Y)

Undercutting defeater, scoped to the *institution* axis only:

    df1: eligible(X,Y) <| co_worker(X,Y),
                          large_institution(X,Y),
                          different_department(X,Y)

``df1`` is strictly more specific than ``d3`` (its body is a proper
superset), so ``GeneralizedSpecificity`` lets it defeat the
institutional-COI rule. ``df1`` is registered as a *defeater* (Garcia
& Simari 2004 §3.3) rather than a full defeasible rule: it exists to
attack, not to be used as a premise in later chains — a reviewer we
grant on a big-institution waiver is not transitive grounds for other
conclusions.

Superiority pairs (bridging axes that specificity leaves unordered):

    (d2, d1), (d3, d1), (d4, d1) — each disqualifier beats the default,
                                  whose body shares no literals with
                                  any of them.
    (d4, df1) — the advisor-COI rule outranks the large-institution
                waiver. Being at a big university with a separate
                department does not wash away a supervisor relation.

Sources:
- García & Simari 2004 §3.3 p. 14 (defeaters vs. defeasible rules);
  §4.1 p. 17 (CompositePreference of SuperiorityPreference and
  GeneralizedSpecificity).
- Simari & Loui 1992 Lemma 2.4 (``GeneralizedSpecificity``).
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
            # Two routes into the derived co_worker predicate. Neither
            # strictly implies the other in the wild, but both count
            # as co-working for COI purposes.
            Rule(id="s1", head="co_worker(X,Y)", body=["same_institution(X,Y)"]),
            Rule(id="s2", head="co_worker(X,Y)", body=["advisor_of(X,Y)"]),
        ],
        defeasible_rules=[
            # Default: a submitted reviewer bid makes you eligible.
            Rule(id="d1", head="eligible(X,Y)", body=["bid(X,Y)"]),
            # Co-authorship COI.
            Rule(id="d2", head="~eligible(X,Y)", body=["recent_coauthor(X,Y)"]),
            # Institutional COI (derived via s1 or s2).
            Rule(id="d3", head="~eligible(X,Y)", body=["co_worker(X,Y)"]),
            # Advisor-of COI.
            Rule(id="d4", head="~eligible(X,Y)", body=["advisor_of(X,Y)"]),
        ],
        defeaters=[
            # Undercutting waiver: large institution with a distinct
            # department lets the reviewer survive the institutional
            # COI rule. Body strictly supersets d3's body, so
            # GeneralizedSpecificity ranks df1 > d3.
            Rule(
                id="df1",
                head="eligible(X,Y)",
                body=[
                    "co_worker(X,Y)",
                    "large_institution(X,Y)",
                    "different_department(X,Y)",
                ],
            ),
        ],
        presumptions=[],
        superiority=[
            # Disqualifiers outrank the default — specificity is silent
            # here (disjoint antecedents) so superiority does the work.
            ("d2", "d1"),
            ("d3", "d1"),
            ("d4", "d1"),
            # Advisor-COI is not waivable by the institution-size
            # loophole. Keeps PhD supervision disqualifying even when
            # the reviewer is in a different department of a large
            # university.
            ("d4", "df1"),
        ],
        conflicts=[],
    )


def _eligible(reviewer: str, author: str) -> GroundAtom:
    return GroundAtom(predicate="eligible", arguments=(reviewer, author))


# Four reviewer/author pairs, each probing a different axis of COI.
# Alice bid for paper-a and has no ties; Bob co-authored with author-b
# recently; Carol shares a large institution with author-c but in a
# different department; Dave was the doctoral advisor of author-d and
# is also at a large institution, separate department — the waiver
# that rescues Carol must NOT rescue Dave.
facts: PredicateFacts = {
    "bid": {
        ("alice", "author_a"),
        ("bob", "author_b"),
        ("carol", "author_c"),
        ("dave", "author_d"),
    },
    "recent_coauthor": {("bob", "author_b")},
    "same_institution": {("carol", "author_c")},
    "advisor_of": {("dave", "author_d")},
    "large_institution": {
        ("carol", "author_c"),
        ("dave", "author_d"),
    },
    "different_department": {
        ("carol", "author_c"),
        ("dave", "author_d"),
    },
}

theory = _build_theory(facts)
criterion = CompositePreference(
    SuperiorityPreference(theory),
    GeneralizedSpecificity(theory),
)

alice_q = _eligible("alice", "author_a")
bob_q = _eligible("bob", "author_b")
carol_q = _eligible("carol", "author_c")
dave_q = _eligible("dave", "author_d")

result_alice = answer(theory, alice_q, criterion)
result_bob = answer(theory, bob_q, criterion)
result_carol = answer(theory, carol_q, criterion)
result_dave = answer(theory, dave_q, criterion)

assert result_alice is Answer.YES, f"alice: expected YES, got {result_alice!r}"
assert result_bob is Answer.NO, f"bob: expected NO, got {result_bob!r}"
assert result_carol is Answer.YES, f"carol: expected YES, got {result_carol!r}"
assert result_dave is Answer.NO, f"dave: expected NO, got {result_dave!r}"


def _tree_for(atom: GroundAtom) -> DialecticalNode:
    """Build the marked dialectical tree rooted at ``atom``.

    Garcia & Simari 2004 Def 5.1: the tree is rooted at a chosen
    argument for the query literal. Each scenario here has a unique
    defeasible argument for ``eligible(reviewer, author)`` (the bid
    rule), so the choice is unambiguous.
    """
    arguments = tuple(build_arguments(theory))
    root = next(arg for arg in arguments if arg.conclusion == atom and arg.rules)
    return build_tree(root, criterion, theory, universe=arguments)


if __name__ == "__main__":
    print("Reviewer assignment under multi-axis conflict of interest")
    print("  strict s1:  co_worker(X,Y)  :- same_institution(X,Y)")
    print("  strict s2:  co_worker(X,Y)  :- advisor_of(X,Y)")
    print("  default d1: eligible(X,Y)   <= bid(X,Y)")
    print("  coi     d2: ~eligible(X,Y)  <= recent_coauthor(X,Y)")
    print("  coi     d3: ~eligible(X,Y)  <= co_worker(X,Y)")
    print("  coi     d4: ~eligible(X,Y)  <= advisor_of(X,Y)")
    print("  waiver df1: eligible(X,Y)   <| co_worker ^ large_institution ^ different_department")
    print("  superiority: (d2,d1) (d3,d1) (d4,d1) (d4,df1)")
    print()
    print("Alice — bid on author_a's paper, no COI on any axis.")
    print(f"  answer(eligible(alice, author_a)) = {result_alice.name}")
    print()
    print("Bob — bid on author_b's paper, recent co-author.")
    print("  d2 defeats d1 via superiority (d2, d1).")
    print(f"  answer(eligible(bob, author_b)) = {result_bob.name}")
    print()
    print("Carol — bid on author_c's paper, same (large, separate-dept) institution.")
    print("  d3 fires via s1, but df1 is strictly more specific and defeats it.")
    print("  d1 ends undefeated: waiver restores eligibility on the institution axis.")
    print(f"  answer(eligible(carol, author_c)) = {result_carol.name}")
    print()
    print("Dave — bid on author_d's paper, was the PhD advisor, large-dept waiver facts hold.")
    print("  d4 fires via advisor_of. df1 also fires (co_worker via s2 + waiver facts).")
    print("  Superiority (d4, df1) keeps the advisor rule ahead of the waiver, so")
    print("  d4 defeats d1 and df1 cannot rescue. No scalar priority captures this:")
    print("  the same waiver that saved Carol is overruled by the advisor axis.")
    print(f"  answer(eligible(dave, author_d)) = {result_dave.name}")
    print()
    print("Dialectical tree for eligible(dave, author_d):")
    print(render_tree(_tree_for(dave_q)))
    print()
    print("Prose explanation (Garcia & Simari 2004 §6):")
    print(explain(_tree_for(dave_q), criterion))
