# P0.1 — Baseline snapshot report

Baseline file: `C:\Users\Q\code\gunray\notes\refactor_baseline.md`

## 1. Unit test pass count and time

Command:

```
uv run pytest tests -q --durations=0 -k "not test_conformance"
```

Summary: **50 passed, 1 failed, 295 deselected, wall time 57.33s**.

Failing test: `tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`

Failing example (Hypothesis-shrunk):

```
raw_theory = (frozenset([]), (), (('a', ()), ('~a', ())))
antecedent = ('true',)
consequent = ('literal', 'a')
gunray._formula_entails -> True
suite reference _formula_entails -> False
assert True is False
```

## 2. Conformance suite pass count and time

Command:

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120
```

Summary: **0 passed, 295 failed, 0 xfail/skipped, wall time 51.60s**.

Every case fails with the same adapter-level error:

```
>       raise TypeError(f"Unsupported input type: {type(item).__name__}")
E       TypeError: Unsupported input type: Program
```

The known slow case `strict_only_souffle_hmmer_CPtrLoad` did not time out in this run — it failed fast with the same `TypeError: Unsupported input type: Program` as every other conformance case. The P0.2 perf signal is currently masked by this adapter breakage.

## 3. LOC of the defeasible module

```
784 src/gunray/defeasible.py
```

## 4. LOC of all gunray source

```
    30 src/gunray/__init__.py
    59 src/gunray/adapter.py
    39 src/gunray/ambiguity.py
   699 src/gunray/closure.py
     9 src/gunray/compile.py
   241 src/gunray/compiled.py
   141 src/gunray/conformance_adapter.py
   784 src/gunray/defeasible.py
    39 src/gunray/errors.py
   732 src/gunray/evaluator.py
   415 src/gunray/parser.py
    80 src/gunray/relation.py
    83 src/gunray/schema.py
    79 src/gunray/semantics.py
   116 src/gunray/stratify.py
     9 src/gunray/tolerance.py
   218 src/gunray/trace.py
   103 src/gunray/types.py
  3876 total
```

## 5. Hypothesis property test count

Command:

```
uv run pytest tests --collect-only -q 2>&1 | grep -i hypothesis | wc -l
```

Output: **1**.

The single match is the pytest plugin banner line (`plugins: ... hypothesis-6.151.12 ...`), not an actual test ID. The command as written does not select test identifiers; the literal recorded number is 1 per the prompt's instructions.

## 6. Paper-citation count in source docstrings

Grep tool matches across `src/gunray/`:

- `Garcia.*200[4]`: 0 matches
- `Simari.*199[2]`: 1 match (`src/gunray/defeasible.py`)

Sum: **1**.

## 7. Git HEAD commit hash at start

Omitted per prompt (no commit is being produced by this dispatch). Recorded in baseline file.

## 8. Dirty-state snapshot

```
 M notes/cptrload_timeout_analysis.md
 M out
?? .hypothesis/
?? notes/defeasible_conformance.md
?? notes/readme_rewrite.md
?? notes/what_sucks_review.md
?? prompts/
?? src/gunray.tar
```

Captured before `notes/refactor_baseline.md` was created.

## Failures and anomalies observed

1. **Unit test failure — closure faithfulness.** Gunray's reduced `_formula_entails` says `True` for an entailment that the ranked-world reference oracle says is `False`, given the contradictory defeasible theory `(('a', ()), ('~a', ()))` with antecedent `true` and consequent `a`. This is a correctness divergence from the Morris 2020 Algorithms 3-6 reference, not a flake.
2. **Conformance suite total breakdown.** 0 of 295 cases pass. Every failure is the same `TypeError: Unsupported input type: Program` raised from the adapter. This means the `--datalog-evaluator=gunray.adapter.GunrayEvaluator` entry point is handing the runner a `Program` object that the runner/evaluator does not know how to consume. Whatever changed recently about the adapter contract or suite expectation, the two sides no longer agree.
3. **`strict_only_souffle_hmmer_CPtrLoad` status unmeasurable.** The prompt flagged this case as the known P0.2 perf issue. In this run it did not time out — it failed fast with the same `TypeError` as everything else — so no wall-time signal for the perf regression exists in this baseline.
4. **Hypothesis test count command is degenerate.** The pipeline `collect-only -q ... | grep -i hypothesis | wc -l` matches only the pytest plugin banner, not test IDs. Recording 1 per instructions.

## One-line summary

baseline recorded; 50 unit pass / 0 conformance pass
