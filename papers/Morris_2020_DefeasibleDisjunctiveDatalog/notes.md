---
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:16:45Z"
---
# Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog

Morris, M., Ross, T., and Meyer, T. (2020). *Algorithmic definitions for KLM-style defeasible disjunctive Datalog*. South African Computer Journal, 32(2), 141-170. DOI: 10.18489/sacj.v32i2.846

**Tags:** #defeasible-reasoning #datalog #KLM #rational-closure #lexicographic-closure #relevant-closure #nonmonotonic-reasoning

---

## Summary

This paper extends the KLM (Kraus, Lehmann, Magidor) approach to defeasible reasoning from propositional logic into Disjunctive Datalog. The authors provide algorithmic definitions for three forms of defeasible entailment -- Rational Closure, Lexicographic Closure, and Relevant Closure -- adapted to handle disjunction, variables, and constants in the Datalog setting. They prove that all three algorithms satisfy the KLM properties and are LM-rational, while showing through counter-examples that Relevant Closure does not satisfy Or, CM, or RM (only Rational Closure and Lexicographic Closure are fully LM-rational in the propositional-level sense). *(p.1)*

---

## Problem

Classical Datalog uses classical logical entailment, which is monotonic -- adding new information cannot retract previously derived conclusions. This prevents handling defeasible implications (defaults with exceptions). While defeasible reasoning has been extensively studied in propositional logic via the KLM framework, extending it to Datalog requires addressing: (1) the richer syntax of Datalog including disjunction, variables, and constants; (2) interactions between variables and constants that propositional logic does not capture; and (3) the fact that Datalog's syntax restricts which KLM properties can be expressed. *(pp.1-2, 7-8)*

---

## Contributions

1. **BaseRankDatalog algorithm** -- adapts the propositional BaseRankProp algorithm to rank defeasible Datalog knowledge bases, handling Horn clauses with Herbrand semantics. *(p.9)*
2. **RationalClosureDatalog algorithm** -- adapts Rational Closure to Datalog, using BaseRankDatalog for ranking and classical Datalog entailment checks. Proven LM-rational. *(pp.9-10)*
3. **RelevantClosureDatalog algorithm** -- adapts Relevant Closure to Datalog with relevance-based partitioning. Proven LM-rational but shown NOT to satisfy Or, CM, or RM via counter-examples. *(pp.13-14)*
4. **LexicographicClosureDatalog algorithm** -- adapts Lexicographic Closure to Datalog using SubsetRankDatalog for finer-grained ranking. Proven LM-rational. *(pp.15-18)*
5. **Formal proofs** that Rational Closure and Lexicographic Closure satisfy all expressible KLM properties (Ref, LLE, And, Or, RW, CM, RM) for Datalog. *(pp.20-29)*
6. **Counter-examples** showing Relevant Closure fails Or, CM, and RM in Datalog. *(pp.25-29)*
7. **Extension of Datalog syntax** to Datalog+ which introduces compound terms (A, B, ...) allowing conjunction in rule heads, enabling expression of defeasible implications with conjunctive molecules. *(pp.8-9)*

---

## Methodology

### Approach
The paper follows the established methodology from Casini et al. (2014) for extending propositional defeasible entailment algorithms to richer logics. The key insight is that defeasible entailment in propositional logic can be computed via a ranking procedure (BaseRankProp) followed by iterative removal of ranked levels until a classical entailment check succeeds. The authors adapt each sub-algorithm to handle Datalog-specific features. *(p.2)*

### Datalog Syntax and Semantics
- **Disjunctive Datalog** (Datalog^v): function-free Horn clauses with disjunction in heads. Rules have the form `l_1, ..., l_n -> l_{n+1}, ..., l_m` (body -> head). *(p.5)*
- **Herbrand Base** (BP^Gamma): the set of all ground facts constructible from the symbols in a Datalog program Gamma. *(p.6)*
- **Herbrand interpretation**: a subset tau of BP^Gamma. A rule alpha is true for tau iff for every grounding substitution theta, if all body literals hold in tau, at least one head literal holds. *(p.6)*
- **Entailment**: K |= alpha iff alpha is true in every Herbrand model of K. *(p.6)*
- **Molecules**: shorthand for combinations of literals. A disjunctive molecule alpha^v = l_1 v ... v l_k. A conjunctive molecule alpha^c = l_1 ^ ... ^ l_k. A molecule is either disjunctive or conjunctive. *(pp.6-7)*
- **Defeasible rules**: `alpha |~ beta` ("alpha typically entails beta"), where alpha, beta are molecules. *(pp.7-8)*
- **Datalog+**: extension adding compound terms A, B, ... (conjunctions/disjunctions of literals) to represent defeasible implications more expressively. A fact in Datalog+ is a compound; rules have the form A_1, ..., A_n -> B_1, ..., B_m. *(pp.8-9)*

### Defeasible Entailment (KLM Framework)
The KLM approach (Kraus et al., 1990) defines defeasible entailment via rationality properties. A knowledge base K = (D, C) where D is defeasible rules and C is classical rules. K |~_def alpha |~ beta means "from K, we can defeasibly conclude that alpha typically entails beta." *(p.3)*

**KLM properties** expressed in Datalog+ *(p.9)*:
- **(Ref)**: K |~ alpha |~ alpha *(reflexivity)*
- **(LLE)**: If K |= alpha <-> beta and K |~ alpha |~ gamma, then K |~ beta |~ gamma *(left logical equivalence)*
- **(And)**: If K |~ alpha |~ beta and K |~ alpha |~ gamma, then K |~ alpha |~ beta ^ gamma *(conjunction)*
- **(Or)**: If K |~ alpha |~ gamma and K |~ beta |~ gamma, then K |~ alpha v beta |~ gamma *(disjunction)*
- **(RW)**: If K |~ alpha |~ beta and K |= beta -> gamma, then K |~ alpha |~ gamma *(right weakening)*
- **(CM)**: If K |~ alpha |~ beta and K |~ alpha |~ gamma, then K |~ alpha ^ beta |~ gamma *(cautious monotonicity)*
- **(RM)**: If K |~ alpha |~ gamma and K |~/~ alpha |~ -beta, then K |~ alpha ^ beta |~ gamma *(rational monotonicity)*

---

## Algorithms

### Algorithm 1: RationalClosureProp *(p.4)*
**Input:** Defeasible propositional KB K, defeasible implication alpha |~ beta
**Output:** true/false
Uses BaseRankProp to rank K, then iteratively removes lowest-ranked levels while checking if R_inf U R |= -alpha. If at any level R_inf U R |/= -alpha, checks if R_inf U R |= alpha -> beta.

### Algorithm 2: BaseRankProp *(p.5)*
**Input:** Defeasible propositional KB K
**Output:** Ordered tuple (R_0, ..., R_{n-1}, R_inf, n)
Iteratively partitions defeasible rules by exceptionality: E_0 = K-tilde (materialized defeasible rules), then E_{i+1} = {alpha -> beta in E_i | E_i |= -alpha}. Exceptional rules move to higher ranks.

### Algorithm 3: BaseRankDatalog *(p.9)*
Same as BaseRankProp but adapted for Datalog. Uses classical Datalog entailment. E_0 includes materialized defeasible rules. Exceptionality check: {alpha -> beta in E_i | E_i U C |= alpha -> bot} where bot (falsum) is represented via the ⊥ literal. *(p.10)*

### Algorithm 4: RationalClosureDatalog *(p.10)*
**Input:** Defeasible Datalog KB D, classical Datalog KB C, defeasible rule alpha |~ beta
**Output:** true/false
Uses BaseRankDatalog for ranking, then iteratively removes levels checking R_inf U R U R' |= alpha -> bot. When the antecedent is no longer exceptional, checks entailment of the full rule.

### Algorithm 5: RelevantClosureProp *(p.13)*
**Input:** Defeasible propositional KB K, defeasible implication alpha |~ beta, partition R, R-bar of K
**Output:** true/false
Same as RationalClosureProp but only removes "relevant" statements from each level -- those in the justification set of -alpha.

### Algorithm 6: RelevantClosureDatalog *(p.14)*
Adaptation of RelevantClosureProp to Datalog.

### Algorithm 7: SubsetRankProp *(p.16)*
**Input:** Defeasible propositional KB K
**Output:** Extended ranking with subset-based refinement
For each level in BaseRankProp output, generates all possible subsets of size k (from 1 to |B_i|), forms disjunctions D_{i,j}, applies RNF (Rule Normal Form), creating a finer ranking.

### Algorithm 8: SubsetRankDatalog *(p.17)*
Adaptation of SubsetRankProp to Datalog. Uses RNF(Gamma) which takes a Datalog+ statement and converts to a set of Datalog^v rules via CNF conversion:
1. Compute CNF(Gamma)
2. Convert to conjunction of clauses (alpha_i^^ -> beta_i^v)
3. Return set of clauses *(p.17)*

### Algorithm 9: LexicographicClosureDatalog (implied, p.18)
Uses SubsetRankDatalog ranking, otherwise same structure as RationalClosureDatalog. Proven LM-rational (Proposition 3). *(p.18)*

---

## Key Definitions

### Exceptionality *(p.8-9)*
A molecule alpha is **exceptional** w.r.t. a knowledge base K if K |= alpha -> bot (i.e., alpha is classically inconsistent with K). A defeasible rule alpha |~ beta is exceptional w.r.t. K if alpha is exceptional w.r.t. K.

### Relevance *(pp.13-14)*
- **Definition 1**: alpha is exceptional for K if K |= alpha -> bot. *(p.14)*
- **Definition 2**: J_K^f is the set of all justifications -- minimal subsets J of K such that J |= f (i.e., J is a justification of f w.r.t. K). *(p.14)*
- **Definition 3 (Basic Relevant Closure)**: alpha |~ beta is in the Basic Relevant Closure of K if it is in the Relevant Closure of K w.r.t. J_K(alpha). *(p.14)*
- **Definition 4 (Minimal Relevant Closure)**: Uses J_min^K(f) = {J in J_K(f) | r(alpha) <= r(gamma) for every gamma in J, for every J' in J_K(f)}. *(p.14)*

### LM-Rationality *(p.3)*
An algorithm for defeasible entailment is **LM-rational** if it satisfies all KLM properties. Lehmann and Magidor (1992) argued this is the minimum standard for rational defeasible entailment.

### Herbrand Interpretation *(p.6)*
tau is a **Herbrand model** of a set of Horn clauses X iff every clause in X is true in tau under the standard substitution semantics. K |= alpha iff every Herbrand model of K is also a model of alpha.

---

## Parameters Table

| Parameter | Description | Source |
|-----------|-------------|--------|
| K = (D, C) | Knowledge base: D = defeasible rules, C = classical rules | *(p.8)* |
| R_0, ..., R_{n-1} | Ranked levels from BaseRank (R_0 = least exceptional) | *(p.5, 9)* |
| R_inf | Infinite rank level (classical/maximally exceptional rules) | *(p.5, 9)* |
| n | Number of finite ranks | *(p.5, 9)* |
| BP^Gamma | Herbrand Base of program Gamma | *(p.6)* |
| J_K(f) | Set of all justifications of f w.r.t. K | *(p.14)* |
| J_min^K(f) | Minimal justifications (by rank) | *(p.14)* |
| D_{i,j} | Subset-derived disjunctive statements for Lexicographic ranking | *(p.17)* |
| RNF(Gamma) | Rule Normal Form -- converts Datalog+ to Datalog^v rules | *(p.17)* |
| CNF(Gamma) | Conjunctive Normal Form of a Datalog+ statement | *(p.17)* |

---

## Implementation Details

### BaseRankDatalog Procedure *(p.9-10)*
1. Start with E_0 = materialized defeasible rules union classical rules C (as Datalog^v clauses)
2. At each iteration, identify exceptional rules: those alpha -> beta where E_i U C |= alpha -> bot
3. Move exceptional rules to next rank R_i
4. Repeat until fixed point
5. Remaining rules go to R_inf (infinite rank)
6. Proposition 1: BaseRankDatalog checks exceptionality using entailment check E_i U C |= alpha -> bot, replacing the propositional check with Datalog entailment *(p.10)*

### RationalClosureDatalog Procedure *(p.10)*
1. Compute BaseRankDatalog ranking
2. Set R = union of all finite ranks, R' = classical rules
3. While R_inf U R U R' |= alpha -> bot and R is non-empty:
   - Remove lowest rank from R
4. Check if R_inf U R U R' |= alpha -> beta
5. Key difference from propositional: uses Herbrand semantics, so need to handle ground instantiation

### Interaction Between Variables and Constants *(p.11)*
- KLM properties do NOT fully capture variable/constant interactions in Datalog
- Example 5: Birds fly, Tweety is non-flying bird, Chirpy is a bird
  - BaseRankDatalog puts all statements at same level (inconsistent KB)
  - Algorithm cannot distinguish individual exceptions from universal rules
  - This is a known limitation; the scope of this paper is LM-rationality, not full variable/constant reasoning *(p.11)*

### RelevantClosureDatalog *(pp.12-14)*
- Motivation: Rational Closure is too aggressive -- removes entire levels even when only some statements conflict
- Relevant Closure only removes statements whose justification sets are relevant to the antecedent
- Partitions statements into relevant (R) and irrelevant (R-bar) sets
- Only removes from R at each iteration
- **Key finding**: Minimal Relevant Closure satisfies LLE but does NOT satisfy Or, CM, or RM in Datalog *(p.25-29)*

### LexicographicClosureDatalog *(pp.15-18)*
- Motivation: Lexicographic Closure considers all possible subsets of statements at each level
- SubsetRankDatalog generates finer rankings by considering all k-subsets of each level B_i
- For each k-subset, forms disjunction D_{i,j} of conjunctions of subset elements
- Converts to RNF (Rule Normal Form) via CNF transformation
- RNF steps: (1) compute CNF, (2) convert to conjunction of clauses alpha_i^^ -> beta_i^v, (3) convert to set of clauses *(p.17)*
- Result: finer ranking allows more statements to survive removal, producing more conclusions

### Proof Strategy for LM-Rationality *(pp.20-29)*
- Proofs for Rational Closure: directly show each KLM property holds by case analysis on the ranking and entailment checks
- Proofs for Lexicographic Closure: show that the proofs for Rational Closure by RationalClosureDatalog are independent of the ranking produced by BaseRankDatalog, so the SubsetRankDatalog ranking works identically *(p.18)*
- Proofs for Relevant Closure: counter-examples using lattice-structured knowledge bases *(pp.25-29)*

---

## Figures

- **Figure 1** *(p.5)*: Ranking of a propositional knowledge base K with BaseRankProp. Shows R_0, R_1, R_inf levels.
- **Figure 2** *(p.12)*: Desired ranking of a Datalog knowledge base K for Example 5 (birds/Tweety/Chirpy). Shows how variable/constant interaction causes all rules to land at same level.
- **Figure 3** *(p.13)*: Ranking for Example 6 (people/students/taxes). Shows how Relevant Closure partitions differently than Rational Closure.
- **Figure 4** *(p.16)*: Base ranking of propositional KB for Lexicographic Closure example.
- **Figure 5** *(p.16)*: SubsetRanking of propositional KB K -- shows the finer ranking with B_{i,j} levels.
- **Figure 6** *(p.26)*: Lattice representing K for the Or counter-example.
- **Figure 7** *(p.26)*: Ranking of K for Or counter-example.
- **Figure 8** *(p.27)*: Lattice representing K for CM counter-example.
- **Figure 9** *(p.28)*: Ranking of K for CM counter-example.

---

## Results

1. **Rational Closure for Datalog is LM-rational** (Proposition 2, p.10). Proof in Appendix A. *(pp.20-25)*
2. **Lexicographic Closure for Datalog is LM-rational** (Proposition 3, p.18). Proofs reuse Rational Closure proofs since SubsetRankDatalog ranking is independent. *(p.18, Appendix B)*
3. **Relevant Closure for Datalog is LM-rational** but does NOT satisfy Or, CM, or RM when considering the full set of KLM properties. The paper provides explicit counter-examples for each. *(pp.25-29, Appendix C)*
4. **Rational Closure for Datalog was already proven LM-rational** by Casini et al. (2019) -- this paper provides an independent proof. *(p.10)*
5. **The KLM properties are not fully expressive** for Datalog due to variable/constant interactions -- they cannot capture rules involving mixing of individual constants and universal variables. This is explicitly out of scope. *(p.11)*

---

## Limitations

1. **Variable/constant interactions**: The KLM properties do not capture interactions between variables and constants in rules. The algorithms cannot distinguish individual exceptions (e.g., "Tweety doesn't fly") from universal defaults (e.g., "Birds fly") when they interact. *(p.11)*
2. **No semantic definition**: The paper provides only algorithmic definitions, not model-theoretic semantic definitions of defeasible entailment for Datalog. *(p.18)*
3. **Relevant Closure limitations**: Does not satisfy Or, CM, or RM -- meaning it fails three of the seven KLM properties. This makes it strictly weaker than Rational or Lexicographic Closure. *(pp.25-29)*
4. **Minimal models not explored**: The paper does not explore computing defeasible entailment based on minimal Herbrand models (a standard Datalog technique). *(p.18)*
5. **Computational complexity**: No complexity analysis of the algorithms is provided. SubsetRankDatalog in particular requires generating all subsets of each rank level, which is exponential. *(p.17)*

---

## Arguments Against Prior Work

- **Against Casini et al. (2014)**: The propositional Relevant Closure definition, when adapted to Datalog, does not satisfy Or, CM, or RM. The authors provide explicit counter-examples. *(pp.25-29)*
- **Against the view that Relevant Closure is always preferable to Rational Closure**: While Relevant Closure is more fine-grained (retains more statements), it sacrifices fundamental rationality properties. *(p.14, pp.25-29)*
- **Extension of Morris et al. (2019)**: This paper extends the earlier workshop paper on defeasible disjunctive Datalog with full proofs and the addition of Lexicographic and Relevant Closure (the 2019 paper only covered Rational Closure). *(p.1)*

---

## Design Rationale

- **Why Disjunctive Datalog?** Standard (non-disjunctive) Datalog cannot express disjunction in rule heads. But many KLM properties (especially Or) require disjunction. The authors argue that restricting to non-disjunctive Datalog would mean some KLM properties "will never be covered by defeasible entailment algorithms for Disjunctive Datalog" -- so disjunction is necessary for completeness. *(p.8)*
- **Why LM-rationality as the benchmark?** Lehmann & Magidor (1992) established that an algorithm satisfying all KLM properties is the minimum standard for "rational" defeasible entailment. The authors adopt this as their evaluation criterion. *(p.3)*
- **Why Datalog+ syntax?** Standard Datalog syntax cannot express conjunction in rule heads. Datalog+ adds compound terms to allow expressing defeasible implications with conjunctive conclusions, which is needed for the And property. *(pp.8-9)*
- **Why three closure types?** Each represents a different trade-off between conservatism and expressiveness. Rational Closure is most conservative (removes entire levels), Relevant Closure is most targeted (removes only relevant statements), and Lexicographic Closure is in between (finer subset-based ranking). *(pp.4, 12, 15)*

---

## Testable Properties

1. **BaseRankDatalog terminates**: The algorithm must reach a fixed point where E_i = E_{i-1}, since each iteration strictly reduces the set of non-exceptional rules. *(p.9)*
2. **Rational Closure satisfies all 7 KLM properties**: Ref, LLE, And, Or, RW, CM, RM. Each can be tested with specific knowledge bases. *(p.9, Appendix A)*
3. **Lexicographic Closure satisfies all 7 KLM properties**: Same as Rational Closure. *(p.18, Appendix B)*
4. **Relevant Closure fails Or**: The counter-example in Appendix C.2 provides a specific knowledge base where K |~_RC a |~ e and K |~_RC g |~ e but K |~/~_RC a v g |~ e. *(pp.26-27)*
5. **Relevant Closure fails CM**: Counter-example in Appendix C.3. *(pp.27-28)*
6. **Relevant Closure fails RM**: Counter-example in Appendix C.4 (same as CM counter-example). *(p.29)*
7. **SubsetRankDatalog produces a refinement of BaseRankDatalog**: Every statement that is in R_i according to BaseRank must appear in some R_k according to SubsetRank, with the ordering preserved. *(p.17)*
8. **Rational Closure is more conservative than Lexicographic Closure**: Every defeasible implication entailed by Rational Closure must also be entailed by Lexicographic Closure (but not vice versa). *(p.15)*
9. **Entailment checks reduce to classical Datalog entailment**: The algorithms use classical entailment as a black box, so correctness depends on the classical entailment oracle being correct. *(throughout)*

---

## Relevance to propstore

### Direct Relevance
- **Defeasible reasoning in Datalog**: propstore's argumentation layer could benefit from Datalog-based defeasible reasoning as an alternative or complement to ASPIC+. The ranking-based approach (BaseRank) is conceptually similar to preference ordering in ASPIC+.
- **Multiple closure operators**: The three closure types (Rational, Lexicographic, Relevant) map naturally to propstore's render-time policy concept -- different closure operators could be different render policies over the same knowledge base.
- **Non-commitment discipline**: The paper's approach of computing entailment at query time (rather than materializing conclusions) aligns with propstore's lazy-until-rendering principle.

### Specific Connections
- **KLM properties as formal tests**: The seven KLM properties provide testable invariants for any defeasible reasoning system, including propstore's argumentation layer.
- **Ranking as preference**: BaseRank produces a preference ordering over defeasible rules. This is directly comparable to the preference ordering in ASPIC+ (propstore's `aspic_bridge.py`).
- **Relevant Closure's failure modes**: The counter-examples showing Relevant Closure fails Or, CM, RM are cautionary for any system that tries to be "more precise" by only removing relevant conflicting information -- the trade-off is loss of rationality properties.

### Architectural Implications
- The algorithms are purely query-time computations -- they do not modify the knowledge base. This fits propstore's immutable storage + render-time resolution architecture.
- The Datalog+ extension (compound terms) suggests that propstore's concept representation may need to support conjunctive and disjunctive concept compositions for full expressiveness.

---

## Open Questions

1. Can the variable/constant interaction problem (Example 5, p.11) be resolved by a richer set of rationality properties beyond KLM?
2. What is the computational complexity of LexicographicClosureDatalog? The subset enumeration in SubsetRankDatalog is exponential -- is there a tractable approximation?
3. Can the Datalog approach be combined with ASPIC+ to get both structured argumentation and defeasible Datalog entailment?
4. How does this relate to Diller (2025) on grounding rule-based argumentation in Datalog?

---

## Related Work (from references, p.19)

- **Kraus, Lehmann, Magidor (1990)**: Original KLM properties for nonmonotonic reasoning
- **Lehmann & Magidor (1992)**: What does a conditional knowledge base entail? -- defines LM-rationality
- **Casini et al. (2014)**: Taking defeasible entailment beyond rational closure (propositional relevant/lexicographic closure)
- **Casini, Meyer, & Varzinczak (2019)**: Taking defeasible entailment beyond rational closure (extended)
- **Casini et al. (2019)**: Practical Reasoning for Defeasible Description Logics (ALC)
- **Freund (1998)**: Preferential reasoning in the perspective of Poole default logic
- **Ceri et al. (1989)**: What you always wanted to know about Datalog
- **Pasarella & Lobo (2017)**: Framework for Modeling Relationship-based Access Control Policies in Datalog
- **Moodley (2015)**: Practical Reasoning for Defeasible Description Logics (doctoral dissertation)
- **Morris, Ross, & Meyer (2019)**: Defeasible disjunctive Datalog (workshop paper, predecessor to this)
- **Britz (1995)**: Defeasible inheritance-based description logics (another approach to defeasible DLs)

---

## Collection Cross-References

### Already in Collection
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — cited indirectly via shared Datalog+argumentation space; Diller grounds first-order ASPIC+ into Datalog, Morris extends defeasible reasoning into Datalog. Complementary: Diller provides the grounding mechanism, Morris provides the defeasible entailment semantics.
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — foundational defeasible reasoning framework with specificity-based defeat; Morris's KLM-based approach provides a different (ranking-based) mechanism for the same problem of resolving conflicting defeasible conclusions.
- [[Garcia_2004_DefeasibleLogicProgramming]] — DeLP uses dialectical trees for defeasible reasoning in logic programming; Morris uses ranking-based closure operators in Datalog. Both address defeasible reasoning in rule-based languages but with fundamentally different resolution mechanisms.
- [[Pollock_1987_DefeasibleReasoning]] — Pollock's rebutting/undercutting defeat distinction is orthogonal to Morris's ranking-based approach; Morris's closure operators resolve conflicts by exceptionality ranking rather than defeat type.
- [[Dung_1995_AcceptabilityArguments]] — Morris's Rational Closure is an alternative to Dung-style argumentation for resolving defeasible conflicts; both provide formal semantics for which conclusions to accept from conflicting information.

### New Leads (Not Yet in Collection)
- Kraus, Lehmann, & Magidor (1990) — "Nonmonotonic reasoning, preferential models and cumulative logics" — foundational KLM properties paper; defines the rationality postulates that Morris proves satisfaction of
- Lehmann & Magidor (1992) — "What does a conditional knowledge base entail?" — defines LM-rationality, the benchmark Morris uses
- Casini, Meyer, & Varzinczak (2019) — "Taking defeasible entailment beyond rational closure" — direct predecessor; defines propositional Relevant and Lexicographic Closure that Morris extends to Datalog
- Casini et al. (2014) — "Taking defeasible entailment beyond rational closure" (JELIA) — original propositional definitions adapted in this paper

### Supersedes or Recontextualizes
- Morris, Ross, & Meyer (2019) workshop paper — this journal paper extends the 2019 workshop paper with full proofs plus Lexicographic and Relevant Closure (the 2019 paper only covered Rational Closure)

### Conceptual Links (not citation-based)
- [[Maher_2021_DefeasibleReasoningDatalog]] — both address defeasible reasoning in Datalog but from different traditions: Maher compiles Nute-style defeasible logic into Datalog-neg via metaprograms, Morris extends KLM-style closure operators to Disjunctive Datalog. Different formalisms (defeasible logic vs KLM), same target language (Datalog), complementary approaches.
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — Diller uses Datalog as a grounding back-end for ASPIC+, Morris uses Datalog as the object language for defeasible reasoning. Together they suggest a pipeline: Morris's defeasible Datalog rules could be grounded via Diller's procedure before argumentation.
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — Brewka's preferred subtheories use priority-based maximal consistent subsets; Morris's Lexicographic Closure uses subset-based ranking refinement. Both address the problem of choosing among conflicting defaults with different granularity.
- [[Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning]] — Li analyzes which KLM-like properties ASPIC+ satisfies; Morris proves KLM satisfaction for Datalog closure operators. Both use the same rationality postulate framework as their evaluation criterion.

### Cited By (in Collection)
- (none found)
