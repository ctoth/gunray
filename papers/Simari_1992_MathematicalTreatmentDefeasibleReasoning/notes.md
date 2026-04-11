---
title: "A Mathematical Treatment of Defeasible Reasoning and its Implementation"
authors: "Guillermo R. Simari, Ronald P. Loui"
year: 1992
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(92)90069-A"
---

# A Mathematical Treatment of Defeasible Reasoning and its Implementation

## One-Sentence Summary
Provides a rigorous mathematical foundation for defeasible argumentation by combining Poole's specificity criterion with Pollock's warrant theory into a unified system with formal definitions of argument structures, specificity ordering, defeat, and justified beliefs, plus a Prolog implementation ("jf").

## Problem Addressed
Prior systems for defeasible reasoning (Poole, Pollock, Nute's d-Prolog, Loui, Geffner-Pearl) each had deficiencies: Poole defined specificity correctly but lacked operational completeness; Pollock defined warrant operationally but rejected specificity as a generalization of subclass defeaters; inheritance-based systems were ad hoc. No unified, mathematically rigorous system existed that handled all benchmark examples correctly. *(p.5-6)*

## Key Contributions
- Formal definition of **Defeasible Logic Structure** (K, Delta) separating context from defeasible rules *(p.5-6)*
- Rigorous definition of **argument structures** <T,h> as minimal consistent sets of grounded defeasible rule instances that defeasibly derive a conclusion *(p.8-9)*
- Formal **specificity ordering** on argument structures with proof that equi-specificity is an equivalence relation and the induced ordering is a partial order *(p.11-14)*
- **Algebra of arguments**: combination (join) and intersection (meet) operations forming a lattice over subargument structures *(p.16-20)*
- Formal definitions of **disagreement**, **counterargument**, and **defeat** relations *(p.21-23)*
- **Dialectical justification process**: inductive definition of S-arguments and I-arguments at levels, with theorem proving unique stable set exists and is findable *(p.24-26)*
- **Search space reduction** lemmas enabling efficient implementation *(p.27-28)*
- **Prolog implementation** ("jf") using backward chaining with Horn clauses for context and defeasible clauses *(p.34-42)*

## Methodology
The paper builds from first-order logic L with a meta-linguistic relation ">-" (defeasible rules) expressing "reasons to believe the antecedent provide reasons to believe the consequent." Knowledge is split into K (indefeasible context) and Delta (defeasible rules). Arguments are constructed as minimal consistent subsets of grounded defeasible rule instances. A specificity ordering compares arguments. The dialectical process alternates between supporting arguments (S-theories) and interfering arguments (I-arguments), converging to a unique stable set of justified facts. *(p.3-8)*

## Key Equations

### Defeasible Consequence
$$
\Gamma \mid\!\sim A
$$
Where: $\Gamma$ is a set of wffs and grounded defeasible rule instances; $A$ is defeasibly derivable from $\Gamma$ iff there exists a sequence $B_1, \ldots, B_m$ with $A = B_m$ and each $B_i$ is an axiom of $\mathcal{L}$, or $A_i \in \Gamma$, or $A_i$ follows by modus ponens or instantiation of a universally quantified sentence.
*(p.6)*

### Argument Structure (Revised Definition 2.2)
$$
\langle T, h \rangle_{\mathcal{K}} \text{ iff } (1)\ \mathcal{K} \cup T \mid\!\sim h,\quad (2)\ \mathcal{K} \cup T \not\mid\!\sim \bot,\quad (3)\ \nexists T' \subset T,\ \mathcal{K} \cup T' \mid\!\sim h
$$
Where: $T \subseteq \Delta^i$ (grounded instances of defeasible rules), $h \in Sent_C(\mathcal{L})$ (closed sentence), $\mathcal{K}$ is the context. Condition 3 enforces minimality (non-redundancy, "Occam's Razor for arguments").
*(p.9)*

### Strict Specificity (Definition 2.6)
$$
\langle T_1, h_1 \rangle \succ_{\text{spec}} \langle T_2, h_2 \rangle
$$
iff (1) for all $e \in Sent_C(\mathcal{L})$ such that $\mathcal{K}_N \cup \{e\} \cup T_1 \mid\!\sim h_1$, also $\mathcal{K}_N \cup \{e\} \cup T_2 \mid\!\sim h_2$; AND (2) there exists $e \in Sent_C(\mathcal{L})$ such that $\mathcal{K}_N \cup \{e\} \cup T_2 \mid\!\sim h_2$ but $\mathcal{K}_N \cup \{e\} \cup T_1 \not\mid\!\sim h_1$ and $\mathcal{K}_N \cup \{e\} \not\models h_2$ (non-triviality).
*(p.11)*

### Disagreement (Definition 4.1)
$$
\langle T_1, h_1 \rangle \bowtie_{\mathcal{K}} \langle T_2, h_2 \rangle \text{ iff } \mathcal{K} \cup \{h_1, h_2\} \vdash \bot
$$
*(p.22)*

### Counterargument (Definition 4.2)
$$
\langle T_1, h_1 \rangle \stackrel{h}{\otimes} \langle T_2, h_2 \rangle
$$
iff there exists a subargument $\langle T, h \rangle$ of $\langle T_2, h_2 \rangle$ such that $\langle T_1, h_1 \rangle \bowtie_{\mathcal{K}} \langle T, h \rangle$ and $\mathcal{K} \cup \{h_1, h\} \vdash \bot$.
*(p.22)*

### Defeat (Definition 4.3)
$$
\langle T_1, h_1 \rangle \gg_{\text{def}} \langle T_2, h_2 \rangle
$$
iff there exists a subargument $\langle T, h \rangle$ of $\langle T_2, h_2 \rangle$ such that $\langle T_1, h_1 \rangle \stackrel{h}{\otimes} \langle T_2, h_2 \rangle$ (counterargues at $h$) AND $\langle T_1, h_1 \rangle \succ \langle T, h \rangle$ (is more specific than $T$ for $h$).
*(p.23)*

### Justification (Definition 4.4-4.5) — Dialectical Levels
1. All arguments are level 0 S-arguments (supporting) and I-arguments (interfering)
2. $\langle T_1, h_1 \rangle$ is a level $(n+1)$ S-argument iff there is no level $n$ I-argument $\langle T_2, h_2 \rangle$ that counterargues it, and no $\langle T_2, h_2 \rangle \in \text{AStruc}$ that for some $h$, $\langle T_2, h_2 \rangle \stackrel{h}{\otimes} \langle T_1, h_1 \rangle$
3. $\langle T_1, h_1 \rangle$ is a level $(n+1)$ I-argument iff there is no level $n$ I-argument $\langle T_2, h_2 \rangle$ that defeats it

$\langle T, h \rangle$ justifies $h$ iff there exists $m$ such that for all $n \geq m$, $\langle T, h \rangle$ is an $S^n$-theory for $h$.
*(p.24-25)*

### Termination Theorem (Theorem 4.1)
For any Defeasible Logic Structure $(\mathcal{K}, \Delta)$, there is a unique stable set, and the operator $\Sigma$ will find it.
*(p.26)*

### Argument Combination (Join)
$$
\langle T_3, h_3 \rangle = \langle T_1, h_1 \rangle \sqcup \langle T_2, h_2 \rangle, \quad T_3 = T_1 \cup T_2, \quad h_3 = h_1 \wedge h_2
$$
*(p.17)*

### Argument Intersection (Meet)
$$
\langle T_3, h_3 \rangle = \langle T_1, h_1 \rangle \sqcap \langle T_2, h_2 \rangle, \quad T_3 = T_1 \cap T_2, \quad h_3 = (\mathcal{K} \cup \{B_i\}_{i \in I})^+
$$
Where $\{B_i\}_{i \in I}$ is the set of consequents of rules in $T_3$.
*(p.19)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Context (necessary) | $\mathcal{K}_N$ | - | - | Closed sentences in $\mathcal{L}$ | 5 | Sentences with variables = necessary knowledge |
| Context (contingent) | $\mathcal{K}_C$ | - | - | Ground sentences in $\mathcal{L}$ | 5 | Individual constants = contingent facts |
| Defeasible rules | $\Delta$ | - | - | Set of $\alpha \succ\!\!- \beta$ rules | 5 | Non-closed wffs with free variables |
| Context | $\mathcal{K}$ | - | - | $\mathcal{K}_N \cup \mathcal{K}_C$ | 6 | Must be consistent ($\mathcal{K} \not\vdash \bot$) |
| Grounded instances | $\Delta^i$ | - | - | Ground instances of $\Delta$ | 8 | Replace all free variables with constants from $\mathcal{L}$ |

## Implementation Details
- **Data structures**: Argument structures $\langle T, h \rangle$ where $T$ is a set of grounded defeasible rule instances (the "argument basis") and $h$ is the supported conclusion *(p.8)*
- **Operators on arguments**: $An(T)$ returns antecedents, $Co(T)$ returns consequents, $Lit(\langle T,h \rangle) = An(T) \cup Co(T) - \{h\}$ returns all literals *(p.10)*
- **Specificity check reduced**: Lemma 2.4 shows specificity can be checked via antecedents only: $\langle T_1, h_1 \rangle \succeq \langle T_2, h_2 \rangle$ iff $\forall x \in An(T_2), \mathcal{K}_N \cup An(T_1) \cup T_2 \mid\!\sim x$ *(p.14)*
- **Covering lemma**: If $\langle T_1, h_1 \rangle \succeq \langle T_2, h_2 \rangle$ and $\langle T_2, h_2 \rangle$ contains subargument $\langle R, p \rangle$, then $\langle T_1, h_1 \rangle$ contains subargument $\langle S, p \rangle$ with $\langle S, p \rangle \succeq \langle R, p \rangle$ *(p.15)*
- **Lattice structure**: $\mathcal{F}$ (family of subarguments) with combination and intersection forms a lattice. Combination is associative and commutative; identity element is $\langle \emptyset, \mathcal{K}^+ \rangle$. Intersection identity is $\langle T, h \rangle$ itself *(p.17-20)*
- **Implementation language**: Prolog, using Horn clauses for $\mathcal{K}$ and Horn-like defeasible clauses ($B \!\!\prec A_1, \ldots, A_n$) for $\Delta$ *(p.34-36)*
- **Negation**: Uses explicit `neg` prefix operator (not negation-as-failure); `neg neg A = A` *(p.36-37)*
- **jf system architecture**: `analyze(Goal, Argument, Defeater_List)` calls `construct_argument`, `find_defeaters`, `test_defeaters` *(p.41)*
- **Argument construction**: Backward chaining from goal; always finds most specific argument first (unit clauses preferred) *(p.39-40)*
- **Counterargument search**: Forms set of atoms in argument plus their deductive consequences, then backward-chains from negations of those atoms *(p.40)*
- **Specificity test**: Uses activation models — $M$ is activation model for $\langle T, h \rangle$ if $M$ is model of $\mathcal{K}_N$ and for the rules $T'$ forming subset of $T$ such that $\mathcal{K}_N \cup \{e\} \cup T' \mid\!\sim h$ *(p.40)*

## Figures of Interest
- No numbered figures in the paper; examples serve as illustrations throughout

## Results Summary
The system correctly handles all standard benchmark examples: Opus (penguin doesn't fly) *(p.29)*, Nixon Diamond (skeptical — no answer for equi-specific conflicting arguments) *(p.30)*, Cascaded Ambiguities (extended Nixon Diamond — correct skeptical behavior on dependent chains) *(p.31-32)*, and Royal African Elephants (off-path vs on-path preemption handled correctly via specificity) *(p.32-33)*. The reasoner is skeptical: when arguments of equal specificity conflict, no answer is given. *(p.30)*

## Limitations
- Language restricted to Horn clauses for implementation (not full first-order logic) *(p.35)*
- Specificity comparison is based on semantical work not reported in the paper (available in Simari's thesis [23]) *(p.44)*
- The paper acknowledges that the definition of level $n$ computation, while clear and concise, does not directly yield an easy logic programming implementation *(p.42)*
- Only defeasible rules of form $\alpha \succ\!\!- \beta$ (single consequent); no disjunctive conclusions *(p.4-5)*
- Negation handled as explicit `neg` prefix, not full classical negation *(p.36-37)*

## Arguments Against Prior Work
- **Poole [19,20]**: Correct on specificity as comparison measure but "stops short in the operational aspects" — impossible to decide when to apply his specificity comparator. Does not address complexity of interactions among arguments' specificity. *(p.5-6)*
- **Pollock [18]**: Treats operational aspects correctly but "rejects specificity as a generalization of the subclass defeater," placing him "in an extreme minority in the defeasible reasoning community." Has taken research in statistical direction, "which is too general." *(p.5-6)*
- **Nute's d-Prolog [16,17]**: Introduction of absolute rules, defeasible rules, and defeater rules "amounts to a retreat from the goal of having a declarative language." The purpose of defeater rules was to account for exceptions, but they add special rule kinds. *(p.34)*
- **Loui [10]**: Definition of arguments as digraphs "confuses definitional and implementational issues, which this paper separates." The system's spirit and syntactic considerations ($\mathcal{K}$, $\Delta$, $\succ\!\!-$) are taken from Loui, who in turn evolved from Kyburg. *(p.44)*
- **Geffner-Pearl [5]**: Represents "an alternative, older paradigm, based on arguments instead of irrelevance." *(p.44)*
- **Inheritance reasoners**: Produce a "clash of intuitions" and "plethora of theories" with few ways to classify systems. The path-based approach is ad hoc. *(p.4-5)*

## Design Rationale
- **Separation of K and Delta**: Knowledge split into indefeasible context and defeasible rules to cleanly distinguish what is certain from what is tentative *(p.5)*
- **Necessary vs contingent in K**: $\mathcal{K}_N$ (sentences with variables = universal laws) vs $\mathcal{K}_C$ (ground sentences = particular facts), because specificity comparison uses only $\mathcal{K}_N$ *(p.5, 11)*
- **Minimality of arguments**: Non-redundancy condition (Def 2.2, condition 3) acts as "Occam's Razor for arguments" — only the rules actually needed for derivation are included *(p.9)*
- **Specificity over activation models**: Using model-theoretic activation rather than syntactic comparison ensures the ordering works correctly even when argument structures have different internal organization *(p.11)*
- **Skeptical reasoner chosen**: Over credulous (gives all possible conclusions equal standing) and shortest-path (arbitrary), because skepticism correctly withholds judgment on genuinely ambiguous cases *(p.30)*
- **Horn clause restriction for implementation**: Preserves clear semantics while enabling efficient Prolog execution; avoids extra-logical features like cut *(p.35)*

## Testable Properties
- The specificity relation $\succeq$ on AStruc$/\!\approx$ is a partial order (reflexive, transitive, antisymmetric on equivalence classes) *(p.13-14)*
- Equi-specificity $\approx$ is an equivalence relation on AStruc *(p.13)*
- Any argument is at least as specific as any of its subarguments: $\langle T, h \rangle \succeq \langle S, j \rangle$ for all $\langle S, j \rangle \subseteq \langle T, h \rangle$ *(p.13)*
- Subarguments of a given argument structure are pairwise concordant *(p.16)*
- The combination of concordant argument structures is well-defined and forms a lattice with intersection *(p.17-20)*
- For any Defeasible Logic Structure, there exists a unique stable set of justified facts *(p.26)*
- The $\Sigma$ operator converges: if $\Sigma^n(\text{AStruc}) = \Sigma^{n+1}(\text{AStruc})$ then $\Sigma^n(\text{AStruc})$ is stable *(p.26)*
- If $\langle T, h \rangle$ justifies $h$, then every subargument $\langle R, q \rangle$ of $\langle T, h \rangle$ justifies $q$ *(p.25)*
- Opus example: system concludes $\neg F(opus)$ (penguins don't fly defeats birds fly, by specificity) *(p.29)*
- Nixon Diamond: system gives no answer (equi-specific arguments, skeptical reasoner) *(p.30)*
- Covering property: if $\langle T_1, h_1 \rangle \succeq \langle T_2, h_2 \rangle$ and $T_2$ has subargument $\langle R, p \rangle$, then $T_1$ has subargument $\langle S, p \rangle$ with $\langle S, p \rangle \succeq \langle R, p \rangle$ *(p.15)*
- Discarding arguments: if $\langle T, h \rangle$ is $S^n$-theory in $\Omega_{\text{big}}$ then it is $S^n$-theory in $\Omega_{\text{small}}$ (safe to discard covered arguments) *(p.27-28)*

## Relevance to Project
This is a foundational paper for argument-based defeasible reasoning. Its formal framework directly grounds propstore's argumentation layer:
- The Defeasible Logic Structure (K, Delta) maps to propstore's separation of source-of-truth storage from heuristic analysis
- The dialectical justification process (S-arguments vs I-arguments at levels) provides a formal foundation for how propstore's argumentation layer should resolve competing claims
- The specificity ordering provides a principled preference criterion that could complement or replace ad hoc ordering in propstore's render layer
- The unique stable set theorem guarantees termination and determinism for any computation over the argumentation layer
- The algebra of arguments (lattice structure) could inform how propstore combines or intersects argument structures when merging proposals

## Open Questions
- [ ] How does this specificity-based approach compare with ASPIC+ preference orderings (Modgil & Prakken 2018)?
- [ ] Can the activation-model specificity test be made efficient for large knowledge bases?
- [ ] How does the unique stable set relate to Dung's grounded extension?
- [ ] The Horn clause restriction limits expressiveness — does propstore need full first-order?

## Related Work Worth Reading
- Poole 1988 [19] — "A Logical Framework for Default Reasoning" — the specificity definition this paper builds on
- Pollock 1987 [18] — "Defeasible Reasoning" — the warrant theory this paper reformulates
- Loui 1987 [10] — "Defeat Among Arguments" — predecessor system for argument comparison
- Geffner & Pearl 1989 [5] — "A Framework for Reasoning with Defaults" — alternative approach
- Touretzky 1986 [26] — "The Mathematics of Inheritance Systems" — inheritance-based approach
- Simari 1989 [23] — PhD thesis with full proofs and additional detail

## Collection Cross-References

### Already in Collection
- [[Pollock_1987_DefeasibleReasoning]] — cited as [18]; Simari & Loui reformulate Pollock's warrant theory as the dialectical S-argument/I-argument process, while criticizing Pollock's rejection of specificity
- [[Reiter_1980_DefaultReasoning]] — cited as [21]; Reiter's default logic is the competing non-argument-based approach to defeasible reasoning that Simari & Loui's system is an alternative to

### New Leads (Not Yet in Collection)
- Poole (1988) — "A Logical Framework for Default Reasoning" — the specificity definition that Simari & Loui formalize and extend
- Loui (1987) — "Defeat Among Arguments" — direct predecessor system; Simari & Loui's formal language evolved from this
- Touretzky (1986) — "The Mathematics of Inheritance Systems" — inheritance-based approach critiqued by Simari & Loui

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Dung_1995_AcceptabilityArguments]] — cites as [57]; Dung critiques Simari & Loui for focusing on argument structure rather than acceptability, and argues their system adopts Pollock's criterion "without providing a general mechanism" — Dung's abstract AF framework subsumes this approach *(p.351)*
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cites as [46]; references as an early structured argumentation system *(p.51)*
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — cites in reference list *(p.389)*
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — cites in reference list; uses Garcia & Simari formalism as an example evaluated against rationality postulates
- [[Karacapilidis_2001_ComputerSupportedArgumentationCollaborative]] — lists as a New Lead for bridging informal scoring with formal semantics
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — cites in reference list as a key structured argumentation system in the Pollock tradition

### Conceptual Links (not citation-based)
**Structured argumentation foundations:**
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Strong.** ASPIC+ is the modern successor to the structured argumentation tradition that Simari & Loui helped establish. Simari's separation of K (context) and Delta (defeasible rules) directly maps to ASPIC+'s knowledge base with strict/defeasible rules. The specificity ordering maps to ASPIC+'s preference orderings. ASPIC+ generalizes beyond specificity to multiple preference criteria.
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Dung explicitly subsumes Simari & Loui's system: the dialectical justification process (S-arguments vs I-arguments at levels) corresponds to computing extensions of the induced abstract AF. Dung's critique is that the abstract framework reveals properties (stable extensions, preferred extensions) that Simari & Loui's concrete formalism obscures. This tension — abstract vs structured — remains central to argumentation theory.

**Defeat and preference:**
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — **Moderate.** Baroni's reinstatement and skepticism adequacy principles formalize properties that Simari & Loui's dialectical process satisfies informally. The unique stable set theorem (Theorem 4.1) corresponds to computing the grounded extension in Baroni's framework.
- [[Caminada_2006_IssueReinstatementArgumentation]] — **Moderate.** Caminada formalizes reinstatement via labellings; Simari & Loui's dialectical levels (S-arguments defeating I-arguments defeating S-arguments...) implement a concrete reinstatement mechanism. The convergence to a unique stable set parallels the uniqueness of the grounded labelling.

**Defeasible reasoning lineage:**
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — **Strong.** Prakken's survey of Pollock's contributions contextualizes the same theoretical tradition that Simari & Loui work in. Simari & Loui's critique of Pollock (rejecting specificity) and reformulation of Pollock's warrant theory are directly relevant to Prakken's assessment of Pollock's lasting contributions vs limitations.
- [[Brewka_2010_AbstractDialecticalFrameworks]] — **Moderate.** Brewka & Woltran cite Simari & Loui for specificity-based preference ordering in defeasible reasoning. ADFs generalize Dung AFs (which Simari & Loui's dialectical trees instantiate) by allowing arbitrary acceptance conditions on nodes, subsuming the attack-only model that Simari & Loui's framework generates.

---

**See also:** [[Garcia_2004_DefeasibleLogicProgramming]] - DeLP extends and supersedes this predecessor by adding LP integration, dialectical trees with formal acceptability conditions, default negation, presumptions, and a concrete Prolog/WAM implementation.

**See also:** [[Goldszmidt_1992_DefeasibleStrictConsistency]] - Complementary 1992 work on defeasible reasoning. While Simari & Loui formalize argument structure and specificity-based defeat, Goldszmidt & Pearl formalize consistency of mixed defeasible/strict databases via probabilistic semantics and provide a polynomial-time decision procedure. Together they cover argument construction and database coherence.
