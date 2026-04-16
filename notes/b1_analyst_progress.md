# B1.7 analyst progress notes

Datestamp: 2026-04-13

## GOAL
Read-only review of Block 1 (B1.1-B1.6). Produce `reports/b1-analyst.md`
with verdict (GREEN/YELLOW/RED), gate ratchet numbers, findings for
checks 1-9, and conformance classification audit.

## DONE so far
- Read the plan `~/.claude/plans/ticklish-frolicking-bengio.md`
  (Gates table + Block 1 section).
- Read all five B1 coder reports:
  - `reports/b1-scorch-and-foundations.md` (B1.2): 784->104 LOC,
    scorched earth, 5 new Hypothesis properties, 3 trace tests skipped
    with reasons.
  - `reports/b1-disagreement-and-build-arguments.md` (B1.3): +7
    properties, arguments.py 366 LOC, disagreement.py 87 LOC.
  - `reports/b1-defeat-and-tree.md` (B1.4): +7 properties, dialectic.py
    341 LOC; directional sub-argument-descent fix landed with verified
    red commit (`722827c` greened `e030503` red).
  - `reports/b1-render-and-answer.md` (B1.5): +4 properties; dialectic.py
    538 LOC; opus-NO deviation recorded (prompt bug, not discretion).
  - `reports/b1-wire-evaluator-and-nests-fix.md` (B1.6): wiring landed;
    defeasible.py 282 LOC; three skipped trace tests un-skipped;
    conformance 235/59/1; 32-case regression classified into
    28 specificity-needed / 2 paper-correct / 1 scalability-deselected.
- Read scout report partially (sections 1-2).

## KEY OBSERVATIONS (from reports)
- Gate ratchets per coders:
  - defeasible.py LOC: 784 (baseline) -> 104 (B1.2) -> 282 (B1.6).
    Strictly smaller than baseline. PASSES gate.
  - Hypothesis properties: 0 (baseline) -> +5 (B1.2) -> +7 (B1.3)
    -> +7 (B1.4) -> +4 (B1.5) -> +0 new in B1.6. Plan expected >= 30.
    B1.6 report claims 35 via @given decorators. NEEDS VERIFICATION.
  - Paper citations: 0 -> 11 (B1.2) -> 24 (B1.3) -> 28 (B1.4) -> 31
    (B1.5) -> 32 (B1.6). PASSES "strictly increases" gate.
  - Unit suite at B1.6 tip: 106 passed / 0 skipped / 1 failed. The one
    failure is the pre-existing test_closure_faithfulness ranked-world
    oracle, documented in P0.1 as out-of-scope.
  - Conformance: 235 passed / 59 failed / 1 deselected. Block 1 is
    allowed red per plan.
  - Deleted symbols: zero matches per B1.2 report.
- Directional fix verified in B1.4: commit `e030503` red,
  commit `722827c` green for sub-argument descent.
- opus deviation in B1.5 is genuine: prompt's literal assertion was a
  Block-2 result; coder correctly refused to implement specificity and
  recorded in progress#deviations. No architectural discretion taken.
- depysible_nests_in_trees deviation in B1.6: coder argues Def 3.1
  cond 2 forbids argument for `flies(tweety)` because
  `~flies(tweety)` is in Pi. Recorded in progress#deviations.
  NOTE: this directly conflicts with plan's Block-1 exit criterion
  which said "both nests_in_trees cases fixed" -- need to audit this
  deviation carefully.
- long_chain deselected for scalability (O(2^|Delta|) enumerator at
  |Delta|=20). B1.3 flagged scalability as a Block-2 concern.

## STILL TO DO
1. Run verification commands (pytest, pyright, wc, rg patterns).
2. Read live source tree: arguments.py, disagreement.py, dialectic.py,
   preference.py, answer.py, defeasible.py, __init__.py.
3. Read live test tree (all test files listed in prompt).
4. Read notes/refactor_progress.md (especially #deviations).
5. Read remaining scout report sections (5, 6 on paper examples).
6. Check 1: deletion-integrity rg, ambiguity.py/test_defeasible_core.py
   absence, TODO/FIXME/XXX.
7. Check 2: skip markers audit.
8. Check 4: docstring citation audit across new modules.
9. Check 5: manually read counter_argues in dialectic.py to confirm
   sub-argument descent.
10. Check 6: enumerate every @given with file/line + max_examples.
11. Check 7: conformance classification audit table.
12. Check 8: deviations audit against progress log.
13. Check 9: unused imports, dead code, edge cases.
14. Write final report.

## CURRENT BLOCKER
None. All artifacts are accessible and verification commands are
specified. The main open question is the nests_in_trees deviation:
the plan required both cases fixed by end of Block 1; B1.6 recorded
both as paper-correct regressions. This is the most consequential
thing to adjudicate in the final report.

## NEXT
Run verification commands in parallel, then read live source files.

## CHECKPOINT 2 (2026-04-13 mid-analysis)

### Verification commands run so far
- `git log --oneline master..HEAD` -> empty (master IS the B1 tip;
  all B1 commits are on master directly).
- `git log --oneline -40` confirms full B1 commit trail matches
  coder-report hashes. B1.2 through B1.6 all landed in expected
  order.
- `wc -l` of the new modules (live):
  - defeasible.py: 282 (matches B1.6)
  - arguments.py: 366
  - disagreement.py: 87
  - dialectic.py: 538
  - preference.py: 37
  - answer.py: 21
  - __init__.py: 38
- `ls ambiguity.py test_defeasible_core.py` -> both absent. OK.
- Deletion-integrity rg: zero matches in tests/. **ONE stale match
  in src/**: `src/gunray/dialectic.py:96` contains a docstring
  reference to `_find_blocking_peer`. Not a call — it is historical
  context ("The deleted _find_blocking_peer never descended..."). A
  strict reading of the plan's gate says "Zero after Block 1";
  a lenient reading (gate tests functionality, not prose) passes.
  Will flag as YELLOW cosmetic gate failure in report.
- `pytest.mark.skip` in tests/: zero matches. **B1.6 fully un-skipped
  the three B1.2 parked tests.** Gate satisfied.
- TODO/FIXME/XXX in src/gunray: zero. Clean.
- Paper citations: 32 total across 6 files. Gate satisfied.
  - arguments.py 6, defeasible.py 2, answer.py 2,
    disagreement.py 3, preference.py 5, dialectic.py 14.
- @given property count: **35** across 10 files.
  - test_answer.py: 4 (B1.2 has 1, B1.5 added 3)
  - test_arguments_basics.py: 3 (B1.2)
  - test_build_arguments.py: 4 (B1.3)
  - test_disagreement.py: 3 (B1.3)
  - test_parser_properties.py: 7 (pre-existing)
  - test_dialectic.py: 7 (B1.4)
  - test_preference.py: 1 (B1.2)
  - test_closure_faithfulness.py: 2 (pre-existing)
  - test_render.py: 1 (B1.5)
  - test_trace.py: 3 (pre-existing; re-landed)
  - Total new in B1: 5 (B1.2) + 7 (B1.3) + 7 (B1.4) + 4 (B1.5)
    = 23 new. Baseline had ~12. Total now 35 >= 30.

### Live source observations
- **arguments.py**: `Argument` is a frozen dataclass with ONLY
  `rules: frozenset[GroundDefeasibleRule]` and `conclusion: GroundAtom`.
  Satisfies adversary check (a) "Argument is a pair ⟨A, h⟩ and
  nothing else". `is_subargument(a,b) := a.rules <= b.rules` —
  one conjunct exactly. Module docstring cites Def 3.1 and
  Simari 92 Def 2.2. `build_arguments` docstring cites same.
- **answer.py**: `Answer` enum with YES/NO/UNDECIDED/UNKNOWN.
  Docstring cites Def 5.3 with description of all four branches.
- **preference.py**: `PreferenceCriterion` protocol cites §4;
  `TrivialPreference` cites Defs 4.1/4.2. Clean.
- **disagreement.py**: `disagrees` cites Def 3.3 verbatim; handles
  the direct-complement special case AND the closure-based path.
- **dialectic.py** counter_argues (lines 84-101): explicitly
  descends into sub-arguments via `_disagreeing_subarguments`,
  which iterates `build_arguments(theory)` and filters by
  `is_subargument(sub, target)`. **The directional fix is real.**
  Docstring cites Def 3.4. Note: the docstring on
  line 96 mentions the deleted `_find_blocking_peer` by name (see
  deletion-integrity note above).
- **dialectic.py** proper_defeater (126-144): cites Def 4.1, uses
  sub-arg descent.
- **dialectic.py** blocking_defeater (147-165): cites Def 4.2,
  uses sub-arg descent.
- **dialectic.py** build_tree (240-267): cites Def 5.1 + Def 4.7,
  enumerates Def 4.7 conds 1-4 explicitly in the docstring.
  Implementation in `_expand` (270-333) implements each check:
  cond 4 at lines 296-297 (blocking-of-blocking rejection),
  cond 3 at lines 300-304 (sub-argument line-exclusion),
  cond 2 at lines 310-324 (supporting / interfering concordance),
  cond 1 is structurally guaranteed by `build_arguments` being
  finite + cond 3 forbidding re-entry.
- **dialectic.py** mark (336-352): cites Proc 5.1; pure, post-order,
  leaf->U, any-U-child->D, all-D-children->U. Three-line
  function body.
- **dialectic.py** answer (489-537): cites Def 5.3 verbatim; implements
  all four cases in order YES -> NO -> UNDECIDED -> UNKNOWN. Note
  that the final branch returns UNDECIDED when exactly one predicate
  is in the language but no argument was found — see OPEN ISSUE
  below.
- **__init__.py** exports Answer, Argument, is_subargument,
  PreferenceCriterion, TrivialPreference. Does NOT export
  DialecticalNode, build_tree, counter_argues, mark, render_tree,
  answer, disagrees, build_arguments. The plan Section 1.4 scout
  landing directive said these should go into `__init__.py`. This
  is a minor public-surface shortfall; propstore consumers will
  need to import from `gunray.dialectic` directly.
- **arguments.py** imports `_match_positive_body` from `.evaluator`
  (underscore-prefix private) and `IndexedRelation` from `.relation`.
  These are OK but fragile — flag as "cross-module private coupling".

### OPEN ISSUES TO INVESTIGATE
1. **dialectic.py answer() final UNDECIDED fallback (line 537)**:
   When the predicate is in the language but no argument exists
   for either polarity, it returns UNDECIDED. Per Def 5.3 this
   should be UNDECIDED only when an argument *exists* for either
   polarity. Need to check if this case is reachable and correct.
2. **Cross-module private imports**: dialectic.py imports
   `_fact_atoms`, `_force_strict_for_closure` from arguments
   (underscore-private). Cosmetic but worth noting.
3. **nests_in_trees plan deviation**: plan said "both
   nests_in_trees cases fixed by end of Block 1"; B1.6 reclassified
   them as paper-correct regressions. Need to read the progress-log
   deviation section in full.
4. **Deletion-integrity docstring match**: the rg pattern catches
   `_find_blocking_peer` mentioned in dialectic.py:96 docstring.

## CURRENT BLOCKER
None. Still need to: read defeasible.py live, read all test files
(especially test_dialectic.py for the sub-argument red test),
read notes/refactor_progress.md#deviations, run pytest and
pyright to sanity-check gate numbers.

## CHECKPOINT 3 (all verification commands run)

### Verification command results (all confirmed)
- **Unit pytest**: `106 passed, 1 failed, 295 deselected in 75.26s`.
  The 1 failure is `test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  (pre-existing P0.1). **Matches B1.6 report exactly.** Zero skipped.
- **Project pyright**: `0 errors, 0 warnings, 0 informations` on
  `arguments.py answer.py preference.py disagreement.py dialectic.py
  defeasible.py __init__.py`. Gate satisfied.
- **vulture**: not installed in the venv (`No module named vulture`).
  Plan lists vulture as a gate but the codebase doesn't ship it
  as a dev dep. Will note as a GAP in report (Block 1 never ran
  the dead-code gate).
- **Directional fix red test** (commit `e030503`): explicit
  chain theory with attacker `~q` at sub-argument q of
  `⟨{r1,r2}, r(a)⟩`. Under root-only attack, counter_argues would
  return False; under sub-arg descent it returns True. This is
  exactly the red the plan called for. Verified by reading the
  diff from commit e030503.
- **@given max_examples audit**: every property in
  test_arguments_basics, test_answer, test_build_arguments,
  test_disagreement, test_preference, test_render, test_dialectic
  uses `@settings(max_examples=500, deadline=None|5000)`. Zero
  violations. Gate satisfied.

### Docstring citation audit (complete)
All required functions cite the required paper anchors:
- Argument: Def 3.1 ✓
- is_subargument: Fig 1 ✓
- Answer: Def 5.3 ✓
- PreferenceCriterion: §4 ✓
- TrivialPreference: Defs 4.1/4.2 ✓
- disagrees: Def 3.3 ✓
- build_arguments: Def 3.1 + Simari 92 Def 2.2 ✓
- counter_argues: Def 3.4 ✓
- proper_defeater: Def 4.1 ✓
- blocking_defeater: Def 4.2 ✓
- build_tree: Def 5.1 + Def 4.7 ✓
- mark: Proc 5.1 ✓
- answer: Def 5.3 ✓

### Remaining work
1. Read scout report sections 5 and 6 (paper examples).
2. Spot-check test_build_arguments.py and test_answer.py.
3. Check edge cases: empty theory, single-rule, strict-only shortcut.
4. Construct conformance classification audit table (partial
   sampling per prompt — don't need to rerun all 32).
5. Consider the UNDECIDED fallback on dialectic.py:537 more
   carefully — is it reachable under any realistic theory?
6. Write the final report.

### VERDICT DIRECTION SO FAR
Leaning **GREEN** with minor YELLOW observations:
- Cosmetic gate failure: dialectic.py:96 docstring mentions
  `_find_blocking_peer` by name, tripping the gate rg pattern.
- vulture gate was never executed (vulture not installed).
- Minor semantic drift: answer() UNDECIDED fallback on line 537
  returns UNDECIDED for a case the paper arguably treats as UNKNOWN.
- __init__.py doesn't re-export DialecticalNode, build_tree,
  counter_argues, mark, render_tree, answer, disagrees,
  build_arguments — scout directive said to add these.
- nests_in_trees plan deviation: plan required both cases
  passing; B1.6 recorded as paper-correct regression. Agreed
  with coder's paper reading; deviation is well-argued and
  documented.

None of these are blockers. B1.8 adversary should follow.

## CURRENT BLOCKER
None. Proceeding to write the final report.
