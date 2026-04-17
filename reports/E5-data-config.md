# E5 — data fusion + config precedence

Two examples added on top of `a50e596`.

## Files

- `examples/data_fusion_sources.py` — three sources disagree on
  Einstein's birth year; explicit `superiority`
  (biography > official > wikipedia) resolves it. Zero-arity-per-year
  predicates (`born_1879`, `born_1880`) avoid multi-valued `conflicts`.
  Assert: `born_1879(einstein)=YES`, `born_1880(einstein)=NO`.
- `examples/config_precedence.py` — strict chain
  `safe_mode → kill_switch → env_override → default_on` lets
  `GeneralizedSpecificity` order four alternating defaults
  d4 > d3 > d2 > d1 with no `superiority` pairs. Four scenarios assert
  the cascade YES/NO/YES/NO.

## Gate

- `uv run pytest tests -q` — 200 passed, 293 skipped, 2 deselected.
- `uv run pyright` — 0 errors.
- `uv run ruff check` — All checks passed.
- `uv run ruff format --check` on both new files — already formatted.

Both scripts execute and all asserts pass.
