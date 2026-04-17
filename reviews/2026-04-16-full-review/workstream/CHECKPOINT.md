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
