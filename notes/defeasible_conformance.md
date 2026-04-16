# Defeasible Conformance Failures - 2026-04-11

## Setup
- Correct evaluator: `gunray.defeasible.DefeasibleEvaluator` (NOT `SemiNaiveEvaluator`)
- Run: `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.defeasible.DefeasibleEvaluator --datalog-tags=defeasible --timeout=120`
- Result: 173 passed, 3 failed

## Failures (3, not 7)

### Failure 1 & 2: depysible_nests_in_trees_tina, depysible_nests_in_trees_tweety
- Error: `missing section 'undecided'`
- Expected: `undecided: {nests_in_trees: [[tweety]]}` (for both - note: tina test also expects tweety!)
- The evaluator doesn't produce an `undecided` section for these atoms
- Root cause: nests_in_trees(tweety) depends on flies(tweety), which is blocked by strict ~flies. But nests_in_trees(tweety) is supported by a chain through the defeasible flies(X) :- bird(X). The evaluator classifies it as `not_defeasibly` rather than `undecided`.

### Failure 3: maher_example3_freddie_nonflight
- Error: `section 'definitely' predicate 'bird': expected [('freddie',)], got [('freddie',), ('tweety',)]`
- Expected: only freddie in `definitely.bird`
- Actual: both freddie AND tweety in `definitely.bird`
- Root cause: tweety is a penguin fact, and there's a strict rule bird(X) :- penguin(X). The evaluator derives bird(tweety) via strict rule and puts it in `definitely`. But the test expects `definitely.bird` to only contain freddie.
- Wait - the test ONLY checks the predicates it mentions. The assertion iterates over `expected.items()` and checks each predicate. So `expected.definitely.bird = [('freddie',)]` but `actual.definitely.bird = {('freddie',), ('tweety',)}`. The test expects freddie-only but evaluator derives both.
- The test YAML only lists freddie as a bird fact, but tweety is a penguin, and r3 strict rule derives bird(tweety). So the evaluator IS correct to derive bird(tweety) definitely. The test expectation seems to be about query scoping (only asking about freddie).
- Actually re-reading: the test expects `definitely.bird: [[freddie]]` meaning ONLY freddie. But bird(tweety) is definitely derived via strict r3. So either the test is wrong, or the evaluator should be filtering by query scope.

## Key question
The `expect` dict in tests is a SUBSET check or EXACT match? Looking at runner.py line 154: `if expected_set != actual_set` - it's an EXACT match per mentioned predicate. So when the test says `definitely.bird: [[freddie]]`, it means exactly that set - no tweety allowed.

This means the maher_example3 test expects that bird(tweety) should NOT be in the definitely section. But tweety IS a penguin, and r3 strictly derives bird from penguin. Unless... the test expects query-scoped output, not full model. Or the defeasible semantics only puts things in `definitely` that are relevant to the query.

## Updated findings (after full trace)

Correct evaluator path: `gunray.adapter.GunrayEvaluator` (dispatches to DefeasibleEvaluator for theories).
maher_example3 was fixed by correcting the YAML expectations (test was wrong, not evaluator).

### Remaining: 2 failures, both nests_in_trees undecided classification

Both `depysible_nests_in_trees_tina` and `depysible_nests_in_trees_tweety` expect:
  `undecided: {nests_in_trees: [[tweety]]}`
But evaluator returns no `undecided` section.

### Root cause analysis for nests_in_trees(tweety)

Theory: tweety is a penguin. Strict rule derives ~flies(tweety). Defeasible rule r4 derives flies(tweety) from bird(tweety). r7 derives nests_in_trees(X) from flies(X).

In the proof loop: nests_in_trees(tweety) depends on flies(tweety) being proven. flies(tweety) can never be proven because ~flies(tweety) is definitely true (strict rule). So nests_in_trees(tweety) is NOT proven. Correct so far.

Post-proof classification (lines 85-116):
1. Find support_rules for nests_in_trees(tweety): [r7 grounded: body=(flies(tweety),)]
2. Filter to `supported_rules` via `_attacker_body_available(rule, supported, definitely)` — this checks if rule body is available in `supported` (positive closure). flies(tweety) IS in supported (positive closure derives it ignoring conflicts). So supported_rules is non-empty.
3. Then calls `_has_blocking_peer()` to decide undecided vs not_defeasibly.

`_has_blocking_peer` for nests_in_trees(tweety):
- Looks for opposing atoms: ~nests_in_trees(tweety) (via conflict pairs)
- Checks rules_by_head for ~nests_in_trees(tweety) — there are NO rules deriving ~nests_in_trees
- So the inner loop over attackers finds nothing
- Returns False → atom goes to `not_defeasibly` instead of `undecided`

### The bug
`_has_blocking_peer` only looks for direct conflicts on nests_in_trees — but the actual blocking happens UPSTREAM on flies(tweety). nests_in_trees(tweety) is undecided not because of a direct conflict on nests_in_trees, but because its prerequisite (flies(tweety)) is itself blocked/undecided.

The evaluator doesn't propagate undecidedness through dependency chains. An atom whose body depends on an unproven-but-supported atom should be undecided if the body atom is undecided or blocked. Currently it only checks for direct conflicts on the atom itself.

### This is ONE bug, not multiple
Both nests_in_trees test cases fail for the same reason: upstream undecidedness doesn't propagate through defeasible rule chains.
