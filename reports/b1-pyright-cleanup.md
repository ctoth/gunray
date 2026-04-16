# B1.2b — Pyright cleanup after scorched earth

Dispatch: `prompts/b1-pyright-cleanup.md`. Expected work: patch
`src/gunray/defeasible.py` for a missing `defaultdict` import, annotate
two keep-list helpers with `# pyright: ignore[reportUnusedFunction]`,
silence an unused `policy` parameter, and trace the root cause of the
test-file type-unknown errors.

## Verdict: no-op. Targeted files are already clean.

HEAD at dispatch time is `9cefb43` — the tip of the B1.2 scorched
earth series. No drift from the B1.2 commits. Pyright on the exact
verification command from the prompt reports zero diagnostics:

```
$ uv run pyright src/gunray/defeasible.py src/gunray/arguments.py \
    src/gunray/answer.py src/gunray/preference.py \
    tests/test_arguments_basics.py tests/test_answer.py \
    tests/test_preference.py
0 errors, 0 warnings, 0 informations
```

JSON form on `src/gunray/defeasible.py` alone:

```json
{
    "version": "1.1.408",
    "generalDiagnostics": [],
    "summary": {
        "filesAnalyzed": 1,
        "errorCount": 0,
        "warningCount": 0,
        "informationCount": 0
    }
}
```

Unit suite (`uv run pytest tests -q -k "not test_conformance"`):
`51 passed, 3 skipped, 1 failed` — identical to the B1.2 baseline.
The one failure is `test_closure_faithfulness.py::test_formula_
entailment_matches_ranked_world_reference_for_small_theories`,
unrelated to defeasible / arguments / answer / preference, and
pre-existed the dispatch.

## 1. Why each diagnostic group does not fire

### `reportUndefinedVariable` / "defaultdict" on defeasible.py:89

Stale. Line 89 of the current `src/gunray/defeasible.py` is:

```python
def _atoms_to_section(atoms: set[GroundAtom]) -> dict[str, set[FactTuple]]:
    section: dict[str, set[FactTuple]] = {}
    for atom in atoms:
        section.setdefault(atom.predicate, set()).add(atom.arguments)
    return section
```

It uses `dict.setdefault`, not `defaultdict`. `defaultdict` is neither
imported nor referenced, so there is no undefined-variable error to
fix. The prompt's diagnostic list appears to reference a version of
`_atoms_to_section` that was rewritten before B1.2 landed; the file
that reached `9cefb43` already uses the `dict.setdefault` form.

### `reportUnusedFunction` on `_evaluate_strict_only_theory` and `_atoms_to_section`

Globally suppressed. `pyproject.toml` has:

```toml
[tool.pyright]
...
reportUnusedFunction = "none"
```

So the two keep-list helpers reserved for B1.6 do not need
per-function `# pyright: ignore` annotations. The project-level
config already silences the rule.

### Unused `policy` parameter in `evaluate` / `evaluate_with_trace`

Pyright does not report this under the current strict config for
this file. The parameter is part of the public signature and is
consumed by the type system (it appears in the function signature
annotated as `Policy`); pyright strict mode does not warn on
unreferenced parameters unless `reportUnusedParameter` is promoted,
and it is not promoted in `pyproject.toml`. A cosmetic `del policy`
with a B1.6 comment would satisfy an imaginary warning and add
noise to a stable contract; I did not add it.

### Test-file type-unknown errors

Could not reproduce. Invoking pyright explicitly on
`tests/test_arguments_basics.py tests/test_answer.py
tests/test_preference.py` reports 0 errors. `Argument`,
`is_subargument`, `Answer`, `YES`, `NO`, and the conftest strategy
all resolve to known types. Relevant pieces observed:

- `src/gunray/arguments.py` uses `from __future__ import annotations`
  and defines `@dataclass(frozen=True, slots=True) class Argument`
  with explicit field annotations (`rules: frozenset[
  GroundDefeasibleRule]`, `conclusion: GroundAtom`). Pyright can
  infer the constructor's return type without help.
- `tests/test_arguments_basics.py` imports
  `from gunray.arguments import Argument, is_subargument` — explicit
  names, not a wildcard.
- `tests/conftest.py`'s `arguments_strategy` has an explicit return
  type annotation.
- `src/gunray/__init__.py` re-exports via explicit names, preserving
  the type binding.

One non-obvious contributor: `pyproject.toml` sets
`include = ["src"]`, so a default `uv run pyright` invocation does
not analyze `tests/` at all. The verification command in the prompt
overrides this by passing explicit test paths, which is how I
reproduced the (zero-diagnostic) result.

## 2. Diff applied

None. Zero lines modified. 0/30 of the budget consumed.

## 3. Pyright output before and after

Identical (they are the same run — no patch was applied):

```
0 errors, 0 warnings, 0 informations
```

## 4. Commit hashes

None. No commits produced, because no code changed. Per the "do
not improvise" directive in the dispatch and the completion-criteria
rule ("show evidence"), manufacturing a cosmetic commit to satisfy
the dispatch header would be worse than reporting the observed
state.

If Q wants the `del policy` comment / the per-function
`# pyright: ignore` annotations added anyway (defensive, in case a
future pyright config tightens), the patch is obvious and fits in
well under 30 lines — say the word.

## 5. One-line summary

Targeted files already satisfy strict pyright at HEAD `9cefb43`;
the prompt's diagnostic list was stale, so this dispatch is a
confirmed no-op.
