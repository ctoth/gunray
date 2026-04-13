# P0.1.5 adapter TypeError fix — scratch notes

## 2026-04-13 — checkpoint

**GOAL:** Fix `TypeError: Unsupported input type: Program` at
`gunray.adapter.GunrayEvaluator.evaluate` so the conformance suite
runs through the public adapter entry point. Minimal fix, ≤ 20 lines.

**OBSERVED:**
- `src/gunray/adapter.py:32` raises the TypeError. Blame is
  `eed751ac` (original), but the behavior regression came from
  commit `9aae5ab` "Decouple Gunray runtime from conformance
  schema" (2026-04-12).
- Before `9aae5ab`, `adapter.py` imported
  `DefeasibleTheory, Policy, Program` from
  `datalog_conformance.schema` — so the runner's suite types were
  matched directly by `isinstance`.
- After `9aae5ab`, `adapter.py` imports those names from
  `.schema` (gunray-native dataclasses). The conformance runner
  still constructs `datalog_conformance.schema.Program`, which is
  now a different class — `isinstance` returns False, dispatch
  hits the `raise` branch.
- `src/gunray/conformance_adapter.py` already knows how to
  translate suite-native inputs into gunray-native ones via
  `_translate_program` / `_translate_theory` / `_translate_policy`.
  The `9aae5ab` commit introduced that file as the suite bridge.
- `tests/test_conformance.py` constructs a runner via
  `YamlTestRunner.from_import_path(import_path)` where
  `import_path` is whatever `--datalog-evaluator` resolves to.
  Foreman's prompt requires the baseline to use
  `gunray.adapter.GunrayEvaluator` (propstore's public surface).
  The runner passes `datalog_conformance.schema.Program` /
  `.DefeasibleTheory` instances into `evaluator.evaluate(...)`.

**ROOT CAUSE:** The decoupling commit moved all suite-type
translation into `conformance_adapter.py`, leaving
`gunray.adapter.GunrayEvaluator` unable to accept the types the
runner actually passes. The baseline entry point and the bridge
diverged.

**PLANNED FIX (minimal):** In `adapter.py`, when `evaluate` /
`evaluate_with_trace` sees an input that is not gunray-native,
fall through to `GunrayConformanceEvaluator` for translation.
Concretely: construct a `GunrayConformanceEvaluator` lazily and
delegate on the `else` branch instead of raising TypeError.
Same treatment for `satisfies_klm_property`. All changes inside
`adapter.py`. No signature changes. Under 20 lines.

Alternative if cleaner: make `GunrayEvaluator` itself do the
translation inline by importing the suite types lazily. But that
duplicates logic already in `conformance_adapter.py`. Delegation
is smaller.

**NEXT:** Write the fix, run the conformance suite, record
counts, commit, update `notes/refactor_baseline.md`, write the
report.

**STUCK:** None yet.

## 2026-04-13 — post-fix checkpoint

**DONE:**
- Applied minimal fix to `src/gunray/adapter.py`: added
  `_suite_bridge()` helper that lazily instantiates
  `GunrayConformanceEvaluator`, reuses `self` as its `_core`,
  and dispatches non-native inputs through it. Replaced the
  three `raise TypeError` branches with bridge delegation.
- Diff footprint: 15 insertions, 3 deletions across a single
  file (`src/gunray/adapter.py`). Well under the 20-line cap.
- `git diff --stat`: `src/gunray/adapter.py | 18 +++++++++++++++---`

**OBSERVED — conformance run
(`--datalog-evaluator=gunray.adapter.GunrayEvaluator
-q --timeout=120`):**
- `267 passed, 28 failed, 0 xfail/skipped, wall 457.01s`.
  Was `0 passed, 295 failed, 51.60s` pre-fix.
- All 28 failures are `nemo_negation` cases with
  `SafetyViolationError: Variables in negated literals must
  be positively bound` — engine-level negation safety bug,
  unrelated to the adapter boundary and out of scope for this
  dispatch.
- Targeted re-run `-k "nests_in_trees or CPtrLoad"`:
  `5 passed in 227.51s`. The three
  `depysible_nests_in_trees_*` cases and both
  `*souffle_hmmer_CPtrLoad` cases all PASS under the public
  adapter. This contradicts the prompt's expectation that
  `nests_in_trees` should fail; record verbatim in the report.
- CPtrLoad runs slow (~100s each) but does not hit the 120s
  timeout in this environment — it completes, so it now
  registers as a pass. The P0.2 perf bug is visible (~100s
  per case) but no longer hidden behind the TypeError.

**OBSERVED — unit tests
(`uv run pytest --ignore=tests/test_conformance.py -q`):**
- `1 failed, 50 passed, 7.31s`. Same pre-existing
  `test_closure_faithfulness::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  failure from P0.1. No regressions.

**ROOT CAUSE (confirmed):** Commit `9aae5ab` "Decouple Gunray
runtime from conformance schema" changed `adapter.py` from
importing `Program/DefeasibleTheory/Policy` from
`datalog_conformance.schema` to importing them from
`.schema`. The conformance runner still constructs
`datalog_conformance.schema.Program` instances, so the
`isinstance(item, Program)` check became False for suite
inputs and the dispatch fell through to the TypeError branch.
The `GunrayConformanceEvaluator` bridge was introduced by the
same commit to handle suite-type translation, but nothing
glued it back to `GunrayEvaluator` — so the public entry
point propstore uses was orphaned.

**NEXT:** Write `reports/p0-adapter-typeerror-fix.md`, update
`notes/refactor_baseline.md` with a `## Post-adapter-fix
conformance` section, commit everything.

