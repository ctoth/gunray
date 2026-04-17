"""Git ancestry: plain Datalog via the transitive-closure idiom.

Shows: ``GunrayEvaluator`` dispatching a ``Program`` to
``SemiNaiveEvaluator`` and the standard reachability encoding of
transitive closure over a commit DAG.
Source: Abiteboul, Hull, and Vianu 1995, "Foundations of Databases",
Example 3.1.5 p.46 (reachability / path recursion).
"""

from __future__ import annotations

from gunray import GunrayEvaluator, Model, Program
from gunray.schema import FactTuple

# Commit DAG (parent edges, child -> parent):
#
#     c1 -- c2 -- c3 ---- c6 -- c7 (HEAD on main)
#            \             /
#             c4 -- c5 ---+     (feature branch merged into c6)
#
# edge(child, parent) means "child has parent as a direct ancestor".
edges: set[FactTuple] = {
    ("c2", "c1"),
    ("c3", "c2"),
    ("c4", "c2"),
    ("c5", "c4"),
    ("c6", "c3"),
    ("c6", "c5"),
    ("c7", "c6"),
}

program = Program(
    facts={"edge": edges},
    rules=[
        "ancestor(X, Y) :- edge(X, Y).",
        "ancestor(X, Z) :- edge(X, Y), ancestor(Y, Z).",
    ],
)

model = GunrayEvaluator().evaluate(program)
assert isinstance(model, Model)
ancestors = model.facts["ancestor"]

# c1 is the initial commit; c7 is HEAD. Transitive closure must reach
# back to the root along either the direct chain or the feature branch.
assert ("c7", "c1") in ancestors, f"expected ancestor(c7, c1), got {ancestors!r}"
assert ("c6", "c1") in ancestors
assert ("c5", "c1") in ancestors


if __name__ == "__main__":
    print("Git ancestry (Datalog transitive closure)")
    print()
    print("  edge facts (child -> parent):")
    for child, parent in sorted(edges):
        print(f"    {child} -> {parent}")
    print()
    print("  rules:")
    print("    ancestor(X, Y) :- edge(X, Y).")
    print("    ancestor(X, Z) :- edge(X, Y), ancestor(Y, Z).")
    print()
    print(f"  derived ancestor/2 facts ({len(ancestors)}):")
    for child, parent in sorted(ancestors):
        print(f"    ancestor({child}, {parent})")
    print()
    print("  c1 is the initial commit; c7 is HEAD.")
    print(f"  ancestor(c7, c1) present: {('c7', 'c1') in ancestors}")
