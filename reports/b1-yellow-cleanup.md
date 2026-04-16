# B1.9 YELLOW cleanup report

## Summary

Cleared both YELLOW items from the B1 adversary review: (1) the
cosmetic `_find_blocking_peer` docstring tripwire in
`src/gunray/dialectic.py`, and (2) the missing Block 1 re-exports
from `src/gunray/__init__.py`. Total diff 29 content-line changes
(27 insertions + 2 modifications across two files), well under
the 50-line budget.

## Diffs applied

### `src/gunray/dialectic.py` (counter_argues docstring, ~line 93)

```diff
-    **Directional fix**: this implementation iterates *every*
-    sub-argument of ``target`` (via ``is_subargument`` per
-    ``arguments.py``) rather than comparing only root conclusions.
-    The deleted ``_find_blocking_peer`` never descended; that is the
-    whole point of this refactor.
+    **Directional fix**: this implementation iterates *every*
+    sub-argument of ``target`` (via ``is_subargument`` per
+    ``arguments.py``) rather than comparing only root conclusions.
+    The old atom-level blocking check never descended into
+    sub-arguments; descending is the whole point of this refactor.
```

### `src/gunray/__init__.py` (full rewrite — 27 insertions, 2 mods)

Added imports:

- `from .arguments import Argument, build_arguments, is_subargument`
  (added `build_arguments`)
- `from .dialectic import (DialecticalNode, answer, blocking_defeater,
  build_tree, counter_argues, mark, proper_defeater, render_tree)`
  (new import block)
- `from .disagreement import complement, disagrees, strict_closure`
  (new import)

Added `__all__` entries (alphabetically sorted): `DialecticalNode`,
`answer`, `blocking_defeater`, `build_arguments`, `build_tree`,
`complement`, `counter_argues`, `disagrees`, `mark`,
`proper_defeater`, `render_tree`, `strict_closure`.

Also fixed a pre-existing sort inversion in the original `__all__`
(`DefeasibleModel` was listed before `DatalogTrace`); the rewrite
restores proper alphabetical order per convention.

All 17 new symbols were verified to exist in the claimed modules
before any edit, satisfying the hard-stop directive.

## Verification

### Unit suite

```
$ uv run pytest tests -q -k "not test_conformance"
...
========== 1 failed, 106 passed, 295 deselected in 116.25s (0:01:56) ==========
```

- 106 passed, 1 failed, 0 skipped, 295 deselected.
- Single failure:
  `tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  — pre-existing Hypothesis-discovered failure unrelated to this
  cleanup (triggered on a theory with conflicting defaults
  `{a, ~a}` and the `true -> a` entailment question). Matches the
  prompt's expected baseline ("1 pre-existing fail").

### Pyright

```
$ uv run pyright src/gunray/__init__.py src/gunray/dialectic.py
0 errors, 0 warnings, 0 informations
```

### Deletion grep

```
$ rg '_can_prove|_find_blocking_peer|_has_blocking_peer|_has_live_opposition|_supporter_survives|_is_more_specific|_expand_candidate_atoms' src/ tests/
(no output — zero matches)
```

### Smoke import

```
$ uv run python -c "from gunray import Argument, Answer, build_arguments, disagrees, DialecticalNode, build_tree, mark, answer, render_tree, TrivialPreference; print('ok')"
ok
```

All four verification criteria met.

## Commits

- `d8eab6d` — `docs(dialectic): rewrite docstring that cited deleted _find_blocking_peer`
- `5196c20` — `feat(gunray): export Block 1 public surface from package __init__`

## One-line summary

B1.9 YELLOW cleanup complete: docstring tripwire cleared, Block 1
public surface re-exported from `gunray.__init__`; 29 diff lines,
106/1 pre-existing, pyright clean, deletion grep clean, smoke
import ok.
