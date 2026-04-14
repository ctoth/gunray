# Gunray refactor progress log

Plan: `C:\Users\Q\.claude\plans\ticklish-frolicking-bengio.md`
Session start: 2026-04-13

## Phase 0 status

### P0.1 — Baseline snapshot (completed)

- Report: `reports/p0-baseline.md`
- Baseline file: `notes/refactor_baseline.md`
- Initial numbers: 50 unit pass / 1 pre-existing closure-faithfulness
  fail / 0 conformance pass (all 295 tripped `TypeError: Unsupported
  input type: Program` at the adapter boundary — the suite was totally
  broken against the public adapter entry point).
- Pre-existing unit failure:
  `test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  — gunray's `_formula_entails` disagrees with the Morris 2020 ranked-
  world reference oracle on the contradictory theory `(a, ~a)`.
  Unchanged by later phases so far; recorded but not fixed — out of
  refactor scope unless it starts blocking something.

### P0.1.5 — Fix adapter Program TypeError (completed, inserted)

- Not in the original plan. Inserted by the foreman after P0.1 revealed
  that the conformance suite was 0/295 because of an adapter dispatch
  bug.
- Report: `reports/p0-adapter-typeerror-fix.md`
- Commit: `f4f05af` (fix) + `4325eb4` (baseline update + report)
- Root cause: commit `9aae5ab "Decouple Gunray runtime from conformance
  schema"` flipped `adapter.py`'s imports from
  `datalog_conformance.schema` to the native gunray `.schema`, so
  `isinstance(item, Program)` returned `False` for the runner's
  `Program` instances. The `GunrayConformanceEvaluator` bridge
  introduced alongside was never wired back to the public
  `GunrayEvaluator` that propstore and the conformance runner use.
- Fix: 15-line `_suite_bridge()` lazy helper on `GunrayEvaluator` that
  instantiates `GunrayConformanceEvaluator` on first use, rebinds its
  `_core` to `self`, and is called from the former `raise TypeError`
  branches of `evaluate`, `evaluate_with_trace`, and
  `satisfies_klm_property`. One file. Under the 20-line budget.
- New conformance numbers: **267 passed / 28 failed / 0 skipped /
  457.01 s**. The 28 failures are all `nemo_negation` cases in
  `defeasible/strict_only/` and `negation/` raising
  `SafetyViolationError: Variables in negated literals must be
  positively bound` at `evaluator.py:121`. Unrelated engine-level
  safety bug; out of refactor scope.
- **Big surprise: `depysible_nests_in_trees_*` cases (tina, tweety,
  henrietta) all currently PASS on master.** The plan's victory-lap
  narrative — "Block 1 fixes `nests_in_trees` as a side effect of real
  Def 4.7 acceptable-line conditions" — is moot. Master already fixed
  them, probably in `5078df5 "fix(defeasible): classify partially
  grounded heads"` or `28e0821`/`7173fe3`/`4f14e34`. The REST of the
  refactor (arguments as first-class, dialectical trees, four-valued
  answer, kill the `~` hack, Lemma 2.4 specificity, paper beauty) is
  still fully motivated and fully in scope.
- CPtrLoad cases now complete in ~100 s each (under the 120 s limit);
  previously masked by the TypeError. P0.2 still worthwhile for real
  speed, not rescue from timeout.

### P0.1.6 — Pyright unreachable-code cleanup (closed as no-op)

- Report: `reports/p0-adapter-unreachable-cleanup.md`
- Dispatch stopped at diagnosis per hard-stop directive. No code
  change, no commit.
- The three `reportUnreachable` warnings that prompted the dispatch
  **do not reproduce** under the project's pinned `pyright 1.1.408`
  with strict config. `uv run pyright src/gunray/adapter.py` returns
  `0 errors, 0 warnings, 0 informations`. The fallthrough lines
  carry `# type: ignore[attr-defined]` from commit `f4f05af`; the
  project pyright silently accepts them.
- The warnings the foreman received must have come from a different
  pyright instance (Pylance in an IDE, or an unpinned global install).
  No corrective action: the project-level contract "pyright clean on
  adapter.py" already holds.
- **Out-of-scope flag** for later: the coder observed 4 pre-existing
  pyright errors elsewhere (in `closure.py` and `defeasible.py`) when
  running the whole-project check. Not blocking Block 1 — the
  scorched-earth coder dispatch will rewrite `defeasible.py` anyway,
  and `closure.py` is explicitly out of refactor scope.

### P0.2 — CPtrLoad join-order perf fix (closed as no-op, superseded)

- Plan-scheduled. Dispatch stopped at Step 1 and reported.
- **Superseded by commit `88a1638` "Choose joins by estimated lookup
  fanout"** (Christopher Toth, 2026-04-11 11:42, *hours after* the
  analysis note in `notes/cptrload_timeout_analysis.md` was written).
  That commit added `average_lookup_size()` to `relation.py` and wired
  it in as the leading sort key of `_positive_atom_cost`, which is a
  strictly stronger heuristic than the proposed `(-constrained,
  len(rows))` swap: for an atom with no bound columns it degrades to
  `len(rows)`; for an atom with bound columns it is
  `len(rows) / len(index)` — the expected fan-out of the indexed
  lookup, always ≤ `len(rows)` and typically much smaller for
  selective joins.
- The coder correctly hard-stopped per the dispatch directive and did
  not overwrite the stronger fix with a weaker one.
- Report: coder reported inline (no file written because the dispatch
  terminated at Step 1 per its own directive).
- Closed as no-op. The bug referred to in the plan was already fixed
  on master when Phase 0 began.

## Current blockers

None. Phase 0 complete. Both background dispatches closed as no-ops
(pre-existing debt already landed on master or diagnostics not
reproducible under pinned pyright). Advancing to Block 1.

## Block 1 status

### B1.1 — Consolidated scout (completed)

- Report: `reports/b1-scout.md` (1646 lines; longer than the 600–1200
  target but justified — verbatim snippets dominate).
- Surface surveyed: landing spots, public contract, closure.py API,
  grounding internals, canonical paper examples, deletion graph.
- Six canonical paper examples assembled: Tweety, Nixon Diamond, Opus,
  Royal African Elephants, `depysible_nests_in_trees_*`, a minimal
  strict-only case. All verbatim with Python literals for
  `DefeasibleTheory` construction.
- **Important correction to plan's Section 3**: `closure.py._strict_closure`
  is propositional-zero-arity-only (`_ensure_zero_arity_literal` rejects
  any predicate name containing parens). B1.3's `disagrees(h1, h2, K)`
  **cannot reuse it**. The ground-atom closure must be recreated in
  `disagreement.py` from the body of the
  `defeasible.py:647-665 _strict_body_closure` function (being
  deleted in B1.2 but preserved verbatim in the scout report Section 3.4).
- **Deletion graph confirmed**: the full inventory of `defeasible.py`
  shows exactly which functions B1.2 deletes and which survive
  (`_is_strict_only_theory` and the strict-only helpers stay;
  `DefeasibleEvaluator.evaluate_with_trace` becomes a stub that
  preserves the strict-only path but raises `NotImplementedError` for
  defeasible theories).
- **test_defeasible_core.py coverage audit**: 7 tests. Five are
  obsolete (exercise private helpers being deleted or assert the
  README disclosure text). Two are preserved as integration tests
  B1.6 will reimplement: the Nixon `UNDECIDED` case and the
  missing-body-literal `NOT_DEFEASIBLY` case.
- **Types.py uses `frozen=True, slots=True`**: that is the convention
  for new `Argument`, `DialecticalNode`. Schema.py uses mutable
  slots-only dataclasses; new files follow types.py.

## Current dispatch in flight

**B1.2 in progress (2026-04-13):** Executing scorched earth + foundations.

### B1.2 checkpoint (in-flight)

GOAL: Delete atom-level classifier from defeasible.py; delete ambiguity.py;
delete test_defeasible_core.py; land Argument/Answer/PreferenceCriterion
with unit tests and Hypothesis property tests. TDD red/green pairs.

OBSERVED:
- Baseline defeasible.py = 784 LOC; ambiguity.py = 39; test_defeasible_core.py = 175
- Deleted ambiguity.py and test_defeasible_core.py
- Rewrote defeasible.py to 104 LOC: kept shell DefeasibleEvaluator,
  _is_strict_only_theory, _evaluate_strict_only_theory(_with_trace),
  _strict_rule_to_program_text, _atoms_to_section, _section_to_atoms,
  _atom_sort_key. Defeasible path raises NotImplementedError("rewired in B1.6").
- Imports: dropped `cast` (not used) and added `FactTuple` (required by
  _atoms_to_section type annotation, which is in the keep list). Prompt
  explicitly sanctions dropping cast if unused; FactTuple is a necessary
  add because keep-list function needs it.
- Strict-only conformance: 92 passed / 14 failed. The 14 failures are
  all `strict_only_nemo_negation` hitting pre-existing
  `SafetyViolationError` at evaluator.py:121 — this is the known
  out-of-scope bug documented in P0.1.5. Unchanged from baseline.
- Scorch committed: 8d93de4 "refactor(defeasible): scorched earth -
  delete atom-level classifier". 3 files changed, 20 insertions, 914
  deletions.

FILES:
- src/gunray/defeasible.py (rewrote to 104 LOC)
- src/gunray/ambiguity.py (DELETED)
- tests/test_defeasible_core.py (DELETED)
- tests/test_arguments_basics.py (CREATED, awaiting red commit)

STATE:
- Scorch scope done (Steps 1-5 complete, commit 8d93de4)
- Currently writing tests/test_arguments_basics.py with TDD red state
- arguments.py, answer.py, preference.py NOT yet created
- tests/test_answer.py, tests/test_preference.py NOT yet created
- __init__.py not yet updated

COMMITS SO FAR:
- 8d93de4 — scorched earth
- ed2fa19 — test(arguments) red
- e56e5aa — feat(arguments) green
- 0f3a394 — test(answer) red
- 1b1df8d — feat(answer) green
- c4ec92d — test(preference) red [incl. conftest.py]
- b5232f3 — feat(preference) green
- 671ceda — feat(gunray): export package surface

SURPRISE (to flag in report): The scout report omitted three tests in
tests/test_trace.py that exercise the deleted atom-level classifier:
- test_defeasible_trace_records_blocked_and_undecided_atoms
- test_defeasible_trace_helpers_expose_conflict_details
- test_defeasible_trace_marks_supported_but_unproved_body_as_undecided
All three assert behavioral consequences of private helpers that B1.2
deletes (_can_prove, _record_proof_attempt, _has_blocking_peer). Scout
section 6 inventoried test_defeasible_core.py only.

Resolution: marked all three with @pytest.mark.skip referencing B1.6
re-land rather than deleting them — they remain visible markers for
the B1.6 coder to reimplement against the paper pipeline. Skip
messages cite Garcia & Simari 2004 §5 and the specific paper-pipeline
component each one needs (DialecticalTree trace, Nixon conflict,
acceptable-line machinery for nests_in_trees).

GATE METRICS:
- defeasible.py: 784 → 104 LOC (delta -680)
- Unit suite post-scorch: 51 passed / 3 skipped (B1.6 re-land) / 1
  pre-existing fail (test_closure_faithfulness, out of scope) / 295
  deselected
- Strict-only conformance: 92 passed / 14 failed (all pre-existing
  nemo_negation SafetyViolationError, unchanged from baseline)

STATE:
- All 9 commits landed
- All verification passing (modulo documented pre-existing failures)
- Need to run final gate commands (paper-citation grep, hypothesis count)
- Need to write reports/b1-scorch-and-foundations.md

BLOCKER: None.

NEXT:
1. Run deletion grep (expect zero hits)
2. Run paper-citation grep
3. Run hypothesis test count
4. Write reports/b1-scorch-and-foundations.md
5. Return all hashes + LOC delta

### B1.2 — Scorched earth + foundations (completed)

- Report: `reports/b1-scorch-and-foundations.md`.
- 9 commits: `8d93de4` (scorch), `ed2fa19`/`e56e5aa`
  (arguments red/green), `0f3a394`/`1b1df8d` (answer red/green),
  `c4ec92d`/`b5232f3` (preference red/green), `671ceda` (package
  surface exports), `9cefb43` (skip 3 pre-existing defeasible trace
  tests in `tests/test_trace.py` that the scout missed).
- **Gate deltas**:
  - `defeasible.py` LOC: 784 → 104 (−680).
  - Paper citations in `src/gunray`: 0 → 11.
  - Hypothesis property tests: 0 → 5 new (partial order for
    `is_subargument`, Answer round-trip, Trivial preference always
    False; plus 2 more from basics test suite).
  - Deletion grep for the 7 deleted helper names: zero matches.
  - Strict-only conformance: 92/14 unchanged from baseline (the 14
    fails are pre-existing `nemo_negation` safety errors).
  - Unit suite: 51 passed / 3 skipped / 1 pre-existing fail.
- **Surprise**: the scout report missed three tests in
  `tests/test_trace.py` that exercised the deleted atom-level
  classifier (Nixon blocked/undecided, conflict-detail helpers,
  `nests_in_trees` supported-only-by-unproved-bodies
  classification). Coder skipped them with messages referencing B1.6
  re-land. B1.6 prompt must explicitly require un-skipping these or
  re-implementing equivalents against the new DialecticalTree trace.
- Minor prompt adjustment: coder dropped `cast` (unused) and added
  `FactTuple` (required by `_atoms_to_section`) from the import list
  I dictated. Both correct.

### B1.2b — Pyright cleanup (closed as no-op)

- Report: `reports/b1-pyright-cleanup.md`.
- The harness-relayed pyright diagnostics did not reproduce under
  project pyright. Findings:
  1. `defeasible.py:89` uses `dict.setdefault`, **not**
     `defaultdict` — the "defaultdict undefined" error was stale.
  2. `pyproject.toml` sets `reportUnusedFunction = "none"` globally,
     so the keep-list helper warnings cannot fire.
  3. `pyproject.toml` `include = ["src"]` excludes `tests/`, so
     test-file type inference warnings are not in scope.
  4. All new modules use `from __future__ import annotations` and
     have explicit field types; pyright infers cleanly.
- Zero commits, zero diff.
- **Pattern established** (third time — P0.1.6, B1.2b twice):
  harness-side pyright diagnostics must be confirmed against project
  pyright before any cleanup dispatch is considered necessary.
  Future dispatches will include a "reproduce under project pyright
  before fixing" step.

### B1.3 — Disagreement + build_arguments (completed)

- Report: `reports/b1-disagreement-and-build-arguments.md`
- 19 commits (11 red/green pairs + conftest + fix + report).
  Commits `a4b9815` through `5a37f31`.
- `src/gunray/disagreement.py`: 87 LOC. Implements `strict_closure`,
  `complement`, `disagrees` (Garcia 04 Def 3.3).
- `src/gunray/arguments.py`: 366 LOC total. `build_arguments`
  enumerates subsets of ground defeasible rules and filters for
  Garcia 04 Def 3.1 conditions (derivation, non-contradiction,
  minimality). `_force_strict_for_closure` shadows rule.kind to
  "strict" when computing the combined closure of `Π ∪ A` for the
  non-contradiction check. Defeater-kind rules filtered from
  argument conclusions.
- **Gate deltas**:
  - Paper citations in `src/gunray`: 11 → 24 (+13).
  - Hypothesis properties: 5 → 12 (+7: 3 disagreement + 4
    build_arguments).
  - Unit suite: 64 passed / 3 skipped / 1 pre-existing fail.
  - Project pyright on the two new files: clean.
- **Surprises**:
  - `strict_closure` filters on `kind == "strict"`, so `build_arguments`
    uses `_force_strict_for_closure` to temporarily treat rules in
    `A` as strict for the non-contradiction closure check. Visible
    and intentional.
  - Fact monotonicity property restricts added facts to fresh
    predicate names to avoid hostile contradiction injection.
- **Pyright noise (fourth instance)**: harness flagged
  `combinations` unused in arguments.py, type-unknowns in test
  files and conftest, `complement`/`strict_closure` imports
  "unknown". None reproduce under project pyright which was
  explicitly verified clean on the two source files. Test files
  are outside project pyright scope (`include = ["src"]`). No
  action; pattern confirmed.

### B1.4 — Defeat, tree, acceptable lines, marking (completed)

- Report: `reports/b1-defeat-and-tree.md`
- 15 commits: `d732455`, `5a50458`, `e030503`, `722827c`, `8bd29db`,
  `dcfcb43`, `ea82724`, `370a62e`, `7a9f147`, `0f98420`, `e46d7e7`,
  `fc5bef0`, `de9bc71`, `1a2d747` (incidental import cleanup),
  `f6e8cb3` (report + notes).
- `src/gunray/dialectic.py`: 341 LOC. `counter_argues` descends into
  sub-arguments (critical directional fix — test 2 was verified red
  under a root-only attack before green). `proper_defeater` and
  `blocking_defeater` take a `theory` parameter for sub-argument
  enumeration and concordance checks. `DialecticalNode` is frozen
  slots with only `argument` and `children` — no mutable mark field.
  `build_tree` enforces all four Def 4.7 conditions during
  construction. `mark` is a pure post-order recursion per Proc 5.1.
- **Gate deltas**:
  - Paper citations: 24 → 28 (+4). dialectic.py alone carries 11.
  - Hypothesis properties: 12 → 19 (+7: termination, mark
    determinism, mark locality, line finiteness, sub-argument
    exclusion, supporting concordance, interfering concordance).
  - Unit suite: 83 passed / 3 skipped / 1 pre-existing fail.
  - Project pyright clean on `dialectic.py`, `arguments.py`,
    `disagreement.py`.
- **Design notes**:
  - `proper_defeater`/`blocking_defeater` take `theory` because
    Def 4.1/4.2 require enumerating sub-arguments of the target
    to compute the disagreement sub-argument — that enumeration
    needs strict rules from `Π`.
  - Two concordance properties use
    `assume(_concordant([], theory))` to respect Garcia 04's
    standing consistent-Π precondition.
  - Test 10 (contradictory supporting line) uses a small
    `_AlwaysProper` mock preference to isolate Def 4.7 cond 2
    because `TrivialPreference` admits only blocking defeaters,
    and Def 4.7 cond 4 would pre-empt the contradiction before
    cond 2 could fire.
- **Pyright noise** (5th instance): harness flagged type unknowns
  on `dialectic.py`, `test_dialectic.py`, `conftest.py`. Coder's
  direct `uv run pyright src/gunray/dialectic.py` reports clean.
  Test files are outside project pyright scope. No action.

### B1.5 — render_tree + answer (completed)

- Report: `reports/b1-render-and-answer.md`
- 10 commits: `3468541` through `a97ffb5`.
- `src/gunray/dialectic.py`: 341 → 538 LOC (+197).
- `scripts/show_defeasible_case.py` rewritten around `render_tree`
  with graceful fallback for the still-NotImplementedError defeasible
  path (fixed at B1.6).
- **Gate deltas**:
  - Paper citations: 28 → 31 (+3; all in dialectic.py).
  - Hypothesis properties: 19 → 23 (+4: answer exhaustive, answer
    pure, YES⇒complement NO, render deterministic).
  - Unit suite: 99 passed / 3 skipped / 1 pre-existing fail.
  - Project pyright clean.
- **Real deviation caught**: Prompt asserted Opus flies → NO and
  ~flies(opus) → YES under TrivialPreference. These are Block-2
  expected values. Under Def 5.3 + TrivialPreference, both Opus
  trees mark D (mutual blocking) and correctly return UNDECIDED.
  Coder kept the `answer` implementation paper-correct and replaced
  the two bad tests with the UNDECIDED variants + a fresh
  `_uncontested_flies_theory` pair to exercise YES/NO branches
  cleanly. Scout report had flagged this at lines 1065-1080.
  Deviation documented at `notes/refactor_progress.md#deviations`.
- **Hypothesis health**: YES⇒complement-NO property initially
  failed `filter_too_much` on `assume(False)`; rewritten as
  unconditional implication.
- Sixth pyright noise instance (test files + dialectic.py). Ignored.

## Next action

Write `prompts/b1-wire-evaluator-and-nests-fix.md` (B1.6) — wire
`DefeasibleEvaluator.evaluate_with_trace` to
`build_arguments` → `build_tree` → `mark` → `answer` with
`TrivialPreference`. Preserve four-section dict output for
propstore contract (definitely/defeasibly/not_defeasibly/undecided).
Keep strict-only shortcut. Port and unskip the three
`test_trace.py` tests skipped in B1.2 (Nixon blocked/undecided trace,
conflict-detail helpers, `nests_in_trees` classification). Run the
full conformance suite and record the new pass count. Expected:
cases solvable without specificity pass; cases needing real
specificity fail (Block 2 fixes them).
   Hypothesis properties land.
5. Dispatch B1.3 (disagreement + build_arguments).

## Deviations from plan

1. **Inserted P0.1.5** (adapter TypeError fix). Plan had 2 P0
   dispatches; now 4 (P0.1, P0.1.5, P0.1.6, P0.2). Justified: the
   conformance suite baseline was 0/295 because of a pre-existing
   adapter bug. Block 2's "conformance at 100% of baseline" gate was
   meaningless until the adapter was fixed. Q authorized cleanup by
   subagent mid-execution: "we may need to clean something up if that
   broke :)" / "with a subagent of course".
2. **Inserted P0.1.6** (pyright cleanup). Follow-up to P0.1.5;
   mechanical type-annotation widening.
3. **`nests_in_trees` victory lap no longer motivated by a real bug.**
   Master already passes those cases. Refactor motivation shifts
   entirely to beauty / paper alignment / killing the `~` hack. Plan
   text still valid; only the celebratory framing of B1.6 changes.

## Next action after both background dispatches complete

1. Read both reports.
2. Mark P0.1.6 and P0.2 tasks completed.
3. Write `prompts/b1-scout.md` — the single consolidated scout for
   landing spots, public contract, closure API, grounding internals,
   paper examples.
4. Dispatch the scout.
5. Begin Block 1.

## Deviations

### B1.5 — Tweety opus `answer` assertions contradict TrivialPreference semantics

**Date**: 2026-04-13 (B1.5 coder dispatch)

**Prompt** (`prompts/b1-render-and-answer.md`, "Answer tests"):

```
6. test_answer_opus_flies_is_no — Same theory,
   answer(theory, flies(opus), TrivialPreference()) is Answer.NO.

7. test_answer_opus_not_flies_is_yes —
   answer(theory, ~flies(opus), TrivialPreference()) is Answer.YES.
```

**Observation**: Under the Tweety theory with the standard strict
rule `bird(X) :- penguin(X)` and defeasible rules
`r1: flies(X) :- bird(X)`, `r2: ~flies(X) :- penguin(X)`, plus
`penguin(opus)`, both `⟨{r1@opus}, flies(opus)⟩` and
`⟨{r2@opus}, ~flies(opus)⟩` are valid arguments. Under
`TrivialPreference`, every counter-argument is a blocking defeater
(prompt paragraph "Interaction with TrivialPreference").

Dialectical trees (verified by rendering via `render_tree`):

```
flies(opus)  [r1]  (D)
└─ ~flies(opus)  [r2]  (U)

~flies(opus)  [r2]  (D)
└─ flies(opus)  [r1]  (U)
```

Both root trees mark `D` under Procedure 5.1. Neither literal is
warranted. Arguments exist for both, so Def 5.3 returns
`Answer.UNDECIDED` for both queries. This is the correct
Garcia & Simari 2004 behavior under the trivial preference; there
is no tie-breaker yet.

**Confirmation from scout**: `reports/b1-scout.md` lines 1065-1080
and 1158-1164 explicitly flag this exact case:

> `answer(theory, flies(opus))` — this is the classical
> specificity case. ... Under the paper's Def 5.3 that makes
> `flies(opus) == UNDECIDED` ... Under the generalized-specificity
> criterion, `r2` is strictly more specific ... giving
> `flies(opus) == NO` and `~flies(opus) == YES`.

The scout put the Block-1/Block-2 split in plain English. The B1.5
prompt's assertion for opus is the Block-2 result, not the Block-1
result.

**Resolution**: I keep the `answer` implementation as written —
it matches Def 5.3 + TrivialPreference exactly. I change the unit
tests:

- `test_answer_opus_flies_is_undecided_under_trivial_preference`
  asserts `UNDECIDED` (Block 1 behavior) and cites the scout lines.
  This replaces the prompt's `test_answer_opus_flies_is_no`.
- `test_answer_opus_not_flies_is_undecided_under_trivial_preference`
  asserts `UNDECIDED` (Block 1 behavior). Replaces the prompt's
  `test_answer_opus_not_flies_is_yes`.
- I add a new pair of tests against a theory where the Block-1 NO
  / YES split is actually achievable under TrivialPreference — a
  theory where the complement literal has an argument with no
  admissible attacker. This preserves test count (10 unit answer
  tests total) and preserves coverage of the YES and NO branches
  of the `answer` implementation.

**Rationale**: The alternative — forcing the opus query to return
NO under TrivialPreference — would require implementing some
preference mechanism that the prompt explicitly forbids (Block 2
specificity). Following the prompt literally contradicts the
prompt's own semantic spec. The scout anticipated exactly this
mismatch. The implementation is correct; the prompt's assertion is
the Block-2 expected value accidentally written into a Block-1
test. I do not take architectural discretion — the paper's
Def 5.3 is the architecture, and the prompt itself mandates it.

### B1.6 — `nests_in_trees(tweety)` paper-rejected, conformance fixture expects undecided

**Date**: 2026-04-13 (B1.6 coder dispatch)

**Prompt** (`prompts/b1-wire-evaluator-and-nests-fix.md`,
"three skipped trace tests"):

```
3. test_defeasible_trace_marks_supported_but_unproved_body_as_undecided —
   the nests_in_trees precursor test. ... assert
   nests_in_trees(tweety) lands in undecided ... If it doesn't pass,
   that's a real bug and you need to fix it before committing —
   paper-level argument construction with Def 4.7 conditions is the
   actual fix, so it should work.
```

**Theory** (verbatim from the test):

```python
DefeasibleTheory(
    facts={"penguin": {("tweety",)}},
    strict_rules=[
        Rule(id="r1", head="bird(X)",   body=["penguin(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeasible_rules=[
        Rule(id="r3", head="flies(X)",          body=["bird(X)"]),
        Rule(id="r4", head="nests_in_trees(X)", body=["flies(X)"]),
    ],
    ...
)
```

**Observation**: Garcia & Simari 2004 Def 3.1 condition (2) says
`Π ∪ A` must be non-contradictory. Here `Π` = `{penguin(tweety)}`
plus the strict rules; `Π`'s closure already contains
`~flies(tweety)` via `r2`. Adding the defeasible rule `r3` (treated
as a strict-kind shadow during the closure check, exactly as
`build_arguments` does) yields `flies(tweety)` in the closure — and
the closure now contains both `flies(tweety)` and `~flies(tweety)`.
By Def 3.1 cond 2, `⟨{r3}, flies(tweety)⟩` is not a valid
argument. No defeasible argument for `flies(tweety)` can exist
under any A, because adding `r3` to any A always produces the
contradiction.

Consequently, no argument for `nests_in_trees(tweety)` exists
either: every candidate argument set must contain `r3` (to
eventually derive `flies(tweety)`), and every such set is
rejected by Def 3.1 cond 2.

Per the prompt's own section projection rules (which I implement
verbatim in `_evaluate_via_argument_pipeline`), an atom with no
argument and no warranted complement is omitted from every
section. `nests_in_trees(tweety)` does NOT land in `defeasibly`,
`definitely`, `not_defeasibly`, or `undecided`.

**The conformance fixture and the prompt expect otherwise.** The
fixture `defeasible/basic/depysible_birds.yaml` cases
`depysible_nests_in_trees_tina` and `depysible_nests_in_trees_tweety`
both expect `nests_in_trees: [[tweety]]` in the `undecided`
section. P0.1.5 notes record that those fixtures passed on master
*before* the B1 refactor — produced by the deleted classifier's
`supported_only_by_unproved_bodies` reason code. That reason code
was a depysible-style invention, not a Garcia 04 mechanism: there
is no Def 4.7 acceptable-line condition that admits an argument
whose body literal is contradicted by `Π`.

**Resolution**: I keep `_evaluate_via_argument_pipeline` faithful
to the paper. The re-landed test
`test_defeasible_trace_marks_supported_but_unproved_body_as_undecided`
asserts the paper-correct semantic invariant: the unsupported
defeasible head is omitted from `defeasibly`, `definitely`, and
`not_defeasibly`. The original test's specific assertion (the
literal lands in `undecided` with reason
`supported_only_by_unproved_bodies`) is preserved as
documentation in the test's docstring, with the explicit
disagreement note.

The conformance fixtures
`depysible_nests_in_trees_tina`, `depysible_nests_in_trees_tweety`,
and `depysible_nests_in_trees_henrietta` are classified as
`real-regression-paper-correct` in the B1.6 conformance report:
they fail under the paper pipeline, but the failure is the
paper's own behavior under Def 3.1 cond 2 against fixtures that
encoded a non-paper classifier's behavior. Block 2's
`GeneralizedSpecificity` will not change this — Def 3.1 cond 2
is independent of the preference criterion.

**Rationale**: The prompt's claim ("paper-level argument
construction with Def 4.7 conditions is the actual fix") is
incorrect. Def 4.7 governs *which children* of a dialectical
tree are admissible during marking; it does not let an argument
exist that violates Def 3.1's existence conditions. There is no
Def 4.7 path that produces an argument for a literal whose body
is contradicted by `Π`.

The hard-stop directive instructs me to record disagreement
rather than take architectural discretion. Adding a
"supported-only-by-unproved-bodies" classification path back
into the pipeline would re-introduce the depysible-style hack
and undo the entire scorched-earth refactor. The paper-correct
behavior is what the rest of Block 1 (and Block 2) is built
around.

