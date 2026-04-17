# F-C — `render_tree_mermaid` emitter

## Implementation

- `src/gunray/dialectic.py`: added `render_tree_mermaid(tree) -> str`
  after `_render_child_lines`. Reuses `_mark_table`,
  `_sorted_children`, `_format_atom`, `_format_rule_ids`. Pre-order
  synthetic ids (`n0`, `n1`, ...); edges emitted parent-first after
  all node declarations. Pure, deterministic.
- `src/gunray/__init__.py`: imported `render_tree_mermaid` and added
  to `__all__`.

## Tests

- `tests/test_render_mermaid.py` mirrors `tests/test_render.py`:
  leaf-case, Tweety opus snapshot (byte-for-byte `==`), Nixon diamond
  snapshot, determinism guard, two Hypothesis property tests.

## Gate (all green)

- `uv run pytest tests -q` — 200 passed, 293 skipped.
- Conformance suite — 284 passed, 9 skipped, 2 deselected.
- `uv run pyright` — 0 errors.
- `uv run ruff check` — clean.
- `uv run ruff format --check` — clean.
