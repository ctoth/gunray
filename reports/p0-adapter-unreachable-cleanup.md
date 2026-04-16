# P0.1.6 — Adapter unreachable-code cleanup: diagnosis-only, no-op

Date: 2026-04-13
Status: STOPPED at diagnosis per the prompt's hard-stop directive. No
source changes made.

## Summary

The three `reportUnreachable` warnings the prompt cites at
`src/gunray/adapter.py` lines 42, 61, 71 do not reproduce against the
current working tree under pyright 1.1.408 with the project's strict
configuration. adapter.py is already clean. There is nothing to fix
inside the requested ≤10-line budget.

## Diagnosis

### What the prompt expected

> pyright narrows `item` (typed `Program | DefeasibleTheory`) to
> `Never` after the `isinstance` chain, and flags the
> `_suite_bridge()` fallthrough as unreachable.

### What I actually observed

Every pyright invocation I could construct against adapter.py returned
zero diagnostics:

1. Scoped run (strict + project config):
   ```
   > uv run pyright src/gunray/adapter.py
   0 errors, 0 warnings, 0 informations
   ```
2. Full project run (for context):
   ```
   > uv run pyright
   ... c:\Users\Q\code\gunray\src\gunray\closure.py (2 errors)
   ... c:\Users\Q\code\gunray\src\gunray\defeasible.py (2 errors)
   4 errors, 0 warnings, 0 informations
   ```
   adapter.py is not in the diagnostic list. The 4 pre-existing errors
   live in closure.py and defeasible.py and are out of scope for this
   P0.
3. Forced `reportUnreachable` via a throwaway pyright config that
   inherited the project's strict settings and then set
   `reportUnreachable = "error"` (I wrote, ran, and deleted
   `pyrightcheck.json`; it is not in the commit):
   ```
   > uv run pyright -p pyrightcheck.json
   0 errors, 0 warnings, 0 informations
   ```
4. JSON output confirming zero generalDiagnostics:
   ```
   > uv run pyright --outputjson src/gunray/adapter.py
   { ... "errorCount": 0, "warningCount": 0, "informationCount": 0 ... }
   ```

pyright version: `pyright 1.1.408`.

### Why the prompt's prediction did not hold

Reading `src/gunray/adapter.py` as it stands after commit `f4f05af`:

- `evaluate` is annotated `item: Program | DefeasibleTheory`.
- `evaluate_with_trace` is annotated the same.
- `satisfies_klm_property` is annotated `theory: DefeasibleTheory`.

Each fallthrough line is a `return self._suite_bridge().<method>(...)`
call with a `# type: ignore[attr-defined]` comment. The prompt's
theory was that after the `isinstance` chain pyright narrows `item` to
`Never` and flags the fallthrough as unreachable. In principle that
narrowing should happen. In practice this pyright build does not
report an unreachable diagnostic there; the only diagnostic such a
line could have attracted is `reportAttributeAccessIssue` (calling
`.evaluate` on `object`), and the existing
`# type: ignore[attr-defined]` already silences that.

I did not investigate further why pyright 1.1.408 chooses not to mark
the fallthroughs as unreachable — could be version-specific narrower
behavior, could be interaction with the `# type: ignore` line, could
be that strict mode defaults `reportUnreachable` to `"none"` in this
build even when other strict checks are active. I did not verify
which, because the observable contract Q cares about ("pyright stays
clean on adapter.py") already holds.

## Changes

None. adapter.py is byte-for-byte identical to the tip of
`f4f05af`/`4325eb4`.

```
> git diff HEAD -- src/gunray/adapter.py
(empty)
```

## Verification

Per the prompt's Step 3 checklist, even though no fix was applied:

### pyright on adapter.py
```
> uv run pyright src/gunray/adapter.py
0 errors, 0 warnings, 0 informations
```

### Unit suite (excluding conformance)
```
> uv run pytest tests -q -k "not test_conformance"
1 failed, 50 passed, 295 deselected in 54.94s
```
The single failure is
`tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
— the known closure faithfulness fail flagged by
`notes/defeasible_conformance.md` and carried forward from the P0.1.5
baseline. 50/50 non-closure-faithfulness tests pass. Matches the
baseline the prompt described.

### Conformance collect
```
> uv run pytest tests/test_conformance.py \
    --datalog-evaluator=gunray.adapter.GunrayEvaluator \
    -q --timeout=120 -x --co
...
295 tests collected in 60.92s (0:01:00)
```
No collection errors. 295 tests enumerated, matching the P0.1.5
denominator.

## Commit hash

No commit produced. adapter.py has no changes to commit. Creating an
empty commit would be dishonest about the state of the tree and
violates CLAUDE.md's "only describe what you verified" rule: I cannot
honestly author a "clean up unreachable-code warnings" commit when
there are no warnings to clean up.

## Recommended next step

Close P0.1.6 as a no-op. If the original warnings were observed in an
IDE-embedded pyright (VS Code Pylance, or a different pyright build
pinned by some other environment), capture the exact invocation and
version that produced the output quoted in the prompt, and re-run the
cleanup against that environment — the fix the prompt anticipates
(widen `item` to `object` and drop the `# type: ignore[attr-defined]`
tags in favor of a runtime-level dispatch) is still the right shape
if those warnings reappear. The 4 unrelated pyright errors currently
in `closure.py` and `defeasible.py` are separate work; flag them for a
follow-up P0 if the project's "pyright stays clean" rule is meant
globally and not just for adapter.py.

## One-line summary

adapter.py already passes pyright cleanly under the project's strict
config; the P0.1.5-attributed `reportUnreachable` warnings do not
reproduce, so no code change is warranted.
