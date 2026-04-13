# P0.1.5 — Adapter TypeError Fix Report

## 1. Diagnosis

### Symptom

Running the conformance suite via the public adapter entry point

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120
```

failed every one of the 295 cases with the identical error at
`src/gunray/adapter.py:32`:

```
raise TypeError(f"Unsupported input type: {type(item).__name__}")
TypeError: Unsupported input type: Program
```

### Root cause

Commit **`9aae5ab` — "Decouple Gunray runtime from conformance
schema"** (2026-04-12) changed the imports at the top of
`src/gunray/adapter.py` from

```python
from datalog_conformance.schema import DefeasibleTheory, Policy, Program
```

to

```python
from .schema import DefeasibleTheory, Policy, Program
```

where `.schema` is the new gunray-native module introduced in the
same commit.

The conformance runner (`datalog_conformance.runner.YamlTestRunner`)
still constructs instances of **`datalog_conformance.schema.Program`**
and `DefeasibleTheory` and passes them to
`evaluator.evaluate(case.program)`. The `isinstance` dispatch in
`GunrayEvaluator.evaluate` checks against the gunray-native types,
which are now different classes with the same `__name__`, so every
isinstance check returns False and the dispatch hits the `raise
TypeError` branch. Hence the error message says `Program` but
isinstance says no — two different classes named `Program`.

The same commit introduced `src/gunray/conformance_adapter.py` with a
`GunrayConformanceEvaluator` that already contains the bridge
logic (`_translate_program`, `_translate_theory`, `_translate_policy`).
But nothing glued that bridge back to `GunrayEvaluator`. The public
adapter — which propstore consumes and which `tests/test_conformance.py`
uses for the baseline — was orphaned from the suite's type graph.

Git blame on the `raise` line shows `eed751ac` (the original commit
that created the file) — the literal line text is original — but the
actual regression was introduced by `9aae5ab` flipping the import
source so that it can no longer match suite-native inputs.

### Why isinstance was returning False on a class called `Program`

The error message renders `type(item).__name__`, which is the string
`"Program"`. But the gunray-native `Program` dataclass in
`src/gunray/schema.py` is unrelated by inheritance to
`datalog_conformance.schema.Program`. The runner constructs the
suite class; the adapter checks against the native class; isinstance
correctly returns False. This is the "stale import aliasing" failure
mode listed in the prompt.

## 2. Fix

Single-file edit to `src/gunray/adapter.py`: instead of raising
TypeError on a non-native input, lazily instantiate
`GunrayConformanceEvaluator`, rebind its `_core` to `self` so the
bridge reuses the same engine instances, and delegate the call. This
keeps the fast-path unchanged for gunray-native inputs and reuses
the existing (already-tested) translation logic for suite inputs.

```diff
diff --git i/src/gunray/adapter.py w/src/gunray/adapter.py
index ad7e8bd..4814912 100644
--- i/src/gunray/adapter.py
+++ w/src/gunray/adapter.py
@@ -16,6 +16,16 @@ class GunrayEvaluator:
         self._datalog = SemiNaiveEvaluator()
         self._defeasible = DefeasibleEvaluator()
         self._closure = ClosureEvaluator()
+        self._bridge: object | None = None
+
+    def _suite_bridge(self) -> object:
+        if self._bridge is None:
+            from .conformance_adapter import GunrayConformanceEvaluator
+
+            bridge = GunrayConformanceEvaluator()
+            bridge._core = self  # reuse this evaluator's engines
+            self._bridge = bridge
+        return self._bridge

     def evaluate(self, item: Program | DefeasibleTheory, policy: Policy | None = None) -> object:
         if isinstance(item, Program):
@@ -29,7 +39,7 @@ class GunrayEvaluator:
             }:
                 return self._closure.evaluate(item, actual_policy)
             return self._defeasible.evaluate(item, actual_policy)
-        raise TypeError(f"Unsupported input type: {type(item).__name__}")
+        return self._suite_bridge().evaluate(item, policy)  # type: ignore[attr-defined]

     def evaluate_with_trace(
         self,
@@ -48,7 +58,7 @@ class GunrayEvaluator:
             }:
                 return self._closure.evaluate_with_trace(item, actual_policy, trace_config)
             return self._defeasible.evaluate_with_trace(item, actual_policy, trace_config)
-        raise TypeError(f"Unsupported input type: {type(item).__name__}")
+        return self._suite_bridge().evaluate_with_trace(item, policy, trace_config)  # type: ignore[attr-defined]

     def satisfies_klm_property(
         self,
@@ -56,4 +66,6 @@ class GunrayEvaluator:
         property_name: str,
         policy: Policy,
     ) -> bool:
-        return self._closure.satisfies_klm_property(theory, property_name, policy)
+        if isinstance(theory, DefeasibleTheory):
+            return self._closure.satisfies_klm_property(theory, property_name, policy)
+        return self._suite_bridge().satisfies_klm_property(theory, property_name, policy)  # type: ignore[attr-defined]
```

Diff size: `src/gunray/adapter.py | 18 +++++++++++++++---` — 15
insertions, 3 deletions. One file touched. No signature changes. No
new top-level imports (the `GunrayConformanceEvaluator` import is
function-scoped inside `_suite_bridge` to avoid a circular import at
module load; `conformance_adapter` imports `adapter`, so an
unconditional top-level import would loop).

## 3. Verification

### Full conformance suite

Command (same as the baseline):

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120
```

Result: **267 passed, 28 failed, 0 xfail/skipped, wall time
457.01s** (pre-fix: 0 passed, 295 failed, 51.60s).

All 28 failures share the same root cause and are all
`nemo_negation` cases:

- 14 under `defeasible/strict_only/strict_only_negation_nemo_negation::strict_only_nemo_negation_*`
- 14 under `negation/nemo_negation::nemo_negation_*`

Every one of them raises
`gunray.errors.SafetyViolationError: Variables in negated literals
must be positively bound` at `src/gunray/evaluator.py:121`. This is
an engine-level negation safety bug; the adapter boundary is no
longer implicated. Out of scope for this dispatch.

### `depysible_nests_in_trees_*`

The prompt expected these three cases to fail as the bug the
Block 1 refactor will fix. **They currently pass** under the public
adapter:

```
tests/test_conformance.py::test_yaml_conformance[defeasible/basic/depysible_birds::depysible_nests_in_trees_tina] PASSED
tests/test_conformance.py::test_yaml_conformance[defeasible/basic/depysible_birds::depysible_nests_in_trees_tweety] PASSED
tests/test_conformance.py::test_yaml_conformance[defeasible/basic/depysible_birds::depysible_nests_in_trees_henrietta] PASSED
```

None appear in the failure list of the full run; a targeted
`-k "nests_in_trees or CPtrLoad"` run shows all 5 matching cases
passing. **Flagging this finding verbatim** rather than dismissing
it: the Block 1 plan's assumption that `nests_in_trees` needs to
be fixed should be re-verified against the current master state
before the foreman dispatches B1.6.

### `strict_only_souffle_hmmer_CPtrLoad`

The prompt asked whether this case times out or completes. **It
completes** — no timeout observed in either the full run or the
targeted `-k` run (which took 227.51s for 5 cases, implying
~100s per CPtrLoad case). Slow but under the 120s per-case
timeout in this environment. The P0.2 perf bug is visible as
wall-time pressure but does not mark the case as failed. Noted
for P0.2, no action taken here.

### Pre-existing closure faithfulness unit-test failure

Running `uv run pytest --ignore=tests/test_conformance.py -q
--timeout=120`:

```
FAILED tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories
======================== 1 failed, 50 passed in 7.31s =========================
```

Same falsifying example as in P0.1 baseline
(`raw_theory=(frozenset([]), (), (('a', ()), ('~a', ())))`,
antecedent `('true',)`, consequent `('literal', 'a')`). Unchanged
by this fix, as expected.

## 4. Baseline update

`notes/refactor_baseline.md` now includes a new `## Post-adapter-fix
conformance` section at the end with the new 267/28/0 numbers, the
explanation of the 28 `nemo_negation` failures, the `nests_in_trees`
PASS finding, and the CPtrLoad status. The original "Conformance
suite pass count and time" section (`0 passed, 295 failed, 51.60s`)
is preserved for history per the prompt's instructions.

## 5. Commit hash

`f4f05af23133caa6a88c8beeaae6f1de9a29a1c2`
(short: `f4f05af`)

Commit message: `fix(adapter): delegate suite-native inputs to the
conformance bridge`.

## 6. One-line summary

Public `GunrayEvaluator` now delegates non-native inputs to the
existing `GunrayConformanceEvaluator` bridge instead of raising
TypeError, restoring 267 of 295 conformance cases through the
public adapter entry point.
