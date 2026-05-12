# A Semantic Decomposition of Defeasible Logics

## Source

- Authors: Michael J. Maher and Guido Governatori
- Venue/year: AAAI-99
- Read from page images: `pngs/page-000.png` through `pngs/page-006.png`

## Implementation-Relevant Notes

- Page 1 gives the four conventional defeasible-logic tags: `+Delta`, `-Delta`, `+partial`, and `-partial`, where negative tags mean that non-provability has itself been proved.
- Page 1 defines definite provability over facts and strict rules, and defeasible provability over strict/defeasible rules plus counterattack. The important condition for `+partial q` is that every rule for the complement of `q` must either be inapplicable or countered by an applicable superior rule for `q`.
- Page 1 defines `-partial q` as the constructive failure condition: `q` is not definitely provable and either all strict/defeasible rules for `q` fail, the complement is definitely provable, or there is an applicable opposing rule that cannot be beaten by an applicable superior rule for `q`.
- Page 2 introduces a bottom-up operator over four sets of literals and proves that its fixed point captures the proof theory for finite propositional defeasible theories.
- Page 2 states coherence and consistency for conventional defeasible logic: a literal is not both provable and unprovable, and defeasible inconsistency only arises from definite inconsistency.
- Pages 2-3 introduce well-founded defeasible logic. A self-supporting rule such as `p => p` yields neither positive nor negative conventional DL conclusions, while the well-founded variant can derive the negative tag by using unfounded sets.
- Page 3 gives a concrete well-founded example where conventional DL derives only negative tags for `d` and `not d`, while the well-founded variant also derives negative tags for `a` and `not c`.
- Page 3 starts the metaprogram decomposition with predicates for `fact`, `strict`, `defeasible`, `defeater`, and `sup`.
- Page 3 gives the core clauses: `definitely` from facts or strict rules, `not_definitely` from failure of `definitely`, `defeasibly` from `definitely` or a supportive rule whose body is defeasible and not overruled, `overruled` from applicable contrary rules, `defeated` from superior applicable rules, and `not_defeasibly` from failure of `defeasibly`.
- Page 4 maps a defeasible theory into metaprogram facts and states that Kunen semantics of the metaprogram characterizes the four DL proof tags.
- Pages 4-5 connect well-founded defeasible logic to well-founded semantics and show that well-founded DL generally derives more conclusions than conventional DL under the same syntax.
- Page 5 adds explicit failure operators as a conservative extension: rules may require failure to prove a literal definitely or defeasibly without changing interpretations for theories that do not use those operators.

## Gunray Implications

- Treating `not_defeasibly` and `not_definitely` as explicit result classifications is paper-backed; they are not merely absence of answers.
- Conventional DL and well-founded DL differ on cycles. Gunray should not make unfounded-set behavior implicit in the current SPINdle fixture work unless the target fixture explicitly demands the well-founded variant.
- A test-first implementation should encode the metaprogram clauses as properties over small theories: positive definite, negative definite, positive defeasible, negative defeasible, overruled, and defeated.
