# Papers

## [Computing Generalized Specificity](Stolzenburg_2003_ComputingGeneralizedSpecificity/notes.md)  (argumentation, defeasible-reasoning, specificity)
This paper gives computational characterizations of generalized specificity for DeLP arguments using activation sets and derivation-tree path sets. It shows that fixed rule priorities are not evidence-sensitive enough when strict background knowledge and multi-antecedent defeasible rules are present. It is directly relevant to Gunray's generalized-specificity preference implementation and property tests.

## [The making of SPINdle](Lam_2009_MakingSPINdle/notes.md)  (defeasible-reasoning, spindle, implementation)
This implementation paper describes SPINdle's proof-tag target, preprocessing architecture, normalisation of superiority/defeaters, and conclusion-generation process. It is directly relevant to Gunray's SPINdle fixture projection work.

## [A Semantic Decomposition of Defeasible Logics](Maher_1999_SemanticDecomposition/notes.md)  (defeasible-reasoning, metaprogramming, well-founded-semantics)
This paper decomposes defeasible logic into executable metaprogram predicates such as `definitely`, `not_definitely`, `defeasibly`, and `not_defeasibly`. It is the clearest source for treating negative proof tags as explicit classifications rather than absence of answers.

## [Argumentation Semantics for Defeasible Logic](Governatori_2004_ArgumentationSemantics/notes.md)  (argumentation, ambiguity, defeasible-reasoning)
This paper gives argumentation semantics for ambiguity propagation and ambiguity blocking, with an appendix metaprogram showing that the key implementation distinction is whether opposition is evaluated through `supported` or `defeasibly`.
