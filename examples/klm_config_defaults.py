"""KLM rational closure: DB-down suppresses the server-responds default.

Shows: ``ClosurePolicy.RATIONAL_CLOSURE`` routing into ``ClosureEvaluator`` and
producing a zero-arity ``DefeasibleModel`` where an exceptional subclass
(``db_down``) blocks the more general default (``server_responds`` under
``server_up``). The ``ClosureEvaluator`` enforces a zero-arity
propositional fragment (``closure.py:134`` ``_ensure_propositional``),
so the scenario is encoded with propositional atoms rather than Datalog
predicates.
Source: Lehmann and Magidor 1992, "What does a conditional knowledge
base entail?", Artificial Intelligence 55(1), rational-closure ranking
p.33; ranking algorithm per Morris, Ross, and Meyer 2020 Algorithm 3
p.150 (as cited in ``closure.py``).
"""

from __future__ import annotations

from gunray import (
    ClosurePolicy,
    DefeasibleModel,
    DefeasibleTheory,
    GunrayEvaluator,
    Rule,
)
from gunray.schema import FactTuple, PredicateFacts

# Zero-arity facts: the server is up, and the database is down.
empty_tuple: FactTuple = ()
facts: PredicateFacts = {
    "server_up": [empty_tuple],
    "db_down": [empty_tuple],
}

theory = DefeasibleTheory(
    facts=facts,
    # A server being down is classically incompatible with responding.
    strict_rules=[Rule(id="s1", head="~server_responds", body=["server_down"])],
    defeasible_rules=[
        # General default: servers typically respond.
        Rule(id="d1", head="server_responds", body=["server_up"]),
        # Exceptional subclass: db_down servers typically do not respond.
        Rule(id="d2", head="~server_responds", body=["db_down"]),
        # db_down is a species of server_up (db_down implies server_up by default).
        Rule(id="d3", head="server_up", body=["db_down"]),
    ],
)

model = GunrayEvaluator().evaluate(theory, closure_policy=ClosurePolicy.RATIONAL_CLOSURE)
assert isinstance(model, DefeasibleModel)

defeasibly = model.sections.get("defeasibly", {})
not_defeasibly = model.sections.get("not_defeasibly", {})

# Rational closure ranks d1 at rank 0 and d2 at rank 1 (db_down is
# exceptional w.r.t. d1). Under db_down the higher rank wins, so
# ~server_responds is warranted and server_responds is not.
assert "~server_responds" in defeasibly, (
    f"expected ~server_responds in defeasibly, got {sorted(defeasibly)!r}"
)
assert "server_responds" in not_defeasibly, (
    f"expected server_responds in not_defeasibly, got {sorted(not_defeasibly)!r}"
)


if __name__ == "__main__":
    print("KLM rational closure: DB-down server defaults")
    print()
    print("  facts: server_up, db_down")
    print("  s1: ~server_responds :- server_down   (strict)")
    print("  d1:  server_responds <= server_up")
    print("  d2: ~server_responds <= db_down")
    print("  d3:  server_up       <= db_down")
    print()
    print("  defeasibly:")
    for atom in sorted(defeasibly):
        print(f"    {atom}")
    print("  not_defeasibly:")
    for atom in sorted(not_defeasibly):
        print(f"    {atom}")
    print()
    print("  db_down is exceptional under d1, so rational closure gives")
    print("  d2 the higher rank and ~server_responds is the warranted")
    print("  conclusion rather than server_responds.")
