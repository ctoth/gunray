# B2 — Adversary review

**Dispatch:** B2 adversary (directional review of B2.1–B2.5)
**Date:** 2026-04-13
**Mode:** Read-only. No source/test edits. No commits.
**Scope:** Plan, five B2 coder/scout reports, live source
(`preference.py`, `arguments.py`, `defeasible.py`, `dialectic.py`),
live tests (`test_specificity.py`, `test_superiority.py`),
deviations log, policy decision note, and paper notes for Garcia 04
and Simari 92. Conformance fixtures for the five new paper-correct
regressions read verbatim.

---

## Verdict — **DRIFT**

Block 2 is fundamentally paper-aligned on the load-bearing questions
— Lemma 2.4, the Garcia 04 §4.1 rule-priority criterion, Def 3.1
cond 2's rejection of arguments contradicted by Π, and the four-
valued Def 5.3 answer. The 250 ceiling is a real paper-correctness
ceiling under the foreman's "no weakening" stance. However, three
real drifts need foreman attention before Block 3 starts, and one
additional documentation gap.

**None of the drifts is a principle violation, and none blocks Block 3
on its own.** The coder reports are accurate on every item I
independently checked. The drifts are:

1. **Q9 / CompositePreference is not a strict partial order.** The
   any-wins composition can exhibit both asymmetry and transitivity
   failures. `tests/test_superiority.py:273-278` already acknowledges
   the asymmetry failure directly ("both can be true here"). Garcia 04
   §4 / §5's dialectical-tree theorems are stated over strict-partial-
   order preferences. The composite does not meet that precondition.
   Gunray's operational pipeline happens to remain well-defined
   because `_defeat_kind` at `dialectic.py:211-237` resolves each
   defeat locally without needing global transitivity, but the drift
   is real at the theoretical level and the docstring at
   `preference.py:266-272` correctly avoids claiming it is an order.
   This deserves an explicit deviation entry.
2. **Q4 / `defeater_probed → not_defeasibly` shim.** Outside strict
   Def 5.3, a Spindle/Nute compat layer. Documented in the B2.4
   report, but not recorded in `notes/refactor_progress.md#deviations`.
   Defensible as a projection choice for a case the paper doesn't
   cover, but ought to be surfaced.
3. **Q10 / Missing Block 2 entries in the deviations log.** The
   defeater_probed shim, the 250 paper-correctness ceiling, and the
   CompositePreference non-strict-partial-order situation are all
   coder-report-level findings that never made it into
   `notes/refactor_progress.md#deviations`. The existing log stops
   at B1.6.

Additional non-drift observations worth recording in the report:

- **Q6 / Spindle implicit-failure classification gap** is a genuine
  Def 5.3 ambiguity, not a gunray drift. The three cases legitimately
  fall between UNKNOWN (predicate not in language) and UNDECIDED
  (some argument exists). Gunray's "omit" is the paper-strict
  choice and is defensible.
- **Q5 / the five new paper-correct regressions are all verified
  independently.** The B2.5 classification is correct; one fixture
  (`morris_example5_tweety_blocked_default`) has `superiority: []`
  so B2.4's "specificity-no-help (superiority)" bucket was wrong —
  B2.5 fixed the bucket but the real drift originated in B2.4.

---

## Per-question answers Q1–Q10

### Q1 — Is `GeneralizedSpecificity` Lemma 2.4?

**Verdict: ALIGNED.**

Simari 92 notes line 111 states Lemma 2.4 verbatim: `⟨T₁, h₁⟩ ⪰
⟨T₂, h₂⟩ iff ∀x ∈ An(T₂), K_N ∪ An(T₁) ∪ T₂ |~ x` (p.14).

`src/gunray/preference.py:46-150` implements this faithfully:

- `__init__` at lines 83-91 stores `grounded.grounded_strict_rules`
  only — not facts. The class docstring at lines 68-75 explicitly
  argues why facts are excluded ("if `K_N` included grounded facts
  then every antecedent literal corresponding to a fact would be
  trivially derivable and specificity would collapse"). This is
  `K_N` in the Simari 92 sense: strict rules, no facts.
- `_covers` at lines 121-150 closes
  `strict_closure(covering_antecedents, self._strict_rules + shadowed)`
  where `shadowed = _force_strict_for_closure(rule) for rule in
  covered_argument.rules`. That is exactly `K_N ∪ An(T_covering) ∪ T_covered`
  with `T_covered`'s rules treated as strict-propagating for the
  closure check, matching Lemma 2.4's construction.
- `prefers` at lines 93-119 checks `_covers(left, right) AND NOT
  _covers(right, left)`. That is the strict ≻ direction: left covers
  right, right does not cover left. This is a strict partial order on
  the argument lattice modulo equi-specificity.
- `left == right` short-circuit at line 109 guarantees irreflexivity
  independently of the covering math.
- The empty-antecedent short-circuit at lines 138-141 returns `True`
  for empty covered antecedents. This is the vacuous quantifier
  `∀x ∈ ∅ . ...` = True. Correct under Simari 92 Prop 3.3
  ("equi-specificity for empty arguments").

Hypothesis properties at
`tests/test_specificity.py:125-152` verify irreflexivity,
antisymmetry, and transitivity at `max_examples=500`. Zero falsifying
examples. The properties encode the exact strict-partial-order axioms
the paper proves for Lemma 2.4's induced ordering.

**No drift. Lemma 2.4 implemented verbatim, with correct exclusion of
facts from `K_N`.**

### Q2 — Is `SuperiorityPreference` Garcia 04 §4.1?

**Verdict: ALIGNED. The paper supports strict-all-rules dominance.**

The critical question was whether Garcia 04 §4.1 intends strict
dominance ("every rule in A₁ dominates every rule in A₂") or
maximum-element dominance ("the highest-priority rule in A₁ dominates
the highest-priority rule in A₂").

`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md:170`,
verbatim (p.15):

> Rule priority criterion: explicitly ordered defeasible rules,
> argument preferred if **all its rules** have higher priority

That is strict-all-rules dominance. Not "some rule", not "the
highest rule", not "the max element" — **all its rules**. Garcia 04
§4.1 as recorded in the paper notes is unambiguous on this point.

`src/gunray/preference.py:236-240` implements exactly this:

```python
for lr in left.rules:
    for rr in right.rules:
        if (lr.rule_id, rr.rule_id) not in closure:
            return False
return True
```

Every pair in `left.rules × right.rules` must be in the transitive
closure of the priority relation. A single missing pair returns
`False`. The transitive closure is computed once per theory at
`preference.py:200-213`.

The 2 `partial-dominance` cases in B2.5 report §4 Group C
(`spindle_racket_simplified_penguin`,
`spindle_racket_test_theories::spindle_racket_penguin_exception`)
genuinely fail under the strict reading because a multi-rule
`flies` argument `⟨{r1, r2}, flies⟩` gets only a partial superiority
cover `(r3, r2)` or `(r4, r2)` — the priority relation doesn't cover
`(r3, r1)` or `(r4, r1)`. Under strict dominance, partial coverage is
insufficient. Under max-element dominance, these fixtures would pass.

**The paper says strict dominance. The Spindle fixtures apparently
use a weaker reading. Gunray correctly follows the paper.** B2.5's
test `test_superiority_partial_dominance_fails` at
`tests/test_superiority.py:234-254` pins the strict reading with a
paper-citation docstring and a synthesised multi-rule left argument.

No code change needed. The 2 partial-dominance fixtures are Spindle
deviating from the paper, not gunray. The foreman's
"no weakening" directive is correct.

### Q3 — Is `CompositePreference` the right composition?

**Verdict: ALIGNED (paper is silent; the implementation is a
defensible engineering choice).**

`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md:168-170` and
`:271` state Garcia 04's position: the comparison criterion is
**modular and replaceable**, but the paper gives no composition rule
for the case where multiple criteria apply simultaneously. §3.2 /
§4.1 does not say "specificity first" or "superiority first" — it
says the criteria can be swapped in and out, one at a time, per
application.

`defeasible.py:106-109` wires:

```python
criterion = CompositePreference(
    SuperiorityPreference(theory),
    GeneralizedSpecificity(theory),
)
```

Any-wins. Foreman directive: "explicit user-supplied priority wins,
specificity fallback". This is one of several defensible orderings.
Alternatives — specificity-first, all-agree intersection, disjoint
use-one-or-the-other — are all also defensible, and none has paper
authority over the others.

The foreman's choice is pragmatically motivated by the conformance
suite: the six Group-B-B2.5 wins are all equi-specific rule pairs
where only the superiority list can break the tie, so "superiority
first" is the path that lights up conformance wins. If the paper
had specifically mandated one order, the empirical evidence
(B2.5 report §5: "no fixture revealed the foreman's ordering
decision to be wrong") wouldn't be enough. But since the paper is
silent, empirical evidence plus clear citation of Garcia 04 §4.1's
modularity principle is enough.

**No drift. Composition order is a defensible engineering choice
under a paper-silent envelope.**

### Q4 — Defeater-rule participation

**Verdict: MINOR DRIFT (defensible; documented in B2.4 report but not
in `notes/refactor_progress.md#deviations`).**

Two red flags from the prompt:

**Red flag 1 (Garcia 04 defeater kind):** `B2.4 report §1 Observation
1` admits that the dispatch prompt's citation of "Garcia 04 Def 3.6"
does not exist. The paper notes confirm:
`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md:87-95` shows
Def 3.1, 3.3, 3.4, 3.5 followed immediately by Def 4.1 (proper
defeater) and Def 4.2 (blocking defeater). No Def 3.6.

Garcia 04 recognises only two rule kinds: strict and defeasible.
"Defeater" in Garcia 04 is a *role* an attacking argument plays in
the dialectical tree, not a rule kind. The third `kind="defeater"`
in gunray's `DefeasibleTheory.defeaters` is a Nute/Antoniou/Spindle
import that gunray inherited from its depysible-compatible origins
(the deleted `ambiguity.py` and the YAML fixtures).

B2.4's "Reading A" (one-rule defeater argument, filtered from warrant)
is the Nute convention. It is internally consistent, does not
interact badly with the Garcia 04 pipeline (because defeater
arguments are structurally regular `Argument` values — only the
`rules` field carries a `kind="defeater"` marker — and
`counter_argues`, `is_subargument`, and Def 4.7 all operate on rule
set shape, not rule kind), and is filtered out at two layers:

- `dialectic.py:488-496` `_is_warranted` skips any candidate whose
  rule set contains a defeater-kind rule.
- `defeasible.py:129-139` `_evaluate_via_argument_pipeline` skips
  defeater arguments in the `warranted` set and tracks them separately
  in `defeater_probed`.

This is defensible. The paper does not cover this case, so gunray is
free to make a projection choice.

**Red flag 2 (`defeater_probed → not_defeasibly`):** `defeasible.py:
137-180` routes atoms touched by defeater arguments into
`not_defeasibly` via the `defeater_probed` set. Exact code:

```python
defeater_probed: set[GroundAtom] = {
    arg.conclusion for arg in arguments if _is_defeater_argument(arg)
}
# ...
if no or defeater_touches:
    not_defeasibly_atoms.add(atom)
    classifications.append(ClassificationTrace(
        ...
        reason="complement_warranted" if no else "defeater_probed",
        ...
    ))
```

This is strictly outside Def 5.3. Garcia 04 Def 5.3's four answers
are YES/NO/UNDECIDED/UNKNOWN. A defeater-probed atom that is not
warranted (its defeater attacker blocks its peer but neither side
wins) falls into none of these cleanly — because Garcia 04 does not
define defeater rules at all.

The Spindle fixtures expect both the defeater head and its
complement in `not_defeasibly`, which is Spindle/DeLP's "probed and
fails" convention. Gunray's current projection matches. This is
defensible as a compatibility shim for a paper-undefined case, but
it is not paper-mandated.

**Drift call: minor and defensible, but should be in the deviations
log.** B2.4 report §6 acknowledges it as a "Section projection needed
a third path" surprise. `notes/refactor_progress.md#deviations` has
no Block 2 entry for it.

### Q5 — Paper-correct regressions: really permanent?

**Verdict: ALIGNED. Every one of the five new cases independently
verified.**

I read all five fixtures verbatim and re-derived the Def 3.1 cond 2
rejection mechanism by hand:

**`maher_example2_tweety`**
(`.venv/.../defeasible/superiority/maher_example2_tweety.yaml`) —
Facts `penguin: tweety, bird: freddie, injured: freddie`. Strict
`r3: bird(X) :- penguin(X)`, `r4: ~fly(X) :- injured(X)`. Defeasible
`r1: fly(X) :- bird(X)`, `r2: ~fly(X) :- penguin(X)`. Superiority
`[r2, r1]`.

`Pi` closure includes `~fly(freddie)` via strict `r4@freddie` +
fact `injured(freddie)`. Building `⟨{r1@freddie}, fly(freddie)⟩`
requires `Pi ∪ {r1@freddie}` non-contradictory; closure becomes
`{..., fly(freddie), ~fly(freddie)}` — contradictory. Def 3.1 cond 2
rejects. `fly(freddie)` is never a conclusion in `build_arguments`'s
output. Fixture expects `not_defeasibly: fly: [[freddie], [tweety]]`.
The `conclusions` loop at `defeasible.py:163` never iterates
`fly(freddie)` because it isn't in the conclusion set. Hence it is
omitted from the section. **Mechanism confirmed.**

**`maher_example3_freddie_nonflight`** — identical theory (except
facts); identical mechanism. **Confirmed.**

**`spindle_racket_strict_beats_defeasible`** — facts `a, b`, strict
`r1: c :- a, b`, defeasible `r2: ~c :- a, b`. Pi contains `c` via
`r1 + facts`. `⟨{r2}, ~c⟩` gets `Pi ∪ {r2}` contradictory (both `c`
and `~c`). Cond 2 rejects. `~c ∉ conclusions`. Fixture expects
`not_defeasibly: ~c`. **Confirmed.**

**`spindle_racket_mixed_strict_defeasible_conflict`** — strict
`r1: c :- a`, defeasible `r2: ~c :- b`, facts `a, b`. Pi contains
`c`. `⟨{r2}, ~c⟩` rejected by cond 2. **Confirmed.** (Note: this
fixture has `conflicts: [[c, ~c]]` which is redundant since `c` and
`~c` are already complementary literals — it doesn't affect the
rejection.)

**`morris_example5_tweety_blocked_default`** — facts `bird: tweety,
chirpy` and `~fly: tweety`. Defeasible `r1: fly(X) :- bird(X)`.
`Pi` contains `~fly(tweety)` directly as a fact. `⟨{r1@tweety},
fly(tweety)⟩` gets `Pi ∪ {r1@tweety}` closing to include both
`fly(tweety)` and `~fly(tweety)` — contradictory. Cond 2 rejects.

**Critical B2.4 misclassification note:** the fixture YAML has
`superiority: []` (no superiority list at all). B2.4 classified it
as `specificity-no-help (superiority)` based purely on a superficial
reading of the filename pattern; the fixture never had superiority
content. B2.5 caught the misclassification. This is a B2.4 drift
that B2.5 fixed — but it means B2.4's classification table was at
least one row wrong purely from the fixture-name heuristic, not
from mechanism inspection. Not a principle violation (the net
answer is correct) but worth noting as a lesson.

**All five new cases are correctly classified as paper-correct
regressions.** The uniform mechanism is: Pi strictly entails the
complementary literal → Def 3.1 cond 2 rejects the argument the
fixture expects → the atom never enters the conclusion set → the
section projection loop at `defeasible.py:163` never iterates it
→ omitted from every section. The fixtures encode a Spindle/DePYsible
convention (populate `not_defeasibly` with "unprovable heads") that
is not a Garcia 04 semantics. Paper wins per the foreman directive.

### Q6 — Spindle implicit-failure classification gap defensible?

**Verdict: DEFENSIBLE PAPER GAP.**

The three cases are:
- `spindle_racket_unsatisfied_antecedent` (fact `p`, rule
  `r :- p, q`; no `q`)
- `spindle_racket_query_missing_premise_failure` (defeasible
  `ready_review :- tests_pass, code_complete`; only `code_complete`
  is a fact)
- `spindle_racket_query_missing_premise_theory` (same theory as
  above, different file)

Mechanism: a defined-but-unprovable head. The predicate IS in the
language (it is a rule head). There is no argument for the head
(body is not derivable), and no argument for its complement. Not
the same as Group A (where Pi strictly entails the complement and
the complementary literal has an `⟨∅, complement⟩` argument).

Garcia 04 Def 5.3 states:
- **YES**: `h` is warranted.
- **NO**: `~h` is warranted.
- **UNDECIDED**: neither is warranted **but there exists at least
  one argument for `h` or `~h`**.
- **UNKNOWN**: `h` is not in the language of the program.

UNDECIDED explicitly requires an argument to exist. UNKNOWN requires
the predicate to be out-of-language. The defined-but-unprovable case
satisfies neither precondition: the predicate IS in the language
(UNKNOWN is wrong), and NO argument exists for either side
(UNDECIDED is wrong under the paper's literal phrasing).

**Garcia 04 Def 5.3 does not cleanly cover this case.** The paper
has a genuine four-valued gap. Gunray's current behaviour — omit
the atom from all sections — is the paper-strict projection choice
(if no section can contain it, put it in none). Spindle/DePYsible
chooses `not_defeasibly` as the projection. Both are defensible; the
paper has no opinion.

B2.5's classification of these as "spindle-implicit-failure-gap"
separate from Group A (paper-correct regressions) is correct. These
are NOT Def 3.1 cond 2 rejections — the arguments are rejected by
condition (1), not (2) — but the section-projection consequence is
similar: the atom never makes it into the conclusion set.

**No drift. The paper gap is real; the defensible choice is
"omit".** If propstore or a downstream consumer eventually
requires the Spindle projection, the fix is a small addition to
`_classify_defeasibility` that seeds `not_defeasibly` from every
defeasible rule head that has no argument — but that would be a
Spindle-compat shim, explicitly outside Def 5.3, and should be
recorded as a deviation.

### Q7 — Implementation smuggling audit

**Verdict: ALIGNED (one known shim, documented).**

I looked for:
- Special-case branches keyed to fixture filenames. **None found.**
- Non-paper classification paths in `_classify_defeasibility`. **One
  found: `defeater_probed` at `defeasible.py:137-180`.** Documented
  in the B2.4 report §6.
- Ad-hoc "if not found in X, fall back to Y" paths. **None found
  beyond the B2.4 `defeater_probed` shim.**
- Spindle/DePYsible compatibility toggles introduced without
  foreman approval. **None.**

The `pytest_collection_modifyitems` deselection of
`spindle_racket_query_long_chain` at `tests/conftest.py` is a
documented scalability workaround (B2.3 report §6, option 3) that
preserves the fixture for a future goal-directed rewrite. The fixture
stays in the suite; only the collection hook excludes it. This is
not smuggling; it is a documented engineering deferral.

**No other smuggling.**

### Q8 — Argument pair shape

**Verdict: ALIGNED.**

`src/gunray/arguments.py:42-55`:

```python
@dataclass(frozen=True, slots=True)
class Argument:
    rules: frozenset[GroundDefeasibleRule]
    conclusion: GroundAtom
```

Two fields. `frozen=True, slots=True`. No new field, no method
creep. The defeater-argument path at `arguments.py:184-192` emits
regular `Argument` values where the `rules` field happens to contain
only `kind="defeater"` rules — no new type, no new field, no new
category.

**Pair shape preserved.**

### Q9 — Does `CompositePreference` satisfy strict partial order axioms?

**Verdict: DRIFT — composition is NOT a strict partial order, and
this is acknowledged in the test suite but not in the deviations
log.**

The counterexample the prompt asked me to construct is already in
the test suite verbatim. `tests/test_superiority.py:257-278`:

```python
def test_composite_superiority_over_specificity() -> None:
    """Specificity says r1 > r2; superiority says r2 > r1; composite picks r2."""
    ...
    # Sanity: specificity alone prefers r1; superiority alone prefers r2.
    assert spec.prefers(r1_arg, r2_arg) is True
    assert sup.prefers(r2_arg, r1_arg) is True

    # Composite: superiority fires first and wins.
    assert composite.prefers(r2_arg, r1_arg) is True
    assert composite.prefers(r1_arg, r2_arg) is True
    # NB: both can be true here — this is exactly the composite-disagreement
    # case that motivates the foreman's any-wins semantics. ...
```

**This is an explicit, asserted violation of asymmetry.** With
P1 preferring a>b and P2 preferring b>a, the composite says both
directions simultaneously. A strict partial order requires `∀a, b.
¬((a ≻ b) ∧ (b ≻ a))`. The composite fails this axiom by design.

Transitivity is also lost in general. Consider P1: `a > b`, P2:
`b > c`. Composite says `a > b` (via P1) and `b > c` (via P2). But
neither child claims `a > c`, so composite says `a > c` is False.
Transitivity fails.

The Garcia 04 §4 / §5 theorems about the dialectical tree's marking
behaviour (Procedure 5.1) are stated over strict partial order
preferences. Gunray's composite is not one. Operationally, gunray's
`_defeat_kind` at `dialectic.py:211-237` resolves each defeat
locally (one candidate vs one sub-argument at a time) and does not
rely on global transitivity or asymmetry — so the pipeline remains
well-defined and deterministic. But the theoretical guarantees no
longer follow from the paper directly; they would need to be
re-proven for a non-strict-order preference.

**The docstring at `preference.py:266-272` is technically accurate**
— it claims only irreflexivity and a weak "monotonicity" property,
never strict partial order. **The B2.5 Hypothesis property
`test_hypothesis_composite_is_monotonic` is NOT an axiom check:**
it verifies `composite.prefers(a, b) → some child fires`, which is
trivially true by the definition of `any`. It is not a strict-PO
property test.

**This is a real drift that was never surfaced as a deviation.** The
coder knew (the test comment says "both can be true here"); the
adversary review is the first place it lands as a foreman-level
finding. Three defensible responses:

1. **Fix the composition.** Replace `any`-wins with a
   "first-criterion-to-fire, ordering-sensitive" semantics:

   ```python
   for c in self._criteria:
       if c.prefers(left, right):
           return True
       if c.prefers(right, left):
           return False
   return False
   ```

   This preserves asymmetry when each child is asymmetric, and it
   preserves transitivity up to the first-firing child. It matches
   the foreman's "superiority wins where it fires, specificity
   fallback" directive more cleanly than `any`-wins.

2. **Keep `any`-wins and document the drift.** Add an entry to
   `notes/refactor_progress.md#deviations` stating that the composite
   is not a strict partial order, explain why the dialectical tree
   still works operationally, and cite the test comment.

3. **Verify empirically.** Run the composite-aware Hypothesis
   property `test_hypothesis_composite_is_irreflexive_and_asymmetric`
   (new) against the small_theory_strategy at max_examples=500 and
   see how often the composite fails asymmetry. If it fails commonly,
   option 1 becomes more compelling. If it fails only on rare
   superiority-inversion cases, option 2 is adequate.

Option 1 is the cleanest fix and is the recommendation below.

### Q10 — Deviations audit

**Verdict: DRIFT (Block 2 entries are missing from the log).**

`notes/refactor_progress.md#deviations` is thorough through B1.6:

- P0.1.5 / P0.1.6 / `nests_in_trees` victory lap: all documented
  with Q's mid-execution approval cited, all justified with paper-
  level reasoning.
- B1.5 Opus answer test assertions: a full deviation entry with
  rendered trees, the paper-correct UNDECIDED result under
  TrivialPreference, and an explicit "I do not take architectural
  discretion" paragraph.
- B1.6 `nests_in_trees(tweety)` paper-rejection: a full deviation
  entry citing Def 3.1 cond 2 verbatim and classifying the fixture
  as `real-regression-paper-correct`.

**Block 2 has no deviation entries.** The following should have
entries but don't:

1. **B2.3 `Policy.PROPAGATING` deprecation.** This is recorded in
   `notes/policy_propagating_fate.md` (a foreman decision document)
   but not in the deviations log. The decision is clean and paper-
   justified, but the deviations section is the canonical place for
   "plan said X, we did Y" records.
2. **B2.4 `defeater_probed` section projection shim.** Strictly
   outside Def 5.3. Documented in the B2.4 report §6 surprises, but
   not in the deviations log. A paper-gap-compat choice, defensible
   but undocumented at the canonical place.
3. **B2.5 `CompositePreference` is not a strict partial order.**
   Acknowledged in the test comment, not in the B2.5 report's
   explicit surprises list (though the "composition interpretation
   notes" §5 hints at it by saying the ordering "is theoretical").
   Not in the deviations log. This is the biggest gap.
4. **B2.5 250 paper-correctness ceiling.** The original Block 2 gate
   was ≥267; the B2.5 report discovers the real ceiling is 250 and
   explains why. This is the most consequential plan revision of
   Block 2, and it should have a deviation entry documenting the
   foreman's acceptance of the revised ceiling and the classification
   of the 17-case gap.

**None of these is a smuggled architectural discretion.** All four
are documented in their respective reports and are paper-reasoned.
The drift is purely at the meta-level of "the deviations log should
be the canonical record, and the log is not up to date for Block 2".

---

## Block 2 gate reality check

**The 250 ceiling is the real paper-correctness maximum under the
foreman's "no weakening" directive.** Verification:

- **28 `nemo_negation`** cases: pre-existing P0.1.5 engine bug
  (`SafetyViolationError`). Independent of the defeasible pipeline;
  Block 2 is not the place to fix it.
- **9 `paper-correct-regression`** cases: Def 3.1 cond 2 genuinely
  rejects the arguments the fixtures expect. The mechanism is
  Garcia 04's own behaviour under the paper-defined argument
  existence conditions. These fixtures encode Spindle/DePYsible's
  "populate unprovable heads" convention. Fixing them requires
  weakening Def 3.1 cond 2 or adding a non-paper classification path.
- **3 `spindle-implicit-failure-gap`** cases: Def 5.3 doesn't cover
  the defined-but-unprovable head. Paper-strict choice is "omit".
  Fixing them requires adding a Spindle-compat projection path.
- **2 `partial-dominance`** cases: Garcia 04 §4.1 literally says
  "all its rules have higher priority". The strict reading is
  paper-correct; the Spindle fixtures use a weaker reading. Fixing
  them requires weakening `SuperiorityPreference` to some "max-
  element" or "any-dominates-any" variant.
- **2 `regime-not-implemented`** cases: Antoniou propagating semantics
  deprecated per `notes/policy_propagating_fate.md`. Out of the
  two-paper source-of-truth envelope.
- **1 `scalability`** case: goal-directed argument enumeration
  deferred to a follow-up plan.

Total: 28 + 9 + 3 + 2 + 2 + 1 = **45 cases** accounted for. B2.5
reports 250 passed / 44 failed / 1 deselected, so 45 = 44 + 1.
Matches exactly.

**Is there a defensible path to higher than 250?**

Yes, but not under the "no weakening" directive:

- **+3 cases** by adding a Spindle-compat projection path for the
  implicit-failure gap (Group Q6). Seed `not_defeasibly` with every
  defeasible rule head that has no argument. Cost: ~10 LOC in
  `_classify_defeasibility`. Paper status: non-Garcia compat shim.
- **+2 cases** by weakening `SuperiorityPreference` to "max-element
  dominance" or "any-rule dominates any-rule". Cost: ~5 LOC in
  `preference.py`. Paper status: contradicts the paper notes line 170.
- **+9 cases** by adding a Spindle-compat projection that populates
  `not_defeasibly` for atoms whose complement is in Pi's strict
  closure even when the atom itself has no argument. Cost: a second
  classification path in `_classify_defeasibility` that iterates the
  Pi closure rather than just the conclusions. Paper status: adds a
  non-paper projection layer.
- **+2 cases** by restoring a `Policy.PROPAGATING` implementation
  via a tree-construction variant that demands proper defeaters at
  every expansion. Paper status: Antoniou 2007 rather than Garcia 04.

**Total ceiling under Spindle-compat shims: ~266** (+16 cases). Still
short of the original 267 gate (because nemo_negation is out-of-scope
for any of these). Reaching 267 requires fixing the nemo_negation
engine bug, which is plan-independent.

**Recommendation: accept 250 as the Block 2 ceiling.** All 16
Spindle-compat cases are recoverable in a dedicated "Spindle-compat"
follow-up block (call it Block 2.5 or Block 3 pre-work), each with
its own explicit paper-deviation entry. The refactor's "paper wins"
principle remains intact because the shims are opt-in and confined
to the section-projection layer, not the argument-enumeration or
dialectical-tree layers.

---

## Disagreements with the coder reports

### Disagreement 1 — B2.4 "specificity-no-help (superiority)" classification

**Coder claim (B2.4 report §7):** "The remaining 16
`specificity-no-help` cases all have equi-specific rule pairs and
require the theory's explicit `superiority` list to break the tie."

**Reality:** B2.5 discovered that 10 of the 16 don't have that
shape at all. 5 are Def 3.1 cond 2 paper-correct regressions, 3 are
the Spindle implicit-failure gap, 2 are partial-dominance edge cases.
Only 6 of the 16 are actually resolvable by `SuperiorityPreference`.

**Root cause:** B2.4's classification was based on the presence of a
`superiority:` field in the fixture YAML, not on mechanism inspection.
`morris_example5_tweety_blocked_default` has `superiority: []` —
literally no superiority content — and B2.4 still bucketed it as
superiority-needed. That is pure filename/tag-based bucketing.

**Severity:** Low. The B2.5 reclassification is correct, and B2.5
explicitly flags this as a misclassification. No code is wrong — but
the B2.4 report's confidence in its 16-case estimate was misplaced,
and if the foreman had dispatched B2.5 with a "make all 16 pass"
directive (instead of "land SuperiorityPreference and classify
everything"), B2.5 would have been set up to fail with a confusing
verdict.

### Disagreement 2 — B2.5 composition-interpretation notes

**Coder claim (B2.5 report §5):** "No fixture revealed the
foreman's ordering decision to be wrong. ... The foreman's
decision is theoretical."

**Reality:** The composition is not a strict partial order. Under
`any`-wins semantics, the composite can exhibit both asymmetry and
transitivity failures (see Q9 above). The test
`test_composite_superiority_over_specificity` explicitly exercises
an asymmetry-failing case. That is strictly stronger than "the
ordering is theoretical" — the composite is a broken preference
relation at the theoretical level, and its operational correctness
depends on `_defeat_kind` resolving each defeat locally without
requiring global transitivity.

**Severity:** Medium. No production impact observed, but this is
a latent hazard. If a future refactor adds caching or pruning to
the dialectical tree construction that exploits transitivity (e.g.
"if `a > b` and `b > c` then skip considering `a > c`"), the
composite's transitivity failure will cause incorrect answers.

### Disagreement 3 — B2.4 "Garcia 04 Def 3.6" prompt

The prompt `prompts/b2-defeater-participation.md` cites
"Garcia 04 Def 3.6" as the authority for defeater-rule semantics.
B2.4 correctly identified that there is no Def 3.6 in Garcia 04.
This is a prompt bug, not a coder issue, but the B2.4 report
correctly flagged it.

**Severity:** Documentation only. The foreman's prompt should be
corrected to cite "Nute 1994 / Antoniou 2007" for the defeater kind
or to explicitly acknowledge that defeater rules are a gunray-level
convenience not in the paper source-of-truth set.

---

## Recommendations to the foreman

Before Block 3 starts:

1. **Record Block 2 deviations.** Add to
   `notes/refactor_progress.md#deviations` four entries, one each
   for: the `Policy.PROPAGATING` deprecation (cite
   `notes/policy_propagating_fate.md`); the B2.4 `defeater_probed`
   shim (cite B2.4 report §6); the B2.5 `CompositePreference`
   non-strict-partial-order situation (cite
   `tests/test_superiority.py:273-278`); the B2.5 250-ceiling
   discovery and the Spindle-compat cost/benefit.

2. **Fix `CompositePreference` to be a strict partial order.**
   The cleanest fix is to replace `any`-wins with
   first-criterion-to-fire-ordering-sensitive semantics:

   ```python
   def prefers(self, left: Argument, right: Argument) -> bool:
       for c in self._criteria:
           if c.prefers(left, right):
               return True
           if c.prefers(right, left):
               return False
       return False
   ```

   This preserves the foreman's "superiority first, specificity
   fallback" directive while restoring asymmetry and transitivity
   at the composite level. Add a new Hypothesis property
   `test_hypothesis_composite_is_asymmetric` at max_examples=500.
   Rerun the conformance suite; expect the B2.5 250 pass count to
   hold (because the wins are all on equi-specific rule pairs where
   specificity is silent and superiority fires first regardless of
   semantics).

   Scope: one small coder dispatch, maybe a B2.7 or a Block 3
   pre-work. Not blocking Block 3, but better to land before
   propstore starts consuming the new preference API.

3. **Correct the B2.4 prompt's "Garcia 04 Def 3.6" citation.**
   Replace with "Nute 1994 / Antoniou 2007 defeater rule convention;
   Garcia 04 does not define a third rule kind".

4. **Accept the 250 ceiling as a documented Block 2 result.** The
   17 remaining in-scope failures each fall into a paper-defined or
   paper-gap category that cannot be resolved without explicit
   Spindle-compat shims. Defer those shims to a dedicated Spindle-
   compat block after Block 3 propstore work is complete, or leave
   them permanently as "gunray is the paper-strict implementation,
   Spindle is the paper-relaxed one".

5. **Do not fix the Q6 Spindle implicit-failure gap in Block 3.**
   The three affected cases require a non-paper projection path
   in `_classify_defeasibility`. Adding it would be the first
   paper-ambiguity-driven deviation in the section projection
   layer, and it should get its own dispatch with an explicit
   deviation log entry, not be smuggled into Block 3's propstore
   integration work.

6. **Record the 5-fixture Q5 verification as an adversary
   signoff.** The foreman can now cite this review as independent
   paper-mechanism verification for the 9 total paper-correct
   regressions (4 B1.6 carryovers + 5 B2.5 new) rather than relying
   solely on the coder reports.

Block 3 may start as soon as (1) and (3) are addressed. (2) can
land in parallel with Block 3 or as a B2.7 follow-up. (4), (5), (6)
are documentation-only. Nothing in this review blocks Block 3.

---

## One-line verdict

**DRIFT — Block 2 is paper-aligned on the load-bearing questions
(Lemma 2.4, Garcia 04 §4.1 strict dominance, Def 3.1 cond 2, Def
5.3), the 250 ceiling is a real paper-correctness ceiling, and no
principle is violated — but the `CompositePreference` any-wins
semantics is not a strict partial order, the `defeater_probed`
section-projection shim is a Spindle-compat layer outside strict Def
5.3, and neither is recorded in the deviations log alongside the
Block 2 ceiling and the Policy deprecation; fix the composite and
update the log before Block 3 starts.**
