# Workstream checkpoint

## Baseline capture

- `uv run pytest tests -q`: `139 passed, 292 skipped, 3 deselected in 83.05s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 262.91s`
- `uv run pyright`: failed before workstream edits with 6 errors in `src/gunray/closure.py`
- `uv run ruff check`: failed before workstream edits with 21 violations across existing source/tests

Baseline did not match `README.md` / workstream expected state for static analysis, so execution is blocked before P0-T1 per `GROUND_RULES.md`.

## Baseline unblocker

- Fixed the pre-existing `closure.py` pyright issues by typing the ranked-score callback and the zero-arity trace atom helper.
- Ran `uv run ruff check --fix` and `uv run ruff format` to clean pre-existing import and formatting drift.
- Added two focused performance unblockers after conformance exposed reproducible HMMER CPtrStore timeouts:
  - `80b64b8` / `2f294d3`: `IndexedRelation.difference()` bulk-copies set differences instead of rebuilding row-by-row.
  - `16e1f44` / `60c0b07`: join-order costing estimates fanout without materializing full hash indexes.
- `uv run pyright`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
- `uv run ruff format --check`: `46 files already formatted`
- `uv run pytest tests -q`: `139 passed, 292 skipped, 3 deselected in 96.74s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 316.77s`

## P0-T1 summary

- `src/gunray.tar`: absent and not tracked in this checkout.
- `out`: untracked scratchpad appeared during local git-log inspection and was removed.
- `.gitignore`: added `.hypothesis/`.
- `uv run pytest tests -q`: `141 passed, 292 skipped, 3 deselected in 83.54s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 279.95s`
- `uv run pyright`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
- `uv run ruff format --check`: `47 files already formatted`

## P1-T1 summary

- Red commit: `74d91f0` reproduced the strict-only Pi contradiction leak with two explicit tests and one Hypothesis property.
- Green change: strict-only evaluation raises `ContradictoryStrictTheoryError` when Pi derives complementary literals or explicit conflict pairs.
- Green change: `build_arguments()` raises the same error when Pi is contradictory before argument enumeration.
- Test harness update: two external Spindle fixtures that expect contradictory strict facts are treated as local expected-error conformance cases.
- Strategy update: shared small-theory Hypothesis generator avoids constructing contradictory strict knowledge bases for ordinary argument/preference properties.
- `uv run pytest tests/test_strict_only_pi_contradiction.py -v`: `3 passed`
- `uv run pytest tests -q`: `144 passed, 292 skipped, 3 deselected in 136.13s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 308.54s`
- `uv run pyright src/gunray/defeasible.py src/gunray/errors.py src/gunray/arguments.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/defeasible.py src/gunray/errors.py src/gunray/arguments.py tests/conftest.py tests/test_conformance.py tests/test_strict_only_pi_contradiction.py`: `All checks passed!`

## P1-T2 summary

- Red commit: `d7da22e` reproduced GeneralizedSpecificity preferring a defeasible argument over a strict empty-rules argument.
- Green change: `GeneralizedSpecificity.prefers()` now treats any empty-rules argument as incomparable under specificity.
- `uv run pytest tests/test_specificity.py -v`: `12 passed`
- `uv run pytest tests -q`: `146 passed, 292 skipped, 3 deselected in 89.18s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 314.27s`
- `uv run pyright src/gunray/preference.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/preference.py tests/test_specificity.py`: `All checks passed!`

## P1-T3 summary

- Red commit: `bfc41fc` reproduced the Def 3.3 Pi-facts drop with a direct disagreement test, a facts-monotonicity property, and an end-to-end `DefeasibleEvaluator` case.
- Green change: `strict_closure()` and `disagrees()` accept strict facts and seed closure with `seeds | facts`.
- Green change: dialectic disagreement checks now pass grounded Pi facts through `_theory_pi_facts()`.
- Audit note: `GeneralizedSpecificity._covers()` still excludes facts because the existing implementation documents K_N as strict-rule coverage only; no fact plumbing was added there.
- Unblocker: `281a8cc` / `7d4ea60` pinned and fixed an unrelated closure full-suite failure where `_branch_satisfiable()` treated negative strict body literals as derivable atoms instead of absence constraints.
- `uv run pytest tests/test_disagreement.py -v`: `9 passed`
- `uv run pytest tests/test_disagreement.py tests/test_dialectic.py tests/test_specificity.py -v`: `38 passed`
- `uv run pytest tests/test_closure.py tests/test_closure_faithfulness.py -v`: `8 passed`
- `uv run pytest tests -q`: `150 passed, 292 skipped, 3 deselected in 98.70s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 318.46s` (no pass-count delta)
- `uv run pyright src/gunray/disagreement.py src/gunray/dialectic.py src/gunray/preference.py src/gunray/arguments.py src/gunray/closure.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`

## P2-T1 summary

- Red commit: `36f72d1` pinned the package-level preference subclass export contract and `__all__` completeness/sort order.
- Green change: exported `CompositePreference`, `GeneralizedSpecificity`, and `SuperiorityPreference` from `gunray.__init__`.
- Green change: sorted the existing `Program` / `ProofAttemptTrace` ordering in `__all__`.
- `uv run pytest tests/test_public_api.py -v`: `2 passed`
- `uv run pytest tests -q`: `152 passed, 292 skipped, 3 deselected in 90.71s`
- `uv run pyright src/gunray/__init__.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
- Inline import command from the task file was not run because the repo Python tooling rule forbids `python -c`; the import path is covered by `tests/test_public_api.py`.

## P2-T2 summary

- Red commit: `d6c44bb` rewrote the defeasible trace tests to pin argument-centric fields and absence of old flat rule-fire fields.
- Green change: removed `ProofAttemptTrace`, `ClassificationTrace`, their factories, and `DefeasibleTrace` flat-list accessors.
- Green change: `DefeasibleTrace` now carries `arguments`, `trees`, and `markings`, with `arguments_for_conclusion()`, `tree_for()`, and `marking_for()` helpers.
- Green change: `DefeasibleEvaluator` retains dialectical trees and U/D markings while computing warrant.
- Green change: package exports and README trace prose were updated for the new trace contract.
- Propstore check: exact grep for `trace.proof_attempts`, `trace.classifications`, `proof_attempts_for`, `classifications_for`, `ProofAttemptTrace`, and `ClassificationTrace` found no code consumers. No propstore code migration was needed.
- Propstore baseline: `uv run pytest -q` failed before any propstore edits with `9 failed, 2550 passed, 1 warning in 523.76s`; all failures were `NameError("name 'RenderPolicy' is not defined")` in CLI/world render-policy tests. No propstore files were changed.
- `uv run pytest tests/test_trace.py -v`: `10 passed`
- `uv run pytest tests -q`: `153 passed, 292 skipped, 3 deselected in 144.25s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: first full rerun hit a HMMER timeout artifact; focused HMMER rerun passed `2 passed, 293 deselected in 267.63s`; second full rerun passed `282 passed, 10 skipped, 3 deselected in 355.61s`
- `uv run pyright src`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
- README trace verification: temporary script run with `uv run python tools/readme_trace_example.py` exercised `find_rule_fires()`, `arguments_for_conclusion()`, `tree_for()`, and `marking_for()` successfully; script was removed before commit.

## P2-T3 summary

- Red commit: `2aac26c` pinned `NegationSemantics`, SAFE default rejection, NEMO opt-in, strict-only defeasible default safety, and real Nemo conformance adapter routing.
- Green change: added `NegationSemantics.SAFE` / `NegationSemantics.NEMO` and exported it from `gunray`.
- Green change: restored the unsafe negation variable check in `_validate_program()` when mode is SAFE.
- Green change: threaded `negation_semantics` through `SemiNaiveEvaluator`, `DefeasibleEvaluator`, and `GunrayEvaluator`.
- Green change: conformance adapter fingerprints the Nemo negation fixture families and routes only those suite items to NEMO mode.
- Green change: removed the obsolete skip for `errors/review_v2_unsafe_negation::unsafe_negation_variable_only_in_negative_literal`; the fixture now passes under SAFE default.
- Green change: old review-v2 Nemo behavior tests now request `NegationSemantics.NEMO` explicitly.
- `uv run pytest tests/test_negation_semantics.py -v`: `5 passed`
- `uv run pytest tests/test_negation_semantics.py tests/test_evaluator_review_v2.py -v`: `7 passed`
- `uv run pytest tests -q`: `158 passed, 292 skipped, 3 deselected in 129.38s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `283 passed, 9 skipped, 3 deselected in 319.25s`
- `uv run pyright src`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`

## P3-T1 summary

- Red commit: `694688f` pinned `_unify()` treating `{"X": None}` as a bound value, not an absent binding.
- Green change: `_unify()` now uses `candidate.get(term.name, _UNBOUND)` and checks `is _UNBOUND` for binding absence.
- Audit note: nearby `is None` checks were left alone where they represent non-binding control flow or expression-evaluation failure, not direct binding absence in `_unify()`.
- `uv run pytest tests/test_evaluator_review_v2.py -v`: `3 passed`
- `uv run pytest tests -q`: `159 passed, 292 skipped, 3 deselected in 88.72s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `283 passed, 9 skipped, 3 deselected in 279.73s`
- `uv run pyright src/gunray/evaluator.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/evaluator.py tests/test_evaluator_review_v2.py`: `All checks passed!`

## P3-T2 summary

- Red commit: `e73e996` pinned `add_values()` accepting numeric pairs and rejecting mixed, string-only, and bool operands.
- Green change: `add_values()` now raises `SemanticError` for non-numeric and bool operands instead of string-concatenating.
- Audit: `rg -n -F "add_values" src tests ../datalog-conformance-suite/src/datalog_conformance/_tests` found only parser/evaluator call sites and the new tests; no fixture depended on string concatenation.
- `uv run pytest tests/test_semantics.py -v`: `4 passed`
- `uv run pytest tests -q`: `163 passed, 292 skipped, 3 deselected in 127.55s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `283 passed, 9 skipped, 3 deselected in 359.62s`
- `uv run pyright src/gunray/semantics.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/semantics.py tests/test_semantics.py`: `All checks passed!`
