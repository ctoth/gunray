---
title: "Computing Generalized Specificity"
authors: "Frieder Stolzenburg; Alejandro J. Garcia; Carlos I. Chesnevar; Guillermo R. Simari"
year: 2003
venue: "Journal of Applied Non-Classical Logics"
doi_url: "https://doi.org/10.3166/jancl.13.87-113"
pages: 27
---

# Computing Generalized Specificity

## One-Sentence Summary
The paper gives a computational form of generalized specificity for DeLP-style
arguments by replacing an exponential possible-facts definition with equivalent
activation-set and path-set characterizations over completed derivation trees.

## Problem Addressed
Rule-based defeasible systems need a criterion for deciding between
contradictory conclusions, but fixed programmer-supplied rule priorities are
too brittle when the evidence set changes. Stolzenburg et al. argue for an
autonomous, context-sensitive comparison over whole arguments, including strict
background rules as well as defeasible rules. *(pp.1-3)*

## Key Contributions
- Defines generalized specificity for DeLP arguments using possible-fact
  activation and a non-triviality condition. *(p.8)*
- Shows why comparing only pairs of defeasible rules is unsatisfactory when
  strict rules connect or disconnect antecedents. *(pp.9-10)*
- Introduces pruning and argument completions to make specificity computable
  in the presence of strict rules and multi-antecedent rules. *(pp.11-13)*
- Gives an algorithm for computing non-trivial activation sets from a completed
  argument. *(p.14)*
- Proves equivalence between the original generalized-specificity relation and
  a revised activation-set criterion when completions are handled correctly.
  *(pp.14-16)*
- Gives a path-set characterization that can be implemented syntactically over
  derivation trees. *(pp.16-17)*

## Study Design

## Methodology
The paper is theoretical. It starts from DeLP programs `P = (Pi, Delta)`, where
`Pi` is strict knowledge and `Delta` is defeasible knowledge. Arguments are
minimal non-contradictory sets of ground defeasible rule instances that support
literal conclusions under strict closure. Generalized specificity is first
defined semantically using all possible fact sets, then reformulated through
completed derivation trees, activation sets, and path sets so the comparison is
computationally attractive. *(pp.3-17)*

## Key Equations / Statistical Models

Generalized specificity: argument `(A1, h1)` is more specific than `(A2, h2)`
when every possible-fact set `H` that non-trivially activates `A1` for `h1`
also activates `A2` for `h2`.

```text
Pi_G union H union A1 derives h1
and
Pi_G union H does not derive h1
imply
Pi_G union H union A2 derives h2
```

Here `Pi_G` is the set of non-fact strict rules, `F` is the set of literals
that have defeasible derivations, and `H` ranges over subsets of `F`. *(p.8)*

Strict specificity adds a witness showing the reverse implication fails:

```text
exists H' subset F:
  Pi_G union H' union A2 derives h2
  Pi_G union H' does not derive h2
  Pi_G union H' union A1 does not derive h1
```

*(p.8)*

Activation-set criterion:

```text
(A1, h1) is strictly more specific than (A2, h2)
iff
1. for all U in NTAct-sets(A1), Pi_G union U union A2 derives h2
2. exists U' in NTAct-sets(A2) such that Pi_G union U' union A1 does not derive h1
```

*(p.14)*

Path-set criterion:

```text
T1 >= T2 iff for every path t2 in Paths(T2)
there exists a path t1 in Paths(T1) such that t1 subseteq t2
```

*(p.16)*

Syntactic specificity criterion:

```text
(A1, h1) >= (A2, h2)
iff for all derivation trees T1 for h1 pruned wrt A1,
there is a derivation tree T2 for h2 pruned wrt A2
such that T1 >= T2
```

*(p.16)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Strict-rule set | `Pi` | - | - | finite set | 4 | Strict part of a DeLP program. |
| Defeasible-rule set | `Delta` | - | - | finite set | 4 | Tentative rules; presumptions are excluded from the paper's object language. |
| Argument rule set | `A` | - | - | subset of ground instances of `Delta` | 6 | Must support the conclusion, be non-contradictory with `Pi`, and be minimal. |
| Non-fact strict rules | `Pi_G` | - | - | subset of `Pi` | 8 | Strict rules in `Pi` that are not facts. |
| Possible facts | `F` | - | - | literals with a defeasible derivation | 8 | Candidate facts used in Definition 3.1. |
| Completed argument | underlined `A` | - | - | strict and defeasible rules without facts | 12-13 | Built from a derivation tree for an argument; multiple completions may exist. |
| Activation set | `U` | - | - | subset of `Lit(A)` | 13 | Minimal set of literals that activates a completed argument. |
| Non-trivial activation set | `NTAct-sets(A)` | - | - | activation sets where strict knowledge alone does not derive the conclusion | 13 | Used to avoid trivial activations. |
| Paths of a derivation tree | `Paths(T)` | - | - | set of root-excluded leaf-to-ancestor literal sets | 16 | Used for syntactic comparison. |

## Effect Sizes / Key Quantitative Results

Not applicable.

## Methods & Implementation Details
- A strict rule is `Head <- Body`; if the body is empty, it is a fact. A
  defeasible rule uses the weaker arrow and has a non-empty body in this paper.
  *(pp.3-4)*
- Presumptions are explicitly excluded because they can yield counterintuitive
  specificity comparisons when compared only by subset size. *(p.4)*
- A defeasible derivation tree is an and-tree rooted at the literal being
  derived; each node corresponds to a strict or defeasible rule instance whose
  children are the instantiated body literals. *(p.5)*
- An argument is a minimal set of ground defeasible rule instances `A` such
  that `Pi union A` derives the conclusion and is non-contradictory. Strict
  rules are not part of the argument rule set. *(pp.6-7)*
- Strict-only arguments cannot be defeated because a non-empty defeater would
  make itself contradictory under the strict derivation. *(p.7)*
- Specificity is independent of defeat; in DeLP, defeat decides when the
  specificity comparison is consulted. *(p.9)*
- Example 3.2 shows why pruning is needed: while comparing `A` for `x` and `B`
  for `~x`, another argument completion can activate a derivation, so derivation
  tree portions outside the compared argument must be removed. *(p.11)*
- Definition 3.3 prunes a derivation tree by deleting nodes below labels that
  are heads of defeasible rules outside the compared argument. *(p.12)*
- Definition 3.5 gives the computationally preferred completion: a derivation
  tree for `h` that does not use any defeasible rule outside `A`; the completion
  is the set of strict and defeasible non-fact rules used in that tree. *(p.12)*
- Figure 3 algorithm initializes a stack with `({h}, trivial)`, expands a set by
  replacing one literal with the body of a non-empty rule from the completion,
  marks the expansion non-trivial when a defeasible rule is used, and returns all
  generated non-trivial activation sets. *(p.14)*
- Theorem 3.11 proves that the activation-set version with original
  completions is equivalent to the original Definition 3.1 relation. *(pp.15-16)*
- Theorem 3.15 proves that the path-set relation implies the original
  specificity relation; if there are no non-fact strict rules, the converse also
  holds. *(p.17)*
- Example 3.16 demonstrates why the converse direction of Theorem 3.15 requires
  the empty-`Pi_G` restriction. *(p.18)*

## Figures of Interest
- **Figure 1 (p.6):** Derivation trees for the soccer-domain Example 2.6.
- **Figure 2 (p.11):** Derivation trees for Example 3.2, including the pruned
  branch that motivates Definition 3.3.
- **Figure 3 (p.14):** Algorithm for computing non-trivial activation sets.
- **Figure 4 (p.18):** Derivation trees for Example 3.16, the counterexample to
  a converse implication when strict background rules are present.

## Results Summary
The paper concludes that generalized specificity can be characterized by
activation sets and derivation trees, avoiding a direct search through all
possible fact sets. In restricted settings with singleton antecedents and no
strict background rules, the syntactic path-set check reduces to one subset test
over linear derivations, hence can be done in polynomial time. *(pp.18-19)*

## Limitations
- The paper excludes presumptions from the object language. *(p.4)*
- The direct possible-facts definition is exponential and not itself the
  recommended implementation route. *(p.12)*
- With non-empty strict background knowledge, path-set specificity is not fully
  equivalent in both directions to the original relation. *(pp.17-18)*
- The paper focuses on the comparison criterion, not full dialectical-tree
  construction. *(p.19)*

## Arguments Against Prior Work
- Fixed programmer-supplied priorities are not evidence-sensitive: when the
  evidence set changes, a priority relation that once produced the intuitive
  result may become wrong. *(pp.1-2, 20)*
- Dung and Son's approach assumes background knowledge is empty; the paper
  treats strict background rules as part of the comparison problem. *(pp.1-2,
  20)*
- Prioritized default logic and inheritance approaches impose explicit
  preference orderings and often ignore strict rules in the specificity
  comparison. *(pp.22-23)*
- Rule-priority approaches such as the superiority relation in defeasible logic
  compare clauses, while this paper compares complete arguments. *(p.24)*

## Design Rationale
- Compare arguments, not isolated rules, because strict rules can make an
  apparently more informed rule no more specific in context. *(pp.9-10)*
- Use completions and pruning because specificity must account for derivations
  that support body literals without importing unrelated defeasible rules into
  the compared argument. *(pp.11-13)*
- Treat strict rules as background knowledge rather than argument support, but
  allow them to participate in the derivation/completion machinery. *(pp.6-13)*
- Keep specificity modular relative to defeat: a specificity relation can be
  embedded naturally in DeLP by the defeater notion. *(p.19)*

## Testable Properties
- Strict-only arguments must not be defeated by non-empty defeasible arguments.
  *(p.7)*
- If an argument is activated non-trivially by `H`, specificity requires the
  compared argument to activate under the same `H`. *(p.8)*
- Adding or replacing strict background facts can change specificity results;
  fixed rule priorities must not be used as a substitute oracle. *(pp.9-10)*
- Activation-set generation must return only sets reached through at least one
  defeasible-rule expansion as non-trivial. *(pp.13-14)*
- If `Pi_G` is empty, path-set specificity and original specificity coincide
  in both directions. *(p.17)*
- If `Pi_G` is non-empty, the path-set converse can fail, as in Example 3.16.
  *(p.18)*

## Relevance to Project
Gunray's `GeneralizedSpecificity` should be tested against activation-set and
path-set edge cases, especially strict background rules, pruning/completion
cases, and strict-only arguments. The paper supports a single corrected default
specificity implementation rather than optional compatibility modes.

## Open Questions
- [ ] Whether Gunray's current implementation already computes completions over
  strict background rules in the Stolzenburg sense.
- [ ] Whether current tests include Example 3.2, Example 3.6, and Example 3.16
  as page-cited edge cases.
- [ ] Whether a small independent activation-set oracle can be kept in tests
  without becoming a second production implementation.

## Related Work Worth Reading
- Dung and Son 1996 on argumentation-theoretic reasoning with specificity.
- Simari and Loui 1992 on mathematical treatment of defeasible reasoning.
- Garcia 1997/1998/2000 DeLP definitions and implementation.
- Brewka and Eiter 2000 on prioritized default logic.
- Horty 1994 on defeasible inheritance networks.

## Collection Cross-References

### Already in Collection
- [A Mathematical Treatment of Defeasible Reasoning and its Implementation](../Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md) — cited as one of the specificity foundations that this paper turns into a computational criterion for DeLP-style arguments.
- [Defeasible Logic Programming: An Argumentative Approach](../Garcia_2004_DefeasibleLogicProgramming/notes.md) — Garcia 2004 cites this paper for the formal specificity comparison criterion used in DeLP.
- [Relational Databases as a Massive Information Source for Defeasible Argumentation](../Deagustini_2013_RelationalDatabasesDefeasibleArgumentation/notes.md) — later relational-database work depends on DeLP argument construction where specificity is a comparison component.

### New Leads (Not Yet in Collection)
- Dung and Son (1996), "An Argumentation-theoretic Approach to Reasoning with Specificity" — directly contrasted as less able to handle strict background knowledge.
- Garcia (1997), "Defeasible Logic Programming: Definition and Implementation" — implementation source for the DeLP system using the activation-set algorithm.
- Garcia (2000), "Defeasible Logic Programming: Definition, Operational Semantics and Parallelism" — broader implementation and operational source for DeLP.
- Brewka and Eiter (2000), "Prioritizing Default Logic" — comparison point for explicit-priority default reasoning.
- Prakken and Sartor (1997), "Argument-based logic programming with defeasible priorities" — comparison point for explicit defeasible priorities.

### Supersedes or Recontextualizes
- [A Mathematical Treatment of Defeasible Reasoning and its Implementation](../Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md) — recontextualizes Poole/Simari-style specificity as a computable activation-set/path-set criterion over DeLP derivation trees.

### Cited By (in Collection)
- [Defeasible Logic Programming: An Argumentative Approach](../Garcia_2004_DefeasibleLogicProgramming/notes.md) — cites Stolzenburg 2003 as the formal details of DeLP's generalized-specificity comparison criterion.

### Conceptual Links (not citation-based)
- [Grounding Rule-Based Argumentation with Datalog](../Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md) — both papers replace naive rule expansion with a more structured computation over derivations: Stolzenburg for argument comparison and Diller for first-order ASPIC+ grounding.
- [A Mathematical Treatment of Defeasible Reasoning and its Implementation](../Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md) — Simari and Loui provide the older specificity/warrant foundation; Stolzenburg adds the algorithmic machinery Gunray should test against.
