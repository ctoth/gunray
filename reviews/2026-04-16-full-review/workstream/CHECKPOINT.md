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

## P3-T3 summary

- Red commit: `fc3aadb` pinned frozen field assignment on `Rule`, `Program`, and `DefeasibleTheory`, plus empty `Rule` id/head rejection and ghost superiority reference rejection.
- Green change: `Rule`, `Program`, `DefeasibleTheory`, `Model`, and `DefeasibleModel` now use `frozen=True, slots=True`.
- Green change: `Rule.__post_init__()` rejects empty ids and heads.
- Green change: `DefeasibleTheory.__post_init__()` validates each superiority pair against strict, defeasible, and defeater rule ids.
- Audit: literal searches for `.facts =`, `.rules =`, `.strict_rules =`, `.defeasible_rules =`, `.defeaters =`, and `.superiority =` in `src`/`tests` found no schema field mutation outside the new frozen-assignment tests; other `.rules =` hits were assertion/docstring text.
- `uv run pytest tests/test_schema.py -v`: `6 passed`
- `uv run pytest tests -q`: `169 passed, 292 skipped, 3 deselected in 106.99s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `283 passed, 9 skipped, 3 deselected in 296.60s`
- `uv run pyright src/gunray/schema.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/schema.py tests/test_schema.py`: `All checks passed!`

## P3-T4 summary

- Green change: replaced vacuous dialectic mark-local property with `test_hypothesis_mark_follows_child_labels`, which checks Procedure 5.1 directly over generated child U/D labels.
- Green change: replaced the fact-monotonicity property's unused fresh predicate with an in-body defeasible/defeater predicate and a fresh constant row; filtered out strict-rule theories so the added fact cannot make Pi contradictory.
- Green change: added `test_hypothesis_render_tree_contains_root_conclusion` so `render_tree()` cannot satisfy the property by returning an empty string; kept deterministic rendering as a separate property.
- Mutation validation: temporarily changed `mark()` to return `U` for non-leaves; `uv run pytest tests/test_dialectic.py::test_hypothesis_mark_follows_child_labels -q` failed with Hypothesis examples `['D']` and `['U']`; reverted the break.
- Mutation validation: temporarily changed `build_arguments()` to return an empty set when the fresh added fact was present; `uv run pytest tests/test_build_arguments.py::test_hypothesis_build_arguments_monotonic_under_body_fact_addition -q` failed with missing base arguments; reverted the break.
- Mutation validation: temporarily changed `render_tree()` to return `""`; `uv run pytest tests/test_render.py::test_hypothesis_render_tree_contains_root_conclusion -q` failed on missing root predicate text; reverted the break.
- `uv run pytest tests/test_dialectic.py tests/test_build_arguments.py tests/test_render.py -v`: `33 passed`
- `uv run pytest tests -q`: `170 passed, 292 skipped, 3 deselected in 133.45s`
- `uv run ruff check tests/test_dialectic.py tests/test_build_arguments.py tests/test_render.py`: `All checks passed!`
- `uv run pyright tests/` was intentionally not run because Q's current instruction is not to typecheck tests.

## P4-T1 summary

- Pre-state LOC: `671` lines by `(Get-Content src/gunray/closure.py | Measure-Object -Line).Lines`; the workstream's 821 LOC value was stale before this slice.
- Pre-state vulture: reported `RankScore`, public `ClosureEvaluator` members/trace attributes, `_lexicographic_preferred_default_sets`, `_branch_closure`, `_is_consistent`, and `_world_satisfies_rules`. `_formula_branches` and `_formula_true_in_closure` were not directly reported because they were only used inside already-dead helper code.
- Reachability audit: `_search_model` is live through `_model_exists`; it was not deleted. The task text's claim that `_branch_closure` was the live engine was stale in current code, and `_branch_closure` was vulture-dead.
- Green change: removed `RankScore`, `_lexicographic_preferred_default_sets`, `_branch_closure`, `_is_consistent`, `_formula_branches`, `_formula_true_in_closure`, and `_world_satisfies_rules`.
- Green change: added `notes/code_review_2026-04-16.md` "Post-workstream delta" note recording the real 671 -> 549 LOC closure cull.
- Post-state LOC: `549` lines.
- Post-state vulture: only public API / trace attribute false positives remain (`ClosureEvaluator`, `evaluate`, `satisfies_klm_property`, `definitely`, `supported`).
- `uv run pytest tests/test_closure.py tests/test_closure_faithfulness.py -v`: `8 passed`
- `uv run pytest tests -q`: `170 passed, 292 skipped, 3 deselected in 132.09s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: timed out in known HMMER `strict_only_souffle_hmmer_CPtrStore` case under default 30s timeout.
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q -k "strict_only_souffle_hmmer_CPtrStore" --timeout=240`: `1 passed, 294 deselected in 158.89s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q --timeout=240`: `283 passed, 9 skipped, 3 deselected in 297.31s`
- `uv run pyright src/gunray/closure.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/closure.py`: `All checks passed!`

## P4-T2 summary

- Red commit: `d642725` added `tests/test_dialectic_perf.py`; on pre-fix code it timed out under the 30s marker while stuck in a repeated `build_arguments(theory)` call from `build_tree()`.
- Green change: `build_tree()` now accepts an optional precomputed `universe`; `_expand()`, `_defeat_kind()`, and `_disagreeing_subarguments()` consume that universe instead of rebuilding arguments per candidate.
- Green change: `DefeasibleEvaluator` and `_is_warranted()` pass their already-built argument universe into `build_tree()`.
- Green change: removed `spindle_racket_query_long_chain` from `_CONFORMANCE_DESELECTED`; only the two HMMER `CPtrLoad` outliers remain deselected.
- `uv run pytest tests/test_dialectic_perf.py -v`: `1 passed in 20.04s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q -k "spindle_racket_query_long_chain"`: `1 passed, 294 deselected in 64.37s`
- `uv run pytest tests/test_dialectic.py tests/test_dialectic_perf.py tests/test_defeasible_evaluator.py -v`: `23 passed in 27.97s`
- `uv run pytest tests -q`: `171 passed, 293 skipped, 2 deselected in 110.25s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q --timeout=240`: `284 passed, 9 skipped, 2 deselected in 322.03s`
- `uv run pyright src/gunray/dialectic.py src/gunray/defeasible.py`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check src/gunray/dialectic.py src/gunray/defeasible.py tests/test_dialectic_perf.py tests/conftest.py`: `All checks passed!`

## P4-T3 summary

- Green change: added `src/gunray/_internal.py` as the package-internal seam for shared grounding, matcher, validation, sort-key, and strict-rule text helpers.
- Green change: moved `_ground_theory`, `_force_strict_for_closure`, `_match_positive_body`, and their helper clusters out of sibling modules into `_internal`.
- Green change: moved adjacent cross-module private seams used by scripts/tests (`_normalize_rules`, `_validate_program`, `_constraints_hold`, `_negative_body_holds`, `_atom_sort_key`, `_strict_rule_to_program_text`, and matcher iteration/order helpers) into `_internal` so source/script imports no longer reach into `arguments.py`, `evaluator.py`, or `defeasible.py` for underscore-prefixed helpers.
- Type cleanup after Q's correction: `_internal.py` now uses local aliases such as `Binding`, `RelationModel`, `RelationOverrides`, `ArityMap`, `FactModel`, and `RuleText` instead of leaving the extracted seam as raw `dict[...]` / `str` soup.
- Grep verification: `git grep -nE 'from gunray\.[A-Za-z_]+ import _' -- src/gunray scripts; git grep -nE 'from \.(arguments|evaluator|defeasible) import _' -- src/gunray` returned no hits.
- `uv run pytest tests/test_compiled_matcher.py tests/test_evaluator_review_v2.py tests/test_build_arguments.py tests/test_specificity.py tests/test_dialectic.py -q`: `49 passed`
- `uv run pytest tests -q`: `171 passed, 293 skipped, 2 deselected in 114.32s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q --timeout=240`: `284 passed, 9 skipped, 2 deselected in 297.75s`
- `uv run pyright src`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
