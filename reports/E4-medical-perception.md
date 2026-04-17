# E4 — Medical + perception

## Files

- `examples/clinical_drug_safety.py` — three-level specificity on
  aspirin safety via the strict chain
  `cardiac_event_patient -> warfarin_patient -> patient`. Three
  scenarios (alice/bob/carol) assert `YES / NO / YES`.
- `examples/looks_red_under_red_light.py` — Pollock 1995
  *Cognitive Carpentry* undercutter in the `defeaters` slot.
  Scenario A asserts `YES`; scenario B asserts that neither
  `red(apple)` nor `~red(apple)` is warranted.

## Gate

- `uv run pytest tests -q` — 200 passed, 293 skipped.
- `uv run pytest tests/test_conformance.py
  --datalog-evaluator=...GunrayConformanceEvaluator -q` —
  284 passed, 9 skipped, 2 deselected.
- `uv run pyright` — 0 errors.
- `uv run ruff check` + `ruff format --check` — clean.

## Note

Drug name quoted as `"aspirin"` in rule heads: the parser treats
unquoted lowercase identifiers as variables
(`src/gunray/parser.py:192`), so constants in rule terms must be
string-literal scalars.
