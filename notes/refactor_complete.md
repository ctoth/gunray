# Refactor complete — historical record

**Date**: 2026-04-14 (B3-close)
**Commit range**: `5078df5..a1afcf2` — 86 commits.
**Final gunray remote SHA**: `a1afcf2`.
**Final propstore SHA**: `5f8f43d`.

## Goal

Rebuild gunray's defeasible evaluator as a verbatim implementation
of the Garcia & Simari 2004 argument / dialectical-tree pipeline,
eliminate downstream hacks in propstore, and re-establish paper
citations as first-class documentation in the source tree.

## Context and paper anchors

The pre-refactor `defeasible.py` was a 784-line classifier built
from ad-hoc "reason codes" and `supported_only_by_unproved_bodies`
heuristics. It carried no citation of Garcia 2004 or Simari 1992
and could not justify its own classifications paper-textually.
Downstream propstore had a `_split_section_predicate` hack that
stripped `~` from negated section keys because gunray's
sectioning contract was inconsistent.

The target pipeline is Garcia 2004 §3–§5 verbatim:

- Def 3.1: argument structure `⟨A, h⟩`.
- Def 3.4: counter-argument at sub-argument.
- Def 4.1 / 4.2: proper / blocking defeater.
- Def 4.7: acceptable argumentation line (concordance,
  sub-argument exclusion, block-on-block ban).
- Def 5.1: dialectical tree.
- Proc 5.1: U/D marking.
- Def 5.3: four-valued answer.
- §4.1: rule priority.

With Simari 1992 Lemma 2.4 as the generalized specificity
fallback when explicit superiority is silent.

## Commit range

```
git log --oneline 5078df5..a1afcf2
```

86 commits on gunray master between the pre-refactor baseline
(`5078df5 fix(defeasible): classify partially grounded heads`)
and the B3-close tip (`a1afcf2 fix(packaging): add py.typed
marker per PEP 561`). Grouped by block:

- P0.1 / P0.1.5 / P0.1.6 / P0.2 — adapter TypeError fix and
  cptrload perf fix (baseline repair).
- B1.1–B1.9 — consolidated scout, scorched-earth, disagreement
  + build_arguments, defeat/tree/Def 4.7, render + answer,
  evaluator wiring + nests_in_trees, analyst, adversary,
  yellow cleanup.
- B2.1–B2.6 — policy-usage scout, generalized specificity,
  policy routing, defeater participation, superiority +
  composite preference, composite first-fire fix and close.
- B3.1–B3.4 — propstore scout, propstore direct replacement,
  docs + cleanup, final verifier (this dispatch).

## LOC deltas (`src/gunray/`)

Baseline from `notes/refactor_baseline.md` §4 (pre-refactor,
`5078df5`):

```
     30 src/gunray/__init__.py
     59 src/gunray/adapter.py
     39 src/gunray/ambiguity.py
    699 src/gunray/closure.py
      9 src/gunray/compile.py
    241 src/gunray/compiled.py
    141 src/gunray/conformance_adapter.py
    784 src/gunray/defeasible.py
     39 src/gunray/errors.py
    732 src/gunray/evaluator.py
    415 src/gunray/parser.py
     80 src/gunray/relation.py
     83 src/gunray/schema.py
     79 src/gunray/semantics.py
    116 src/gunray/stratify.py
      9 src/gunray/tolerance.py
    218 src/gunray/trace.py
    103 src/gunray/types.py
   3876 total
```

Post-refactor (`a1afcf2`):

```
     61 src/gunray/__init__.py
     71 src/gunray/adapter.py
     21 src/gunray/answer.py
    410 src/gunray/arguments.py
    699 src/gunray/closure.py
    241 src/gunray/compiled.py
    141 src/gunray/conformance_adapter.py
    339 src/gunray/defeasible.py
    548 src/gunray/dialectic.py
     87 src/gunray/disagreement.py
     39 src/gunray/errors.py
    724 src/gunray/evaluator.py
    415 src/gunray/parser.py
    336 src/gunray/preference.py
     80 src/gunray/relation.py
    105 src/gunray/schema.py
     79 src/gunray/semantics.py
    116 src/gunray/stratify.py
    218 src/gunray/trace.py
    103 src/gunray/types.py
   4833 total
```

Key file deltas:

- **`defeasible.py`**: 784 → **339** (−445). Scorched in B1.2
  and rebuilt as a thin projection layer over
  `_evaluate_via_argument_pipeline`, with a
  `_is_strict_only_theory` shortcut into `SemiNaiveEvaluator`.
- **`evaluator.py`**: 732 → 724 (−8). Strict-only fast path
  retained; classifier removed.
- **`arguments.py`**: 0 → **410** (new). Def 3.1 argument
  enumeration; Def 3.6 defeater-rule participation landed in
  B2.4.
- **`dialectic.py`**: 0 → **548** (new). Def 3.4
  `counter_argues`, Def 4.1 / 4.2 defeater kinds,
  Def 4.7 `build_tree` with concordance and block-on-block
  enforcement, Proc 5.1 U/D marking, `render_tree`.
- **`disagreement.py`**: 0 → **87** (new). Literal-complement
  / disagreement predicates used by argument construction.
- **`preference.py`**: 0 → **336** (new). `TrivialPreference`,
  `GeneralizedSpecificity` (Simari 92 Lemma 2.4 antecedent-only
  reduction), `SuperiorityPreference` (Garcia 04 §4.1 rule
  priority), and `CompositePreference` with
  first-criterion-to-fire semantics.
- **`answer.py`**: 0 → **21** (new). Def 5.3 four-valued
  `answer(theory, literal, criterion)`.
- **`__init__.py`**: 30 → 61 (+31). Block 1 public surface
  exports.

Net module total: 3876 → 4833 (+957). Growth sits in the
pipeline modules, offset by a 445-line reduction in
`defeasible.py` — the refactor traded an opaque classifier
for named, paper-anchored pipeline stages.

Stable legacy modules untouched by scope: `closure.py`,
`compiled.py`, `conformance_adapter.py`, `evaluator.py`
(functional preservation), `parser.py`, `relation.py`,
`semantics.py`, `stratify.py`, `trace.py`, `types.py`,
`errors.py`. `ambiguity.py`, `compile.py`, `tolerance.py`
deleted or consumed.

## Conformance delta

| Stage                              | Pass | Fail | Deselected |
|------------------------------------|------|------|------------|
| Pre-refactor P0.1 run              |   0  |  295 |      0     |
| Post-adapter-fix P0.1.5 baseline   |  267 |   28 |      0     |
| Block 1 (scorched + wired)         |  243 |   52 |      0     |
| B2.4 defeater participation        |  244 |   50 |      1     |
| B2.5 / B2.6 superiority + composite|  250 |   44 |      1     |

Final **250 / 44 / 1** is the paper-correctness ceiling
documented in `reports/b2-superiority-preference.md` and
`notes/refactor_progress.md` ("Block 2 250 conformance ceiling
vs plan ≥267 target"). Classification of the 44 failures:

- **9 paper-correct regressions** (Def 3.1 cond 2) — fixtures
  encoded a non-paper classifier. Paper pipeline rejects
  arguments whose bodies are contradicted by `Π`.
- **3 Spindle implicit-failure cases** (Def 5.3 classification
  gap). Fixable only with an opt-in Spindle-compat shim.
- **2 partial-dominance edge cases** (Garcia 04 §4.1 strict
  dominance — every rule in the stronger argument must
  dominate every rule in the weaker).
- **28 `nemo_negation`** (SafetyViolationError: negation-safety
  bug in the engine-level path, independent of the defeasible
  refactor).
- **2 antoniou regime-not-implemented** (`PROPAGATING`;
  deprecated in B2.3 per
  `notes/policy_propagating_fate.md`).
- **1 `spindle_racket_query_long_chain`** (scalability,
  deselected via `conftest.py`).

B2 adversary (Q5) independently verified the strict-dominance
and `Π ∪ A` non-contradictory readings against Garcia 04 §3.1
and §4.1.

## Paper-citation delta

Grep across `src/gunray/`:

- Baseline (`notes/refactor_baseline.md` §6): **1** line
  matching `Garcia.*200[4]|Simari.*199[2]`, in
  `defeasible.py`.
- Post-refactor: **47** lines across 7 files
  (`arguments.py` 7, `answer.py` 2, `defeasible.py` 3,
  `dialectic.py` 14, `disagreement.py` 3, `preference.py` 15,
  `schema.py` 3).

**Delta: +46**.

Every definition / procedure / lemma reference is now in-source
at the call site it justifies.

## Hypothesis property test delta

Grep `@given` across `tests/`:

- Baseline: effectively 0 (`notes/refactor_baseline.md` §5
  notes that the baseline command was broken and returned a
  spurious 1 from the pytest plugin banner).
- Post-refactor: **45** `@given` test functions across 12 test
  files (`test_arguments_basics` 3, `test_build_arguments` 5,
  `test_answer` 4, `test_closure_faithfulness` 2,
  `test_dialectic` 7, `test_disagreement` 3,
  `test_parser_properties` 7, `test_render` 1, `test_trace` 3,
  `test_preference` 1, `test_superiority` 5,
  `test_specificity` 4).

Key properties run at `max_examples=500`: Def 4.7 conditions
(7), answer YES/NO/UNDECIDED/UNKNOWN invariants (4),
`test_hypothesis_composite_is_asymmetric` (composite preference
asymmetry over random acyclic superiority lists).

## Paper-correct finding: `nests_in_trees(tweety)`

Flagged in B1.6, pinned in `notes/refactor_progress.md`
("B1.6 — `nests_in_trees(tweety)` paper-rejected..."), then
re-verified by the B1.8 adversary and the B2 adversary Q5.

Under the Tweety + `r4: nests_in_trees(X) :- flies(X)` theory,
`Π` = `{penguin(tweety), r1, r2}` already derives
`~flies(tweety)`. Any candidate argument for `flies(tweety)`
must contain `r3`, and `Π ∪ {r3}` closes both `flies(tweety)`
and `~flies(tweety)`. Def 3.1 cond 2 (`Π ∪ A` must be
non-contradictory) therefore rejects every `flies(tweety)`
argument, and consequently every `nests_in_trees(tweety)`
argument.

The pre-refactor fixture
`depysible_nests_in_trees_{tina,tweety,henrietta}` expected
`nests_in_trees: [[tweety]]` in `undecided`, via the
pre-refactor `supported_only_by_unproved_bodies` reason code.
That reason code was a depysible-style invention with no
Def 4.7 analogue. The paper pipeline correctly omits the
literal from every section.

The three fixtures are classified **real-regression
paper-correct** and left failing. The B2 adversary confirmed
that no Def 4.7 path produces an argument for a literal whose
body is contradicted by `Π`.

## `Policy.PROPAGATING` deprecation

Removed in B2.3 via `9eca818
refactor(schema): deprecate Policy.PROPAGATING per
notes/policy_propagating_fate.md`. The decision of record is
`notes/policy_propagating_fate.md`: `PROPAGATING` comes from
Antoniou 2007 §3.5 (tag-propagation defeasible logic), a
different paper family than Garcia 04 / Simari 92. The gunray
pipeline has no mechanism that implements tag propagation;
carrying the enum value advertised behaviour gunray does not
deliver. The two `antoniou` regime-not-implemented fixtures
are explicitly out-of-scope.

## 16 refactor-scope failures (outside the plan's ≥267 gate)

The Block 2 final state has 44 failures; 28 are the
`nemo_negation` safety bug (engine path, not refactor scope).
The 16 refactor-scope failures categorize as:

- **9** Def 3.1 cond 2 paper-correct regressions (permanent).
- **3** Spindle implicit-failure classification gap (opt-in
  shim only).
- **2** Garcia 04 §4.1 strict-dominance edge cases (paper
  strictly rejects Spindle's "max dominates max" relaxation).
- **2** antoniou `PROPAGATING` regime-not-implemented.

Each category has a recorded cause (`reports/b2-superiority-preference.md`)
and a Foreman decision.

## Propstore update summary

`reports/b3-propstore-update.md` has the detailed list. Key
items:

- **`~`-strip hack deleted** — `_split_section_predicate` in
  `propstore/aspic_bridge.py` is gone (`20aa028 refactor(aspic_bridge):
  delete _split_section_predicate hack`). Propstore now reads
  gunray sections directly because gunray finally returns
  consistent section keys.
- **`arguments` field added** — `ground(return_arguments=True)`
  populates a `bundle.arguments` field (`f7a04eb feat(propstore):
  ground(return_arguments=True) populates bundle (green)`), with
  a Hypothesis property test (`fbb97e2 test(propstore):
  hypothesis property for ground(return_arguments=True)`).
- **PROPAGATING test references** — two propstore tests
  referenced `Policy.PROPAGATING`; B3.2 handled them per
  `reports/b3-propstore-update.md`.
- **`py.typed` marker landed upstream** — `gunray a1afcf2`
  pushed in this B3-close dispatch. Propstore's
  `# pyright: ignore[reportMissingTypeStubs]` shim
  (propstore `41aa2fe`) is now reverted as propstore
  `5f8f43d`, restoring strict-pyright cleanliness without
  local suppressions.
- **Propstore gunray pin** — bumped to `a1afcf2` via
  `uv lock --upgrade-package gunray` + `uv sync`. `uv.lock`
  is gitignored in propstore, so no lock commit exists; the
  pin bump is environmental, not source-controlled.

## Final status

- Gunray unit: 136 passed / 0 skipped / 1 pre-existing failure
  (`test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  — predates the refactor; unchanged).
- Gunray conformance: 250 / 44 / 1.
- Pyright: clean on
  `defeasible.py`, `arguments.py`, `dialectic.py`,
  `disagreement.py`, `preference.py`, `answer.py`,
  `__init__.py`.
- Paper citations: 47.
- Hypothesis `@given` functions: 45.
- Propstore: no `~`-strip hack, no
  `# pyright: ignore[reportMissingTypeStubs]` shims, gunray
  imports strict-pyright clean via PEP 561 marker.

Refactor: **done**.
