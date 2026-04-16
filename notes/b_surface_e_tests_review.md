# Surface E: tests review (analyst subagent)

## 2026-04-16 — checkpoint 3

### CONFIRMED FACTS

1. **Unit suite (no `--datalog-evaluator`)**: 139 passed / 292 skipped /
   3 deselected in 112.43s. Refactor doc claims 136 passed / 0 skipped
   / 1 pre-existing failure. **Drift**:
   - +3 passes (tests added since doc)
   - 292 "skipped" are conformance fixtures with no evaluator (expected)
   - The "1 pre-existing failure" closure_faithfulness now PASSES.
2. **`@given` count**: 45 across 12 files — matches doc.
3. **Conformance run**: 295 collected / 3 deselected / 292 selected.
   At ~67% complete in last poll (no failures shown yet). Background
   monitor bv8luqzyq awaits completion.
4. **`Policy.PROPAGATING`**: removed entirely from enum. No test
   verifies the deprecation. `evaluate_with_trace` does `del policy`,
   silently ignoring any value passed.
5. **`tests/test_defeasible_core.py`**: deleted; replaced by
   `test_defeasible_evaluator.py` and per-stage modules.
6. **Conftest deselects/skips**: 3 scalability deselects + 9 paper-
   anchored skips. `nemo_negation` is NOT in the skip list (only
   `unsafe_negation_variable_only_in_negative_literal` is).
7. **`DefeasibleTheory.conflicts`** field: 40 instances of
   `conflicts=[]` across 10 test files — never tested non-empty.

### KEY ISSUES

a. **Vacuous property tests**:
   - `test_dialectic.py::test_hypothesis_mark_is_local` — `del right_marks`,
     `if False else`, `right_children` constructed identical to
     `left_children`. Tests `mark(x) == mark(x)`, not locality.
   - `test_build_arguments.py::test_hypothesis_build_arguments_is_monotonic_in_facts`
     — adds fact under `__fresh_fact_predicate__` that no rule
     references. Trivially true.
   - `test_render.py::test_hypothesis_render_tree_is_deterministic` —
     only purity check, no correctness check.

b. **Hypothesis anti-patterns**:
   - `test_superiority.py::theory_with_random_superiority` uses
     `random.Random(seed)` inside a Hypothesis composite. Hypothesis
     cannot shrink through it.
   - `test_specificity.py` and `test_superiority.py` use `data.draw(idx)`
     on small `args` tuples → narrow exploration.

c. **Coverage holes**:
   - `Policy.PROPAGATING` deprecation untested.
   - `_is_strict_only_theory` not tested directly.
   - `CompositePreference` (both fire AND agree) — no labeled test.
   - `DefeasibleTheory.conflicts` non-empty — never exercised.
   - `nemo_negation` bug — only tickled via conformance suite, no
     minimal failing case in the unit suite.
   - Empty theory edge case — never tested.

d. **Performance bombs (untested)**:
   - `counter_argues` calls `_disagreeing_subarguments` which calls
     `build_arguments(theory)` again — every counter-attack check
     re-runs the full O(2^|Δ|) enumeration. `build_tree` then walks
     this for each candidate. No bound test, no perf assertion.
   - `SuperiorityPreference.__init__` runs an O(n^4)-ish iterative
     transitive-closure. Untested for large priority lists.
   - `evaluate_with_trace(theory, policy)` ignores `policy` silently.
     No test catches accidental policy passing.

### TESTS RUNNING

bv8luqzyq monitor waiting for conformance completion. Last log poll
showed ~67% pass with no failures yet. Will yield 250/44/1 or close
when done.

### DELIVERABLE STATUS

Have all evidence needed to write the surface-e-tests.md report.
`reviews/2026-04-16-full-review/` directory exists. Will wait briefly
for conformance completion (to give exact numbers) then write the
report. If conformance hasn't finished, report will say "in flight,
~67% with no failures observed" and not block on the final number.
