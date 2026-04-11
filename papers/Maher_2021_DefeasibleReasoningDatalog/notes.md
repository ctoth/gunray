---
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:15:42Z"
---
# Defeasible Reasoning via Datalog

- **Title:** Defeasible Reasoning via Datalog
- **Authors:** Michael J. Maher
- **Year:** 2021
- **Venue:** Under consideration for Theory and Practice of Logic Programming (TPLP)
- **doi_url:** https://arxiv.org/abs/2106.10946

## One-Sentence Summary

The paper compiles defeasible logic $DL(\partial_{||})$ into standard Datalog$^\neg$ programs via metaprogram representation and unfold/fold transformations, proving correctness and establishing structural properties that enable efficient implementation using existing Datalog engines.

## Problem Addressed

Implementations of defeasible logic are typically bespoke, tightly coupled to specific hardware/software architectures, and difficult to port. The paper addresses how to leverage the mature ecosystem of Datalog implementations (top-down tabling, SLG resolution, bottom-up semi-naive) to execute defeasible reasoning without building custom inference engines. *(p.1)*

## Key Contributions

1. **Metaprogram representation** of defeasible logic $D(1,1)$ (a.k.a. $DL(\partial_{||})$) as a logic program, building on Maher & Governatori 1999 and Antoniou et al. 2000. *(p.12)*
2. **Compilation via unfold/fold transformations** that convert the metaprogram into a standard Datalog$^\neg$ program $T_D$ (later $S_D$) that is linear in the size of the defeasible theory. *(p.16-22)*
3. **Correctness proofs** that the compiled program preserves the well-founded semantics of the original defeasible theory. *(p.25-29)*
4. **Structural property theorems** showing the compiled program inherits properties (range-restriction, stratification, call-consistency, local stratification) from the source theory. *(p.30-31)*
5. **Identification of executable subsets** — hierarchical theories yield stratified programs; locally hierarchical theories yield locally stratified programs; all theories yield call-consistent programs. *(p.33-35)*

## Methodology

The approach proceeds in stages:

1. **Represent** the defeasible theory $D = (F, R, >)$ as unit clauses: `fact(p)`, `strict(r, p, [q1,...,qn])`, `defeasible(r, p, [q1,...,qn])`, `defeater(r, p, [q1,...,qn])`, `sup(r, s)`. *(p.12)*
2. **Express** the inference rules of $DL(\partial_{||})$ as a metaprogram $\mathcal{M}(D)$ with clauses c1-c8 defining `definitely`, `lambda`, `defeasibly`, `overruled`, `defeated`. *(p.12-13)*
3. **Transform** via partial evaluation: unfold all occurrences of theory-representation predicates, delete them. Result: $P_D$. *(p.16-17)*
4. **Further transform** by introducing body predicates $\text{body}_r^\Delta$, $\text{body}_r^\lambda$, $\text{body}_r^d$, folding to eliminate list structures and function symbols. Result: $T_D$. *(p.18-20)*
5. **Final transforms** to eliminate remaining function symbols via predicate renaming (c22-c31), producing the final Datalog$^\neg$ program. *(p.20-21)*

## Key Equations

### Defeasible Logic Inference Rules *(p.8)*

**Definite provability (+$\Delta$):**

$$+\Delta: \text{If } P(1) \vdash +\Delta \text{ then either } -\Delta.1) \; P(1) \vdash +\Delta \text{ or } -\Delta.2) \; P(2) = -\Delta q \text{ then}$$

The four inference tags:
- $+\Delta q$: $q$ is definitely provable (strict rules only)
- $-\Delta q$: $q$ is not definitely provable
- $+\partial q$: $q$ is defeasibly provable
- $-\partial q$: $q$ is not defeasibly provable

Where:
- $F$ = set of facts
- $R$ = set of rules (strict $\to$, defeasible $\Rightarrow$, defeater $\leadsto$)
- $>$ = superiority relation on rules
- $R[q]$ = rules with head $q$
- $R_s[q]$ = strict rules for $q$
- $R_{sd}[q]$ = strict or defeasible rules for $q$

### Core Metaprogram Clauses *(p.12-13)*

```
c1  definitely(X) :- fact(X).
c2  definitely(X) :- strict(R, X, [Y1,...,Yn]),
                      definitely(Y1), ..., definitely(Yn).
c3  lambda(X) :- definitely(X).
c4  lambda(X) :- not definitely(~X),
                  strict_or_defeasible(R, X, [Y1,...,Yn]),
                  lambda(Y1), ..., lambda(Yn).
c5  defeasibly(X) :- definitely(X).
c6  defeasibly(X) :- not definitely(~X),
                      strict_or_defeasible(R, X, [Y1,...,Yn]),
                      defeasibly(Y1), ..., defeasibly(Yn),
                      not overruled(X).
c7  overruled(X) :- rule(S, ~X, [U1,...,Un]),
                     lambda(U1), ..., lambda(Un),
                     not defeated(S, ~X).
c8  defeated(S, ~X) :- sup(T, S),
                        strict_or_defeasible(T, X, [V1,...,Vn]),
                        defeasibly(V1), ..., defeasibly(Vn).
```

### Final Compiled Program $T_D$ / $S_D$ Structure *(p.21-22)*

For each fact $q(\vec{a})$ in $D$: unit clauses `definitely_q`, `lambda_q`, `defeasibly_q`. *(p.21)*

For each strict rule $r$: clauses c32 (`definitely_q :- body_r^Delta`), c33 (`lambda_q :- body_r^Delta`), c34 (`defeasibly_q :- body_r^Delta`), c35 (`body_r^Delta :- definitely_q1,...,definitely_qn`). *(p.21)*

For each strict/defeasible rule $r$: c36 (`lambda_q :- not definitely_~q, body_r^lambda`), c37 (`defeasibly_q :- not definitely_~q, body_r^d, not overruled_q`), c38 (`body_r^lambda :- lambda_q1,...,lambda_qn`), c39 (`body_r^d :- defeasibly_q1,...,defeasibly_qn`). *(p.21)*

For each opposing rule $s$ superior to $t$: c40 (`overruled_~q :- body_s^lambda, not defeated_q(s, a)`), c41 (`defeated_q(s, ~A) :- body_t^d`). *(p.21-22)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Defeasible theory | $D$ | — | — | — | 7 | Triple $(F, R, >)$ |
| Facts | $F$ | — | — | — | 7 | Set of ground atoms |
| Rules | $R$ | — | — | — | 7 | Strict ($\to$), defeasible ($\Rightarrow$), defeater ($\leadsto$) |
| Superiority relation | $>$ | — | — | — | 7 | Partial order on rules |
| Metaprogram | $\mathcal{M}(D)$ | — | — | — | 12 | Logic program encoding of D |
| Compiled program | $T_D$ / $S_D$ | — | — | — | 20-21 | Final Datalog$^\neg$ program |
| Well-founded model | $\models_{WF}$ | — | — | — | 5 | 3-valued Herbrand interpretation |

## Methods & Implementation Details

### Defeasible Logic Variant D(1,1) *(p.7-9)*

$D(1,1)$ is a specific defeasible logic from the parameterized family of Maher 2012. It corresponds to $DL(\partial_{||})$ — the standard variant used in most implementations. Key properties:
- No team defeat (individual defeat only)
- Locally hierarchical (superiority relation only between individual rules)
- Propositional or first-order (with function-free restriction for Datalog compilation) *(p.11)*

### Metaprogram Construction *(p.12-14)*

The defeasible theory is encoded as unit clauses (facts about the theory structure). The inference rules become logic program clauses. Two metaprograms:
- $\mathcal{M}_{D_1}(D)$: under well-founded semantics *(p.13)*
- $\mathcal{M}_{D_2}(D)$: under Fitting semantics *(p.13)*

Key property: both metaprograms are call-consistent (Proposition 6, p.14), ensuring well-founded semantics is well-defined. *(p.14)*

### Unfold/Fold Transformation Pipeline *(p.16-22)*

1. **Partial evaluation** (Section 6.1): Unfold all theory-representation predicates (`fact`, `strict`, `defeasible`, `defeater`, `sup`). Delete unfolded predicates. Preserves well-founded semantics per Maher 1990, Aravindan & Dung 1995. *(p.16)*
2. **Body predicate introduction** (Section 6.2): For each rule $r$ with head $A$ and body $B_1,...,B_n$, introduce:
   - $\text{body}_r^d(\text{args}(A))$ :- `defeasibly(B1),...,defeasibly(Bn)` *(p.18)*
   - $\text{body}_r^\lambda(\text{args}(A))$ :- `lambda(B1),...,lambda(Bn)` *(p.18)*
   - $\text{body}_r^\Delta(\text{args}(A))$ :- `definitely(B1),...,definitely(Bn)` *(p.18)*
3. **Function symbol elimination** (Section 6.2 cont): Replace atoms with function-symbol arguments by predicate-renamed atoms (c22-c31). *(p.20)*

### Size Complexity *(p.22)*

The resulting program $T_D$ is linear in the size of the defeasible theory $D$ (Proposition 11). Specifically, for each rule in $D$, a bounded number of clauses are generated, and each clause is bounded in size by the original rule. *(p.22)*

### Structural Properties (Theorem 21) *(p.30)*

The compiled program $S_D$ satisfies:
1. **Datalog$^\neg$**: function-free *(p.30)*
2. **Variable-free iff D is**: ground theories yield ground programs *(p.30)*
3. **Range-restricted iff D is**: all variables in the head appear in positive body literals *(p.30)*
4. **Safi iff D is range-restricted**: "stratified after function-free instantiation" *(p.30)*
5. **Call-consistent**: no predicate depends positively and negatively on itself *(p.30)*
6. **Stratified iff D is hierarchical**: no rule attacks itself through superiority *(p.31)*
7. **Locally stratified iff D is locally hierarchical** *(p.31)*

### Execution Strategies *(p.33-35)*

| Strategy | System | Semantics | Applicability | Page |
|----------|--------|-----------|---------------|------|
| SLG resolution | XSB | Well-founded | All theories | 33 |
| Semi-naive bottom-up | DLV, IRIS | Well-founded | All theories | 33 |
| Top-down + tabling | XSB | Well-founded | All theories | 33 |
| Stratified evaluation | Any Datalog | Stratified | Hierarchical theories | 34 |
| Ground + ASP | Gringo/Clingo | Stable models | Range-restricted | 35 |
| Fitting semantics | Any | Fitting | All theories (for defeasibly only) | 35 |

## Figures of Interest

- **Example 2** *(p.7-8)*: Tweety/penguin example illustrating defeasible theory structure
- **Example 8** *(p.17)*: Two-rule defeasible theory showing full transformation output
- **Example 12** *(p.22-23)*: Expanded Tweety example showing compiled program $T_D$
- **Example 5** *(p.11)*: Animal taxonomy (egg-laying, mammal, monotreme) showing practical encoding

## Results Summary

- The compilation is **provably correct**: Theorems 15, 19 establish equivalence between the defeasible logic conclusions and the well-founded semantics of the compiled Datalog program. *(p.25, 29)*
- The compiled program is **linear in size** relative to the input theory. *(p.22)*
- **Structural properties transfer**: stratification, range-restriction, call-consistency of the source theory are preserved in the compiled program. *(p.30-31)*
- The approach works for **multiple semantics**: well-founded, Fitting, stratified, stable models. *(p.33-35)*
- The compilation is **modular** in the sense that adding rules to D adds clauses to $S_D$ without modifying existing ones. *(p.22)*

## Limitations

- Only addresses $D(1,1)$ / $DL(\partial_{||})$ — the simplest defeasible logic variant. Team defeat, ambiguity blocking/propagating variants not covered. *(p.11)*
- Does not handle function symbols in rules — requires Datalog (function-free) restriction. *(p.11, 30)*
- The superiority relation must be acyclic for some structural properties. *(p.7)*
- No empirical benchmarks comparing compiled Datalog execution vs. bespoke implementations. *(p.35)*
- The paper does not address incremental updates to the defeasible theory (adding/removing rules dynamically). *(implicit)*

## Arguments Against Prior Work

- Bespoke implementations (like Deimos, d-Prolog) are tied to specific architectures, limiting portability and reuse. *(p.1)*
- Prior metaprogram approaches (Maher & Governatori 1999, Antoniou et al. 2000) stopped at the metaprogram stage without compiling to pure Datalog. *(p.13-14)*
- Governatori 2011 and Lam & Governatori 2009 extended to other defeasible logics but focused on direct implementation rather than compilation. *(p.14)*
- CLP-based approaches (Bassiliades & Antoniou 2006, Governatori & Maher 2017) use constraint logic programming but do not produce standard Datalog programs. *(p.14)*

## Design Rationale

The key insight is that **unfold/fold transformations preserve well-founded semantics** (Maher 1990, Aravindan & Dung 1995). By starting from a correct metaprogram and applying only semantics-preserving transformations, correctness of the final compiled program follows compositionally. This avoids the need for direct correctness proofs of complex compiled programs. *(p.16-18)*

The choice of well-founded semantics (over stable models) is deliberate: well-founded semantics always exists, is unique, and is polynomial-time computable, making it suitable for the "complete but possibly undecided" approach of defeasible reasoning. *(p.4-5)*

## Testable Properties

1. **Compilation correctness**: For any defeasible theory $D$ and ground literal $q$, $+\partial q$ in $D$ iff `defeasibly_q` is true in the well-founded model of $S_D$. *(p.29, Theorem 19)*
2. **Size linearity**: $|S_D| = O(|D|)$ where size is measured in symbols. *(p.22, Proposition 11)*
3. **Call-consistency**: $S_D$ is always call-consistent regardless of $D$. *(p.30, Theorem 21.5)*
4. **Stratification preservation**: If $D$ is hierarchical, $S_D$ is stratified. *(p.30, Theorem 21.6)*
5. **Definite provability correctness**: `definitely_q(a)` in $P_D$ under WF iff $+\Delta q(a)$ in $D$. *(p.25, Theorem 15)*
6. **Negative conclusion correctness**: `not defeasibly_q(a)` in WF model of $S_D$ iff $-\partial q(a)$ in $D$. *(p.29, Theorem 19)*
7. **Hierarchical completeness**: For hierarchical $D$, every literal is either definitely true or definitely false in $S_D$ (no undefined). *(p.34, Theorem 22)*

## Relevance to Project

**High relevance to propstore's argumentation layer.** propstore uses ASPIC+ (via `aspic_bridge.py` and `aspic.py`) to construct arguments from claims. This paper provides an alternative compilation path: defeasible theories could be compiled to Datalog programs and evaluated using existing Datalog engines, potentially offering:

1. **Performance**: The compiled program is linear in size and can leverage optimized Datalog engines (XSB, DLV) with decades of optimization. This could be faster than propstore's current recursive ASPIC+ argument construction for large claim sets.
2. **Approximation**: The structural properties (stratification, call-consistency) enable sound approximations — computing only the positive or negative part of conclusions. This maps to propstore's need for tractable argumentation over large knowledge bases.
3. **Semantic compatibility**: The well-founded semantics used here aligns with propstore's "non-commitment" principle — conclusions can be true, false, or undefined, matching the three-valued approach needed for lazy evaluation until render time.
4. **Bridge to defeasible logic**: propstore currently uses ASPIC+ which is argument-based. This paper shows how to compile the rule-based defeasible logic into executable programs. If propstore wants to support both argument-based and rule-based defeasible reasoning, this compilation technique provides the bridge.

The key limitation for propstore is that this paper only covers $D(1,1)$, while propstore's argumentation needs may require team defeat or other variants. However, the metaprogram approach is explicitly designed to be extensible to other defeasible logics (Section 10, p.35-36).

## Open Questions

1. How does the compiled Datalog program's performance compare to ASPIC+ argument construction on realistic propstore workloads?
2. Can the metaprogram approach be extended to handle ASPIC+ directly (with preferences, undermining, etc.)?
3. What is the relationship between the defeasible logic's superiority relation and ASPIC+'s preference ordering? Can one be compiled to the other?
4. How would incremental theory updates (adding new claims/rules) be handled in the compiled program?

## Related Work

- **Antoniou et al. 2001**: Framework for defeasible logic in ASPIC+ *(p.8)*
- **Governatori & Maher 2017**: Annotated defeasible logic *(p.14)*
- **Nute 1994**: Original defeasible logic formulation *(p.8)*
- **Billington et al. 2010**: Well-founded semantics for defeasible logic *(p.5)*
- **Maher 2012**: Parameterized family of defeasible logics $D(d,a)$ *(p.9)*
- **Swift & Warren 2012**: XSB Prolog with well-founded semantics *(p.33)*
- **Gebser et al. 2019**: Gringo/Clingo ASP system *(p.35)*
- **Caminada & Amgoud 2007**: Bridge between defeasible logic and ASPIC+ argumentation *(cited in references)*

## Collection Cross-References

### Already in Collection
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — cited for rationality postulates (closure, consistency) that structured argumentation systems must satisfy; Maher's compilation preserves these via structural properties of the compiled program
- [[Dung_1995_AcceptabilityArguments]] — foundational; Maher notes that defeasible logic and logic programming with NAF are special forms of Dung's argumentation (p.1)

### New Leads (Not Yet in Collection)
- Maher & Governatori (1999) — "A semantic decomposition of defeasible logics" — foundational metaprogram approach this paper extends
- Antoniou et al. (2001) — "Representation results for defeasible logic" — formal framework for D(1,1) variant
- Swift & Warren (2012) — "XSB: extending Prolog with tabled logic programming" — primary execution target for compiled theories
- Maher (2012) — "Relative expressiveness of defeasible logics" — parameterized D(d,a) family from which D(1,1) is drawn

### Supersedes or Recontextualizes
- (none in collection)

### Cited By (in Collection)
- [[Garcia_2004_DefeasibleLogicProgramming]] — cites Maher's earlier work on defeasible logic representations and implementations
- [[Antoniou_2007_DefeasibleReasoningSemanticWeb]] — cites Maher's defeasible logic work

### Conceptual Links (not citation-based)
**Defeasible logic compilation to Datalog:**
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — Strong. Diller grounds first-order ASPIC+ theories into Datalog programs for extension computation; Maher compiles defeasible logic D(1,1) into Datalog programs for defeasible reasoning. Both use Datalog as a compilation target for nonmonotonic reasoning, but from different source formalisms (ASPIC+ vs defeasible logic). Together they suggest a unified Datalog execution substrate for propstore's argumentation.
- [[Bozzato_2020_DatalogDefeasibleDLLite]] — Strong. Combines Datalog with defeasible reasoning in description logic context. Different approach (defeasible DL-Lite) but same intersection of Datalog and defeasible reasoning.
- [[Morris_2020_DefeasibleDisjunctiveDatalog]] — Strong. Extends defeasible Datalog to disjunctive rules. Directly builds on the same tradition of compiling defeasible reasoning into Datalog-based systems.

**Argumentation and structured reasoning:**
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Moderate. ASPIC+ with preferences; Maher's superiority relation on defeasible rules is a simpler preference mechanism. Caminada & Amgoud 2007 bridges these two traditions.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — Moderate. ASPIC+ constructs arguments from strict/defeasible rules, same rule types as Maher's defeasible logic but with different evaluation mechanism (extensions vs tagged proofs).
- [[Garcia_2004_DefeasibleLogicProgramming]] — Strong. DeLP is another approach to defeasible logic programming with argumentation-based semantics, contrasting with Maher's compilation approach.
- [[Pollock_1987_DefeasibleReasoning]] — Moderate. Pollock's defeasible reasoning is one of the formalisms Dung showed is a special case of argumentation; Maher's D(1,1) is another.
