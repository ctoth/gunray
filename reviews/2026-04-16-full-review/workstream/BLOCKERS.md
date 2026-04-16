# Workstream blockers

## Baseline static-analysis failure

Status: resolved by preliminary unblocker cleanup.

- Task id: baseline capture before P0-T1
- Observed:
  - Unit baseline passed: `139 passed, 292 skipped, 3 deselected`.
  - Conformance baseline passed: `282 passed, 10 skipped, 3 deselected`.
  - `uv run pyright` failed before any workstream edits with 6 errors in `src/gunray/closure.py`.
  - `uv run ruff check` failed before any workstream edits with 21 violations.
- Tried:
  - Ran the exact four baseline commands requested by `workstream/README.md`.
  - Confirmed no tracked working-tree edits existed before baseline; only untracked `.hypothesis/`, `prompts/`, and `reviews/` were present.
- What I think is going on:
  - The current repo state is not the static-clean baseline described by the review. The code and tests pass dynamically, but existing type/lint debt predates this workstream execution.
- Specific question for review:
  - Should the baseline static-analysis failures be fixed as a preliminary hygiene commit outside P0-T1, or should the workstream expected baseline be amended to this current state before execution resumes?

Resolution:
- The user explicitly directed fixing the issues and unblocking the workstream.
- Static analysis was cleaned without changing workstream task semantics.
- `uv run pyright`, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest tests -q` now pass.

### Pyright failure

```text
src/gunray/closure.py:82:28 - error: Cannot assign to attribute "definitely" for class "DefeasibleTrace"
src/gunray/closure.py:83:27 - error: Cannot assign to attribute "supported" for class "DefeasibleTrace"
src/gunray/closure.py:282:5 - error: Type annotation is missing for parameter "score"
src/gunray/closure.py:320:9 - error: Type of "world_score" is unknown
src/gunray/closure.py:323:13 - error: Type of "best_score" is unknown
6 errors, 0 warnings
```

### Ruff failure

```text
uv run ruff check
Found 21 errors.
```

Representative categories:
- unsorted import blocks in `src/gunray/arguments.py` and multiple tests
- unused imports in `tests/test_build_arguments.py`
- long lines in `src/gunray/dialectic.py`, `tests/test_closure.py`, and `tests/test_closure_faithfulness.py`
