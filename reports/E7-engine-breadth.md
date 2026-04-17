# E7 — engine breadth

## Files added
- `examples/git_ancestry.py` — `GunrayEvaluator.evaluate(Program(...))`
  over a 7-commit DAG with a branch+merge; asserts
  `ancestor(c7, c1)` in the derived relation.
- `examples/klm_config_defaults.py` — `Policy.RATIONAL_CLOSURE` over a
  zero-arity `DefeasibleTheory` (db_down exceptional to
  server_responds); asserts `~server_responds` in `defeasibly` and
  `server_responds` in `not_defeasibly`.
- `examples/safe_vs_nemo.py` — one `Program` with
  `suspicious(X) :- person(X), not flagged(Y).` run twice; SAFE raises
  `SafetyViolationError`, NEMO returns a `Model` with
  `suspicious(alice)` and `suspicious(bob)`.

## KLM input type
`Policy.RATIONAL_CLOSURE` consumes `DefeasibleTheory` directly via
`adapter.py:40-46` which routes to `ClosureEvaluator.evaluate`; no
separate input type is required. The constraint is that
`_ensure_propositional` (closure.py:134) forbids defeaters,
superiority, conflicts, non-empty-arity facts, and literals containing
parentheses, so the example uses zero-arity atoms throughout.

## Gate
- `uv run pytest tests -q` — 200 passed, 293 skipped, 2 deselected.
- Conformance (`--datalog-evaluator=...GunrayConformanceEvaluator`) —
  284 passed, 9 skipped, 2 deselected.
- `uv run pyright` — 0 errors, 0 warnings.
- `uv run ruff check` — all checks passed.
- `uv run ruff format --check` — 70 files already formatted.

## Commit
Recorded after `git commit`.
