---
title: "A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility"
authors: [Loris Bozzato, Thomas Eiter, Luciano Serafini]
year: 2020
institutions: [Fondazione Bruno Kessler, TU Wien]
tags: [defeasible-reasoning, description-logics, datalog, DL-Lite, exceptions, knowledge-representation]
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:16:39Z"
---
# A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility

## Summary

This paper presents a Datalog translation for reasoning on DL-Lite_R knowledge bases extended with defeasible axioms (axioms that admit exceptions). The approach builds on the "justifiable exception" semantics from the authors' prior CKR (Contextualized Knowledge Repository) framework. The key contribution is providing a complete and correct materialization procedure for instance checking in DL-Lite_R with defeasibility, via translation to answer set programs. The paper also establishes complexity results: satisfiability is NLogSpace-complete (combined) and FO-rewritable (data), while instance checking is coNP-complete (combined) and coNP-hard (data). *(p.1)*

## Problem

Standard DL-Lite knowledge bases use strict concept inclusions (GCIs) that admit no exceptions. Real-world ontologies need defeasible axioms — rules that hold "typically" but can be overridden for specific individuals. The challenge is to integrate defeasibility into DL-Lite_R while: (1) maintaining a well-defined semantics, (2) providing a concrete reasoning procedure, and (3) characterizing computational complexity. Prior approaches either targeted more expressive DLs (losing tractability) or did not provide Datalog-based materialization. *(pp.1-2)*

## Contributions

1. **Defeasible Knowledge Base (DKB) definition** for DL-Lite_R with justifiable exceptions, adapted from the CKR framework *(p.4)*
2. **Complete Datalog translation** — a set of Datalog rules that compiles a DKB into an answer set program whose answer sets correspond exactly to justified DKB models *(pp.6-8)*
3. **Soundness and completeness proof** (Theorem 1) establishing correspondence between CAS-models and answer sets *(p.8)*
4. **Complexity analysis**: satisfiability is NLogSpace-complete/FO-rewritable; instance checking is coNP-complete/coNP-hard *(pp.9-10)*
5. **Correctness of the materialization procedure** for instance checking *(p.8)*

## Methodology

### DL-Lite_R Preliminaries *(p.2)*

The paper uses standard DL-Lite_R with:
- **NC**: set of atomic concepts
- **NR**: set of atomic roles  
- **NI**: set of individual constants
- **Concept expressions**: C ::= A | ∃R | ¬C where A ∈ NC, R is a role
- **GCIs** (General Concept Inclusions): C ⊑ D
- **Role inclusions**: R ⊑ S
- An ABox of assertions A(a), R(a,b)

A DL interpretation I = (Δ^I, ·^I) where Δ^I is a non-empty set and ·^I maps concepts/roles to extensions. Standard name assumption (UNA) is adopted. *(p.2)*

### Defeasible Knowledge Base (DKB) *(pp.3-4)*

**Definition 1**: A DKB K = ⟨C, D⟩ where:
- C is a classical DL-Lite_R knowledge base (TBox + ABox)
- D is a set of defeasible axioms (same syntactic form as GCIs but can be overridden)

**Example 1** (PhD student scenario): In a university, department members must teach at least a course. PhD students who are recognized as department members are not allowed to hold a course. This creates a conflict that defeasible axioms resolve. *(p.4)*

```
∃DocStudentOf ⊑ ¬(∃Course_C), DeptMember ⊑ ∃(∃TeachCourse),
PhdMember ⊑ DeptMember, PhdMember ⊑ ¬(∃TeachCourse),
ProfLicence(alice), PhdMember(bob)
```

### CAS-Interpretations and Clashing Assumptions *(pp.4-5)*

**Definition 4 (CAS-interpretation)**: I_CAS = ⟨I, Σ⟩ where I is a DL interpretation and Σ is a set of clashing assumptions.

A **clashing assumption** (α, e) is an axiom-element pair such that:
- α is an instantiation for an axiom α ∈ D
- (α, e) is a clashing set if it consists of ABox assertions over D and negated ABox assertions of ⟨C⟩ such that B_I(Σ) is unsatisfiable

**Definition 5 (CAS-model)**: Given a DKB K, a CAS-interpretation I_CAS = ⟨I, Σ⟩ is a CAS-model if the following hold:
- (i) I is a model of C ∪ D_Σ (D minus the excepted axioms)
- (ii) for every (α, e) ∈ Σ, element e ∈ Δ, with all required role assertions
- (iii) for every D(e) ∈ E, clashing with C, with proper grounding
- (iv) Σ is non-redundant *(p.5)*

Key property: In DKB models, clashing assumptions are non-redundant (in absence of reflexivity, no spurious properties occur). *(p.5)*

### Datalog Translation *(pp.5-7)*

**Section 4** presents the core technical contribution. The translation P(K) consists of five categories of Datalog rules:

1. **DL-Lite_R input and output rules (I_in, I_out)**: translate axioms to Datalog facts encoding the TBox, ABox, and defeasible axioms *(p.6)*

2. **Axiom deduction rules (Σ_d)**: standard DL-Lite_R completion rules for subsumption, role inheritance, and existential introduction. For existentials, auxiliary "unnamed" individuals `nom` are introduced *(p.6)*

3. **Overriding rules (Σ_ov)**: define when a defeasible axiom's application can be overridden — i.e., when clashing conditions for recognizing an exceptional instance are met. For axioms of form B ⊑ C̃, the translation introduces rules checking negative information *(p.7)*

4. **Defeasible axiom input rules (Σ_def)**: translate defeasible axioms (D) to input facts, marking axioms as "defeasible" with a predicate that conditions application on non-exception status. Key rule pattern:
   ```
   instd(x, a, c) :- not_d_appl(x, a, c), d(c), all_inst(x, c)
   ```
   where `all_inst` checks universal applicability and `not_d_appl` ensures the axiom is not overridden *(p.6)*

5. **Defeasible application rules (Σ_appl)**: apply defeasible axioms only to instances that have not been recognized as exceptional. Uses answer-set negation (NAF) *(p.7)*

**Translation process** *(p.7)*:
Given a DKB K in DL-Lite_R normal form, program P(K) is computed by:
1. Translating all axioms to input/output predicates
2. Adding deduction rules for subsumption closure
3. Adding overriding/clashing rules
4. Adding defeasible application rules

### Correctness *(pp.7-8)*

**Proposition 1**: For every justified clashing assumption σ, the interpretation S = I(Σ_j) is an answer set of P(K); and conversely, every answer set of P(K) is of the form S = I(Σ_j) where Σ_j is a (maximal) justified clashing assumption set for C. *(p.8)*

**Theorem 1**: Let K be a DKB in DL-Lite_R normal form, and let α ∈ L_C such that K(α) is defined. Then K ⊨ α iff P(K) ⊨_s α. This establishes soundness and completeness of the Datalog translation. *(p.8)*

## Key Equations and Formalisms

### DL-Lite_R Concept Expressions *(p.2)*

```
C ::= A | ∃R           (1) — left-side concept
D ::= A | ¬A | ∃R | ¬∃R   (2) — right-side concept
```

### Normal Form Translation *(p.3)*

A signature Σ = (P, C) of a finite set C of constants and a finite set P of predicates. Answer set programs use NAF (negation as failure). A literal is either a positive literal p(...) or a strong negation ¬p(...). *(p.3)*

### CAS-model Satisfaction *(p.5)*

For a DKB K = ⟨C, D⟩, CAS-interpretation I_CAS = ⟨I, Σ⟩:
- NI-congruent: a^I = a for every a ∈ NI
- D_Σ = D \ {α ∈ D | (α,e) ∈ Σ for some e} — defeasible axioms minus exceptions

### Datalog Rule Patterns *(pp.6-7)*

**Input translation** (for concept inclusion A ⊑ B):
```
triple(x, a, c) :- supg(c, x, a), inst(x, c)
```

**Overriding rule** (for defeasible B ⊑ C̃):
```
instd(x, a, c) :- not d_appl(x, a, c), d(c), all_inst(x, c)
```

**Defeasible application**:
```
d_appl(x, a, c) :- clashing(x, a, c), not exc(x, a, c)
```

## Parameters / Constants Table

| Symbol | Meaning | Domain |
|--------|---------|--------|
| K = ⟨C, D⟩ | Defeasible knowledge base | TBox+ABox + defeasible axioms |
| C | Classical DL-Lite_R KB | TBox ∪ ABox |
| D | Set of defeasible axioms | Subset of GCI syntax |
| I_CAS = ⟨I, Σ⟩ | CAS-interpretation | DL interpretation + clashing assumptions |
| Σ | Set of clashing assumptions | Pairs (α, e) |
| P(K) | Datalog translation program | Answer set program |
| nom | Auxiliary unnamed individual | For existential axioms |
| NC, NR, NI | Atomic concepts, roles, individuals | Signature components |

## Implementation Details

### Translation Architecture *(pp.5-7)*

The translation compiles a DKB into a standard answer set program (ASP). Implementation would require:

1. **Parser** for DL-Lite_R normal form axioms
2. **Rule generator** for each of the 5 rule categories
3. **ASP solver** (e.g., clingo/DLV) as the reasoning backend
4. **Skolem function generator** for existential axioms (`nom` individuals)

### Key Design Decision: Negative Reasoning *(p.6)*

The paper notes that DL-Lite axioms allow negative reasoning directly in the encoding. The treatment of negative information is "directly encoded in clashing sets" rather than requiring separate closed-world reasoning. This is possible because DL-Lite_R's limited expressiveness allows negative literals to be handled through Datalog negation-as-failure. *(p.6)*

### Existential Handling *(p.6)*

For every axiom of kind α = A ⊑ ∃R, an auxiliary abstract individual `nom^α` is added to represent the class of all R-successors introduced by α. This is the standard Skolemization approach for DL-Lite existentials. *(p.6)*

## Figures and Examples

**Example 1** *(p.4)*: University scenario — PhD students vs. department members and teaching obligations. Shows how defeasible axioms allow exceptions: PhD students are department members but excepted from the teaching requirement.

**Example 2** *(p.5)*: Extension of Example 1 showing CAS-model construction. The justified CAS-model recognizes bob as an exception to the teaching requirement since he is a PhD student, while alice (with ProfLicence) retains the obligation.

## Results

### Complexity Results *(pp.9-10)*

**Theorem 2** *(p.9)*: For DL-Lite_R DKB K, model satisfiability of K is:
- **Combined complexity**: NLogSpace-complete
- **Data complexity**: FO-rewritable (first-order rewritable)

This matches classical DL-Lite_R satisfiability — defeasibility adds no overhead for satisfiability checking.

**Theorem 3** *(p.10)*: For DKB K and axiom α, deciding K ⊨ α is:
- **Combined complexity**: coNP-complete (for instance checking with data complexity)
- **Data complexity**: coNP-hard

The coNP-hardness comes from the need to check all possible clashing assumption sets. Proof via reduction from propositional CDNF satisfiability. *(p.10)*

### Complexity Mitigation *(p.10)*

The paper discusses typing of axioms to reduce complexity:
- Typing each argument x of an axiom to restrict whether x is an individual from the DKB type (i.e., a named individual) or an unnamed individual from Skolemization
- With typing, certain defeasible axioms D(α,e) with restrictions on α have no existential restrictions, and satisfiability can be checked more efficiently *(p.10)*

## Limitations

1. **Restricted to DL-Lite_R**: Does not handle more expressive DLs like ALC or SHIQ *(p.10)*
2. **No reflexivity axioms**: The framework assumes no reflexive roles; reflexive properties would complicate clashing assumption reasoning *(p.5)*
3. **coNP data complexity for instance checking**: While satisfiability is tractable, instance checking with defeasible axioms is coNP-hard — a significant jump from classical DL-Lite_R's polynomial data complexity *(p.10)*
4. **Single-context only**: The paper does not address the full CKR framework with multiple hierarchical contexts; that is future work *(p.11)*
5. **No implementation evaluation**: The paper provides the theoretical framework but no empirical evaluation of the Datalog translation's performance *(p.11)*

## Arguments Against Prior Work

- **Against Bonatti et al. [2,3]**: Their "overriding semantics" for defeasible DLs uses a different formalization based on circumscription and preference. The authors argue their "justifiable exception" approach is more naturally aligned with DL-Lite's limited expressiveness and provides a direct Datalog encoding. *(p.11)*
- **Against Casini et al. [14]**: Their "rational closure" approach for DLs, while well-studied for the EL family, does not directly provide a materialization-based reasoning procedure. *(p.11)*
- **Against Pensel & Turhan [23]**: Their work on defeasible EL_⊥ uses rational/relevant semantics, which is different from the justifiable exception semantics used here. *(p.11)*

## Design Rationale

The paper adopts the "justifiable exception" paradigm (from the CKR framework) rather than rational closure or circumscription because:

1. **Direct Datalog encoding**: The justifiable exception semantics maps naturally to answer set programming, enabling practical materialization *(p.6)*
2. **Preservation of DL-Lite tractability**: Satisfiability remains NLogSpace-complete, matching classical DL-Lite_R *(p.9)*
3. **Negative reasoning without CWA**: DL-Lite_R's limited form allows negative literals to be directly encoded in clashing sets, avoiding the need for separate closed-world assumption reasoning *(p.6)*
4. **Compatibility with CKR**: The approach extends naturally to contextualized knowledge repositories with hierarchies *(p.11)*

## Testable Properties

1. **Soundness**: Every answer set of P(K) corresponds to a justified CAS-model of K (Theorem 1) *(p.8)*
2. **Completeness**: Every justified CAS-model of K has a corresponding answer set (Theorem 1) *(p.8)*
3. **Satisfiability preservation**: K is satisfiable iff P(K) has at least one answer set *(p.8)*
4. **Non-redundancy of clashing assumptions**: In any DKB model, clashing assumptions must be non-redundant — no subset of Σ suffices *(p.5)*
5. **Complexity bounds**: Satisfiability in NLogSpace; instance checking in coNP *(pp.9-10)*
6. **Exception inheritance**: If a is an instance of a defeasible axiom's antecedent AND a clashing set exists, a is excepted from the axiom *(p.5)*
7. **Monotonicity of classical part**: Adding classical axioms to C cannot remove exceptions (exceptions only depend on clashing with C) *(p.5)*

## Relevance to propstore

### Direct Relevance

1. **Defeasible reasoning as a first-class concept**: propstore's argumentation layer handles conflicting claims and evidence accumulation. This paper provides a formal semantics for "typical but overridable" assertions — directly relevant to propstore's non-commitment discipline where multiple rival normalizations must coexist. *(p.1)*

2. **Clashing assumptions as a formal model for exceptions**: The CAS-interpretation framework (interpretation + set of clashing assumptions) maps to propstore's model of holding multiple competing stances without forcing resolution. Clashing assumptions are essentially "recognized exceptions" — stored with provenance. *(pp.4-5)*

3. **Datalog as reasoning substrate**: The translation to answer set programs is relevant to propstore's ASPIC+ bridge, which already translates claims/stances to formal argument types. The Datalog rules here could inform how defeasible concept inclusions are handled in the argumentation layer. *(pp.5-7)*

4. **Complexity characterization**: The coNP-hardness of instance checking with defeasible axioms is important for propstore's render-time resolution strategy — it means that defeasible reasoning over DL-Lite ontologies is inherently harder than classical reasoning, which affects what can be computed eagerly vs. lazily. *(pp.9-10)*

### Indirect Relevance

5. **Exception semantics for concept merging**: When propstore performs vocabulary reconciliation or concept merging, defeasible axioms could model "typically A ⊑ B, but with exceptions." This is richer than simple subsumption. *(p.4)*

6. **Non-commitment at the ontological level**: The DKB model allows a knowledge base to hold both "PhDStudents are DeptMembers" and "PhDStudents are excepted from teaching" without resolving the conflict at storage time — only at query/render time. This mirrors propstore's core design principle. *(p.4)*

## Open Questions

1. How does the CKR extension with hierarchical contexts (mentioned as future work) interact with propstore's context formalization (McCarthy 1993 `ist(c, p)`)? *(p.11)*
2. Can the Datalog translation be integrated with propstore's existing ASPIC+ bridge, or does it require a separate reasoning pathway? *(p.7)*
3. The coNP hardness for instance checking — does this affect propstore's render-time performance for defeasible concept queries? *(p.10)*
4. How do multiple defeasible axiom sets interact when merging knowledge from different sources (the "multiple nuclear elements" question)? *(p.10)*

## Related Work (from paper)

- Baader et al. 2003 — Description Logic Handbook [1]
- Bonatti et al. 2015, 2011 — Overriding semantics and defeasible inclusions in DLs [2,3]
- Bonatti et al. 2006 — DLs with circumscription [4]
- Bozzato et al. 2014, 2018 — CKR with justifiable exceptions [5,6]
- Bozzato et al. 2019 — Note on reasoning on DL-Lite_R with defeasibility (precursor) [7]
- Bozzato et al. 2012 — Effective tableaux for CKR [8]
- Bozzato & Serafini 2013 — Materialization calculus for contexts in Semantic Web [9]
- Britz et al. 2008 — Introducing role defeasibility in DLs [11]
- Casini & Straccia 2010 — Rational closure for DLs [14]
- Eiter et al. 2008 — Combining ASP with DLs for the Semantic Web [15]
- Giordano et al. 2013 — Non-monotonic DL for reasoning about typicality [18]
- Pensel & Turhan 2018 — Defeasible EL_⊥ [23]

## Collection Cross-References

### Already in Collection
- (none — no cited papers are currently in the collection)

### New Leads (Not Yet in Collection)
- Bonatti, Faella, Petrova, Sauro (2015) — "A new semantics for overriding in description logics" — alternative defeasibility semantics via circumscription-based overriding, relevant for comparing exception mechanisms
- Casini, Straccia (2010) — "Rational closure for defeasible description logics" — rational closure approach as alternative to justifiable exceptions
- Eiter, Ianni, Lukasiewicz, Schindlauer, Tompits (2008) — "Combining ASP with DLs for the Semantic Web" — ASP+DL integration for semantic web reasoning
- Giordano, Gliozzi, Olivetti, Pozzato (2013) — "A non-monotonic description logic for reasoning about typicality" — typicality-based defeasibility in DLs
- Pensel, Turhan (2018) — "Reasoning in the defeasible description logic EL_bot" — defeasible reasoning under rational/relevant semantics

### Conceptual Links (not citation-based)
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — Both papers use Datalog as a formal reasoning substrate. Diller grounds ASPIC+ argumentation in Datalog; Bozzato translates defeasible DL-Lite reasoning into Datalog/ASP. The two approaches could be composed: Bozzato's DKB translation generates defeasible knowledge, Diller's grounding could build arguments over it.
- [[McCarthy_1993_FormalizingContext]] — Bozzato's CKR framework (which this paper simplifies for DL-Lite) is built on contextualized knowledge repositories. McCarthy's ist(c,p) formalization of contexts is the theoretical ancestor. The CKR hierarchy of contexts directly inherits from McCarthy's lifting rules.
- [[Ghidini_2001_LocalModelsSemanticsContextual]] — CKR's multi-context architecture draws on local models semantics. Ghidini's bridge rules between local theories map to CKR's inter-context knowledge flow, which Bozzato's defeasible axioms can override.
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — This paper explicitly argues against circumscription-based approaches to defeasibility (Bonatti et al. 2006 use circumscription for DL defeasibility). McCarthy's circumscription is the formal alternative that Bozzato's "justifiable exception" semantics replaces.
