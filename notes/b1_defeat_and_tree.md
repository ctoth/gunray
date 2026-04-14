# B1.4 progress — defeat, tree, acceptable lines, marking

## GOAL
Create `src/gunray/dialectic.py` with `counter_argues` (descends into
sub-arguments — directional fix), `proper_defeater`,
`blocking_defeater`, `DialecticalNode`, `build_tree` enforcing Garcia
04 Def 4.7 during construction, `mark` per Proc 5.1. Strict TDD red/
green. 10 paper-example tests + 7 Hypothesis properties in
`tests/test_dialectic.py`.

## DONE so far (2026-04-13)
- Read prompt `prompts/b1-defeat-and-tree.md`.
- Read reports: scout (sections 5 and index), B1.2, B1.3.
- Read `src/gunray/arguments.py`, `disagreement.py`, `preference.py`.
- Read `tests/conftest.py` — `arguments_strategy`,
  `small_theory_strategy` exist.
- Scout section 5 theories (Tweety, Nixon, Opus) captured mentally.

## FILES (context)
- `src/gunray/arguments.py` — `Argument`, `is_subargument`,
  `build_arguments`, `_force_strict_for_closure`, `_fact_atoms`.
- `src/gunray/disagreement.py` — `disagrees`, `complement`,
  `strict_closure`.
- `src/gunray/preference.py` — `PreferenceCriterion`,
  `TrivialPreference`.
- `tests/conftest.py` — strategies already support B1.3 properties;
  need to add root-argument strategy for tree tests.

## KEY OBSERVATIONS
- `Argument.rules` is `frozenset[GroundDefeasibleRule]`; conclusion
  is `GroundAtom`.
- `is_subargument(a, b) = a.rules <= b.rules` — subset on rule sets.
- `disagrees(h1, h2, strict_context)` takes strict rules only
  (filters `kind=="strict"`). For dialectic we need the theory's
  strict rules; reach them via `parse_defeasible_theory` or pass
  them as a new parameter. The prompt says `build_tree` takes
  `theory: DefeasibleTheory`.
- The sub-arguments of `<A, h>` are all `<A', h'>` with
  `A' subset A`. Need to iterate over arguments produced by
  `build_arguments(theory)` and test `is_subargument(subarg, a2)`.
- Def 4.7 cond 2 concordance = union of rules in the set + Pi is
  non-contradictory. Will compute via `strict_closure` on
  `_fact_atoms` + strict rules + shadow-strict of defeasible rules.

## PLAN
1. Create empty `tests/test_dialectic.py` with import → red.
2. TDD `counter_argues` (tests 1 + 2) — make sure test 2 fails
   before descent is added, then add the sub-argument descent.
3. TDD `proper_defeater`, `blocking_defeater` (tests 3 + 4).
4. TDD `DialecticalNode` dataclass + `build_tree` stub.
5. TDD `build_tree` against Nixon (test 5), circular (8),
   reciprocal-blocking (9), contradictory supporting (10).
6. TDD `mark` (tests 6 + 7).
7. Property tests (11-17) — need helper in conftest to pick root
   argument from `build_arguments(theory)`, with `assume(...)` to
   skip empty-argument theories.
8. Run final `uv run pytest tests -q -k "not test_conformance"`
   and `uv run pyright src/gunray/dialectic.py`.
9. Write report `reports/b1-defeat-and-tree.md`.

## STUCK
Not stuck.

## PROGRESS 2026-04-13 (mid)
- Baseline ran: 66 passed, 3 skipped, 1 pre-existing
  `test_closure_faithfulness` fail (expected).
- d732455 — test(dialectic): counter_argues at root (red)
- 5a50458 — feat(dialectic): counter_argues at root + module stubs
  (green). Stubs for DialecticalNode / build_tree / proper_defeater
  / blocking_defeater raise NotImplementedError. `mark` is already
  implemented because it's tiny and pure.
- Added chain theory test for directional sub-argument attack.
  Currently red: root-only attack returns False on
  ⟨{r3}, ~q(a)⟩ vs ⟨{r1,r2}, r(a)⟩. About to green by iterating
  sub-arguments of target.

## NEXT
- Green test 2 by enumerating sub-arguments of `target` via
  `build_arguments(theory)` + `is_subargument`. Commit.
- Tests 3-10 (defeaters, tree, marking).
- Property tests 11-17 with new conftest helper.

## PROGRESS 2026-04-13 (later)
- e030503 — red: counter_argues descends into sub-arguments
- 722827c — green: directional fix (iterate sub-arguments + disagrees)
- 8bd29db — red: proper + blocking defeaters
- dcfcb43 — green: proper + blocking (helper `_disagreeing_subarguments`)
- ea82724 — red: Nixon Diamond tree shape
- Next: implement `build_tree` to satisfy Nixon case. Algo:
  recursive walk carrying the current line; for each candidate
  defeater, check Def 4.7 cond 2 (supporting/interfering
  concordance), cond 3 (no line member is sub-argument of earlier
  member), cond 4 (blocking-after-blocking terminates), admit if
  OK and recurse. Line is a list of (Argument, "proper"|"blocking").

## KEY DESIGN NOTES
- I made `proper_defeater`/`blocking_defeater` take `theory` as a
  parameter (the prompt wrote the signature without theory, but
  counter_argues NEEDS theory to resolve strict rules). I'll note
  this in the report surprises.
- `build_tree` needs theory's strict rules for concordance — same
  helper `_theory_strict_rules`.
- Concordance check: `strict_closure(_fact_atoms(facts) ∪ union_of_sets_heads, strict_rules_grounded + defeasible_shadowed)` has no complementary pair. Reuse `_force_strict_for_closure` from arguments.py.

## PROGRESS 2026-04-13 (latest)
- 370a62e — green build_tree (Def 4.7 cond 2-4)
- 7a9f147 — test(dialectic): mark Nixon and Tweety
- 0f98420 — test(dialectic): circular argumentation
- e46d7e7 — test(dialectic): reciprocal blocking cond 4
- fc5bef0 — test(dialectic): contradictory supporting line cond 2
- All 10 unit tests passing.
- Property tests 11-17 written in tests/test_dialectic.py.
- Added `theory_with_root_argument_strategy` in conftest.py.

## PROGRESS 2026-04-13 (final stretch)
- Fixed `tests.conftest` import → `from conftest import ...`
  (pattern used by other test files).
- Fixed Hypothesis precondition: theories with inconsistent Π
  (e.g. strict rule `~p :- p` + fact p) make `_concordant([])`
  False. Added `assume(_concordant([], theory))` to properties 16
  and 17. Garcia 04 p.8 assumes consistent Π anyway, so this is
  the right filter.
- All 17 dialectic tests pass in ~9 s.
- Full suite: 83 passed, 3 skipped, 1 pre-existing
  closure_faithfulness failure (unchanged).
- Pyright on dialectic.py: 0 errors after removing unused
  imports (`GroundAtom`, `_force_strict_for_closure`).
- Commits so far since B1.4 start:
  d732455 test red t1
  5a50458 green t1
  e030503 test red t2
  722827c green t2
  8bd29db test red t3+t4
  dcfcb43 green t3+t4
  ea82724 test red t5
  370a62e green t5 (build_tree)
  7a9f147 test t6+t7 (pre-green mark)
  0f98420 test t8
  e46d7e7 test t9
  fc5bef0 test t10
  de9bc71 test properties 11-17
  + pending commit for pyright cleanup

## STUCK
Not stuck.

## NEXT
- Commit pyright cleanup.
- Count LOC; gather gate metrics; write `reports/b1-defeat-and-tree.md`.
- Final assistant reply.
