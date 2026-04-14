# B2.2 — GeneralizedSpecificity progress notes

## 2026-04-13 start

**GOAL:** Extend `src/gunray/preference.py` with `GeneralizedSpecificity`
implementing Simari 92 Lemma 2.4 antecedent-only reduction. 6 paper-example
unit tests + 4 Hypothesis properties at max_examples=500. Strict TDD.
Do NOT wire into evaluator (B2.3). Do NOT touch Policy.PROPAGATING (B2.3).

**FILES:**
- `src/gunray/preference.py` — target, currently 37 LOC; contains
  `PreferenceCriterion` protocol + `TrivialPreference`.
- `src/gunray/arguments.py` — contains `_force_strict_for_closure`
  (line 212) and `Argument` dataclass (line 42). Reuse the shadow pattern.
- `src/gunray/disagreement.py` — contains `strict_closure` (line 41),
  filters on `kind == "strict"`. Must shadow defeasible rules first.
- `src/gunray/schema.py` — `DefeasibleTheory`, `Rule`, `Policy`.
- `tests/test_specificity.py` — new test file to create.
- `tests/conftest.py` — has `small_theory_strategy` etc. Reuse for
  Hypothesis properties.

## Lemma 2.4 formula (verbatim from paper notes p.14)

`⟨T₁, h₁⟩ ≽ ⟨T₂, h₂⟩` iff `∀x ∈ An(T₂), K_N ∪ An(T₁) ∪ T₂ |~ x`.

Strict: add converse-fails side.

## Observations

- `build_arguments` computes ground rules and pi_closure. The
  `Argument.rules` field carries `frozenset[GroundDefeasibleRule]` —
  already ground.
- `strict_closure(seeds, strict_rules)` forward-chains. Seeds are
  facts/atoms; strict_rules filtered by `kind=="strict"`.
- Strategy for Lemma 2.4 check: seeds = `K_N_facts ∪ An(T₁) ∪ An(T₂)`?
  No — the formula is `K_N ∪ An(T₁) ∪ T₂ |~ x`. K_N is the strict-rule
  context (rules + facts). An(T₁) are antecedent literals seeded in.
  T₂ are the defeasible rules from the right argument, treated as
  strict for the closure check (reuse `_force_strict_for_closure`).
- An(T) = union of rule bodies for r in T.rules.
- The pi_closure of facts under strict rules is `K_N`. Strict closure
  call shape: `strict_closure(facts_plus_antecedents, strict_rules + shadowed_T2)`.
- `theory.strict_rules` is `list[Rule]` (ungrounded). Must ground them
  via the grounding machinery. Simplest path: call `build_arguments`
  or replicate the grounding step. Or: pull ground strict rules from
  a helper. Need to check — can I just call the existing internals, or
  do I need to re-ground? Options:
  - Option A: duplicate grounding logic (bad, violates DRY)
  - Option B: expose a helper `_ground_theory_strict` in arguments.py
    and call it from preference.py
  - Option C: grind the theory once via the same `_positive_closure_for_grounding`
    + `_ground_rule_instances` path
  
  **CHOOSING:** Option B — factor a small internal helper so
  preference.py depends only on one shared function.

## Nixon test concern

Prompt Test 3 uses `direct_nixon_theory` (no `nixonian` indirection) but
the simpler form. The two rules r1 `~pacifist :- republican` and
r2 `pacifist :- quaker` should be equi-specific. Check:
- left=r1, right=r2. An(r1)={republican(nixon)}. An(r2)={quaker(nixon)}.
  Seeds = {quaker(nixon), republican(nixon), ...facts, shadow(r1)}?
  No: `K_N ∪ An(T₁) ∪ T₂` — seeds = facts + An(left) + shadow(T_right).
- So seeds for left≽right: facts + {republican(nixon)} + shadowed_r2
- Does quaker(nixon) ∈ closure? Only if fact. Yes — `quaker` is a fact.
- So quaker(nixon) is in closure trivially via fact. That means
  ∀x ∈ An(r2): x in closure → True, so left ≽ right.
- Symmetric: right ≽ left trivially too.
- → equi-specific → returns False. Correct.

Actually wait — if facts supply both quaker and republican, **both
sides** trivially cover the other. Good. This is why Nixon is
equi-specific: it's not about rules, both premises are just facts.

## Opus test sanity check

Facts: bird(opus), penguin(opus). Strict: s1: bird(X) :- penguin(X).
Defeasible: r1: flies(X) :- bird(X), r2: ~flies(X) :- penguin(X).

left = r2 (penguin branch, ~flies(opus)). right = r1 (bird branch).
An(left) = {penguin(opus)}. An(right) = {bird(opus)}.

left ≽ right? seeds = facts + {penguin(opus)} + shadowed(r1).
Is bird(opus) ∈ closure? Yes — fact AND via s1 from penguin.
→ True.

right ≽ left? seeds = facts + {bird(opus)} + shadowed(r2).
Is penguin(opus) ∈ closure? It's a fact — yes.
→ True.

**PROBLEM:** Because penguin(opus) is a FACT in this theory, the
trivial covering holds both ways. That would make them equi-specific!

This is the classic problem with grounded specificity vs generalized
specificity. The paper's Lemma 2.4 is stated for abstract arguments
over the theory, not over the ground instance. The covering has to
ignore trivializing facts — K_N = strict RULES, not K_N ∪ facts.

Re-reading prompt: "For Phase 2 gunray we treat K_N as the
strict-rule set." Only rules, not facts!

**This is load-bearing.** The prompt explicitly says K_N is
strict-rule-only, excluding facts. Without that, the Opus test fails
equi-specific when it should be strict.

So: seeds = An(T₁) ∪ An(T₂) (no facts), closed under
`strict_rules + shadow(T₂)`.

Re-check Opus with facts excluded:
- left ≽ right: seeds = {penguin(opus), bird(opus)} (from left ant + maybe right ant? no, `An(T₁) ∪ T₂` — seeds are just An(T₁))
  
  Wait, rereading: "`K_N ∪ An(T₁) ∪ T₂ |~ x`" where x ∈ An(T₂).
  So seeds = An(T₁), rules = strict_rules + shadow(T₂), and we check
  each x ∈ An(T₂) is in the closure.
  
- left=r2, right=r1. An(left)={penguin(opus)}, An(right)={bird(opus)}.
- left ≽ right: seeds={penguin(opus)}, rules=[s1] + shadow([r1]).
  strict_closure: penguin(opus) → (via s1) bird(opus). ✓
  Is bird(opus) in closure? Yes. So left ≽ right.
- right ≽ left: seeds={bird(opus)}, rules=[s1] + shadow([r2]).
  strict_closure: bird(opus) is seed; s1 needs penguin(opus) in
  body, not there; r2 shadowed: head=~flies(X), body=penguin(opus),
  not fired. Closure = {bird(opus)}.
  Is penguin(opus) in closure? NO. So right does NOT cover left.
- ∴ left ≽ right, but not right ≽ left → left strictly more specific. ✓

For Nixon with same pattern (K_N = strict rules only, no facts):
- An(r1)={republican(nixon)}, An(r2)={quaker(nixon)}.
- left=r1 ≽ right=r2: seeds={republican(nixon)}, rules=[] + shadow(r2).
  r2 shadowed: head=pacifist(X), body=quaker(X). quaker(nixon) not
  in closure, r2 doesn't fire. Closure = {republican(nixon)}.
  Is quaker(nixon) in closure? NO. → r1 does not cover r2.
- Symmetric: r2 does not cover r1.
- → neither prefers. ✓ Matches equi-specific expectation.

GOOD. K_N must be strict rules only (no facts).

## STUCK: none yet. Starting TDD.

## NEXT

1. Write test_specificity.py with test 1 (Opus) in red state.
2. Commit red.
3. Implement GeneralizedSpecificity skeleton that fails.
4. Make Opus test pass (green).
5. Add tests 2, 3, 5, 6 — likely all green with one impl.
6. Add test 4 (Royal Elephants) — may need more work.
7. Add Hypothesis properties (red first for each).
8. Commit each green.
9. Verification: pyright, pytest, record commit hashes.

## COMMITS (so far)

- 54ce786 — test(specificity): paper-example and Hypothesis property tests (red)
- (green commit pending)

## Progress 2026-04-13 mid-dispatch

**DONE:**
- Read prompt, scout report, paper notes, arguments.py, disagreement.py,
  preference.py, conftest.py, schema.py.
- Wrote notes file with Lemma 2.4 analysis including the load-bearing
  insight that K_N must be strict-rules-only (excluding facts) to
  produce the correct Opus and Nixon verdicts.
- Baseline pytest: 106 passed / 1 pre-existing fail (test_closure_faithfulness).
- Wrote tests/test_specificity.py (330 lines): 6 paper unit tests +
  4 Hypothesis properties at max_examples=500. Initial red state
  confirmed (ImportError for GeneralizedSpecificity).
- Commit 54ce786 captures red state.
- Refactored src/gunray/arguments.py: extracted `_GroundedTheory`
  dataclass and `_ground_theory()` helper, then rewrote
  `build_arguments` to call it. All 15 arguments/build_arguments
  tests still pass — refactor clean.
- Wrote src/gunray/preference.py GeneralizedSpecificity class:
  - `__init__` stashes grounded strict rules (excluding facts).
  - `prefers(left, right)` computes covering via
    `_covers(left_ant, right, right_ant)` then `_covers(right_ant,
    left, left_ant)`.
  - `_covers` does strict_closure(covering_antecedents,
    strict_rules + shadowed_covered_rules) and checks
    covered_antecedents ⊆ closure.
  - Empty-antecedent case returns vacuously True (covers).
  - `left == right` short-circuit for irreflexivity.
  - Helper `_antecedents_of(argument)` = union of rule bodies.
- Docstring cites Simari 92 Def 2.6, Lemma 2.4, Garcia 04 Def 3.5
  (paper-citation ratchet).
- All 10 tests pass first try (6 paper + 4 Hypothesis @ 500 examples).
  Hypothesis stats: 500 passing per property, 24-48 invalid.

**OBSERVED:**
- Royal African Elephants verdict: d2 (gray via african_elephant) is
  strictly preferred over d1 (~gray via elephant). Verified by the
  test passing.
- Opus: r2 (penguin) strictly preferred over r1 (bird). Verified.
- Nixon: equi-specific in both directions. Verified.
- No Hypothesis counterexamples. Strict partial order holds on the
  small_theory strategy with 500 examples per property.

**STUCK:** none.

**NEXT:**
1. Commit the green state (refactor + GeneralizedSpecificity).
2. Run full test suite (non-conformance) to confirm no regression.
3. Run pyright on preference.py and test_specificity.py.
4. Write reports/b2-specificity.md.
5. Final LOC count for preference.py.

