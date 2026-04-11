---
title: "DR-Prolog: A System for Defeasible Reasoning with Rules and Ontologies on the Semantic Web"
authors:
  - Grigoris Antoniou
  - Antonis Bikakis
year: 2007
venue: IEEE Transactions on Knowledge and Data Engineering
doi_url: https://doi.org/10.1109/TKDE.2007.29
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:15:11Z"
---
## One-Sentence Summary

DR-Prolog is a Prolog-based implementation of defeasible logic that translates defeasible theories into logic programs under Well-Founded Semantics, integrates with RDF/RDFS/OWL ontologies, and supports configurable reasoning variants (ambiguity blocking vs. propagating, conflicting literals). *(p.1)*

## Problem Addressed

The Semantic Web requires nonmonotonic reasoning to handle dynamic knowledge (business rules, policies) alongside static ontological knowledge, but existing defeasible reasoning implementations either lacked Semantic Web integration, declarative semantics, or flexibility across reasoning variants. *(p.2-4)*

## Key Contributions

1. **Complete defeasible logic implementation** with strict/defeasible rules, priorities, classical negation, NAF simulation, ambiguity blocking/propagating, and conflicting literals *(p.3)*
2. **Translation to logic programs under Well-Founded Semantics** via a meta-program approach, with formal correctness guarantee: $p$ is defeasibly provable in $D$ iff $p$ is in the Well-Founded Model of $P(D)$ *(p.12)*
3. **Semantic Web integration** — RDF/RDFS/OWL ontologies translated to logical facts and rules, reasoning over combined ontological + defeasible knowledge *(p.14-17)*
4. **RuleML compatibility** — input/output in RuleML XML format for interoperability *(p.3, 18)*
5. **Performance evaluation** against Deimos and d-Prolog across structured benchmark theories *(p.19-24)*

## Methodology

The system translates a defeasible theory $D = (F, R, >)$ into a logic program $P(D)$ using a meta-program approach. The translation encodes facts, strict rules, defeasible rules, and superiority relations as Prolog facts, then applies a fixed meta-program that defines derivability. XSB Prolog's `sk_not` operator provides correct evaluation under Well-Founded Semantics. *(p.12-14)*

RDF/RDFS data is parsed via SWI-Prolog's RDF parser and transformed into logical facts. RDFS schema constructs (subClassOf, subPropertyOf, domain, range) become rules. OWL constructs (equivalentClass, equivalentProperty, sameIndividualAs, transitive/symmetric/functional/inverse properties, restrictions, collections) are translated to additional rules. *(p.14-17)*

## Key Equations

### Defeasible Theory Definition
A defeasible theory is a triple $D = (F, R, >)$ where $F$ is a finite set of facts, $R$ is a finite set of rules, and $>$ is a superiority relation on $R$ (acyclic, irreflexive). *(p.8)*

### Strict Rules
$$A \rightarrow p$$
Whenever premises $A$ hold, conclusion $p$ is indisputable (definite inference). *(p.8)*

### Defeasible Rules
$$A \Rightarrow p$$
Conclusion $p$ can be defeated by contrary evidence. *(p.8)*

### Translation to Logical Facts
For $D = (F, R, >)$: *(p.12)*
- $\text{fact}(p)$ for each $p \in F$
- $\text{strict}(r_i, p, [q_1, \ldots, q_n])$ for each rule $r: q_1, \ldots, q_n \rightarrow p \in R$
- $\text{defeasible}(r_i, p, [q_1, \ldots, q_n])$ for each rule $r: q_1, \ldots, q_n \Rightarrow p \in R$
- $\text{sup}(r, s)$ for each pair where $r > s$

### Ambiguity Blocking Metaprogram (core clauses)
*(p.13)*

```
c1: supportive_rule(Name,Head,Body) :- strict(Name,Head,Body).
c2: supportive_rule(Name,Head,Body) :- defeasible(Name,Head,Body).
c3: definitely(X) :- fact(X).
c4: definitely(X) :- strict(R,X,[Y1,...,Yn]), definitely(Y1),...,definitely(Yn).
c5: defeasibly(X) :- definitely(X).
c6: defeasibly(X) :- sk_not definitely(~X), supportive_rule(R,X,[Y1,...,Yn]),
                      defeasibly(Y1),...,defeasibly(Yn), sk_not overruled(R,X).
c7: overruled(R,X) :- supportive_rule(S,~X,[U1,...,Un]),
                       defeasibly(U1),...,defeasibly(Un), sk_not defeated(S,~X).
c8: defeated(S,X) :- sup(T,S), supportive_rule(T,~X,[U1,...,Un]),
                      defeasibly(U1),...,defeasibly(Un).
```

### Ambiguity Propagating Variant
Replaces `defeasibly` with `supported` in overruled clause: *(p.14)*

```
c7': overruled(R,X) :- supportive_rule(S,~X,[U1,...,Un]),
                        supported(U1),...,supported(Un), sk_not defeated(S,~X).
c5': supported(X) :- definitely(X).
c6': supported(X) :- sk_not definitely(~X), supportive_rule(R,X,[Y1,...,Yn]),
                      supported(Y1),...,supported(Yn), sk_not defeated(R,X).
```

### NAF Simulation
Each rule $r: L_1, \ldots, L_n, \neg M_1, \ldots, \neg M_k \Rightarrow L$ is replaced by: *(p.9-10)*
- $r: L_1, \ldots, L_n, \text{neg}(M_1), \ldots, \text{neg}(M_k) \Rightarrow L$
- $\Rightarrow \text{neg}(M_i)$ and $M_i \Rightarrow \neg\text{neg}(M_i)$ for each $i$

### Conflicting Literals
Given `conflict :: L, M`, augment the theory with cross-negation rules: *(p.11)*
- For all rules $r_i: q_1, \ldots, q_n \rightarrow M$, add $r_i: q_1, \ldots, q_n \rightarrow \neg L$
- For all rules $r_i: q_1, \ldots, q_n \rightarrow L$, add $r_i: q_1, \ldots, q_n \rightarrow \neg M$
- Same for defeasible rules ($\Rightarrow$)

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Facts | $F$ | set | - | finite | 8 | Ground literals |
| Rules | $R$ | set | - | finite | 8 | Strict ($\rightarrow$) or defeasible ($\Rightarrow$) |
| Superiority | $>$ | relation | - | acyclic | 8 | Irreflexive, on pairs of rules |
| XSB stack size | - | MB | 20 | - | 21 | Global + local stack |
| XSB heap size | - | MB | 100 | - | 21 | For meta-program approach |
| Max theory size | - | rules | ~20000 | - | 22 | Memory limit on test hardware |

## Methods & Implementation Details

### Architecture *(p.17-18)*
- **RDF & OWL Translator**: SWI-Prolog RDF parser transforms triples to Prolog facts *(p.14)*
- **DL Parser**: Validates defeasible logic syntax
- **RuleML Parser**: Parses extended RuleML DTD with `<def>` (defeasible rules) and `<superiority>` elements *(p.18)*
- **Logic Translator**: Converts validated theories to logic programs via meta-program *(p.12-13)*
- **Reasoning Engine**: XSB Prolog with `sk_not` for WFS evaluation *(p.13)*

### Two Translation Approaches *(p.12, 24)*
1. **Meta-program** (adopted): Supports variables, computes all derivable literals. Uses fixed clauses c1-c8 *(p.13)*
2. **Direct translation** (Antoniou & Maher 2002): Faster but propositional only, cannot compute all literals at once *(p.24)*

### OWL Translation Coverage *(p.15-17)*
Rules o1-o27 covering: equivalentClass, equivalentProperty, sameIndividualAs, TransitiveProperty, SymmetricProperty, InverseOf, FunctionalProperty, InverseFunctionalProperty, allValuesFrom restrictions, hasValue restrictions, intersectionOf, oneOf.

### Benchmark Theory Types *(p.19-20)*
- **chain(n)**: Linear chain of $n$ defeasible rules from one fact
- **circle(n)**: Circular chain of $n$ defeasible rules (tests loop handling)
- **levels(n)**: Cascade of $2n+1$ disputed conclusions with priorities
- **teams(n)**: Team-based attack/support structure (exponential in $n$)
- **tree(n,k)**: $k$-branching tree of depth $n$
- **dag(n,k)**: Directed acyclic graph, $k$-branching, depth $n$, literal reuse $k$ times

## Figures of Interest

- **Figure 1** *(p.17)*: DR-Prolog system architecture diagram
- **Figure 2** *(p.25)*: Tourism domain RDFS ontology
- **Figure 3** *(p.26)*: Travel ontology RDF instances
- **Figure 4** *(p.26)*: RDF advertisement expression
- **Figure 5** *(p.27)*: User requirements as defeasible rules with priorities
- **Table 1** *(p.20)*: Test theory size formulas
- **Table 2** *(p.22)*: Execution times for undisputed inferences (DR-Prolog vs Deimos vs d-Prolog)
- **Table 3** *(p.23)*: Execution times for disputed inferences
- **Table 4** *(p.24)*: Execution times for direct translation approach

## Results Summary

- DR-Prolog performance proportional to theory size for most benchmarks *(p.23)*
- Comparable to Deimos on disputed inferences; slightly slower on undisputed *(p.23)*
- d-Prolog fails on cyclic theories (infinite loops) and most disputed inferences *(p.22-23)*
- d-Prolog faster on simple undisputed chains due to direct strict rule execution *(p.22)*
- Direct translation approach faster but limited to propositional, cannot enumerate all derivable literals *(p.24)*
- Memory limitation: XSB default allocation constrains theory size to ~20000 rules *(p.22)*

## Limitations

- Meta-program approach slower than direct translation due to indirection *(p.24)*
- XSB memory constraints limit scalable theory size *(p.22)*
- OWL coverage partial — many OWL constructs cannot be captured by rule languages *(p.3)*
- No arithmetic capabilities in the rule language *(p.30)*
- Defeaters (a third rule type in full defeasible logic) not implemented *(p.8, implied)*
- No formal proof of correctness for the meta-program (relies on established results from Antoniou et al. 2006, Maher et al. 2001) *(p.12)*

## Arguments Against Prior Work

- **d-Prolog** (Covington 1997): Not declarative (no `sk_not`), propositional only, no Semantic Web integration, loops on cyclic theories *(p.28)*
- **Deimos** (Maher et al. 2001): Haskell-based, no Semantic Web integration, no RuleML, propositional, no conflicting literals, isolated system *(p.29)*
- **Delores** (Maher et al. 2001): Linear complexity but only ambiguity blocking, propositional, no variables, no conflicting literals *(p.29)*
- **DR-DEVICE** (Bassiliades 2004): Java/Jess, only ambiguity blocking, no RDFS/OWL support, no formal semantic grounding (uses metaprogram as guiding principle only) *(p.29)*
- **SweetJess** (Grosof et al. 2002): Jess-based courteous logic, only one reasoning variant, restricted by Jess limitations *(p.29-30)*

## Design Rationale

- **Well-Founded Semantics chosen** over Stable Model Semantics for low computational complexity *(p.12)*
- **Meta-program approach chosen** over direct translation for variable support and ability to compute all derivable literals, despite slower execution *(p.12, 24)*
- **XSB Prolog chosen** as reasoning engine because it natively supports WFS via tabled resolution and `sk_not` *(p.13)*
- **NAF simulation in object language** rather than meta-level to maintain modularity and avoid interaction with defeasible negation *(p.9-10)*

## Testable Properties

1. **Correctness**: $p$ defeasibly provable in $D$ iff $p$ in Well-Founded Model of $P(D)$ *(p.12)*
2. **NAF simulation equivalence**: Transformed theory without NAF produces same conclusions as original theory with NAF, restricted to original language *(p.10)*
3. **Conflicting literals expansion**: Given `conflict :: L, M`, deriving $L$ blocks derivation of $M$ and vice versa *(p.11)*
4. **Ambiguity blocking**: If $p$ is ambiguous, rules with $p$ in body are blocked from firing *(p.10)*
5. **Ambiguity propagating**: If $p$ is ambiguous, dependent literals also become ambiguous *(p.10)*
6. **Superiority resolution**: If $r_1 > r_2$ and both applicable with conflicting conclusions, $r_1$'s conclusion is derived *(p.8)*
7. **Definite inference monotonicity**: Strict rule chains are monotonic — adding defeasible rules cannot retract definitely provable conclusions *(p.8, 13)*
8. **Skeptical behavior**: No contradictory pair $\{p, \neg p\}$ can both be defeasibly provable *(p.7)*
9. **Performance scaling**: Execution time proportional to theory size for chain/tree/dag theories *(p.23)*

## Relevance to Project

**High relevance to propstore's argumentation layer.** The paper's defeasible logic formalization maps directly to propstore's defeasible reasoning needs:

- **Rule types map to ASPIC+ components**: DR-Prolog's strict rules correspond to ASPIC+ strict rules, defeasible rules to ASPIC+ defeasible rules. The superiority relation corresponds to rule preference ordering. *(p.8)*
- **Ambiguity handling is a render-time policy choice**: DR-Prolog supports both ambiguity blocking and propagating as switchable variants. This aligns with propstore's design of multiple render policies over the same corpus — the choice between blocking/propagating is a resolution strategy, not a storage decision. *(p.10-11)*
- **Conflicting literals generalize binary negation**: The `conflict :: L, M, ...` construct allows declaring mutual exclusivity beyond simple negation. This maps to propstore's contrariness/conflict declarations. *(p.11)*
- **Meta-program translation pattern**: The translation of defeasible theories to logic programs via meta-predicates (supportive_rule, definitely, defeasibly, overruled, defeated) provides a reference implementation pattern for propstore's argumentation evaluation. *(p.13-14)*
- **WFS vs. stable models tradeoff**: The choice of Well-Founded Semantics for computational tractability is relevant to propstore's extension computation strategy. *(p.12)*
- **NAF simulation technique**: The modular NAF elimination via auxiliary predicates could inform how propstore handles negation-as-failure in claim evaluation. *(p.9-10)*

## Open Questions

1. How do defeaters (blocking rules that don't support their own conclusion) interact with the meta-program? The paper omits them. *(p.8)*
2. What is the formal relationship between defeasible logic variants and ASPIC+ defeat types? Governatori et al. [2004] describe DL in argumentation-theoretic terms. *(p.9)*
3. Can the meta-program approach be extended to handle preferences over argument chains (as in ASPIC+) rather than just local rule priorities? *(p.7)*
4. How does the OWL translation interact with defeasible rules when ontological axioms conflict with defeasible conclusions? *(p.15-17)*

## Related Work

- Nute 1994, Antoniou et al. 2001 — defeasible logic foundations
- Maher et al. 2001, Antoniou & Maher 2002, Antoniou et al. 2006 — translation to logic programs
- Governatori et al. 2004 — argumentation-theoretic semantics for DL
- Maher 2002 — model-theoretic semantics for DL
- Covington 1997, Covington 2000 — d-Prolog implementation
- Bassiliades 2004 — DR-DEVICE (Jess-based)
- Grosof 1997 — Courteous Logic Programs
- Grosof et al. 2002 — SweetJess
- Horrocks et al. 2005 — SWRL
- Wagner 2003 — two types of negation for Semantic Web

## Collection Cross-References

### Already in Collection
- [[Reiter_1980_DefaultReasoning]] — cited as foundational default logic work, the alternative nonmonotonic framework that defeasible logic simplifies *(p.2)*
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — cited as another nonmonotonic approach (circumscription) that defeasible reasoning offers an alternative to *(p.2)*
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — foundational defeasible reasoning formalism; DR-Prolog implements a related but distinct defeasible logic tradition *(p.2)*
- [[Dung_1995_AcceptabilityArguments]] — the abstract argumentation framework foundation; Governatori et al. 2004 connect defeasible logic to Dung-style argumentation semantics *(p.9)*
- [[Garcia_2004_DefeasibleLogicProgramming]] — cited for deliberative stock market agents using defeasible logic programming *(p.2)*
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ strict/defeasible rule distinction directly parallels DR-Prolog's rule types
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — preference ordering in ASPIC+ relates to DR-Prolog's superiority relation
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — grounding rule-based argumentation in Datalog; DR-Prolog's translation to logic programs is an earlier approach to the same problem space

### New Leads (Not Yet in Collection)
- Governatori et al. 2004 — "Argumentation Semantics for Defeasible Logics" (J. Logic and Computation 14,5:675-702) — formally connects defeasible logic variants to argumentation-theoretic semantics
- Maher et al. 2001 — "Embedding Defeasible Logic into Logic Programs" — foundational meta-program translation correctness proofs
- Antoniou et al. 2006 — "Embedding Defeasible Logic into Logic Programming" (J. Logic Programming 41,1:45-57) — WFS correctness for defeasible logic translation

### Conceptual Links (not citation-based)
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — Both address defeasible reasoning but from different traditions: Simari-Loui use argument specificity for defeat, while Antoniou-Bikakis use explicit rule priorities. The superiority relation in DR-Prolog is a simpler mechanism than specificity-based preference.
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — Both translate rule-based defeasible reasoning into a tractable logic programming framework (Datalog vs. XSB/WFS). Diller grounds ASPIC+ rules into Datalog; Antoniou translates defeasible logic into Prolog meta-programs. Different formalisms, convergent implementation strategy.
- [[Verheij_2002_ExistenceMultiplicityExtensionsDialectical]] — Verheij's dialectical justification (justifiable/defeatable/ambiguous) maps closely to DR-Prolog's definitely/defeasibly/overruled proof categories.

### Cited By (in Collection)
- (none found)
