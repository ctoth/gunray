# B2.2b — Verify potential NameError in arguments.py

## Verdict

**NO-OP HARNESS NOISE.** The ninth stale harness-pyright false alarm.
`facts` is well-scoped; project pyright is silent; the unit suite is
green; the only conformance failures are the pre-existing
specificity-value mismatches that B2.3 is queued to fix, not NameError
crashes.

## Line 164 in reality

The harness report says
`src/gunray/arguments.py:164:30  "facts" is not defined`. The actual
line 164 of `src/gunray/arguments.py` post-commit `eaf538d` is:

```python
    pi_closure = strict_closure(fact_atoms, grounded_strict_rules)
```

No `facts` reference at column 30 of line 164. The harness diagnostic
is pointing at a line that doesn't contain the symbol it's flagging.

The only `_fact_atoms(facts)` call in the file is at **line 130**,
inside `_ground_theory`:

```python
def _ground_theory(theory: SchemaDefeasibleTheory) -> _GroundedTheory:
    ...
    facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)   # line 97
    ...
    return _GroundedTheory(
        fact_atoms=_fact_atoms(facts),                                      # line 130
        ...
    )
```

`facts` is a local variable bound on line 97 by tuple-unpacking the
return of `parse_defeasible_theory`. It is in scope at line 130. There
is no NameError possible — this is plain lexical-scope Python.

In `build_arguments` itself (line 137 onward), there is no `facts`
variable; the function uses `fact_atoms = grounded.fact_atoms` (line
161) via the `_GroundedTheory` dataclass produced by `_ground_theory`.

## Project pyright output

```
$ uv run pyright src/gunray/arguments.py
0 errors, 0 warnings, 0 informations
```

Clean. Zero diagnostics of any severity. The project's pyright
(strict) does not see `reportUndefinedVariable` or anything else on
`arguments.py`.

## Unit suite result

```
$ uv run pytest tests -q -k "not test_conformance and not test_closure_faithfulness"
...
114 passed, 298 deselected in 102.55s (0:01:42)
```

114 passed — matches the ~115 expected in the prompt. `build_arguments`
runs under every covering test. No NameError, no crash.

## Sanity conformance result (tweety / nixon / opus)

```
$ uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q -k "tweety or nixon or opus" --timeout=60
...
5 failed, 7 passed, 283 deselected in 65.68s (0:01:05)
```

All 5 failures are **ConformanceFailure value mismatches**, not
`NameError`. Representative failure:

```
datalog_conformance.runner.ConformanceFailure:
  maher_example2_tweety policy 'blocking' section 'defeasibly'
  predicate '~fly': expected [('freddie',), ('tweety',)], got [('freddie',)]
```

All 5 failures are tweety cases:
- `depysible_birds::depysible_not_flies_tweety`
- `depysible_birds::depysible_nests_in_trees_tweety`
- `depysible_birds::depysible_flies_tweety`
- `morris_example5_birds::morris_example5_tweety_blocked_default`
- `superiority/maher_example2_tweety::maher_example2_tweety`

These are the **expected pre-B2.3 residuals** — Block 2 landed
`GeneralizedSpecificity` in `preference.py` but has not yet wired it
into the dialectic dispatch (`B2.3: Policy routing + full green` is
still pending in the task list). They have nothing to do with an
undefined variable in `arguments.py` — if `facts` were genuinely
undefined, `build_arguments` would raise `NameError` and these tests
would error out during argument construction, not return a nearly
correct derivation set missing a single tweety row.

The seven tweety/nixon/opus cases that *pass* are additional evidence
that `build_arguments` is executing its full body, including the
grounding pipeline that routes through `_ground_theory` -> `_fact_atoms(facts)`.

## Confirmation that `facts` is in scope

| Location                         | How `facts` is bound                                    |
|----------------------------------|---------------------------------------------------------|
| `_ground_theory` line 97         | `facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)` |
| `_ground_theory` line 130 usage  | passed into `_fact_atoms(facts)` — in same function scope |
| `_fact_atoms` line 274 signature | `facts: Mapping[str, set[tuple[Scalar, ...]]]` — it's the parameter |
| `_positive_closure_for_grounding` line 285 signature | `facts: Mapping[str, set[tuple[Scalar, ...]]]` — also parameter |
| `build_arguments` line 137       | does not reference `facts` at all — uses `fact_atoms = grounded.fact_atoms` |

Every `facts` token in `arguments.py` is either a function parameter
or a local tuple-unpacked binding. There is no free `facts` reference
anywhere in the file.

## One-line summary

Harness pyright is reporting a `reportUndefinedVariable` on a line
that doesn't contain the symbol and on a variable that is properly
parameter-bound in every function that touches it; project pyright is
clean, the unit suite is green, and the conformance failures are the
pre-existing B2.3 specificity-routing gap, not a NameError — ninth
false alarm, no action taken.
