---
title: "Defeasible Logic Programming: An Argumentative Approach"
authors: "Alejandro J. Garcia, Guillermo R. Simari"
year: 2004
venue: "Theory and Practice of Logic Programming"
doi_url: "https://doi.org/10.1017/S1471068403001674"
pages: "95-138"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T07:45:04Z"
---
# Defeasible Logic Programming: An Argumentative Approach

## One-Sentence Summary
Presents DeLP, a complete formalism that combines logic programming with defeasible argumentation via dialectical trees to provide a four-valued query answer system (YES/NO/UNDECIDED/UNKNOWN) where tentative information is represented as defeasible rules and conflicts are resolved through argument comparison and dialectical analysis.

## Problem Addressed
Existing logic programming approaches lack principled mechanisms for representing tentative/defeasible information and resolving contradictions arising from it. Standard LP treats all rules as strict, and prior defeasible reasoning systems either lack Prolog-like unification and LP infrastructure, or handle contradictions through priorities embedded in the derivation process rather than through independent argument comparison. *(p.1-2)*

## Key Contributions
- A complete formalism (DeLP) combining logic programming with defeasible argumentation *(p.1)*
- A language that distinguishes strict rules (sound knowledge) from defeasible rules (tentative information) using the `~>` operator *(p.2-3)*
- Formal definitions of argument structure, counter-argument, disagreement, and defeat based on defeasible derivations *(p.8-11)*
- A modular comparison criterion for arguments (generalized specificity), independent of the derivation mechanism *(p.12-14)*
- A dialectical analysis framework using dialectical trees with formal acceptability conditions on argumentation lines *(p.17-22)*
- A marking procedure on dialectical trees to determine warrant status *(p.23-24)*
- A four-valued answer system: YES, NO, UNDECIDED, UNKNOWN *(p.25)*
- Extensions for default negation (`not`) and presumptions *(p.29-33)*
- Implementation as both a Prolog meta-interpreter and a WAM-based abstract machine *(p.33-34)*

## Methodology
The paper defines the DeLP formalism bottom-up:
1. Define the language (strict rules, defeasible rules, facts)
2. Define defeasible derivation (argument construction by chaining rules)
3. Define argument structures and sub-arguments
4. Define disagreement and counter-arguments (attack)
5. Define defeat via argument comparison criteria
6. Define dialectical trees that collect all argumentation lines
7. Define acceptability conditions on argumentation lines to prevent pathological cases
8. Define a marking procedure on dialectical trees to determine warrant
9. Define the four-valued answer to queries

## Key Equations / Statistical Models

### Ground instances of a program

$$
Ground(\mathscr{P}) = \bigcup_{R \in \mathscr{P}} Ground(R)
$$
Where: $Ground(R)$ is the set of all ground instances of schematic rule $R$; $\mathscr{P}$ is a de.l.p.
*(p.4)*

### Defeasible Derivation (Definition 2.5)

A defeasible derivation of $L$ from $\mathscr{P}$, denoted $\mathscr{P} \vert\sim L$, is a finite sequence $L_1, L_2, \ldots, L_n = L$ of ground literals where each $L_i$ is either:
(a) a fact in $\Pi$, or
(b) there exists a rule $R_i$ in $\mathscr{P}$ (strict or defeasible) with head $L_i$ and body $B_1, B_2, \ldots, B_k$ and every literal of the body is an element $L_j$ of the sequence appearing before $L_i$ ($j < i$).
*(p.5-6)*

### Argument Structure (Definition 3.1)

Let $\mathscr{P} = \Pi \cup \Delta$ be a de.l.p. An argument structure for a literal $h$, denoted $\langle \mathscr{A}, h \rangle$, is a pair where $\mathscr{A} \subseteq \Delta$ satisfying:
1. there exists a defeasible derivation for $h$ from $\Pi \cup \mathscr{A}$
2. the set $\Pi \cup \mathscr{A}$ is non-contradictory, and
3. $\mathscr{A}$ is minimal: there is no proper subset $\mathscr{A}'$ of $\mathscr{A}$ such that conditions (1) and (2) hold.
*(p.8)*

### Disagreement (Definition 3.3)

Two literals $h$ and $h_1$ *disagree* if and only if the set $\Pi \cup \{h, h_1\}$ is contradictory.
*(p.10)*

### Counter-argument (Definition 3.4)

$\langle \mathscr{A}_1, h_1 \rangle$ *counter-argues*, *rebuts*, or *attacks* $\langle \mathscr{A}_2, h_2 \rangle$ at literal $h$ iff there exists a sub-argument $\langle \mathscr{A}, h \rangle$ of $\langle \mathscr{A}_2, h_2 \rangle$ such that $h$ and $h_1$ *disagree*.
*(p.10-11)*

### Generalized Specificity (Definition 3.5)

$\langle \mathscr{A}_1, h_1 \rangle$ is *strictly more specific* than $\langle \mathscr{A}_2, h_2 \rangle$ (denoted $\langle \mathscr{A}_1, h_1 \rangle \succ \langle \mathscr{A}_2, h_2 \rangle$) iff:
Let $H_1$ be the set of all literals that have a defeasible derivation from $\mathscr{P}$ (without including facts), and $F_1, F_2$ be the activating sets.
1. For all $F \subseteq H_1$, if $\Pi \cup F \cup \mathscr{A}_1$ activates $\mathscr{A}_1$ then $\Pi \cup F \cup \mathscr{A}_2$ activates $\mathscr{A}_2$ (i.e., $\mathscr{A}_1$ is activated in at least as many scenarios)
2. There exists at least one $F$ such that $\mathscr{A}_1$ is activated but $\mathscr{A}_2$ is not
*(p.13)*

### Proper Defeater (Definition 4.1)

$\langle \mathscr{A}_1, h_1 \rangle$ is a *proper defeater* for $\langle \mathscr{A}_2, h_2 \rangle$ at literal $h$ iff $\langle \mathscr{A}_1, h_1 \rangle$ counter-argues $\langle \mathscr{A}_2, h_2 \rangle$ at $h$ with disagreement sub-argument $\langle \mathscr{A}, h \rangle$ and $\langle \mathscr{A}_1, h_1 \rangle$ is strictly preferred to $\langle \mathscr{A}, h \rangle$.
*(p.16)*

### Blocking Defeater (Definition 4.2)

$\langle \mathscr{A}_1, h_1 \rangle$ is a *blocking defeater* for $\langle \mathscr{A}_2, h_2 \rangle$ at literal $h$ iff $\langle \mathscr{A}_1, h_1 \rangle$ counter-argues $\langle \mathscr{A}_2, h_2 \rangle$ at $h$ and neither is strictly preferred to the other.
*(p.16)*

### Acceptable Argumentation Line (Definition 4.7)

An argumentation line $\Lambda = [\langle \mathscr{A}_0, h_0 \rangle, \langle \mathscr{A}_1, h_1 \rangle, \ldots, \langle \mathscr{A}_n, h_n \rangle]$ is *acceptable* iff:
1. $\Lambda$ is a finite sequence
2. the set $S_s$ of supporting arguments is concordant, and the set $S_i$ of interfering arguments is concordant
3. no $\langle \mathscr{A}_i, h_i \rangle$ is a sub-argument of any $\langle \mathscr{A}_j, h_j \rangle$ appearing earlier ($j < i$)
4. for all $k$, if the argument $\langle \mathscr{A}_k, h_k \rangle$ is a blocking defeater for $\langle \mathscr{A}_{k-1}, h_{k-1} \rangle$, then $\langle \mathscr{A}_{k+1}, h_{k+1} \rangle$ (if it exists) must be a proper defeater for $\langle \mathscr{A}_k, h_k \rangle$
*(p.21)*

### Dialectical Tree (Definition 5.1)

Let $\langle \mathscr{A}_0, h_0 \rangle$ be an argument structure from program $\mathscr{P}$. A dialectical tree for $\langle \mathscr{A}_0, h_0 \rangle$, denoted $\mathscr{T}_{\langle \mathscr{A}_0, h_0 \rangle}$, is defined as follows:
1. The root of the tree is labeled with $\langle \mathscr{A}_0, h_0 \rangle$
2. Let $N$ be a non-root node labeled with $\langle \mathscr{A}_n, h_n \rangle$ and $\Lambda = [\langle \mathscr{A}_0, h_0 \rangle, \ldots, \langle \mathscr{A}_n, h_n \rangle]$ the sequence of labels on the path from root to $N$. Let $\langle \mathscr{B}_1, q_1 \rangle, \ldots, \langle \mathscr{B}_k, q_k \rangle$ be all defeaters for $\langle \mathscr{A}_n, h_n \rangle$. For each $\langle \mathscr{B}_i, q_i \rangle$ such that the argumentation line $\Lambda' = [\Lambda, \langle \mathscr{B}_i, q_i \rangle]$ is acceptable, the node $N$ has a child $N_i$ labeled $\langle \mathscr{B}_i, q_i \rangle$.
*(p.22)*

### Marking Procedure (Procedure 5.1)

1. All leaves in $\mathscr{T}_{\langle \mathscr{A}, h \rangle}$ are marked as "U" (undefeated) in $\mathscr{T}^*_{\langle \mathscr{A}, h \rangle}$
2. Let $\langle \mathscr{A}_i, h_i \rangle$ be an inner node of $\mathscr{T}_{\langle \mathscr{A}, h \rangle}$. Then $\langle \mathscr{A}_i, h_i \rangle$ will be marked as "D" (defeated) in $\mathscr{T}^*_{\langle \mathscr{A}, h \rangle}$ iff it has at least a child marked as "U". Otherwise it is marked "U".
*(p.24)*

### Warrant (Definition 5.2)

A literal $h$ is *warranted* from a de.l.p. $\mathscr{P}$ iff there exists an argument structure $\langle \mathscr{A}, h \rangle$ such that the root of the marked dialectical tree $\mathscr{T}^*_{\langle \mathscr{A}, h \rangle}$ is marked "U".
*(p.24)*

### Answer to a Query (Definition 5.3)

The answer of a DeLP query for a literal $h$ from de.l.p. $\mathscr{P}$:
- **YES** if $h$ is warranted
- **NO** if the complement $\bar{h}$ is warranted
- **UNDECIDED** if neither $h$ nor $\bar{h}$ is warranted, but there exists at least one argument for $h$ or $\bar{h}$
- **UNKNOWN** if $h$ is not in the language of the program
*(p.25)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Strict rules set | $\Pi$ | - | - | - | 3 | Set of strict rules and facts |
| Defeasible rules set | $\Delta$ | - | - | - | 3 | Set of defeasible rules |
| Strong negation | $\sim$ | - | - | - | 2 | Classical/explicit negation |
| Default negation | $not$ | - | - | - | 29 | Only in Extended DeLP |
| Query answer values | - | - | - | {YES, NO, UNDECIDED, UNKNOWN} | 25 | Four-valued |
| Marking labels | - | - | - | {U, D} | 24 | Undefeated/Defeated |

## Methods & Implementation Details

### Language Structure
- A de.l.p. $\mathscr{P} = (\Pi, \Delta)$ where $\Pi$ = strict rules + facts, $\Delta$ = defeasible rules *(p.3)*
- Strict rule: $L_0 \leftarrow L_1, \ldots, L_n$ where $L_0$ is a literal and $L_1, \ldots, L_n$ are literals *(p.3)*
- Defeasible rule: $L_0 \prec L_1, \ldots, L_n$ (read "L_0 is tentatively implied by L_1...L_n") *(p.3)*
- A fact is a strict rule with empty body *(p.3)*
- Strong negation $\sim$ is used in the object language; $\sim p$ and $p$ are complementary literals *(p.2)*
- Variables denoted by uppercase letters; ground instances obtained via Herbrand base *(p.4)*

### Argument Construction
- Arguments are built by chaining defeasible and strict rules *(p.8)*
- An argument $\langle \mathscr{A}, h \rangle$ requires $\mathscr{A} \subseteq \Delta$ to be minimal and $\Pi \cup \mathscr{A}$ non-contradictory *(p.8)*
- Strict derivations (using only $\Pi$) cannot be counter-argued (Proposition 3.1) *(p.11)*
- Sub-argument $\langle \mathscr{B}, q \rangle$ of $\langle \mathscr{A}, h \rangle$ means $\mathscr{B} \subseteq \mathscr{A}$ *(p.9)*

### Disagreement and Attack
- Two literals disagree when adding both to $\Pi$ creates a contradiction *(p.10)*
- Complementary literals $p$ and $\sim p$ trivially disagree *(p.10)*
- Non-complementary literals can also disagree if strict rules connect them *(p.10)*
- Counter-argument attacks at a sub-argument's conclusion (the disagreement sub-argument) *(p.10-11)*
- Direct attack: counter-argument targets the root conclusion. Indirect attack: targets a sub-argument *(p.10, Fig 2)*

### Comparison Criteria
- Comparison criterion is modular: independent of derivation, can be replaced *(p.14)*
- Generalized specificity: prefers arguments that use more specific information (more premises relative to activation conditions) *(p.13)*
- Rule priority criterion: explicitly ordered defeasible rules, argument preferred if all its rules have higher priority *(p.15)*
- Strict derivations are implicitly preferred over all defeasible arguments *(p.14)*

### Problematic Argumentation Situations
- Self-defeating arguments: impossible in DeLP because $\Pi \cup \mathscr{A}$ must be non-contradictory (Proposition 4.2) *(p.18)*
- Reciprocal defeaters: two arguments that defeat each other, must be detected and avoided *(p.19, Fig 5)*
- Circular argumentation: argument reintroduced later in its own defense, detected via sub-argument check *(p.19-20, Fig 6-7)*
- Contradictory argumentation: supporting arguments contradict each other *(p.20-21, Fig 8)*
- Blocking defeater defeating a blocking defeater: not allowed; must use proper defeater to defeat a blocking defeater (condition 4 of Def 4.7) *(p.21)*

### Dialectical Analysis
- Dialectical tree: AND-OR-like tree where root is the queried argument, children are defeaters *(p.22)*
- Argumentation lines: paths from root to leaf, each must be acceptable *(p.17, 21)*
- Marking procedure: bottom-up labeling, leaves=U, inner node=D iff any child is U *(p.24)*
- Warrant: root marked U means the argument is warranted *(p.24)*

### Warrant Procedure with Pruning
- Prolog-like specification given in Fig 13 *(p.28-29)*
- Pruning: if a node in a dialectical tree is already determined (all children processed and mark won't change), skip remaining defeater exploration *(p.28-29)*
- Similar to alpha-beta pruning in game trees *(p.27)*
- Depth-first construction with marking during construction *(p.27-28)*

### Extended DeLP with Default Negation (Section 6.1)
- Adds `not` (default negation/negation as failure) distinct from `~` (strong negation) *(p.29)*
- Default negated literals can appear in rule bodies but NOT in rule heads *(p.30)*
- Default negated literals become additional points of attack *(p.31)*
- Argument for `not L` exists if `L` is not warranted *(p.30)*
- Creates interaction between argumentation and default negation *(p.30-31)*

### Extended DeLP with Presumptions (Section 6.2)
- A presumption is a defeasible rule with empty body *(p.32)*
- Presumptions are a special case of defeasible rules *(p.32)*
- Comparison criterion must handle the fact that presumption-based arguments use no evidence *(p.32-33)*

### Implementation (Section 7)
- Prolog meta-interpreter implemented *(p.33)*
- Abstract machine based on Warren Abstract Machine (WAM) extension called ODAM (Omission-capable Defeasible Argument Machine) *(p.33-34)*
- Virtual machine prototype also developed *(p.33)*
- Multi-agent system application: stock market domain *(p.34)*
- Dialectical tree construction can become large for non-trivial scenarios *(p.34)*
- Search procedure described for efficiently building dialectical trees *(p.34)*

## Figures of Interest
- **Fig 1 (p.10):** Argument $\langle \mathscr{A}, h \rangle$ and sub-argument $\langle \mathscr{B}, q \rangle$ as nested triangles
- **Fig 2 (p.10):** Indirect attack (left) vs direct attack (right) on argument structures
- **Fig 3 (p.17):** Argumentation lines as sequences of defeating arguments
- **Fig 4 (p.18):** Self-defeating argument leading to infinite argumentation line
- **Fig 5 (p.19):** Reciprocal defeaters
- **Fig 6 (p.19):** Circular argumentation
- **Fig 7 (p.20):** Circular argumentation with sub-argument reuse
- **Fig 8 (p.20):** Contradictory argumentation line
- **Fig 9 (p.23):** Dialectical tree for Example 5.1 with multiple branches
- **Fig 10 (p.24):** Marked dialectical tree (U/D labels)
- **Fig 11 (p.27):** Marked dialectical tree for argument structure (left) and pruned version (right)
- **Fig 12 (p.28):** Argumentation lines of Example 5.7 showing tree expansion
- **Fig 13 (p.29):** Prolog-like specification of warrant procedure with pruning

## Results Summary
DeLP provides a complete, implemented formalism that:
- Handles contradictory information without collapsing into inconsistency *(p.1)*
- Provides four distinct query answers (YES/NO/UNDECIDED/UNKNOWN) *(p.25)*
- Prevents all pathological argumentation patterns (self-defeat, circularity, contradiction in support) *(p.18-21)*
- Has been implemented both as a Prolog interpreter and an abstract machine *(p.33-34)*
- Has been applied to multi-agent systems and stock market domains *(p.34)*

## Limitations
- Comparison criterion (generalized specificity) may not be suitable for all domains *(p.14)*
- Dialectical tree construction can become computationally expensive for non-trivial programs *(p.34)*
- The specificity criterion has problems when the argument has certain presumptions (Section 6.3) *(p.33)*
- No complexity analysis provided *(throughout)*
- Default negation interaction with argumentation creates subtle issues around when `not L` should be treated as defeated *(p.31)*
- Rule priority criterion defined but no mechanism for acquiring priorities automatically *(p.15)*
- No formal semantics connecting DeLP to well-known LP semantics (answer sets, well-founded) -- comparison is informal *(p.35-37)*

## Arguments Against Prior Work

### Against n-Prolog (Gabbay 1985)
- n-Prolog was the first to introduce defeasible reasoning with LP, but it does not allow default negation and uses strict rules and strong negation only. DeLP extends the approach with proper defeasible rules. *(p.34-35)*

### Against Nute's Defeasible Logic (1994)
- Uses a priority relation on rules directly embedded in the derivation. DeLP separates comparison from derivation, making the criterion modular and replaceable. *(p.35)*

### Against OSCAR (Pollock 1987, 1995)
- OSCAR uses a procedural approach; a conclusion may be "warranted" and then "unwarranted" as a result of further reasoning. DeLP's dialectical trees prevent this non-monotonic oscillation by considering all argumentation lines simultaneously. *(p.35)*

### Against Prakken and Sartor (1997)
- Uses a dialectical proof theory but the proof procedure for logic programs is quite different from dialectical trees. In PLP, default negated literals are defended by rules, and the comparison is based on rule strength. *(p.35, 37)*

### Against Dung (1993, 1995)
- Dung's abstract framework is very general but does not provide a concrete language or argument construction mechanism. DeLP provides both. *(p.35)*

### Against Extended Logic Programming (Gelfond & Lifschitz 1991)
- ELP computes stable models (answer sets). When contradictory rules exist, two complementary conclusions appear in different stable models, requiring a choice. DeLP keeps both and resolves via dialectical analysis. *(p.35-36)*

### Against WFSX (Alferes & Pereira)
- WFSX adds explicit negation to well-founded semantics. DeLP and WFSX handle contradictions differently: WFSX may produce contradictory well-founded models, DeLP never produces contradictions because argumentation prevents it. *(p.36)*

### Against Brewka's PLP (2001)
- PLP (Prioritized Logic Programs) uses only default negated literals for attack. DeLP uses both strong negation disagreement and default negation. Also PLP's argument reinstatement is different. *(p.37-38)*

## Design Rationale
- **Separation of comparison from derivation:** The comparison criterion is modular and can be replaced without changing the argumentation framework. This allows domain-specific preference criteria. *(p.14)*
- **Dialectical trees over proof trees:** Using AND-OR dialectical trees rather than linear proof trees allows considering all possible counter-arguments simultaneously and prevents the oscillation problem found in OSCAR. *(p.22, 35)*
- **Four-valued answers:** UNDECIDED is distinct from UNKNOWN -- UNDECIDED means there are arguments but none prevails; UNKNOWN means the literal is not in the language. This prevents conflating ignorance with indecision. *(p.25)*
- **Blocking defeaters cannot defeat blocking defeaters:** This prevents infinite chains of mutually blocking arguments. A blocking defeater can only be defeated by a proper (strictly preferred) defeater. *(p.21)*
- **Non-contradictory argument requirement:** By requiring $\Pi \cup \mathscr{A}$ to be non-contradictory, self-defeating arguments are structurally impossible (Proposition 4.2). *(p.8, 18)*
- **Concordance requirement:** Supporting arguments in an argumentation line must be concordant (their union with $\Pi$ must be non-contradictory). This prevents contradictory support chains. *(p.20-21)*
- **Sub-argument exclusion:** An argument cannot be reintroduced as its own defeater later in an argumentation line. This prevents circular reasoning. *(p.21)*

## Testable Properties
- No argument structure can be self-defeating (Proposition 4.2) *(p.18)*
- If $\mathscr{A}_1 = \emptyset$ and $\mathscr{A}_2 = \emptyset$, then $\langle \mathscr{A}_1, h_1 \rangle \equiv \langle \mathscr{A}_2, h_2 \rangle$ (equi-specificity for empty arguments) (Proposition 3.3) *(p.14)*
- If two arguments are equi-specific then their conclusions cannot disagree (Proposition 3.4) *(p.14)*
- Equi-specificity is an equivalence relation (Lemma 3.1) *(p.14)*
- A strictly derived literal is always warranted (Proposition 5.1) *(p.24)*
- Strictly derived literals have no counter-arguments (Proposition 3.1) *(p.11)*
- There is no possible counter-argument for an argument structure $\langle \emptyset, h \rangle$ (Proposition 3.2) *(p.11)*
- Every acceptable argumentation line is finite (by Definition 4.7, condition 1) *(p.21)*
- The set of supporting arguments in an acceptable line is concordant (Def 4.7, condition 2) *(p.21)*
- The set of interfering arguments in an acceptable line is concordant (Def 4.7, condition 2) *(p.21)*
- A blocking defeater for a blocking defeater will not be considered a defeater (Def 4.7, condition 4) *(p.21)*
- The dialectical tree is always finite (follows from acceptable line finiteness + finite defeater count) *(p.22)*
- Marking procedure terminates (finite tree) *(p.24)*
- For any query $h$: exactly one of YES/NO/UNDECIDED/UNKNOWN holds *(p.25)*

## Relevance to Project
DeLP is the closest existing system to what propstore plans for quantified rule-based reasoning. Key relevances:

1. **Dialectical trees map to propstore's argumentation layer:** DeLP's dialectical tree construction (Def 5.1) and marking procedure (Procedure 5.1) provide a concrete algorithm for the Dung-AF-like computation propstore needs. The U/D marking is equivalent to computing grounded extensions.

2. **Four-valued answers match propstore's non-commitment discipline:** DeLP's YES/NO/UNDECIDED/UNKNOWN maps directly to propstore's need to represent honest ignorance vs. genuine disagreement at render time.

3. **Modular comparison criterion:** DeLP's separation of argument comparison from derivation (Section 3.2) mirrors propstore's need for pluggable preference orderings in the ASPIC+ bridge.

4. **Acceptable argumentation lines:** The four conditions of Definition 4.7 provide concrete constraints for propstore's argumentation line validation.

5. **Default negation interaction:** Section 6.1's treatment of `not` in conjunction with defeasible argumentation is directly relevant to propstore's handling of absence-of-evidence claims.

6. **Concrete implementation architecture:** The WAM-based abstract machine (Section 7) provides a reference for efficient implementation of dialectical analysis.

## Open Questions
- [ ] How does DeLP's generalized specificity relate to ASPIC+'s last-link/weakest-link principles?
- [ ] Can DeLP's dialectical tree marking be mapped to Dung's grounded semantics formally?
- [ ] How would DeLP handle propstore's probabilistic/subjective-logic opinions rather than binary warrant?
- [ ] What is the computational complexity of dialectical tree construction for realistic knowledge bases?
- [ ] How does the pruning optimization (Fig 13) compare to existing AF solver optimizations?

## Related Work Worth Reading
- Simari, G. R. and Loui, R. P. (1992) "A Mathematical Treatment of Defeasible Reasoning and its Implementation" -- predecessor formalism *(already in collection)*
- Prakken, H. and Sartor, G. (1997) "Argument-based extended logic programming with defeasible priorities" -- key comparison system *(p.35)*
- Stolzenburg, F. et al. (2003) "Computing generalized specificity" -- formal details of the comparison criterion *(p.13)*
- Chesnevar, C. I. et al. (2003) "An abstract machine for defeasible argumentation" -- the ODAM implementation *(p.34)*
- Garcia, A. J. et al. (2004) "Dialectical trees for DeLP" -- efficiency of warrant procedure
- Brewka, G. (2001) "On the relation between defeasible logic and well-founded semantics" *(p.37)*
- Alferes, J. J. and Pereira, L. M. (1996) "Reasoning with logic programming" -- WFSX comparison *(p.36)*

## Collection Cross-References

### Already in Collection
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] -- direct predecessor formalism by the same authors; DeLP extends this with LP integration and dialectical trees
- [[Pollock_1987_DefeasibleReasoning]] -- OSCAR system compared against in Section 8; DeLP addresses OSCAR's oscillation problem via dialectical trees
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] -- Brewka's preferred subtheories compared in Section 8
- [[Dung_1995_AcceptabilityArgumentsFundamentalRole]] -- abstract AF that DeLP instantiates with concrete argument construction

### Cited By (in Collection)
- [[Caminada_2007_EvaluationArgumentationFormalisms]] -- cites DeLP as an argumentation formalism evaluated against rationality postulates
- [[Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible]] -- cites DeLP as prior work on defeasible LP
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] -- cites DeLP in context of structured argumentation
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] -- cites DeLP as a structured argumentation system
- [[Lehtonen_2020_AnswerSetProgrammingApproach]] -- cites DeLP in context of ASP-based argumentation
- [[Li_2017_TwoFormsMinimalityASPIC]] -- cites DeLP's minimality condition on arguments
- [[Thimm_2020_ApproximateReasoningASPICArgumentSampling]] -- cites DeLP as related work
- [[Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks]] -- cites DeLP
- [[Hunter_2021_ProbabilisticArgumentationSurvey]] -- cites DeLP in argumentation survey

### Conceptual Links (not citation-based)
- [[Caminada_2006_IssueReinstatementArgumentation]] -- DeLP's dialectical tree marking (U/D) is closely related to Caminada's three-valued labellings (in/out/undec); the marking procedure is essentially computing a labelling
- [[Modgil_2018_ModifiedASPICFrameworkStructuredArgumentation]] -- ASPIC+ is the main modern successor framework; DeLP's modular comparison criterion maps to ASPIC+'s preference ordering, and DeLP's argument construction maps to ASPIC+'s strict/defeasible rule distinction
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] -- DeLP's supporting/interfering argument concordance conditions relate to Cayrol's bipolar framework treatment of support+attack

### New Leads (Not Yet in Collection)
- Stolzenburg, F. et al. (2003) "Computing generalized specificity" -- formal algorithm for the specificity comparison criterion
- Chesnevar, C. I. et al. (2003) "An abstract machine for defeasible argumentation" -- ODAM implementation details
- Prakken, H. and Sartor, G. (1997) "Argument-based logic programming with defeasible priorities" -- primary comparison system, dialectical proof theory

### Supersedes or Recontextualizes
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] -- DeLP extends and supersedes this predecessor by adding LP integration, dialectical trees, default negation, and a concrete implementation
