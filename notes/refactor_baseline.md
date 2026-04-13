# Refactor Baseline — 2026-04-13

## 1. Unit test pass count and time

Command:

```
uv run pytest tests -q --durations=0 -k "not test_conformance"
```

Output (trimmed to headers, slowest durations, and summary):

```
platform win32 -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Q\code\gunray
configfile: pyproject.toml
plugins: datalog-conformance-0.1.0, hypothesis-6.151.12, timeout-2.4.0
timeout: 30.0s
timeout method: thread
timeout func_only: False
collected 346 items / 295 deselected / 51 selected

tests\test_closure.py ....                                               [  7%]
tests\test_closure_faithfulness.py .F.                                   [ 13%]
tests\test_compiled_matcher.py ......                                    [ 25%]
tests\test_defeasible_core.py .......                                    [ 39%]
tests\test_evaluator_review_v2.py .                                      [ 41%]
tests\test_parser_properties.py .................                        [ 74%]
tests\test_parser_review_v2.py ....                                      [ 82%]
tests\test_trace.py .........                                            [100%]

================================== FAILURES ===================================
__ test_formula_entailment_matches_ranked_world_reference_for_small_theories __
...
>           assert actual is expected
E           assert True is False
E           Falsifying example: test_formula_entailment_matches_ranked_world_reference_for_small_theories(
E               raw_theory=(
E                   frozenset([]),
E                   (),
E                   (('a', ()), ('~a', ())),
E               ),
E               data=data(...),
E           )
E           Draw 1 (antecedent): ('true',)
E           Draw 2 (consequent): (lambda item: ('literal', item))('a')
tests\test_closure_faithfulness.py:137: AssertionError
============================== slowest durations ==============================
3.00s call     tests/test_closure.py::test_or_counterexample_fails_only_for_relevant_closure
2.00s call     tests/test_closure_faithfulness.py::test_or_property_matches_ranked_world_reference_for_small_theories
1.54s call     tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories
1.21s call     tests/test_parser_properties.py::test_split_top_level_property_round_trips_generated_top_level_items
0.35s call     tests/test_parser_properties.py::test_parse_rule_text_property_partitions_body_items_by_kind
0.17s call     tests/test_parser_properties.py::test_parse_constraint_text_property_preserves_operator
0.17s call     tests/test_parser_properties.py::test_is_constraint_property_only_matches_top_level_comparisons
0.16s call     tests/test_trace.py::test_datalog_trace_property_captured_rows_land_in_final_model
0.16s call     tests/test_trace.py::test_datalog_trace_property_find_rule_fires_matches_manual_filter
0.15s call     tests/test_trace.py::test_strict_only_trace_property_matches_definite_section
(139 durations < 0.005s hidden.  Use -vv to show these durations.)
=========================== short test summary info ===========================
FAILED tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories
================ 1 failed, 50 passed, 295 deselected in 57.33s ================
```

Summary: **50 passed, 1 failed, 295 deselected, wall time 57.33s**.

## 2. Conformance suite pass count and time

Command:

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120
```

Output (head, representative failure, and summary):

```
platform win32 -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Q\code\gunray
configfile: pyproject.toml
plugins: datalog-conformance-0.1.0, hypothesis-6.151.12, timeout-2.4.0
timeout: 120.0s
timeout method: thread
timeout func_only: False
collected 295 items

tests\test_conformance.py FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF [ 15%]
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF [ 40%]
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF [ 64%]
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF [ 88%]
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF                                [100%]

Representative failure (all 295 failures share this error mode):

    runner.run_test_case(case)
...
>       raise TypeError(f"Unsupported input type: {type(item).__name__}")
E       TypeError: Unsupported input type: Program

============================ 295 failed in 51.60s =============================
```

Summary: **0 passed, 295 failed, 0 xfail/skipped, wall time 51.60s**.

Anomaly: every conformance case fails with `TypeError: Unsupported input type: Program`. No timeout observed for `strict_only_souffle_hmmer_CPtrLoad` — it failed fast with the same TypeError like every other case. The Dispatch P0.2 perf issue is masked by this adapter-level breakage and cannot be measured from this run.

## 3. LOC of the defeasible module

Command:

```
wc -l src/gunray/defeasible.py
```

Output:

```
784 src/gunray/defeasible.py
```

## 4. LOC of all gunray source

Command:

```
wc -l src/gunray/*.py
```

Output:

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

Output:

```
1
```

Note: the single match is the pytest plugin banner line `plugins: datalog-conformance-0.1.0, hypothesis-6.151.12, timeout-2.4.0`, not a test ID. Actual hypothesis-strategy-based test count per the exact command as written: **1** (which is spurious). The true number of Hypothesis `@given` test functions is not captured by this command and is left as written per prompt instructions.

## 6. Paper-citation count in source docstrings

Grep tool counts across `src/gunray/`:

- Pattern `Garcia.*200[4]`: 0 matches (0 files)
- Pattern `Simari.*199[2]`: 1 match (1 file: `src/gunray/defeasible.py`)

Sum: **1**.

## 7. Git HEAD commit hash at start

Command:

```
git rev-parse HEAD
```

Output:

```
5078df5ee65ae17ee2a614299ba395ed8a7664d9
```

## 8. Dirty-state snapshot

Command:

```
git status --short
```

Output:

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

Captured before creating `notes/refactor_baseline.md`; this file will add an additional untracked entry after creation.

## Post-adapter-fix conformance

After P0.1.5 (`fix(adapter): ...`), re-running the same command under
the public `gunray.adapter.GunrayEvaluator` entry point:

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120
```

Summary: **267 passed, 28 failed, 0 xfail/skipped, wall time 457.01s**
(previously 0 passed, 295 failed, 51.60s).

This is the real baseline for the Block 2 gate. The section above is
retained for history.

Notable observations:

- All 28 failures share the same error: `SafetyViolationError:
  Variables in negated literals must be positively bound`, and all are
  `nemo_negation` cases (14 under `defeasible/strict_only/` and the
  corresponding 14 under `negation/`). This is an engine-level
  negation-safety bug, independent of the adapter boundary.
- The three `depysible_nests_in_trees_*` cases (`tina`, `tweety`,
  `henrietta`) PASS under the public adapter. The P0.1.5 prompt
  expected them to fail — they do not in this environment.
- The two `*souffle_hmmer_CPtrLoad` cases (`strict_only_*` and
  the plain `souffle_hmmer_CPtrLoad`) PASS. Targeted run of the 5
  `-k "nests_in_trees or CPtrLoad"` cases completes in 227.51s,
  so the CPtrLoad case is taking roughly 100s each — slow enough
  that the P0.2 perf concern is real, but under the 120s per-case
  timeout in this run, so they register as passes rather than
  timeouts.
- The pre-existing closure faithfulness unit-test failure is still
  present: `tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  — unchanged from Section 1 above and from the P0.1 snapshot.
