# E6 — explanations gallery

Added `examples/explanations_gallery.py` printing the four-valued
answer, rendered dialectical tree, and `explain()` prose for six
canonical cases in fixed order:

1. Opus — `flies(opus)` = NO (penguin specificity).
2. Tweety — `flies(tweety)` = YES (uncontested).
3. Nixon diamond — `pacifist(nixon)` = UNDECIDED (blocking defeat).
4. Royal African elephant — `gray(clyde)` = YES.
5. Innocent until proven guilty, scenario B — `innocent` = NO
   (superiority + specificity over presumption).
6. Looks-red under red light, scenario B — `red(apple)` = UNDECIDED
   (Pollock undercutter).

Theories are copied inline from the peer example files and
`tests/test_specificity.py` with source citations per the prompt.

## Gates

- `uv run pytest tests -q` — 200 passed, 293 skipped.
- `uv run pyright examples/explanations_gallery.py` — clean.
- `uv run ruff check` / `ruff format --check` — clean.
- `uv run python examples/explanations_gallery.py` — exit 0.

## Commit

Built on top of `52615fd`; see the log for the SHA.
