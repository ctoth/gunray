---
title: "On the Logic of Iterated Belief Revision"
authors: "Adnan Darwiche, Judea Pearl"
year: 1997
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/S0004-3702(96)00038-0"
pages: "1-29"
volume: "89"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-29T03:10:15Z"
---
# On the Logic of Iterated Belief Revision

## One-Sentence Summary

Proposes four additional postulates (C1-C4) beyond AGM to properly regulate iterated belief revision by requiring revision to operate on epistemic states (which encode conditional beliefs and revision strategies) rather than mere belief sets.

## Problem Addressed

The AGM postulates (Alchourron, Gardenfors, Makinson 1985) are too permissive for iterated belief revision: they constrain only what propositions are in the next belief set, not how the epistemic state (conditional beliefs, revision strategy) transforms. This permits counterintuitive responses to sequences of observations. *(p.1-3)*

## Key Contributions

- Demonstrates via concrete examples that AGM-compatible revision operators can produce counterintuitive conditional belief changes *(p.5-6)*
- Proposes modifying AGM to operate on epistemic states rather than belief sets, weakening postulate R4 to R*4 *(p.7)*
- Proposes four new postulates (C1-C4) that constrain how conditional beliefs transform under revision *(p.11)*
- Provides a representation theorem (Theorem 13) characterizing C1-C4 via faithful assignments on pre-orders *(p.14)*
- Constructs a concrete revision operator (Spohn-based bullet operator) satisfying all postulates *(p.15)*
- Shows C1-C4 are independent of each other and of the modified AGM postulates *(p.16)*
- Analyzes absolute minimization of conditional belief change (postulates C5, C6) and shows it is too strong *(p.16-17)*
- Introduces degree of acceptance for evidence-strength-qualified versions of the postulates *(p.18)*

## Study Design

*Non-empirical paper: pure theory, proofs, formal postulates.*

## Methodology

The paper proceeds by:
1. Reviewing the AGM/KM framework and its representation theorem (Katsuno-Mendelzon) *(p.4-5)*
2. Constructing counterexamples showing AGM permits counterintuitive iterated behavior *(p.5-6)*
3. Broadening the framework from belief sets to epistemic states *(p.6-8)*
4. Analyzing minimal change of conditional beliefs via postulate CB *(p.8-10)*
5. Proposing four postulates C1-C4 that selectively preserve conditional beliefs *(p.10-11)*
6. Providing representation theorems and a concrete satisfying operator *(p.13-15)*
7. Analyzing stronger postulates C5-C6 and showing they are too restrictive *(p.16-17)*

## Key Equations / Statistical Models

### KM Postulates (propositional reformulation of AGM)

$(R1)\ \psi \circ \mu$ implies $\mu$. *(p.4)*

$(R2)$ If $\psi \wedge \mu$ is satisfiable, then $\psi \circ \mu \equiv \psi \wedge \mu$. *(p.4)*

$(R3)$ If $\mu$ is satisfiable, then $\psi \circ \mu$ is also satisfiable. *(p.4)*

$(R4)$ If $\psi_1 \equiv \psi_2$ and $\mu_1 \equiv \mu_2$, then $\psi_1 \circ \mu_1 \equiv \psi_2 \circ \mu_2$. *(p.4)*

$(R5)\ (\psi \circ \mu) \wedge \phi$ implies $\psi \circ (\mu \wedge \phi)$. *(p.4)*

$(R6)$ If $(\psi \circ \mu) \wedge \phi$ is satisfiable, then $\psi \circ (\mu \wedge \phi)$ implies $(\psi \circ \mu) \wedge \phi$. *(p.4)*

### Modified Postulates for Epistemic States

$(R^*4)$ If $\Psi_1 = \Psi_2$ and $\mu_1 \equiv \mu_2$, then $\Psi_1 \circ \mu_1 \equiv \Psi_2 \circ \mu_2$. *(p.7)*

Where: Revision now operates on epistemic states $\Psi$ (not belief sets $\psi$), and the result $\Psi \circ \mu$ is also an epistemic state. $Bel(\Psi)$ denotes the belief set associated with epistemic state $\Psi$.

Key weakening: R*4 requires identity of epistemic states ($\Psi_1 = \Psi_2$), not merely equivalence of belief sets ($\psi_1 \equiv \psi_2$). This allows two agents with the same beliefs but different revision strategies to revise differently. *(p.7)*

### KM Representation Theorem (extended)

$$
Mods(\Psi \circ \mu) = \min(Mods(\mu), \leqslant_\Psi)
$$

Where: $Mods(\mu)$ is the set of worlds satisfying $\mu$; $\leqslant_\Psi$ is the total pre-order on worlds associated with epistemic state $\Psi$ via a faithful assignment.
*(p.8)*

### The Four DP Postulates (C1-C4)

$(C1)$ If $\alpha \models \mu$, then $(\Psi \circ \mu) \circ \alpha \equiv \Psi \circ \alpha$. *(p.11)*

*Explanation:* When two pieces of evidence arrive, the second being more specific than the first, the first is redundant; the second evidence alone would yield the same belief set. Equivalently: learning full information $\mu$ should wash out any previously learned partial information. *(p.11)*

$(C2)$ If $\alpha \models \neg\mu$, then $(\Psi \circ \mu) \circ \alpha \equiv \Psi \circ \alpha$. *(p.11)*

*Explanation:* When two contradictory pieces of evidence arrive, the last one prevails; the second evidence alone would yield the same belief set. *(p.11)*

$(C3)$ If $\Psi \circ \alpha \models \mu$, then $(\Psi \circ \mu) \circ \alpha \models \mu$. *(p.11)*

*Explanation:* An evidence $\mu$ should be retained after accommodating a more recent evidence $\alpha$ that implies $\mu$ given current beliefs. *(p.11)*

$(C4)$ If $\Psi \circ \alpha \not\models \neg\mu$, then $(\Psi \circ \mu) \circ \alpha \not\models \neg\mu$. *(p.11)*

*Explanation:* No evidence can contribute to its own demise. If $\mu$ is not contradicted after seeing $\alpha$, then it should remain uncontradicted when $\alpha$ is preceded by $\mu$ itself. *(p.11)*

### Conditional Belief Reformulations of C1-C4

$(C1')$ If $\alpha \models \mu$, then $\Psi \models \beta|\alpha$ iff $\Psi \circ \mu \models \beta|\alpha$. *(p.11)*

*Explanation:* Accommodating evidence $\mu$ should not perturb any conditional beliefs that are conditioned on a premise more specific than $\mu$. *(p.11)*

$(C2')$ If $\alpha \models \neg\mu$, then $\Psi \models \beta|\alpha$ iff $\Psi \circ \mu \models \beta|\alpha$. *(p.11)*

*Explanation:* Accommodating evidence $\mu$ should not perturb any conditional beliefs that are conditioned on a premise that contradicts $\mu$. *(p.11)*

$(C3')$ If $\Psi \models \mu|\alpha$, then $\Psi \circ \mu \models \mu|\alpha$. *(p.11)*

*Explanation:* The conditional $\mu|\alpha$ should not be given up after accommodating evidence $\mu$. *(p.11)*

$(C4')$ If $\Psi \not\models \neg\mu|\alpha$, then $\Psi \circ \mu \not\models \neg\mu|\alpha$. *(p.11)*

*Explanation:* The conditional $\neg\mu|\alpha$ should not be acquired after accommodating evidence $\mu$. *(p.11)*

### Representation Theorem for C1-C4

**Theorem 13.** A revision operator satisfies $(R^*1)-(R^*6)$ and $(C1)-(C4)$ iff its corresponding faithful assignment satisfies: *(p.14)*

$(CR1)$ If $\omega_1 \models \mu$ and $\omega_2 \models \mu$, then $\omega_1 \leqslant_\Psi \omega_2$ iff $\omega_1 \leqslant_{\Psi \circ \mu} \omega_2$.

$(CR2)$ If $\omega_1 \models \neg\mu$ and $\omega_2 \models \neg\mu$, then $\omega_1 \leqslant_\Psi \omega_2$ iff $\omega_1 \leqslant_{\Psi \circ \mu} \omega_2$.

$(CR3)$ If $\omega_1 \models \mu$ and $\omega_2 \models \neg\mu$, then $\omega_1 <_\Psi \omega_2$ only if $\omega_1 <_{\Psi \circ \mu} \omega_2$.

$(CR4)$ If $\omega_1 \models \mu$ and $\omega_2 \models \neg\mu$, then $\omega_1 \leqslant_\Psi \omega_2$ only if $\omega_1 \leqslant_{\Psi \circ \mu} \omega_2$.

*Meaning:* C1-C4 constrain only some parts of the pre-order $\leqslant_\Psi$ into the pre-order $\leqslant_{\Psi \circ \mu}$. CR1 and CR2 preserve relative ordering within $\mu$-worlds and within $\neg\mu$-worlds. CR3 and CR4 preserve strict/non-strict ordering between $\mu$-worlds and $\neg\mu$-worlds. The postulates do NOT constrain the relative ordering of worlds when $\omega_1 \models \neg\mu$ and $\omega_2 \models \mu$ (i.e., when a non-$\mu$ world is compared to a $\mu$-world). *(p.14)*

### Spohn's (mu,m)-Conditionalization

$$
\kappa_{(\mu,m)}(\omega) = \begin{cases} \kappa(\omega) - \kappa(\mu), & \text{if } \omega \models \mu; \\ \kappa(\omega) - \kappa(\neg\mu) + m, & \text{if } \omega \models \neg\mu. \end{cases}
$$

Where: $\kappa$ is an ordinal conditional function (ranking) mapping worlds to non-negative integers; $\kappa(\mu) = \min_{\omega \models \mu} \kappa(\omega)$; $m$ is the post-revision degree of plausibility of $\mu$; smaller rank = more plausible. *(p.15)*

### The Bullet Revision Operator

$$
(\kappa \bullet \mu)(\omega) = \begin{cases} \kappa(\omega) - \kappa(\mu), & \text{if } \omega \models \mu; \\ \kappa(\omega) + 1, & \text{if } \omega \models \neg\mu. \end{cases}
$$

Where: This is $(\mu, m)$-conditionalization with $m = \kappa(\neg\mu) + 1$, ensuring the post-revision degree of plausibility of $\mu$ is one degree higher than its current value.
*(p.15)*

**Theorem 14.** The revision operator $\bullet$ satisfies postulates $(R^*1)-(R^*6)$ and $(C1)-(C4)$. *(p.15)*

### The Diamond Operator (for independence proof)

$$
(\kappa \diamond \mu)(\omega) = \begin{cases} \kappa(\omega) - \kappa(\mu), & \text{if } \omega \models \mu; \\ \kappa(\omega) + 1, & \text{if } \omega \models \neg\mu,\ \kappa(\omega) < 2; \\ \kappa(\omega) - 1, & \text{if } \omega \models \neg\mu,\ \kappa(\omega) \geqslant 2. \end{cases}
$$

Where: This operator satisfies $(R^*1)-(R^*6)$ and $(C1)$ but NOT $(C3)$ or $(C4)$, proving the independence of C3 and C4 from C1 (Theorem 15). *(p.26)*

### Postulates C5 and C6 (Absolute Minimization)

$(C5)$ If $\Psi \circ \mu \models \neg\alpha$ and $\Psi \circ \alpha \not\models \mu$, then $(\Psi \circ \mu) \circ \alpha \not\models \mu$. *(p.16)*

*Explanation:* If evidence $\mu$ rules out the premise $\alpha$, then the conditional belief $\mu|\alpha$ should not be acquired after observing $\mu$. *(p.16)*

$(C6)$ If $\Psi \circ \mu \models \neg\alpha$ and $\Psi \circ \alpha \models \neg\mu$, then $(\Psi \circ \mu) \circ \alpha \models \neg\mu$. *(p.16)*

*Explanation:* If evidence $\mu$ rules out the premise $\alpha$, then the conditional belief $\neg\mu|\alpha$ should not be given up after observing $\mu$. *(p.16)*

**Theorem 16.** A revision operator satisfies $(R^*1)-(R^*6)$, $(C5)$, and $(C6)$ iff the operator and its corresponding faithful assignment satisfy CR5 and CR6. *(p.16)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Post-revision plausibility degree | m | ordinal | kappa(neg mu)+1 for bullet | >= 0 | p.15 | In (mu,m)-conditionalization |
| World plausibility rank | kappa(omega) | ordinal | - | >= 0 | p.14 | 0 = most plausible |
| Proposition plausibility rank | kappa(mu) | ordinal | - | >= 0 | p.14 | min over satisfying worlds |

## Methods & Implementation Details

- Belief set: deductively closed set of propositions, represented by a sentence $\psi$ in propositional language $\mathcal{L}$ *(p.4)*
- Epistemic state $\Psi$: contains belief set $Bel(\Psi)$ plus all information needed for coherent reasoning, including conditional beliefs and revision strategy *(p.2)*
- Faithful assignment: maps each epistemic state $\Psi$ to a total pre-order $\leqslant_\Psi$ on worlds $W$ such that: (1) $\omega_1, \omega_2 \models \Psi$ only if $\omega_1 =_\Psi \omega_2$; (2) $\omega_1 \models \Psi$ and $\omega_2 \not\models \Psi$ only if $\omega_1 <_\Psi \omega_2$; (3) $\Psi = \Phi$ only if $\leqslant_\Psi = \leqslant_\Phi$ *(p.8)*
- Ordinal conditional function (ranking) $\kappa$: maps worlds to non-negative integers (ordinals); rank 0 = most plausible; $\kappa(\mu) = \min_{\omega \models \mu} \kappa(\omega)$; accepted propositions = those true in all rank-0 worlds: $Mods(Bel(\kappa)) = \{\omega : \kappa(\omega) = 0\}$ *(p.14-15)*
- The bullet operator $\bullet$ is a specific instance of Spohn's $(\mu,m)$-conditionalization that: (a) shifts all $\mu$-worlds down by $\kappa(\mu)$ (normalizing to 0), (b) shifts all $\neg\mu$-worlds up by 1 *(p.15)*
- Conditioning is a shifting process: relative order within $Mods(\mu)$ preserved, relative order within $Mods(\neg\mu)$ preserved, all $\mu$-worlds become more plausible than all $\neg\mu$-worlds *(p.26)*

## Figures of Interest

- **Table A.1 (p.19):** AGM-compatible operator contradicting postulate C1 (adder/multiplier example)
- **Table A.2 (p.19):** AGM-compatible operator contradicting postulate C2 (smart/rich example)
- **Table A.3 (p.20):** AGM-compatible operator contradicting postulate C3 (bird/flies example)
- **Table A.4 (p.20):** AGM-compatible operator contradicting postulate C4 (shining_sun/nice_day example)
- **Table B.1 (p.27):** Scenario where diamond operator violates C3
- **Table B.2 (p.27):** Scenario where diamond operator violates C4

## Results Summary

1. AGM postulates R1-R6 are too weak for iterated revision because they only constrain belief sets, not epistemic states *(p.1-3)*
2. The modified postulates R*1-R*6 (operating on epistemic states) have the same representation theorem as KM, just with a stronger identity condition *(p.7-8)*
3. Postulate CB (absolute minimization of conditional belief change) rules out counterintuitive examples but is itself too strong — it leads to counterintuitive results by insisting on preserving ALL conditional beliefs *(p.8-10)*
4. The four postulates C1-C4 selectively preserve conditional beliefs and avoid the problems of both AGM (too weak) and CB (too strong) *(p.11)*
5. C1-C4 correspond to preserving parts of the pre-order: within-$\mu$-world ordering (CR1), within-$\neg\mu$-world ordering (CR2), strict $\mu$-over-$\neg\mu$ ordering (CR3), non-strict $\mu$-over-$\neg\mu$ ordering (CR4) *(p.14)*
6. The Spohn-based bullet operator satisfies all postulates and is compatible with qualitative probabilistic conditioning (Jeffrey's rule) *(p.14-15)*
7. C3 and C4 are independent of C1 — there exists an operator (diamond) satisfying R*1-R*6 and C1 but not C3 or C4 *(p.16)*
8. Stronger postulates C5-C6 (absolute minimization) prohibit some legitimate conditional belief changes *(p.16-17)*
9. AGM postulates together with C1 are sufficient to imply C3 and C4 IF revisions depend only on the current belief set (R4 instead of R*4), but this requirement is itself too restrictive *(p.16)*

## Limitations

- The postulates are qualitative — they do not account for the strength of evidence triggering the change. The authors note this as important future work. *(p.17-18)*
- Postulates C5 and C6 (which would give absolute minimization) are shown to be too strong, prohibiting legitimate changes *(p.16-17)*
- The framework assumes a single revision operator applied uniformly; the authors suggest investigating sequences of operators $\circ_0, \circ_1, \circ_2, \ldots$ with different evidence strengths *(p.17-18)*
- No treatment of contraction (belief removal) — only revision (belief accommodation) is addressed

## Arguments Against Prior Work

- **AGM framework (Alchourron, Gardenfors, Makinson 1985):** Too weak for iterated revision because postulates are one-step only and cannot regulate how conditional beliefs transform *(p.1-3)*
- **Gardenfors' attempt** to include conditional beliefs as propositional beliefs: leads to triviality result [8, pp. 156-166] *(p.3)*
- **Boutilier's natural revision:** Equivalent to postulate CB (absolute change minimization), which preserves ALL conditional beliefs — shown to be too strong, leading to counterintuitive results *(p.3, 9-10)*
- **Postulate R4 (belief-set-based identity):** Too restrictive — requires revision to depend only on current belief set, preventing two agents with same beliefs but different revision strategies from diverging *(p.7)*
- **Freund and Lehmann [6]:** Showed that R1-R6 and C2 clash, but this is only valid under R4 (not R*4) *(p.7)*

## Design Rationale

- **Epistemic states over belief sets:** Belief sets lose information about conditional beliefs and revision strategy. Two agents with identical beliefs but different evidential histories should be allowed to revise differently. *(p.2, 7)*
- **Selective preservation (C1-C4) over absolute preservation (CB):** CB forces preservation of all conditional beliefs, but some changes are legitimate — when new evidence supports a conditional belief, that belief may appropriately change. C1-C4 preserve only those conditional beliefs that should not be affected by the evidence. *(p.10-11)*
- **Weakening R4 to R*4:** Necessary to allow revision to be a function of epistemic states, not just belief sets. Without this, C3 and C4 become derivable from C1 alone, which is too restrictive. *(p.7, 16)*
- **Choice of Spohn's framework:** Ordinal conditional functions provide the right level of abstraction — qualitative version of probabilistic conditioning that satisfies all proposed postulates. *(p.14-15)*

## Testable Properties

- **C1:** If $\alpha \models \mu$, then $(\Psi \circ \mu) \circ \alpha \equiv \Psi \circ \alpha$ — more specific evidence makes prior general evidence redundant *(p.11)*
- **C2:** If $\alpha \models \neg\mu$, then $(\Psi \circ \mu) \circ \alpha \equiv \Psi \circ \alpha$ — contradicting later evidence overrides earlier evidence *(p.11)*
- **C3:** If $\Psi \circ \alpha \models \mu$, then $(\Psi \circ \mu) \circ \alpha \models \mu$ — evidence retained when subsequent evidence supports it *(p.11)*
- **C4:** If $\Psi \circ \alpha \not\models \neg\mu$, then $(\Psi \circ \mu) \circ \alpha \not\models \neg\mu$ — evidence cannot contribute to its own demise *(p.11)*
- **CR1-CR4:** Pre-order preservation conditions are directly testable on any ranking-based revision operator *(p.14)*
- **Bullet operator:** For any ranking $\kappa$ and proposition $\mu$: $(\kappa \bullet \mu)(\omega) = \kappa(\omega) - \kappa(\mu)$ if $\omega \models \mu$; $\kappa(\omega) + 1$ if $\omega \models \neg\mu$ *(p.15)*
- **Independence:** C3 and C4 are NOT derivable from R*1-R*6 + C1 (diamond operator counterexample) *(p.16, 26-27)*
- **C1 sufficient with R4:** Under R4 (not R*4), C1 alone implies C3 and C4 *(p.16)*

## Relevance to Project

This paper is critical for propstore's belief revision operations. The project's CLAUDE.md references Dixon 1993 (ATMS context switching = AGM operations) as aspirational. Darwiche-Pearl 1997 shows that AGM alone is insufficient for iterated revision — precisely the situation when processing a sequence of git commits or claim updates. The four DP postulates (C1-C4) provide the correctness criteria for any iterated revision operation in the system:

- **Git commits as iterated revisions:** Each commit revises the epistemic state of the repository. C1-C4 regulate how conditional beliefs (e.g., claim stances conditional on contexts) should transform across a sequence of commits.
- **Epistemic states vs belief sets:** The project's non-commitment discipline already aligns with operating on epistemic states rather than collapsing to belief sets — the sidecar stores the full epistemic state, not just current beliefs.
- **Spohn rankings as plausibility orderings:** The ordinal conditional functions map naturally to the project's existing preference orderings in argumentation.
- **CR1-CR4 as implementation constraints:** Any revision operator implemented in the system should satisfy these pre-order preservation conditions.

## Open Questions

- [ ] How do C1-C4 interact with the ATMS label-based representation used in the project?
- [ ] Can Spohn's (mu,m)-conditionalization be implemented using the existing opinion algebra (Josang 2001)?
- [ ] What is the relationship between evidence strength (Section 8's future work) and the uncertainty parameter u in subjective logic?
- [ ] Should the project implement the bullet operator specifically, or a more general (mu,m)-conditionalization with configurable m?

## Related Work Worth Reading

- Spohn [23, 24]: Ordinal conditional functions — the mathematical framework underlying the bullet operator -> NOW IN COLLECTION: [[Spohn_1988_OrdinalConditionalFunctionsDynamic]]
- Boutilier [3, 4]: Natural revision — the absolute minimization approach that C1-C4 improve upon
- Katsuno and Mendelzon [17]: The KM representation theorem that this paper extends
- Lehmann [18]: Belief revision revised — related approach to iterated revision
- Goldszimdt and Pearl [12, 13]: Qualitative probabilities for default reasoning — connects rankings to probabilistic reasoning

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — cited as [1,2]; the AGM postulates that this paper extends and shows are insufficient for iterated revision
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — cited as [8]; epistemic entrenchment orderings that this paper shows cannot be constrained by one-step postulates alone
- [[Reiter_1980_DefaultReasoning]] — cited as [21]; default logic as one of the frameworks where belief change arises

### Now in Collection (previously listed as leads)
- [[Spohn_1988_OrdinalConditionalFunctionsDynamic]] — Defines ordinal conditional functions (OCFs/kappa-functions) as qualitative epistemic state representations mapping propositions to ordinal disbelief grades. OCFs support reversible A_n-conditionalization with firmness parameter n, prove commutativity of conditionalization, and establish independence properties paralleling probability theory. This is the mathematical foundation for the bullet operator and (mu,m)-conditionalization used in this paper.

### New Leads (Not Yet in Collection)
- Boutilier (1996) — "Iterated revision and minimal revision of conditional beliefs" — the natural revision approach that C1-C4 improve upon
- Katsuno & Mendelzon (1991) — "Propositional knowledge base revision and minimal change" — the KM representation theorem extended here

### Supersedes or Recontextualizes
- [[Alchourron_1985_TheoryChange]] — this paper shows AGM postulates are necessary but insufficient for iterated revision; C1-C4 are the additional constraints needed
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — epistemic entrenchment alone cannot regulate iterated revision; the ordering transforms must also be constrained

### Cited By (in Collection)
- [[Bonanno_2010_BeliefChangeBranchingTime]] — explicitly discusses DP postulates (DP1-DP4), shows they are expressible in ternary belief revision functions, and proves AGM-consistency imposes only weak constraints on iterated revision
- [[Baumann_2015_AGMMeetsAbstractArgumentation]] — cites in context of AGM revision for argumentation frameworks

### Conceptual Links (not citation-based)
- [[Dixon_1993_ATMSandAGM]] — Dixon proves ATMS context switching = AGM operations; Darwiche-Pearl shows AGM alone is insufficient for iterated revision. Together: ATMS-based systems need additional constraints (C1-C4) beyond what Dixon's AGM bridge provides when processing sequences of context switches.
- [[Shapiro_1998_BeliefRevisionTMS]] — Shapiro bridges TMS and AGM traditions; Darwiche-Pearl extends AGM for iteration. The TMS tradition's justification structures may naturally encode the epistemic state information that Darwiche-Pearl shows is needed beyond belief sets.
- [[Chan_2005_DistanceMeasureBoundingProbabilistic]] — Chan & Darwiche's CD-distance bounds probability ratio changes under revision; this paper's Spohn rankings are a qualitative version of the same probabilistic conditioning framework. CD-distance could provide a quantitative metric for the qualitative pre-order changes regulated by CR1-CR4.
- [[Rotstein_2008_ArgumentTheoryChangeRevision]] — adapts AGM-style revision to argumentation frameworks with warrant-prioritized operators. The DP postulates (C1-C4) should apply as additional correctness criteria for iterated argument revision.
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — surveys argumentation dynamics including revision; DP postulates provide the formal criteria for when such dynamics are iterated.
- [[Goldszmidt_1992_DefeasibleStrictConsistency]] — **Strong.** Goldszmidt & Pearl's consistency criterion for mixed defeasible/strict databases determines *when* revision is needed (database is inconsistent); Darwiche & Pearl's iterated revision postulates govern *how* to revise. The System Z / ranking function equivalence in Goldszmidt & Pearl connects directly to the Spohn ranking functions that Darwiche & Pearl use as their canonical epistemic state representation.
