---
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:13:19Z"
---
# Deciding Consistency of Databases Containing Defeasible and Strict Information

## Frontmatter
- **Title:** Deciding Consistency of Databases Containing Defeasible and Strict Information
- **Authors:** Moisés Goldszmidt, Judea Pearl
- **Year:** 1992
- **Venue:** Proceedings of the First International Conference on Artificial Intelligence Planning Systems (AIPS-92), also Technical Report R-170, Cognitive Systems Lab, UCLA
- **doi_url:** https://arxiv.org/abs/1304.1507

## One-Sentence Summary
The paper provides a formal criterion for deciding when a database containing both defeasible (default) and strict (classical) sentences is consistent, defines probabilistic semantics for such mixed databases, and gives a polynomial-time testing procedure. *(p.0)*

## Problem Addressed
Databases mixing strict sentences (e.g., "typically, birds fly") and classical sentences (e.g., "penguins do not fly") can generate inconsistencies. Prior work lacked a clear distinction between knowledge base design (accepting exceptions) and knowledge base containing outright contradictions. The paper addresses: when does a mixed defeasible+strict database become inconsistent, and how can this be tested efficiently? *(p.0-1)*

## Key Contributions
1. **Formal consistency criterion** for databases mixing defeasible and strict information, based on a probabilistic interpretation of defaults. *(p.0)*
2. **Polynomial-time decision procedure** for testing consistency of such databases. *(p.0, p.3-4)*
3. **Clear separation** between "exceptions" (tolerable inconsistencies inherent to defeasible reasoning) and genuine "contradictions" (inconsistencies that cannot be resolved). *(p.0, p.1)*
4. **Probabilistic semantics** grounding: defeasible sentences are interpreted as probabilistic statements with high but not certain probability, allowing a formal characterization. *(p.1-2)*
5. **Polynomial complexity result**: worst-case O(P|S| + |S|^3) where P = number of defeasible sentences, S = number of strict sentences. *(p.7)*

## Methodology

### Formal Framework
The paper uses a propositional language L built from a finite set of atoms with standard connectives. *(p.1)*

**Key distinction:** *(p.1)*
- **Strict sentences** (`→`): classical material conditional, e.g., `a → b` meaning all a's are b's
- **Defeasible sentences** (`~>`): conditional defaults, e.g., `a ~> b` meaning "typically, a's are b's" — interpreted as high conditional probability P(b|a) > 0.5

**Probabilistic interpretation:** A defeasible sentence `a ~> b` is satisfied by a probability distribution P if P(b|a) > 0.5 (assuming P(a) > 0). A strict sentence `a → b` is satisfied if P(b|a) = 1. *(p.1-2)*

### Consistency Definition
**Definition 1 (Probabilistic consistency):** Let D be a set of defeasible and strict sentences expressible as conditionals from atoms of P. We say P probabilistically satisfies (p-satisfies) D if there exists a probability distribution over the atoms of P that satisfies all defeasible sentences in D and P(s) > 0 for all strict sentences s in D. *(p.2)*

**Definition 2 (Consistency):** D is consistent if every subset of D that contains only strict sentences (or the empty set) is p-satisfiable. *(p.2)*

**Key insight — tolerability:** A defeasible sentence δ can be "tolerated" by a set of sentences Σ if adding δ to Σ does not make Σ inconsistent. A defeasible sentence is tolerable if there exists a truth assignment that satisfies the conjunction of the strict sentences while also making the defeasible sentence plausible. *(p.2-3)*

### Tolerability and Entailment
**Definition 3 (Toleration):** Let δ be a sentence in Σ which entails sentences d and counterpart d̄. We say δ is tolerated by S and counterpart if there exists a truth assignment t such that the formula representing Σ under t is satisfiable. *(p.2)*

**Definition 4 (Entailment/e-entailed):** Given a p-consistent set D, a conditional statement c is e-entailed by D if every consistent extension of D that contains c is p-consistent. *(p.2-3)*

### Non-consistency (Inconsistency) Detection
Non-satisfiability (inconsistency) occurs whenever the accepted set of conditional sentences has probability equal to zero in all the probability model-spaces of D. *(p.2)*

The paper shows that deciding if a database is inconsistent reduces to checking whether all defeasible sentences can be "tolerated" by the strict sentences. *(p.3)*

## Key Equations

### Probabilistic Satisfaction
$$P(\beta | \alpha) > 0.5$$ 
for defeasible sentences $\alpha \sim\!> \beta$, where $P$ is a probability distribution over atoms. *(p.1)*

$$P(\beta | \alpha) = 1$$
for strict sentences $\alpha \rightarrow \beta$. *(p.1)*

### Quasi-conjunction (material adequacy)
$$C(D) = \{q_1 \lor \neg s_1, D \geq 0; \ldots; s_n \geq 0, q_n \lor \neg s_n\}$$
The quasi-conjunction C(D) provides sufficient conditions for deciding p-satisfiability — if C(D) is verified by P, then in particular D is p-satisfied by P. *(p.1, p.5)*

### Partition-based probability assignment
For constructing a satisfying probability distribution:
$$P(l_i) = \frac{1}{n+1}$$
where n is the number of atoms, distributed to make the defeasible premises have arbitrarily high probability. *(p.5-6)*

### Complexity bound
$$O(P \cdot |S| + |S|^3)$$
where $P$ = number of defeasible sentences (cardinality of $D \setminus S$), $S$ = number of strict sentences. *(p.7)*

## Parameters Table

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Probability threshold for defeasibility | - | - | > 0.5 | (0.5, 1) | p.1 | Conditional probability threshold for "typically" |
| Number of defeasible sentences | P | count | - | >= 0 | p.7 | In complexity bound |
| Number of strict sentences | \|S\| | count | - | >= 0 | p.7 | In complexity bound |
| Number of atoms | n | count | - | >= 1 | p.5 | Used in probability partition construction |

## Methods & Implementation Details

### The Testing Procedure (Algorithm) *(p.3-4, p.7)*
The procedure has two phases:

**Phase 1:** Check if the set of strict sentences S is classically consistent (standard SAT check, but the paper restricts to a tractable fragment). *(p.3)*

**Phase 2:** Iteratively test each defeasible sentence δ_i for tolerability against S:
1. Input: set X = D ∪ S of defeasible and strict sentences
2. While D is not empty:
   a. Pick any sentence e ∈ D such that e is tolerated by S ∪ D'
   b. If e is found, remove e from D, add to D'
   c. If no tolerable e exists, REPORT INCONSISTENT
3. If D becomes empty, REPORT CONSISTENT *(p.7)*

**Toleration check:** For each defeasible sentence, check whether a satisfying truth assignment exists for the conjunction of the material counterparts of the strict sentences — this is a propositional satisfiability check restricted to the material content. *(p.3-4)*

### Complexity Analysis *(p.7)*
- Each iteration of the WHILE loop removes at least one sentence, so at most P iterations
- Each iteration requires at most |S| satisfiability checks  
- Each satisfiability check involves propositional satisfiability of the material counterpart
- The paper notes that for the restricted class of sentences considered (conditionals expressible as implications over atoms), propositional satisfiability is polynomial
- Worst case: O(P|S| + |S|^3) for the overall procedure

### Connection to System Z *(p.1, p.5)*
The notion of p-entailment is shown to be equivalent to that of entailment in preferential model semantics (System Z, Lehmann and Magidor 1992). The defeasible sentences receive a ranking (Z-ordering) where more specific defaults override more general ones.

### Theorems
**Theorem 1:** D ∪ S is p-consistent if and only if every non-empty subset of X = S ∪ D is p-satisfiable. The p-satisfiability check reduces to classical satisfiability of the material counterpart. *(p.2-3)*

**Theorem 3:** X = D ∪ S is p-consistent iff X(·) = {δ | δ ∈ X} is substantively inconsistent. The key structural result linking probabilistic consistency to syntactic tolerability checking. *(p.5-6)*

**Theorem 4:** The worst-case complexity of testing consistency of X is O(P|S| + |S|^3). *(p.7)*

## Figures of Interest
- **Example 1** *(p.3)*: Nixon Diamond variant — "Typically, Nixonians are Republican" vs "Typically, Quakers are pacifists" vs "All Republicans are non-pacifists" — demonstrates how the procedure correctly identifies a consistent database that merely has exceptions.
- **Example 2** *(p.3)*: Modified example adding "Typically, pacifists are pensioned" — shows how this can create genuine inconsistency vs. tolerable exceptions.

## Results Summary
1. A mixed defeasible+strict database is consistent iff every defeasible sentence can be "tolerated" by the strict sentences through an iterative process of removing tolerable defaults. *(p.2-3)*
2. The decision procedure runs in polynomial time for the class of databases considered. *(p.7)*
3. The probabilistic semantics (p-entailment) coincides with preferential model semantics (System Z). *(p.5)*
4. The procedure correctly handles the Nixon Diamond and similar benchmark cases. *(p.3-4)*

## Limitations
- Restricted to propositional language — no first-order quantification. *(p.1)*
- The polynomial complexity holds for conditionals over atoms; general propositional satisfiability is NP-complete, so the tractability depends on the syntactic form of sentences. *(p.7)*
- The probability threshold of 0.5 is somewhat arbitrary — the paper notes this is "close to Poole's notion" but other thresholds could be considered. *(p.1)*
- Does not address dynamic database updates (adding/removing sentences over time). *(p.5)*
- Limited to two types of sentences (defeasible and strict) — does not handle graded levels of defeasibility. *(p.1)*

## Arguments Against Prior Work
- **Against Poole (1991):** Poole's system uses specificity orderings but lacks a clear probabilistic foundation for when defaults become inconsistent vs. merely exceptional. Goldszmidt & Pearl provide this foundation. *(p.0, p.5)*
- **Against pure skeptical approaches:** Purely skeptical nonmonotonic systems (that withdraw all conflicting defaults) lose useful information. The tolerance-based approach preserves maximal information while detecting genuine contradictions. *(p.0-1)*
- **Against Adams (1975) original formulation:** While Adams provides the epsilon-semantics foundation, his system does not address the consistency decision problem for mixed databases directly. *(p.5)*

## Design Rationale
The core insight is that "inconsistency" in a defeasible database should not mean "there exist exceptions to defaults" (that is the whole point of defaults). Instead, inconsistency means "no probability distribution can simultaneously satisfy all the strict constraints while making the defaults merely probable." The tolerance-based procedure captures exactly this distinction. *(p.0-1, p.5)*

## Testable Properties

1. **Tolerability is order-independent:** The consistency verdict should not depend on the order in which defeasible sentences are tested for tolerance. *(p.3)*
2. **Strict-only subset consistency:** If the strict sentences alone are inconsistent, the whole database is inconsistent regardless of defeasible content. *(p.2)*
3. **Adding a tolerable default preserves consistency:** If δ is tolerable by S, then D ∪ {δ} remains consistent if D was consistent. *(p.2-3)*
4. **Nixon Diamond is consistent:** A database with "birds fly," "penguins don't fly," "Tweety is a bird and penguin" should be judged consistent (exceptions, not contradictions). *(p.3)*
5. **Polynomial complexity:** Testing should complete in O(P|S| + |S|^3) time. *(p.7)*
6. **Equivalence to System Z:** The p-entailment relation should coincide with the Z-ranking entailment. *(p.5)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation layer:

1. **Defeasible vs. strict claims:** propstore stores both defeasible and strict claims. This paper provides the theoretical foundation for deciding when a collection of such claims is consistent — essential for the conflict detection system.
2. **Tolerance-based consistency:** The iterative tolerance procedure maps naturally to propstore's approach of holding multiple competing claims without premature resolution. The key insight — that "exceptions" are different from "contradictions" — aligns with propstore's non-commitment discipline.
3. **Probabilistic grounding:** The paper's probabilistic semantics for defaults connects directly to propstore's subjective logic / opinion algebra layer, where beliefs carry uncertainty. The 0.5 threshold for "typically" could inform stance classification thresholds.
4. **Polynomial decidability:** The tractability result is practically important — propstore needs to be able to check consistency of claim databases efficiently.
5. **Connection to System Z / preferential semantics:** propstore's ASPIC+ bridge already handles preference orderings; the equivalence to System Z means the tolerance-based approach is compatible with the existing argumentation framework.
6. **Relation to Simari & Loui 1992:** Both papers are from the same era of defeasible reasoning formalization. Simari & Loui focus on argument structure; Goldszmidt & Pearl focus on database consistency. Together they cover the "when do arguments conflict" and "is the overall knowledge base coherent" questions.

## Open Questions
1. How does the tolerance procedure extend to first-order databases with variables?
2. Can the 0.5 probability threshold be made adaptive based on domain knowledge?
3. How does this consistency notion interact with ASPIC+ structured argumentation — can we use it as a pre-filter before building argument graphs?
4. What happens when the database is dynamically updated — can consistency be maintained incrementally?
5. How does this relate to Konieczny & Pino Pérez's IC merging — both deal with consistency of merged information sources?

## Related Work
- **Adams (1975):** Epsilon-semantics for conditional logic — foundational for the probabilistic interpretation used here. *(p.5)*
- **Lehmann & Magidor (1992):** System Z and rational closure — the paper shows equivalence of p-entailment to System Z. *(p.1, p.5)*
- **Poole (1991):** Default logic and specificity — addressed but lacking the probabilistic consistency criterion. *(p.0, p.5)*
- **Pearl (1988, 1991):** Probabilistic semantics for defaults — predecessor work by co-author. *(p.5)*
- **de Kleer (1986):** ATMS — related assumption-based approach to managing multiple consistent contexts. *(p.5)*
- **Reiter (1980):** Default logic — the classical framework that this paper extends with consistency testing. *(p.5)*
- **Simari & Loui (1992):** Mathematical treatment of defeasible reasoning — complementary work on argument structure. *(Related in collection)*

## Collection Cross-References

### Already in Collection
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — cited as [Gärdenfors, 88]; Knowledge in Flux, the AGM belief revision framework that provides the broader epistemological context for consistency of belief bases
- [[Reiter_1980_DefaultReasoning]] — cited as [Reiter, 80]; the classical default logic paper whose consistency problem this paper addresses with probabilistic semantics
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — complementary contemporaneous work; Simari & Loui formalize argument structure and specificity for defeasible reasoning, while Goldszmidt & Pearl formalize database consistency for mixed defeasible/strict sentences

### Cited By (in Collection)
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — cites Goldszmidt's qualitative probabilities work ([11], [12], [13] in their bibliography) as connecting ranking functions to probabilistic reasoning and causal models

### New Leads (Not Yet in Collection)
- Adams (1975) — "The Logic of Conditionals" — foundational epsilon-semantics that grounds the probabilistic interpretation of defaults used here
- Lehmann & Magidor (1992) — "Rational Logics and their Models" — defines System Z; this paper proves p-entailment equivalence to System Z
- Poole (1991) — default logic with specificity; Goldszmidt & Pearl improve on Poole's consistency notion

### Conceptual Links (not citation-based)
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — **Strong.** Both papers from 1992 formalize defeasible reasoning from complementary angles. Simari & Loui focus on argument structure (what constitutes a valid argument, how specificity determines defeat); Goldszmidt & Pearl focus on database consistency (when does a collection of defeasible+strict sentences become incoherent). Together they answer "how do arguments work?" and "when is the whole knowledge base broken?" — both questions propstore's argumentation layer must address.
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — **Strong.** Darwiche & Pearl's iterated belief revision postulates (C1-C4) govern how epistemic states change under revision; Goldszmidt & Pearl's consistency criterion determines when revision is needed (the database is inconsistent). The ranking functions used in Darwiche & Pearl connect directly to Goldszmidt & Pearl's System Z equivalence.
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — **Moderate.** AGM provides the revision framework; Goldszmidt & Pearl provide the consistency detection that determines when revision operations are necessary for mixed defeasible/strict databases.
