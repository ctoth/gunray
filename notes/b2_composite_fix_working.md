# B2.6 — CompositePreference fix working notes

**Date**: 2026-04-13

## GOAL
Fix `CompositePreference` to first-criterion-to-fire semantics, add four
deviation log entries, run final Block 2 verifier, emit MERGE/NO-MERGE.

## OBSERVED (so far)
- `src/gunray/preference.py:277-278`: current body is
  `return any(c.prefers(left, right) for c in self._criteria)`. That is
  the any-wins semantics adversary Q9 flagged.
- `src/gunray/preference.py:243-278`: CompositePreference docstring
  explicitly sells "any-wins". Must rewrite.
- `tests/test_superiority.py:257-279`: `test_composite_superiority_over_specificity`
  asserts `composite.prefers(r2_arg, r1_arg) is True` AND
  `composite.prefers(r1_arg, r2_arg) is True` with comment
  "both can be true here — this is exactly the composite-disagreement
  case that motivates the foreman's any-wins semantics". This test
  must be rewritten to first-fire semantics.
- `tests/test_superiority.py:407-427`:
  `test_hypothesis_composite_is_monotonic` — asserts monotonic any-wins.
  Still valid under first-fire (if composite fires, one of P1/P2 fired),
  keep as-is. New asymmetry property must be added.
- `tests/test_superiority.py:281-296`: specificity fallback test — still
  valid under first-fire (superiority silent, specificity fires).
- `notes/refactor_progress.md:783-` has Deviations section. Four new
  entries required.
- Block 2 final state already at 250/44/1 per lines 704-729.

## PLAN
1. Red test first — add new failing test for asymmetry/first-fire, run to confirm RED.
2. Apply fix in preference.py.
3. Rewrite existing `test_composite_superiority_over_specificity`.
4. Add `test_hypothesis_composite_is_asymmetric` Hypothesis property.
5. Run unit suite. Must be 134 passed + 1 pre-existing closure failure.
6. Run conformance suite. Must stay 250/44/1.
7. Add four deviation entries to notes/refactor_progress.md.
8. Run full verifier suite.
9. Write report and emit verdict.

## STUCK
Nothing — progressing cleanly.

## PROGRESS CHECKPOINT (after code commit)

- **Tests written + RED confirmed**: Added `_MockPreference`,
  `test_composite_first_criterion_to_fire_mock`,
  `test_composite_first_criterion_falls_through_when_silent`,
  `test_hypothesis_composite_is_asymmetric`. Rewrote
  `test_composite_superiority_over_specificity` to assert
  `composite.prefers(r1_arg, r2_arg) is False`. Initial run
  produced 2 failures (both the new assertions that exercise
  any-wins misbehaviour).
- **Fix landed**: `src/gunray/preference.py` `CompositePreference.prefers`
  now implements first-criterion-to-fire: iterate criteria, if
  `c.prefers(left, right)` return True, if `c.prefers(right, left)`
  return False, else fall through. Docstring rewritten accordingly.
- **Unit suite GREEN**: 136 passed / 1 failed (`test_closure_faithfulness`
  pre-existing baseline) / 295 deselected. Test count consistent:
  B2.5 baseline 133 + 3 new (2 wiring + 1 asymmetry property) = 136.
- **Conformance GREEN**: 250 passed / 44 failed / 1 deselected.
  Unchanged from B2.5 — adversary's "zero impact" hypothesis
  **verified**.
- **Commit hash (fix)**: `a8569a6` —
  "fix(preference): CompositePreference uses first-criterion-to-fire semantics"

## NEXT
1. Commit the test rewrite separately (per spec: two commits).
2. Add four deviation entries to notes/refactor_progress.md.
3. Run pyright + LOC + paper-citations + skip-marker checks.
4. Write `reports/b2-composite-fix-and-close.md`.
