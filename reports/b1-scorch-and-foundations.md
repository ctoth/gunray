# B1.2 — Scorched earth + foundations report

Dispatch: scorched earth deletion of the atom-level defeasible classifier,
plus north-star foundations (`Argument`, `Answer`, `PreferenceCriterion`,
`TrivialPreference`) with unit tests and Hypothesis property tests. TDD
red/green commits per foundation.

## 1. Commit hashes

In chronological order:

| Commit  | Kind          | Message                                                                            |
|---------|---------------|------------------------------------------------------------------------------------|
| 8d93de4 | scorch        | refactor(defeasible): scorched earth - delete atom-level classifier                |
| ed2fa19 | arguments red | test(arguments): Argument value type and is_subargument (red)                      |
| e56e5aa | arguments green | feat(arguments): Argument value type and is_subargument (green)                  |
| 0f3a394 | answer red    | test(answer): four-valued Answer enum (red)                                        |
| 1b1df8d | answer green  | feat(answer): four-valued Answer enum (green)                                      |
| c4ec92d | preference red | test(preference): TrivialPreference and PreferenceCriterion protocol (red)       |
| b5232f3 | preference green | feat(preference): TrivialPreference and PreferenceCriterion protocol (green)   |
| 671ceda | surface       | feat(gunray): export Argument, Answer, PreferenceCriterion on package surface      |
| 9cefb43 | trace-skip    | test(trace): skip three pre-refactor defeasible trace tests                        |

Every red/green pair was verified: the red commit fails to import the
not-yet-existing module; the green commit makes the tests pass.

## 2. LOC delta on defeasible.py

- Before (baseline at scout): **784** lines
- After (HEAD = 9cefb43): **104** lines
- Delta: **-680**

The scorched-earth commit itself reports `3 files changed, 20 insertions(+),
914 deletions(-)` — the 914 deletions span `defeasible.py` (-764), the
whole of `src/gunray/ambiguity.py` (-39), and the whole of
`tests/test_defeasible_core.py` (-175). The 20 insertions are the new
docstring, `evaluate_with_trace` stub, and re-indented strict-only path.

## 3. Deletion grep

```
rg '_can_prove|_find_blocking_peer|_has_blocking_peer|_has_live_opposition|_supporter_survives|_is_more_specific|_expand_candidate_atoms' src/ tests/
```

Output: **zero matches**. All seven atom-level classifier helpers are
gone from both source and tests. `src/gunray/ambiguity.py` and
`tests/test_defeasible_core.py` are deleted in the same commit.

## 4. Strict-only conformance pass count

Command:

```
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q --timeout=120 -k "strict_only"
```

Result: **92 passed, 14 failed, 189 deselected in 292.87 s**.

The 14 failures are all `defeasible/strict_only/strict_only_negation_nemo_negation::*`
cases raising `gunray.errors.SafetyViolationError: Variables in negated
literals must be positively bound` at `src/gunray/evaluator.py:121`. This
is the exact pre-existing engine-level safety bug documented in
`notes/refactor_progress.md` under P0.1.5 (scope: 28 `nemo_negation`
failures across all conformance, of which 14 land in the strict-only
subset). **Unchanged from baseline** — scorched earth did not regress the
strict-only shortcut.

## 5. Unit suite summary

Command:

```
uv run pytest tests -q -k "not test_conformance"
```

Result: **51 passed / 3 skipped / 1 failed / 295 deselected in 52.91 s**.

- The 51 passes include 6 new `test_arguments_basics.py` tests, 3 new
  `test_answer.py` tests, 2 new `test_preference.py` tests, plus the
  pre-existing trace / closure / parser / compiled / evaluator suites.
- The 3 skips are the three `test_trace.py` tests flagged in Section 8
  below. They carry `@pytest.mark.skip(reason="...B1.6 re-land...")`
  markers citing the specific paper-pipeline component that needs to
  re-land.
- The 1 failure is the pre-existing
  `test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  case recorded as out-of-refactor-scope in
  `notes/refactor_progress.md` P0.1 — unchanged since baseline.

No new unit-test failures. No deleted-test knowledge was lost: the Nixon
`UNDECIDED` and `nests_in_trees` UNDECIDED claims both now live as
skipped tests pointing the B1.6 coder at the exact theories and
assertions they need to re-land against the dialectical-tree pipeline.

## 6. Hypothesis property test count

The prompt's heuristic command is noisy (it only catches the
pytest-header line containing `hypothesis-6.151.12`). A direct count via
`@given` decorators is more honest:

```
rg '^@given' tests/ -c
```

Output:

```
tests/test_arguments_basics.py:3
tests/test_answer.py:1
tests/test_closure_faithfulness.py:2
tests/test_parser_properties.py:7
tests/test_preference.py:1
tests/test_trace.py:3
```

Total: **17** `@given` property tests across 6 files.
**New in this dispatch**: **5** (3 arguments + 1 answer + 1 preference).
All five run at `max_examples=500` (per prompt spec).

## 7. Paper-citation count

Command:

```
rg 'Garcia.*200[4]|Simari.*199[2]' src/gunray -c
```

Output:

```
src/gunray/arguments.py:3
src/gunray/answer.py:2
src/gunray/defeasible.py:1
src/gunray/preference.py:5
```

Total: **11** paper-citation hits in `src/gunray/`. Baseline before B1.2
was 0 (no module or docstring cited either paper). The refactor gate
ratchet climbs from 0 to 11.

## 8. Surprises

**Three pre-existing trace tests unaccounted for in the scout report.**

`tests/test_trace.py` contains three tests that assert behavioral
consequences of the atom-level classifier:

1. `test_defeasible_trace_records_blocked_and_undecided_atoms`
   — exercises the Nixon theory and asserts
   `trace.proof_attempts[...].result == "blocked"` /
   `trace.classifications[...].result == "undecided"`. Both lists are
   populated by `_record_proof_attempt` and the blocking-peer path,
   which `8d93de4` deleted.

2. `test_defeasible_trace_helpers_expose_conflict_details` — same Nixon
   theory, asserts the `equal_strength_peer_conflict` reason code and
   the `~pacifist(nixon)` opposing atom; both come from the deleted
   `_find_blocking_peer` / `_record_proof_attempt` path.

3. `test_defeasible_trace_marks_supported_but_unproved_body_as_undecided`
   — asserts the `supported_only_by_unproved_bodies` classification
   reason for `nests_in_trees(tweety)` under the penguin theory; this
   reason code was produced by the blocking-fixed-point classifier in
   the deleted code.

Scout Section 6 only inventoried `tests/test_defeasible_core.py`; these
three `test_trace.py` cases slipped through.

**Resolution applied in this dispatch:** marked all three with
`@pytest.mark.skip(...)` citing a B1.6 re-land rather than deleting
them. Each skip reason names the paper-pipeline component that should
re-land the assertion (dialectical tree, Nixon `UNDECIDED` answer,
acceptable-line machinery per Garcia & Simari 2004 Def 4.7). This keeps
the lost coverage visible as a checklist for the B1.6 coder rather than
burying it under a deletion.

**Foreman action item:** B1.6's prompt should explicitly cite the three
skipped tests by name and require the coder to un-skip them (or delete
them after verifying the paper pipeline re-lands the same assertions
under new names).

**Minor note on imports.** The prompt's Step 3 "exactly" import list
included `cast` and omitted `FactTuple`. After the cull, `cast` is
unused (as the prompt anticipated: *"drop if nothing uses cast"*) but
`_atoms_to_section` — which the prompt explicitly keeps — takes
`dict[str, set[FactTuple]]` and therefore needs `FactTuple` imported
from `schema`. Added `FactTuple`, dropped `cast`; net change is neutral
and the spirit of the prompt ("only these survive") is preserved.

## 9. One-line summary

scorched earth landed; 3 new types with 5 new property tests;
defeasible.py 784→104 LOC.
