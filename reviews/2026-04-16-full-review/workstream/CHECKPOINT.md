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
- `uv run pyright`: `0 errors, 0 warnings, 0 informations`
- `uv run ruff check`: `All checks passed!`
- `uv run ruff format --check`: `46 files already formatted`
- `uv run pytest tests -q`: `139 passed, 292 skipped, 3 deselected in 96.74s`
- `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q`: `282 passed, 10 skipped, 3 deselected in 316.77s`
