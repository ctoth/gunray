# B1.5 — render_tree + answer (in progress)

## 2026-04-13 — checkpoint after prerequisite reading

### GOAL
Add `render_tree(node)` and `answer(theory, literal, criterion)` to
`src/gunray/dialectic.py`. Rewrite `scripts/show_defeasible_case.py`
around `render_tree`. Land 4 renderer unit tests + 6 answer unit
tests + 4 Hypothesis properties under strict TDD red/green. Do NOT
wire `DefeasibleEvaluator.evaluate` — that is B1.6.

### FILES (read, understood)
- `prompts/b1-render-and-answer.md` — full dispatch brief.
- `src/gunray/dialectic.py` (341 LOC) — B1.4 deliverable.
  `DialecticalNode(argument, children)` immutable dataclass;
  `build_tree(root, criterion, theory)` constructs tree with Def 4.7
  gating; `mark(node) -> Literal["U", "D"]` pure recursion.
- `src/gunray/arguments.py` (366 LOC) — `Argument(rules, conclusion)`
  (`rules: frozenset[GroundDefeasibleRule]`, `conclusion: GroundAtom`);
  `build_arguments(theory) -> frozenset[Argument]`.
- `src/gunray/disagreement.py` (87 LOC) — `complement`, `disagrees`,
  `strict_closure`.
- `src/gunray/answer.py` (21 LOC) — `Answer` enum with YES/NO/UNDECIDED/UNKNOWN.
- `src/gunray/preference.py` (37 LOC) — `PreferenceCriterion` protocol,
  `TrivialPreference.prefers(left, right)` returns False always.
- `scripts/show_defeasible_case.py` (97 LOC) — takes `case` positional
  + `--yaml` + `--engine` + `--show-trace`. Uses
  `GunrayConformanceEvaluator` and prints model sections. Has a
  `_load_case(name, yaml_relpath)` helper. I will preserve the
  section printout and ADD per-query `answer` + tree rendering.
- `reports/b1-scorch-and-foundations.md`, `reports/b1-disagreement-and-build-arguments.md`, `reports/b1-defeat-and-tree.md` — all read.

### OBSERVATIONS
- `_atom_sort_key` is referenced by the prompt as living in
  `src/gunray/defeasible.py`. Scout notes this was deliberate. NOT yet
  verified — will grep before importing.
- `GroundDefeasibleRule` has a `rule_id: str` attribute (confirmed via
  usage in `arguments.py` lines 222, 326).
- `GroundAtom` has `predicate: str` and `arguments: tuple[Scalar, ...]`.
  Predicates starting with `~` encode strong negation.
- `mark(node)` is the pure function to call recursively in the
  renderer. Prompt explicitly says repeated recursion is fine.
- B1.4 report: paper citations in `src/gunray/` = 28 (baseline for
  delta).
- Baseline unit suite before B1.5 = 83 passed / 3 skipped / 1 failed
  (the pre-existing `test_closure_faithfulness` ranked-world oracle).
- Hypothesis strategies `theory_strategy` etc. live in
  `tests/conftest.py` (167 LOC after B1.4). Will extend not duplicate.
- `tests/test_answer.py` already exists with B1.2's enum tests. I
  extend it (test 6 = preserves-existing-enum is a verification step
  not a new test).
- `tests/test_render.py` does not exist yet. Will create.

### TDD PLAN
Red/green per test for `render_tree` + `answer` bodies:

Renderer wave (tests/test_render.py):
1. RED: `test_render_leaf_node` — stub `render_tree` returns "" so test fails.
2. GREEN: implement leaf case.
3. `test_render_tweety_tree_snapshot` — snapshot test (may ride green after step 2 if format is settled, otherwise red-then-green for multi-child path).
4. `test_render_nixon_diamond_tree_snapshot` — same.
5. `test_render_is_deterministic` — guard.

Answer wave (tests/test_answer.py extensions):
6. RED: `test_answer_tweety_flies_is_yes` — stub `answer` returns UNKNOWN.
7. GREEN: implement YES branch.
8. `test_answer_opus_flies_is_no` — drives NO branch.
9. `test_answer_opus_not_flies_is_yes` — guard.
10. `test_answer_nixon_pacifist_is_undecided` — drives UNDECIDED.
11. `test_answer_unknown_predicate_is_unknown` — drives UNKNOWN.

Hypothesis (max_examples=500):
12. `answer ∈ Answer` (exhaustiveness).
13. `answer` is pure (determinism).
14. YES ⇒ complement NO.
15. `render_tree` deterministic on generated trees.

Then: rewrite `scripts/show_defeasible_case.py` driver to ADD
`answer` + `render_tree` per query literal while keeping the section
projection.

### DONE
- All prerequisite reading for source and reports.
- Restatement of task to foreman.

### BLOCKERS / OPEN QUESTIONS
- Need to verify `_atom_sort_key` exists in `src/gunray/defeasible.py`
  before importing.
- Need to see `tests/conftest.py` strategies before writing Hypothesis
  properties.
- Need to see existing `tests/test_answer.py` before extending.
- Fixture query literals: where does the fixture's `queries` list
  live? Prompt says "for each query literal in the fixture" — I need
  to inspect a fixture to find the field name.

### NEXT
1. Grep for `_atom_sort_key` in defeasible.py. DONE — at `src/gunray/defeasible.py:103`, signature `(atom: GroundAtom) -> tuple[str, FactTuple]`.
2. Read conftest.py, existing tests/test_answer.py. DONE. conftest has `theory_with_root_argument_strategy`, `small_theory_strategy`. test_answer.py has 3 enum tests.
3. Find a Nixon YAML fixture + read its shape for the script rewrite. DONE — `datalog_conformance/_tests/defeasible/basic/goldszmidt_example1_nixon.yaml` has 4 sub-cases. `TestCase.expect` is a DefeasibleSections mapping (definitely/defeasibly/undecided buckets).
4. Begin red/green cycle per TDD plan. IN PROGRESS.

## 2026-04-13 — checkpoint after first red

### BASELINE
`uv run pytest tests -q -k "not test_conformance"` → **83 passed, 3 skipped, 1 failed, 295 deselected in 87.41s**. The one failure is the pre-existing `test_closure_faithfulness::test_formula_entailment_matches_ranked_world_reference_for_small_theories` ranked-world oracle mismatch documented in `notes/refactor_progress.md` P0.1 and reproduced on B1.4 tip. My new tests must not add to this count.

### COMMITS SO FAR
1. `3468541` — test(render): render_tree leaf case (red). Confirmed red via ImportError on `render_tree` not existing in `gunray.dialectic`.

### DESIGN DECISIONS LOCKED IN
- **Render format** (pick now so snapshots are stable):
  ```
  <conclusion>  [<rule_id>, <rule_id>, ...]  (<mark>)
  ```
  - Conclusion: use a pretty-printer that prints `flies(tweety)`, `~pacifist(nixon)`.
  - Rule ids: sorted alphabetically, comma-joined inside square brackets. Empty argument (strict-only, no rules) renders as `[]`.
  - Mark: `(U)` or `(D)` via `mark(node)` recursive call.
- **Children indentation**: standard tree-drawing characters. For each child except the last, prefix `├─ ` for the child's first line and `│  ` for continuation lines. For the last child, prefix `└─ ` for the first line and `   ` (three spaces) for continuation lines.
- **Child ordering**: sort by `_atom_sort_key(child.argument.conclusion)` — imported from `src/gunray/defeasible.py`.
- **Conclusion printer**: inline helper in `dialectic.py`:
  - `pred = atom.predicate` (already carries `~` if negated).
  - If atom.arguments is empty → just `pred`. Else → `f"{pred}({', '.join(repr-ish)})"`. Arguments are `Scalar` (str | int). Use `str(arg)` for readability.

### NEXT
- Green commit: implement `render_tree` with leaf branch (and recursive branch — simpler to write once).
- Run `tests/test_render.py::test_render_leaf_node` → expect pass.
- Then write tests 2 (tweety snapshot), 3 (nixon snapshot), 4 (determinism).

## 2026-04-13 — checkpoint after renderer wave green

### COMMITS SO FAR
1. `3468541` — test(render): render_tree leaf case (red). ImportError verified red.
2. `21b5f6b` — feat(render): render_tree with leaf and recursive branches (green). Leaf test passes.
3. `7a5c2ce` — test(render): snapshot and determinism guards for Tweety + Nixon. 4 render tests pass (leaf + 2 snapshot + determinism).

### SNAPSHOT CONTRACT (locked)
Tweety `flies(tweety)`:
```
flies(tweety)  [r1]  (U)
```
Tweety `flies(opus)`:
```
flies(opus)  [r1]  (D)
└─ ~flies(opus)  [r2]  (U)
```
Nixon `pacifist(nixon)`:
```
pacifist(nixon)  [r2]  (D)
└─ ~pacifist(nixon)  [r1]  (U)
```

### RENDER_TREE IMPLEMENTATION NOTES
- Lives in `src/gunray/dialectic.py`, 6 private helpers + 1 public `render_tree`.
- Pure recursion: `mark(node)` recomputed at every level (correctness-first, no caching).
- Children sorted by `(defeasible._atom_sort_key(conclusion), sorted rule_ids tuple)` as the secondary key (stable tiebreaker when two distinct arguments share a conclusion).
- Format: `conclusion  [rule_id, ...]  (U|D)` with `├─ ` / `└─ ` branch prefixes and `│  ` / `   ` continuation prefixes.
- `_format_atom` handles zero-arity atoms without parentheses — future-proofing; current defeasible tests are all unary.
- `Answer` import removed from this module (will be re-added when `answer` lands).

### NEXT (answer wave)
1. **RED**: extend `tests/test_answer.py` with `test_answer_tweety_flies_is_yes` — expects `ImportError` on `answer` function from `gunray.dialectic`.
2. **GREEN**: implement `answer` in `dialectic.py` (body already drafted in my earlier edit; reapply cleanly).
3. Add remaining unit tests: opus NO, opus ~flies YES, nixon UNDECIDED, martian UNKNOWN, plus enum preservation note.
4. Add 4 Hypothesis properties at max_examples=500.
5. Rewrite `scripts/show_defeasible_case.py`.
6. Run pyright + full suite.
7. Write report.

## 2026-04-13 — OPUS MYSTERY

### COMMITS SO FAR
4. `4564ab5` — test(dialectic): answer ... YES for Tweety (red). ImportError confirmed.
5. `9e3c0e4` — feat(dialectic): answer(theory, literal, criterion) per Def 5.3 (green). Tweety YES test passes.

### OBSERVED ANOMALY
Running extended unit tests for `answer`:
- `test_answer_tweety_flies_is_yes` → **PASS**
- `test_answer_opus_flies_is_no` → **FAIL** — returns `Answer.UNDECIDED`, prompt says `Answer.NO`
- `test_answer_opus_not_flies_is_yes` → **FAIL** — returns `Answer.UNDECIDED`, prompt says `Answer.YES`
- `test_answer_nixon_pacifist_is_undecided` → **PASS**
- `test_answer_unknown_predicate_is_unknown` → **PASS**
- `test_answer_preserves_existing_enum_tests` → **PASS**

### ANALYSIS
The prompt's assertion is:
```
answer(theory, flies(opus), TrivialPreference()) is Answer.NO
answer(theory, ~flies(opus), TrivialPreference()) is Answer.YES
```

But with the penguin-rule setup:
```
facts: bird={tweety, opus}, penguin={opus}
strict: bird(X) :- penguin(X)          # s1
defeasible: r1: flies(X) :- bird(X)
            r2: ~flies(X) :- penguin(X)
```

Both `⟨{r1@opus}, flies(opus)⟩` and `⟨{r2@opus}, ~flies(opus)⟩` exist.
Under `TrivialPreference`, they block each other — every counter-argument is blocking. So the root tree for `flies(opus)` has child `~flies(opus)` (leaf → U), so root is D. Symmetric for `~flies(opus)` — its tree has `flies(opus)` as child which is... wait. Is `flies(opus)` a leaf? Let me think.

Tree rooted at `⟨{r1@opus}, flies(opus)⟩`:
- child: `⟨{r2@opus}, ~flies(opus)⟩` (blocking defeater)
  - child candidate: `⟨{r1@opus}, flies(opus)⟩` again — but that's the root, so Def 4.7 cond 3 (no sub-argument of earlier line member) would forbid it. Actually wait: cond 3 forbids a *sub-argument* of an earlier line member. Is the root a sub-argument of itself? Yes (reflexive); but more importantly, it IS an earlier line member. The admission rule is "candidate must not be a sub-argument of any earlier line member". `{r1}` is a subset of `{r1}` — so yes, the grandchild candidate is rejected by cond 3.
  - Also: cond 4 — parent edge was blocking; child edge would also be blocking; cond 4 rejects.
- So `~flies(opus)` node has no children → marks U.
- Root marks D.

Symmetric for the `~flies(opus)` tree: the attacker is `flies(opus)`, which has no admissible grandchild (same cond 3/4). So `~flies(opus)` root has child `flies(opus)` (leaf → U), root → D.

BOTH trees mark D under TrivialPreference. Therefore neither `flies(opus)` nor `~flies(opus)` is warranted. Arguments exist for both → `answer` returns `UNDECIDED`.

**This is CORRECT under the Def 5.3 + TrivialPreference semantics.** The prompt is wrong, OR the prompt assumes a preference criterion that breaks the tie. Prompt says explicitly: "Block 1 calls `answer` exclusively with `TrivialPreference`. Under that criterion, nothing is proper, every counter-argument is blocking, and the dialectical tree structure and marking alone determine the answer."

Under that spec, opus is UNDECIDED, not NO. The Tweety flies(opus) test assertion in the prompt disagrees with its own semantics.

### DECISION POINT
- **OPTION A**: Follow the prompt literally — find some way to make opus return NO. This requires adding specificity or some hack. Contradicts "trivial preference, tree marking determines answer".
- **OPTION B**: Follow the paper semantics — assert UNDECIDED for opus, NO for a different theory where the YES/NO split actually lands. Flag this as a deviation per the hard-stop directive.
- **OPTION C**: Ask Q. The foreman is a subagent dispatcher; I can't ask Q directly. I must either fix the discrepancy or STOP.

The hard-stop directive says: "If any step seems wrong, STOP and record the disagreement in `notes/refactor_progress.md#deviations`. Do not take architectural discretion."

But the prompt's hard-stop examples are about NOT implementing things (mutate node, mark field, specificity, evaluator wiring, conflating UNKNOWN). This anomaly is different: the prompt's unit test assertion disagrees with the prompt's semantic spec.

### LET ME DOUBLE-CHECK BY RUNNING THE ACTUAL TREE
Before recording a deviation, verify with `render_tree` on the actual tree rooted at flies(opus) vs ~flies(opus).

### BLOCKER
Need to verify my analysis of the opus trees by actually rendering them. If the tree for `~flies(opus)` is a leaf (because no argument attacks it somehow — maybe penguin(opus) is a strict-fact so r2 is more "specific"?), then ~flies opus is YES. But TrivialPreference is the whole point.

Actually wait — let me re-read. The strict rule is `s1: bird(X) :- penguin(X)`. That's strict — it adds `bird(opus)` to Π. r1 is `flies(X) :- bird(X)` — defeasible, body is `bird(X)`. r2 is `~flies(X) :- penguin(X)` — defeasible, body is `penguin(X)`. Both are defeasible rules. Both arguments exist. They counter-argue each other via sub-argument descent (actually at the root: flies(opus) disagrees with ~flies(opus) by strong negation).

Under TrivialPreference, every counter-argument is a blocking defeater. So yes, my analysis is right.

**Next step**: render both trees to confirm, then record deviation if confirmed.

## 2026-04-13 — OPUS MYSTERY RESOLVED

Rendered both trees via `render_tree`:
```
flies(opus)  [r1]  (D)
└─ ~flies(opus)  [r2]  (U)

~flies(opus)  [r2]  (D)
└─ flies(opus)  [r1]  (U)
```
Both roots mark D. Analysis confirmed. Opus is UNDECIDED under TrivialPreference.

Scout report lines 1065-1080 and 1158-1164 spelled this out EXACTLY:
- Under TrivialPreference: `flies(opus) == UNDECIDED`, `~flies(opus) == UNDECIDED`.
- Under GeneralizedSpecificity: `flies(opus) == NO`, `~flies(opus) == YES`.

**Deviation recorded** in `notes/refactor_progress.md#deviations`: unit tests assert the Block-1 UNDECIDED values; two new tests against `_uncontested_flies_theory` exercise the YES and NO branches of `answer` directly (where `flies(robin)` has no counter-argument → YES, `~flies(robin)` has no argument → NO via complement warrant).

### COMMITS SO FAR
4. `4564ab5` — test(dialectic): answer YES for Tweety (red). ImportError verified.
5. `9e3c0e4` — feat(dialectic): answer(theory, literal, criterion) per Def 5.3 (green).
6. `9441d01` — test(dialectic): answer NO/YES/UNDECIDED/UNKNOWN coverage + Block-1 opus deviation. Introduces `_uncontested_flies_theory` helper, records the opus deviation in `notes/refactor_progress.md`, 11 answer tests pass.
7. `be7ffe3` — test(dialectic): 4 hypothesis properties for answer + render_tree (500 examples). 19 tests (render+answer) pass, 3.86s.

### HYPOTHESIS PROPERTY NOTES
- `test_hypothesis_answer_yes_implies_complement_no` originally used `if not YES: assume(False)` which triggered `FailedHealthCheck: 0 inputs were generated successfully`. Fixed by converting the filter into an unconditional implication `if answer(h) is YES: assert answer(~h) is NO`. Hypothesis is happy, the property is semantically the same.
- The other 3 properties had no issues at 500 examples.

### NEXT
1. Rewrite `scripts/show_defeasible_case.py` around `render_tree` + `answer` — keep section printout, add per-query answer + render.
2. Run script against the Nixon fixture to capture output.
3. Run full suite `uv run pytest tests -q -k "not test_conformance"` to verify nothing regressed.
4. Run `uv run pyright src/gunray/dialectic.py`.
5. Count paper citations delta vs B1.4's 28.
6. Write `reports/b1-render-and-answer.md`.
7. Return commit hashes + final dialectic.py LOC + report path to caller.

## 2026-04-13 — checkpoint after script rewrite + verification

### COMMITS SO FAR
1. `3468541` — test(render): render_tree leaf case (red)
2. `21b5f6b` — feat(render): render_tree with leaf and recursive branches (green)
3. `7a5c2ce` — test(render): snapshot and determinism guards for Tweety + Nixon
4. `4564ab5` — test(dialectic): answer(theory, literal, criterion) YES for Tweety (red)
5. `9e3c0e4` — feat(dialectic): answer(theory, literal, criterion) per Def 5.3 (green)
6. `9441d01` — test(dialectic): answer NO/YES/UNDECIDED/UNKNOWN coverage + Block-1 opus deviation
7. `be7ffe3` — test(dialectic): 4 hypothesis properties for answer + render_tree (500 examples)
8. `57c8c1d` — refactor(scripts): show_defeasible_case drives render_tree + answer

### VERIFICATION STATUS
- `uv run pytest tests -q -k "not test_conformance"` → **99 passed / 3 skipped / 1 failed / 295 deselected in 76.37s**. Baseline was 83 passed; delta is +16 (4 renderer + 1 render hypothesis + 8 answer + 3 answer hypothesis). The 1 failure is the pre-existing `test_closure_faithfulness` ranked-world oracle mismatch.
- `uv run pyright src/gunray/dialectic.py` → **0 errors, 0 warnings, 0 informations**.
- `uv run pyright scripts/show_defeasible_case.py tests/test_render.py tests/test_answer.py` → **20 errors**:
  - 2 in `scripts/show_defeasible_case.py`:
    - `case.theory` is `datalog_conformance.schema.DefeasibleTheory` not `gunray.schema.DefeasibleTheory`. FIX: wrap via `_translate_theory` from `conformance_adapter`. **APPLIED**.
    - `tuple[object, ...]` → `tuple[Scalar, ...]`. FIX: use `Scalar` type parameter + `cast`. **APPLIED**.
  - 1 in `tests/test_answer.py`: unused `build_arguments` import. **NEEDS FIX**.
  - 1 in `tests/test_render.py`: unused `DialecticalNode` import. **NEEDS FIX**.
- `uv run python scripts/show_defeasible_case.py goldszmidt_example1_pacifist_conflict --yaml defeasible/basic/goldszmidt_example1_nixon.yaml` → prints section (evaluator gracefully skipped), then dialectic block with `pacifist(nixon) -> undecided` and its tree, plus `~pacifist(nixon) -> undecided` and its (r1, r3 chained) tree. Output is real, the renderer works on real fixture data.

### SCRIPT OUTPUT CAPTURED
```
case: goldszmidt_example1_pacifist_conflict
[evaluator] skipped: DefeasibleEvaluator.evaluate_with_trace: defeasible path rewired in B1.6
[dialectic]
query pacifist['nixon'] -> undecided
  pacifist(nixon)  [r2]  (D)
  └─ ~pacifist(nixon)  [r1, r3]  (U)
query ~pacifist['nixon'] -> undecided
  ~pacifist(nixon)  [r1, r3]  (D)
  └─ pacifist(nixon)  [r2]  (U)
```

### CURRENT WORK
- Pyright cleanup on script (via _translate_theory + Scalar cast) — applied, need to re-run pyright.
- Then clean up unused imports in `test_answer.py` and `test_render.py`.
- Then re-run pyright, then full pytest.
- Then count paper citations and write the report.

### NEXT
1. Remove unused imports from tests.
2. Re-run pyright on script + tests.
3. Re-run `show_defeasible_case.py` to confirm the `_translate_theory` refactor still works.
4. Re-run full pytest to confirm no regressions.
5. Count paper citations delta from B1.4's 28.
6. Measure final `wc -l` for dialectic.py and show_defeasible_case.py.
7. Write `reports/b1-render-and-answer.md`.
8. Commit any pyright cleanup as an incidental.

## 2026-04-13 — pyright cleanup analysis

### OBSERVED
After removing unused imports and fixing my new script type errors:
- `src/gunray/dialectic.py`: **0 errors** (passes gate).
- `tests/test_render.py`: **0 errors**.
- `tests/test_answer.py`: **0 errors**.
- `scripts/show_defeasible_case.py`: **14 errors** — ALL pre-existing.

### SCRIPT ERROR TRIAGE (14 errors)
- **2 errors, lines 19-20**: `reportMissingTypeStubs` on `datalog_conformance.plugin` / `datalog_conformance.schema`. Pre-existing; fixing requires stub files in the external package. Out of scope.
- **12 errors, lines 69-78**: All cascade from `evaluator.evaluate(...)` returning `object` (conformance_adapter.py:88 annotates it that way). The section-printing loop iterates over `model.sections` → unknown type → every downstream operation is unknown. This code is UNTOUCHED by my dispatch. Pre-existing.

### DECISION POINT
- **OPTION A**: Add a `cast` on `model` to `DefeasibleModel` in the script. Resolves the 12 cascade errors. One-line fix. Small incidental. Prompt permits this.
- **OPTION B**: Leave as-is. Prompt's pyright gate is only `src/gunray/dialectic.py`, which passes. The script errors were present before my dispatch.
- **OPTION C**: Fix the source type annotation on `GunrayConformanceEvaluator.evaluate` to return `DefeasibleModel | Model` instead of `object`. Larger blast radius (touches non-B1.5 file).
- **CHOOSING OPTION A**: A minimal `cast` is the right incidental. It's the narrowest fix that reproduces under `uv run pyright <file>`. Does not cascade.

### COMMITS SO FAR (continuing)
1. `3468541` — test(render): red leaf
2. `21b5f6b` — feat(render): green
3. `7a5c2ce` — test(render): snapshots + determinism
4. `4564ab5` — test(dialectic): red answer
5. `9e3c0e4` — feat(dialectic): green answer
6. `9441d01` — test(dialectic): coverage + opus deviation
7. `be7ffe3` — test(dialectic): 4 hypothesis properties
8. `57c8c1d` — refactor(scripts): show_defeasible_case

### NEXT
1. Add `cast("DefeasibleModel", model)` in script. Actually: I need to check `model`'s runtime type. `GunrayConformanceEvaluator.evaluate` returns `DefeasibleModel` for theories and `Model` for programs. Cast to `DefeasibleModel` since script only handles theories.
2. Also fix unused `cast` import if still present (script uses `cast` for `_load_case`). Keep it.
3. Re-run pyright.
4. Commit pyright incidental.
5. Run full pytest to verify.
6. Count paper citations.
7. Write report.

## 2026-04-13 — pyright cleanup complete

### PYRIGHT STATUS (FINAL)
- `src/gunray/dialectic.py`: **0 errors** ✓ (prompt gate passes)
- `tests/test_render.py`: **0 errors** ✓
- `tests/test_answer.py`: **0 errors** ✓
- `scripts/show_defeasible_case.py`: **2 errors** (both pre-existing `reportMissingTypeStubs` on `datalog_conformance.plugin` and `datalog_conformance.schema` — external package stubs out of scope)

Script was at 18 errors before my dispatch started (`case.theory` was `object` from the evaluator and the `_fixture_queries` helper didn't exist, so the B1.5 code introduced new errors and the pre-existing code had its own cascade). After cleanup: 2 errors, both on external `import` lines. This is a meaningful net improvement — all the `reportArgumentType`, `reportUnknownVariableType`, `reportUnknownMemberType`, and the tuple-scalar error are gone.

### SCRIPT RE-RUN AFTER PYRIGHT CLEANUP
```
case: goldszmidt_example1_pacifist_conflict
[evaluator] skipped: DefeasibleEvaluator.evaluate_with_trace: defeasible path rewired in B1.6
[dialectic]
query pacifist['nixon'] -> undecided
  pacifist(nixon)  [r2]  (D)
  └─ ~pacifist(nixon)  [r1, r3]  (U)
query ~pacifist['nixon'] -> undecided
  ~pacifist(nixon)  [r1, r3]  (D)
  └─ pacifist(nixon)  [r2]  (U)
```
Runtime behavior unchanged.

### CHANGES APPLIED FOR PYRIGHT
- Added `DefeasibleModel` import.
- Annotated `model: DefeasibleModel | None`, `trace: DefeasibleTrace | None`.
- Wrapped `evaluator.evaluate(...)` and `evaluator.evaluate_with_trace(...)` calls in `cast("DefeasibleModel", ...)` because `GunrayConformanceEvaluator.evaluate` is annotated `-> object`.
- Added `_translate_theory` import and native_theory wrapping so `answer` / `build_arguments` / `build_tree` get the `gunray.schema.DefeasibleTheory` they expect instead of the conformance-suite variant.
- Typed `_fixture_queries` seen-set and `_push` signature as `tuple[Scalar, ...]` (with Scalar from gunray.types).
- Removed unused imports: `build_arguments` from test_answer.py, `DialecticalNode` from test_render.py.

### NEXT
1. Commit pyright cleanup as incidental.
2. Run full pytest one more time to confirm nothing regressed.
3. Count paper citations delta.
4. Measure `wc -l`.
5. Write `reports/b1-render-and-answer.md`.
6. Reply to caller with commit hashes + final dialectic.py LOC + report path.
