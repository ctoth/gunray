# B1.6 — Wire DefeasibleEvaluator + port trace tests

## GOAL
Wire `DefeasibleEvaluator.evaluate_with_trace` to the paper pipeline
(`build_arguments` -> `build_tree` -> `mark` -> four-section projection),
keep strict-only shortcut intact, un-skip three trace tests, run full
conformance, classify failures.

## DONE (2026-04-13)
- Read prompt `prompts/b1-wire-evaluator-and-nests-fix.md` end-to-end
- Restated to Q, got confirmation
- Read all five Block 1 reports (scout/scorch/disagreement/defeat/render)
- Read current `src/gunray/defeasible.py` (105 LOC, raises NotImplementedError on defeasible path)
- Read `tests/test_trace.py` (3 skipped tests at lines 71, 111, 152)
- Read `src/gunray/arguments.py` (build_arguments fully landed in B1.3)
- Have full mental model of Argument shape, section projection rules, trace shape

## FILES (and why)
- `src/gunray/defeasible.py` — target, replace NotImplementedError branch
- `tests/test_trace.py` — un-skip 3 tests, re-write against new trace shape
- `tests/test_defeasible_evaluator.py` — NEW, sections projection unit tests
- `src/gunray/arguments.py` — `build_arguments`, `Argument` (read-only)
- `src/gunray/dialectic.py` — `build_tree`, `mark`, `answer`, `DialecticalNode` (need to read)
- `src/gunray/disagreement.py` — `complement` helper
- `src/gunray/preference.py` — `TrivialPreference`
- `src/gunray/trace.py` — DefeasibleTrace shape (need to read fully)
- `reports/b1-wire-evaluator-and-nests-fix.md` — final report

## Key facts observed
- `Argument(rules=frozenset(), conclusion=h)` ⇒ strict (definitely)
- `DefeasibleTrace` has fields: config, definitely, supported, strict_trace, proof_attempts, classifications
- `ProofAttemptTrace`: atom, result, reason, supporter_rule_ids, attacker_rule_ids, opposing_atoms
- `ClassificationTrace`: same shape
- The three skipped tests reference `trace.proof_attempts_for(atom, result=...)` and `trace.classifications_for(...)` helpers — need to verify if these exist on DefeasibleTrace today
- `DefeasibleModel.sections` four keys: definitely / defeasibly / not_defeasibly / undecided
- Section projection rules (verbatim from prompt):
  - strict = ∃⟨∅,h⟩
  - yes = ∃⟨A,h⟩ marked U
  - no = ∃⟨A,complement(h)⟩ marked U
  - definitely iff strict
  - defeasibly iff yes OR strict
  - not_defeasibly iff no AND NOT strict
  - undecided iff (NOT yes AND NOT no AND NOT strict) AND (some arg for h or complement(h))
  - UNKNOWN: predicate not in language ⇒ omitted from all sections

## STUCK
Not stuck. Reconnaissance complete on every source I need.

## Confirmed signatures and import shapes
- `Argument(rules: frozenset[GroundDefeasibleRule], conclusion: GroundAtom)` — frozen dataclass
- `build_arguments(theory) -> frozenset[Argument]`
- `build_tree(root, criterion, theory) -> DialecticalNode`
- `mark(node) -> Literal["U", "D"]`
- `answer(theory, literal, criterion) -> Answer`
- `complement(atom) -> GroundAtom` from `disagreement.py`
- `TrivialPreference()` from `preference.py`
- `_theory_predicates(theory)` is a private helper in `dialectic.py` — strips ~ prefix
- DefeasibleTrace HAS `proof_attempts_for(atom, *, result, reason)` and `classifications_for(...)` helpers ALREADY (they survived scorched earth). Good news for trace test re-land.

## CRITICAL: Circular import hazard
`src/gunray/dialectic.py` line 50 imports `from .defeasible import _atom_sort_key`. So `defeasible.py` cannot do top-level `from .dialectic import ...`. Must use lazy in-function imports.

## Tweety theory expected sections (per prompt, double-checked)
- definitely: bird(tweety), bird(opus), penguin(opus) — all strict-derivable. bird(opus) is ALSO strict via s1: bird(X) :- penguin(X), and penguin(opus) is a fact. bird(tweety) is a fact.
- defeasibly: same as above plus flies(tweety) (no counter-argument)
- undecided: flies(opus) and ~flies(opus) (mutual blocking under TrivialPreference, both trees mark D)
- not_defeasibly: nothing (no warranted complement-only case in this theory under TrivialPreference)

## Nixon theory (test_trace.py existing skipped test uses)
Indirect form: facts={nixonian(nixon), quaker(nixon)}, rules r1: republican(X) :- nixonian(X), r2: pacifist(X) :- quaker(X), r3: ~pacifist(X) :- republican(X)
- pacifist(nixon) and ~pacifist(nixon) → undecided (mutual block under TrivialPreference)

## nests_in_trees test
penguin(tweety) fact, strict r1: bird :- penguin, r2: ~flies :- penguin. defeasible r3: flies :- bird, r4: nests_in_trees :- flies.
Argument for nests_in_trees(tweety) = {r3, r4} (via flies(tweety), via bird(tweety) via penguin(tweety)).
Counter: ~flies(tweety) is STRICT from penguin(tweety). Strict argument <empty, ~flies(tweety)>.
counter_argues: attacker root conclusion ~flies(tweety) disagrees with sub-argument flies(tweety) of the nests target. So <{}, ~flies(tweety)> defeats <{r3,r4}, nests_in_trees(tweety)>. Tree: <{r3,r4},nests>; child <{},~flies>. The strict child is a leaf marks U → root marks D → not warranted.
For complement ~nests_in_trees(tweety): no rule produces it, no argument exists. So neither side warranted, but at least one argument exists for nests_in_trees → UNDECIDED.

## DONE since last checkpoint
- Read dialectic.py (538 LOC), trace.py (DefeasibleTrace + helpers), disagreement.py, preference.py, __init__.py, conftest.py, test_answer.py, adapter.py
- Confirmed `wc -l defeasible.py` = 104 (matches scorch baseline)
- Unit baseline DONE: 99 passed / 3 skipped / 1 failed (pre-existing closure_faithfulness)
- Conformance baseline still running in bg id `bayhh8zp0`
- Wrote tests/test_defeasible_evaluator.py (4 tests), verified RED (3 NotImplementedError + 1 strict-only pass)
- Committed RED: `3cf8804 test(defeasible): sections projection for Tweety, Nixon, missing body (red)`
- Wired src/gunray/defeasible.py with paper pipeline (build_arguments + build_tree + mark + section projection). Used lazy in-function imports to break circular dep with dialectic.py
- Verified GREEN: all 4 sections projection tests PASS

## Wiring details
- `_evaluate_via_argument_pipeline` is the new function
- Uses lazy import of `arguments`, `dialectic`, `disagreement`, `preference` inside the function body
- Section projection rules implemented verbatim per prompt:
  - strict = ∃⟨∅, h⟩
  - yes = ∃⟨A, h⟩ marked U (computed once per atom into `warranted` set)
  - no = ∃⟨A, complement(h)⟩ marked U
  - definitely iff strict
  - defeasibly iff yes OR strict
  - not_defeasibly iff no AND NOT strict
  - undecided iff none of the above AND argument exists for atom or complement
  - UNKNOWN: predicate not in language → omitted from all sections
- Trace: populates `definitely`, `supported` (definitely + defeasibly), `classifications` (one per classified atom), `proof_attempts` (one per blocked/undecided atom with reason `equal_strength_peer_conflict`)
- `_supporter_rule_ids(atom, arguments)` collects sorted rule_id list for trace introspection

## NEXT (immediately after this notes update)
1. Record the nests_in_trees deviation in notes/refactor_progress.md#deviations
2. Re-land trace test 1 (Nixon undecided) — should pass cleanly
3. Re-land trace test 2 (Nixon helpers) — verify supporter_rule_ids etc match
4. Re-land trace test 3 (nests_in_trees tweety) — REWRITE: assert that the literal is OMITTED from defeasibly (not in undecided either), document the deviation in test docstring
5. Wait for conformance baseline; run conformance on new code
6. Classify failures (expected: depysible_nests_in_trees_tweety/tina go from passing to undecided-but-without-nests OR fail on schema)
7. Write report

## CRITICAL FINDING (the nests_in_trees deviation)
- The third skipped trace test asserts `model.sections["undecided"]["nests_in_trees"] == {("tweety",)}`
- Theory: penguin(tweety) fact + STRICT rules `bird:-penguin` and `~flies:-penguin`. The strict closure of Π already contains ~flies(tweety).
- Per Garcia 04 Def 3.1 cond 2, NO defeasible argument for flies(tweety) can exist (the closure of Π+{r3} contains both flies and ~flies). Therefore no argument for nests_in_trees(tweety) exists either.
- Per the prompt's projection rules, atoms with no argument and no warranted complement and no strict derivation are OMITTED from every section.
- The depysible-style "supported_only_by_unproved_bodies" classification is NOT a Garcia 04 Def 5.3 result — it was a pre-paper invention in the deleted classifier.
- P0.1.5 notes report depysible_nests_in_trees_(tina,tweety,henrietta) all PASSED on master before B1 refactor. The paper-correct pipeline cannot reproduce this.
- This is a known divergence, not a fixable bug under the paper. I will:
  1. Record as deviation in notes/refactor_progress.md#deviations
  2. Re-land test #3 with paper-correct semantic invariant: "literal omitted from defeasibly when its body is contradicted by Π"
  3. Classify the conformance fixture failures as `real-regression` for the wire-up report (with paper-justified reasoning)

## DONE in this stretch
- Wrote test file, verified RED, committed RED `3cf8804`
- Wrote wired defeasible.py implementation, committed GREEN `5c38f62`
- All 4 unit tests pass
- Full unit suite: 103 passed / 3 skipped / 1 failed (only pre-existing closure_faithfulness)
- Investigated nests_in_trees: discovered Def 3.1 cond 2 rejection
- Investigated depysible_nests_in_trees_tina variant: works (no penguin/strict-flies conflict)
- Conformance baseline (POST-WIRE) finished but truncated output (only saw 49 of 92 failures via tail)
- Re-run conformance in bg id `bf20ni1e7` with full output, NOT YET COMPLETE
- Inspected Nixon trace output: classifications and proof_attempts populated correctly
  - pacifist(nixon): result=undecided, supporter_rule_ids=('r2',), attacker_rule_ids=('r1','r3'), opposing=(~pacifist(nixon),)
  - The original test 2 expected attacker=('r3',) — that was WRONG, the correct attacker chain is (r1, r3) since both are needed
- Started un-skipping test 1 (Nixon undecided trace) — removed @pytest.mark.skip and added new docstring

## Conformance baseline divergence (CONCERN)
- Documented baseline (P0.1.5): 267 passed / 28 failed
- Actual baseline (POST-WIRE, truncated): 92 failed / 203 passed
- Gap: 64 more failures than P0.1.5 documented
- Truncated tail shows: 14 strict_only_negation_nemo + 14 negation/nemo + spindle_racket_* + maher_*
- Need full output to enumerate all 92 and classify
- Full output run is bg id `bf20ni1e7`

## CRITICAL: Conformance I'm seeing IS post-wire
The baseline I tried to run was AFTER my green commit. So 92 failed is the post-wire number. The pre-wire baseline (before B1.6) had only the strict-only path landing through the new pipeline; the defeasible path raised NotImplementedError which would convert most defeasible cases to errors. So the documented 267/28 baseline was when DefeasibleEvaluator HAD the working classifier (P0.1.5 pre-scorch). I missed that in my reading of the prompt.

The numbers will be:
- pre-B1.2 scorch: 267/28
- post-B1.2 scorch: most defeasible cases ERROR (NotImplementedError) — much worse
- post-B1.6 wire: SOME come back; spindle_racket and maher and nests_in_trees may not

## NEXT
1. Refactor _supporter_rule_ids to take typed Argument param to satisfy pyright
2. Wait for bg `bvyjo530m` conformance run with full output
3. Classify every conformance failure (nemo_negation / specificity / build_arguments-scalability / paper-correct-divergence)
4. Run full unit suite for regression check
5. Write final report
6. Commit pyright fix + final docs commit

## DONE in this stretch (lots)
- Inspected Nixon trace output: shows correct (r1, r3) attacker chain
- Re-landed test 1 (Nixon undecided): un-skipped, removed marker, added new docstring
- Re-landed test 2 (helpers): updated attacker_rule_ids assertion ('r3',) → ('r1', 'r3')
- Re-landed test 3 (nests_in_trees): rewritten with paper-correct invariant: literal omitted from defeasibly/definitely/not_defeasibly + classification not present
- Removed unused `import pytest` from test_trace.py
- All 9 trace tests pass, ZERO @pytest.mark.skip remaining
- Committed trace re-lands as `f2c4935`
- Recorded full B1.6 deviation in notes/refactor_progress.md#deviations explaining Def 3.1 cond 2 rejection
- Conformance bg `bf20ni1e7` HUNG/timed out on spindle_racket_query_long_chain (20-rule chain → 2^20 build_arguments enumeration → cubic recursive call from build_tree)
- Started new conformance bg `bvyjo530m` with `--tb=no -rfE` for full failure listing
- Pyright on defeasible.py: 5 errors (Argument unused; getattr fallbacks lose type info)
- defeasible.py LOC = 276 (was 104, +172)

## Identified failure categories
1. nemo_negation safety errors: 28 cases (pre-existing)
2. spindle_racket_*: 20+ cases — likely all combinatorial scaling in build_arguments (long_chain has 20 defeasible rules → 2^20 subsets)
3. maher_*: 2 cases — likely specificity needed
4. depysible_nests_in_trees_*: 3 cases — paper-correct divergence
5. ?: ~40 more failures hidden in truncated tail

## STUCK
Slightly stuck on: build_arguments scalability hangs the conformance suite hard. The B1.3 report explicitly flagged O(2^|Δ|) as a Block 2 concern. The wire-up itself is correct; the underlying primitive is too slow for big fixtures. Will document as `real-regression-build-arguments-scalability` in the report — NOT a B1.6 wiring bug.

## Conformance run history
- Run 1 `bayhh8zp0` `2>&1 | tail -50`: COMPLETED 471s, summary `92 failed, 203 passed`, tail truncated to 49 visible failures
- Runs 2-4: ALL HUNG on spindle_racket_query_long_chain (long_chain is the only fixture with 20 defeasible rules; build_arguments enumerates 2^20 = 1M subsets, then build_tree recursively re-calls build_arguments per candidate)
- Categorized run 1 visible failures:
  - 14 negation/nemo_negation
  - 14 defeasible/strict_only/strict_only_negation_nemo_negation (28 nemo_negation total = matches P0.1.5 baseline)
  - 13 defeasible/basic/spindle_racket_test_theories (specificity-needed under TrivialPreference)
  - 5 defeasible/basic/spindle_racket_query_tests
  - 1 maher_example3_freddie_nonflight
  - 1 maher_example2_tweety
  - 1 spindle_racket_query_integration
- Total visible: 49; remaining 43 from total 92 are hidden in middle of truncated output
- Run 5 `btjb5pn7t` --deselect long_chain: NOW RUNNING

## Why run 1 succeeded but runs 2+ hang
Run 1 was BEFORE my green commit. defeasible.py raised NotImplementedError on every defeasible case → fast failure. After the wire-up, the same cases now run the real pipeline, and long_chain hangs hard.

## Identified problematic case
Only ONE: `spindle_racket_query_long_chain` (20 defeasible rules, no strict, simple chain L0→L1→...→L20). build_arguments would enumerate 2^20 = 1,048,576 subsets just for this theory. This is a known B1.3 scalability limit explicitly flagged as a B2 concern.

## Plan for full classification
1. Wait for run 5 (deselect long_chain) to complete — currently stuck around 53% on something
2. Read full failure list from notes/conformance_full.log
3. Classify each: nemo_negation / specificity-needed / build_arguments-scalability (long_chain) / paper-correct-divergence (nests_in_trees) / real-regression-other
4. Write report
5. Commit final docs commit

## Run 5 stuck somewhere around 53%
Pattern: `..........................FF..FF.FF...FFF.F...` (15%) `....F..F..FF....FF.F..F.F.F....FFF.FFF..F...F.F.........................` (40%) `....FFFFFFFFFFFFFF.....................................` (some sub 53%)
- 26 + 47 = 73 chars in line 1+2
- 13 + 4 + 14 + 37 = 68 chars approx in line 3
- Position ~141 of 294 = ~48% by char count
- 14 consecutive F's in a row early in line 3 — that's spindle_racket_test_theories failing
- Then 4 dots, 14 F's again (same fixture or another), then dots
- The hang must be on a fixture between 50-55%

## My next move if hang doesn't clear
1. Kill the run and add more --deselect targets (may need to enumerate more pathological fixtures)
2. OR use the partial output to extract everything I can and classify what I have
3. The 49 visible failures from run 1 + the partial output from run 5 should give enough categorization
4. Worst case: report partial conformance numbers ("X passed, Y failed of 294 attempted, +1 long_chain deselected as combinatorial-explosion")

## STATE: just killed run 5
- Run 5 hung at 611 bytes after 30s wait. Pytest stuck inside build_arguments with the thread-method timeout NOT killing.
- Currently the suite has ~14 F's at the start of line 3 + many dots. About 50% completion.
- Killed PID 300240 via taskkill.

## Approach: targeted runs by directory
- Test ID format is `[basic/facts::facts_only]` — the file path. Use `-k` to filter.
- `-k "defeasible_basic and not long_chain"` did not match because the format uses `/` not `_`.
- Use `-k "defeasible/basic"` or plain `-k "spindle_racket"` etc.
- Plan: run conformance by category groups, deselecting specific known-slow cases.
- Categories to test independently:
  1. strict_only/* (no defeasible pipeline; baseline 14 nemo_negation failures expected)
  2. defeasible/basic/* (most paper examples; need to deselect long_chain)
  3. defeasible/superiority/* (likely specificity-needed)
  4. defeasible/ambiguity/* 
  5. defeasible/closure/*, defeasible/klm/*

## NEXT
1. Run strict_only conformance (should match P0.1.5 "92 passed, 14 failed") — DONE 92/14
2. Run defeasible/basic conformance, deselecting long_chain — DONE 40/27
3. Run remaining defeasible categories — DONE
4. Aggregate failures, classify each — IN PROGRESS
5. Write report and final docs commit

## Final conformance numbers
- strict_only: 92 passed / 14 failed (matches P0.1.5)
- defeasible/basic minus long_chain: 40 passed / 27 failed
- defeasible/superiority: 0 passed / 2 failed
- defeasible/{ambiguity,closure,klm}: 3 passed / 2 failed
- negation/: 19 passed / 14 failed
- basic/ (non-defeasible): 26 passed / 0 failed
- recursion/: 49 passed / 0 failed
- errors/: 6 passed / 0 failed
- TOTAL: 235 passed / 59 failed / 1 deselected (long_chain) = 295 cases

## Failure category analysis (from running representative failures with -tb)
1. **nemo_negation safety errors** (28 cases): 14 in defeasible/strict_only/strict_only_negation_nemo_negation + 14 in negation/nemo_negation. Pre-existing engine bug, P0.1.5 documented.
2. **TrivialPreference mutual blocking** (most defeasible/* failures): expected `defeasibly: {flies(...)}` or `not_defeasibly: {flies(...)}`, got `undecided: {flies, ~flies}`. Specificity-needed Block 2.
3. **paper-correct divergence**: depysible_nests_in_trees_(tina, tweety, henrietta) — unsupported defeasible head omitted from sections per Def 3.1 cond 2 instead of being in undecided.
4. **build_arguments-scalability**: long_chain (1 case, deselected)

## Specific failures I've examined
- spindle_racket_basic_conflict: expected flies in defeasibly, actual has flies/~flies in undecided → specificity-needed
- maher_example2_tweety: expected ~fly(tweety) in defeasibly, actual undecided → specificity-needed
- bozzato_example1_bob_exception: expected ~teach_course(bob) in defeasibly, got [] → specificity-needed
- depysible_flies_tweety: expected flies(tweety) in not_defeasibly, missing section not_defeasibly → specificity-needed (wants ~flies warranted)
- morris_example5_tweety_blocked_default: expected fly(tweety) in not_defeasibly → specificity-needed
- depysible_nests_in_trees_*: paper-correct divergence

## Pattern
All non-nemo_negation failures appear to fall into specificity-needed (Block 2) or paper-correct divergence (the 3 nests_in_trees cases). I have NOT seen any "real-regression-other" yet. Will spot-check a few more to confirm.

## Final TODO before report
- Re-check unit suite to confirm no regression
- LOC on defeasible.py: 282 (was 104, +178). Within "well under 300" budget
- Pyright: 0 errors
- 4 commits so far: 3cf8804 (red), 5c38f62 (green), f2c4935 (trace re-land), 0a4c399 (pyright fix)

The mystery: run 1 completed but runs 2/3 hang. Difference might be:
- run 1 had pre-pyright-fix code; runs 2/3 have post-fix code. But the fix only changed type annotations, no runtime change.
- run 1 had stale .pyc cache that may have skipped certain tests
- pytest-timeout might handle thread vs signal differently

## DONE in this stretch
- Refactored _supporter_rule_ids to take Iterable[Argument]
- Added TYPE_CHECKING import of Argument
- Removed `del Argument` workaround
- Pyright on defeasible.py: 0 errors
- defeasible.py LOC = 282 (was 104, +178)
- Committed pyright fix as `0a4c399`
- Re-verified test_defeasible_evaluator.py + test_trace.py: 13 passed
- Killed stuck conformance pytest process
- Run 4 of conformance launched in bg

## NEXT
1. Wait for run 4 (will tee output to notes/conformance_full.log so I get everything)
2. Read FULL failure list
3. Classify each failure: nemo_negation, specificity-needed, build_arguments-scalability, paper-correct-divergence, real-regression-other
4. Run final unit suite check
5. Write final report
6. Commit final docs commit

## Known shape of trace fields (post-wire)
- DefeasibleTrace.definitely: tuple of strict atoms
- DefeasibleTrace.supported: tuple of (definitely + defeasibly) atoms
- DefeasibleTrace.classifications: list of ClassificationTrace, result in {definitely, defeasibly, not_defeasibly, undecided}
- DefeasibleTrace.proof_attempts: list of ProofAttemptTrace, only for blocked/undecided atoms
- Helpers `proof_attempts_for(atom, *, result, reason)` and `classifications_for(...)` work as before

## Conformance baseline target
267 passed / 28 failed (all `nemo_negation` safety errors per P0.1.5).
