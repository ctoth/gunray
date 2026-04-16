# B1.8 — Adversary review progress

Date: 2026-04-13

## GOAL
Directional paper-alignment review of Block 1. Answer Q1–Q10, focus
on Q10 (nests_in_trees Def 3.1 cond 2 reading). Produce
`reports/b1-adversary.md`. Read-only.

## DONE (so far)
- Read prompt `prompts/b1-adversary.md` fully.
- Read plan `plans/ticklish-frolicking-bengio.md`.
- Read scout report `reports/b1-scout.md` sections 1-3 (landing
  spots, public contract, closure.py API).
- Read source verbatim: `arguments.py`, `disagreement.py`,
  `dialectic.py`, `answer.py`, `preference.py`, `defeasible.py`.

## OBSERVATIONS (verbatim from source)
- `Argument` dataclass is frozen(slots), exactly two fields
  `rules: frozenset[GroundDefeasibleRule]` and
  `conclusion: GroundAtom`. (arguments.py:42-55)
- `is_subargument(a, b)` is `a.rules <= b.rules`. Reflexive
  subset-on-rules. (arguments.py:58-67)
- `counter_argues` delegates to `_disagreeing_subarguments`, which
  iterates over ALL `build_arguments(theory)` and filters by
  `is_subargument(sub, target)`. It descends, not root-only.
  (dialectic.py:84-123)
- `build_tree` / `_expand` enforces Def 4.7:
  - cond 1: `build_arguments` returns finite frozenset.
  - cond 2: `_concordant(supporting, theory)` +
    `_concordant(interfering, theory)` checked at EVERY child admit.
  - cond 3: `any(is_subargument(candidate, earlier) for earlier in line)`.
  - cond 4: `parent_edge_kind == "blocking" and kind == "blocking"`
    truncates. (dialectic.py:270-333)
- `mark` is pure post-order, no cache, no second parameter.
  (dialectic.py:336-352)
- `answer` builds one arguments set once, calls `_is_warranted` for
  literal and complement. Handles UNKNOWN via
  `_theory_predicates` + `_strip_negation`. Returns UNDECIDED if
  some argument exists for either polarity, else UNKNOWN only if
  BOTH literal_predicate and complement_predicate are absent from
  the language — otherwise falls through to UNDECIDED. That is the
  suspicious fall-through: predicate in language but no argument ⇒
  UNDECIDED (not UNKNOWN). (dialectic.py:489-537)
- `build_arguments` enumerates every subset of grounded defeasible
  rules via `combinations`, checks non-contradiction via
  `_has_contradiction` on `strict_closure(fact_atoms, strict + A')`
  where `A'` are defeasible rules wrapped as strict via
  `_force_strict_for_closure`. Minimality enforced by comparing
  `rule_set` against `prior` survivors. (arguments.py:70-209)
- `_force_strict_for_closure` wraps defeasible as strict
  **only for the closure computation** of Def 3.1 cond 2.
  (arguments.py:212-226)
- `disagrees` takes a complementary shortcut then falls through to
  strict_closure check. Strict closure path IS taken when
  h1 != complement(h2). (disagreement.py:68-87)
- `_concordant` also uses `_force_strict_for_closure`. Def 4.7
  cond 2 interpretation matches Def 3.1 cond 2 interpretation.
- `defeasible.py` projection produces all four keys always, then
  filters empty ones when constructing `DefeasibleModel`. Section
  keys are byte-identical ("definitely", "defeasibly",
  "not_defeasibly", "undecided"). (defeasible.py:187-195)

## STUCK / BLOCKER
- Need to read paper notes for Def 3.1, Def 3.3, Def 3.4, Def 4.1,
  Def 4.2, Def 4.7, Def 5.1, Def 5.3, Proc 5.1, Simari Def 2.2.
- Need to read analyst report + coder reports + refactor_progress
  deviations section to form disagreements.
- Q10 blocker: need paper-notes text on "Pi union A is
  non-contradictory" to decide whether `_force_strict_for_closure`
  is paper-correct or over-eager.

## NEXT
Complete: `reports/b1-adversary.md` written.
Verdict: **ALIGNED**. Q10: coder's Def 3.1 cond 2 reading is
paper-correct (anchored to Simari 92 Def 2.2's `K ∪ T |/~ ⊥`,
corroborated by Garcia 04 Prop 4.2 and the henrietta control case).
