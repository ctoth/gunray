# B2 adversary checkpoint

**Date:** 2026-04-13
**Dispatch:** B2 adversary — directional review of everything Block 2 produced.
**Mode:** Read-only. No code edits, no commits. Deliverable is `reports/b2-adversary.md`.

## GOAL
Answer Q1-Q10 from `prompts/b2-adversary.md`, verdict ALIGNED / DRIFT / VIOLATION, with special
attention to Q2 (SuperiorityPreference strict vs max-element), Q3 (composition order),
Q5 (5 new paper-correct regressions), Q6 (Spindle classification gap), Q9 (CompositePreference
is it still a strict partial order).

## DONE (artifacts read)
- `prompts/b2-adversary.md`
- `C:\Users\Q\.claude\plans\ticklish-frolicking-bengio.md`
- `reports/b2-scout-policy.md` (B2.1)
- `reports/b2-specificity.md` (B2.2)
- `reports/b2-policy-routing-and-full-green.md` (B2.3)
- `reports/b2-defeater-participation.md` (B2.4)
- `reports/b2-superiority-preference.md` (B2.5)
- `src/gunray/preference.py` entire
- `src/gunray/arguments.py` entire
- `src/gunray/defeasible.py` entire
- `src/gunray/dialectic.py` entire

## TODO
- `notes/refactor_progress.md` (deviations section) — NOT yet read
- `notes/policy_propagating_fate.md` — NOT yet read
- `papers/Garcia_2004_DefeasibleLogicProgramming/notes.md` (§4.1 rule priority) — NOT yet read
- `papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md` (Def 2.6 / Lemma 2.4) — NOT yet read
- `tests/test_specificity.py`
- `tests/test_superiority.py`
- `tests/test_answer.py`
- `tests/test_build_arguments.py`
- Conformance fixture YAMLs for the 5 new paper-correct regressions:
  - `maher_example2_tweety`
  - `maher_example3_freddie_nonflight`
  - `spindle_racket_strict_beats_defeasible`
  - `spindle_racket_mixed_strict_defeasible_conflict`
  - `morris_example5_tweety_blocked_default`

## PRELIMINARY OBSERVATIONS (from code + reports)

### Q1 — `GeneralizedSpecificity`
- `preference.py:46-150`. K_N is strict rules only (not facts) — `__init__` stores only
  `grounded.grounded_strict_rules`. The report §5.1 explains why facts are excluded.
  This matches Lemma 2.4's "K_N = strict rule set" convention.
- `_covers` uses `strict_closure(covering_antecedents, self._strict_rules + shadowed_T_covered)`,
  with `T_covered` shadowed via `_force_strict_for_closure`. This is the antecedent-only
  Lemma 2.4 reduction under the closure operator `|~`.
- Strict partial order: `prefers` requires `left covers right` AND `not right covers left`.
  That is strict dominance of left over right. Looks correct.
- `left == right` short-circuit ensures irreflexivity independently of the covering math.
- One minor concern: empty-antecedent vacuous-coverage short-circuit returns True, so
  an empty-rules argument vacuously covers anything. That is consistent with Simari 92's
  degenerate case but might create odd equi-specific relations with strict-only args.
  Strict-only args however are `Argument(rules=frozenset(), ...)`, so the `left == right`
  path never mattered — but `_covers` returning True for empty covered_antecedents means
  the strict-only side ALWAYS covers, so `prefers(strict_only, anything_else) == True`
  unless the other side also covers. VERIFY IN TESTS.

### Q2 — `SuperiorityPreference` strict-vs-max
- `preference.py:153-240`. Strict dominance: for every `(lr, rr) in left.rules x right.rules`,
  `(lr.rule_id, rr.rule_id)` must be in the transitive closure. Single missing pair = False.
- B2.5 report §4 Group C admits 2 cases fail because a multi-rule argument's constituent
  rules don't all get a dominance pair. That is exactly the "strict vs max-element" call.
- **Open directional question**: the paper reading. I have not yet read Garcia 04 §4.1
  in the paper notes. Must do so before deciding. The dispatch test
  `test_superiority_partial_dominance_fails` pins the strict reading — but that is
  implementation choice, not paper authority.
- Suspicion: Garcia 04 probably defines this over the argument pair only, or is silent,
  and Spindle/DeLP use a weaker (max-element / any-dominates-any) reading. That is
  where the verdict hinges.

### Q3 — Composition order
- `CompositePreference(SuperiorityPreference(theory), GeneralizedSpecificity(theory))`
  wired in `defeasible.py:106-109`. Any-wins semantics.
- Foreman directive: superiority first, specificity fallback.
- B2.5 report §5 notes "no fixture revealed the foreman's ordering decision to be wrong"
  — the wins are on equi-specific rule pairs where specificity contributes nothing, so
  the order is empirically irrelevant.
- Open: paper authority. Need to read Garcia 04 §3.2 / §4.1 for composition guidance.
  Suspicion: paper is silent, so any composition is acceptable, but the strict vs
  specificity reading matters for the theoretical semantics of "user override".

### Q4 — Defeater participation (B2.4)
- B2.4 report §1 Observation 1 admits "Garcia 2004 has no Def 3.6" — the prompt cited
  a Def that does not exist in the paper. Defeater rules are Nute/Antoniou.
- Decision: Reading A (one-rule defeater arguments). Implementation in
  `arguments.py:184-192` emits `Argument(rules={d}, conclusion=d.head)` per grounded defeater
  whose body is in `pi_closure` and whose `Pi ∪ {d}` is non-contradictory.
- `_is_warranted` at `dialectic.py:488-496` skips defeater-argument candidates.
- `_classify_defeasibility` at `defeasible.py:125-180` uses a `defeater_probed` set to route
  atoms into `not_defeasibly` when the atom (or its complement) is the head of a
  defeater-kind argument. This is outside strict Def 5.3.
- Red flag #2 (the `defeater_probed → not_defeasibly` shim) is acknowledged in the B2.4
  report as "slightly outside strict Def 5.3" but defensible because Spindle fixtures
  expect it. Defensibility = how to call this.

### Q5 — 5 new paper-correct regressions
- Pattern per B2.5 report §4 Group A: `Pi` already strictly contains the literal the
  defeasible argument would conclude → Def 3.1 cond 2 rejects the argument.
- I have NOT independently verified any of the 5 fixtures. Must read their YAML.

### Q6 — Spindle implicit-failure classification gap
- 3 cases: `spindle_racket_unsatisfied_antecedent`, `spindle_racket_query_missing_premise_failure`,
  `spindle_racket_query_missing_premise_theory`. Expected result: unprovable-body literal
  lands in `not_defeasibly`.
- Current `_classify_defeasibility` only populates `not_defeasibly` if complement is warranted
  OR `defeater_probed`. A defined-but-unprovable atom with no defeater touch is OMITTED.
- Spindle/DePYsible expects it in `not_defeasibly`. Gunray doesn't implement that.
- Is this paper-correct? Garcia 04 Def 5.3's four answers are YES/NO/UNDECIDED/UNKNOWN.
  UNKNOWN = predicate not in language. UNDECIDED requires at least one argument to exist.
  Defined-but-unprovable = predicate IS in language, NO argument exists for either side.
  Def 5.3 literally does not cover this case. Answer: paper-gap, defensible classification.
  But `not_defeasibly` vs omission is a projection choice.

### Q7 — Implementation smuggling
- `defeater_probed` in `_classify_defeasibility` — B2.4 acknowledged shim. NOT keyed to a
  fixture file name; it is generic.
- `f14da0d`: deselected `spindle_racket_query_long_chain` for scalability. Fixture still
  present; deselected via `pytest_collection_modifyitems`. Documented in B2.3 report §6.
- Haven't seen any hard-keyed branches to fixture names. Need to scan.

### Q8 — Argument pair shape
- `arguments.py:42-55`. `Argument` is still `@dataclass(frozen=True, slots=True)` with
  `rules: frozenset[GroundDefeasibleRule]` and `conclusion: GroundAtom`. Two fields.
  No new field. CLEAN.

### Q9 — CompositePreference strict partial order?
- `CompositePreference.prefers = any(c.prefers(left, right) for c in self._criteria)`.
- Irreflexivity: if each child is irreflexive, `any` of False across all children is
  False. OK.
- Antisymmetry: `any(P1(a,b), P2(a,b))` and `any(P1(b,a), P2(b,a))` can both be True
  simultaneously if P1(a,b) and P2(b,a) — antisymmetry CAN FAIL. Counterexample:
  SuperiorityPreference says `(a, b)` is in closure but `(b, a)` is not.
  GeneralizedSpecificity says `b covers a` strictly. Then P1(a,b)=True, P2(b,a)=True,
  composite prefers a over b AND b over a. Mutual preference — asymmetry violated.
- Transitivity: can also fail. Given P1(a,b)=True, P2(b,c)=True. Composite prefers
  a over b and b over c. But neither P1 nor P2 necessarily has (a,c). Both children
  can miss the transitive pair because one child sees one half and the other sees
  the other half.
- **This is the biggest directional red flag.** The Hypothesis property
  `test_hypothesis_composite_is_monotonic` is about monotonicity ("if composite prefers
  then some child fires"), NOT about strict partial order axioms. B2.5 did not verify
  the composite is a strict partial order.
- Whether this matters depends on whether `build_tree` / `mark` actually require the
  criterion to be a strict partial order. Need to check.

### Q10 — Deviations audit
- Haven't read `notes/refactor_progress.md#deviations` yet.

## STUCK
Not stuck. Need more reads.

## NEXT
1. Read paper notes: Garcia 04 §4.1 for Q2 strict vs max; Simari 92 Lemma 2.4 for Q1.
2. Read `notes/refactor_progress.md` deviations and `notes/policy_propagating_fate.md`.
3. Read the 5 paper-correct regression fixtures for Q5 independent verification.
4. Read tests for Q1 Q2 Q9 property axioms.
5. Write `reports/b2-adversary.md` with verdict.

## INITIAL VERDICT LEAN
Probably **DRIFT** — not a full VIOLATION, but:
- Q9 CompositePreference is almost certainly NOT a strict partial order. Missing property
  coverage is a drift requiring either (a) fix composition to be strict, or (b) document
  that the dialectical tree only needs prefers to be a relation, not a strict PO.
- Q2 strict vs max is the second hinge. Paper reading decides.
- The 5 new paper-correct regressions look mechanically plausible but I haven't checked
  even one fixture by hand.

---

## POST-SECOND-SWEEP FINDINGS (2026-04-13, after reading papers and fixtures)

### Q1 VERIFIED
- Lemma 2.4 per Simari 92 notes line 111: `⟨T₁, h₁⟩ ⪰ ⟨T₂, h₂⟩ iff
  ∀x ∈ An(T₂), K_N ∪ An(T₁) ∪ T₂ |~ x`.
- `preference.py:121-150` `_covers` implements this via
  `strict_closure(covering_antecedents, self._strict_rules + shadowed_T_covered)`,
  where `T_covered` is `right.rules` shadowed strict via `_force_strict_for_closure`.
  Matches the lemma verbatim. K_N = strict rules only (no facts).
- `prefers` = `_covers(left, right) AND NOT _covers(right, left)`. That is the strict
  ≻ direction. `left == right` short-circuit for irreflexivity.
- **VERDICT Q1: ALIGNED.** Lemma 2.4 implemented correctly.

### Q2 VERIFIED — STRICT DOMINANCE IS THE PAPER READING
- Garcia 04 notes line 170 verbatim (p.15): "**Rule priority criterion: explicitly
  ordered defeasible rules, argument preferred if all its rules have higher priority**".
- That is strict-all-rules dominance, matching `SuperiorityPreference` at
  `preference.py:236-240`: `for lr in left.rules: for rr in right.rules:
  if (lr.rule_id, rr.rule_id) not in closure: return False`.
- B2.5 is paper-correct. Spindle/DeLP implementations use a weaker reading.
- **VERDICT Q2: ALIGNED.** The paper supports strict dominance. The 2 partial-dominance
  Spindle fixtures in Group C are Spindle deviating from the paper, not gunray.

### Q3 — composition order
- Paper is silent. Garcia 04 §3.2/§4.1 says comparison criteria are modular and
  replaceable — no composition rule given. Gunray picks "superiority first, specificity
  fallback" which is a reasonable engineering choice.
- B2.5 report §5 notes that no fixture exercises the ordering in a differential way.
- **VERDICT Q3: ALIGNED** (paper is silent, implementation is one defensible choice).
  Minor drift: an all-agree composition or a priority-replaces-specificity composition
  would also be defensible. But neither is paper-mandated.

### Q4 VERIFIED
- B2.4 report §1 Obs 1: Garcia 2004 has no Def 3.6. Confirmed by paper notes — there is
  no Def 3.6 between Def 3.5 (specificity) and Def 4.1 (proper defeater). The prompt
  citation was fabricated by an upstream author.
- Defeater rules are Nute/Antoniou. Garcia 04 has only strict + defeasible rule kinds.
  Reading A ("one-rule defeater argument, filtered from warrant") is consistent with
  the Nute reading.
- Implementation: `arguments.py:184-192` emits one-rule defeater arguments;
  `dialectic.py:488-496` `_is_warranted` filters them; `defeasible.py:125-140`
  `_classify_defeasibility` routes `defeater_probed` atoms into `not_defeasibly`.
- **Red flag confirmed**: the `defeater_probed → not_defeasibly` shim at
  `defeasible.py:137-180` IS outside strict Def 5.3. Def 5.3 doesn't say anything
  about what to do with defeater-probed atoms — the paper doesn't define defeater
  rules at all. The shim is defensible as a Nute-semantics projection, but it's a
  Spindle-compat choice, not a paper-mandated one. The B2.4 report acknowledged this.
- **VERDICT Q4: DRIFT (minor, defensible).** The shim is a documented compatibility
  layer, not a smuggled semantic change.

### Q5 VERIFIED INDEPENDENTLY (5 fixtures read)
- `maher_example2_tweety.yaml`: Pi closure contains `~fly(freddie)` via strict
  `r4: ~fly :- injured` + fact `injured(freddie)`. So `⟨{r1@freddie}, fly(freddie)⟩`
  gets `Pi ∪ {r1@freddie}` contradictory → Def 3.1 cond 2 rejects. `fly(freddie)`
  never becomes a conclusion. Fixture expects `fly: [[freddie], [tweety]] → not_defeasibly`.
  The `fly(freddie)` atom is never iterated. CONFIRMED Group A.
- `maher_example3_freddie_nonflight.yaml`: same theory, same mechanism. CONFIRMED.
- `spindle_racket_strict_beats_defeasible`: Pi contains `c` via strict `r1: c :- a, b`
  + facts `a, b`. `⟨{r2}, ~c⟩` rejected by cond 2. `~c` never a conclusion. Fixture
  expects `~c → not_defeasibly`. CONFIRMED Group A.
- `spindle_racket_mixed_strict_defeasible_conflict`: Pi contains `c` via strict
  `r1: c :- a` + fact `a`. `⟨{r2}, ~c⟩` rejected. Fixture expects `~c → not_defeasibly`.
  Note the fixture declares `conflicts: [[c, ~c]]` which is redundant. CONFIRMED Group A.
- `morris_example5_tweety_blocked_default`: Fact `~fly(tweety)`. Pi contains `~fly(tweety)`.
  `⟨{r1@tweety}, fly(tweety)⟩` rejected by cond 2. Fixture has `superiority: []`
  (NO superiority pair at all, contra B2.4's classification based on YAML field).
  CONFIRMED Group A.
- **VERDICT Q5: ALIGNED.** All 5 new paper-correct regressions are correctly classified.
  The mechanism is uniform: Pi strictly entails the complementary literal, so Def 3.1
  cond 2 rejects the argument for the fixture-expected atom, so the atom never becomes
  a conclusion, so `_classify_defeasibility`'s `for atom in conclusions` loop doesn't
  iterate it, so it's omitted from every section. The fixtures encode Spindle/DePYsible's
  "include unprovable heads in not_defeasibly" convention that is NOT a Garcia 04
  semantics. Paper wins per the foreman directive.

### Q6 — Spindle implicit-failure gap (3 cases)
- `spindle_racket_unsatisfied_antecedent`: fact p, defeasible `r1: r :- p, q`. No `q`
  fact. No argument for `r` (body q missing). No argument for `~r`. Fixture expects
  `r → not_defeasibly`.
- This is a DIFFERENT mechanism from Group A. In Group A, Pi contains the complement
  strictly, so the complement is warranted as `⟨∅, ~literal⟩`, which makes the
  literal "no" — but gunray doesn't iterate the literal because no conclusion set
  contains it. In Group B, NEITHER side has an argument; defined-but-unprovable atom.
- Def 5.3: YES/NO require warrant. UNDECIDED requires at least one argument to exist
  (for literal or complement). UNKNOWN is for predicates not in the language.
- `r` IS in the language (it is the head of r1). `r` has no argument. `~r` has no
  argument. None of Def 5.3's four answers cleanly applies. The paper does not cover
  this case.
- Spindle/DePYsible chooses `not_defeasibly` as the projection. Gunray could legitimately
  choose omission (paper-strict) or `not_defeasibly` (Spindle-compat). Current gunray
  omits.
- **VERDICT Q6: DEFENSIBLE PAPER GAP.** The three cases sit in a genuine Def 5.3
  ambiguity. Gunray's choice to omit is paper-strict. B2.5's classification is
  defensible.

### Q7 — Smuggling audit
- `defeater_probed` shim — known, documented, Spindle-compat. Defensible.
- `pytest_collection_modifyitems` deselection of `spindle_racket_query_long_chain` —
  documented scalability workaround. Defensible.
- No fixture-name-keyed branches observed. No ad-hoc compatibility paths beyond
  `defeater_probed`. `_classify_defeasibility` has no other suspicious branches.
- **VERDICT Q7: ALIGNED.** Only one known shim, documented.

### Q8 — Argument shape
- `arguments.py:42-55`. `Argument(rules, conclusion)`. Two fields. Still a pair.
- **VERDICT Q8: ALIGNED.**

### Q9 — CompositePreference strict partial order — THE BIG FINDING
- `CompositePreference.prefers = any(c.prefers(left, right) for c in self._criteria)`.
- **Test file `tests/test_superiority.py:273-278` directly confirms the break**:
  ```
  # Composite: superiority fires first and wins.
  assert composite.prefers(r2_arg, r1_arg) is True
  assert composite.prefers(r1_arg, r2_arg) is True
  # NB: both can be true here — this is exactly the composite-disagreement
  # case that motivates the foreman's any-wins semantics. The dialectical
  # tree resolves the apparent symmetry through the attack relation.
  ```
- **This is an explicit acknowledgment that the composite is NOT asymmetric.** With
  P1 preferring a>b and P2 preferring b>a, `composite.prefers(a,b)==True AND
  composite.prefers(b,a)==True`. That is a direct violation of asymmetry, which is
  part of the strict-partial-order axioms that `GeneralizedSpecificity` and
  `SuperiorityPreference` individually satisfy.
- Transitivity: also almost certainly violated in general. Consider P1: a>b only,
  P2: b>c only. Composite says a>b and b>c. Neither P1 nor P2 says a>c. So composite
  does NOT say a>c. Transitivity fails.
- **Neither the adversary's Hypothesis property suite nor the B2.5 property
  `test_hypothesis_composite_is_monotonic` checks composite partial-order axioms.**
  That property is "if composite fires, some child fires" — trivially true by
  definition of `any`. It is NOT an axiom check.
- The consequences depend on whether `build_tree`/`mark` actually assume a strict
  partial order. Looking at `dialectic.py:126-144` (`proper_defeater`) and
  `dialectic.py:147-165` (`blocking_defeater`): they ask `criterion.prefers(attacker, sub)`
  and `criterion.prefers(sub, attacker)` and classify attack kind accordingly. They
  don't rely on transitivity globally — each defeat is a local decision.
- But `_defeat_kind` at `dialectic.py:211-237` has a subtle issue: if `criterion.prefers`
  is not asymmetric, a candidate could be simultaneously proper AND out-preferred by
  the sub-argument. Reading the code: `proper_hit = criterion.prefers(attacker, sub)`,
  `blocking_hit = not criterion.prefers(sub, attacker)`. If both `prefers(a,sub)` and
  `prefers(sub,a)` are True (the composite case tested explicitly), `proper_hit = True`
  and `blocking_hit = False`. So the attack counts as proper, and the sub is not
  simultaneously treated as its own proper defeater back. This is asymmetry-broken
  but operationally well-defined because `_defeat_kind` sees only one direction per
  call. The code is robust to the non-strict relation, but the underlying theoretical
  guarantees of Garcia 04 §4-5 depend on the preference being a strict PO.
- **VERDICT Q9: DRIFT — documented in tests but not called out as a paper-level issue.**
  The composite is NOT a strict partial order; the test comment explicitly says "both
  can be true". The dialectical tree happens to resolve this via the attack relation
  rather than the preference math, so operationally it works. But claiming the composite
  is a "strict partial order preference criterion" would be false — and Garcia 04's
  theorems about the dialectical tree's marking behavior are stated over strict partial
  orders. This is a real paper-gap. Either:
  - (a) composition should prefer to be strict (e.g. `all`-wins or
    `first-criterion-to-fire` with ordering-sensitivity), or
  - (b) the documentation should say explicitly that the composite is a NON-strict
    relation and the dialectical tree only requires asymmetry in the local-defeat
    check, not globally.
- Current status: `preference.py:268-272` claims "irreflexive iff every child is
  irreflexive, and is monotonic in the sense that ..." — it correctly does NOT claim
  asymmetry or transitivity. So the docstring is accurate. But the foreman and plan
  never surfaced this as a known limitation, and the B2.5 report's §5 "composition
  interpretation notes" frames it as "no fixture reveals ordering is wrong", not as
  "the composite is not an order at all".

### Q10 — Deviations audit
- `notes/refactor_progress.md:757-773`: P0 deviations (P0.1.5, P0.1.6, `nests_in_trees`
  victory lap no longer motivated) — all justified, all documented with Q approval.
- `notes/refactor_progress.md:783-965`: B1 deviations (B1.5 opus answer test assertions,
  B1.6 nests_in_trees paper-rejection). Both documented with paper citations, both
  cite Def 3.1 cond 2 or Def 5.3 verbatim. Both are hard-stop-style
  "I disagree with the prompt; paper wins" entries. Defensible.
- `notes/policy_propagating_fate.md`: clean decision doc for PROPAGATING deprecation.
  Paper authority (Antoniou 2007 is out-of-scope per refactor source-of-truth set),
  consumer analysis, reversibility note. Clean.
- I have NOT found an explicit B2 entry in the deviations section for any of:
  - The `defeater_probed` shim (B2.4).
  - The composite non-strict-partial-order situation (B2.5).
  - The paper-correct regression ceiling of 250 (B2.5).
- **VERDICT Q10: DRIFT.** The B2.5 composite-not-a-partial-order issue and the
  defeater_probed shim should be recorded as deviations. The 250 ceiling should also
  be recorded. Not architectural smuggling, but insufficient documentation.

## REVISED VERDICT LEAN
**DRIFT** — not a VIOLATION, but several items need foreman attention:
1. Q9: Document the composite-is-not-a-strict-partial-order situation explicitly
   (either fix or document the consequence in preference.py and in the deviations log).
2. Q10: Record B2.4's defeater_probed shim and the 250 ceiling as deviations.
3. Q4: The defeater_probed shim is a known compat layer — minor drift, defensible.
4. Q6: The Spindle implicit-failure classification gap is a real paper-ambiguity — the
   three cases are legitimately not covered by Def 5.3 cleanly; gunray's "omit" is the
   paper-strict choice.

Not VIOLATION because:
- Q1, Q2, Q5, Q7, Q8 are all ALIGNED with the papers.
- The drifts are minor and well-bounded.
- The 250 ceiling is genuinely the paper-correctness maximum; the 17 remaining cases
  all require either non-paper semantics (Spindle implicit-failure, partial dominance,
  propagating regime) or a pre-existing engine bug (nemo_negation).

## NEXT
Write reports/b2-adversary.md with verdict, per-question findings, gate reality check,
disagreements with coder reports, and recommendations.
