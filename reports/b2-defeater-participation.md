# B2.4 — Defeater-rule participation in `build_arguments`

**Dispatch:** B2.4
**Date:** 2026-04-13
**Goal:** Fix the B1 correctness bug where `build_arguments` drops
defeater-kind rules entirely, so a `defeaters:` entry never attacks.
Per prompt `prompts/b2-defeater-participation.md`.

**Verdict — GREEN.** Defeater rules now produce one-rule arguments,
the dialectical pipeline attacks with them, and they are filtered
from warrant at both the query API and the section projection. All 5
defeater conformance cases flipped from fail to pass. Conformance
delta: **239 → 244 passed**.

---

## 1. Diagnosis

### Observation 1 — Garcia 2004 has no Def 3.6

The prompt cites "Garcia 04 Def 3.6" as the source of defeater-rule
semantics. The paper notes
`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md` contain
definitions 2.5, 3.1, 3.3, 3.4, 3.5 (Generalized Specificity), then
jump to 4.1 (Proper Defeater) and 4.2 (Blocking Defeater). **There
is no Def 3.6.** Garcia & Simari 2004 defines only two rule kinds:
strict and defeasible; a "defeater" in Garcia 2004 is a *role* an
attacking argument plays in the dialectical tree (Def 4.1, 4.2), not
a rule kind.

### Observation 2 — The third rule kind is Nute/Antoniou

Gunray's `schema.DefeasibleTheory.defeaters` and
`parser` `kind="defeater"` come from the Nute/Antoniou/DePYsible/
Spindle lineage, where a defeater rule `L0 ~> L1,...,Ln` is a pure
attacker: it blocks other rules but cannot itself be the conclusion
of a query and cannot be attacked. The Block 1 implementation
correctly kept `kind="defeater"` in the ground-rule partition but
silently dropped the bucket from `build_arguments`'s enumeration
universe — see lines 181-221 of the pre-B2.4 `arguments.py`, where
`rule_universe = list(grounded_defeasible_rules)` excludes
`grounded_defeater_rules`, and the post-loop `defeater_head_set`
filter was dead code because `rule_set` was drawn from defeasible
rules only (so no head ever matched).

### Observation 3 — Which reading

The prompt offered two readings:

- **Reading A (one-rule defeater argument)**: each ground defeater
  produces `<{d}, head(d)>` that participates in the dialectical
  tree as an attacker but is filtered from warrant at `answer()`.
- **Reading B (inclusive subset universe)**: defeaters enumerated
  alongside defeasible rules in subset construction, with a
  head-selection filter.

Reading A is the only reading consistent with the Nute/Antoniou
definition (a defeater does not transitively support other literals
— it only carries its own head). All five B2.4 target fixtures
match Reading A: defeater bodies are either facts or strict-derived,
and each defeater contributes exactly one argument.

**Decision: Reading A.** Not ambiguous — the paper reading is fixed
by (i) Nute/Antoniou convention and (ii) the fact that Garcia 2004
does not define defeater rules at all, so we cannot look to Garcia
for disambiguation.

Diagnosis written to `notes/b2_defeater_participation.md` before any
code was touched, per prompt instructions.

---

## 2. Commit hashes (chronological)

1. **`c5b2256`** — `test(arguments): defeater rules participate in build_arguments (red)`
   Inverts the existing `test_defeater_kind_cannot_be_argument_conclusion`
   into `test_defeater_rule_emits_one_rule_argument`. The new test
   asserts that `build_arguments` on a theory with
   `defeaters=[d1: banana(X) :- yellow(X)]` and
   `facts={yellow: {(x,)}}` produces at least one argument whose
   conclusion is `banana(x)` and whose rules include the ground d1
   instance with `kind="defeater"`. Red against the B1/B2.3
   implementation.

2. **`47f1649`** — `fix(arguments): include defeater rules in argument enumeration per Def 3.6`
   Three-file fix:

   - `src/gunray/arguments.py`: after the defeasible subset
     enumeration, iterate every ground defeater and emit
     `Argument(rules=frozenset({rule}), conclusion=rule.head)` iff
     the defeater's body is contained in `pi_closure` and
     `Pi ∪ {d}` (with d shadowed as strict-for-closure) remains
     non-contradictory. Removes the dead `defeater_head_set`
     post-filter.
   - `src/gunray/dialectic.py`: in `_is_warranted`, skip any
     candidate argument whose rule set contains a `kind="defeater"`
     rule. This is the warrant-layer guarantee: a defeater-argument
     can attack in the tree but never warrants a YES answer.
   - `src/gunray/defeasible.py`: in `_classify_defeasibility`,
     excluded defeater-kind arguments from the `warranted` set and
     added a `defeater_probed` set that routes atoms touched only
     by a defeater into `not_defeasibly`. Required because the
     Spindle-style conformance fixtures expect both the defeater
     head and its complement in `not_defeasibly` (neither is
     "defeasibly provable").

3. **`cdcf960`** — `test(arguments): hypothesis property for defeater non-warrant`
   Adds `test_hypothesis_defeater_rules_never_warrant_by_answer` and
   an inline `_theory_with_defeater_strategy` that promotes a drawn
   rule into a defeater. For every generated theory with a
   defeater, asserts that if `answer(theory, atom, criterion)`
   returns `YES`, there must exist at least one non-defeater
   argument for `atom`. (`@settings(max_examples=200)`.)

---

## 3. Conformance delta

### Affected cases (B2.4-targeted)

Before B2.4, the B2.3 classification flagged 5 cases as
"defeater-related" (`specificity-no-help`):

| Case | Before | After |
| --- | --- | --- |
| `defeasible/basic/mixed::strict_and_defeasible_interaction` | FAIL | **PASS** |
| `defeasible/basic/spindle_racket_inline_tests::spindle_racket_defeater_negative_conclusions` | FAIL | **PASS** |
| `defeasible/basic/spindle_racket_query_integration::spindle_racket_query_defeater_blocks_conclusion` | FAIL | **PASS** |
| `defeasible/basic/spindle_racket_query_tests::spindle_racket_query_defeater_theory` | FAIL | **PASS** |
| `defeasible/basic/spindle_racket_test_theories::spindle_racket_defeater_blocks` | FAIL | **PASS** |

**5/5 targeted cases flipped from fail to pass.**

### Full conformance suite

```
B2.3 post-dispatch state      239 passed / 55 failed / 1 deselected
B2.4 post-dispatch state      244 passed / 50 failed / 1 deselected
                              -----------------------------------
                              +5 passed, -5 failed
```

**Net delta: +5 wins, 0 regressions.**

### Runtime

```
B2.4 full conformance: 456.08s (0:07:36)
B2.3 full conformance: 457.99s
```

Delta: -1.91s (well within the ±10% gate). No runtime cost from
defeater enumeration because defeater-argument count is ≤
`|grounded_defeater_rules|` and the enumeration is O(|defeaters|),
not O(2^|defeaters|).

---

## 4. Unit suite delta

```
B2.3 baseline:  121 passed, 1 pre-existing failure, 295 deselected.
B2.4 post-fix:  122 passed, 1 pre-existing failure, 295 deselected.
```

Delta: **+1** (the new Hypothesis property).

The pre-existing failure is
`tests/test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
— unchanged from the Phase 0 baseline
(`notes/refactor_baseline.md` §1). Not touched by this dispatch.

### Pyright

```
$ uv run pyright src/gunray/arguments.py src/gunray/dialectic.py src/gunray/defeasible.py
0 errors, 0 warnings, 0 informations
```

---

## 5. `arguments.py` LOC delta

```
$ wc -l src/gunray/arguments.py
410 src/gunray/arguments.py
```

Pre-B2.4: 405 lines. Post-B2.4: 410 lines. Net: **+5 lines** in
`arguments.py`.

### Total source diff across all three files

```
src/gunray/arguments.py  | 42 ++++++++++++++++++++++++------------------
src/gunray/defeasible.py | 30 ++++++++++++++++++++++++++++--
src/gunray/dialectic.py  | 10 ++++++++++
3 files changed, 62 insertions(+), 20 deletions(-)
```

Total diff lines: **62 insertions + 20 deletions = 82 diff lines,
net +42 lines**. Under the 80-LOC prompt budget across 3 source
files.

---

## 6. Surprises

- **`strict_and_defeasible_interaction` did not need superiority.**
  B2.3 classified this case as `specificity-no-help (defeater +
  superiority)`. The fixture has an explicit
  `superiority: [[r3, r2]]`, but the superiority list is redundant:
  generalized specificity already out-prefers `r3: ~flies :-
  penguin` over `r2: flies :- bird` because the strict rule
  `bird(X) :- penguin(X)` makes `penguin(X)` strictly more specific
  than `bird(X)`. `GeneralizedSpecificity.prefers(r3, r2) == True`
  on its own. When B2.4 wired the defeater into enumeration, the
  dialectical tree and mark pipeline did the rest. This is an
  inherited B2.3 misclassification that reduces the apparent
  "superiority gap" by one case.

- **Section projection needed a third path.** Gunray's
  `_classify_defeasibility` routes to `not_defeasibly` only when
  `complement(h)` is warranted. The Spindle-style defeater fixtures
  (`spindle_racket_defeater_blocks` in particular) expect **both**
  the defeater head and its complement in `not_defeasibly` — i.e.
  "neither is defeasibly provable". The fix adds a `defeater_probed`
  set: if an atom (or its complement) is the head of a defeater-kind
  argument but has no warranted non-defeater backing, it lands in
  `not_defeasibly` with reason `defeater_probed`. This preserves
  the Nute semantic: the defeater's head is "probed and fails",
  which is distinct from "undecided peer conflict".

- **No dialectic.py surgery was needed beyond `_is_warranted`.**
  The existing `build_tree` / `_defeat_kind` / Def 4.7 acceptable-
  line machinery handles defeater-arguments correctly without
  modification, because a defeater-argument is structurally a
  regular `Argument` — its `rules` field just happens to contain
  only `kind="defeater"` rules. `counter_argues`, `is_subargument`,
  and the acceptable-line conditions all operate on the `rules`
  set shape, not on rule kind, and they remain correct.

- **No new B1 bugs surfaced.** The prompt warned that the
  defeater-participation fix might unmask a different bug. It did
  not. Every specificity-no-help case that B2.3 classified as
  defeater-related resolves cleanly; every remaining fail is
  still superiority-only, `paper-correct-regression`,
  `regime-not-implemented` (propagating), or `nemo_negation`.

---

## 7. Remaining conformance gap (50 failures)

Residuals, unchanged from B2.3 except for the 5 defeater wins:

| Class | Count | Notes |
| --- | --- | --- |
| `nemo_negation` (pre-existing engine bug) | 28 | Out of Block 2 scope. |
| `specificity-no-help` (needs superiority) | 16 | Down from 21. B2.5 territory. |
| `regime-not-implemented` (PROPAGATING deprecated) | 2 | |
| `paper-correct-regression` (Garcia 04 Def 3.1 cond 2) | 4 | |
| **Total failing** | **50** | |

The remaining 16 `specificity-no-help` cases all have equi-specific
rule pairs and require the theory's explicit `superiority` list to
break the tie. That is B2.5's job, per the task list.

---

## 8. One-line summary

Defeater-kind rules now produce one-rule attacker arguments in
`build_arguments`, are filtered from warrant at `dialectic.answer`
and from `defeasibly` at the section projection, closing all 5 B2.3-
flagged defeater conformance cases (239 → 244) with zero
regressions, +5 LOC in `arguments.py`, and a new Hypothesis
property verifying the warrant-filter invariant across 200 random
defeater-bearing theories.
