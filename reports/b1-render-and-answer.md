# B1.5 — render_tree + answer

## One-line summary

Strict TDD landed `render_tree` (pure deterministic Unicode debugger
for `DialecticalNode`) and `answer(theory, literal, criterion)`
(Garcia & Simari 2004 Def 5.3 four-valued DeLP query) on top of
`src/gunray/dialectic.py`, rewrote `scripts/show_defeasible_case.py`
around `render_tree`, landed 4 renderer unit tests + 8 answer unit
tests + 4 Hypothesis properties at 500 examples each, and discovered
that the prompt's `opus_flies == NO` assertion is the Block-2
generalized-specificity result accidentally written into a Block-1
test — deviation recorded with the paper anchor and a matching pair
of NO/YES tests against a fresh theory that exercises those branches
under `TrivialPreference` correctly.

## 1. Commits (chronological)

| # | Hash | Kind | Message |
| - | ---- | ---- | ------- |
| 1 | `3468541` | red   | test(render): render_tree leaf case (red) |
| 2 | `21b5f6b` | green | feat(render): render_tree with leaf and recursive branches (green) |
| 3 | `7a5c2ce` | test  | test(render): snapshot and determinism guards for Tweety + Nixon |
| 4 | `4564ab5` | red   | test(dialectic): answer(theory, literal, criterion) YES for Tweety (red) |
| 5 | `9e3c0e4` | green | feat(dialectic): answer(theory, literal, criterion) per Def 5.3 (green) |
| 6 | `9441d01` | test  | test(dialectic): answer NO/YES/UNDECIDED/UNKNOWN coverage + Block-1 opus deviation |
| 7 | `be7ffe3` | test  | test(dialectic): 4 hypothesis properties for answer + render_tree (500 examples) |
| 8 | `57c8c1d` | refactor | refactor(scripts): show_defeasible_case drives render_tree + answer |
| 9 | `aa41ad1` | chore | chore(b1.5): pyright incidental — type script model, drop unused imports |

Red commits 1 and 4 were verified red by `ImportError` on the
not-yet-existing `render_tree` / `answer` names. Commits 3, 6, 7 land
additional regression guards and Hypothesis properties on
already-green implementations — the same pattern B1.3 and B1.4 used
for guard tests that were green on first run because the earlier
green commit already covered them.

## 2. Final file LOCs

| File | LOC (before B1.5) | LOC (after B1.5) | Delta |
| ---- | ----------------: | ---------------: | ----: |
| `src/gunray/dialectic.py`              | 341 | **538** | +197 |
| `scripts/show_defeasible_case.py`      |  97 | **205** | +108 |
| `tests/test_render.py`                 |   0 | **142** | +142 (new file) |
| `tests/test_answer.py`                 |  31 | **262** | +231 |

Dialectic deltas: the `render_tree` wave added 6 helpers
(`_format_atom`, `_format_rule_ids`, `_sorted_children`,
`_render_lines`, `_render_child_lines`, plus the public
`render_tree`) and the `answer` wave added 4 (`_theory_predicates`,
`_strip_negation`, `_is_warranted`, and public `answer`).

## 3. Gate metrics

- **Unit suite pass count**: `uv run pytest tests -q -k "not test_conformance"` →
  **99 passed / 3 skipped / 1 failed / 295 deselected in 74.11 s**.
  Baseline before this dispatch (B1.4 tip) was 83 passed. The +16
  delta breaks down as:
  - 4 renderer unit tests (`tests/test_render.py`).
  - 1 renderer Hypothesis property (`tests/test_render.py`).
  - 8 new answer unit tests (`tests/test_answer.py`).
  - 3 new answer Hypothesis properties (`tests/test_answer.py`).
  The 1 pre-existing failure is the
  `test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
  ranked-world oracle mismatch documented in
  `notes/refactor_progress.md` P0.1 and carried forward unchanged
  from B1.4.
- **New Hypothesis properties**: **4**, all decorated with
  `@settings(max_examples=500, deadline=None)`. Paper / prompt
  citations:
  - `test_hypothesis_answer_is_member_of_enum` — exhaustiveness of
    Def 5.3 case analysis.
  - `test_hypothesis_answer_is_pure` — determinism; guards against
    caching or mutation leakage in the tree machinery.
  - `test_hypothesis_answer_yes_implies_complement_no` — complement
    consistency; phrased as an unconditional implication rather
    than `assume(False)` to avoid Hypothesis's `filter_too_much`
    health-check firing (most random small theories do not warrant
    a generated literal, so `assume` would reject 100 % of inputs
    and hang generation).
  - `test_hypothesis_render_tree_is_deterministic` — renderer
    purity over Hypothesis-generated `(theory, root)` pairs via the
    existing B1.4 `theory_with_root_argument_strategy`.
- **Paper citations in `src/gunray/`**: **31** total Garcia/Simari
  hits across 6 files (B1.4 was 28 → **+3**). Breakdown after the
  dispatch:
  - `answer.py`: 2 (unchanged)
  - `arguments.py`: 6 (unchanged)
  - `defeasible.py`: 1 (unchanged)
  - `disagreement.py`: 3 (unchanged)
  - `preference.py`: 5 (unchanged)
  - `dialectic.py`: **14** (was 11 → +3 for the `render_tree` /
    `answer` module-docstring paragraphs and the `_theory_predicates`
    / `_is_warranted` / `answer` function docstrings)
- **`wc -l src/gunray/dialectic.py`**: **538** (B1.4 was 341 → +197).
- **`wc -l scripts/show_defeasible_case.py`** (before → after):
  **97 → 205** (+108). The growth is roughly 50/50 between the
  dialectic printing section and the new `_fixture_queries` /
  `_translate_theory` / graceful-fallback plumbing.
- **`uv run pyright src/gunray/dialectic.py`** → **0 errors, 0
  warnings, 0 informations**.
- **`uv run pyright tests/test_render.py tests/test_answer.py`** →
  **0 errors, 0 warnings, 0 informations**.
- **`uv run pyright scripts/show_defeasible_case.py`** → **2
  errors**, both `reportMissingTypeStubs` on
  `datalog_conformance.plugin` / `datalog_conformance.schema`.
  These were present before the dispatch started (the pre-B1.5
  script imported both modules identically); the remaining 16
  pre-existing errors on the section-printing loop cascade were
  cleared as an incidental via commit `aa41ad1`. External stubs
  are out of scope for this dispatch.

## 4. Test → paper anchor → result mapping

| # | File | Test | Paper anchor | Result |
| - | ---- | ---- | ------------ | ------ |
| 1 | `test_render.py` | `test_render_leaf_node` | Garcia 04 Proc 5.1 (leaf mark = U) + render engineering | pass |
| 2 | `test_render.py` | `test_render_tweety_opus_tree_snapshot` | Scout 5.1 + Garcia 04 Def 5.1 / Proc 5.1 | pass |
| 3 | `test_render.py` | `test_render_nixon_diamond_tree_snapshot` | Scout 5.2 + Garcia 04 Def 5.1 / Def 4.7 cond 3 & 4 | pass |
| 4 | `test_render.py` | `test_render_is_deterministic` | renderer purity | pass |
| 5 | `test_render.py` | `test_hypothesis_render_tree_is_deterministic` | renderer purity (500 examples) | pass |
| 6 | `test_answer.py` | `test_answer_tweety_flies_is_yes` | Garcia 04 Def 5.3 (YES branch) | pass |
| 7 | `test_answer.py` | `test_answer_opus_flies_is_undecided_under_trivial_preference` | Garcia 04 Def 5.3 + TrivialPreference; scout 5.1 lines 1065-1080 | pass |
| 8 | `test_answer.py` | `test_answer_opus_not_flies_is_undecided_under_trivial_preference` | Garcia 04 Def 5.3 + TrivialPreference; scout 5.1 lines 1065-1080 | pass |
| 9 | `test_answer.py` | `test_answer_uncontested_flies_is_yes` | Garcia 04 Def 5.3 YES branch (no counter-argument) | pass |
| 10 | `test_answer.py` | `test_answer_uncontested_not_flies_is_no` | Garcia 04 Def 5.3 NO branch (complement warranted, literal has no argument) | pass |
| 11 | `test_answer.py` | `test_answer_nixon_pacifist_is_undecided` | Scout 5.2 + Garcia 04 Def 5.3 UNDECIDED branch | pass |
| 12 | `test_answer.py` | `test_answer_unknown_predicate_is_unknown` | Garcia 04 Def 5.3 UNKNOWN branch (language check) | pass |
| 13 | `test_answer.py` | `test_answer_preserves_existing_enum_tests` | B1.2 enum regression guard | pass |
| 14 | `test_answer.py` | `test_hypothesis_answer_is_member_of_enum` | Garcia 04 Def 5.3 exhaustiveness (500 examples) | pass |
| 15 | `test_answer.py` | `test_hypothesis_answer_is_pure` | determinism (500 examples) | pass |
| 16 | `test_answer.py` | `test_hypothesis_answer_yes_implies_complement_no` | Garcia 04 Def 5.3 complement consistency (500 examples) | pass |

## 5. Snapshot outputs

### Tweety `⟨{r1@opus}, flies(opus)⟩`

```
flies(opus)  [r1]  (D)
└─ ~flies(opus)  [r2]  (U)
```

### Nixon Diamond `⟨{r2}, pacifist(nixon)⟩`

```
pacifist(nixon)  [r2]  (D)
└─ ~pacifist(nixon)  [r1]  (U)
```

### Tweety leaf `⟨{r1@tweety}, flies(tweety)⟩`

```
flies(tweety)  [r1]  (U)
```

## 6. Script output

```
$ uv run python scripts/show_defeasible_case.py goldszmidt_example1_pacifist_conflict --yaml defeasible/basic/goldszmidt_example1_nixon.yaml
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

And on a simpler case from the same fixture:

```
$ uv run python scripts/show_defeasible_case.py goldszmidt_example1_nixonian_nixon --yaml defeasible/basic/goldszmidt_example1_nixon.yaml
case: goldszmidt_example1_nixonian_nixon
[evaluator] skipped: DefeasibleEvaluator.evaluate_with_trace: defeasible path rewired in B1.6
[dialectic]
query nixonian['nixon'] -> yes
  nixonian(nixon)  []  (U)
```

Notes on the script's graceful fallback: the pre-B1.5 version of the
script crashed with a `NotImplementedError` on every defeasible
fixture because `DefeasibleEvaluator.evaluate_with_trace` currently
raises on the defeasible path (rewired in B1.6). The B1.5 rewrite
catches that exception, prints `[evaluator] skipped: ...`, and then
runs the `[dialectic]` section regardless — so the rendered tree is
usable for B1.6 debugging against real fixtures today, not later.

## 7. Surprises

### The opus deviation — prompt mismatch vs. paper semantics

The prompt listed two assertions that should have been Block-2
results:

```
test_answer_opus_flies_is_no      → answer(..., flies(opus))  is Answer.NO
test_answer_opus_not_flies_is_yes → answer(..., ~flies(opus)) is Answer.YES
```

The prompt's own "Interaction with TrivialPreference" paragraph
says: *"Under that criterion, nothing is proper, every
counter-argument is blocking, and the dialectical tree structure
and marking alone determine the answer."*

Under that rule, the Tweety theory's opus arguments — `⟨{r1@opus},
flies(opus)⟩` and `⟨{r2@opus}, ~flies(opus)⟩` — block each other,
both dialectical trees mark `D`, and Def 5.3 returns `UNDECIDED`
for both queries. I verified this by rendering both trees:

```
flies(opus)  [r1]  (D)          ~flies(opus)  [r2]  (D)
└─ ~flies(opus)  [r2]  (U)      └─ flies(opus)  [r1]  (U)
```

The scout report anticipated this exact mismatch at lines 1065-1080:

> `answer(theory, flies(opus))` — this is the classical
> specificity case. ... Under the paper's Def 5.3 that makes
> `flies(opus) == UNDECIDED` ... Under GeneralizedSpecificity,
> `r2` is strictly more specific ... giving `flies(opus) == NO` and
> `~flies(opus) == YES`.

Following the prompt literally would have required implementing
specificity — which the prompt's own hard-stop directive forbids
("Do NOT implement GeneralizedSpecificity — that is Block 2"). The
implementation as written is the paper's semantics exactly; the
prompt's assertion contradicts its own spec. I took the
minimum-deviation path:

- Unit tests 7 and 8 now assert the Block-1 `UNDECIDED` value and
  cite the scout lines in their docstrings.
- Unit tests 9 and 10 added a small `_uncontested_flies_theory`
  helper where `flies(robin)` has no counter-argument at all —
  this drives the `answer` YES branch and the `answer` NO branch
  (via `complement(~flies(robin)) == flies(robin)` warranted)
  directly under TrivialPreference, preserving coverage of the
  implementation's conditional logic.
- The deviation is recorded in
  `notes/refactor_progress.md#deviations` with the paper anchor,
  the scout quote, and the rationale for the test rewrite.

No architectural discretion was taken: the implementation follows
Def 5.3 verbatim, the tests assert the Block-1 behavior the paper
mandates, and the Block-2 expected values will land automatically
once `GeneralizedSpecificity` is implemented in B2.

### Hypothesis `assume` vs. implication form

`test_hypothesis_answer_yes_implies_complement_no` was originally
written with `if answer(...) is not YES: assume(False)`. Hypothesis
triggered `FailedHealthCheck: filter_too_much` because the
small-theory strategy rarely generates warranted literals (most
small random theories produce UNDECIDED or UNKNOWN under
TrivialPreference). Rewriting as an unconditional implication
`if answer(h) is YES: assert answer(~h) is NO` preserves the
property's semantics, avoids the filter trap, and lets Hypothesis
run the full 500 examples cleanly in ~1 second. No correctness
trade-off — the property is logically identical.

### Script's pre-existing pyright cascade

The pre-B1.5 `scripts/show_defeasible_case.py` had 18 pyright
errors, 12 of them cascading from `GunrayConformanceEvaluator.
evaluate(...) -> object` into the section-printing loop. I cleaned
them up in the `aa41ad1` incidental commit: `cast("DefeasibleModel",
raw_model)` breaks the cascade without touching the adapter's
public type annotation. The 2 remaining `reportMissingTypeStubs`
errors on `datalog_conformance` imports are external package
issues and out of scope.

### `DialecticalNode` is immutable, `mark` is recomputed

Per the hard-stop directive I did not mutate `DialecticalNode`, did
not add a `mark` field, and did not cache anything. The renderer
calls `mark(node)` recursively at every level, which is O(n²) for a
tree of depth n — fine for Block 1 test sizes. Block 2 will want a
`mark` cache if the tree gets big, but that's an explicit Block 2
concern per the hard-stop.

## 8. Hard-stop compliance

- ✓ `DialecticalNode` was not mutated; `render_tree` is a pure
  function over the immutable tree.
- ✓ No `mark` field was added to `DialecticalNode`.
- ✓ `DefeasibleEvaluator.evaluate` was not wired — that is B1.6.
  The script's graceful `NotImplementedError` handler makes the
  current B1.5 deliverables usable at a REPL today; B1.6 will
  replace that path with the real wiring.
- ✓ `GeneralizedSpecificity` was not implemented — that is Block 2.
- ✓ `answer` handles the `UNKNOWN` case explicitly via
  `_theory_predicates` plus a strong-negation-stripping check. It
  does not conflate "no argument found" with "predicate not in
  language": the UNDECIDED branch runs first if any argument exists
  for the literal or its complement, and UNKNOWN runs only if both
  predicates are absent from the language.
- ✓ Pyright reproduction rule: every pyright diagnostic cleaned in
  `aa41ad1` reproduces under `uv run pyright <file>`.

## 9. Next

B1.6 will wire `DefeasibleEvaluator.evaluate` onto the
`build_arguments` / `build_tree` / `mark` / `answer` pipeline, un-skip
the three `test_trace.py` tests B1.2 parked with `@pytest.mark.skip`,
and pick up the `nests_in_trees` UNDECIDED regression. The
`render_tree` debugger is ready for that dispatch — it already
handles the `[r1, r3]` multi-rule chained-argument case visible in
the pacifist_conflict script output above.
