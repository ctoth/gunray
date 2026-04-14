# B2.5 — SuperiorityPreference + composition with GeneralizedSpecificity

**Dispatch:** B2.5
**Date:** 2026-04-13
**Goal:** Add `SuperiorityPreference` (Garcia & Simari 2004 §4.1 rule
priority criterion with transitive closure) and `CompositePreference`
(any-wins composition, superiority delegated before specificity) to
`src/gunray/preference.py`, and wire
`CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`
into `DefeasibleEvaluator.evaluate_with_trace`. Per prompt
`prompts/b2-superiority-preference.md`.

**Verdict — GREEN per dispatch contract, but well below the 260
target ceiling because B2.4's "specificity-no-help (superiority)"
classification was a guess based on the YAML `superiority:` field
rather than on the actual failure mechanism.** Six of the sixteen
"superiority-needed" cases flip to pass under
`CompositePreference`. The other ten subdivide into three groups
that all fall outside the rule-priority criterion's authority:
five are Garcia 04 Def 3.1 cond 2 paper-correct regressions of the
exact same shape as the depysible_birds nests/flies cases, three
are a Spindle/DePYsible "implicit failure" classification path
gap with no superiority involvement at all, and two are a
partial-dominance edge case where a multi-rule argument needs a
priority entry over each of its constituent rules — paper-faithful
Garcia 04 §4.1 rejects partial dominance, and the dispatch prompt's
test #5 (`test_superiority_partial_dominance_fails`) explicitly pins
that reading. Conformance: **B2.4 244/50 → B2.5 250/44**.

---

## 1. Commit hashes (chronological)

1. **`0e7f5c0`** — `test(superiority): SuperiorityPreference and CompositePreference (red)`
   Adds `tests/test_superiority.py` with 7 paper-example unit tests +
   4 Hypothesis properties at `max_examples=500`. Also creates
   `notes/b2_superiority_preference.md` for live state. RED via
   `ImportError: cannot import name 'CompositePreference' from
   'gunray.preference'`.

2. **`01f701f`** — `feat(preference): SuperiorityPreference and CompositePreference (green)`
   Implements both classes in `src/gunray/preference.py` (162 →
   292 LOC, +130). `SuperiorityPreference` precomputes the
   transitive closure of `theory.superiority` over rule_ids in the
   constructor (repeated relational composition until fixpoint),
   and `prefers(left, right)` requires every rule in `left.rules`
   to dominate every rule in `right.rules` under the closed
   relation — the strict Garcia 04 §4.1 reading. Reflexivity,
   strict-vs-defeasible, and partial-dominance edge cases all
   return False. `CompositePreference(*criteria)` is a thin
   delegator with `any`-wins semantics. All 11 new tests GREEN.

3. **`d650611`** — `feat(defeasible): compose superiority over specificity in evaluator`
   Replaces the bare `criterion = GeneralizedSpecificity(theory)`
   in `_evaluate_via_argument_pipeline` with
   `criterion = CompositePreference(SuperiorityPreference(theory),
   GeneralizedSpecificity(theory))`. Two-line change plus an
   import block update and a paper-citation comment.

---

## 2. Conformance delta

```
B2.4 post-dispatch state      244 passed / 50 failed / 1 deselected
B2.5 post-dispatch state      250 passed / 44 failed / 1 deselected
                              -----------------------------------
                              +6 passed, -6 failed
```

**Net delta: +6 wins, 0 regressions.** Every B2.4-passing case
still passes. Wall time **462.19s** vs B2.4's 456.08s (+6.11s,
+1.3%). Well within the ±10% gate (411s – 502s).

### Specificity-+-superiority wins (6 cases that flipped)

The six cases that now pass under
`CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`:

1. `defeasible/basic/spindle_racket_inline_tests::spindle_racket_superiority_conflict`
2. `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_penguin_superiority`
3. `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_conflict_theory`
4. `defeasible/basic/spindle_racket_test_theories::spindle_racket_basic_conflict`
5. `defeasible/basic/spindle_racket_test_theories::spindle_racket_medical_treatment`
6. `defeasible/basic/spindle_racket_test_theories::spindle_racket_penguin_exception_test`

All six fit the same pattern: a pair of equi-specific defeasible
rules with a single explicit `superiority` pair `(higher, lower)`
that the rule priority criterion can resolve directly. None of
them require multi-rule dominance.

---

## 3. Unit suite delta

```
B2.4 baseline:  122 passed, 1 pre-existing failure, 295 deselected.
B2.5 post-fix:  133 passed, 1 pre-existing failure, 295 deselected.
```

Delta: **+11** (the 7 paper-example unit tests + 4 Hypothesis
properties added in `tests/test_superiority.py`).

The pre-existing failure is
`tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
— unchanged since the Phase 0 baseline. Not touched by this
dispatch.

### Hypothesis property results

All four `tests/test_superiority.py` properties pass at
`max_examples=500`:

- `test_hypothesis_superiority_is_irreflexive` — verified across 500
  random theories with random acyclic superiority decorations.
- `test_hypothesis_superiority_is_transitive` — closure semantics.
- `test_hypothesis_superiority_is_antisymmetric` — over acyclic
  superiority lists generated via random topological order.
- `test_hypothesis_composite_is_monotonic` — any-wins guarantee.

### Pyright

```
$ uv run pyright src/gunray/preference.py src/gunray/defeasible.py
0 errors, 0 warnings, 0 informations
```

Two pre-existing pyright errors in `src/gunray/closure.py` (lines
80-81, `tuple[object, ...]` not assignable to `tuple[GroundAtom, ...]`)
are unrelated to this dispatch and reproduce on a clean working
tree. Not touched.

The B2.4 harness `arguments.py:97 "_conflicts" is not accessed`
warning does not reproduce under
`uv run pyright src/gunray/arguments.py` — clean. Not touched per
the pyright reproduction rule.

---

## 4. Classification table — every still-failing case

The 44 residual failures break down as follows. Cases marked
`paper-correct-regression` and `propagating-deprecated` have been
flagged in prior dispatch reports as permanent fails; cases marked
`spindle-implicit-failure-gap` and `partial-dominance` are new B2.5
classifications that B2.4 mis-bucketed under `specificity-no-help
(superiority)` based on the YAML `superiority:` field alone.

### Group A — paper-correct regressions (Garcia 04 Def 3.1 cond 2)

5 new cases here, plus the 4 carryovers from B2.4. Total **9 paper-correct
regressions**. The mechanism is uniform: `Pi` already strictly contains
the literal that the defeasible argument would conclude, so by
condition (2) of Def 3.1 (`Pi ∪ A` non-contradictory) the argument
the fixture expects cannot exist.

| Case | Mechanism |
| --- | --- |
| `defeasible/basic/depysible_birds::depysible_nests_in_trees_tina` | Carryover B2.4. `~flies(tina)` strictly entailed via `r3@tweety`. |
| `defeasible/basic/depysible_birds::depysible_nests_in_trees_tweety` | Carryover B2.4. Same. |
| `defeasible/basic/depysible_birds::depysible_flies_tweety` | Carryover B2.4. Same shape. |
| `defeasible/basic/depysible_birds::depysible_not_flies_tweety` | Carryover B2.4. Same. |
| `defeasible/superiority/maher_example2_tweety` | **NEW.** Strict `~fly :- injured` + fact `injured(freddie)` makes Pi strictly contain `~fly(freddie)`, so `<{r1@freddie}, fly(freddie)>` violates cond (2). Fixture expects `fly(freddie) → not_defeasibly`. |
| `defeasible/superiority/maher_example3_freddie_nonflight` | **NEW.** Same theory and mechanism. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_strict_beats_defeasible` | **NEW.** Strict `c :- a,b` + facts `a, b` makes `c` strict; defeasible `~c :- a,b` cannot form. |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_mixed_strict_defeasible_conflict` | **NEW.** Strict `c :- a` + fact `a` yields `c` strict; defeasible `~c :- b` cannot form. |
| `defeasible/basic/morris_example5_birds::morris_example5_tweety_blocked_default` | **NEW.** `~fly(tweety)` is a strict fact; r1: `fly :- bird` cannot form `<{r1@tweety}, fly(tweety)>`. **No superiority pair in this fixture at all** — B2.4 misclassified it. |

### Group B — Spindle/DePYsible implicit-failure classification gap

3 cases. Mechanism: a defined-but-unprovable atom (rule body has a
missing premise, no fact backing) is expected to land in
`not_defeasibly`. Gunray's `_classify_defeasibility` only places
atoms in `not_defeasibly` if `complement(h)` is warranted or a
defeater probes it; an atom with no arguments at all is omitted.
This is **not a Garcia 04 issue and not a superiority issue** — it
is a Spindle/DePYsible classification convention that `gunray` does
not implement.

| Case | Notes |
| --- | --- |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_unsatisfied_antecedent` | r1 needs `p,q`; only `p` is a fact. No argument for `r` and none for `~r`. Expected `r → not_defeasibly`. |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_missing_premise_failure` | Defeasible `ready_review :- tests_pass, code_complete`, only `code_complete` fact. Same mechanism. |
| `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_missing_premise_theory` | Same fixture as above, different file. |

### Group C — partial-dominance / multi-rule argument

2 cases. Mechanism: the argument for `flies` uses a chain of
defeasible rules `{r1: bird :- tweety, r2: flies :- bird}`.
Superiority `(r3, r2)` says `r3` dominates `r2` but **not r1**.
The strict Garcia 04 §4.1 reading ("every rule in A1 has higher
priority than every rule in A2") refuses partial dominance.

| Case | Notes |
| --- | --- |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_simplified_penguin` | `r3-arg.rules = {r3}`, `flies-arg.rules = {r1, r2}`. `(r3, r1)` not in closure → dominance fails. |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_penguin_exception` | Same shape with `(r4, r2)`. |

The dispatch prompt's task #4 unit test #5
(`test_superiority_partial_dominance_fails`) **explicitly pins the
strict reading**, and the hard-stop directive forbids weakening
`SuperiorityPreference` to make a fixture pass. Both my
implementation and my test are paper-faithful. The Spindle/DeLP
implementations that admit these fixtures are doing something
weaker than Garcia 04 §4.1 says — possibly "any rule in left
dominates any rule in right" — but that is not the criterion the
foreman ratified.

### Group D — `regime-not-implemented` (PROPAGATING deprecated)

| Case |
| --- |
| `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguity_propagates_to_downstream_rule` |
| `defeasible/ambiguity/antoniou_basic_ambiguity::antoniou_ambiguous_attacker_blocks_only_in_propagating` |

2 cases. Carryover from B2.3. `Policy.PROPAGATING` was deprecated
per `notes/policy_propagating_fate.md`. Permanent fail in scope.

### Group E — `nemo_negation` (pre-existing engine bug)

| Tranche | Count |
| --- | --- |
| `defeasible/strict_only/strict_only_negation_nemo_negation::*` | 14 |
| `negation/nemo_negation::*` | 14 |

28 cases. P0.1.5 engine bug
(`SafetyViolationError: Variables in negated literals must be
positively bound`). Independent of the defeasible pipeline; out of
Block 2 scope.

### Group F — scalability (deselected)

| Case |
| --- |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_long_chain` |

Deselected via `tests/conftest.py::pytest_collection_modifyitems`
since B2.3.

### Class totals

| Class | Count | Notes |
| --- | --- | --- |
| `nemo_negation` | 28 | Engine bug (pre-existing). |
| `paper-correct-regression` (Garcia 04 Def 3.1 cond 2) | 9 | 4 carryover + 5 new B2.5 reclassifications. |
| `spindle-implicit-failure-gap` | 3 | New B2.5 classification. Not Garcia 04. |
| `partial-dominance` | 2 | New B2.5 classification. Strict Garcia 04 §4.1 rejects. |
| `regime-not-implemented` (PROPAGATING) | 2 | |
| `scalability` (deselected) | 1 | |
| `superiority-resolved` (B2.5 wins) | 6 | |
| **Total failing+deselected** | **45** | 44 failing + 1 deselected. |

---

## 5. Composition interpretation notes

The foreman's decision was: **superiority wins where it fires;
otherwise fall through to specificity**. Encoded as
`CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`
with `any`-wins semantics. The B2.5 conformance run exercises this
composition extensively, and **no fixture revealed the foreman's
ordering decision to be wrong**. Specifically:

- The 6 wins all fire on the superiority criterion alone (the rules
  are equi-specific and only the explicit pair can break the tie).
  Specificity does not contribute.
- The cases where specificity is strictly more specific (Opus,
  bozzato_example1_bob, depysible_birds_tina) all still pass —
  superiority is empty for those theories, so the criterion
  vacuously returns False and specificity takes over.
- No B2.4-passing case regressed under the composition. If the
  foreman had picked the opposite ordering (specificity > superiority)
  the wins would still land for the equi-specific cases — but the
  composite-inversion test
  (`test_composite_superiority_over_specificity` in
  `tests/test_superiority.py`) demonstrates that the ordering
  matters in the contrived case where specificity says `r1 > r2`
  and superiority says `r2 > r1`. No conformance fixture exercises
  that path, so the empirical evidence is consistent with both
  orderings; the foreman's decision is theoretical.

The 2 partial-dominance failures (Group C) are not a composition
problem — they would still fail under either ordering, because
neither criterion can resolve a multi-rule dominance partial check
when the priority list only mentions one of the constituent rules.
Reaching those fixtures would require a different
`SuperiorityPreference` *semantic*, not a different composition
order.

---

## 6. Paper citation count delta

Counted by `grep -ric "Garcia\|Simari\|Antoniou\|Maher\|Morris\|
Loui\|Goldszmidt\|Nute\|Spindle\|Bozzato" src/gunray/`.

```
B2.4:  80 citations
B2.5:  84 citations
delta: +4
```

All four new citations land in `src/gunray/preference.py`:

- 2× "Garcia & Simari 2004 §4.1" on the `SuperiorityPreference`
  class docstring and `prefers` method.
- 1× "Garcia & Simari 2004 §4.1" on the `CompositePreference`
  class docstring (modular composition note).
- 1× "Simari 92 Lemma 2.4 / Garcia 04 Def 3.5" inline comment in
  the evaluator (unchanged from B2.3).

(The actual count delta inside `preference.py` alone is 13 → 17,
which matches.)

---

## 7. `wc -l src/gunray/preference.py` — before / after

```
B2.4 (commit 5078df5 era): 162 src/gunray/preference.py
B2.5 (commit d650611):     292 src/gunray/preference.py
delta:                     +130 lines
```

Two new classes (`SuperiorityPreference` 73 LOC counting docstring,
`CompositePreference` 35 LOC counting docstring) plus an updated
module docstring. No change to `TrivialPreference` or
`GeneralizedSpecificity`.

---

## 8. Surprises

- **B2.4's "specificity-no-help (superiority)" classification was
  wrong for 10 of the 16 cases.** The classification was based on
  the presence of a `superiority:` field in the fixture YAML, not
  on the actual failure mechanism. Five of those cases are
  Garcia 04 Def 3.1 cond 2 paper-correct regressions; three are a
  Spindle implicit-failure classification gap with no superiority
  involvement at all (and one of those — `morris_example5_tweety_
  blocked_default` — has no `superiority:` field in the YAML
  whatsoever); two are the partial-dominance edge case. The real
  B2.5 ceiling under the foreman's "no weakening" directive is
  **250, not 260**. That number is reachable, and it is the number
  this dispatch hit.

- **The partial-dominance edge case is the most interesting
  finding.** Spindle/DeLP implementations apparently apply a
  weaker reading than Garcia 04 §4.1 explicitly states, where
  `r3-arg.prefers(flies-arg)` returns True even though `r3` does
  not dominate every rule in `flies-arg.rules = {r1, r2}`. The
  weaker readings I can imagine are (a) "some rule in left
  dominates the maximum of right", (b) "left.rules is a singleton
  whose rule dominates one rule in right", or (c) "the
  superiority entry is interpreted as an attack relation between
  *arguments* rather than between rules". Each of these admits the
  Spindle fixtures, but each also opens a question of paper
  authority that goes beyond Garcia 04 §4.1. Per the hard-stop
  directive, this dispatch did not weaken the criterion — the
  finding is recorded here and is a foreman call for a possible
  B2.6 dispatch.

- **The Spindle implicit-failure classification gap is purely a
  section-projection issue.** It does not require any change to
  the preference criterion, the argument enumerator, or the
  dialectical tree. A possible fix would be to seed
  `not_defeasibly` with every literal that appears as the head of
  any rule (defeasible or strict) and has no warrant — but that
  would also need to preserve the UNKNOWN gate. This is queued
  for a follow-up dispatch, not this one.

- **Runtime overhead from `SuperiorityPreference` is negligible.**
  The transitive closure is computed once per theory; the per-call
  dominance check is O(|left.rules| × |right.rules|) with a
  frozenset lookup at the leaf. Most theories have ≤3 rules per
  argument, so the per-call cost is dwarfed by the
  `GeneralizedSpecificity` strict closure walk that the composite
  also runs.

---

## 9. One-line summary

`SuperiorityPreference` (Garcia 04 §4.1, transitive closure) and
`CompositePreference` (any-wins, superiority delegated before
specificity) land in `src/gunray/preference.py` and wire into the
evaluator, closing 6 of the 16 B2.4-flagged "specificity-no-help
(superiority)" cases (244 → 250) and revealing that the other 10
were misclassified — 5 are Garcia 04 Def 3.1 cond 2 paper-correct
regressions, 3 are a Spindle/DePYsible implicit-failure
classification gap with no superiority involvement, and 2 are a
partial-dominance edge case the dispatch prompt and hard-stop
directive both refuse to grab by weakening the paper-strict
priority criterion.
