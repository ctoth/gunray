# Citations

Papers anchoring the implementation. Each entry names what Gunray
uses from the paper and where that use lives. Source comments cite
definitions and page numbers; grep `src/` for `Def 3.1`, `Def 4.7`,
`Procedure 5.1`, `Lemma 2.4`, `Algorithm 3`.

## Load-bearing (cited in `src/`)

### García & Simari 2004 — *Defeasible Logic Programming*
The DeLP pipeline Gunray implements verbatim. Uses:

- Def 3.1 (argument well-formedness) — [`arguments.py`](src/gunray/arguments.py)
- Def 3.3 (literal disagreement, facts-plus-rules) — [`disagreement.py`](src/gunray/disagreement.py)
- Def 3.4 (counter-argument) — [`dialectic.py`](src/gunray/dialectic.py)
- Def 4.1 / 4.2 (proper and blocking defeaters) — [`dialectic.py`](src/gunray/dialectic.py), [`preference.py`](src/gunray/preference.py)
- Def 4.7 (acceptable argumentation line — concordance, sub-argument exclusion, block-on-block ban) — [`dialectic.py`](src/gunray/dialectic.py)
- Def 5.1 (dialectical tree) — [`dialectic.py`](src/gunray/dialectic.py)
- Procedure 5.1 (post-order U/D marking) — [`dialectic.py`](src/gunray/dialectic.py)
- Def 5.3 (four-valued answer YES/NO/UNDECIDED/UNKNOWN) — [`answer.py`](src/gunray/answer.py)
- §4.1 (user superiority, composed ahead of specificity) — [`preference.py`](src/gunray/preference.py)
- §6 p. 29 (explanation prose, reason-per-edge) — [`dialectic.py`](src/gunray/dialectic.py) `explain()`
- §6.2 p. 32 (presumptions as empty-body defeasible rules, `h -< true`) — [`schema.py`](src/gunray/schema.py), [`parser.py`](src/gunray/parser.py)

### Simari & Loui 1992 — *A Mathematical Treatment of Defeasible Reasoning*
Generalized specificity and the argument-structure foundations García
2004 builds on. Uses:

- Def 2.2 (argument structure, aligned with García Def 3.1) — [`arguments.py`](src/gunray/arguments.py)
- Def 2.6 (strict specificity) and Lemma 2.4 (generalized specificity) — [`preference.py`](src/gunray/preference.py) `GeneralizedSpecificity`
- Implementation Details p. 10 (`An(T)` activation set construction) — [`preference.py`](src/gunray/preference.py)

### Morris, Ross & Meyer 2020 — *Defeasible Disjunctive Datalog*
KLM closure lifted to Datalog+. Uses:

- Algorithm 3 p. 150 (rational closure) — [`closure.py`](src/gunray/closure.py)
- Algorithm 4 p. 151 (lexicographic closure) — [`closure.py`](src/gunray/closure.py)
- §subset-ranking pp. 156–158 (relevant closure) — [`closure.py`](src/gunray/closure.py)
- Restatement of KLM properties for Datalog+ (`Or` postulate surface) — [`closure.py`](src/gunray/closure.py)

### Kraus, Lehmann & Magidor 1990 — *Nonmonotonic Reasoning, Preferential Models and Cumulative Logics*
*Artificial Intelligence* 44, 167–207. DOI: [10.1016/0004-3702(90)90101-5](https://doi.org/10.1016/0004-3702(90)90101-5).
Source of the KLM postulates. Gunray's closure engine implements the
`Or` disjunction postulate directly — [`closure.py`](src/gunray/closure.py)
cites KLM 1990 via Morris/Ross/Meyer 2020's Datalog+ restatement.
`tests/test_closure_faithfulness.py` carries the Hypothesis comparison
against the ranked-world reference evaluator for small generated
theories, including the public `Or` postulate check.

### Apt, Blair & Walker 1988 — *Towards a Theory of Declarative Knowledge*
Stratified-negation safety for Datalog. Uses:

- Safety condition: every variable in a negated body literal must be
  bound by a positive body literal — [`schema.py`](src/gunray/schema.py)
  `NegationSemantics.SAFE`, `SafetyViolationError`
- Stratification construction (Tarjan SCC + Kahn topological sort) —
  [`stratify.py`](src/gunray/stratify.py)

### Ivliev, Gerlach, Meusel, Steinberg & Krötzsch 2024 — *Nemo: Your Friendly and Versatile Rule Reasoning Toolkit*
KR 2024. DOI: [10.24963/kr.2024/70](https://doi.org/10.24963/kr.2024/70).
The existential reading of variables in negated literals over the
active Herbrand universe — [`schema.py`](src/gunray/schema.py)
`NegationSemantics.NEMO`. Used for the conformance suite's Nemo
fixtures; disagrees with `SAFE` on meaningful cases.

### Nute / Antoniou — defeater-kind reading
A defeater rule whose head disagrees with but is not complementary to
the attacked literal participates only as a pure attacker, not as a
supporter of its own head. Cited in [`arguments.py`](src/gunray/arguments.py),
[`defeasible.py`](src/gunray/defeasible.py), and [`dialectic.py`](src/gunray/dialectic.py)
as the "Nute/Antoniou reading"; see `notes/b2_defeater_participation.md`.
The former section-level `not_defeasibly` projection derived from this
reading is superseded by Garcia & Simari 2004 Def 5.3 `yes` / `no` /
`undecided` / `unknown`; defeater participation is now inspectable on
the trace instead of encoded as a model section.

### Diller, Geilke, Gottifredi, García & Simari 2025 — *Grounding Rule-Based Argumentation in Datalog*
Gunray uses the paper's Datalog-grounding contract for the public
grounding inspection surface:

- Definition 9 p. 3 (ground substitutions are those whose rule bodies
  hold in the least Datalog model) — [`_internal.py`](src/gunray/_internal.py)
  computes the shared positive grounding model and substitutions.
- Algorithm 2 p. 7 (ASPIC+-specific grounding simplifications) —
  [`grounding.py`](src/gunray/grounding.py) implements the conservative
  strict/fact-only fragment in `_simplify_strict_fact_grounding`.
- Deliberate carve-out: Gunray does not remove defeasible or defeater
  ground rules during this simplification; it only resolves strict
  rules whose bodies are already definite facts.

## Contextual (shaped design, not directly implemented)

### Darwiche & Pearl 1997 — *On the Logic of Iterated Belief Revision*
Four postulates (C1–C4) beyond AGM for iterated revision. Informed
thinking about sequential updates over defeasible theories but no
belief-revision operator ships in this engine.

### Goldszmidt & Pearl 1992 — *On the Consistency of Defeasible Databases*
Tolerance-based consistency for mixed strict/defeasible databases,
equivalent to System Z preferential semantics. Background for the
Π-consistency check in the strict-only fast path, though the actual
check is a direct `{h, ~h}` derivation test, not a tolerance partition.

### Deagustini, Dalibón, Gottifredi, Falappa, Chesñevar & Simari 2013 — *Relational Databases as a Massive Information Source for Defeasible Argumentation*
DB-DeLP architecture connecting DeLP to relational databases via
retrieval functions. Architectural reference for future data-source
bridges; nothing in the current engine depends on it.

### Bozzato, Eiter & Serafini 2020 — *Enhancing Web Ontologies with Defeasible Axioms in Datalog Rewritings*
Datalog translation for DL-Lite_R with justifiable-exception
semantics. Read for the defeasible-DL landscape; Gunray is not a
description-logic system.

### Maher 2021 — *Relating Defeasible Logic to Datalog*
Compilation of defeasible logic D(1,1) into Datalog-with-negation
via metaprograms and unfold/fold. Alternative compilation path
considered and not taken; Gunray stays with the García 2004 direct
pipeline.

## Out-of-contract (explicitly not implemented)

### Antoniou 2007 — *Defeasible Reasoning on the Semantic Web*
DR-Prolog's ambiguity-propagating variant (c7' meta-rule) has no
seam in the García 2004 dialectical-tree pipeline. `Policy.PROPAGATING`
was deprecated — see `notes/policy_propagating_fate.md`. The
conformance fixtures exercising it are marked out-of-contract, not
silently counted as passes. Antoniou's defeater-kind reading *is*
used (see Nute/Antoniou above); the ambiguity-propagating semantics
is not.
