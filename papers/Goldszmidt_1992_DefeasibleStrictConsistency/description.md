---
tags: [defeasible-reasoning, consistency, probabilistic-semantics, nonmonotonic-logic, database-consistency]
---
Provides a formal criterion for deciding when a database containing both defeasible (default) and strict (classical) sentences is consistent, based on probabilistic semantics where defaults are interpreted as high conditional probabilities. The key contribution is a polynomial-time tolerance-based procedure that distinguishes genuine contradictions from mere exceptions to defaults, with equivalence to System Z preferential semantics. Directly relevant to propstore's conflict detection and argumentation layers, providing theoretical grounding for when mixed defeasible/strict claim databases are coherent versus genuinely inconsistent.
