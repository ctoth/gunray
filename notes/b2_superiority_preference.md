# B2.5 — SuperiorityPreference + composition with GeneralizedSpecificity

## GOAL
Add `SuperiorityPreference` (Garcia 04 §4.1 rule priority criterion w/ transitive
closure) and `CompositePreference` (any-wins, superiority delegated before
specificity) to `src/gunray/preference.py`, wire `CompositePreference(
SuperiorityPreference, GeneralizedSpecificity)` into
`DefeasibleEvaluator.evaluate_with_trace`. Target conformance: 244/50 → 260.

## DONE
- 2026-04-13: Read prompt `prompts/b2-superiority-preference.md`.
- Read `reports/b2-policy-routing-and-full-green.md` (B2.3) and
  `reports/b2-defeater-participation.md` (B2.4).
- Read `src/gunray/preference.py` (162 LOC) and
  `src/gunray/defeasible.py` evaluator path.
- Confirmed `schema.DefeasibleTheory.superiority: list[tuple[str, str]]`
  exists with `(stronger_id, weaker_id)` semantics.
- Confirmed `GroundDefeasibleRule.rule_id: str` carries the rule id used
  in the superiority pairs.
- Confirmed `Argument.rules: frozenset[GroundDefeasibleRule]`.

## FILES
- `src/gunray/preference.py` — add `SuperiorityPreference` and
  `CompositePreference` classes. Currently exports `PreferenceCriterion`
  protocol, `TrivialPreference`, `GeneralizedSpecificity`.
- `src/gunray/defeasible.py` — `_evaluate_via_argument_pipeline` line 97:
  swap `criterion = GeneralizedSpecificity(theory)` for the composite.
- `tests/test_superiority.py` — new file (dedicated, per prompt
  preference). 7 paper-example unit tests + 4 Hypothesis properties at
  max_examples=500.
- `reports/b2-superiority-preference.md` — new report.

## DESIGN
- `SuperiorityPreference.__init__(theory)`: stash `theory.superiority`,
  precompute the transitive closure as a `frozenset[tuple[str, str]]`
  on rule_ids. Floyd-Warshall or repeated relational composition.
- `prefers(left, right)`:
  - If either side has empty `rules`, return False (strict-only
    arguments are incomparable under priority — handled by strict-only
    shortcut elsewhere).
  - Reflexivity: `left == right` → False.
  - Dominance check: every rule_id in `left.rules` must dominate every
    rule_id in `right.rules` under the closed relation. If any pair
    fails (no `(lr, rr)` entry in closure), return False.
  - Returns True only if dominance holds for all pairs AND there is at
    least one rule in each side.
- `CompositePreference(*criteria)`: `prefers(a, b) = any(c.prefers(a,b))`.

## CONFORMANCE BASELINE (B2.4)
- 244 passed / 50 failed / 1 deselected. Wall ~456s.
- 16 `specificity-no-help` cases need superiority handling.
- 2 antoniou PROPAGATING (deprecated, permanent fail).
- 4 paper-correct regressions (Garcia 04 Def 3.1 cond 2, permanent fail).
- 1 spindle_racket_long_chain (deselected scalability).
- 28 nemo_negation (engine bug, out of scope).

Realistic ceiling: 244 + 16 = **260**, not 267.

## STUCK
Nothing yet — about to write red tests.

## NEXT
1. Write `tests/test_superiority.py` with 5 unit tests for
   `SuperiorityPreference` + 3 Hypothesis properties (RED).
2. Implement `SuperiorityPreference` (GREEN).
3. Add 2 unit tests + 1 property for `CompositePreference` (RED).
4. Implement `CompositePreference` (GREEN).
5. Wire composite into evaluator.
6. Run full conformance, record delta.
7. Classify residuals, write report.
