"""Financial-transaction authorization: break-glass as one axis among several.

Shows: authorization on *non-linearly-ordered* overrides. Four
defeasible rules and no strict rules; superiority pairs encode the
policy relationships we know, and deliberately leave one pair
*unordered* so that when both bodies fire together the engine returns
``UNDECIDED`` rather than inventing a precedence that policy has not
specified.

    d1: can_authorize(X,T)  <= officer(X), within_limit(X,T)    (default)
    d2: ~can_authorize(X,T) <= is_beneficiary(X,T)              (self-dealing bar)
    d3: ~can_authorize(X,T) <= under_audit(T), officer(X)       (audit hold)
    d4: can_authorize(X,T)  <= emergency(T), officer(X)         (break-glass)
    d5: ~can_authorize(X,T) <= high_value(T), sole_approver(X,T) (four-eyes rule)

Superiority (Garcia & Simari 2004 §4.1 p. 17 — user priority composed
ahead of ``GeneralizedSpecificity``):

    (d2, d1), (d3, d1), (d5, d1) — each disqualifier beats the
                                  default on disjoint antecedents.
    (d4, d3) — break-glass overrides an ordinary audit hold.
    (d2, d4) — but the self-dealing bar survives break-glass.

Observe: ``d4`` is *not* ranked against ``d5``. The marking policy does not grant
emergency the power to waive the four-eyes requirement, nor does it
grant four-eyes enough weight to trump a declared emergency. When
both fire together, specificity is silent (disjoint bodies) and
superiority is silent, so ``d4`` and ``d5`` mutually block each
other. The engine reports ``Answer.UNDECIDED`` — a principled refusal
rather than a silent default. No scalar priority encoding of the
five rules can produce this four-valued answer; any total order
either lets emergency waive four-eyes or lets four-eyes override
emergency, and the policy is deliberately agnostic between the two.

Sources:
- García & Simari 2004 §3.3 p. 14 (defeat); §4.1 p. 17 (composite
  preference); Def 5.3 p. 28 (four-valued answer).
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
        strict_rules=[],
        defeasible_rules=[
            Rule(id="d1", head="can_authorize(X,T)", body=["officer(X)", "within_limit(X,T)"]),
            Rule(id="d2", head="~can_authorize(X,T)", body=["is_beneficiary(X,T)"]),
            Rule(id="d3", head="~can_authorize(X,T)", body=["under_audit(T)", "officer(X)"]),
            Rule(id="d4", head="can_authorize(X,T)", body=["emergency(T)", "officer(X)"]),
            Rule(
                id="d5",
                head="~can_authorize(X,T)",
                body=["high_value(T)", "sole_approver(X,T)"],
            ),
        ],
        defeaters=[],
        presumptions=[],
        superiority=[
            # Disqualifiers outrank the default where specificity is
            # silent (disjoint antecedents).
            ("d2", "d1"),
            ("d3", "d1"),
            ("d5", "d1"),
            # Break-glass waives an ordinary audit hold.
            ("d4", "d3"),
            # ...but the self-dealing bar survives break-glass.
            ("d2", "d4"),
            # Deliberately no pair between d4 and d5: policy does not
            # grant emergency the authority to waive four-eyes, nor
            # four-eyes the authority to trump emergency. The pairing
            # is left to mutual block so the engine yields UNDECIDED.
        ],
        conflicts=[],
    )


def _query(user: str, txn: str) -> GroundAtom:
    return GroundAtom(predicate="can_authorize", arguments=(user, txn))


# Five scenarios probing each policy interaction independently.
facts: PredicateFacts = {
    "officer": {("alice",), ("carol",), ("dave",), ("eve",), ("frank",)},
    # Note: frank's high-value txn t_f is deliberately NOT within_limit —
    # high-value transactions by definition exceed an individual
    # officer's normal spending authority and require the four-eyes
    # rule. That keeps d1 from firing for frank, so the frank scenario
    # is a clean two-way fight between break-glass (d4) and four-eyes
    # (d5).
    "within_limit": {
        ("alice", "t_a"),
        ("carol", "t_c"),
        ("dave", "t_d"),
        ("eve", "t_e"),
    },
    "under_audit": {("t_c",), ("t_d",)},
    "emergency": {("t_d",), ("t_e",), ("t_f",)},
    "is_beneficiary": {("eve", "t_e")},
    "high_value": {("t_f",)},
    "sole_approver": {("frank", "t_f")},
}

theory = _build_theory(facts)
criterion = CompositePreference(
    SuperiorityPreference(theory),
    GeneralizedSpecificity(theory),
)

alice_q = _query("alice", "t_a")
carol_q = _query("carol", "t_c")
dave_q = _query("dave", "t_d")
eve_q = _query("eve", "t_e")
frank_q = _query("frank", "t_f")

result_alice = answer(theory, alice_q, criterion)
result_carol = answer(theory, carol_q, criterion)
result_dave = answer(theory, dave_q, criterion)
result_eve = answer(theory, eve_q, criterion)
result_frank = answer(theory, frank_q, criterion)

assert result_alice is Answer.YES, f"alice: expected YES, got {result_alice!r}"
assert result_carol is Answer.NO, f"carol: expected NO, got {result_carol!r}"
assert result_dave is Answer.YES, f"dave: expected YES, got {result_dave!r}"
assert result_eve is Answer.NO, f"eve: expected NO, got {result_eve!r}"
assert result_frank is Answer.UNDECIDED, f"frank: expected UNDECIDED, got {result_frank!r}"


def _tree_for(atom: GroundAtom) -> DialecticalNode:
    """Build the marked dialectical tree rooted at ``atom``.

    Picks the defeasible argument concluding ``atom``. For ``eve``
    and ``frank`` scenarios, the relevant root is the one derived
    from ``d4`` (break-glass), since that is the argument under
    defeat by ``d2``/``d5`` respectively.
    """
    arguments = tuple(build_arguments(theory))
    roots = [arg for arg in arguments if arg.conclusion == atom and arg.rules]
    if not roots:
        raise AssertionError(f"no defeasible argument for {atom!r}")
    # Prefer the argument using the most premises (break-glass wins
    # over the plain default when both apply) for a richer tree.
    return build_tree(
        max(roots, key=lambda a: len(a.rules)),
        criterion,
        theory,
        universe=arguments,
    )


if __name__ == "__main__":
    print("Financial transaction authorization — break-glass as one axis among several")
    print("  d1: can_authorize(X,T)  <= officer(X), within_limit(X,T)")
    print("  d2: ~can_authorize(X,T) <= is_beneficiary(X,T)             (self-dealing bar)")
    print("  d3: ~can_authorize(X,T) <= under_audit(T), officer(X)      (audit hold)")
    print("  d4: can_authorize(X,T)  <= emergency(T), officer(X)        (break-glass)")
    print("  d5: ~can_authorize(X,T) <= high_value(T), sole_approver(X,T) (four-eyes)")
    print("  superiority: (d2,d1) (d3,d1) (d5,d1) (d4,d3) (d2,d4)")
    print("  --- NO pair between d4 and d5 ---")
    print()
    print("Alice — routine authorization, within limit, nothing else fires.")
    print(f"  answer(can_authorize(alice, t_a)) = {result_alice.name}")
    print()
    print("Carol — transaction under audit, no emergency.")
    print("  d3 defeats d1 via superiority. Audit hold stands.")
    print(f"  answer(can_authorize(carol, t_c)) = {result_carol.name}")
    print()
    print("Dave — transaction under audit AND emergency declared.")
    print("  d4 beats d3 via (d4, d3). Break-glass releases the audit hold.")
    print(f"  answer(can_authorize(dave, t_d)) = {result_dave.name}")
    print()
    print("Eve — is the beneficiary, emergency declared.")
    print("  d4 fires, but (d2, d4) keeps the self-dealing bar ahead of break-glass.")
    print(f"  answer(can_authorize(eve, t_e)) = {result_eve.name}")
    print()
    print("Frank — emergency declared AND high-value txn AND sole approver.")
    print("  d4 (can) and d5 (~can) have disjoint bodies and no superiority pair.")
    print("  Specificity is silent, superiority is silent, so they mutually block:")
    print("  emergency cannot waive four-eyes, four-eyes cannot trump emergency.")
    print(f"  answer(can_authorize(frank, t_f)) = {result_frank.name}")
    print()
    print("Dialectical tree for can_authorize(frank, t_f):")
    print(render_tree(_tree_for(frank_q)))
    print()
    print("Prose explanation (Garcia & Simari 2004 §6):")
    print(explain(_tree_for(frank_q), criterion))
