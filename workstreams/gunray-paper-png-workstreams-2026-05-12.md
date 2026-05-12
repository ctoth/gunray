# Gunray Paper-PNG Workstreams

Date: 2026-05-12

## Goal

Turn the next paper-backed Gunray candidates into executable workstreams,
using paper page images as the authority and Hypothesis as the main
regression net.

This file defines independent workstreams. Do not treat a passing full suite
as completion for a workstream unless every phase in that workstream is done.

## Paper-Reading Rule

- Use paper page images directly. Do not use `pdftotext` or extracted text as
  the basis for paper claims.
- Every paper claim used in a test or implementation must cite a local page
  image path and visible page number when available.
- If a required paper is not in `papers/`, first run the paper ingestion
  workflow that creates a paper directory and PNGs. Do not substitute web
  snippets or citation metadata for a page-image reread.

## Page Images Already Reread For This Plan

- Diller 2025:
  - `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-002.png`
    defines ASPIC+ arguments, attacks, abstract AFs, extensions, and Example 1.
  - `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-005.png`
    defines approximated/non-approximated predicates and Transformation 2.
  - `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-006.png`
    states Lemma 2, Theorem 2, Example 8, and strict-rule/fact simplification.
- Garcia 2004:
  - `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-012.png`
    introduces comparing arguments and generalized specificity.
  - `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-013.png`
    gives Definition 3.5 and Example 3.5.
  - `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-029.png`
    starts Section 6.1 default negation.
  - `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-030.png`
    gives Definitions 6.1 and 6.2.
  - `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-031.png`
    gives Definition 6.3 and Example 6.1 setup.
- Antoniou 2007:
  - `papers/Antoniou_2007_DefeasibleReasoningSemanticWeb/pngs/page-009.png`
    describes defeasible-logic proof theory and NAF simulation.
  - `papers/Antoniou_2007_DefeasibleReasoningSemanticWeb/pngs/page-010.png`
    defines the ambiguity-blocking vs ambiguity-propagating example.
- Goldszmidt 1992:
  - `papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-001.png`
    defines defeasible and strict conditional sentences and probability
    assignments.
  - `papers/Goldszmidt_1992_DefeasibleStrictConsistency/pngs/page-003.png`
    gives the two-phase consistency procedure and bird/penguin and Nixon
    examples.

## Global Execution Rules

- Work test-first and deletion-first where replacing an existing surface.
- Commit every edit slice atomically with path-limited git commands.
- Use `uv run pytest ...`, `uv run pyright src`, `uv run ruff check`, and
  `uv run ruff format --check`.
- For long full-suite or conformance runs, state the timeout before launching.
- After every passing substantial targeted run, reread the active workstream
  before choosing the next unchecked phase.
- Prefer Hypothesis generators over one-off example tests when the paper
  states an invariant, monotonicity property, equivalence, order property, or
  closure condition.

## Dependency Order

Execute in this order unless the user explicitly chooses a different one:

1. WS-GUN-PNG-1: Stolzenburg specificity paper ingestion and specificity audit.
2. WS-GUN-PNG-2: Diller grounding-as-execution.
3. WS-GUN-PNG-3: Garcia default-negation completion and stress properties.
4. WS-GUN-PNG-4: Antoniou ambiguity-propagation optional semantics.
5. WS-GUN-PNG-5: Spindle / defeasible-logic projection skips adjudication.
6. WS-GUN-PNG-6: Goldszmidt p-consistency / System-Z analysis surface.

Before implementation, prove the order mechanically with a small reusable
order check or a simple script/test that verifies every prerequisite appears
before each dependent workstream in this file.

## WS-GUN-PNG-1: Stolzenburg Specificity Paper And Audit

### Goal

Ground Gunray's shipped `GeneralizedSpecificity` in the algorithmic source
identified by Garcia 2004 and Deagustini 2013: Stolzenburg et al. 2003,
"Computing generalized specificity".

### Paper Prerequisite

This paper is not currently a paper directory. First run the real paper
workflow for exactly:

```text
/research-papers:paper-process Stolzenburg Garcia Chesnevar Simari 2003 Computing generalized specificity
```

If nested skill invocation is unavailable, use the paper-process fallback
helper and follow it literally. Stop if retrieval resolves to the wrong paper.

After processing, reread the generated PNGs and add the exact page image refs
for:

- formal generalized-specificity algorithm;
- activation-set construction;
- edge cases for circular preconditions, specificity incomparability, and
  strict-vs-defeasible boundaries.

### Red Tests

Add `tests/test_stolzenburg_specificity.py`.

Required example tests:

- Garcia 2004 Definition 3.5 / Example 3.5 remains pinned against page images
  `page-012.png` and `page-013.png`.
- Add at least two examples from Stolzenburg page images after paper-process.

Required Hypothesis tests:

- Generate small strict rule DAGs and defeasible rule pairs where the
  antecedent-coverage relation can be computed by an independent oracle.
- Assert `GeneralizedSpecificity.compare` agrees with the oracle.
- Assert strict specificity remains irreflexive, asymmetric, and transitive on
  generated argument triples.
- Assert adding an irrelevant fact predicate cannot change a comparison.
- Assert strict-only empty-rule arguments are never dominated by non-empty
  defeasible arguments.

Expected red:

- At least one oracle-backed edge case should fail if the current Lemma 2.4
  specialization is too narrow or if it lacks a page-backed Stolzenburg anchor.
- If all behavior already passes, the red phase must fail on missing
  Stolzenburg citation/page evidence in code/docs/tests.

### Implementation

- Update citations/docstrings to cite the Stolzenburg page images where the
  shipped algorithm actually relies on them.
- If the oracle exposes a behavior bug, fix `src/gunray/preference.py` without
  adding a compatibility-specificity mode.
- Do not add a second generalized-specificity implementation in production.

### Gates

```powershell
uv run pytest tests/test_specificity.py tests/test_preference.py tests/test_stolzenburg_specificity.py -q
uv run pytest tests/test_superiority.py tests/test_answer.py -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full gate:

```powershell
uv run pytest
uv run pyright src
```

## WS-GUN-PNG-2: Diller Grounding-As-Execution

### Goal

Turn Diller 2025 grounding from inspection-only support into an executable
evaluation route whose answers are equivalent to the current direct DeLP
pipeline on its supported fragment.

### Paper Basis

- Diller `page-002.png`: arguments, attacks, AF extensions, and Example 1.
- Diller `page-005.png`: Definition 12 and Transformation 2.
- Diller `page-006.png`: Lemma 2, Theorem 2, Example 8, and strict/fact
  simplification.

### Red Tests

Add `tests/test_diller_grounding_execution.py`.

Required example tests:

- A theory matching Diller Example 1 shape, asserting generated ground
  instances and answer-equivalence.
- A Transformation-2 case where non-approximated predicates introduce negated
  conditions and suppress a grounding that the naive route would otherwise
  produce.
- A strict/fact simplification case from `page-006.png` where a strict rule
  becomes a fact and is removed from argumentation rules.

Required Hypothesis tests:

- Generate small range-restricted `DefeasibleTheory` instances with bounded
  constants, strict rules, defeasible rules, defeaters, conflicts, and default
  negated bodies.
- Compare answers from the existing direct evaluator and the Diller execution
  route for every generated query atom in the theory language.
- Assert simplification never introduces new non-strict rules.
- Assert every simplified definite fact is derivable in the original strict
  closure.
- Assert no generated ground rule has variables after execution grounding.
- Assert non-approximated predicate computation is monotone under adding
  independent strict/fact-only predicates.

Expected red:

- No public Diller execution route exists.
- Existing `inspect_grounding()` reports simplification but evaluation does not
  consume it as an execution strategy.

### Target Architecture

Add one explicit public execution surface, for example:

```python
class GroundingMode(str, Enum):
    DIRECT = "direct"
    DILLER_SIMPLIFIED = "diller_simplified"
```

and thread it through `DefeasibleEvaluator.evaluate(...)` and
`evaluate_with_trace(...)`.

`DIRECT` keeps the current route. `DILLER_SIMPLIFIED` must evaluate the
simplified grounded theory produced from the same grounder and expose the
grounding inspection in trace.

Do not keep an unowned shadow evaluator. Do not create a separate production
answer projection. The final answer model and trace types remain the public
surface.

### Implementation Notes

- Add a conversion from `GroundingSimplification` back to a normalized
  ground-only `DefeasibleTheory`.
- Preserve source rule IDs and substitutions in `GroundingInspection`.
- Ensure defeater and default-negated bodies survive conversion correctly.
- If a generated case is outside the Diller-supported fragment, reject it with
  an explicit typed error instead of silently falling back to direct mode.

### Gates

```powershell
uv run pytest tests/test_diller_def12.py tests/test_grounding_inspection.py tests/test_grounding_simplification.py tests/test_diller_grounding_execution.py -q
uv run pytest tests/test_defeasible_evaluator.py tests/test_dialectic.py tests/test_answer.py -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full/conformance gate:

```powershell
uv run pytest
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pyright src
```

## WS-GUN-PNG-3: Garcia Default-Negation Completion

### Goal

Audit and complete Garcia 2004 Section 6.1 default negation against page
images, especially Definition 6.1, Definition 6.2, Definition 6.3, and Example
6.1.

### Paper Basis

- Garcia `page-029.png`: default negation is allowed only in defeasible rule
  bodies; `not F` means F is not warranted.
- Garcia `page-030.png`: Definition 6.1 and Definition 6.2 reject
  self-defeating arguments.
- Garcia `page-031.png`: Definition 6.3 makes default-negated literals new
  attack points and gives Example 6.1.

### Red Tests

Add or extend `tests/test_default_negation_garcia.py`.

Required example tests:

- Definition 6.1: default-negated body literals are ignored for derivability
  but must remain assumptions for argument validity and attack.
- Definition 6.2: an argument that derives L while using `not L` in one of its
  own rules is rejected.
- Definition 6.3: an argument for L attacks an opponent argument that depends
  on `not L`.
- Example 6.1: transforming `p <- q, not s` into strong-negation priority rules
  is not equivalent; Gunray must not implement default negation by that
  shortcut.

Required Hypothesis tests:

- Generate small theories with default-negated bodies and assert no accepted
  argument contains a default-negated assumption contradicted by its own strict
  closure.
- Generate attacker theories where adding a warranted L cannot make an
  argument depending on `not L` become warranted.
- Assert default-negated atoms never appear in strict rules; construction or
  parsing must reject them.
- Assert removing an irrelevant default-negated literal preserves answers.

Expected red:

- Current coverage exists for a subset of Definition 6.2/6.3, but Example 6.1
  and property-level stress tests are missing.

### Implementation

- Prefer tightening existing default-negation logic in `arguments.py` and
  `dialectic.py`.
- Delete any old shortcut that treats default negation as strong negation or a
  priority transformation if such a path exists.
- Do not add a new default-negation policy unless the page-image evidence
  requires a semantics split.

### Gates

```powershell
uv run pytest tests/test_default_negation_garcia.py tests/test_defeasible_evaluator.py tests/test_dialectic.py -q
uv run pytest tests/test_workstream_o_gun_garcia_done.py -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full gate:

```powershell
uv run pytest
uv run pyright src
```

## WS-GUN-PNG-4: Antoniou Ambiguity Propagation

### Goal

Make the currently skipped Antoniou ambiguity-propagation family executable as
an optional semantics, or prove by page-image evidence that it remains
out-of-contract and update the skip rationale.

### Paper Basis

- Antoniou `page-009.png`: defeasible-logic proof-theory summary and NAF
  simulation.
- Antoniou `page-010.png`: ambiguity-blocking vs ambiguity-propagating
  example with `pacifist(a)` and dependent `hasGun(a)`.

### Red Tests

First unskip only these fixture IDs locally:

- `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguous_attacker_blocks_only_in_propagating`
- `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguity_propagates_to_downstream_rule`

Add `tests/test_antoniou_ambiguity_policy.py`.

Required example tests:

- Encode the page-010 Quaker/Republican/hasGun example.
- Under Garcia/Simari blocking path, document the current answer.
- Under the new Antoniou propagation path, assert ambiguity propagates to
  dependent conclusions as described on the page image.

Required Hypothesis tests:

- Generate chains `a` vs `~a`, then `a -> b` vs independent `b`, and assert
  propagation blocks downstream acceptance when the upstream literal is
  ambiguous.
- Assert propagation is conservative: if no upstream ambiguity reaches a body,
  propagation and blocking agree.
- Assert adding a priority resolving the upstream conflict makes propagation
  and blocking agree.

Expected red:

- `MarkingPolicy` currently only supports the Garcia/Simari blocking
  dialectical-tree path.
- The fixture family is skipped in `tests/conftest.py`.

### Target Architecture

If supporting Antoniou, add an explicit policy surface, not a hidden behavior
change:

```python
class MarkingPolicy(str, Enum):
    BLOCKING = "blocking"
    ANTONIOU_PROPAGATING = "antoniou_propagating"
```

The default remains Garcia/Simari `BLOCKING`. The new policy is opt-in and
page-cited to Antoniou `page-010.png`.

If page-image reread shows the conformance fixture is not actually the
Antoniou semantics, do not implement it. Instead keep the skip, update its
reason with the page-image contradiction, and add a test that enforces the
skip rationale.

### Gates

```powershell
uv run pytest tests/test_antoniou_ambiguity_policy.py tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pytest tests/test_defeasible_evaluator.py tests/test_dialectic.py tests/test_answer.py -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full gate:

```powershell
uv run pytest
uv run pyright src
```

## WS-GUN-PNG-5: Spindle / Defeasible-Logic Projection Skips

### Goal

Adjudicate the remaining deliberate Spindle-style skips:

- implicit `not_defeasibly` classification for defined-but-unprovable heads;
- partial-dominance superiority where a multi-rule argument is treated as
  stronger despite only partial rule priority coverage.

### Paper Prerequisites

The current Gunray corpus has Antoniou 2007 and Maher 2021, but not the
primary SPINdle / Governatori papers needed to decide these fixture semantics
from page images.

Run paper-process for:

```text
/research-papers:paper-process Lam Governatori 2009 The making of SPINdle
/research-papers:paper-process Governatori Maher 1999 A semantic decomposition of defeasible logics
/research-papers:paper-process Governatori et al. 2004 Argumentation Semantics for Defeasible Logics
```

Stop if any retrieval resolves to the wrong paper. After processing, reread
the generated PNGs and record exact page refs before touching code.

### Red Tests

First unskip only these fixture groups locally:

- `defeasible/basic/spindle_racket_inline_tests::spindle_racket_unsatisfied_antecedent`
- `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_missing_premise_failure`
- `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_missing_premise_theory`
- `defeasible/basic/spindle_racket_inline_tests::spindle_racket_simplified_penguin`
- `defeasible/basic/spindle_racket_test_theories::spindle_racket_penguin_exception`

Add `tests/test_spindle_projection_semantics.py`.

Required Hypothesis tests:

- Generate theories with predicates whose heads are syntactically defined but
  whose bodies are unprovable; assert the chosen projection either classifies
  them consistently or rejects the projection as outside Gunray's semantics.
- Generate multi-rule arguments with partial superiority coverage and assert
  the chosen criterion is either Garcia strict all-pairs dominance or a
  separately named SPINdle dominance policy.
- Assert the default Garcia/Simari path never changes when the SPINdle policy
  is absent.

Expected red:

- The fixture group is currently skipped.
- Current `SuperiorityPreference` requires every left rule to dominate every
  right rule; partial dominance should fail under Garcia page evidence.

### Target Architecture

Do not silently change `SuperiorityPreference`.

If SPINdle semantics is supported, add a separate explicit policy or adapter
surface, for example:

```python
class ProjectionSemantics(str, Enum):
    GARCIA = "garcia"
    SPINDLE = "spindle"
```

The default remains `GARCIA`.

If page-image evidence supports the current skips, keep the skips but replace
generic reasons with primary-paper page refs and add tests asserting the
fixture IDs stay skipped unless `ProjectionSemantics.SPINDLE` exists.

### Gates

```powershell
uv run pytest tests/test_spindle_projection_semantics.py tests/test_superiority.py tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full gate:

```powershell
uv run pytest
uv run pyright src
```

## WS-GUN-PNG-6: Goldszmidt P-Consistency / System-Z Analysis

### Goal

Add a separate analysis surface for Goldszmidt and Pearl 1992 p-consistency /
strict p-entailment over mixed strict and defeasible conditional databases.

This is not a replacement for Garcia/Simari argumentation answers.

### Paper Basis

- Goldszmidt `page-001.png`: defeasible conditional, strict conditional, and
  probability-assignment semantics.
- Goldszmidt `page-003.png`: two-phase consistency procedure, complexity
  theorem, bird/penguin consistency example, and Nixon inconsistency example.

### Red Tests

Add `tests/test_goldszmidt_consistency.py`.

Required example tests:

- Bird/penguin database is p-consistent even with exception defaults.
- Nixon-style database on page 003 is inconsistent in the offending-set sense.
- Strict conditionals are tested only against the strict set when checking
  strict p-entailment.

Required Hypothesis tests:

- Generate small Horn-style conditional databases and assert the consistency
  verdict is order-independent under permutation of defeasible sentences.
- Assert adding a tolerated defeasible sentence to an already consistent layer
  does not make earlier layers depend on input order.
- Assert the procedure returns an offending subset when inconsistent, and that
  every reported offender is drawn from the input.
- Differentially compare against a brute-force truth-assignment oracle for
  tiny propositional vocabularies.

Expected red:

- No `goldszmidt` or p-consistency analysis surface exists in `src/gunray`.

### Target Architecture

Add a new module such as `src/gunray/consistency.py` exposing:

```python
@dataclass(frozen=True, slots=True)
class ConsistencyReport:
    is_consistent: bool
    tolerated_layers: tuple[tuple[str, ...], ...]
    offending_sentence_ids: frozenset[str]

def analyze_p_consistency(database: ConditionalDatabase) -> ConsistencyReport: ...
```

Define a small conditional-database value surface. Do not overload
`DefeasibleEvaluator.evaluate` or `Answer`; this is a different paper
semantics.

### Gates

```powershell
uv run pytest tests/test_goldszmidt_consistency.py -q
uv run pytest tests/test_closure.py tests/test_closure_faithfulness.py -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Full gate:

```powershell
uv run pytest
uv run pyright src
```

## Final Completion Gate For All Workstreams

After all selected workstreams are complete:

```powershell
uv run pytest
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pyright src
uv run ruff check
uv run ruff format --check
```

Then search for stale skip/out-of-contract records:

```powershell
rg -n -F "Unsupported ambiguity-policy regime" tests src README.md ARCHITECTURE.md CITATIONS.md
rg -n -F "Unsupported Spindle projection" tests src README.md ARCHITECTURE.md CITATIONS.md
rg -n -F "partial-dominance" tests src README.md ARCHITECTURE.md CITATIONS.md
rg -n -F "not implemented" tests src README.md ARCHITECTURE.md CITATIONS.md
```

Every remaining hit must be either a current, page-image-cited non-goal or an
active test asserting the explicit policy boundary.
