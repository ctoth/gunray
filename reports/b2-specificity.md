# B2.2 — GeneralizedSpecificity (Simari 92 Lemma 2.4)

**Dispatch:** B2.2
**Date:** 2026-04-13
**Goal:** Land `GeneralizedSpecificity` in `src/gunray/preference.py`
as the paper-legal strict-partial-order preference criterion for
dialectical-tree defeat resolution, backed by paper-example unit
tests and Hypothesis strict-partial-order properties. Do NOT wire
into the evaluator (B2.3). Do NOT touch `Policy.PROPAGATING` (B2.3).

---

## 1. Commit hashes (chronological)

1. **`54ce786`** — `test(specificity): paper-example and Hypothesis
   property tests (red)` — 10 tests added, import fails.
2. **`e8cfb60`** — `feat(preference): GeneralizedSpecificity via
   Simari 92 Lemma 2.4 (green)` — extracted `_ground_theory` helper
   from `build_arguments`, added `GeneralizedSpecificity` class and
   `_antecedents_of` helper. All 10 tests pass first try.
3. **`57eb3b8`** — `test(specificity): inline index strategy to
   satisfy pyright DrawFn protocol` — removed a `_pick` helper that
   pyright rejected because `data.draw` is a bound method rather
   than the `DrawFn` protocol.

---

## 2. Final metrics

| Metric                              | Before | After | Delta |
| ----------------------------------- | ------ | ----- | ----- |
| `src/gunray/preference.py` LOC      | 37     | 162   | +125  |
| `src/gunray/` paper citations       | 32     | 70    | +38   |
| Unit test count (non-conformance)   | 106    | 116   | +10   |
| Pre-existing closure fail           | 1      | 1     | 0     |
| Hypothesis property count (project) | 35     | 39    | +4    |
| Specificity Hypothesis examples     | 0      | 2000  | +2000 |

Full non-conformance suite: **`116 passed, 1 failed`**
(`test_formula_entailment_matches_ranked_world_reference_for_small_theories`
is the pre-existing closure-faithfulness failure — unchanged).

Pyright: **`0 errors, 0 warnings, 0 informations`** on
`src/gunray/preference.py tests/test_specificity.py`.

---

## 3. Paper-example unit tests

Each test is in `tests/test_specificity.py`.

### 3.1 `test_opus_prefers_penguin_over_bird` — Simari 92 §5 p.29

**Proves:** the foundational Opus/Penguin case. With facts
`bird(opus), penguin(opus)`, strict rule `bird(X) :- penguin(X)`,
and defeasible rules `flies(X) :- bird(X)`, `~flies(X) :-
penguin(X)`, Lemma 2.4 yields `r2_arg ≻ r1_arg` because
`penguin(opus)` strict-closes to `bird(opus)` (covering) while
`bird(opus)` does not strict-close to `penguin(opus)` (no reverse
coverage). **Cites:** Simari 92 Def 2.6 / Lemma 2.4 p.14 and Garcia
04 Def 3.5.

### 3.2 `test_tweety_flies_unopposed` — Garcia 04 §3

**Proves:** that `GeneralizedSpecificity(theory)` constructs cleanly
against the full Tweety/Opus combined theory (two constants,
multiple defeasible arguments) and that every argument in
`build_arguments(theory)` is self-equi-specific (irreflexivity
sanity on paper-shaped input, not just Hypothesis-generated theories).
**Cites:** Garcia 04 §3 introductory example.

### 3.3 `test_nixon_diamond_equi_specific` — Simari 92 §5 p.30

**Proves:** neither `r1: ~pacifist(X) :- republican(X)` nor
`r2: pacifist(X) :- quaker(X)` is preferred to the other. Both
antecedents are raw facts with no strict rule linking
`republican` and `quaker`, so each direction's coverage check
fails symmetrically and the criterion returns `False` in both
directions. **Cites:** Simari 92 §5 p.30 (Nixon Diamond).

### 3.4 `test_royal_elephants_off_path` — Simari 92 §5 p.32

**Proves:** the "off-path preemption" case. Theory:
`royal_elephant(clyde)` fact; strict chain
`elephant(X) ← african_elephant(X)`, `african_elephant(X) ←
royal_elephant(X)`; defeasible `~gray(X) :- elephant(X)` (d1) and
`gray(X) :- african_elephant(X)` (d2). `GeneralizedSpecificity`
returns `prefers(d2, d1) is True` and the reverse `False`:
`african_elephant` strict-closes to `elephant` (d2 covers d1)
but not vice versa. **Cites:** Simari 92 §5 p.32-33 Royal African
Elephants.

### 3.5 `test_strict_only_arguments_incomparable` — edge case

**Proves:** two arguments with empty defeasible rule sets (both
derived solely from `Pi`) are equi-specific in both directions.
Both antecedent sets are empty, coverage is vacuously `True` both
ways, and the criterion returns `False`. **Cites:** Simari 92
Def 2.6 (the degenerate `T = ∅` case).

### 3.6 `test_self_comparison_never_prefers` — irreflexivity

**Proves:** `prefers(a, a) is False` for every argument in
`build_arguments(opus_theory)`. Short-circuits on `left == right`
in the implementation; this test hardens that behavior on paper-
example input rather than only Hypothesis-generated theories.
**Cites:** Simari 92 Def 2.6 (strict specificity is a strict order;
irreflexivity is one of the three axioms).

---

## 4. Hypothesis property tests (max_examples=500)

All four properties run against `small_theory_strategy` from
`tests/conftest.py`, which produces theories with up to 2 strict
rules and 3 defeasible rules over 3 predicates and 2 constants.
`theory_with_arguments()` filters theories that produce zero
arguments via `assume()`. Each property uses
`suppress_health_check=[too_slow, data_too_large]` to let the
inner `build_arguments` calls run without Hypothesis bailing.

### 4.1 `test_hypothesis_specificity_is_irreflexive`

**Axiom:** `∀a. ¬(a ≻ a)` — one of the strict partial order axioms
(Simari 92 Def 2.6 / Garcia 04 Def 3.5).
**Stats (final run):**
`500 passing examples, 0 failing examples, 34 invalid examples`
`Stopped because settings.max_examples=500`

### 4.2 `test_hypothesis_specificity_is_antisymmetric`

**Axiom:** `∀a, b. ¬((a ≻ b) ∧ (b ≻ a))` — asymmetry (combined with
irreflexivity gives strict antisymmetry).
**Stats (final run):**
`500 passing examples, 0 failing examples, 26 invalid examples`
`Stopped because settings.max_examples=500`

### 4.3 `test_hypothesis_specificity_is_transitive`

**Axiom:** `∀a, b, c. (a ≻ b) ∧ (b ≻ c) → (a ≻ c)` — transitivity.
**Stats (final run):**
`500 passing examples, 0 failing examples, 34 invalid examples`
`Stopped because settings.max_examples=500`

### 4.4 `test_hypothesis_specificity_is_determined`

**Axiom:** purity — same `(theory, a, b)` inputs produce the same
output across repeated calls, and independent `GeneralizedSpecificity`
instances over the same theory agree.
**Stats (final run):**
`500 passing examples, 0 failing examples, 37 invalid examples`
`Stopped because settings.max_examples=500`

All four properties converged on the first Hypothesis run. No
counterexamples were shrunk. No regressions needed to be captured
as unit tests.

---

## 5. Implementation notes and surprises

### 5.1 `K_N` is strict rules only — not strict rules plus facts

The single most load-bearing decision in this dispatch. The
prompt says "For Phase 2 gunray we treat `K_N` as the strict-rule
set." Dry-running the Opus example with `K_N` including facts
reveals why: if `bird(opus)` and `penguin(opus)` are both seeded
into the strict closure at criterion-construction time, then every
antecedent that matches a fact literal is trivially in the closure
regardless of what rules exist. The Opus case collapses to
equi-specific. The Nixon case collapses to "both sides cover each
other" instead of "neither side covers the other."

The implementation therefore seeds `strict_closure` *only* with the
covering side's antecedents (`An(T₁)`) and lets the strict rules
(plus the shadowed `T_right`) propagate. Facts never enter the
seed set. The Opus test, the Royal Elephants test, and the Nixon
test all pin this: any dispatch that re-introduces facts into
`K_N` will break at least one of them.

### 5.2 `_ground_theory` factored out of `build_arguments`

To avoid duplicating the grounding pipeline between
`build_arguments` and `GeneralizedSpecificity.__init__`, I
extracted a small private helper `_ground_theory(theory) ->
_GroundedTheory` from `arguments.py`. The `_GroundedTheory`
dataclass bundles `fact_atoms`, `grounded_strict_rules`,
`grounded_defeasible_rules`, and `grounded_defeater_rules`.
`build_arguments` now calls it as a single line and unpacks the
result. All 15 pre-existing argument tests still pass — the
refactor is a pure extraction.

### 5.3 Shadowed defeasible rules via `_force_strict_for_closure`

The Lemma 2.4 formula requires the *right*-hand argument's
defeasible rules `T₂` to participate in the closure check (as
if they were strict). `build_arguments` already solved this
problem for Def 3.1 condition (1) by shadowing each defeasible
rule with a `kind="strict"` clone via `_force_strict_for_closure`.
`GeneralizedSpecificity._covers` reuses that exact helper
(imported from `gunray.arguments`). No new closure machinery
was introduced.

### 5.4 Empty-antecedent short-circuit

If either argument has an empty rule set (a strict-only
argument), its antecedent set is empty. The vacuous quantifier
`∀x ∈ ∅. ...` is `True`, so empty antecedent always covers the
other side. The implementation returns `True` from `_covers`
when `covered_antecedents` is empty. This is what drives
`test_strict_only_arguments_incomparable` to the equi-specific
verdict (both sides cover, neither prefers).

### 5.5 `left == right` short-circuit

The dataclass `Argument` is `frozen=True, slots=True`, so
`==` is structural. Short-circuiting at the top of `prefers`
guarantees irreflexivity without depending on the covering
math — which is how Opus's `test_self_comparison_never_prefers`
passes cleanly and how `test_hypothesis_specificity_is_irreflexive`
converges without a single false alarm.

### 5.6 No surprises in Hypothesis

I had one residual worry that the small-theory strategy would
generate a theory with a closure loop (e.g., `p(X) :- q(X)`,
`q(X) :- p(X)`) that inverted transitivity or antisymmetry under
Lemma 2.4. 500 examples per property found zero such cases. This
is consistent with Simari 92's proof that Lemma 2.4 characterizes
a strict partial order over the argument lattice, but I wanted to
see Hypothesis try.

---

## 6. Files touched

- `src/gunray/preference.py` — +125 LOC. `GeneralizedSpecificity`
  class with `__init__`/`prefers`/`_covers`, helper
  `_antecedents_of`, and extensive docstring citing Simari 92 Def
  2.6, Lemma 2.4, and Garcia 04 Def 3.5.
- `src/gunray/arguments.py` — refactor extracting `_ground_theory`
  and `_GroundedTheory` dataclass; `build_arguments` rewritten to
  call the helper. Behavior unchanged.
- `tests/test_specificity.py` — new 329-LOC test module with 6
  paper-example unit tests and 4 Hypothesis properties at
  `max_examples=500`.

Not touched (per hard-stop directive): `defeasible.py`, `adapter.py`,
`schema.py` (Policy enum unchanged), `conformance_adapter.py`,
`dialectic.py`, `evaluator.py`, `disagreement.py`.

---

## 7. Deviations from dispatch

None. The prompt's outline matched the final implementation step
for step: grounded strict-rule cache in `__init__`, antecedent-only
`_covers` using shadowed rules, symmetric check for equi-specific,
short-circuit on self-comparison and empty antecedents.

---

## 8. One-line summary

`GeneralizedSpecificity` lands as 125 new LOC in `preference.py`
with 6 paper-example unit tests (Opus, Tweety, Nixon, Royal
Elephants, strict-only, self-comparison) and 4 Hypothesis
properties at `max_examples=500` all passing, pyright clean, zero
regressions; B2.3 can now wire it into the evaluator.
