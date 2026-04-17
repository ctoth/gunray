# F-C mermaid checkpoint

## 2026-04-16

GOAL: Add `render_tree_mermaid(tree) -> str` to dialectic.py;
GitHub-native Mermaid flowchart emitter.

DONE:
- Added `render_tree_mermaid` in `src/gunray/dialectic.py` after
  `_render_child_lines`. Reuses `_mark_table`, `_sorted_children`,
  `_format_atom`, `_format_rule_ids`. Pre-order synthetic ids
  (`n0`, `n1`, ...). Edges emitted parent-first after nodes.
- Exported from `src/gunray/__init__.py` (imports + `__all__`).
- Added `tests/test_render_mermaid.py` mirroring
  `tests/test_render.py`: leaf, two snapshots (Tweety opus, Nixon
  diamond), determinism guard, two Hypothesis properties.

FILES:
- `src/gunray/dialectic.py` — emitter
- `src/gunray/__init__.py` — export
- `tests/test_render_mermaid.py` — tests

OBSERVED:
- `uv run pytest tests -q` — 200 passed, 293 skipped.
- `uv run pyright` — clean.
- `uv run ruff check` — clean.
- `uv run ruff format` — test file auto-reformatted (snapshot
  line joined on one long line; behavior unchanged).
- Mermaid test subset (6) passed standalone.

NEXT: Run conformance suite, write report, commit on top of 7be7da5.

STUCK: none.
