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
