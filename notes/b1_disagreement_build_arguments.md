# B1.3 — disagreement + build_arguments

## GOAL
Create `src/gunray/disagreement.py` (strict_closure, complement, disagrees per
Garcia 04 Def 3.3). Extend `src/gunray/arguments.py` with `build_arguments`
per Garcia 04 Def 3.1 / Simari 92 Def 2.2. Strict TDD, 3+3 disagreement tests,
5+4 argument tests.

## 2026-04-13 checkpoint — context gathered, no code yet

### DONE
- Read prompt `prompts/b1-disagreement-and-build-arguments.md` (full).
- Read scout report sections 3, 4, 5 (closure API, grounding, paper examples).
- Read current `src/gunray/arguments.py`, `types.py`, `__init__.py`.
- Read `tests/conftest.py` and `tests/test_arguments_basics.py` (pattern: they
  import from `conftest` by name, so we can extend it).
- Checked `_match_positive_body` lives in `src/gunray/evaluator.py:318`.

### FILES
- `src/gunray/arguments.py` — B1.2 landed `Argument(rules, conclusion)` +
  `is_subargument`. Do NOT change Argument itself; add `build_arguments`.
- `src/gunray/types.py` — `GroundAtom(predicate, arguments)`,
  `GroundDefeasibleRule(rule_id, kind, head, body)`. Strong-negation is a
  `~` prefix on the predicate string (e.g. `~flies`).
- `src/gunray/parser.py` — `parse_defeasible_theory` returns
  `(facts_dict, list[DefeasibleRule], conflicts_set)`. `ground_atom`,
  `parse_atom_text`, `_complement` all here.
- `src/gunray/evaluator.py:318` — `_match_positive_body(atoms, model)`.
- `src/gunray/relation.py` — `IndexedRelation`.
- `src/gunray/closure.py` — **cannot reuse** for ground atoms
  (propositional-only). Recreate `strict_closure` from scout 3.4 body.

### KEY CONTRACTS
- `disagrees(h1, h2, K)`: closure of `{h1,h2}` under K contains complementary
  pair. Complementary = same predicate with/without `~` prefix.
- `build_arguments(theory)`: naive 2^|Δ| subset enumeration. Skip defeater-kind
  rules for head candidates (filter per prompt). Strict-only conclusions get
  `Argument(frozenset(), h)`.
- Test files: `tests/test_disagreement.py`, `tests/test_build_arguments.py`.
- Extend `tests/conftest.py` with ground-atom and theory Hypothesis strategies.

### PAPER EXAMPLES (from scout §5)
- Tweety: facts `bird(tweety), bird(opus), penguin(opus)`, strict
  `bird(X):-penguin(X)`, defeasible `r1: flies(X):-bird(X)`,
  `r2: ~flies(X):-penguin(X)`.
- Nixon (direct form): facts `republican(nixon), quaker(nixon)`, no strict,
  `r1:~pacifist(X):-republican(X)`, `r2:pacifist(X):-quaker(X)`.
- Opus subtheory: same as Tweety minus the `bird(tweety)` fact (one-element).

### TDD PLAN (next)
1. conftest: add `ground_atom_strategy`, `strict_rule_tuple_strategy`,
   `small_theory_strategy`.
2. Write `tests/test_disagreement.py`: 3 unit + 3 property tests, one at a
   time, red then green.
3. Write `tests/test_build_arguments.py`: 5 unit + 4 property tests, one at
   a time, red then green.

### NO BLOCKER
Moving to red phase of test 1 (disagrees on complementary literals).

## 2026-04-13 checkpoint 2 — disagreement unit tests 1-3 landed

### DONE (this checkpoint)
- Test 1 (complementary literals): red → green. Commits a4b9815 + 48fd98b.
  Wrote full `src/gunray/disagreement.py` (complement, strict_closure,
  disagrees) as minimal green — turned out to handle all 3 cases.
- Test 2 (unrelated literals): passed immediately. Commit 75d504e as
  regression guard.
- Test 3 (strict-rule disagreement via Opus bird/penguin): passed
  immediately via strict_closure forward-chaining. Needs commit.
- Baseline test suite: 51 passed, 1 pre-existing unrelated
  test_closure_faithfulness failure (ranked-closure reference oracle,
  not touched by this dispatch).

### OBSERVATIONS
- disagreement.py is ~87 LOC; passes pyright in-process (not yet
  run explicitly).
- `strict_closure` ignores non-strict rules by kind — makes it safe
  to pass a heterogeneous context tuple from build_arguments.

### NEXT
- Commit test 3 (green-on-first-run is the same pattern as test 2).
- Extend tests/conftest.py with ground_atom_strategy and strict_rule
  context strategy.
- Write 3 Hypothesis properties: symmetry, monotonicity in context,
  irreflexivity on satisfiable context.
- Then move to build_arguments tests.

### NO BLOCKER

## 2026-04-13 checkpoint 3 — all disagreement tests landed

### DONE (this checkpoint)
- conftest.py: added `ground_atom_strategy`, `strict_rule_strategy`,
  `strict_context_strategy`, `small_theory_strategy`.
- Hypothesis property 1: symmetry. Commit ba88e98. 500 examples pass.
- Hypothesis property 2: monotonicity in context. Commit d5bf4c3.
  500 examples pass.
- Hypothesis property 3: irreflexive on satisfiable context. Uses
  `assume` to reject pre-contradictory contexts. 500 examples pass
  (needs commit).

### RUNNING TOTALS
- disagreement unit tests: 3/3 (done).
- disagreement hypothesis properties: 3/3 (ready to commit last).
- build_arguments unit tests: 0/5.
- build_arguments hypothesis properties: 0/4.

### NEXT
- Commit irreflexivity property.
- Create tests/test_build_arguments.py, unit test 1: Tweety argument exists.
  This requires implementing `build_arguments` minimally.
- Grounding plan: parse_defeasible_theory -> ground rules via
  `_match_positive_body` seeded by the positive fact model.

## 2026-04-13 checkpoint 4 — build_arguments up through test 2

### DONE (this checkpoint)
- Committed a3bbc69 for disagreement irreflexivity property.
- Wrote `tests/test_build_arguments.py` with `_tweety_theory` helper.
- Test 1 (tweety flies argument exists): red → green. Commits
  1b7597d + 3e87048.
- Implemented `build_arguments` in src/gunray/arguments.py (327 new
  lines). Approach:
  - parse_defeasible_theory → (facts, rules, conflicts)
  - Rebuilt positive_closure over all rule bodies to ground bindings.
  - Ground strict, defeasible, defeater rules via `_match_positive_body`.
  - Pi closure = fact atoms under ground strict rules.
  - Each atom in Pi closure → Argument(frozenset(), h).
  - For each subset A of grounded defeasible rules, compute closure
    under ground strict + A (shadowed to kind="strict" via
    `_force_strict_for_closure`); skip if contradictory; record
    minimal A for each head rule.head.
  - Minimality tracked via per-head list of survivor subsets with
    subset pruning.
- Test 2 (opus ~flies argument exists): passed on first run.

### OBSERVATIONS
- The positive_closure helper is needed because `_match_positive_body`
  needs a model dict to find bindings. I use it *only* for grounding —
  not for derivation, so the "positive-only, ignores negation" aspect
  is fine.
- Defeaters land through grounding but are kept separate and excluded
  from subset enumeration. The filter for defeater heads is
  conservative but correct.

### FILE STATE
- src/gunray/disagreement.py: ~87 LOC.
- src/gunray/arguments.py: ~370 LOC (grown from ~42).
- tests/test_disagreement.py: 6 tests (3 unit + 3 property, all pass).
- tests/test_build_arguments.py: 2 tests so far.
- tests/conftest.py: extended with 4 strategies.

## 2026-04-13 checkpoint 5 — build_arguments all unit tests + first property

### DONE (this checkpoint)
- Test 3 (nixon diamond both arguments): green on first run. Commit a83ad9d.
- Test 4 (defeater kind cannot conclude): green on first run. Commit db1b7aa.
- Test 5 (strict-only arguments empty rules): green on first run. Commit da59c3b.
- Hypothesis property 1 (build_arguments deterministic): 500 examples pass.
  Needs commit.

### RUNNING TOTALS
- disagreement unit: 3/3 done.
- disagreement hypothesis: 3/3 done.
- build_arguments unit: 5/5 done.
- build_arguments hypothesis: 1/4 done.
- Remaining: minimality property, non-contradiction property,
  monotonic-in-facts property. Then pyright + final suite.

### NEXT
- Commit determinism property.
- Add minimality property.
- Add non-contradiction property.
- Add monotonic-in-facts property.
- Run full suite + pyright.
- Write report.

## 2026-04-13 checkpoint 6 — all tests green; 3 pyright errors to fix

### DONE
- All 4 build_arguments hypothesis properties landed and committed:
  - determinism (commit beb025c)
  - minimality (commit c0c95f8)
  - non-contradiction (commit 9896cae)
  - monotonicity in facts (commit 653111c)
- Full non-conformance suite: 66 passed, 3 skipped, 1 pre-existing
  failure in test_closure_faithfulness (ranked-closure oracle,
  pre-existing, NOT my regression — same failure was present in the
  baseline I ran at the start).

### PYRIGHT STATUS (3 errors, 0 warnings — need to fix)
All three in src/gunray/arguments.py and all stem from the same root:
`normalize_facts` returns `dict[str, set[tuple[Scalar, ...]]]` but my
helper signatures use `dict[str, set[tuple[object, ...]]]`. Need to
either:
  - Change helper signatures to accept `dict[str, set[tuple[Scalar, ...]]]`,
  - Or use `Mapping[str, set[tuple[Scalar, ...]]]` per pyright's hint.
Plus one error at line 237 where I construct GroundAtom.arguments with
a tuple[object, ...] — IndexedRelation stores rows as tuple[object, ...];
need a cast to tuple[Scalar, ...].

### BLOCKER
Pyright must be green before finishing. 3 errors, all type-annotation
alignment — fixable without rewriting logic. Will also re-check the
full suite after the fix.

### NEXT
- Fix 3 pyright errors.
- Re-run pyright → expect 0/0.
- Re-run full suite → expect 66+ pass.
- Count file LOCs and citations.
- Write reports/b1-disagreement-and-build-arguments.md.

## 2026-04-13 checkpoint 7 — gates met, ready to write report

### DONE (this checkpoint)
- Pyright errors fixed in commit ea98837 (swapped to Mapping[...]
  with Scalar, removed unused `cast` import).
- Pyright now reports 0 errors, 0 warnings on both new files.
- Full suite (excluding pre-existing closure faithfulness and
  conformance): 64 passed, 3 skipped.
- Final soak of B1.3 tests: 15/15 (6 disagreement + 9
  build_arguments) at Hypothesis max_examples=500.

### FINAL METRICS
- src/gunray/disagreement.py: 87 LOC
- src/gunray/arguments.py: 366 LOC
- tests/test_disagreement.py: 102 LOC
- tests/test_build_arguments.py: 316 LOC
- tests/conftest.py: 144 LOC (was 46; +98)
- Paper citations in src/gunray/: 24 Garcia/Simari occurrences,
  up from 11 in B1.2 (+13).

### COMMIT TRAIL (17 commits)
See `git log --oneline a4b9815..ea98837`.

### REPORT TODO
Write reports/b1-disagreement-and-build-arguments.md with commit
hashes, LOC, metrics, property summaries, and one-line summary.
