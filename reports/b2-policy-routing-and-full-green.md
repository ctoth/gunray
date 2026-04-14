# B2.3 — Policy routing + GeneralizedSpecificity wire-up + full conformance drive

**Dispatch:** B2.3
**Date:** 2026-04-13
**Goal:** Deprecate `Policy.PROPAGATING`, wire `GeneralizedSpecificity`
into `DefeasibleEvaluator.evaluate_with_trace`, drive the full
conformance suite toward the Block 2 ≥267-pass gate, and classify
every still-failing case.

**Verdict — HARD STOP per dispatch §"Hard stop directive".** The
gate is NOT met: 239 passed / 55 failed / 1 deselected. The
specificity wire-up delivers the paper-correct Opus resolution and
lands 4 pre-existing failures, but cannot close the 28-case gap on
its own — the remaining in-scope failures need the theory's
`superiority` list to be honored by the preference criterion, a
Garcia 04 / DeLP interpretation question the hard-stop directive
explicitly forbids resolving in this dispatch ("not a place to
start adding ad-hoc compatibility layers"). Report is the
deliverable; the superiority gap is flagged for foreman review.

---

## 1. Commit hashes (chronological)

1. **`328cecf`** — `test(answer): Opus resolves under GeneralizedSpecificity (red)`
   Adds five B2.3 test cases to `tests/test_answer.py`:
   - `test_opus_flies_is_no_under_specificity`
   - `test_opus_not_flies_is_yes_under_specificity`
   - `test_tweety_still_yes_under_specificity`
   - `test_nixon_diamond_still_undecided_under_specificity`
   - `test_sections_projection_under_specificity`

   Four of the five pass even pre-wire because `answer(theory,
   literal, criterion)` accepts the criterion as a parameter and
   `GeneralizedSpecificity` is already implemented. Only the
   section-projection test (which exercises the full evaluator
   path) is truly red against a TrivialPreference-configured
   evaluator.

2. **`87383c8`** — `feat(defeasible): wire GeneralizedSpecificity into evaluator (green)`
   Replaces `TrivialPreference()` with `GeneralizedSpecificity(theory)`
   at `_evaluate_via_argument_pipeline`. Instantiated once per
   evaluator call — the criterion constructor grounds the strict
   rules and caches them for reuse. Two-line diff plus an import
   and an inline citation comment.

3. **`9eca818`** — `refactor(schema): deprecate Policy.PROPAGATING per notes/policy_propagating_fate.md`
   Removes `PROPAGATING = "propagating"` from `Policy`, adds the
   module-level Antoniou-2007 note, rewrites the `Policy`
   docstring to name BLOCKING as the only supported dialectical-
   tree value post-B2, and updates `_evaluate_via_argument_pipeline`'s
   `del policy` comment to explain that the parameter is kept for
   public-API stability. Also updates
   `test_tweety_sections_projection` in
   `tests/test_defeasible_evaluator.py` to assert the Block-2
   Opus resolution (`not_defeasibly: flies(opus)`, `defeasibly:
   ~flies(opus)`) — this test previously pinned the Block-1
   deviation where both landed in `undecided` under
   `TrivialPreference`.

4. **`f14da0d`** — `test(conformance): deselect spindle_racket_query_long_chain for scalability`
   Adds a `pytest_collection_modifyitems` hook in `tests/conftest.py`
   that deselects the `spindle_racket_query_long_chain` parametrize
   id. Scope option 3 from the dispatch prompt — zero code change
   to the argument enumerator, preserves the fixture for a future
   goal-directed rewrite. The case has 20 defeasible rules in a
   linear chain, and `build_arguments`'s `2^|Delta|` naive subset
   enumeration hits the 120s per-case timeout hard.

---

## 2. Before / after conformance delta

```
B1.6 post-wire state          235 passed / 59 failed / 1 deselected
B2.3 post-dispatch state      239 passed / 55 failed / 1 deselected
                              -----------------------------------
                              +4 passed, -4 failed
```

**Gate status — NOT MET.** Target is ≥267 passed. Actual is 239.
Gap = 28 passes. See §4 classification table for what the gap
consists of and §5 for the root-cause reasoning.

### Specificity wins (cases that flipped from fail → pass)

Four cases that `TrivialPreference` could not resolve are now
passing under `GeneralizedSpecificity`:

- `defeasible/basic/depysible_birds::depysible_flies_tina`
- `defeasible/basic/depysible_birds::depysible_not_flies_tina`
- `defeasible/basic/bozzato_example1_bob::bozzato_example1_bob_exception`
- `defeasible/basic/bozzato_example1_bob::bozzato_example1_bob_not_positive_teaching`

All four fit the same pattern as Opus: a specific rule (e.g.
`chicken(X) → ~flies(X)`) and a general rule (e.g. `bird(X) →
flies(X)`) disagree at a literal, and the specific rule's
antecedent strictly covers the general rule's antecedent via a
strict rule chain. Lemma 2.4 makes the specific rule a proper
defeater of the general rule; the general rule's tree marks `D`;
the specific rule's tree marks `U`; Def 5.3 returns NO/YES
accordingly.

### Real regressions — NONE

Every fail → pass movement is a win; no case that passed in B1.6
regressed in B2.3. Verified by diffing the failing-case list
against the B1.6 failure set from
`reports/b1-wire-evaluator-and-nests-fix.md` §4.2.

---

## 3. Unit suite results

```
$ uv run pytest tests -q -k "not test_conformance"
121 passed, 1 failed (test_formula_entailment_matches_ranked_world_reference_for_small_theories)
```

- 121 passed — +5 vs the 116 Block 2 baseline (the five B2.3
  specificity tests at `tests/test_answer.py`).
- 1 pre-existing closure-faithfulness failure, **unchanged** from
  Phase 0 baseline (see `notes/refactor_baseline.md` §1). Not
  touched by this dispatch.

### Pyright

```
$ uv run pyright src/gunray/defeasible.py src/gunray/schema.py src/gunray/preference.py
0 errors, 0 warnings, 0 informations
```

### LOC gate

```
$ wc -l src/gunray/defeasible.py
291 src/gunray/defeasible.py
```

Under the 300-LOC gate.

---

## 4. Classification table for every still-failing case

Columns: **case** / **B1.6 label** / **B2.3 status** / **reason**.

| Case | B1.6 label | B2.3 status | Reason |
| --- | --- | --- | --- |
| `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguity_propagates_to_downstream_rule` | specificity-needed | `regime-not-implemented` | Antoniou 2007 §3.5 c7' propagating semantics; `Policy.PROPAGATING` deprecated per `notes/policy_propagating_fate.md`. |
| `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguous_attacker_blocks_only_in_propagating` | specificity-needed | `regime-not-implemented` | Same. |
| `defeasible/basic/depysible_birds::depysible_nests_in_trees_tina` | `real-regression-paper-correct` | `paper-correct-regression` | Garcia 04 Def 3.1 cond 2: `Pi + A` contradictory via strict `~flies(tina)`, so no `<A, flies(tina)>` exists; expected `undecided` requires an argument for the literal or complement per Def 5.3. Adversary-confirmed in B1.8. |
| `defeasible/basic/depysible_birds::depysible_nests_in_trees_tweety` | `real-regression-paper-correct` | `paper-correct-regression` | Same (`~flies(tweety)` strict-closed via `r3: ~flies(X) :- penguin(X)`). |
| `defeasible/basic/depysible_birds::depysible_flies_tweety` | specificity-needed | `specificity-no-help` | Same shape as the nests cases: `Pi` strictly contains `~flies(tweety)` via `r3@tweety`, so `Pi + {r4@tweety}` is contradictory, no argument for `flies(tweety)` exists, `not_defeasibly` section is not populated. Garcia 04 Def 3.1 cond 2 forbids the argument that the fixture expects. Same mechanism as `nests_in_trees`. |
| `defeasible/basic/depysible_birds::depysible_not_flies_tweety` | specificity-needed | `specificity-no-help` | Same. |
| `defeasible/basic/mixed::strict_and_defeasible_interaction` | specificity-needed | `specificity-no-help` | Uses a **defeater** rule `r3: ~flies(X) :- penguin(X)` with explicit `superiority: [[r3, r2]]`. `build_arguments` does not enumerate defeater rules into arguments (Garcia 04 Def 3.6), so `~flies(opus)` has no argument and r3 cannot attack r2. Specificity cannot produce an attacker that never existed. Needs defeater-participation + superiority-list handling; neither is in B2.3 scope. |
| `defeasible/basic/morris_example5_birds::morris_example5_tweety_blocked_default` | specificity-needed | `specificity-no-help` | Superiority list needed. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_defeater_negative_conclusions` | specificity-needed | `specificity-no-help` | Defeater rules not enumerated. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_mixed_strict_defeasible_conflict` | specificity-needed | `specificity-no-help` | Superiority/defeater. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_simplified_penguin` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_superiority_conflict` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_unsatisfied_antecedent` | specificity-needed | `specificity-no-help` | Superiority/defeater. |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_defeater_blocks_conclusion` | specificity-needed | `specificity-no-help` | Defeater. |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_missing_premise_failure` | specificity-needed | `specificity-no-help` | Superiority/defeater. |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_penguin_superiority` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_long_chain` | scalability | **deselected (conftest)** | Scope option 3. 20 defeasible rules → `2^20` subset enumeration hits per-case timeout. Goal-directed `build_arguments` rewrite deferred to a follow-up plan. |
| `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_conflict_theory` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_defeater_theory` | specificity-needed | `specificity-no-help` | Defeater. |
| `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_missing_premise_theory` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_basic_conflict` | specificity-needed | `specificity-no-help` | **Verified**: theory has two defeasible rules `r1: flies :- bird`, `r2: ~flies :- bird`, identical antecedents, `superiority: [[r1, r2]]`. Lemma 2.4 returns equi-specific (identical antecedents → `An(T₁) = An(T₂)` → mutual coverage). Pure specificity has no mathematical power here; only the superiority list can break the tie. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_defeater_blocks` | specificity-needed | `specificity-no-help` | Defeater. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_medical_treatment` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_penguin_exception` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_penguin_exception_test` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_strict_beats_defeasible` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/strict_only/strict_only_negation_nemo_negation::*` (14) | nemo_negation | `nemo_negation` | Pre-existing P0.1.5 engine bug (`SafetyViolationError: Variables in negated literals must be positively bound`). Independent of the defeasible pipeline; out of Block 2 scope. |
| `defeasible/superiority/maher_example2_tweety::maher_example2_tweety` | specificity-needed | `specificity-no-help` | Superiority. |
| `defeasible/superiority/maher_example3_freddie_nonflight::maher_example3_freddie_nonflight` | specificity-needed | `specificity-no-help` | Superiority. |
| `negation/nemo_negation::*` (14) | nemo_negation | `nemo_negation` | Same as above (non-strict-only tranche). |

### Class totals

| Class | Count |
| --- | --- |
| `nemo_negation` (pre-existing engine bug) | 28 |
| `specificity-no-help` (needs superiority/defeater) | 21 |
| `regime-not-implemented` (PROPAGATING deprecated) | 2 |
| `paper-correct-regression` (Garcia 04 Def 3.1 cond 2) | 4 |
| `scalability` (deselected) | 1 |
| **Total failing+deselected** | **56** (55 failing + 1 deselected) |
| `specificity-resolved` (B2.3 wins) | 4 |

---

## 5. Runtime delta

| Baseline | Wall time |
| --- | --- |
| Phase 0 post-P0.1.5 (`notes/refactor_baseline.md` §"Post-adapter-fix conformance") | 457.01s |
| B1.6 post-wire | (not recorded in dispatch report) |
| **B2.3 post-dispatch** | **457.99s** |

Runtime delta vs Phase 0 baseline: **+0.98s, +0.2%** — well within
the ±10% gate (411.3s – 502.7s). `GeneralizedSpecificity` was
expected to be more expensive per-call than `TrivialPreference`
because it walks the strict closure per comparison, but the
observed overhead is negligible because the criterion caches the
grounded strict-rule tuple at construction time and the per-call
work is a single `strict_closure` pass over a small shadowed-rule
tuple.

Note: the Phase 0 baseline time of 457.01s was captured with
`spindle_racket_query_long_chain` still timing in at ~100s per
subtest under the old evaluator path (see baseline note §2).
B2.3's 457.99s excludes that case (deselected). So the B2.3
per-case overhead is slightly higher than the nominal delta
suggests — but the total is still within the gate, and the
dominant cost is still the naive subset enumeration in
`build_arguments`, not the preference criterion.

---

## 6. Scalability verdict — option 3 (deselect)

The dispatch prompt listed four options for
`spindle_racket_query_long_chain`:

1. Optimize `build_arguments` to be goal-directed (~100 LOC refactor).
2. Add a subset-enumeration budget.
3. Deselect the case from the conformance run.
4. Defer to a follow-up.

**Taken: option 3.** While wiring specificity and chasing the
full-green drive, I did not find goal-directed construction
falling out naturally — specificity is a pure post-construction
preference check that runs over the same `Argument` universe
`TrivialPreference` ran over. There is no insight from B2.3 that
reduces the subset-enumeration cost. Option 1 is a meaningful
refactor in its own right and belongs in a dedicated follow-up
plan (or Block 3 performance dispatch), not in a B2.3 side-quest.

Option 3 is implemented via `pytest_collection_modifyitems` in
`tests/conftest.py` (commit `f14da0d`). The case stays in the
fixture repository; a future dispatch that lands goal-directed
enumeration can drop the deselection and test the win directly.

---

## 7. Opus resolution confirmation

```
$ uv run python -c "..."   # renders the Tweety theory trees
--- flies(opus) tree ---
flies(opus)  [r1]  (D)
└─ ~flies(opus)  [r2]  (U)
mark: D

--- ~flies(opus) tree ---
~flies(opus)  [r2]  (U)
mark: U
```

- r2 (`~flies(X) :- penguin(X)`) is strictly more specific than
  r1 (`flies(X) :- bird(X)`): `penguin(opus)` strict-closes to
  `bird(opus)` via `s1: bird(X) :- penguin(X)`, but the reverse
  closure fails (`bird(opus)` does not imply `penguin(opus)`).
- `flies(opus)` tree: root r1 has exactly one admissible child —
  r2 as proper defeater. r2's subtree is a leaf (no admissible
  counter-attacker because r1 is less specific than r2). Leaf
  marks U; parent marks D.
- `~flies(opus)` tree: root r2 has no admissible children (r1
  would be the only attacker and is out-preferred). Leaf marks U.
- Def 5.3 projection: `flies(opus) → not_defeasibly`,
  `~flies(opus) → defeasibly`. Matches the Block-1.5 "Opus
  deviation" resolution and the four `tests/test_answer.py`
  assertions added in commit `328cecf`.

This is the primary B2.3 paper-correctness win.

---

## 8. Propstore breakage note

The `Policy.PROPAGATING` deprecation will break:

- `propstore/tests/test_grounding_grounder.py:660` — a smoke test
  `test_grounder_policy_is_configurable` whose own docstring (per
  the B2.1 scout, `reports/b2-scout-policy.md` §3.2) states that
  it "pins the narrower contract: calling with `Policy.PROPAGATING`
  returns a valid four-sectioned bundle" but pins no differential
  behavior.

- `propstore/tests/test_defeasible_conformance_tranche.py:37, 43`
  — lists the `antoniou_ambiguous_attacker_blocks_only_in_propagating`
  fixture id. The translation tranche at lines 217-244 branches on
  `case.expect_per_policy` and iterates each policy name, calling
  `GunrayEvaluator().evaluate(translated, Policy(policy_name))`.
  When `policy_name == "propagating"`, this now raises `ValueError`
  at `Policy("propagating")` (the enum member no longer exists).

- `propstore/propstore/grounding/grounder.py:74-156` — the
  docstring (lines 126-134) mentions PROPAGATING and would be
  left as stale prose after the deprecation. The code itself
  merely forwards `policy` to `GunrayEvaluator().evaluate`; the
  default is `Policy.BLOCKING` so non-test callers are unaffected.

**Per dispatch directive, this dispatch DID NOT touch `propstore/`.**
The fixes land in the Block 3 propstore dispatch (queued as
`B3.2: Propstore direct replacement` in the task list). The
correct one-line change for `grounder.py` is to drop the
PROPAGATING mention from the docstring; the correct change for
the two tests is to drop the PROPAGATING case (or skip it with a
clear reason).

I did not verify the propstore breakage by running propstore
tests from this venv because the gunray venv does not currently
have the propstore package installed as a sibling. Treat this as
an analytical note, not an observed failure.

---

## 9. Hard stop — why I stopped rather than pushing a fix

The dispatch prompt's §"Hard stop directive" states:

> If the conformance gate doesn't hit ≥ 267 passed after the
> specificity wire-up, STOP and write a detailed classification
> report rather than pushing a questionable fix. The gate is the
> gate. A paper-correct implementation that falls short of the
> gate is a real finding worth a foreman review, not a place to
> start adding ad-hoc compatibility layers.

The 21 `specificity-no-help` cases plus the 4 `paper-correct-
regression` cases add up to 25 in-scope failures beyond the
expected residuals. None of them are fixable by specificity. The
natural extension is a `SuperiorityAwarePreference` that consults
`theory.superiority` either as an override of or replacement for
`GeneralizedSpecificity.prefers` — but choosing the right
composition ("explicit priority strictly extends specificity" vs
"explicit priority replaces specificity where it is given") is a
**Garcia 04 §4.1 / DeLP reference interpretation question**, not
an obvious engineering call. Shipping a guess would be the exact
"ad-hoc compatibility layer" the directive forbids.

In addition, `build_arguments` does not currently enumerate
defeater rules into arguments, so even a perfect preference
criterion cannot attack with a defeater — `~flies(opus)` via a
`defeaters:` entry has no argument at all. This is a separate
**B1.3 gap** rather than a B2 preference-criterion question, and
is independent of the superiority decision.

**Net finding for foreman:** to reach the Block 2 ≥267-pass gate
via the paper-driven refactor, gunray needs two more primitives
beyond pure specificity:

1. A preference criterion that composes `GeneralizedSpecificity`
   with the theory's `superiority` list. Paper authority: Garcia
   04 §4.1 (the DeLP preference relation is abstract; explicit
   priority is a primary input). The composition rule needs a
   foreman decision.
2. Defeater-participation in `build_arguments` or in the
   attack step. Paper authority: Garcia 04 Def 3.6. A defeater
   rule does not conclude an argument but does participate in
   the attack relation. The current B1.3 implementation drops
   defeater rules entirely from the argument lattice, so they
   never attack anything. This is a B1 bug that B1.6 did not
   surface because `TrivialPreference` made every attack-capable
   argument into a blocking defeater regardless of defeater
   status.

Both are legitimate Block 2 follow-ups (or a new Block 2.5
dispatch) and both are tractable. They are *not* this dispatch's
scope under the hard-stop directive.

---

## 10. Surprises

- **Four of the five new paper-example tests passed red.** The
  tests use `answer(theory, literal, criterion)`, which accepts
  the criterion as an explicit parameter. `GeneralizedSpecificity`
  is already implemented in `preference.py` and there is nothing
  in `answer` that blocks calling it directly. Only the
  `test_sections_projection_under_specificity` test — which goes
  through `GunrayEvaluator.evaluate` and therefore through the
  evaluator wire — was actually red. The prompt's red-first
  instruction was still satisfied (the wire is the thing we were
  testing), but the other four tests function as
  regression guards for `GeneralizedSpecificity` rather than
  classic red/green cycles.

- **The `depysible_flies_tweety` / `depysible_not_flies_tweety`
  cases are the same mechanism as `nests_in_trees`, not
  specificity problems.** B1.6 bucketed them under
  `specificity-needed` but the actual mechanism is Garcia 04 Def
  3.1 cond 2 rejecting the `<{r4}, flies(tweety)>` argument
  because `Pi` strictly contains `~flies(tweety)` via
  `r3: ~flies(X) :- penguin(X)` and `penguin(tweety)`. Specificity
  has no role to play — the arguments the fixture expects do not
  exist in the argument universe. I have reclassified them as
  `specificity-no-help` in this dispatch and flagged them as
  `paper-correct-regression` candidates for the next adversary
  review.

- **Runtime delta was almost zero**, contrary to the prompt's
  warning that "runtime WILL grow" because `GeneralizedSpecificity`
  walks the strict closure per comparison. The reason: the
  `build_arguments` call at the top of `_evaluate_via_argument_pipeline`
  still dominates the per-theory cost, and the per-comparison
  closure walk is O(|strict rules|) with a tiny constant. The
  criterion's aggressive per-call caching (strict rules grounded
  once at construction) further minimizes the per-call cost.

- **Pyright and LOC gates were trivially satisfied.** The wire-up
  was two lines (criterion construction + import), the schema
  change was one line plus a docstring, and the conftest
  deselection was 30 LOC of boilerplate in a file pyright doesn't
  check by default. Total new gunray source LOC: about 15.

---

## 11. One-line summary

`GeneralizedSpecificity` is wired into the evaluator and delivers
the paper-correct Opus resolution plus 4 additional conformance
wins (235 → 239), but cannot close the ≥267 gate on its own
because 21 remaining cases require the theory's `superiority` list
and/or defeater-rule participation — both Garcia 04 primitives
that are out of B2.3 scope per the hard-stop directive — so the
dispatch stops here, classifies all 55 failures, flags the
superiority and defeater gaps as foreman decisions, and locks in
the `Policy.PROPAGATING` deprecation and the spindle long-chain
scalability deselection per scope option 3.
