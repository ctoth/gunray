# Argumentation Semantics for Defeasible Logic

## Source

- Authors: Guido Governatori, Michael J. Maher, Grigoris Antoniou, and David Billington
- Venue/year: Journal of Logic and Computation, 2004
- DOI: 10.1093/logcom/14.5.675
- Read from page images: `pngs/page-000.png` through `pngs/page-027.png`

## Implementation-Relevant Notes

- Page 675 says the paper provides Dung-like argumentation semantics for two key defeasible logics: one ambiguity propagating and one ambiguity blocking.
- Page 676 says the original defeasible logic is ambiguity blocking, while an ambiguity propagating defeasible logic can also be defined.
- Page 677 defines strict rules, defeasible rules, defeaters, superiority, and the bird/broken-wing example. The page also says the paper disregards superiority for exposition, relying on a transformation that empties the superiority relation while preserving conclusions.
- Page 678 defines the rule sets `R_s`, `R_sd`, `R_d`, `R_dft`, `R[q]`, complementary literals, and the four proof tags. Definite provability is strict-only; negative definite provability requires every strict rule for a literal to fail.
- Pages 678-679 define conventional ambiguity-blocking defeasible provability. To prove `+partial q`, opposing rules for the complement of `q` must be inapplicable under negative defeasible proof, or defeated by a superior applicable rule for `q`.
- Page 679 defines ambiguity with the example `=> a`, `=> not a`, `=> b`, `a => not b`. In ambiguity blocking, `b` is provable because the rule for `not b` has ambiguous antecedent `a`; in ambiguity propagation, both `b` and `not b` are blocked.
- Pages 679-680 define support `+Sigma`: a monotonic chain that would derive a literal in the absence of conflicts. This is weaker than defeasible provability.
- Page 680 gives the ambiguity-propagating conditions. Its key change is that attackers are considered applicable when their bodies are supported, not only when they are defeasibly provable.
- Page 681 defines arguments as possibly infinite proof trees. Defeaters can only appear at the top of an argument and cannot be chained for positive evidence.
- Page 682 distinguishes supportive, strict, and defeasible arguments. It connects definite proof to strict supportive arguments and support to supportive arguments.
- Pages 683-684 define attack, supported arguments, undercut, justified arguments, and rejected arguments.
- Page 685 starts grounded semantics for ambiguity propagation: an argument is acceptable when it is strict or every attacker is attacked by already accepted arguments. Rejection is by a proper rejected subargument or attack by a finite argument.
- Page 686 states Theorem 3.12: under grounded semantics, `+partial_ap p` iff `p` is justified and `-partial_ap p` iff `p` is rejected. Example 2.1 rejects all four ambiguous literals under propagation.
- Page 687 defines defeasible semantics for ambiguity blocking. Acceptability is strictness or every attacker being undercut by the accepted set. Rejection requires a rejected subargument or attack by an argument supported by the justified set.
- Page 687 states Theorem 3.15: under defeasible semantics, `+partial p` iff `p` is justified and `-partial p` iff `p` is rejected by justified arguments.
- Page 688 continues Example 2.1: in ambiguity blocking, `b` is justified while `a`, `not a`, and `not b` are rejected. The ambiguity of `a` does not propagate to `b`.
- Pages 688-690 compare grounded and defeasible semantics. Grounded semantics rejects more and justifies fewer; defeasible semantics is more credulous but remains skeptical.
- Pages 691-692 discuss self-defeating and circular arguments. Circular arguments can be neither justified nor rejected unless attacked by supported arguments; this matters for negative proof tags in cycles.
- Page 693 concludes that ambiguity propagation is characterized by Dung grounded semantics, while ambiguity blocking requires the internal structure of arguments to define the needed undercut relation.
- Page 702 Appendix B gives the metaprogram used by the variants. Clauses `c1-c6` are common; `c7` defines `overruled` for ambiguity blocking using `defeasibly` on the opposing rule body, while `c8` defines `overruled` for ambiguity propagation using `supported` on the opposing rule body.

## Gunray Implications

- The existing Antoniou blocking/propagating split is paper-backed: the only metaprogram difference is whether opposition uses `defeasibly` or `supported`.
- SPINdle-style missing-premise expectations should be implemented as proof-tag projection over `not_definitely` and `not_defeasibly`, not by adding an arbitrary output knob.
- Superiority-sensitive fixture work must respect the paper's normal-form claim. If Gunray does not implement the normal-form transformation, tests requiring priority-specific SPINdle behavior need a page-backed deferral or a deletion-first implementation of that transformation.
