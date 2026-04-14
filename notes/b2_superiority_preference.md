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
- 2026-04-13: Wrote 11 tests in `tests/test_superiority.py` (RED
  confirmed via ImportError on CompositePreference). Commit `0e7f5c0`.
- 2026-04-13: Implemented `SuperiorityPreference` and
  `CompositePreference` in `src/gunray/preference.py`. All 11 tests
  GREEN. Pyright clean on preference.py.
- Test suite: 7 unit tests + 4 hypothesis properties at max_examples=500
  all pass in 3.54s.

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

## CONFORMANCE RESULT
- B2.4 baseline: 244 passed / 50 failed / 1 deselected
- **B2.5 actual: 250 passed / 44 failed / 1 deselected**
- Delta: **+6 wins, -6 fails**. Wall 462.19s.
- Below the 260 ceiling — 16 superiority cases targeted, only 6 flipped.

## SUPERIORITY WINS (6)
- spindle_racket_inline_tests::spindle_racket_superiority_conflict
- spindle_racket_query_integration::spindle_racket_query_penguin_superiority
- spindle_racket_query_tests::spindle_racket_query_conflict_theory
- spindle_racket_test_theories::spindle_racket_basic_conflict
- spindle_racket_test_theories::spindle_racket_medical_treatment
- spindle_racket_test_theories::spindle_racket_penguin_exception_test

## STILL FAILING SUPERIORITY-LABELED (10) — full classification

### Group A: paper-correct regressions (Garcia 04 Def 3.1 cond 2) — 5 cases
1. **maher_example2_tweety** — Pi strictly contains `~fly(freddie)` via
   strict `~fly :- injured` + fact `injured(freddie)`. So no
   `<{r1@freddie}, fly(freddie)>` argument can exist (Pi+A contradictory).
   Fixture expects `fly(freddie) → not_defeasibly`. SAME MECHANISM as
   depysible_birds nests cases. PERMANENT FAIL.
2. **maher_example3_freddie_nonflight** — same theory as #1, same mechanism.
3. **spindle_racket_strict_beats_defeasible** — strict `r1: c :- a,b`
   makes `c` strict from facts `a,b`. Defeasible `r2: ~c :- a,b` cannot
   form argument (Pi+{r2} contradictory). Expected `~c → not_defeasibly`.
4. **spindle_racket_mixed_strict_defeasible_conflict** — strict `c :- a`
   yields `c` strict; defeasible `~c :- b` cannot form. Same mechanism.
5. **morris_example5_tweety_blocked_default** — `~fly(tweety)` is a
   strict fact. r1: `fly :- bird` cannot form argument for `fly(tweety)`.
   **No superiority in this fixture at all** — B2.4 misclassified it.

### Group B: Spindle implicit-failure classification gap — 3 cases
6. **spindle_racket_unsatisfied_antecedent** — defeasible `r :- p,q`,
   only fact `p`. No argument for `r` and no argument for `~r`. Gunray's
   classification path requires an argument for `h` or `complement(h)`
   for the atom to appear in any section. Spindle/DePYsible apparently
   emits implicit `not_defeasibly` for any defined-but-unprovable atom.
   **No superiority involvement.** Not Garcia 04. Classification gap.
7. **spindle_racket_query_missing_premise_failure** — same mechanism.
8. **spindle_racket_query_missing_premise_theory** — same mechanism.

### Group C: Partial-dominance / multi-rule argument — 2 cases
9. **spindle_racket_simplified_penguin** — argument for `flies` uses
   `{r1: bird :- tweety, r2: flies :- bird}`. Superiority `(r3, r2)`
   means r3 dominates r2 but **not r1**. Garcia 04 §4.1 strict reading
   ("every rule in A1 has higher priority than every rule in A2") →
   `r3-arg` does NOT dominate `flies-arg`. Spindle reading must be
   weaker (perhaps "some rule in left dominates some rule in right").
   The dispatch prompt's test #5 (`test_superiority_partial_dominance_fails`)
   PINS the paper-strict reading, so weakening the criterion to grab
   these 2 cases would (a) violate the hard-stop directive ("Do NOT
   weaken `SuperiorityPreference`") AND (b) break my own test #5.
10. **spindle_racket_penguin_exception** — same partial-dominance pattern.

## SUMMARY COUNT
- Wins: 6 (target was 16, real ceiling 6 because B2.4 misclassified 10
  of the 16 as superiority when actually paper-correct-regression or
  classification-gap).
- Conformance: B2.4 244/50 → B2.5 250/44 → realistic Block 2 ceiling
  is **250 + 0 superiority remaining**, not 260.
- The 260 ceiling assumed all 16 cases were genuine superiority cases.
  They were not.

## VERIFICATION STATE
- tests/test_superiority.py: 11/11 GREEN
- tests/test_specificity.py: 10/10 GREEN
- tests/test_answer.py: 19/19 GREEN
- tests/test_defeasible_evaluator.py: 4/4 GREEN
- Unit suite: 133 passed (was 122 in B2.4, +11). 1 pre-existing failure
  (closure_faithfulness) unchanged from Phase 0.
- Pyright clean on preference.py and defeasible.py.
- Conformance: 250/44 with no regressions (every B2.4-passing case
  still passes).

## NEXT
1. Sanity-check `out/` files for any stale outputs.
2. Write `reports/b2-superiority-preference.md`.
3. Final summary to user with commit hashes and conformance delta.

## OBSERVATION
Several of the "specificity-no-help" cases that B2.4 classified as
"superiority" are actually **paper-correct regressions** of the same
Def 3.1 cond 2 type as the depysible_birds nests/flies_tweety cases.
The B2.4 classification was a guess based on the `superiority:` field
in the YAML — not on the actual mechanism.

## STUCK
Not stuck. Need to investigate the 10 residual cases to classify them
properly. The hard-stop directive forbids weakening anything to make
fixtures pass, so paper-correct-regression-bucket cases remain failing.

## NEXT
1. Read each residual case briefly and classify (mostly skim YAML).
2. Re-run unit suite to confirm no regression at all.
3. Confirm pyright clean.
4. Write `reports/b2-superiority-preference.md` with classification table.
5. Final report to user.
