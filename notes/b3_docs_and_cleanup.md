# B3.3 — Docs + cleanup

## 2026-04-13

**GOAL**: Five closing-cleanup tasks, one commit each: (1) README "Under the hood"
rewrite, (2) README "Query arguments and render trees" section, (3) defeasible.py
module docstring rewrite, (4) vulture dead-code sweep, (5) notes/refactor_complete.md
historical record.

**DONE (so far)**:
- Read `prompts/b3-docs-and-cleanup.md` — full spec captured. Five tasks, hard
  directive: commit as you go, do NOT touch propstore.
- Read `notes/refactor_progress.md` first 395 lines covering P0, Block 1 through
  B1.6. Need to read the rest (B1.7 through B3.2).
- Read `README.md` (146 lines). The "Under the hood" paragraph lives at lines
  42-58 with the stale disclaimer. The disclaimer to delete is the paragraph
  at lines 52-58 ("The defeasible evaluator is also intentionally narrower...
  strict-body specificity heuristic... not full Simari-Loui 1992 specificity").
- Read `notes/readme_rewrite.md` — prior rewrite pass (2026-04-11) from
  commit `2bbf8f5`. Not directly in scope for this dispatch but explains shape.
- Confirmed repo has `notes/` entries for each prior block dispatch.

**OBSERVED**:
- README currently says "semi-naive Datalog core with stratified negation, a
  defeasible layer implementing both ambiguity-blocking and
  ambiguity-propagating semantics". This is post-refactor stale — the new
  architecture is the argument/dialectical-tree pipeline.
- Current defeasible.py docstring is the B1.2 transitional stub (per spec).
- Git status: M notes/cptrload_timeout_analysis.md, M out, plus untracked
  .hypothesis, notes/defeasible_conformance.md, notes/readme_rewrite.md,
  src/gunray.tar. None touch scope of this dispatch. Will not `git add` these
  — commit only the files I author per task.

**FILES** (to touch this dispatch):
- README.md — task 1 + task 2
- src/gunray/defeasible.py — task 3 (docstring only)
- pyproject.toml — task 4 ONLY if vulture not already a dev dep
- notes/refactor_complete.md — task 5 (new file)
- reports/b3-docs-and-cleanup.md — final report

**OBSERVED (cont'd)**:
- Pre-refactor SHA: `5078df5` (refactor_baseline.md line 189). Current HEAD:
  `e38c66e`.
- Current src/gunray LOC: defeasible.py 329, preference.py 336, arguments.py
  410, dialectic.py 548, disagreement.py 87, answer.py 21. Baseline (from
  refactor_baseline.md): defeasible.py 784, ambiguity.py 39 (DELETED), no
  preference/arguments/dialectic/disagreement/answer.py.
- Baseline paper citations: 1. Current (per B2.5 report): 84 (+).
- Baseline Hypothesis properties: 0 (effectively 1 spurious grep match).
  Current per B2.6 post-fix: ≥35 at max_examples=500 (plus +1 asymmetry).
- Conformance: P0.1.5 baseline 267/28. Final post-B2.6: 250/44/1
  (paper-correctness ceiling; gap of 17 from 267 all explained by B2.5
  classification table in reports/b2-superiority-preference.md).
- __init__.py exports `answer`, `build_arguments`, `build_tree`, `mark`,
  `render_tree`, `Argument`, `Answer`, `TrivialPreference`, `DefeasibleTheory`,
  `Rule`, `Policy`, `GunrayEvaluator`, `DialecticalNode`. The prompt example's
  import list covers symbols that are all exported.
- `answer(theory, literal, criterion)` signature: takes `GroundAtom`, returns
  `Answer`. `build_tree(root, criterion, theory)`. `mark(node)`.
  `render_tree(node) -> str`. `GroundAtom` is in `gunray.types`, not exported
  from package.
- `parser.parse_atom_text(text)` exists and returns an `Atom` (not `GroundAtom`)
  — the example in the prompt imports it. Will need to verify this converts
  cleanly to `GroundAtom` for `answer()`. Likely need `parser.ground_atom` or
  construct directly via `GroundAtom(predicate="flies", arguments=("tweety",))`.
- defeasible.py current module docstring is NOT the B1.2 transitional stub
  from the prompt — it's a post-B1.6 "paper-pipeline wiring" docstring (lines
  1-14 of defeasible.py). Still needs to be rewritten to the final shape per
  task 3; what's there is descriptive but missing the specific Garcia 04
  references listed in the spec (Def 3.1, 3.4, 4.1, 4.2, 4.7, 5.1, 5.3,
  CompositePreference citation, Simari 92 Lemma 2.4).

**PROGRESS (2026-04-13 mid-dispatch)**:
- Task 1 COMPLETE. Commit `3702d90`
  ("docs(readme): rewrite Under the hood for new architecture"). Replaced
  both the "Under the hood" semi-naive paragraph AND the stale
  "intentionally narrower than full DeLP/ASPIC" disclaimer. +27/-16 lines.
- Task 2 COMPLETE. Commit `a8d0a5d`
  ("docs(readme): add Query arguments and render trees section"). Verified
  the exact code block at REPL — prints `flies(tweety)  [r1]  (U)` + all
  assertions pass (YES for tweety, NO for opus, model sections match).
  Used `GroundAtom` directly from `gunray.types` + `GeneralizedSpecificity`
  from `gunray.preference` rather than the prompt's
  `parser.parse_atom_text` sketch — `answer()` takes `GroundAtom`, not
  `Atom`, and the simpler path matches public surface.
- Task 3 COMPLETE. Commit `0c89f42`
  ("docs(defeasible): rewrite module docstring for final shape"). Replaced
  the post-B1.6 "paper-pipeline wiring" docstring with the exact spec
  text — cites Def 3.1, 3.4, 4.1, 4.2, 4.7, 5.1, 5.3, CompositePreference,
  and the Simari 92 Lemma 2.4 fallback. Pyright clean on defeasible.py.
- Task 4 IN PROGRESS. `uv run python -m vulture src/gunray tests/` →
  "No module named vulture". Need to add vulture to dev deps in
  pyproject.toml, then re-run. Per spec, pyproject edit is limited to
  adding vulture only.

**Vulture triage (2026-04-13)**:

Raw output (16 findings, 60%-100% confidence):

1. `src/gunray/compile.py:6` `compilation_surface` — 60%. **DELETE module.**
   No caller anywhere in src/ or tests/. Placeholder stub docstring says
   "Maher-style compilation is not exercised by the current local suite".
2. `src/gunray/tolerance.py:6` `tolerance_surface` — 60%. **DELETE module.**
   No caller. "Goldszmidt-tolerance placeholders for future suite
   expansion". Dead-on-arrival stub.
3. `src/gunray/defeasible.py:299` `_evaluate_strict_only_theory` — 60%.
   **DELETE.** Private wrapper around `_evaluate_strict_only_theory_with_trace`.
   Only grep hit in src/ is its own definition.
4. `src/gunray/evaluator.py:437` `_match_positive_body_with_overrides` — 60%.
   **DELETE.** No caller anywhere. Private helper left behind after an
   earlier refactor.
5. `src/gunray/errors.py:9,15,21,27,33,39` `code` class attrs — 60%.
   **LEAVE, note in report.** Conformance-suite error-code contract; no
   gunray-internal caller but propstore / conformance bridge may consume
   `.code` attribute externally. Public API symbol.
6. `src/gunray/trace.py:48` `delta_sizes` — 60%. **LEAVE, false positive.**
   It's a dataclass field and is assigned by `evaluator.py:158`. Vulture
   cannot follow dataclass attribute writes.
7. `src/gunray/types.py:9` `Binding` TypeAlias — 60%. **LEAVE, note.**
   No internal caller but it's a public type alias in `gunray.types`
   (type stubs / external consumers).
8. `src/gunray/types.py:47` `ValueTerm` TypeAlias — 60%. **LEAVE, false
   positive.** Used via forward-ref strings `"ValueTerm"` in the
   AddExpression/SubtractExpression/Comparison dataclass annotations
   (types.py lines 29-30, 35-36, 41, 43). Vulture can't see through
   string annotations.
9. `tests/conftest.py:32` `pytest_collection_modifyitems` — 60%. **LEAVE.**
   Pytest hook, framework-invoked.
10. `tests/test_conformance.py:44` `pytest_generate_tests` — 60%. **LEAVE.**
    Pytest hook, framework-invoked.
11. `tests/test_dialectic.py:466` unsatisfiable ternary — 100%. **LEAVE,
    note.** This is not a dead-symbol finding but a ternary logic flag.
    Not in scope of a vulture dead-code sweep — would require a test
    rewrite, out of scope of docs dispatch.

**Deletion plan for task 4**:
- Delete `src/gunray/compile.py` and `src/gunray/tolerance.py` (whole files).
- Delete `_evaluate_strict_only_theory` in `defeasible.py`.
- Delete `_match_positive_body_with_overrides` in `evaluator.py`.
- Re-run unit suite + pyright to confirm no regression.
- Commit: `chore(gunray): vulture sweep — delete unreached private helpers`.

**Task 4 COMPLETE**. Commit `916a5a0`
("chore(gunray): vulture sweep — delete unreached private helpers"). Ran
`uv run python -m vulture src/gunray tests/` after adding vulture>=2.11
to pyproject dev deps. Deletions:
- `src/gunray/compile.py` (whole file, placeholder stub)
- `src/gunray/tolerance.py` (whole file, placeholder stub)
- `defeasible.py` `_evaluate_strict_only_theory` wrapper (unused; only
  `_with_trace` is called)
- `evaluator.py` `_match_positive_body_with_overrides` (6-line wrapper,
  no callers)

Left in place with notes:
- errors.py `code` class attributes × 6 (external API contract)
- types.py `Binding` TypeAlias (public type alias)
- types.py `ValueTerm` TypeAlias (used via string forward refs)
- trace.py `delta_sizes` dataclass field (used via dataclass write)
- pytest hook functions in conftest/test_conformance (framework-invoked)
- test_dialectic.py:466 unsatisfiable ternary (not dead-symbol; out of
  scope of sweep)

Post-deletion unit suite: **136 passed / 1 pre-existing fail / 295
deselected**. Pyright clean on defeasible.py + evaluator.py + __init__.py.

**Task 5 IN PROGRESS**: collecting data for notes/refactor_complete.md.
- Full commit range 5078df5..HEAD retrieved (85+ commits).
- Baseline LOC: defeasible.py=784, __init__.py=30, adapter.py=59.
- Current LOC: defeasible.py=327 (post-delete), __init__.py=61,
  adapter.py=71 (both wc counts from earlier).
- B3.2 propstore report opening read: 8 propstore commits
  f35ed89..41aa2fe, propstore green-delta 2417/52 → 2424/46/5xf.
- Gunray final conformance: 250/44/1 paper ceiling.
- Commit hashes for THIS dispatch so far:
  3702d90 (readme Under the hood), a8d0a5d (readme Query section),
  0c89f42 (defeasible docstring), 916a5a0 (vulture sweep).

**NEXT**:
1. Task 1: README "Under the hood" rewrite + commit.
2. Task 2: README "Query arguments and render trees" — use `GroundAtom` directly
   (or `parser.ground_atom`) since `answer()` wants a GroundAtom. REPL verify
   before commit.
3. Task 3: defeasible.py module docstring rewrite (incorporate Def 3.1/3.4/
   4.1/4.2/4.7/5.1/5.3 citations + CompositePreference).
4. Task 4: vulture sweep. Check if installed; add to dev deps if needed.
5. Task 5: notes/refactor_complete.md — have all data except b3-propstore
   summary. Skim reports/b3-propstore-update.md before writing.
6. Verification: unit pytest -k not test_conformance, conformance, pyright on
   defeasible.py + __init__.py. REPL run of README example.
7. Write reports/b3-docs-and-cleanup.md.
