"""SAFE vs NEMO: the same program, two negation semantics.

Shows: ``NegationSemantics.SAFE`` rejecting a rule whose negated body
literal introduces an otherwise-unbound variable, and
``NegationSemantics.NEMO`` accepting the same rule. Gunray evaluates a
negated body literal by scanning for any unifying row in the predicate;
an unbound variable in that literal therefore reads as "the predicate
is empty".
Source: Apt, Blair, and Walker 1988, "Towards a theory of declarative
knowledge", safety condition p.107 (as cited in
``src/gunray/schema.py``); Nemo compatibility mode per Ivliev et al.
2024, "Nemo: Your Friendly and Versatile Rule Reasoning Toolkit",
KR 2024 pp.743-754 (doi:10.24963/kr.2024/70).
"""

from __future__ import annotations

from gunray import GunrayEvaluator, Model, NegationSemantics, Program
from gunray.errors import SafetyViolationError
from gunray.schema import FactTuple

# Two people; the ``flagged/1`` predicate is mentioned only in a rule
# body and has no facts asserted for it at all.
people: set[FactTuple] = {("alice",), ("bob",)}

# The rule has no positive body literal binding Y; Y is introduced only
# inside the negated literal ``not flagged(Y)``. SAFE (Apt-Blair-Walker)
# rejects the rule outright. NEMO accepts it and evaluates the negated
# literal by asking "is there any row of flagged that unifies?" — if
# not, the literal holds and the rule fires.
program = Program(
    facts={"person": people},
    rules=[
        "suspicious(X) :- person(X), not flagged(Y).",
    ],
)

evaluator = GunrayEvaluator()

safe_error: SafetyViolationError | None = None
try:
    evaluator.evaluate(program, negation_semantics=NegationSemantics.SAFE)
except SafetyViolationError as exc:
    safe_error = exc

assert safe_error is not None, "SAFE mode must reject the unbound negated variable"

nemo_model = evaluator.evaluate(program, negation_semantics=NegationSemantics.NEMO)
assert isinstance(nemo_model, Model)
suspicious = nemo_model.facts.get("suspicious", set())

# Under NEMO, ``flagged`` is empty so the negated literal holds, and the
# rule fires once per person. Both alice and bob come out suspicious.
assert ("alice",) in suspicious, f"expected suspicious(alice), got {suspicious!r}"
assert ("bob",) in suspicious, f"expected suspicious(bob), got {suspicious!r}"


if __name__ == "__main__":
    print("SAFE vs NEMO: the same program, two negation semantics")
    print()
    print("  facts: person(alice), person(bob); flagged/1 has no rows")
    print("  rule:  suspicious(X) :- person(X), not flagged(Y).")
    print()
    print("  SAFE  -> SafetyViolationError:")
    print(f"    {safe_error}")
    print()
    print("  NEMO  -> suspicious/1 facts:")
    for row in sorted(suspicious):
        print(f"    suspicious({row[0]})")
    print()
    print("  Y is only bound under negation, so SAFE (Apt-Blair-Walker)")
    print("  rejects the rule. NEMO accepts it; since flagged is empty,")
    print("  no row unifies with flagged(Y) and the negated literal holds,")
    print("  so the rule fires for every person X.")
