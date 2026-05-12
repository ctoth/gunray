# The making of SPINdle

## Source

- Authors: Ho-Pun Lam and Guido Governatori
- Venue/year: RuleML 2009
- DOI: 10.1007/978-3-642-04985-9_29
- Read from page images: `pngs/page-000.png` through `pngs/page-007.png`

## Implementation-Relevant Notes

- Page 1 describes SPINdle as a Java defeasible-logic reasoner for standard and modal DL, with support for facts, strict rules, defeasible rules, defeaters, superiority, negation/conflicting literals, XML/plain-text theory formats, and query-oriented use.
- Page 2 defines a defeasible theory as `(F, R, >)` and says SPINdle considers essentially propositional rules, with variables interpreted as ground instances.
- Page 2 distinguishes strict rules, defeasible rules, and defeaters. Defeaters provide contrary evidence but are not themselves used to draw positive conclusions.
- Page 3 states the skeptical conflict intuition: if there is support for `A` and support for `not A`, no conclusion is drawn unless priority resolves the conflict.
- Page 3 gives the four tags Gunray must be able to project: `+Delta q`, `-Delta q`, `+partial q`, and `-partial q`, meaning definitely provable, not definitely provable, defeasibly provable, and not defeasibly provable.
- Page 3 gives the operational rule for a defeasible conclusion: `p` can be derived when there is an applicable strict/defeasible rule for `p` and opposing rules are either discarded/not applicable or weaker than an applicable rule for `p`.
- Page 4 says SPINdle has a parser, theory normalizer, and inference engine.
- Page 5 says preprocessing transforms a theory into an equivalent theory without superiority relation and defeaters, and also splits multiple-head rules into equivalent single-head rules.
- Page 5 describes conclusion generation as repeatedly asserting facts/conclusions, removing satisfied body literals, deactivating rules with refuted body literals, scanning for empty heads, and moving unresolved conflicting heads into pending conclusions until conflicting rules can be proved negatively.
- Page 6 adds that modal variants need additional rules and conflict-literal lists; this does not affect the standard-DL fixture groups in the Gunray workstream.
- Pages 6-8 are mostly performance and conclusion material. The implementation evidence relevant to Gunray is the intended SPINdle behavior for incomplete/inconsistent theories and the fact that SPINdle treats non-provability as a first-class conclusion tag.

## Gunray Implications

- SPINdle fixture expectations should be interpreted as a projection over four proof tags, not as a request to change base Garcia/Simari warrant semantics.
- Missing or unsatisfied antecedents should be capable of producing negative proof tags where the DL proof theory requires every rule for a literal to fail.
- Superiority should not be hacked at query projection time; the paper frames it as a normal-form transformation issue.
